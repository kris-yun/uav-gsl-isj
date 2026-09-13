#!/usr/bin/env python3
"""Frozen no-learning gates for synchronized two-receiver plume traces."""

from __future__ import annotations

import argparse
import csv
import gzip
import itertools
import json
from pathlib import Path

import numpy as np


SOURCES = ("S_truth", "S_k01", "S_k10", "S_k22")
DESIGN_WINDS = ("W_fast", "W_slow")
EVAL_WIND = "W_altfast"
HIT_FLOOR_PPM = 0.1
TIME_MISMATCH_SAMPLES = 25  # frozen 5 s window at 0.2 s cadence


def read_trace(path: Path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return {
        "plus": np.asarray([float(row["processed_z_plus_ppm"]) for row in rows]),
        "minus": np.asarray([float(row["processed_z_minus_ppm"]) for row in rows]),
    }


def representation(trace, name, control="CORRECT"):
    plus, minus = trace["plus"].copy(), trace["minus"].copy()
    if control == "MEASUREMENT_POSITION_SWAP":
        plus, minus = minus, plus
    elif control == "TIME_MISMATCH":
        minus = np.roll(minus, TIME_MISMATCH_SAMPLES)
        minus[:TIME_MISMATCH_SAMPLES] = 0.0
    elif control == "COLLAPSED_BASELINE":
        minus = plus.copy()
    if name == "S1_PLUS":
        return plus
    if name == "S1_MINUS":
        return minus
    if name == "ORDINARY_D2":
        return np.concatenate((plus, minus))
    difference = plus - minus
    if name == "SIGNED_INCREMENT":
        return difference
    if name == "SECOND_ORDER_STRUCTURE":
        return difference**2
    raise KeyError(name)


def structural_metrics(matrix):
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    singular = np.linalg.svd(centered, compute_uv=False)
    rank = int(np.linalg.matrix_rank(centered))
    distances = [float(np.linalg.norm(matrix[i] - matrix[j])) for i, j in itertools.combinations(range(4), 2)]
    return {
        "rank": rank,
        "singular_values": singular[:4].tolist(),
        "sigma3_sigma1": float(singular[2] / singular[0]) if singular[0] > 0 and len(singular) >= 3 else 0.0,
        "source_contrast_energy": float(np.sum(centered**2)),
        "minimum_source_pair_distance": min(distances),
        "pairwise_collisions_at_1e_9": sum(distance <= 1e-9 for distance in distances),
    }


def fit_scaler(matrix):
    mean = matrix.mean(axis=0)
    scale = matrix.std(axis=0)
    scale[scale < 1e-12] = 1.0
    return mean, scale


def held_identity(traces, rep_name, eval_control="CORRECT"):
    train_x, train_y = [], []
    for wind in DESIGN_WINDS:
        for source in SOURCES:
            train_x.append(representation(traces[(source, wind)], rep_name))
            train_y.append(source)
    train_x = np.asarray(train_x)
    mean, scale = fit_scaler(train_x)
    train_z = (train_x - mean) / scale
    prototypes = {source: train_z[np.asarray(train_y) == source].mean(axis=0) for source in SOURCES}
    cases = []
    for source in SOURCES:
        test = representation(traces[(source, EVAL_WIND)], rep_name, eval_control)
        test_z = (test - mean) / scale
        distances = {candidate: float(np.linalg.norm(test_z - prototypes[candidate])) for candidate in SOURCES}
        ordered = sorted(SOURCES, key=lambda candidate: (distances[candidate], candidate))
        false = min((candidate for candidate in SOURCES if candidate != source), key=lambda candidate: distances[candidate])
        cases.append({
            "source": source, "predicted": ordered[0], "true_rank": ordered.index(source) + 1,
            "true_distance": distances[source], "best_false_source": false,
            "best_false_distance": distances[false], "margin": distances[false] - distances[source],
        })
    return {
        "representation": rep_name, "evaluation_control": eval_control,
        "design_winds": list(DESIGN_WINDS), "evaluation_wind": EVAL_WIND,
        "distance_rule": "train-only coordinate standardization + nearest two-wind source centroid Euclidean distance",
        "rank1_count": sum(case["true_rank"] == 1 for case in cases),
        "minimum_margin": min(case["margin"] for case in cases),
        "mean_margin": float(np.mean([case["margin"] for case in cases])), "cases": cases,
    }


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    traces = {(source, wind): read_trace(args.trace_dir / f"{source}__{wind}.csv.gz") for source in SOURCES for wind in (*DESIGN_WINDS, EVAL_WIND)}
    representations = ("S1_PLUS", "S1_MINUS", "ORDINARY_D2", "SIGNED_INCREMENT", "SECOND_ORDER_STRUCTURE")
    by_wind = {wind: {} for wind in (*DESIGN_WINDS, EVAL_WIND)}
    for wind in by_wind:
        for name in representations:
            matrix = np.stack([representation(traces[(source, wind)], name) for source in SOURCES])
            metrics = structural_metrics(matrix)
            metrics["exposure_samples_by_source"] = {
                source: int(np.count_nonzero(np.maximum(traces[(source, wind)]["plus"], traces[(source, wind)]["minus"]) > HIT_FLOOR_PPM))
                for source in SOURCES
            }
            metrics["temporal_coverage_by_source"] = {source: count / 750.0 for source, count in metrics["exposure_samples_by_source"].items()}
            metrics["structural_gate"] = "PASS" if metrics["rank"] == 3 and metrics["sigma3_sigma1"] >= 0.05 else "FAIL"
            by_wind[wind][name] = metrics
    observability = {
        "schema": "DUAL_UAV_SOURCE_OBSERVABILITY_BY_WIND_V1", "hit_floor_ppm": HIT_FLOOR_PPM,
        "primary_structure": "SIGNED_INCREMENT", "by_wind": by_wind,
        "primary_all_winds_pass": all(by_wind[wind]["SIGNED_INCREMENT"]["structural_gate"] == "PASS" for wind in by_wind),
    }
    held = {name: held_identity(traces, name) for name in representations}
    held_summary = {
        "schema": "DUAL_UAV_INTERNAL_DEVELOPMENT_HOLDOUT_V1", "status_label": "INTERNAL_DEVELOPMENT_HOLDOUT",
        "primary_structure": "SIGNED_INCREMENT", "representations": held,
        "primary_rank1_gate": "PASS" if held["SIGNED_INCREMENT"]["rank1_count"] == 4 else "FAIL",
    }
    controls = {name: held_identity(traces, "SIGNED_INCREMENT", name) for name in ("MEASUREMENT_POSITION_SWAP", "TIME_MISMATCH", "COLLAPSED_BASELINE")}
    correct = held["SIGNED_INCREMENT"]
    for value in controls.values():
        value["degrades_vs_correct"] = value["rank1_count"] < correct["rank1_count"] or value["minimum_margin"] < correct["minimum_margin"]
    controls_summary = {
        "schema": "DUAL_UAV_DESTRUCTIVE_CONTROLS_V1", "time_mismatch_samples": TIME_MISMATCH_SAMPLES,
        "time_mismatch_seconds": TIME_MISMATCH_SAMPLES * 0.2, "correct_signed_increment": correct,
        "controls": controls, "all_destructive_controls_degrade": all(value["degrades_vs_correct"] for value in controls.values()),
    }
    ordinary, signed = held["ORDINARY_D2"], held["SIGNED_INCREMENT"]
    signed_worst_ratio = min(by_wind[wind]["SIGNED_INCREMENT"]["sigma3_sigma1"] for wind in by_wind)
    ordinary_worst_ratio = min(by_wind[wind]["ORDINARY_D2"]["sigma3_sigma1"] for wind in by_wind)
    comparator = {
        "schema": "DUAL_UAV_ORDINARY_D2_COMPARATOR_V1", "same_two_traces": True,
        "ordinary_d2": ordinary, "signed_increment": signed,
        "worst_wind_sigma3_sigma1": {"ordinary_d2": ordinary_worst_ratio, "signed_increment": signed_worst_ratio},
        "strict_signed_advantage": signed["rank1_count"] >= ordinary["rank1_count"] and signed["minimum_margin"] > ordinary["minimum_margin"] and signed_worst_ratio > ordinary_worst_ratio,
        "rule": "signed must match-or-beat held accuracy and strictly beat both minimum held margin and worst-wind structural ratio",
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    dump(args.out_dir / "SOURCE_OBSERVABILITY_BY_WIND.json", observability)
    dump(args.out_dir / "HELD_WIND_SOURCE_IDENTITY.json", held_summary)
    dump(args.out_dir / "NEGATIVE_CONTROLS.json", controls_summary)
    dump(args.out_dir / "ORDINARY_D2_COMPARATOR.json", comparator)
    if not observability["primary_all_winds_pass"]:
        verdict = "B. STRUCTURAL_COMPLEMENTARITY_ONLY_NO_SOURCE_IDENTITY"
    elif held["SIGNED_INCREMENT"]["rank1_count"] != 4:
        verdict = "B. STRUCTURAL_COMPLEMENTARITY_ONLY_NO_SOURCE_IDENTITY"
    elif not controls_summary["all_destructive_controls_degrade"]:
        verdict = "C. NO_TWO_POINT_ADVANTAGE_OVER_ORDINARY_D2"
    elif not comparator["strict_signed_advantage"]:
        verdict = "C. NO_TWO_POINT_ADVANTAGE_OVER_ORDINARY_D2"
    else:
        verdict = "A. TWO_POINT_PHYSICAL_PREMISE_PASS"
    final = {"schema": "DUAL_UAV_TWO_POINT_FINAL_GATE_V2", "verdict": verdict, "causal_localization_claim": "NOT_AUTHORIZED", "stochastic_ood_claim": False}
    dump(args.out_dir / "FINAL_GATE.json", final)
    print(json.dumps(final))


if __name__ == "__main__":
    main()
