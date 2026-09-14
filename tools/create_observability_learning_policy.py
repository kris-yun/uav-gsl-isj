#!/usr/bin/env python3
"""Create the pre-model freeze for the observability-learning falsification."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--starting-sha", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    contract = repo / "docs/CODEX_OBSERVABILITY_LEARNING_FALSIFICATION_V1_20260914.md"
    code_paths = [repo / "tools/build_observability_learning_dataset.py", repo / "tools/create_observability_learning_policy.py", repo / "tools/run_observability_learning_falsification.py"]
    trace_paths = sorted((repo / "experiments/sensing_support_upper_bound_v1/endpoint_design_traces").glob("*.csv.gz"))
    if len(trace_paths) != 96:
        raise RuntimeError(f"expected 96 committed C2 traces, found {len(trace_paths)}")
    policy = {
        "schema": "OBSERVABILITY_LEARNING_POLICY_FREEZE_V1",
        "frozen_before_dataset_label_aggregation_and_model_fit": True,
        "policy_authored_from_commit_sha": args.starting_sha,
        "contract": {"path": contract.relative_to(repo).as_posix(), "sha256": sha256_file(contract)},
        "code": [{"path": path.relative_to(repo).as_posix(), "sha256": sha256_file(path)} for path in code_paths],
        "input_trace_files": [{"path": path.relative_to(repo).as_posix(), "sha256": sha256_file(path)} for path in trace_paths],
        "measurement": {"configuration": "C2_D2_TWO_CHANNEL_PROCESSED_FOPDT", "ordered_channels": ["plus", "minus"], "difference": False},
        "teacher_label": {"window_samples": 26, "window_seconds": 5.0, "targets": ["sigma3_sigma1", "q_energy", "log1p_min_pair_distance", "min_source_hit_support"], "hit_floor_ppm": 0.1, "source_centering": "I - 11T/4", "q_energy_roundoff": "clamp_negative_ratio_to_zero"},
        "student_input": {"history": ["processed_c_plus", "processed_c_minus", "mean_endpoint_wind_uvw", "center_xyz", "center_vxyz"], "excludes": ["source_id", "route_id", "source_coordinate", "future_sample", "privileged_label"]},
        "splits": {"train": {"wind": "W_fast", "routes": [f"AO_{i:02d}" for i in range(8)]}, "development": {"wind": "W_fast", "routes": [f"AO_{i:02d}" for i in range(8, 12)]}, "held": {"wind": "W_slow", "routes": [f"AO_{i:02d}" for i in range(8, 12)]}},
        "models": {"scaler": "train_only_standardization", "regressor": "Ridge", "alpha": 1.0, "baselines": ["constant_train_mean", "gas_only", "gas_wind", "full"]},
        "controls": ["time_reverse", "wind_reverse", "motion_zero", "receiver_swap"],
        "promotion_gate": {"rich_targets": ["sigma3_sigma1", "q_energy", "log1p_min_pair_distance"], "held_vs_constant_improvement_min": 0.20, "held_vs_gas_only_improvement_min": 0.10, "development_vs_constant_improvement_min": 0.20, "held_control_degradation_min": 0.05, "receiver_swap_improvement_max": 0.05, "label_std_nonzero": True},
        "forbidden": ["W_altfast", "new_gaden", "source_id_feature", "route_id_feature", "posthoc_split_change", "posthoc_label_change", "posterior", "closed_loop"],
    }
    freeze_path = out_dir / "LEARNING_POLICY_FREEZE.json"
    freeze_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    targets = [contract, *code_paths, *trace_paths, freeze_path]
    lines = [f"{sha256_file(path)}  {path.relative_to(repo).as_posix()}" for path in sorted(targets, key=lambda path: path.relative_to(repo).as_posix())]
    (out_dir / "PRE_MODEL_SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"trace_count": len(trace_paths), "hash_entries": len(lines), "status": "PASS"}))


if __name__ == "__main__":
    main()
