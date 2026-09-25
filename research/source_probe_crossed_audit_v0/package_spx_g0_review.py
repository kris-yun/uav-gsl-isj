#!/usr/bin/env python3
"""Package independently reproducible SPX-G0 crossed tensors and evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--historical", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, historical, out = args.repo.resolve(), args.historical.resolve(), args.out.resolve()
    evidence = repo / "evidence/source_probe_crossed_audit_v0"
    result = json.loads((evidence / "SPX_G0_RESULT.json").read_text(encoding="utf-8"))
    audit = json.loads((evidence / "SPX_G0_INDEPENDENT_RECOMPUTATION.json").read_text(encoding="utf-8"))
    if audit["independent_recomputation"] != "PASS" or audit["decision"] != result["decision"]:
        raise RuntimeError("independent verification incomplete")
    branch = subprocess.check_output(["git", "-C", str(repo), "branch", "--show-current"], text=True).strip()
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if branch != "research/source-probe-crossed-audit-20260925":
        raise RuntimeError("wrong branch")
    if subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("review package requires clean committed checkout")
    files: dict[str, Path] = {}
    for file in evidence.iterdir():
        if file.is_file():
            files[file.relative_to(repo).as_posix()] = file
    for file in (repo / "research/source_probe_crossed_audit_v0").iterdir():
        if file.is_file() and file.suffix in {".py", ".md"}:
            files[file.relative_to(repo).as_posix()] = file
    extras = {
        "contracts/gate1a_contract.json": historical / "repo/gate1a_contract.json",
        "contracts/CESS_D1R_PANEL_168.tsv": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv",
        "contracts/NPG_G0_PAIR_DEFINITION.csv": repo / "evidence/neural_population_geometry_v0/g0/NPG_G0_PAIR_DEFINITION.csv",
        "contracts/E1_HOUSE_PROBE_CONTRACTS.tsv": repo / "evidence/environment_level_benchmark_v0/e1/E1_HOUSE_PROBE_CONTRACTS.tsv",
        "contracts/E1_HOUSE_SOURCE_PANELS.tsv": repo / "evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv",
        "historical/CENTRAL_G1A_168x16x10x30.npy": historical / "data/reference_168x16x10x30.npy",
        "historical/E2_REFERENCE_12x10x30.npy": repo / "evidence/jtd_e2_20260925/JTD_E2_REFERENCE_12x10x30.npy",
        "historical/E2_FRESH_TARGET_10x30.npy": repo / "evidence/jtd_e2_20260925/JTD_E2_FRESH_TARGET_10x30.npy",
    }
    files.update(extras)
    for name, file in files.items():
        if not file.is_file():
            raise FileNotFoundError(name)
    if out.exists():
        raise RuntimeError("refuse package overwrite")
    manifest = {"branch": branch, "final_commit": commit, "decision": result["decision"],
                "new_plume_runs": 0, "sealed_data_included": False,
                "raw_cube_payload_included": False,
                "raw_cube_inventory_count": 2784,
                "note": "Review package includes all four crossed compact tensors and exact raw-cube path/SHA inventory. Full raw cubes remain on VM because they exceed compact review-package size.",
                "files": {name: {"bytes": file.stat().st_size, "sha256": digest(file)} for name, file in sorted(files.items())}}
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    sums = [f"{meta['sha256']}  {name}" for name, meta in manifest["files"].items()]
    sums.append(f"{hashlib.sha256(manifest_bytes).hexdigest()}  REVIEW_PACKAGE_MANIFEST.json")
    sums_bytes = ("\n".join(sums) + "\n").encode("utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for name, file in sorted(files.items()):
            archive.write(file, name)
        archive.writestr("REVIEW_PACKAGE_MANIFEST.json", manifest_bytes)
        archive.writestr("SHA256SUMS.txt", sums_bytes)
    with zipfile.ZipFile(out) as archive:
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            expected, name = line.split("  ", 1)
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise RuntimeError(f"ZIP internal SHA mismatch: {name}")
    print(json.dumps({"path": str(out), "bytes": out.stat().st_size, "sha256": digest(out),
                      "final_commit": commit, "decision": result["decision"]}, indent=2))


if __name__ == "__main__":
    main()
