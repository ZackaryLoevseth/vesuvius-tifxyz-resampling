# Independent OpenCV resize support review

Reviewed 2026-09-07. Production source was read, not modified. The installed runtime reports OpenCV **5.0.0**, optimized CPU execution enabled and IPP disabled; the build includes ARM NEON and custom HAL implementations. The primary source used is the corresponding OpenCV 5.0.0 tag:

https://github.com/opencv/opencv/blob/5.0.0/modules/imgproc/src/resize.cpp

## Source findings

- Lines 3974 and 4227–4228: explicit destination dimensions determine `inv_scale = destination/source`, then the generic implementation computes its reciprocal. For exact operation-order agreement, use `1.0 / (destination/source)` rather than assuming direct `source/destination` is identical at every floating-point rounding boundary.
- Lines 4110–4112 and 4167–4169: the half-pixel inverse position is calculated in double precision, converted to float32, then floored. Fractional status must be determined after the float32 conversion.
- Lines 965–972: cubic uses Keys parameter **A=-0.75**, not Catmull–Rom's -0.5. A fractional position normally has four contributing taps. At an exact integer position the coefficients are 0, 1, 0, 0.
- Lines 4121–4132 clamp horizontal linear boundaries. `HResizeCubic` clamps individual cubic taps to edge pixels; the generic vertical invoker clamps each row (line 2220). Border replication does not require outside-the-image mask values.
- Lines 4247–4251 bypass interpolation and copy when both dimensions are unchanged.
- Lines 4018–4021 redirect exact twofold reduction in both axes from linear to area interpolation. Its support is the full corresponding 2×2 block with quarter weights.

The old nearest-resized eroded mask samples a different inverse map from linear/cubic coordinate resizing. The support review therefore uses resize contributions directly, not erosion or nearest-neighbor mask logic.

## Independent oracle

`review_oracle.py` measures the installed float32 resize operator with one unit impulse per source pixel. A destination is valid exactly when none of the invalid source impulses produce a nonzero output there. It uses no helper from the candidate. A second implementation derives ideal support using exact rational half-pixel positions and border clamping.

The two oracles agree on **154 small fixture combinations**: identity, twofold enlargement/reduction, noninteger scaling, mixed anisotropic scaling, single unchanged or halved axes, one-row/one-column images, and integer source centers, each with seven validity patterns and both linear/cubic interpolation. `independent_oracle_self_review.json` records this result. This checks agreement between the two oracles. Candidate behavior is evaluated separately by the production regression tests.

## Confirmed large-dimension exceptions in the first candidate

Both results below refer to candidate source SHA-256 `2619428c73ff801823cd2eb6433084309e45564fdcf3a7d3d50f932804a466c6`. They are historical review receipts and should not be overwritten after a fix.

| Actual source/output shape | Invalid source pixel | OpenCV output and weight | First helper result |
|---|---|---|---|
| (1, 16,777,218) → same | (0, 16,777,217) | Same destination pixel, weight 1 (copy) | Incorrectly valid |
| (2, 8,388,610) → (1, 4,194,305), linear | (0, 8,388,609) | (0, 4,194,304), weight 0.25 (area shortcut) | Incorrectly valid |

The first case arises because float32 rounds integer 16,777,217 to 16,777,216. The second rounds half-pixel 8,388,608.5 to 8,388,608; the general footprint calculation consequently drops a nonzero tap used by the area shortcut. Explicitly matching the copy and half-size branches addresses these two exceptions. These are wide, bounded arrays, not scroll-scale downloads.

Receipts: `large_identity_numeric_review.json`, `large_half_numeric_review.json`. Both cases were checked against actual `cv2.resize` basis impulses, not only a numerical prediction.

## Rounding and compatibility limits

- Exact integer positions need only the center source sample for finite sentinel data. Blanket 2×2/4×4 validity at such positions is unnecessarily destructive.
- Near-integer cubic coefficients can be affected by float arithmetic and fused operations. A footprint based on every nominal fractional tap is conservative if a coefficient happens to round to zero; exact minimal-support equivalence across all builds is not established. A stress probe of four single-invalid masks, shape (1,4) → (1,1,000,001), observed **zero** such extra rejections on this build (`cubic_zero_tap_review.json`). Do not claim an observed zero-weight noninteger defect from that probe.
- Binary impulse support is a finite-input interpolation oracle. It is not a guarantee about IEEE `0 × NaN` propagation or invalid inputs containing infinities. The acquired data use finite -1 sentinels.
- Linear interpolation of finite valid coordinates remains in their convex hull. Cubic interpolation can legitimately overshoot even with fully valid support, so bounding-box escape is a decisive contamination check for linear interpolation but not sufficient evidence against cubic interpolation.
- Source review plus these tests does not certify every OpenCV backend, version, dtype, image dimension, or phase. Retain the tested-version statement and ensure the candidate matches fast paths before making broader claims.
