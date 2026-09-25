#!/usr/bin/env python3
"""Create a self-contained, hash-verified NPG-G0 review ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, bank, out = args.repo.resolve(), args.bank.resolve(), args.out.resolve()
    evidence = repo / "evidence/neural_population_geometry_v0/g0"
    result = json.loads((evidence / "NPG_G0_RESULT.json").read_text(encoding="utf-8"))
    audit = json.loads((evidence / "NPG_G0_INDEPENDENT_RECOMPUTATION.json").read_text(encoding="utf-8"))
    if audit["independent_recomputation"] != "PASS" or audit["decision"] != result["decision"]:
        raise RuntimeError("independent audit incomplete")
    branch = subprocess.check_output(["git", "-C", str(repo), "branch", "--show-current"], text=True).strip()
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if branch != "research/neural-population-geometry-g0-20260925":
        raise RuntimeError("wrong branch")
    if subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("package requires clean committed checkout")
    entries: dict[str, Path] = {}
    for file in evidence.iterdir():
        if file.is_file():
            entries[file.relative_to(repo).as_posix()] = file
    for file in (repo / "research/neural_population_geometry_v0").iterdir():
        if file.is_file() and file.suffix in {".py", ".md"}:
            entries[file.relative_to(repo).as_posix()] = file
    extras = {
        "data/reference_168x16x10x30.npy": bank,
        "data/CESS_D1R_PANEL_168.tsv": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv",
        "data/CESS_D1R_REFERENCE_SUMMARY.json": repo / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_REFERENCE_SUMMARY.json",
        "data/JTD_G1A_A0_COMPATIBILITY.json": repo / "evidence/jtd_g1a_20260925/a0/JTD_G1A_A0_COMPATIBILITY.json",
    }
    entries.update(extras)
    for name, file in entries.items():
        if not file.is_file():
            raise FileNotFoundError(name)
    if out.exists():
        raise RuntimeError("refuse to overwrite review ZIP")
    manifest = {"branch": branch, "final_commit": commit, "decision": result["decision"],
                "new_plume_runs": 0, "sealed_data_included": False,
                "files": {name: {"bytes": file.stat().st_size, "sha256": digest(file)} for name, file in sorted(entries.items())}}
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    checks = [f"{info['sha256']}  {name}" for name, info in manifest["files"].items()]
    checks.append(f"{hashlib.sha256(manifest_bytes).hexdigest()}  REVIEW_PACKAGE_MANIFEST.json")
    checks_bytes = ("\n".join(checks) + "\n").encode("utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for name, file in sorted(entries.items()):
            archive.write(file, name)
        archive.writestr("REVIEW_PACKAGE_MANIFEST.json", manifest_bytes)
        archive.writestr("SHA256SUMS.txt", checks_bytes)
    with zipfile.ZipFile(out) as archive:
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            expected, name = line.split("  ", 1)
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise RuntimeError(f"internal package SHA mismatch: {name}")
    print(json.dumps({"path": str(out), "bytes": out.stat().st_size, "sha256": digest(out),
                      "final_commit": commit, "decision": result["decision"]}, indent=2))


if __name__ == "__main__":
    main()
