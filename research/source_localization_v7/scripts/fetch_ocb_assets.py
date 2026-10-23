#!/usr/bin/env python3
"""Fetch the pinned eight DISCOVERY worlds; never recurse or open holdouts.

The output directory is a local cache. Do not include its physical .npy files
in the final review artifact. Optional GITHUB_TOKEN is sent only to the pinned
GitHub raw host and is never printed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gsl_discrimination.data.ocb import load_manifest, verify_file


def fetch(output: Path, manifest_path=None, token=None) -> dict:
    manifest = load_manifest(manifest_path)
    output = Path(output)
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    receipts = []
    headers = {"User-Agent": "gsl-discrimination-v7-readonly"}
    if token:
        headers["Authorization"] = "Bearer " + token
    for world in manifest["worlds"]:
        for kind in ("cube", "pooled"):
            spec = world["files"][kind]
            name = f"{world['run_id']}.{kind}.npy"
            expected_path = "evidence/ocb_r2/aod_r2_f0/targets/" + name
            if spec["filename"] != name or spec["remote_path"] != expected_path:
                raise ValueError("manifest path outside the authorized exact discovery files")
            path = raw / name
            url = f"https://raw.githubusercontent.com/{manifest['repository']}/{manifest['commit']}/{expected_path}"
            status = "verified_existing"
            if not path.exists():
                request = Request(url, headers=headers)
                with urlopen(request, timeout=30) as response:
                    # An asset larger than its frozen length is invalid, never a reason
                    # to download an unbounded remote body.
                    body = response.read(spec["size_bytes"] + 1)
                fd, temporary = tempfile.mkstemp(prefix=name + ".", suffix=".partial", dir=raw)
                temp_path = Path(temporary)
                try:
                    with os.fdopen(fd, "wb") as f:
                        f.write(body)
                    verify_file(temp_path, spec)
                    temp_path.replace(path)
                finally:
                    temp_path.unlink(missing_ok=True)
                status = "downloaded_and_verified"
            verify_file(path, spec)
            receipts.append({
                "run_id": world["run_id"], "kind": kind, "url": url,
                "repo_path": spec["remote_path"], "status": status,
                "git_blob_sha": spec["git_blob_sha"], "sha256": spec["sha256"],
                "bytes": spec["size_bytes"],
            })
    result = {
        "commit": manifest["commit"], "scope": manifest["scope"],
        "world_count": 8, "file_count": len(receipts), "files": receipts,
        "new_propagation_steps": 0, "confirmation_or_H03_targets_read": False,
    }
    (output / "FETCH_RECEIPT.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="local raw-cache directory, outside final artifacts")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    result = fetch(args.output, args.manifest, os.environ.get("GITHUB_TOKEN"))
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, indent=2))


if __name__ == "__main__":
    main()
