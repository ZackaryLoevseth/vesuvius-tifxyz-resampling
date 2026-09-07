# Public Vesuvius geometry fixtures — 2026-09-07

Three genuine PHerc0800 segmented papyrus surface patches were retrieved anonymously from the official `vesuvius-challenge-open-data` S3 bucket. They are original source files, not synthesized examples. Only this `data/` directory was written by the dataset acquisition task.

## Files and provenance

| Segment prefix | Stored TIFF shape | Valid vertices | TIFXYZ bytes (including meta.json) | Matching original OBJ bytes |
|---|---:|---:|---:|---:|
| 20251029010146 | 42 × 42 | 1,444 | 56,459 | 246,972 |
| 20251028220955 | 90 × 84 | 5,600 | 93,375 | 1,030,517 |
| 20251028220042 | 93 × 95 | 5,772 | 94,224 | 1,063,811 |

Each segment directory contains `tifxyz_original/{meta.json,x.tif,y.tif,z.tif}`, a matching `*_original.obj`, and the original S3 object listing. `PUBLIC_DATA_MANIFEST.json` records every exact URL, byte count, response metadata, SHA-256, registry membership, and initial inspection. `SHA256SUMS` covers all 21 downloaded originals. All hashes were rechecked successfully after download. Total downloaded: **2,680,138 bytes**, including provenance.

`provenance/metadata.min.json.original.gz` preserves the actual gzip-encoded response from the public metadata endpoint. Its Last-Modified header was 2026-09-07 09:15:13 GMT. Decompress for inspection; do not overwrite it with decoded JSON. The official documentation and AWS registry HTML are preserved alongside it.

## Access and license

- Official AWS registry: https://registry.opendata.aws/vesuvius-challenge-herculaneum-scrolls/
- Official data documentation: https://github.com/ScrollPrize/open-data
- Bucket: https://vesuvius-challenge-open-data.s3.amazonaws.com/
- Current registry: https://vesuvius-challenge-open-data.s3.amazonaws.com/metadata.min.json
- Both official pages designate **CC BY-NC 4.0** and provide anonymous access with no AWS account required.
- Retrieval used ordinary anonymous HTTPS GET requests. No credentials, sign-in, click-through acceptance, server registration, submission, or contact occurred. No restricted `dl.ash2txt.org` dataset was downloaded.
- Retain source attribution and license when later handling results or data. This local acquisition does not establish permission for every future commercial use or redistribution.

Suggested data citation from the official documentation: Giorgio Angelotti, Stephen Parsons, Sean Johnson, Elian Rafael Dal Prà, Johannes Rudolph, Paul Tafforeau, Alessandro Mirone, et al. *Vesuvius Challenge - CT Scans of Herculaneum Papyri*. Vesuvius Challenge. 2026. Accessed 2026-09-07 from the AWS Open Data registry above.

## Reading and geometry conventions

- Each coordinate TIFF is a single two-dimensional float32 array. The three same-shaped arrays provide the x, y, and z coordinate at a stored UV-grid vertex.
- All absent vertices in these three samples are exactly `(-1, -1, -1)`. Initial inspection found no partial sentinels and no nonfinite entries. Official Python loading uses positive finite z as its fallback validity criterion; these samples' valid vertices satisfy it.
- Metadata `scale` is approximately `[0.05, 0.05]`. This is the full-resolution UV-to-stored-grid factor: one stored index step corresponds to approximately 20 full-resolution UV index steps. **Do not multiply XYZ coordinates by 0.05.** It is not a micrometre conversion.
- The official C++ metadata order is `[x_scale, y_scale]`; the Python reader swaps this into `(scale_y, scale_x)`. Equal-scale fixtures do not independently test that axis-order distinction.
- Official code references: https://github.com/ScrollPrize/villa/blob/main/vesuvius/src/vesuvius/tifxyz/reader.py (metadata scale parsing); https://github.com/ScrollPrize/villa/blob/main/vesuvius/src/vesuvius/tifxyz/types.py (full-resolution index mapping).
- Computed valid-vertex bounding boxes agree exactly with each source metadata bbox. Matching OBJ files have the same valid-vertex counts; their bounding boxes differ by at most 0.0000005 coordinate units due to decimal serialization.
- **Physical units remain a provenance boundary.** These original metadata `area_cm2/area_vx2` ratios imply about 8.32 micrometres per coordinate unit, while the registry's current PHerc0800 scan volume is 8.64 micrometres and separate transformed surfaces are published. Do not use the current 8.64 micrometre value to convert these original coordinates without establishing the transform. Native-coordinate geometry is available immediately; the metadata area values are not independently validated truth.
- These are three patches from one scroll and one scale regime, not broad dataset coverage or a labeled ground-truth corpus for every geometry property.

## Minimal local reader

The bundled workspace Python has NumPy and Pillow; `tifffile` was not installed. Pillow successfully decoded these float32 TIFFs.

```python
from pathlib import Path
import numpy as np
from PIL import Image

patch = Path("data/20251029010146-auto_grown_20251029010146642/tifxyz_original")
xyz = np.stack([np.asarray(Image.open(patch / f"{axis}.tif"))
                for axis in ("x", "y", "z")], axis=-1)
valid = np.isfinite(xyz).all(axis=-1) & (xyz[..., 2] > 0)
```

Preserve all downloaded originals. Put diagnostics, corrected metadata, converted geometry, and experimental outputs elsewhere.
