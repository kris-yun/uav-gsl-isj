"""Extract only the preregistered H03 seed11 data from the immutable archive."""

from __future__ import annotations

import hashlib
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "evidence" / "source" / "CCDE_HELDOUT_EVIDENCE_V3_20260807.tar.gz"
EXPECTED = "bfb841c50e38b9848cb57e0cad22c6a6e65fcc1b754c384df6cc477cc6b0f295"
OUT = ROOT / "work"
PREFIX = "ccde_holdout_v3_20260807/H03_seed11/"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    actual = sha256(ARCHIVE)
    if actual != EXPECTED:
        raise SystemExit(f"archive hash mismatch: {actual}")
    OUT.mkdir(exist_ok=True)
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        members = [m for m in archive.getmembers() if m.name.startswith(PREFIX)]
        if not members:
            raise SystemExit("H03 seed11 data missing")
        for member in members:
            archive.extract(member, OUT, filter="data")
    print(f"MC_SCSP_INPUT_READY members={len(members)} sha256={actual}")


if __name__ == "__main__":
    main()

