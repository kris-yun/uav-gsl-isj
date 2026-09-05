#!/usr/bin/env python3
"""Create an isolated vgr_bridge overlay with the M1+M2 method identity.

The transform is deliberately identity-only: it adds one entry to the
benchmark runner's canonical-method registry and copies no files back into the
persistent ROS workspace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


OLD_ENTRY = '    "CTPI_CREL_TSDC_PIP": {"algorithm": "PMFS", "type": "proposed", "use_sepf": 0},\n'
NEW_ENTRY = '    "CTPI_G2_M1_M2": {"algorithm": "PMFS", "type": "proposed", "use_sepf": 0},\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-package", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--expected-contract-sha256", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    source = args.source_package.resolve()
    output_root = args.output_root.resolve()
    output_package = output_root / "vgr_bridge"
    contract = source / "result_contract.py"
    runner = source / "gsl_benchmark_runner.py"
    if output_root.exists():
        raise SystemExit(f"CTPI_G2_M12_REFUSE_EXISTING_VGR_OVERLAY={output_root}")
    if not contract.is_file() or not runner.is_file():
        raise SystemExit("CTPI_G2_M12_VGR_BRIDGE_SOURCE_INCOMPLETE")
    before_hash = sha256(contract)
    if before_hash != args.expected_contract_sha256:
        raise SystemExit(
            "CTPI_G2_M12_VGR_BRIDGE_CONTRACT_HASH_MISMATCH="
            f"expected:{args.expected_contract_sha256},actual:{before_hash}"
        )

    shutil.copytree(source, output_package, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    output_contract = output_package / "result_contract.py"
    text = output_contract.read_text(encoding="utf-8")
    if text.count(OLD_ENTRY) != 1 or NEW_ENTRY in text:
        raise SystemExit("CTPI_G2_M12_VGR_BRIDGE_CANONICAL_ANCHOR_MISMATCH")
    output_contract.write_text(text.replace(OLD_ENTRY, OLD_ENTRY + NEW_ENTRY), encoding="utf-8")

    manifest = {
        "verdict": "CTPI_G2_M12_VGR_BRIDGE_OVERLAY_PASS",
        "scope": "canonical method identity only",
        "source_package": str(source),
        "output_root": str(output_root),
        "source_contract_sha256": before_hash,
        "overlay_contract_sha256": sha256(output_contract),
        "source_runner_sha256": sha256(runner),
        "overlay_runner_sha256": sha256(output_package / "gsl_benchmark_runner.py"),
        "added_method": "CTPI_G2_M1_M2",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(manifest["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
