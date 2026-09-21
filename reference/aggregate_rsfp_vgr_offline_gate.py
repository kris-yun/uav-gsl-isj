#!/usr/bin/env python3
"""Aggregate the six frozen RSFP fixed-trajectory evaluations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CASES = [
    ("House01", 0), ("House01", 1),
    ("House02", 0), ("House02", 1),
    ("House03", 0), ("House03", 1),
]
CONTROL_KEYS = ("fine_only", "coarse_only", "mean_only")
PRIMARY_KEY = "fixed_only"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--min-pooled-improvement", type=float, default=0.02)
    ap.add_argument("--min-improved-pairs", type=int, default=4)
    ap.add_argument("--max-pair-degradation", type=float, default=0.25)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    rows = []
    payloads = {}
    for house, seed in CASES:
        d = args.run_root / f"{house}_seed{seed}_off_off"
        p = load(d / "rsfp_fixed_trajectory_evaluation.json")
        payloads[(house, seed)] = p
        native = float(p["native_exported"]["pmfs_top5_error_m"])
        primary = float(
            p["variants"][PRIMARY_KEY]["only"]["pmfs_top5_error_m"]
        )
        controls = {
            k: float(p["variants"][k]["only"]["pmfs_top5_error_m"])
            for k in CONTROL_KEYS
        }
        rows.append({
            "house": house,
            "seed": seed,
            "native_error_m": native,
            "primary_error_m": primary,
            "improvement_fraction":
                (native - primary) / max(abs(native), 1e-12),
            "control_error_m": controls,
            "fixed_tilt_error_m": float(
                p["variants"][PRIMARY_KEY]["tilt"]["pmfs_top5_error_m"]
            ),
            "case_valid_for_gate": bool(p.get("valid_for_gate", False)),
            "replay_contract_pass":
                p.get("contract") ==
                "RSFP_VGR_FIXED_TRAJECTORY_300S_REPLAY_V1",
            "method_pass":
                p.get("method") == "RENORMALIZATION_SOURCE_FIXED_POINT_V1",
            "factors_pass": p.get("factors") == [1, 2, 4, 8],
            "endpoint_engine_pass":
                p.get("endpoint_evaluator", {}).get("engine") ==
                "gsl_utils_expected_value_linked_native_v1"
                and bool(p.get("endpoint_evaluator", {}).get(
                    "engine_integrity_pass", False)),
            "scale_order_stability":
                p.get("scale_order_stability", {}).get("stable_fraction"),
            "active_all_scale_valid_candidate_count":
                p.get("active_all_scale_valid_candidate_count"),
            "final_leaf_candidate_count":
                p.get("final_leaf_candidate_count"),
        })

    valid = all(
        r["case_valid_for_gate"]
        and r["replay_contract_pass"]
        and r["method_pass"]
        and r["factors_pass"]
        and r["endpoint_engine_pass"]
        for r in rows
    )

    native_pooled = sum(r["native_error_m"] for r in rows) / len(rows)
    primary_pooled = sum(r["primary_error_m"] for r in rows) / len(rows)
    pooled_gain = (
        native_pooled - primary_pooled
    ) / max(abs(native_pooled), 1e-12)
    improved = sum(
        r["primary_error_m"] < r["native_error_m"] for r in rows
    )
    worst_degradation = max(
        (r["primary_error_m"] - r["native_error_m"])
        / max(abs(r["native_error_m"]), 1e-12)
        for r in rows
    )

    control_pooled = {
        key: sum(r["control_error_m"][key] for r in rows) / len(rows)
        for key in CONTROL_KEYS
    }
    beats_all_controls = all(
        primary_pooled < control_pooled[key] for key in CONTROL_KEYS
    )

    false_collapse = []
    for house, seed in CASES:
        m = payloads[(house, seed)]["variants"][PRIMARY_KEY]["only"]
        if (
            float(m["variance_m2"]) < 1.0
            and float(m["pmfs_top5_error_m"]) > 2.0
        ):
            false_collapse.append(f"{house}_seed{seed}")

    go = (
        valid
        and pooled_gain >= args.min_pooled_improvement
        and improved >= args.min_improved_pairs
        and worst_degradation <= args.max_pair_degradation
        and not false_collapse
        and beats_all_controls
    )

    out = {
        "contract": "RSFP_VGR_FIXED_TRAJECTORY_300S_GATE_V1",
        "method": "RENORMALIZATION_SOURCE_FIXED_POINT_V1",
        "primary_variant": "fixed_only/only",
        "cases": rows,
        "pooled_native_error_m": native_pooled,
        "pooled_primary_error_m": primary_pooled,
        "pooled_improvement_fraction": pooled_gain,
        "improved_pairs": improved,
        "worst_pair_degradation_fraction": worst_degradation,
        "pooled_control_error_m": control_pooled,
        "primary_beats_all_required_controls": beats_all_controls,
        "false_confident_collapse_cases": false_collapse,
        "criteria": {
            "min_pooled_improvement_fraction":
                args.min_pooled_improvement,
            "min_improved_pairs": args.min_improved_pairs,
            "max_pair_degradation_fraction":
                args.max_pair_degradation,
            "must_beat_fine_only": True,
            "must_beat_coarse_only": True,
            "must_beat_naive_mean_only": True,
            "no_false_confident_collapse": True,
            "frozen_factors": [1, 2, 4, 8],
            "truth_independent_variant_selection": True,
            "linked_native_endpoint_required": True,
        },
        "valid": valid,
        "invalid_reason": None if valid else
            "one_or_more_case_integrity_audits_failed",
        "go_for_closed_loop": go,
        "verdict":
            "RSFP_VGR_300S_OFFLINE_GO"
            if go else "RSFP_VGR_300S_OFFLINE_HOLD",
    }

    text = json.dumps(out, indent=2, sort_keys=True)
    print(text)
    target = args.json_out or args.run_root / "rsfp_vgr_300s_offline_gate.json"
    target.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
