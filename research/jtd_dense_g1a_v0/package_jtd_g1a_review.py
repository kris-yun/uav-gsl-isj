#!/usr/bin/env python3
"""Create independently checkable JTD-G1A review ZIP from frozen evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    repo, inp = a.repo.resolve(), a.input.resolve()
    evidence = repo / "evidence/jtd_g1a_20260925"
    result = json.loads((evidence / "science/JTD_G1A_RESULT.json").read_text(encoding="utf-8"))
    independent = json.loads((evidence / "science/JTD_G1A_INDEPENDENT_RECOMPUTATION.json").read_text(encoding="utf-8"))
    refit = json.loads((evidence / "science/JTD_G1A_INDEPENDENT_MODEL_REFITS.json").read_text(encoding="utf-8"))
    if independent["decision"] != result["decision"] or refit["independent_model_refits"] != "PASS":
        raise RuntimeError("scientific verification incomplete")
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    branch = subprocess.check_output(["git", "-C", str(repo), "branch", "--show-current"], text=True).strip()
    if branch != "research/jtd-dense-g1a-v0":
        raise RuntimeError("wrong branch")
    entries: dict[str, Path] = {}
    for file in evidence.rglob("*"):
        if file.is_file():
            entries[str(file.relative_to(repo)).replace("\\", "/")] = file
    for file in (repo / "research/jtd_dense_g1a_v0").glob("*"):
        if file.is_file() and file.suffix in (".py", ".md"):
            entries[str(file.relative_to(repo)).replace("\\", "/")] = file
    extra = {
        "data/reference_168x16x10x30.npy": inp / "CESS_D1R_REFERENCE_REVIEW_20260925/data/reference_168x16x10x30.npy",
        "data/gate1a_contract.json": inp / "CESS_D1R_REFERENCE_REVIEW_20260925/repo/gate1a_contract.json",
        "data/gate1a_source_bank.tsv": inp / "CESS_D1R_REFERENCE_REVIEW_20260925/repo/source_bank.tsv",
        "data/CESS_D1R_ARTIFACT_SHA256.tsv": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_ARTIFACT_SHA256.tsv",
        "data/CESS_D1R_PANEL_168.tsv": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv",
        "data/R0_SOURCE_PANEL_18.tsv": repo / "research/stochastic_benchmark_refoundation/R0_SOURCE_PANEL_18.tsv",
        "data/G0_R0_INPUT_AUDIT.json": inp / "evidence/jtd_g0_20260925/audit/R0_INPUT_AUDIT.json",
        "data/G0_frozen_config.yaml": inp / "evidence/jtd_g0_20260925/config/frozen_config.yaml",
        "data/G0_run_jtd_g0.py": inp / "research/jtd_g0_20260925/run_jtd_g0.py",
    }
    entries.update(extra)
    for name, file in entries.items():
        if not file.is_file():
            raise FileNotFoundError(f"{name}: {file}")
    manifest = {"branch": branch, "final_commit": commit, "decision": result["decision"],
                "source_count": result["source_count"], "target_count": result["target_count"],
                "new_plume_runs": 0, "sealed_house01_dev_or_house03_data_included": False,
                "file_sha256": {name: sha(file) for name, file in sorted(entries.items())}}
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True)+"\n").encode("utf-8")
    checks = [f"{sha(file)}  {name}" for name, file in sorted(entries.items())]
    checks.append(f"{hashlib.sha256(manifest_bytes).hexdigest()}  REVIEW_PACKAGE_MANIFEST.json")
    checks_bytes = ("\n".join(checks)+"\n").encode("utf-8")
    if a.out.exists():
        raise RuntimeError("refuse overwriting package")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for name, file in sorted(entries.items()):
            z.write(file, name)
        z.writestr("REVIEW_PACKAGE_MANIFEST.json", manifest_bytes)
        z.writestr("SHA256SUMS.txt", checks_bytes)
    with zipfile.ZipFile(a.out) as z:
        for line in z.read("SHA256SUMS.txt").decode().splitlines():
            expected, name = line.split("  ", 1)
            actual = hashlib.sha256(z.read(name)).hexdigest()
            if actual != expected:
                raise RuntimeError(f"ZIP internal SHA mismatch: {name}")
    print(json.dumps({"path": str(a.out), "bytes": a.out.stat().st_size, "sha256": sha(a.out),
                      "final_commit": commit, "decision": result["decision"]}, indent=2))


if __name__ == "__main__":
    main()
