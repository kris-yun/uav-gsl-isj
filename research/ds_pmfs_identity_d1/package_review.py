"""Make a compact independently recomputable D1 review archive."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile


REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "evidence/ds_pmfs_identity_d1"
F1 = REPO / "research/aod_house03_f1_full624_20260927/templates"
CODE = REPO / "research/ds_pmfs_identity_d1"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    items = []
    for file in sorted(EVIDENCE.iterdir()):
        if file.is_file():
            items.append((f"evidence/{file.name}", file))
    for file in sorted(CODE.glob("*.py")):
        items.append((f"code/{file.name}", file))
    for file in sorted(args.inputs.iterdir()):
        if file.is_file():
            items.append((f"inputs/{file.name}", file))
    for name in ("nominal_u_full_maps.npy", "nominal_rawu_full_maps.npy", "CANDIDATE_SUPPORT.csv"):
        items.append((f"f1/{name}", F1 / name))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    hashes = []
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=True) as z:
        for name, file in items:
            data = file.read_bytes()
            hashes.append(f"{hashlib.sha256(data).hexdigest()}  {name}\n")
            info = zipfile.ZipInfo(name, (2026, 9, 28, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        info = zipfile.ZipInfo("SHA256SUMS", (2026, 9, 28, 0, 0, 0))
        z.writestr(info, "".join(hashes), compress_type=zipfile.ZIP_DEFLATED)
    data = args.output.read_bytes()
    print(f"{args.output}\nbytes={len(data)}\nsha256={hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
