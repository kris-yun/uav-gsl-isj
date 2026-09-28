"""Create a standalone small CD-D0 review ZIP with its D1 input dependency."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile


REPO = Path(__file__).resolve().parents[2]
F1 = REPO / "research/aod_house03_f1_full624_20260927/templates"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    items = []
    for subdir, label in (("evidence/ds_pmfs_identity_d1", "d1/evidence"),
                          ("evidence/cd_d0_action_sensory", "cd/evidence"),
                          ("research/ds_pmfs_identity_d1", "d1/code"),
                          ("research/cd_d0_action_sensory", "cd/code")):
        for file in sorted((REPO / subdir).iterdir()):
            if file.is_file() and (file.suffix in (".json", ".md", ".py")):
                items.append((f"{label}/{file.name}", file))
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
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        z.writestr(zipfile.ZipInfo("SHA256SUMS", (2026, 9, 28, 0, 0, 0)), "".join(hashes),
                   compress_type=zipfile.ZIP_DEFLATED)
    data = args.output.read_bytes()
    print(f"{args.output}\nbytes={len(data)}\nsha256={hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
