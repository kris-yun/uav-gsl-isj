#!/usr/bin/env python3
"""Recoverably remove only stale temporary shards from interrupted workers."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path


ROOT = Path("/dev/shm/CTT_H01_WIND_BANK_FULL_20260830_R1")
TARGET = Path("/home/zyc/CTT_H01_STALE_TMP_QUARANTINE_20260830")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if TARGET.exists():
        raise SystemExit("CTT_H01_STALE_TMP_QUARANTINE_REFUSE_EXISTING")
    stale = [path for path in ROOT.glob("context_*/member_*/*.tmp.*")
             if time.time() - path.stat().st_mtime > 180]
    TARGET.mkdir(parents=True)
    rows = []
    for source in stale:
        relative = source.relative_to(ROOT)
        target = TARGET / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if digest(source) != digest(target):
            raise RuntimeError(f"CTT_H01_STALE_TMP_COPY_FAIL:{relative}")
        rows.append({"relative": relative.as_posix(), "sha256": digest(source)})
    (TARGET / "MANIFEST.json").write_text(json.dumps({"files": rows}, indent=2) + "\n")
    for source in stale:
        source.unlink()
    print(f"CTT_H01_STALE_TMP_QUARANTINE=PASS files={len(stale)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
