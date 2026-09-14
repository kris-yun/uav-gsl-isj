#!/usr/bin/env python3
"""Freeze the extended-trace audit and scoring code before aggregate scoring."""

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
    paths = [
        root / "tools/audit_support_extension_traces.py",
        root / "tools/score_support_extension.py",
        root / "tools/audit_occupancy_native_parity.py",
        root / "tools/query_synchronized_pair_from_raw_cache.py",
    ]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing scoring input: {missing}")
    result = {
        "schema": "SUPPORT_EXTENSION_SCORING_POLICY_FREEZE_V1",
        "frozen_before_aggregate_source_separation_scoring": True,
        "code": [{"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256(path)} for path in paths],
        "conditions": {
            "sources": ["S_truth", "S_k01", "S_k10", "S_k22"],
            "design_winds": ["W_fast", "W_slow"],
            "held_wind_read": False,
            "sample_count": 1115,
            "prefix_sample_count": 750,
            "windows_s": [5.0, 10.0],
            "rank_gate": "rank == 3",
            "sigma_gate": "sigma3_sigma1 >= 0.05",
            "q_energy_gate": "maximum_q_energy >= 0.01",
            "collision_gate": "exact_pair_collisions == 0",
            "exposure_gate": "union exposure in at least two equal thirds per source per wind",
            "rich_extension_gate": "full_rich_support_score > own_150s_prefix_score + 1e-15 on both winds",
            "rich_support_score": "sigma3_sigma1 + maximum_q_energy + 0.001*log1p(minimum_pair_distance)",
            "channel_order_preserved": True,
            "channel_difference_used": False,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"policy_sha256": sha256(args.out)}))


if __name__ == "__main__":
    main()
