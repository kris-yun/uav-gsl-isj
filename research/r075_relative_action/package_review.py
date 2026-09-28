"""Package R0.75 inputs, exact scoring code, results and SHA256 inventory."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile


REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    items = []
    for root, label, names in (
        (REPO / "evidence/r075_relative_action", "r075/evidence", None),
        (REPO / "research/r075_relative_action", "r075/code", None),
        (REPO / "evidence/ds_pmfs_identity_d1", "prior/d1", (
            "ASSET_FREEZE.json", "COMPACT_EVENTS.json", "D1_RESULT.json")),
        (REPO / "evidence/cd_d0_action_sensory", "prior/cd", ("CD_D0_RESULT.json",)),
        (REPO / "research/ds_pmfs_identity_d1", "prior/d1_code", ("score_shadow.py",)),
        (REPO / "research/cd_d0_action_sensory", "prior/cd_code", ("score_cd_d0.py",)),
    ):
        paths = sorted(root.iterdir()) if names is None else [root / name for name in names]
        for file in paths:
            if file.is_file() and (names is not None or file.suffix in (".json", ".md", ".py")):
                items.append((f"{label}/{file.name}", file))
    for env in range(3):
        for name in (f"env_{env}_bank.npz", f"env_{env}_occupancy.u8"):
            items.append((f"inputs/{name}", args.inputs / name))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    hashes = []
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=True) as z:
        for name, file in items:
            data = file.read_bytes()
            hashes.append(f"{hashlib.sha256(data).hexdigest()}  {name}\n")
            info = zipfile.ZipInfo(name, (2026, 9, 28, 0, 0, 0))
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        info = zipfile.ZipInfo("SHA256SUMS", (2026, 9, 28, 0, 0, 0))
        z.writestr(info, "".join(hashes), compress_type=zipfile.ZIP_DEFLATED)
    data = args.output.read_bytes()
    print(f"{args.output}\nbytes={len(data)}\nsha256={hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
