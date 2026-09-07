"""Compare unchanged upstream and patched resizing on byte-original PHerc0800 meshes.

Run from the work-package directory with its .venv/bin/python. This is a local
geometry check, not a CT/ink evaluation or evidence of prize acceptance.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import statistics
import time
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from vesuvius.tifxyz import read_tifxyz
from vesuvius.tifxyz.upsampling import upsample_coordinates

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("upstream_upsampling", ROOT / "baseline/upsampling.py")
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
cv2.setNumThreads(1)


def support_oracle(mask, output_shape, order):
    """Empirical separable impulse support; abs prevents cubic cancellation.

    Each column/row of the resized identity is an independent source impulse.
    No inverse-coordinate formula from the implementation is used here.
    Ignore only numerical weights <=1e-12 at mathematically exact centers.
    """
    flag = {0: cv2.INTER_NEAREST, 3: cv2.INTER_CUBIC}.get(order, cv2.INTER_LINEAR)
    h, w = mask.shape
    oh, ow = output_shape
    row_weights = np.abs(cv2.resize(np.eye(h, dtype=np.float32), (h, oh), interpolation=flag))
    col_weights = np.abs(cv2.resize(np.eye(w, dtype=np.float32), (ow, w), interpolation=flag))
    return (row_weights @ (~mask).astype(np.float32) @ col_weights) <= 1e-12


def render_example(surface, before, after, oracle, path):
    before_bad = before[3] & ~oracle
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
    fig.suptitle("PHerc. 0800 — linear surface resizing, same coordinates and settings", fontsize=16)
    source_xyz = (surface._x, surface._y, surface._z)
    samples = [(*source_xyz, surface.valid_vertex_mask), before, after]
    names = ["Original coarse surface", "Upstream: accepts invalid-source influence", "Patched: rejects invalid-source influence"]
    colors = ["#2563eb", "#64748b", "#2563eb"]
    for col, (result, name, color) in enumerate(zip(samples, names, colors)):
        valid = result[3]
        stride = max(1, int(np.count_nonzero(valid) / 20000))
        axes[0, col].scatter(result[0][valid][::stride], result[1][valid][::stride], s=1, c=color, rasterized=True)
        axes[0, col].set_title(name, fontsize=11)
        axes[0, col].set_xlabel("X, native coordinate units")
        axes[0, col].set_ylabel("Y, native coordinate units")
        axes[0, col].set_aspect("equal", adjustable="datalim")
        axes[1, col].imshow(valid, cmap="Greys", interpolation="nearest")
        axes[1, col].set_xlabel("Mesh column")
        axes[1, col].set_ylabel("Mesh row")
    axes[0, 1].scatter(before[0][before_bad][::10], before[1][before_bad][::10], s=2, c="#dc2626", rasterized=True)
    bad_overlay = np.zeros((*before_bad.shape, 4))
    bad_overlay[before_bad] = (0.86, 0.15, 0.15, 1.0)
    axes[1, 1].imshow(bad_overlay, interpolation="nearest")
    axes[1, 0].set_title(f"{surface.valid_vertex_mask.sum():,} valid source vertices")
    axes[1, 1].set_title(f"{before_bad.sum():,} accepted points depend on missing vertices", color="#b91c1c")
    axes[1, 2].set_title(f"{np.sum(after[3] & ~oracle):,} such points accepted after fix")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    manifest = json.loads((ROOT / "data/PUBLIC_DATA_MANIFEST.json").read_text())
    for item in manifest["files"]:
        payload = (ROOT / "data" / item["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item["sha256"], item["path"]
    print(f"Original-file checksums: {len(manifest['files'])}/{len(manifest['files'])} PASS", flush=True)
    report = {
        "upstream_commit": (ROOT / "baseline/UPSTREAM_COMMIT.txt").read_text().strip(),
        "baseline_sha256": hashlib.sha256((ROOT / "baseline/upsampling.py").read_bytes()).hexdigest(),
        "patched_sha256": hashlib.sha256((ROOT / "source/vesuvius/src/vesuvius/tifxyz/upsampling.py").read_bytes()).hexdigest(),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "numpy": np.__version__, "opencv": cv2.__version__, "opencv_threads": cv2.getNumThreads()},
        "oracle": "Absolute separable OpenCV source-impulse weights; invalid support >1e-12",
        "benchmark": "One warmup then three complete function calls, same process/input/order; median and range in seconds, CPU only",
        "cases": [],
        "limits": ["Three patches of one scroll", "No CT volume or ink model evaluation", "Coordinate units only; no physical-unit conversion", "No theorem of all-size/backend correctness; supplemental edge tests required"],
    }
    for path in sorted((ROOT / "data").glob("*/tifxyz_original")):
        surface = read_tifxyz(path)
        args = (surface._x, surface._y, surface._z, surface.valid_vertex_mask, surface.get_scale_tuple())
        for order in (0, 1, 3):
            outputs, timings = [], []
            for function in (baseline.upsample_coordinates, upsample_coordinates):
                result = function(*args, order=order)
                elapsed = []
                for _ in range(3):
                    start = time.perf_counter()
                    result = function(*args, order=order)
                    elapsed.append(time.perf_counter() - start)
                outputs.append(result)
                timings.append({"median": statistics.median(elapsed), "min": min(elapsed), "max": max(elapsed), "samples": elapsed})
            before, after = outputs
            oracle = support_oracle(surface.valid_vertex_mask, before[3].shape, order)
            counts = []
            for result in outputs:
                outside = np.zeros(result[3].shape, dtype=bool)
                for output, original in zip(result[:3], args[:3]):
                    valid_values = original[args[3]]
                    outside |= (output < valid_values.min() - 1.0) | (output > valid_values.max() + 1.0)
                counts.append({
                    "accepted": int(result[3].sum()),
                    "accepted_with_invalid_source_support": int(np.sum(result[3] & ~oracle)),
                    "rejected_without_invalid_source_support": int(np.sum(~result[3] & oracle)),
                    "accepted_outside_source_bbox_plus_one": int(np.sum(outside & result[3])),
                })
            common = before[3] & after[3]
            bit_exact_common = all(np.array_equal(a[common], b[common]) for a, b in zip(before[:3], after[:3]))
            assert bit_exact_common
            assert counts[1]["accepted_with_invalid_source_support"] == 0
            assert all(np.all(a[~after[3]] == -1) for a in after[:3])
            if order == 0:
                assert all(np.array_equal(a, b) for a, b in zip(before, after))
            item = {"segment": path.parent.name, "stored_shape": list(surface.shape), "output_shape": list(before[3].shape), "scale": list(surface.get_scale_tuple()), "order": order, "before": counts[0], "after": counts[1], "common_accepted_coordinates_bit_exact": bit_exact_common, "timing_before_seconds": timings[0], "timing_after_seconds": timings[1]}
            report["cases"].append(item)
            print(f"{path.parent.name[:14]} order={order}: invalid-supported accepted {counts[0]['accepted_with_invalid_source_support']:,} -> {counts[1]['accepted_with_invalid_source_support']:,}; median {timings[0]['median']:.4f}s -> {timings[1]['median']:.4f}s; common coordinates BIT-EXACT", flush=True)
            if surface.shape == (42, 42) and order == 1:
                render_example(surface, before, after, oracle, evidence / "PHerc0800_before_after.png")
                np.savez_compressed(evidence / "PHerc0800_resampling_example.npz", before_xyz=np.stack(before[:3], axis=-1), before_valid=before[3], after_xyz=np.stack(after[:3], axis=-1), after_valid=after[3], oracle_valid=oracle)
            (evidence / "real_mesh_results.json").write_text(json.dumps(report, indent=2) + "\n")
    for item in manifest["files"]:
        assert hashlib.sha256((ROOT / "data" / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    print("Real-data validation PASS; all originals unchanged.", flush=True)


if __name__ == "__main__":
    main()
