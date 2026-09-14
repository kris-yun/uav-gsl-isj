#!/usr/bin/env python3
"""Record the pre-response geometry failure for the 5 m aperture test."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root
    inputs = [
        root / "docs/CODEX_APERTURE_EXTENSION_MECHANISM_V1_20260914.md",
        root / "tools/build_aperture_extension_routes.py",
        root / "tools/build_support_extension_routes.py",
        root / "_staging/dual_uav_vm_inputs/OccupancyGrid3D.csv",
        root / "_staging/dual_uav_vm_inputs/W_fast.csv",
        root / "_staging/dual_uav_vm_inputs/W_slow.csv",
    ]
    result = {
        "schema": "APERTURE_EXTENSION_GEOMETRY_GATE_V1",
        "candidate_start_search_budget": 24,
        "valid_candidate_count": 0,
        "response_query_started": False,
        "gas_read": False,
        "held_wind_read": False,
        "separation_m": 5.0,
        "duration_s": 222.8,
        "FINAL_VERDICT": "APERTURE_EXTENSION_MECHANISM_NO_GO_GEOMETRY",
        "MAIN_INNOVATION_CLAIM": "NOT_AUTHORIZED",
        "input_hashes": [{"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256(path)} for path in inputs],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
