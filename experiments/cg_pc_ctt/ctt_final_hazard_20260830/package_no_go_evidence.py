#!/usr/bin/env python3
"""Package the CTT H01 final hazard M1 NO-GO evidence into an auditable tar.gz."""
from __future__ import annotations

import hashlib
import io
import json
import tarfile
import time
from pathlib import Path

REPO = Path(r"D:\ZYC\uav-gsl-isj")
EXP = REPO / "experiments" / "cg_pc_ctt" / "ctt_final_hazard_20260830"
DOCS = REPO / "docs"
STAGING = Path(r"D:\ZYC\A-gas\_staging")
WORK = Path(r"D:\ZYC\A-gas\workspace\CTT_H01_GPU_TRAIN")

TAG = "CTT_H01_FINAL_HAZARD_M1_NO_GO_20260830_R1"
OUT = STAGING / f"{TAG}.tar.gz"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    # (archive_arcname, local_path)
    files: list[tuple[str, Path]] = [
        ("00_EXECUTIVE_VERDICT.md", EXP / "VERDICT_FINAL_HAZARD_M1_20260830.md"),
        ("01_FRESH_WIND_INVENTORY.md", DOCS / "FRESH_WIND_INVENTORY_20260830.md"),
        ("02_FREEZE_FINAL_HAZARD_SOLVER.md", EXP / "FREEZE_FINAL_HAZARD_SOLVER_20260830.md"),
        ("03_FREEZE_FINAL_HAZARD_SOLVER.json", EXP / "FREEZE_FINAL_HAZARD_SOLVER_20260830.json"),
        ("04_FRESH_WIND_INVENTORY.json", EXP / "FRESH_WIND_INVENTORY_20260830.json"),
        ("05_FRESH_CONTEXT_MANIFEST.json", EXP / "evidence_r2" / "fresh_context_manifest.json"),
        ("06_FRESH_BANK_SUMMARY.json", WORK / "CTT_H01_FRESH_BANK_20260830" / "bank_summary.json"),
        ("code/train_eval_final_hazard_solver.py", EXP / "train_eval_final_hazard_solver.py"),
        ("code/ctt_h01_wind_bank_io.py", EXP / "ctt_h01_wind_bank_io.py"),
        ("code/prepare_ctt_h01_fresh_wind_contexts.py", EXP / "prepare_ctt_h01_fresh_wind_contexts.py"),
        ("code/materialize_ctt_h01_fresh_bank.py", EXP / "materialize_ctt_h01_fresh_bank.py"),
        ("code/gen_fresh_wind_inventory.py", EXP / "gen_fresh_wind_inventory.py"),
        ("evidence/06_TRAINING_CONTRACT.json", EXP / "evidence_r2" / "06_TRAINING_CONTRACT.json"),
        ("evidence/07_M1_PHYSICAL_GATE.json", EXP / "evidence_r2" / "07_M1_PHYSICAL_GATE.json"),
        ("evidence/VERDICT.txt", EXP / "evidence_r2" / "VERDICT.txt"),
        ("evidence/conditional_history.json", EXP / "evidence_r2" / "conditional_history.json"),
        ("evidence/static_history.json", EXP / "evidence_r2" / "static_history.json"),
        ("evidence/conditional_best.pt", EXP / "evidence_r2" / "conditional_best.pt"),
        ("evidence/static_best.pt", EXP / "evidence_r2" / "static_best.pt"),
    ]

    for arc, path in files:
        if not path.is_file():
            raise SystemExit(f"MISSING:{path}")

    # build in-memory SHA-256 manifest
    manifest_lines = []
    for arc, path in files:
        manifest_lines.append(f"{sha256_file(path)}\t{arc}\t{path.stat().st_size}")

    manifest_bytes = ("# " + TAG + " SHA-256 manifest\n" +
                      "# generated " + time.strftime("%Y-%m-%dT%H:%M:%S") + "\n" +
                      "\n".join(manifest_lines) + "\n").encode("utf-8")
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()

    # write tar.gz with a wrapping top directory
    STAGING.mkdir(parents=True, exist_ok=True)
    with tarfile.open(OUT, "w:gz") as tar:
        # manifest first
        info = tarfile.TarInfo(f"{TAG}/FILE_SHA256.tsv")
        info.size = len(manifest_bytes)
        tar.addfile(info, io.BytesIO(manifest_bytes))
        for arc, path in files:
            tar.add(path, arcname=f"{TAG}/{arc}")

    print(f"PACKAGED {OUT}")
    print(f"files={len(files)} + manifest")
    print(f"manifest_sha256={manifest_sha}")
    print(f"package_sha256={sha256_file(OUT)}")
    print(f"size={OUT.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
