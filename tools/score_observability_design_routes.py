#!/usr/bin/env python3
"""Apply the frozen persistent-excitation route ranking and hard gates."""

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
WINDOWS_S = (5.0, 10.0)
DT = 0.2
HIT_FLOOR = 0.1
CENTER = np.eye(4) - np.ones((4, 4)) / 4.0


def read_response(path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return np.asarray([float(row["processed_sensor_output_ppm"]) for row in rows])


def metrics(matrix):
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


def corrected_q_energy(matrix, window_s):
    width = int(round(window_s / DT)) + 1
    moment = np.zeros((4, 4))
    for start in range(0, matrix.shape[1] - width + 1):
        residual = CENTER @ matrix[:, start : start + width]
        moment += residual @ residual.T
    eigenvalues = np.sort(np.linalg.eigvalsh(0.5 * (moment + moment.T)))[::-1]
    # M_energy is positive semidefinite. Clamp round-off eigenvalues at zero;
    # this cannot turn a failed positive threshold into a pass.
    return max(0.0, float(eigenvalues[2] / eigenvalues[0])) if eigenvalues[0] > 0 else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.candidate_manifest.read_text(encoding="utf-8"))
    path_cost = {item["route_id"]: item["total_absolute_heading_change_rad"] for item in manifest["candidates"]}
    results = []
    for route_id in sorted(path_cost):
        wind_reports = {}
        for wind in WINDS:
            responses = {source: read_response(args.trace_dir / f"{route_id}__{source}__{wind}.csv.gz") for source in SOURCES}
            matrix = np.stack([responses[source] for source in SOURCES])
            report = metrics(matrix)
            report["q_energy"] = {str(window): corrected_q_energy(matrix, window) for window in WINDOWS_S}
            report["maximum_q_energy"] = max(report["q_energy"].values())
            exposure = {}
            for source in SOURCES:
                active = responses[source] > HIT_FLOOR
                thirds = [int(np.count_nonzero(active[first:last])) for first, last in ((0, 250), (250, 500), (500, 750))]
                exposure[source] = {"samples": int(np.count_nonzero(active)), "third_counts": thirds, "exposed_thirds": sum(count > 0 for count in thirds)}
            report["exposure"] = exposure
            report["rank_gate"] = report["rank"] == 3
            report["sigma_gate"] = report["sigma3_sigma1"] >= 0.05
            report["q_energy_gate"] = report["maximum_q_energy"] >= 0.01
            report["collision_gate"] = report["exact_pair_collisions"] == 0
            report["exposure_gate"] = all(item["exposed_thirds"] >= 2 for item in exposure.values())
            report["all_gates"] = all(report[key] for key in ("rank_gate", "sigma_gate", "q_energy_gate", "collision_gate", "exposure_gate"))
            wind_reports[wind] = report
        result = {
            "route_id": route_id,
            "rank3_wind_count": sum(wind_reports[wind]["rank_gate"] for wind in WINDS),
            "worst_design_sigma3_sigma1": min(wind_reports[wind]["sigma3_sigma1"] for wind in WINDS),
            "worst_design_maximum_q_energy": min(wind_reports[wind]["maximum_q_energy"] for wind in WINDS),
            "minimum_source_exposure_samples": min(wind_reports[wind]["exposure"][source]["samples"] for wind in WINDS for source in SOURCES),
            "minimum_exposed_thirds": min(wind_reports[wind]["exposure"][source]["exposed_thirds"] for wind in WINDS for source in SOURCES),
            "total_absolute_heading_change_rad": path_cost[route_id],
            "both_design_winds_all_gates": all(wind_reports[wind]["all_gates"] for wind in WINDS),
            "winds": wind_reports,
        }
        results.append(result)
    results.sort(key=lambda item: (
        -item["rank3_wind_count"], -item["worst_design_sigma3_sigma1"],
        -item["worst_design_maximum_q_energy"], -item["minimum_source_exposure_samples"],
        -item["minimum_exposed_thirds"], item["total_absolute_heading_change_rad"], item["route_id"],
    ))
    passing = [item for item in results if item["both_design_winds_all_gates"]]
    output = {
        "schema": "OBSERVABILITY_FIRST_DESIGN_SCORE_V1",
        "primary_measurement": "S1_CENTER_PROCESSED_FOPDT",
        "design_winds": list(WINDS), "held_wind_read": False,
        "candidate_count": len(results), "passing_candidate_count": len(passing),
        "ranking": [item["route_id"] for item in results],
        "selected_route": passing[0]["route_id"] if passing else None,
        "OBSERVABILITY_FIRST_ROUTE_PREMISE": "PASS" if passing else "NO_GO",
        "results": results,
    }
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: output[key] for key in ("candidate_count", "passing_candidate_count", "selected_route", "OBSERVABILITY_FIRST_ROUTE_PREMISE")}))


if __name__ == "__main__":
    main()
