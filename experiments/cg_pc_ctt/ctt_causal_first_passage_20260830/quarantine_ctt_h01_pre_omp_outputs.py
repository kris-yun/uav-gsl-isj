#!/usr/bin/env python3
"""Recoverably quarantine the exact pre-OMP-freeze files after VM expansion."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path("/dev/shm/CTT_H01_WIND_BANK_FULL_20260830_R1")
CHECKPOINT_MANIFEST = Path(
    "/home/zyc/CTT_H01_WIND_BANK_FULL_20260830_R1_PRE_VCPU_MANIFEST/source_sha256.tsv"
)
QUARANTINE = Path("/home/zyc/CTT_H01_PRE_OMP_FREEZE_QUARANTINE_20260830")
PRE_FREEZE_EXTRA_COUNT = 20


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    if QUARANTINE.exists():
        raise SystemExit("CTT_H01_QUARANTINE_REFUSE_EXISTING")
    checkpoint_paths = set()
    for line in CHECKPOINT_MANIFEST.read_text(encoding="utf-8").splitlines():
        _, relative = line.split("  ", 1)
        checkpoint_paths.add(relative.removeprefix("./"))
    candidates = []
    for path in ROOT.glob("context_*/member_*/*.bin"):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in checkpoint_paths:
            candidates.append((path.stat().st_mtime_ns, relative, path))
    candidates.sort()
    if len(candidates) <= PRE_FREEZE_EXTRA_COUNT:
        raise SystemExit(f"CTT_H01_QUARANTINE_NOT_ENOUGH_CANDIDATES:{len(candidates)}")
    selected = candidates[:PRE_FREEZE_EXTRA_COUNT]
    QUARANTINE.mkdir(parents=True)
    records = []
    for mtime_ns, relative, source in selected:
        target = QUARANTINE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        source_hash = digest(source)
        shutil.copy2(source, target)
        if digest(target) != source_hash:
            raise RuntimeError(f"CTT_H01_QUARANTINE_COPY_HASH_FAIL:{relative}")
        records.append({"relative": relative, "sha256": source_hash, "mtime_ns": mtime_ns})
    (QUARANTINE / "QUARANTINE_MANIFEST.json").write_text(
        json.dumps({"contract": "CTT_H01_PRE_OMP_FREEZE_QUARANTINE_V1",
                    "reason": "generated_after_vcpu_expansion_before_OMP_NUM_THREADS_4_freeze",
                    "files": records}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for _, relative, source in selected:
        if digest(QUARANTINE / relative) != digest(source):
            raise RuntimeError(f"CTT_H01_QUARANTINE_PRE_UNLINK_HASH_FAIL:{relative}")
        source.unlink()
    print(f"CTT_H01_PRE_OMP_FREEZE_QUARANTINE=PASS files={len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
