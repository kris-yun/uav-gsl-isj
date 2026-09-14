#!/usr/bin/env python3
"""Score the frozen extended two-channel source-response support mechanism."""

from __future__ import annotations

import argparse
import csv
import gzip
import itertools
import json
from pathlib import Path

import numpy as np


SOURCES = ("S_truth", "S_k01", "S_k10", "S_k22")
WINDS = ("W_fast", "W_slow")
DT = 0.2
N = 1115
PREFIX_N = 750
WINDOWS_S = (5.0, 10.0)
HIT_FLOOR = 0.1
CENTER = np.eye(4) - np.ones((4, 4)) / 4.0


def read(path: Path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def response_metrics(feature_matrix, sample_n):
    matrix = feature_matrix[:, :sample_n]
    centered = CENTER @ matrix
    singular = np.linalg.svd(centered, compute_uv=False)
    distances = [float(np.linalg.norm(matrix[i] - matrix[j])) for i, j in itertools.combinations(range(4), 2)]
    return {
        "rank": int(np.linalg.matrix_rank(centered)),
        "singular_values": singular[:4].tolist(),
        "sigma3_sigma1": float(singular[2] / singular[0]) if singular[0] > 0 else 0.0,
        "minimum_pair_distance": min(distances),
        "exact_pair_collisions": sum(distance == 0.0 for distance in distances),
    }


def q_energy(channel_matrices, sample_n, window_s):
    width = int(round(window_s / DT)) + 1
    moment = np.zeros((4, 4))
    for start in range(0, sample_n - width + 1):
        for channel_matrix in channel_matrices:
            residual = CENTER @ channel_matrix[:, start : start + width]
            moment += residual @ residual.T
    eigenvalues = np.sort(np.linalg.eigvalsh(0.5 * (moment + moment.T)))[::-1]
    raw = float(eigenvalues[2] / eigenvalues[0]) if eigenvalues[0] > 0 else 0.0
    return {"raw_ratio": raw, "corrected_ratio": max(0.0, raw), "eigenvalues": eigenvalues.tolist(), "psd_roundoff_clamped": raw < 0.0}


def thirds(active, sample_n):
    bounds = (0, sample_n // 3, (2 * sample_n) // 3, sample_n)
    counts = [int(np.count_nonzero(active[bounds[i]:bounds[i + 1]])) for i in range(3)]
    return {"samples": int(np.count_nonzero(active[:sample_n])), "third_counts": counts, "exposed_thirds": sum(count > 0 for count in counts)}


def measure(source_arrays, sample_n):
    plus = source_arrays["plus_processed"][:sample_n] > HIT_FLOOR
    minus = source_arrays["minus_processed"][:sample_n] > HIT_FLOOR
    union = np.logical_or(plus, minus)
    overlap = np.logical_and(plus, minus)
    return {
        "plus": thirds(plus, sample_n), "minus": thirds(minus, sample_n), "union": thirds(union, sample_n),
        "overlap": thirds(overlap, sample_n),
        "plus_only_samples": int(np.count_nonzero(np.logical_and(plus, np.logical_not(minus)))),
        "minus_only_samples": int(np.count_nonzero(np.logical_and(minus, np.logical_not(plus)))),
    }


def one_wind(route_id, wind, trace_dir, sample_n):
    by_source = {}
    for source in SOURCES:
        rows = read(trace_dir / f"{route_id}__{source}__{wind}.csv.gz")
        if len(rows) != N:
            raise RuntimeError(f"unexpected rows in {route_id}/{source}/{wind}: {len(rows)}")
        by_source[source] = {
            "plus_processed": np.asarray([float(row["processed_c_plus_ppm"]) for row in rows]),
            "minus_processed": np.asarray([float(row["processed_c_minus_ppm"]) for row in rows]),
        }
    channel_matrices = [np.stack([by_source[source][channel] for source in SOURCES]) for channel in ("plus_processed", "minus_processed")]
    feature_matrix = np.concatenate([matrix[:, :sample_n] for matrix in channel_matrices], axis=1)
    report = response_metrics(feature_matrix, sample_n)
    report["q_energy"] = {str(window): q_energy(channel_matrices, sample_n, window) for window in WINDOWS_S}
    report["maximum_q_energy"] = max(item["corrected_ratio"] for item in report["q_energy"].values())
    report["exposure"] = {source: measure(by_source[source], sample_n) for source in SOURCES}
    report["rank_gate"] = report["rank"] == 3
    report["sigma_gate"] = report["sigma3_sigma1"] >= 0.05
    report["q_energy_gate"] = report["maximum_q_energy"] >= 0.01
    report["collision_gate"] = report["exact_pair_collisions"] == 0
    report["exposure_gate"] = all(report["exposure"][source]["union"]["exposed_thirds"] >= 2 for source in SOURCES)
    report["rich_support_score"] = report["sigma3_sigma1"] + report["maximum_q_energy"] + 0.001 * float(np.log1p(report["minimum_pair_distance"]))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.candidate_manifest.read_text(encoding="utf-8"))
    path_cost = {item["route_id"]: item["total_absolute_heading_change_rad"] for item in manifest["candidates"]}
    results = []
    for route_id in sorted(path_cost):
        winds = {}
        for wind in WINDS:
            prefix = one_wind(route_id, wind, args.trace_dir, PREFIX_N)
            full = one_wind(route_id, wind, args.trace_dir, N)
            full["prefix_150s"] = prefix
            full["rich_extension_gain"] = full["rich_support_score"] - prefix["rich_support_score"]
            full["rich_extension_gate"] = full["rich_extension_gain"] > 1e-15
            full["all_gates"] = all(full[key] for key in ("rank_gate", "sigma_gate", "q_energy_gate", "collision_gate", "exposure_gate", "rich_extension_gate"))
            winds[wind] = full
        item = {
            "route_id": route_id,
            "rank3_wind_count": sum(winds[wind]["rank_gate"] for wind in WINDS),
            "worst_design_sigma3_sigma1": min(winds[wind]["sigma3_sigma1"] for wind in WINDS),
            "worst_design_maximum_q_energy": min(winds[wind]["maximum_q_energy"] for wind in WINDS),
            "minimum_source_exposure_samples": min(winds[wind]["exposure"][source]["union"]["samples"] for wind in WINDS for source in SOURCES),
            "minimum_exposed_thirds": min(winds[wind]["exposure"][source]["union"]["exposed_thirds"] for wind in WINDS for source in SOURCES),
            "total_absolute_heading_change_rad": path_cost[route_id],
            "both_design_winds_all_gates": all(winds[wind]["all_gates"] for wind in WINDS),
            "winds": winds,
        }
        results.append(item)
    results.sort(key=lambda item: (-item["rank3_wind_count"], -item["worst_design_sigma3_sigma1"], -item["worst_design_maximum_q_energy"], -item["minimum_source_exposure_samples"], -item["minimum_exposed_thirds"], item["total_absolute_heading_change_rad"], item["route_id"]))
    passing = [item for item in results if item["both_design_winds_all_gates"]]
    report = {
        "schema": "SUPPORT_EXTENSION_SCORE_V1",
        "measurement": "D2_TWO_CHANNEL_PROCESSED_FOPDT",
        "design_winds": list(WINDS),
        "held_wind_read": False,
        "candidate_count": len(results),
        "passing_candidate_count": len(passing),
        "passing_routes": [item["route_id"] for item in passing],
        "ranking": [item["route_id"] for item in results],
        "selected_route": passing[0]["route_id"] if passing else None,
        "configuration_gate": "PASS" if passing else "NO_GO_0_OF_12",
        "rich_support_score_definition": "sigma3_sigma1 + maximum_q_energy + 0.001*log1p(minimum_pair_distance)",
        "results": results,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "SUPPORT_EXTENSION_SCORE.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    final = {
        "schema": "SUPPORT_EXTENSION_MECHANISM_FINAL_GATE_V1",
        "TRACE_INTEGRITY": "PENDING",
        "EXTENDED_C2_PROCESSED_FOPDT": report["configuration_gate"],
        "SELECTED_ROUTE": report["selected_route"],
        "DESIGN_WIND_PASSING_ROUTES": report["passing_routes"],
        "HELD_WIND_STATUS": "NOT_RUN_NOT_READ",
        "MAIN_INNOVATION_CLAIM": "NOT_AUTHORIZED",
        "FINAL_VERDICT": "SUPPORT_EXTENSION_MECHANISM_PASS_LOAD_BEARING_ONLY" if passing else "SUPPORT_EXTENSION_MECHANISM_NO_GO",
    }
    (args.out_dir / "FINAL_GATE.json").write_text(json.dumps(final, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(final))


if __name__ == "__main__":
    main()
