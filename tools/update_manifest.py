"""Regenerate current presentation manifests; preserve frozen publication ledgers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {"MANIFEST.json", "SHA256SUMS"}


def generated_files() -> dict[str, bytes]:
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    ).decode().split("\0")
    files = {
        name: (ROOT / name).read_bytes()
        for name in sorted(set(names) - OUTPUTS - {""})
        if (ROOT / name).is_file()
    }
    manifest = json.loads((ROOT / "MANIFEST.json").read_text())
    manifest["files"] = [
        {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in files.items()
    ]
    manifest["count"] = len(files)
    manifest["scope"] = (
        "Current public presentation tree; MANIFEST.json and SHA256SUMS, "
        "Git metadata, and ignored local files are excluded"
    )
    manifest["editorial_revision"] = {
        "date": "2026-10-07",
        "scope": "HayosoAi public identity and scope wording; measured scientific artifacts unchanged",
        "original_manifest": "FROZEN_PUBLICATION_MANIFEST.json",
        "original_sha256sums": "FROZEN_PUBLICATION_SHA256SUMS",
    }
    encoded = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    files["MANIFEST.json"] = encoded
    sums = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n"
        for name, data in sorted(files.items())
    ).encode()
    return {"MANIFEST.json": encoded, "SHA256SUMS": sums}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = generated_files()
    if args.check:
        stale = [name for name, data in expected.items() if (ROOT / name).read_bytes() != data]
        if stale:
            raise SystemExit("Stale manifest: " + ", ".join(stale))
        print("Current manifest and checksums verified.")
    else:
        for name, data in expected.items():
            (ROOT / name).write_bytes(data)
        print("Current manifest and checksums regenerated.")


if __name__ == "__main__":
    main()
