"""Independent small-array OpenCV resize mask oracle; no production imports by default.

The primary oracle measures the installed cv2.resize linear operator using one
basis impulse per source pixel. It does not reproduce candidate indexing or
erosion logic. Exact-rational geometry supplies a second, independent check.
Run with the existing project .venv; this script installs nothing.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import importlib.util
import json
from pathlib import Path

import cv2
import numpy as np


def basis_influence(source_shape, destination_shape, order):
    """Boolean [source pixel, destination row, destination col] influence.

    Nonzero means exact nonzero output from a unit basis impulse in float32.
    No arbitrary epsilon is used to discard small interpolation coefficients.
    Intended for small arrays only; never run this over full scroll images.
    """
    h, w = source_shape
    dh, dw = destination_shape
    if h * w * dh * dw > 5_000_000:
        raise ValueError("Basis oracle deliberately limited to small fixtures")
    flag = cv2.INTER_LINEAR if order == 1 else cv2.INTER_CUBIC
    influence = np.empty((h * w, dh, dw), dtype=bool)
    for index in range(h * w):
        impulse = np.zeros((h, w), dtype=np.float32)
        impulse.flat[index] = 1.0
        influence[index] = cv2.resize(impulse, (dw, dh), interpolation=flag) != 0
    return influence


def basis_validity(mask, influence):
    """An output is safe iff no invalid input has a nonzero coefficient."""
    return ~np.any(influence[~mask.ravel()], axis=0)


def rational_axis_support(source_size, destination_size, destination_index, order):
    """Ideal half-pixel support computed in exact rational arithmetic.

    For 0 < fractional position < 1, all two linear / four cubic taps are
    nonzero (Keys cubic A=-3/4). At fraction zero only the center contributes.
    Clamp before deduplication; replicated boundary taps refer to one input.
    """
    q = Fraction((2 * destination_index + 1) * source_size, 2 * destination_size) - Fraction(1, 2)
    lower = q.numerator // q.denominator
    if q == lower:
        taps = (lower,)
    elif order == 1:
        taps = (lower, lower + 1)
    elif order == 3:
        taps = (lower - 1, lower, lower + 1, lower + 2)
    else:
        raise ValueError("Only linear/cubic reviewed")
    return tuple(sorted({min(max(tap, 0), source_size - 1) for tap in taps}))


def rational_validity(mask, destination_shape, order):
    """Ideal support oracle; appropriate for ordinary, well-spaced phases.

    Float32 coefficient rounding/backend behavior can differ for extremely
    close-to-integer phases. The basis oracle is authoritative for the installed
    small-array execution; this routine does not claim every-size bit parity.
    """
    h, w = mask.shape
    dh, dw = destination_shape
    if (h, w) == (dh, dw):
        return mask.copy()
    ys = [rational_axis_support(h, dh, row, order) for row in range(dh)]
    xs = [rational_axis_support(w, dw, col, order) for col in range(dw)]
    result = np.ones((dh, dw), dtype=bool)
    # Separable boolean products avoid a Python loop over millions of outputs.
    for dy, rows in enumerate(ys):
        row_valid = np.all(mask[list(rows)], axis=0)
        result[dy] = np.fromiter((all(row_valid[col] for col in cols) for cols in xs), bool, count=dw)
    return result


def fixture_masks(shape):
    h, w = shape
    masks = {"all_valid": np.ones(shape, bool), "all_invalid": np.zeros(shape, bool)}
    for name, position in [("center_hole", (h // 2, w // 2)), ("corner_hole", (0, 0)), ("opposite_corner_hole", (h - 1, w - 1))]:
        mask = np.ones(shape, bool)
        mask[position] = False
        masks[name] = mask
    rows, cols = np.indices(shape)
    masks["checkerboard"] = (rows + cols) % 2 == 0
    masks["invalid_border"] = (rows > 0) & (cols > 0) & (rows < h - 1) & (cols < w - 1)
    return masks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, help="Optional candidate upsampling.py to compare; never edited")
    parser.add_argument("--json", type=Path, help="Optional review result JSON output")
    args = parser.parse_args()
    candidate = None
    if args.candidate:
        spec = importlib.util.spec_from_file_location("reviewed_upsampling", args.candidate)
        candidate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(candidate)
    cases = [
        ("identity", (5, 6), (5, 6)),
        ("double_up", (4, 5), (8, 10)),
        ("noninteger_up", (4, 5), (7, 9)),
        ("anisotropic_mixed", (4, 5), (9, 3)),
        ("double_down_area_shortcut", (6, 8), (3, 4)),
        ("one_axis_identity", (4, 5), (4, 9)),
        ("one_axis_half", (6, 5), (3, 9)),
        ("one_row", (1, 5), (3, 9)),
        ("one_column", (5, 1), (9, 3)),
        ("integer_source_centers", (3, 3), (9, 9)),
        ("noninteger_down", (7, 8), (2, 3)),
    ]
    report = {"cv2_version": cv2.__version__, "optimized": cv2.useOptimized(),
              "candidate_evaluated": candidate is not None,
              "ipp_enabled": cv2.ipp.useIPP() if hasattr(cv2, "ipp") else None,
              "oracle": "float32 basis impulse; exactly nonzero coefficient; no candidate helper calls",
              "cases": [], "oracle_disagreements": 0, "false_accepts": 0, "false_rejects": 0}
    for name, shape, destination in cases:
        for order in (1, 3):
            influence = basis_influence(shape, destination, order)
            for mask_name, mask in fixture_masks(shape).items():
                expected = basis_validity(mask, influence)
                exact = rational_validity(mask, destination, order)
                mismatch = int(np.count_nonzero(expected != exact))
                row = {"case": name, "source_shape": shape, "destination_shape": destination,
                       "order": order, "mask": mask_name, "oracle_disagreements": mismatch,
                       "expected_valid": int(expected.sum())}
                report["oracle_disagreements"] += mismatch
                if candidate is not None:
                    grid = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
                    coordinates = [np.where(mask, offset + grid, -1).astype(np.float32) for offset in (1000, 5000, 9000)]
                    result = candidate.upsample_coordinates(*coordinates, mask,
                        (shape[0] / destination[0], shape[1] / destination[1]), target_scale=1.0, order=order)
                    actual = result[3]
                    false_accepts = int(np.count_nonzero(actual & ~expected))
                    false_rejects = int(np.count_nonzero(~actual & expected))
                    row.update(false_accepts=false_accepts, false_rejects=false_rejects)
                    report["false_accepts"] += false_accepts
                    report["false_rejects"] += false_rejects
                report["cases"].append(row)
    report["fixture_count"] = len(report["cases"])
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))
    for case in report["cases"]:
        if case["oracle_disagreements"] or case.get("false_accepts", 0) or case.get("false_rejects", 0):
            print(json.dumps(case))


if __name__ == "__main__":
    main()
