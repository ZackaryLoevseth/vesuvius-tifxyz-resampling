# Reproduce the local contribution

The existing work directory already contains the checked-out source and task-local environment. From that directory:

```sh
AGENTS_AGENT_MODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=2 .venv/bin/python tools/validate_real_meshes.py
AGENTS_AGENT_MODE=1 NUMBA_NUM_THREADS=2 .venv/bin/python -m pytest -q source/vesuvius/tests/tifxyz/test_upsampling.py
AGENTS_AGENT_MODE=1 NUMBA_NUM_THREADS=2 .venv/bin/python -m pytest -q source/vesuvius/tests/test_surface_preflight.py source/vesuvius/tests/tifxyz_label_transfer/test_io.py
```

The real-data script verifies source hashes before and after execution, measures the preserved upstream function and patched function, writes the quantitative report, and generates the PNG and NPZ example. It writes `evidence/real_mesh_results.json`, `evidence/PHerc0800_before_after.png`, and the example NPZ. Copy previous results to a dated directory before rerunning if you want to preserve them.

## Clean reconstruction from this repository or its ZIP

The ZIP contains the original inputs, original target module, patch, focused tests, review source snapshots, evidence, and reproduction scripts. It omits the 1.6 GB monorepository, virtual environments, and compiled dependencies. `review_source/` is a snapshot for reading, not a complete installed package.

After cloning this repository or extracting its ZIP, the following reconstructs the source. It performs network downloads and local dependency setup; it does not register, accept dataset terms, publish, or submit anything.

```sh
git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa.git source
git -C source fetch --depth 1 origin d8c5f488a105286c548c99c5f7c7ad9f29e3ed14
git -C source checkout --detach d8c5f488a105286c548c99c5f7c7ad9f29e3ed14
git -C source apply ../evidence/tifxyz-resampling-validity.patch
AGENTS_AGENT_MODE=1 AGENTS_ALLOW_INSTALL=1 uv venv --python 3.14 .venv
AGENTS_AGENT_MODE=1 AGENTS_ALLOW_INSTALL=1 uv pip install --python .venv/bin/python -e source/vesuvius numpy==2.5.3 scipy==1.18.1 tifffile==2026.8.23 imagecodecs==2026.8.16 numba==0.67.0 opencv-python-headless==5.0.0.93 pytest==9.1.1 matplotlib==3.11.1
```

Run the first three commands at the top of this document afterward. Full environment versions from the measured macOS arm64 run are recorded in `evidence/environment.freeze.txt`. Reconstructing on another OS may resolve platform-specific wheels differently and does not inherit our validation.

## Baseline regression and OpenCV 4 compatibility

```sh
AGENTS_AGENT_MODE=1 NUMBA_NUM_THREADS=2 .venv/bin/python tools/check_regression_baseline.py
```

This command intentionally loads the original function in memory and must fail its first applicable support regression. Exit 1 is expected; it does not alter the installed source. The preserved log is `evidence/baseline_expected_failure.log`.

The compatibility run used a separately installed OpenCV wheel so the main environment remained unchanged:

```sh
AGENTS_AGENT_MODE=1 AGENTS_ALLOW_INSTALL=1 uv pip install --python .venv/bin/python --target .cv4 --no-deps opencv-python-headless==4.14.0.94
AGENTS_AGENT_MODE=1 PYTHONPATH="$PWD/.cv4:$PWD/source/vesuvius/src" NUMBA_NUM_THREADS=2 .venv/bin/python -m pytest -q source/vesuvius/tests/tifxyz/test_upsampling.py
```

53 focused tests passed on each version. 21 nearby I/O/preflight tests ran on the primary OpenCV 5 environment. The complete ML suite, GPU behavior, Linux and Windows were not tested.

## Data and acceptance boundaries

Use the original inputs already included under `data/`; their manifest contains anonymous official download URLs if re-acquisition is needed. The primary real-data tests do not use generated meshes. The unit tests use controlled edge cases as supplemental numerical regressions.

Data and derived figures remain attributed under CC BY-NC 4.0; see `data/README.md`. Code retains its upstream MIT license. Source hashes and a passing local patch do not establish community adoption, human review, prize submission, eligibility, or payment.
