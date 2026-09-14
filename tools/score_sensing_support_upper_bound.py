#!/usr/bin/env python3
"""Score the four precommitted sensing-support configurations on design winds."""

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
CONFIGURATIONS = {
    "C0": {"name": "S1_CENTER_PROCESSED_FOPDT", "channels": ("center_processed",), "deployable": True, "reference": True},
    "C1": {"name": "S1_CENTER_RAW_ORACLE", "channels": ("center_raw",), "deployable": False, "oracle": True},
    "C2": {"name": "D2_TWO_CHANNEL_PROCESSED_FOPDT", "channels": ("plus_processed", "minus_processed"), "deployable": True},
    "C3": {"name": "D2_TWO_CHANNEL_RAW_ORACLE", "channels": ("plus_raw", "minus_raw"), "deployable": False, "oracle": True},
}


def read_gzip_csv(path: Path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def read_center(path: Path):
    rows = read_gzip_csv(path)
    return {
        "center_processed": np.asarray([float(row["processed_sensor_output_ppm"]) for row in rows]),
        "center_raw": np.asarray([float(row["raw_gas_concentration_ppm"]) for row in rows]),
    }


def read_endpoints(path: Path):
    rows = read_gzip_csv(path)
    return {
        "plus_processed": np.asarray([float(row["processed_c_plus_ppm"]) for row in rows]),
        "minus_processed": np.asarray([float(row["processed_c_minus_ppm"]) for row in rows]),
        "plus_raw": np.asarray([float(row["raw_c_plus_ppm"]) for row in rows]),
        "minus_raw": np.asarray([float(row["raw_c_minus_ppm"]) for row in rows]),
    }


def source_response_metrics(feature_matrix):
    centered = CENTER @ feature_matrix
    singular = np.linalg.svd(centered, compute_uv=False)
    distances = [float(np.linalg.norm(feature_matrix[i] - feature_matrix[j])) for i, j in itertools.combinations(range(4), 2)]
    return {
        "rank": int(np.linalg.matrix_rank(centered)),
        "singular_values": singular[:4].tolist(),
        "sigma3_sigma1": float(singular[2] / singular[0]) if singular[0] > 0 else 0.0,
        "minimum_pair_distance": min(distances),
        "exact_pair_collisions": sum(distance == 0.0 for distance in distances),
    }


def corrected_q_energy(channel_matrices, window_s):
    width = int(round(window_s / DT)) + 1
    moment = np.zeros((4, 4))
    sample_count = channel_matrices[0].shape[1]
    for start in range(0, sample_count - width + 1):
        for channel_matrix in channel_matrices:
            residual = CENTER @ channel_matrix[:, start : start + width]
            moment += residual @ residual.T
    eigenvalues = np.sort(np.linalg.eigvalsh(0.5 * (moment + moment.T)))[::-1]
    raw_ratio = float(eigenvalues[2] / eigenvalues[0]) if eigenvalues[0] > 0 else 0.0
    return {
        "raw_ratio": raw_ratio,
        "corrected_ratio": max(0.0, raw_ratio),
        "eigenvalues": eigenvalues.tolist(),
        "psd_roundoff_clamped": raw_ratio < 0.0,
    }


def temporal_counts(active):
    thirds = [int(np.count_nonzero(active[first:last])) for first, last in ((0, 250), (250, 500), (500, 750))]
    return {"samples": int(np.count_nonzero(active)), "third_counts": thirds, "exposed_thirds": sum(count > 0 for count in thirds)}


def exposure_report(source_channels, config_id):
    if config_id in ("C0", "C1"):
        channel = "center_processed" if config_id == "C0" else "center_raw"
        return {"center": temporal_counts(source_channels[channel] > HIT_FLOOR)}
    suffix = "processed" if config_id == "C2" else "raw"
    plus = source_channels[f"plus_{suffix}"] > HIT_FLOOR
    minus = source_channels[f"minus_{suffix}"] > HIT_FLOOR
    union = np.logical_or(plus, minus)
    overlap = np.logical_and(plus, minus)
    return {
        "plus": temporal_counts(plus),
        "minus": temporal_counts(minus),
        "union": temporal_counts(union),
        "overlap": temporal_counts(overlap),
        "plus_only_samples": int(np.count_nonzero(np.logical_and(plus, np.logical_not(minus)))),
        "minus_only_samples": int(np.count_nonzero(np.logical_and(minus, np.logical_not(plus)))),
    }


def score_configuration(config_id, center_trace_dir, endpoint_trace_dir, path_cost):
    definition = CONFIGURATIONS[config_id]
    results = []
    for route_id in sorted(path_cost):
        winds = {}
        for wind in WINDS:
            by_source = {}
            for source in SOURCES:
                channels = {}
                if any(name.startswith("center_") for name in definition["channels"]):
                    channels.update(read_center(center_trace_dir / f"{route_id}__{source}__{wind}.csv.gz"))
                if any(name.startswith(("plus_", "minus_")) for name in definition["channels"]):
                    channels.update(read_endpoints(endpoint_trace_dir / f"{route_id}__{source}__{wind}.csv.gz"))
                by_source[source] = channels
            channel_matrices = [np.stack([by_source[source][channel] for source in SOURCES]) for channel in definition["channels"]]
            feature_matrix = np.concatenate(channel_matrices, axis=1)
            report = source_response_metrics(feature_matrix)
            q_reports = {str(window): corrected_q_energy(channel_matrices, window) for window in WINDOWS_S}
            report["q_energy"] = q_reports
            report["maximum_q_energy"] = max(item["corrected_ratio"] for item in q_reports.values())
            exposure = {source: exposure_report(by_source[source], config_id) for source in SOURCES}
            report["exposure"] = exposure
            exposure_key = "center" if config_id in ("C0", "C1") else "union"
            report["rank_gate"] = report["rank"] == 3
            report["sigma_gate"] = report["sigma3_sigma1"] >= 0.05
            report["q_energy_gate"] = report["maximum_q_energy"] >= 0.01
            report["collision_gate"] = report["exact_pair_collisions"] == 0
            report["exposure_gate"] = all(exposure[source][exposure_key]["exposed_thirds"] >= 2 for source in SOURCES)
            report["all_gates"] = all(report[key] for key in ("rank_gate", "sigma_gate", "q_energy_gate", "collision_gate", "exposure_gate"))
            winds[wind] = report
        exposure_key = "center" if config_id in ("C0", "C1") else "union"
        item = {
            "route_id": route_id,
            "rank3_wind_count": sum(winds[wind]["rank_gate"] for wind in WINDS),
            "worst_design_sigma3_sigma1": min(winds[wind]["sigma3_sigma1"] for wind in WINDS),
            "worst_design_maximum_q_energy": min(winds[wind]["maximum_q_energy"] for wind in WINDS),
            "minimum_source_exposure_samples": min(winds[wind]["exposure"][source][exposure_key]["samples"] for wind in WINDS for source in SOURCES),
            "minimum_exposed_thirds": min(winds[wind]["exposure"][source][exposure_key]["exposed_thirds"] for wind in WINDS for source in SOURCES),
            "total_absolute_heading_change_rad": path_cost[route_id],
            "both_design_winds_all_gates": all(winds[wind]["all_gates"] for wind in WINDS),
            "winds": winds,
        }
        results.append(item)
    results.sort(key=lambda item: (
        -item["rank3_wind_count"], -item["worst_design_sigma3_sigma1"],
        -item["worst_design_maximum_q_energy"], -item["minimum_source_exposure_samples"],
        -item["minimum_exposed_thirds"], item["total_absolute_heading_change_rad"], item["route_id"],
    ))
    passing = [item for item in results if item["both_design_winds_all_gates"]]
    return {
        "schema": "SENSING_SUPPORT_CONFIGURATION_SCORE_V1",
        "configuration_id": config_id,
        "measurement": definition["name"],
        "channels": list(definition["channels"]),
        "channel_order_preserved": config_id in ("C2", "C3"),
        "channel_difference_used": False,
        "deployable_candidate_eligible": config_id == "C2",
        "oracle_only": config_id in ("C1", "C3"),
        "design_winds": list(WINDS),
        "held_wind_read": False,
        "candidate_count": len(results),
        "passing_candidate_count": len(passing),
        "passing_routes": [item["route_id"] for item in passing],
        "ranking": [item["route_id"] for item in results],
        "selected_route": passing[0]["route_id"] if passing else None,
        "configuration_gate": "PASS" if passing else "NO_GO_0_OF_12",
        "results": results,
    }


def compare_c0_to_reference(c0, reference):
    failures = []
    reference_by_route = {item["route_id"]: item for item in reference["results"]}
    for item in c0["results"]:
        prior = reference_by_route[item["route_id"]]
        for field in ("rank3_wind_count", "minimum_source_exposure_samples", "minimum_exposed_thirds", "both_design_winds_all_gates"):
            if item[field] != prior[field]:
                failures.append(f"{item['route_id']}:{field}")
        for field in ("worst_design_sigma3_sigma1", "worst_design_maximum_q_energy"):
            if abs(item[field] - prior[field]) > 1e-15:
                failures.append(f"{item['route_id']}:{field}")
        for wind in WINDS:
            now, old = item["winds"][wind], prior["winds"][wind]
            for field in ("rank", "exact_pair_collisions", "rank_gate", "sigma_gate", "q_energy_gate", "collision_gate", "exposure_gate", "all_gates"):
                if now[field] != old[field]:
                    failures.append(f"{item['route_id']}:{wind}:{field}")
            for field in ("sigma3_sigma1", "minimum_pair_distance", "maximum_q_energy"):
                if abs(now[field] - old[field]) > 1e-15:
                    failures.append(f"{item['route_id']}:{wind}:{field}")
    return {
        "reference_schema": reference["schema"],
        "reference_passing_candidate_count": reference["passing_candidate_count"],
        "reproduced_passing_candidate_count": c0["passing_candidate_count"],
        "comparison_tolerance": 1e-15,
        "failure_count": len(failures),
        "first_failures": failures[:20],
        "status": "PASS" if not failures and c0["ranking"] == reference["ranking"] else "FAIL",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--center-trace-dir", type=Path, required=True)
    parser.add_argument("--endpoint-trace-dir", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--reference-score", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.candidate_manifest.read_text(encoding="utf-8"))
    path_cost = {item["route_id"]: item["total_absolute_heading_change_rad"] for item in manifest["candidates"]}
    scores = {config_id: score_configuration(config_id, args.center_trace_dir, args.endpoint_trace_dir, path_cost) for config_id in CONFIGURATIONS}
    reference = json.loads(args.reference_score.read_text(encoding="utf-8"))
    c0_comparison = compare_c0_to_reference(scores["C0"], reference)
    scores["C0"]["reference_reproduction"] = c0_comparison

    filenames = {
        "C0": "C0_REFERENCE_REPRODUCTION.json",
        "C1": "C1_CENTER_RAW_ORACLE.json",
        "C2": "C2_D2_PROCESSED_FOPDT.json",
        "C3": "C3_D2_RAW_ORACLE.json",
    }
    for config_id, filename in filenames.items():
        (args.out_dir / filename).write_text(json.dumps(scores[config_id], indent=2) + "\n", encoding="utf-8")

    passing = {config_id: scores[config_id]["passing_candidate_count"] > 0 for config_id in ("C1", "C2", "C3")}
    if passing["C2"]:
        attribution = "MULTICHANNEL_MEASUREMENT_GEOMETRY_IS_LOAD_BEARING_CANDIDATE"
        final_verdict = attribution
        deployable_status = f"FREEZE_REQUIRED_{scores['C2']['selected_route']}"
    elif passing["C1"] and not passing["C2"]:
        attribution = "SENSOR_RESPONSE_DYNAMICS_IS_PRIMARY_BOTTLENECK_SUPPORTED"
        final_verdict = attribution
        deployable_status = "NONE_C2_NO_GO"
    elif passing["C3"] and not passing["C1"] and not passing["C2"]:
        attribution = "JOINT_GEOMETRY_AND_SENSOR_DYNAMICS_LIMITATION_SUPPORTED"
        final_verdict = attribution
        deployable_status = "NONE_C2_NO_GO"
    elif not any(passing.values()):
        attribution = "SENSING_SUPPORT_150S_PREMISE = NO_GO"
        final_verdict = "SENSING_SUPPORT_150S_PREMISE_NO_GO"
        deployable_status = "NONE_C2_NO_GO"
    else:
        attribution = "MULTIPLE_DIAGNOSTIC_CONFIGURATIONS_PASS_REPORTED_WITHOUT_SUPPRESSION"
        final_verdict = attribution
        deployable_status = "NONE_C2_NO_GO"

    comparison = {
        "schema": "SENSING_SUPPORT_CONFIGURATION_COMPARISON_V1",
        "design_winds": list(WINDS),
        "held_wind_read": False,
        "configurations": {
            config_id: {
                "measurement": scores[config_id]["measurement"],
                "passing_candidate_count": scores[config_id]["passing_candidate_count"],
                "passing_routes": scores[config_id]["passing_routes"],
                "selected_route": scores[config_id]["selected_route"],
                "configuration_gate": scores[config_id]["configuration_gate"],
            }
            for config_id in CONFIGURATIONS
        },
        "all_passing_diagnostic_configurations": [config_id for config_id in ("C1", "C2", "C3") if passing[config_id]],
        "PRIMARY_BOTTLENECK_ATTRIBUTION": attribution,
        "DEPLOYABLE_C2_ROUTE_STATUS": deployable_status,
    }
    (args.out_dir / "CONFIGURATION_COMPARISON.json").write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")

    final_gate = {
        "schema": "SENSING_SUPPORT_UPPER_BOUND_FINAL_GATE_V1",
        "TRACE_INTEGRITY": "PENDING_EXTERNAL_AUDIT",
        "C0_REFERENCE_REPRODUCTION": c0_comparison["status"],
        "C1_CENTER_RAW_ORACLE": scores["C1"]["configuration_gate"],
        "C2_D2_PROCESSED_FOPDT": scores["C2"]["configuration_gate"],
        "C3_D2_RAW_ORACLE": scores["C3"]["configuration_gate"],
        "PRIMARY_BOTTLENECK_ATTRIBUTION": attribution,
        "DEPLOYABLE_C2_ROUTE_STATUS": deployable_status,
        "HELD_WIND_STATUS": "NOT_RUN_NOT_READ",
        "FINAL_VERDICT": final_verdict,
        "causal_localization_claim": "NOT_AUTHORIZED",
        "cross_dataset_claim": "NOT_AUTHORIZED",
        "main_innovation_claim": "NOT_AUTHORIZED",
    }
    (args.out_dir / "FINAL_GATE.json").write_text(json.dumps(final_gate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(final_gate))


if __name__ == "__main__":
    main()
