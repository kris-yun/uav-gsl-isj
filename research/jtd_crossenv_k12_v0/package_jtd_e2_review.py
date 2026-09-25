#!/usr/bin/env python3
"""Package the frozen JTD-E2 result and only its OPEN-environment inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    evidence = repo / "evidence/jtd_e2_20260925"
    result = json.loads((evidence / "JTD_E2_RESULT.json").read_text(encoding="utf-8"))
    independent = json.loads((evidence / "JTD_E2_INDEPENDENT_RECOMPUTATION.json").read_text(encoding="utf-8"))
    pretarget = json.loads((evidence / "JTD_E2_PRE_TARGET_INDEPENDENT_VERIFICATION.json").read_text(encoding="utf-8"))
    raw = json.loads((evidence / "JTD_E2_RAW_ARCHIVE_VERIFICATION.json").read_text(encoding="utf-8"))
    if (result["decision"] != independent["decision"]
            or independent["independent_recomputation"] != "PASS"
            or pretarget["independent_pre_target_model_refit"] != "PASS"
            or raw["raw_archive_validation"] != "PASS"):
        raise RuntimeError("independent E2 verification incomplete")
    branch = subprocess.check_output(["git", "-C", str(repo), "branch", "--show-current"], text=True).strip()
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if branch != "research/jtd-crossenv-k12-confirmation-v0":
        raise RuntimeError(f"wrong branch: {branch}")
    if subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("review package requires a clean committed checkout")

    files: dict[str, Path] = {}
    for path in evidence.iterdir():
        if path.is_file():
            files[path.relative_to(repo).as_posix()] = path
    for path in (repo / "research/jtd_crossenv_k12_v0").iterdir():
        if path.is_file() and path.suffix in {".py", ".sh", ".md"}:
            files[path.relative_to(repo).as_posix()] = path
    additional = [
        "evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv",
        "evidence/environment_level_benchmark_v0/e1/E1_HOUSE_PROBE_CONTRACTS.tsv",
        "evidence/environment_level_benchmark_v0/e2/E2_OPEN_DISCOVERY_INDEX.tsv",
        "evidence/environment_level_benchmark_v0/e2/E2_OPEN_DISCOVERY_10x30.npy",
        "evidence/jtd_e1_20260925/JTD_E1_TARGET_MANIFEST.tsv",
        "evidence/jtd_e1_20260925/JTD_E1_FRESH_TARGETS_10x30.npy",
        "research/jtd_cross_environment_v0/run_jtd_e1_vm.py",
    ]
    for relative in additional:
        files[relative] = repo / relative
    for name, path in files.items():
        if not path.is_file():
            raise FileNotFoundError(f"{name}: {path}")
    if out.exists():
        raise RuntimeError(f"refusing to overwrite {out}")
    manifest = {
        "branch": branch,
        "final_commit": commit,
        "decision": result["decision"],
        "new_reference_runs": 108,
        "new_fresh_target_runs": 72,
        "independently_verified": True,
        "sealed_house01_dev_or_house03_included": False,
        "files": {name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
                  for name, path in sorted(files.items())},
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    sums = [f"{meta['sha256']}  {name}" for name, meta in manifest["files"].items()]
    sums.append(f"{hashlib.sha256(manifest_bytes).hexdigest()}  REVIEW_PACKAGE_MANIFEST.json")
    sums_bytes = ("\n".join(sums) + "\n").encode("utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for name, path in sorted(files.items()):
            archive.write(path, name)
        archive.writestr("REVIEW_PACKAGE_MANIFEST.json", manifest_bytes)
        archive.writestr("SHA256SUMS.txt", sums_bytes)
    with zipfile.ZipFile(out) as archive:
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            expected, name = line.split("  ", 1)
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise RuntimeError(f"ZIP internal SHA mismatch: {name}")
    print(json.dumps({"path": str(out), "bytes": out.stat().st_size,
                      "sha256": sha256(out), "final_commit": commit,
                      "decision": result["decision"]}, indent=2))


if __name__ == "__main__":
    main()
