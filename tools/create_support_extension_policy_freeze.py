#!/usr/bin/env python3
"""Create the pre-response policy hash for the support-extension experiment."""

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
    candidate_root = root / "experiments/support_extension_mechanism_v1/candidates"
    manifest_path = candidate_root / "CANDIDATE_MANIFEST.json"
    route_files = sorted(candidate_root.glob("AO_*/*.csv"))
    code_paths = [
        root / "tools/build_support_extension_routes.py",
        root / "tools/build_observability_route_candidates.py",
        root / "tools/build_house02_global_dual_route.py",
        root / "tools/query_sensing_support_design_routes.py",
        root / "tools/audit_sensing_support_upper_bound.py",
        root / "tools/score_sensing_support_upper_bound.py",
        root / "tools/query_synchronized_pair_from_raw_cache.py",
    ]
    contract = root / "docs/CODEX_SUPPORT_EXTENSION_MECHANISM_V1_20260914.md"
    occupancy = root / "_staging/dual_uav_vm_inputs/OccupancyGrid3D.csv"
    winds = [root / "_staging/dual_uav_vm_inputs/W_fast.csv", root / "_staging/dual_uav_vm_inputs/W_slow.csv"]
    if len(route_files) != 36:
        raise RuntimeError(f"expected 36 route CSV files, found {len(route_files)}")
    if not manifest_path.is_file() or not contract.is_file():
        raise RuntimeError("candidate manifest or contract is missing")
    missing = [path for path in [occupancy, *winds, *code_paths] if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing freeze input: {missing}")
    result = {
        "schema": "SUPPORT_EXTENSION_MECHANISM_POLICY_FREEZE_V1",
        "frozen_before_extended_response_query": True,
        "contract": {"path": str(contract.relative_to(root)).replace("\\", "/"), "sha256": sha256(contract)},
        "candidate_manifest": {"path": str(manifest_path.relative_to(root)).replace("\\", "/"), "sha256": sha256(manifest_path)},
        "candidate_route_files": [
            {"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256(path)} for path in route_files
        ],
        "map_and_wind_inputs": [
            {"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256(path)}
            for path in [occupancy, *winds]
        ],
        "code": [
            {"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256(path)} for path in code_paths
        ],
        "frozen_conditions": {
            "house": "House02",
            "sources": ["S_truth", "S_k01", "S_k10", "S_k22"],
            "design_winds": ["W_fast", "W_slow"],
            "forbidden_winds": ["W_altfast", "any_other_wind"],
            "duration_s": 222.8,
            "expected_samples": 1115,
            "cadence_s": 0.2,
            "frame_dt_s": 0.5,
            "frame_min": 0,
            "frame_max": 445,
            "altitude_m": 0.4,
            "speed_mps": 0.35,
            "separation_m": 2.0,
            "fopdt": {"dead_s": 0.4, "rise_s": 1.2, "recovery_s": 1.2, "dt_s": 0.2},
            "receiver_channels": ["plus", "minus"],
            "channel_compression": "NONE_ORDERED_CHANNELS_PRESERVED",
            "raw_cache_mode": "READ_ONLY_PREEXISTING_CACHE_NO_NEW_GADEN",
        },
        "route_selection_provenance": {
            "gas_read": False,
            "raw_cache_read": False,
            "source_identity_or_coordinates_read": False,
            "previous_response_scores_read": False,
            "candidate_count": 12,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"route_files": len(route_files), "policy_sha256": sha256(args.out)}))


if __name__ == "__main__":
    main()
