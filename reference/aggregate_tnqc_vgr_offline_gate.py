#!/usr/bin/env python3
"""Aggregate the six frozen VGR/GADEN TNQC fixed-trajectory evaluations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CASES = [
    ("House01", 0), ("House01", 1),
    ("House02", 0), ("House02", 1),
    ("House03", 0), ("House03", 1),
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--min-pooled-improvement", type=float, default=0.10)
    ap.add_argument("--min-improved-pairs", type=int, default=4)
    ap.add_argument("--max-pair-degradation", type=float, default=0.25)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    rows = []
    payloads = {}
    for house, seed in CASES:
        d = args.run_root / f"{house}_seed{seed}_off_off"
        p = load(d / "tnqc_fixed_trajectory_evaluation.json")
        payloads[(house, seed)] = p
        native = float(p["native_exported"]["pmfs_top5_error_m"])
        fused = float(p["tnqc_fused"]["pmfs_top5_error_m"])
        rows.append({
            "house": house,
            "seed": seed,
            "native_error_m": native,
            "tnqc_fused_error_m": fused,
            "improvement_fraction": (native - fused) / max(abs(native), 1e-12),
            "native_reconstruction_pass": bool(
                p.get("native_reconstruction_audit", {}).get("pass", False)),
            "native_cpp_endpoint_pass": bool(
                p.get("native_cpp_endpoint_audit", {}).get("pass", False)),
            "final_leaf_gate_scope_pass":
                p.get("candidate_gate_scope") ==
                "final_partition_leaf_candidates_only",
            "case_valid_for_gate": bool(p.get("valid_for_gate", False)),
            "selected_source_update_id": p["selected_source_update_id"],
            "selected_source_update_sim_time": p["selected_source_update_sim_time"],
            "budget_to_last_update_gap_s": p["budget_to_last_update_gap_s"],
            "total_evaluated_candidate_count":
                p.get("total_evaluated_candidate_count"),
            "final_leaf_candidate_count":
                p.get("final_leaf_candidate_count"),
            "final_leaf_gate": p.get("tnqc_candidate_bank_gate"),
            "all_evaluated_gate_audit":
                p.get("tnqc_all_evaluated_candidate_gate_audit"),
        })

    valid = all(
        r["case_valid_for_gate"]
        and r["native_reconstruction_pass"]
        and r["native_cpp_endpoint_pass"]
        and r["final_leaf_gate_scope_pass"]
        for r in rows)
    native_pooled = sum(r["native_error_m"] for r in rows) / len(rows)
    fused_pooled = sum(r["tnqc_fused_error_m"] for r in rows) / len(rows)
    pooled_gain = (native_pooled - fused_pooled) / max(abs(native_pooled), 1e-12)
    improved = sum(r["tnqc_fused_error_m"] < r["native_error_m"] for r in rows)
    worst_degradation = max(
        (r["tnqc_fused_error_m"] - r["native_error_m"]) /
        max(abs(r["native_error_m"]), 1e-12)
        for r in rows
    )

    false_collapse = []
    for house, seed in CASES:
        m = payloads[(house, seed)]["tnqc_fused"]
        if float(m["variance_m2"]) < 1.0 and float(m["pmfs_top5_error_m"]) > 2.0:
            false_collapse.append(f"{house}_seed{seed}")

    go = (
        valid
        and pooled_gain >= args.min_pooled_improvement
        and improved >= args.min_improved_pairs
        and worst_degradation <= args.max_pair_degradation
        and not false_collapse
    )
    out = {
        "contract": "TNQC_VGR_FIXED_TRAJECTORY_300S_GATE_V2_FINAL_LEAF",
        "cases": rows,
        "pooled_native_error_m": native_pooled,
        "pooled_tnqc_fused_error_m": fused_pooled,
        "pooled_improvement_fraction": pooled_gain,
        "improved_pairs": improved,
        "worst_pair_degradation_fraction": worst_degradation,
        "false_confident_collapse_cases": false_collapse,
        "criteria": {
            "min_pooled_improvement_fraction": args.min_pooled_improvement,
            "min_improved_pairs": args.min_improved_pairs,
            "max_pair_degradation_fraction": args.max_pair_degradation,
            "native_reconstruction_required": True,
            "native_cpp_expected_value_endpoint_match_required": True,
            "final_leaf_gate_scope_required": True,
            "no_false_confident_collapse": True,
        },
        "valid": valid,
        "invalid_reason": None if valid else
            "one_or_more_case_integrity_audits_failed",
        "go_for_closed_loop": go,
        "verdict": "TNQC_VGR_300S_OFFLINE_GO" if go else "TNQC_VGR_300S_OFFLINE_HOLD",
    }
    text = json.dumps(out, indent=2, sort_keys=True)
    print(text)
    target = args.json_out or args.run_root / "tnqc_vgr_300s_offline_gate.json"
    target.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
