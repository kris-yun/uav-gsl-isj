#!/usr/bin/env python3
"""Aggregate six frozen GCSI fixed-trajectory counterfactual replays."""
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
    ap.add_argument("--min-pooled-improvement", type=float, default=0.02)
    ap.add_argument("--min-nonworse-pairs", type=int, default=4)
    ap.add_argument("--max-pair-degradation", type=float, default=0.25)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    rows = []
    for house, seed in CASES:
        d = args.run_root / f"{house}_seed{seed}_off_off"
        p = load(d / "gcsi_v1_replay.json")
        native = float(p["endpoint"]["native"]["pmfs_top5_error_m"])
        temp = float(
            p["endpoint"]["scalar_tempered_control"]["pmfs_top5_error_m"])
        gcsi = float(p["endpoint"]["gcsi"]["pmfs_top5_error_m"])
        rows.append({
            "house": house,
            "seed": seed,
            "native_error_m": native,
            "scalar_tempered_error_m": temp,
            "gcsi_error_m": gcsi,
            "gcsi_improvement_fraction":
                (native - gcsi) / max(abs(native), 1e-12),
            "gcsi_vs_scalar_fraction":
                (temp - gcsi) / max(abs(temp), 1e-12),
            "native_reconstruction_l1":
                float(p["native_reconstruction"]["l1"]),
            "native_reconstruction_max_abs":
                float(p["native_reconstruction"]["max_abs"]),
            "block_size_m": float(p["block_size_m"]),
            "scalar_temperature": float(p["scalar_temperature"]),
            "native_best_candidate": p["native_best_candidate"],
            "gcsi_variance_m2":
                float(p["posterior_diagnostics"]["gcsi"]["variance_m2"]),
            "scalar_variance_m2":
                float(p["posterior_diagnostics"]
                      ["scalar_tempered_control"]["variance_m2"]),
        })

    n = len(rows)
    native_mean = sum(r["native_error_m"] for r in rows) / n
    temp_mean = sum(r["scalar_tempered_error_m"] for r in rows) / n
    gcsi_mean = sum(r["gcsi_error_m"] for r in rows) / n
    pooled_gain = (native_mean - gcsi_mean) / max(abs(native_mean), 1e-12)
    vs_temp = (temp_mean - gcsi_mean) / max(abs(temp_mean), 1e-12)
    nonworse = sum(
        r["gcsi_error_m"] <= r["native_error_m"] + 1e-12 for r in rows)
    improved = sum(
        r["gcsi_error_m"] < r["native_error_m"] - 1e-12 for r in rows)
    worst_degradation = max(
        (r["gcsi_error_m"] - r["native_error_m"]) /
        max(abs(r["native_error_m"]), 1e-12)
        for r in rows)

    false_collapse = [
        f'{r["house"]}_seed{r["seed"]}'
        for r in rows
        if r["gcsi_variance_m2"] < 1.0 and r["gcsi_error_m"] > 2.0
    ]
    reconstruction_pass = all(
        r["native_reconstruction_l1"] <= 5e-4
        and r["native_reconstruction_max_abs"] <= 5e-6
        for r in rows)

    go = (
        reconstruction_pass
        and pooled_gain >= args.min_pooled_improvement
        and nonworse >= args.min_nonworse_pairs
        and worst_degradation <= args.max_pair_degradation
        and not false_collapse
        and gcsi_mean < temp_mean
    )

    out = {
        "contract": "GCSI_V1_FIXED_TRAJECTORY_300S_GATE",
        "cases": rows,
        "pooled_native_error_m": native_mean,
        "pooled_scalar_tempered_error_m": temp_mean,
        "pooled_gcsi_error_m": gcsi_mean,
        "pooled_gcsi_improvement_fraction": pooled_gain,
        "pooled_gcsi_vs_scalar_tempered_fraction": vs_temp,
        "improved_pairs": improved,
        "nonworse_pairs": nonworse,
        "worst_pair_degradation_fraction": worst_degradation,
        "false_confident_collapse_cases": false_collapse,
        "native_reconstruction_pass": reconstruction_pass,
        "cheap_screen_criteria": {
            "min_pooled_improvement_fraction": args.min_pooled_improvement,
            "min_nonworse_pairs": args.min_nonworse_pairs,
            "max_pair_degradation_fraction": args.max_pair_degradation,
            "must_beat_scalar_tempered_pooled_error": True,
            "no_false_confident_collapse": True,
        },
        "paper_level_note":
            "The existing stronger >=10% project target remains required for "
            "paper-level promotion unless re-frozen under an independent protocol.",
        "go_for_next_stage": go,
        "verdict":
            "GCSI_V1_300S_STAGE2_GO" if go else "GCSI_V1_300S_HOLD",
    }
    text = json.dumps(out, indent=2, sort_keys=True)
    print(text)
    target = args.json_out or args.run_root / "gcsi_v1_300s_gate.json"
    target.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
