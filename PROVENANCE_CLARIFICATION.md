# Clarification of recorded thread configuration

This note clarifies a discrepancy in the published reproduction record without changing the frozen evidence.

[REVIEW_REPORT.md](REVIEW_REPORT.md) describes timing measurements as using one OpenCV thread. The environment in [evidence/real_mesh_results.json](evidence/real_mesh_results.json) records `opencv_threads: 10`. The current [reproduction script](tools/validate_real_meshes.py) requests one thread with `cv2.setNumThreads(1)`.

These records do not presently establish one consistent thread configuration for the reported run. Timing comparisons should be read with that limitation until the run's provenance is reconciled. The reported geometric counts and coordinate comparisons are separate observations; this discrepancy alone neither validates nor invalidates them.

No new reproduction, performance result, downstream-quality result, or maintainer adoption is established by this editorial clarification. The original report and result files remain unchanged.
