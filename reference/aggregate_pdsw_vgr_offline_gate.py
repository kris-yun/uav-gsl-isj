#!/usr/bin/env python3
"""Aggregate the six frozen VGR/GADEN PDSW fixed-trajectory evaluations."""
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
        p = load(d / "pdsw_fixed_trajectory_evaluation.json")
        payloads[(house, seed)] = p
        native = float(p["native_exported"]["pmfs_top5_error_m"])
        pdsw = float(p["pdsw"]["pmfs_top5_error_m"])
        rows.append({
            "house": house,
            "seed": seed,
            "native_error_m": native,
            "pdsw_error_m": pdsw,
            "improvement_fraction":
                (native - pdsw) / max(abs(native), 1e-12),
            "native_reconstruction_pass": bool(
                p.get("native_reconstruction_audit", {}).get("pass", False)),
            "native_cpp_endpoint_pass": bool(
                p.get("native_cpp_endpoint_audit", {}).get("pass", False)),
            "cpp_endpoint_engine_pass":
                p.get("endpoint_evaluator", {}).get("engine") ==
                "gsl_utils_expected_value_linked_native_v1"
                and bool(p.get("endpoint_evaluator", {}).get(
                    "engine_integrity_pass", False)),
            "optimizer_converged": bool(
                p.get("optimizer", {}).get("converged", False)),
            "case_valid_for_gate": bool(p.get("valid_for_gate", False)),
            "replay_contract_pass":
                p.get("contract") ==
                "PDSW_VGR_FIXED_TRAJECTORY_300S_REPLAY_V1_LINKED_NATIVE_ENDPOINT",
            "active_final_leaf_candidate_count":
                p.get("active_final_leaf_candidate_count"),
            "source_weight_entropy_nats":
                p.get("source_weight_summary", {}).get("entropy_nats"),
            "source_weight_max":
                p.get("source_weight_summary", {}).get("max_weight"),
            "common_support_fraction":
                p.get("likelihood_support_audit", {}).get(
                    "common_support_fraction"),
        })

    valid = all(
        r["case_valid_for_gate"]
        and r["native_reconstruction_pass"]
        and r["native_cpp_endpoint_pass"]
        and r["cpp_endpoint_engine_pass"]
        and r["optimizer_converged"]
        and r["replay_contract_pass"]
        for r in rows)

    native_pooled = sum(r["native_error_m"] for r in rows) / len(rows)
    pdsw_pooled = sum(r["pdsw_error_m"] for r in rows) / len(rows)
    pooled_gain = (
        native_pooled - pdsw_pooled) / max(abs(native_pooled), 1e-12)
    improved = sum(r["pdsw_error_m"] < r["native_error_m"] for r in rows)
    worst_degradation = max(
        (r["pdsw_error_m"] - r["native_error_m"])
        / max(abs(r["native_error_m"]), 1e-12)
        for r in rows)

    false_collapse = []
    for house, seed in CASES:
        m = payloads[(house, seed)]["pdsw"]
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
        "contract":
            "PDSW_VGR_FIXED_TRAJECTORY_300S_GATE_V1_LINKED_NATIVE_ENDPOINT",
        "cases": rows,
        "pooled_native_error_m": native_pooled,
        "pooled_pdsw_error_m": pdsw_pooled,
        "pooled_improvement_fraction": pooled_gain,
        "improved_pairs": improved,
        "worst_pair_degradation_fraction": worst_degradation,
        "false_confident_collapse_cases": false_collapse,
        "criteria": {
            "min_pooled_improvement_fraction":
                args.min_pooled_improvement,
            "min_improved_pairs": args.min_improved_pairs,
            "max_pair_degradation_fraction":
                args.max_pair_degradation,
            "native_reconstruction_required": True,
            "linked_native_expected_value_engine_required": True,
            "optimizer_convergence_required": True,
            "no_false_confident_collapse": True,
            "same_frozen_native_trajectory_and_candidate_bank_required": True,
        },
        "valid": valid,
        "invalid_reason": None if valid else
            "one_or_more_case_integrity_audits_failed",
        "go_for_closed_loop": go,
        "verdict":
            "PDSW_VGR_300S_OFFLINE_GO"
            if go else "PDSW_VGR_300S_OFFLINE_HOLD",
    }

    text = json.dumps(out, indent=2, sort_keys=True)
    print(text)
    target = args.json_out or args.run_root / "pdsw_vgr_300s_offline_gate.json"
    target.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
