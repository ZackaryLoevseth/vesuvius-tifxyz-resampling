"""Run a regression against upstream in memory; exit 1 is the expected result."""
import importlib.util
from pathlib import Path
import pytest
import vesuvius.tifxyz.upsampling as candidate

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("upstream_upsampling", root / "baseline/upsampling.py")
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
candidate.upsample_coordinates = baseline.upsample_coordinates
print("Expected failure: regression run against unmodified upstream function", flush=True)
raise SystemExit(pytest.main([str(root / "source/vesuvius/tests/tifxyz/test_upsampling.py"), "-q", "--maxfail=1"]))
