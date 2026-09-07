"""Supplemental kernel regressions for the real-surface resampling failure.

The impulse oracle measures OpenCV's support rather than duplicating its
coordinate mapping. These small edge cases complement the real-scroll evidence.
"""

import cv2
import numpy as np
import pytest

from vesuvius.tifxyz.upsampling import _resize_valid_mask, upsample_coordinates


def _flag(order):
    return {0: cv2.INTER_NEAREST, 3: cv2.INTER_CUBIC}.get(order, cv2.INTER_LINEAR)


def _impulse_validity(mask, output_shape, order):
    """Find invalid support without cancellation between signed cubic weights."""
    invalid_support = np.zeros(output_shape, dtype=bool)
    for row, col in np.argwhere(~mask):
        impulse = np.zeros(mask.shape, dtype=np.float32)
        impulse[row, col] = 1.0
        resized = cv2.resize(
            impulse, output_shape[::-1], interpolation=_flag(order)
        )
        # OpenCV may leave ~1e-17 residue at an exact source center. Ignore
        # double-precision rounding noise, far below float32 coordinate accuracy.
        invalid_support |= np.abs(resized) > 1e-12
    return ~invalid_support


def _resize(mask, output_shape, order):
    rows, cols = np.indices(mask.shape, dtype=np.float32)
    coordinates = (
        np.where(mask, 3000.0 + cols, -1.0),
        np.where(mask, 4000.0 + rows, -1.0),
        np.where(mask, 5000.0 + rows + cols, -1.0),
    )
    source_scale = tuple(
        source / target for source, target in zip(mask.shape, output_shape)
    )
    result = upsample_coordinates(
        *coordinates, mask, source_scale=source_scale, order=order
    )
    return coordinates, result


@pytest.mark.parametrize("order", [0, 1, 3, 2])
@pytest.mark.parametrize(
    "source_shape,output_shape",
    [
        ((1, 1), (3, 5)),
        ((1, 4), (5, 9)),
        ((4, 1), (9, 5)),
        ((2, 2), (11, 22)),
        ((3, 4), (3, 4)),
        ((3, 4), (6, 12)),
        ((7, 9), (11, 22)),
        ((7, 9), (3, 4)),
    ],
)
def test_each_invalid_vertex_matches_opencv_support(
    source_shape, output_shape, order
):
    # Moving the hole across every vertex exercises all corners, edges, and
    # interior taps. In particular, border replication must clamp each tap.
    for row, col in np.ndindex(source_shape):
        mask = np.ones(source_shape, dtype=bool)
        mask[row, col] = False
        coordinates, result = _resize(mask, output_shape, order)
        expected_valid = _impulse_validity(mask, output_shape, order)
        np.testing.assert_array_equal(
            result[3], expected_valid, err_msg=f"invalid vertex {(row, col)}"
        )
        for source, resized in zip(coordinates, result[:3]):
            expected = cv2.resize(
                source, output_shape[::-1], interpolation=_flag(order)
            )
            # Valid coordinate interpolation remains exactly OpenCV's result.
            np.testing.assert_array_equal(
                resized[expected_valid], expected[expected_valid]
            )
            np.testing.assert_array_equal(resized[~expected_valid], -1.0)


@pytest.mark.parametrize("order", [0, 1, 3, 2])
def test_multiple_holes_use_union_of_kernel_support(order):
    mask = np.ones((7, 9), dtype=bool)
    mask[0, 0] = mask[-1, -1] = False
    mask[2:4, 3:5] = False
    _, result = _resize(mask, (11, 22), order)
    np.testing.assert_array_equal(
        result[3], _impulse_validity(mask, (11, 22), order)
    )


@pytest.mark.parametrize("order", [0, 1, 3, 2])
def test_identity_preserves_mask_and_coordinates(order):
    mask = np.array([[True, False, True], [False, True, True]])
    coordinates, result = _resize(mask, mask.shape, order)
    np.testing.assert_array_equal(result[3], mask)
    for original, resized in zip(coordinates, result[:3]):
        np.testing.assert_array_equal(resized, original)


@pytest.mark.parametrize("order", [0, 1, 3, 2])
@pytest.mark.parametrize("is_valid", [False, True])
def test_uniform_mask_is_preserved_at_borders(order, is_valid):
    mask = np.full((3, 4), is_valid, dtype=bool)
    _, result = _resize(mask, (8, 11), order)
    np.testing.assert_array_equal(result[3], is_valid)
    if not is_valid:
        for resized in result[:3]:
            np.testing.assert_array_equal(resized, -1.0)


def test_nearest_preserves_existing_mask_resize():
    mask = np.array(
        [[True, False, True, False], [False, True, True, True],
         [True, True, False, True]]
    )
    _, result = _resize(mask, (8, 11), 0)
    expected = cv2.resize(
        mask.astype(np.uint8), (11, 8), interpolation=cv2.INTER_NEAREST
    ).astype(bool)
    np.testing.assert_array_equal(result[3], expected)


@pytest.mark.parametrize("order", [1, 3])
def test_large_identity_does_not_round_source_indices(order):
    # Above 2**24, float32 cannot represent every integer source index.
    # OpenCV's identity path copies pixels without this rounding.
    mask = np.ones((1, 2**24 + 2), dtype=bool)
    mask[0, -1] = False
    actual = _resize_valid_mask(mask, mask.shape, order)
    np.testing.assert_array_equal(actual, mask)


@pytest.mark.parametrize("order", [1, 2])
def test_large_exact_half_uses_all_four_area_taps(order):
    # OpenCV switches exact 2x linear downsampling to a 2x2 area average.
    # Float32 loses half-integers above 2**23; the shortcut must stay integer.
    mask = np.ones((2, 2**23 + 2), dtype=bool)
    mask[0, -1] = False
    actual = _resize_valid_mask(mask, (1, mask.shape[1] // 2), order)
    assert not actual[0, -1]
    assert actual[0, :-1].all()
