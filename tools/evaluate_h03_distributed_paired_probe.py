#!/usr/bin/env python3
"""Evaluate the frozen distributed paired-intervention H03 premise."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from screen_h03_paired_position_premise import (
    candidate_support,
    predict_all,
    profiled_losses,
    rank_interval,
)


SOURCES = ("SA", "HF")
TRANSPORTS = ("fast", "slow")
NATIVE_GAS_THRESHOLD_PPM = 0.1


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def cosine(left: np.ndarray, right: np.ndarray) -> float | None:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return None if denominator == 0.0 else float(left @ right / denominator)


def station_profiled_loss(observed: np.ndarray, predicted: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Profile one positive scale at a station and normalize by observed energy."""
    loss, amplitude = profiled_losses(observed, predicted)
    energy = float(observed @ observed)
    if energy <= 0.0:
        raise ValueError("ZERO_ACTIVE_STATION_ENERGY")
    return loss / energy, amplitude


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    raw_root = args.raw_root.resolve()
    route_rule_path = repo / "evidence/m1r_h03_distributed_intervention_20260913/route/ROUTE_RULE.json"
    candidate_path = repo / "evidence/cstar_current_runtime_assets240_20260907/maps/H03/candidate.csv"
    loho_path = repo / "evidence/cstar_joint_development_20260908/CROSSED_PLUME_LOHO_SIGN.json"
    route_rule = json.loads(route_rule_path.read_text(encoding="utf-8"))
    loho = json.loads(loho_path.read_text(encoding="utf-8"))
    parameter = next(fold["selected_parameter"] for fold in loho["folds"]
                     if fold["heldout_house"] == "H03")
    candidates = candidate_support(candidate_path)

    histories = {(source, transport): read_jsonl(raw_root / f"H03_{source}_{transport}/measured_history.jsonl")
                 for source in SOURCES for transport in TRANSPORTS}
    manifests = {(source, transport): json.loads(
        (raw_root / f"H03_{source}_{transport}/CASE_MANIFEST.json").read_text(encoding="utf-8"))
        for source in SOURCES for transport in TRANSPORTS}
    truth_xy = {source: np.asarray(manifests[(source, "fast")]["source_xyz_m_evaluator_only"][:2], dtype=float)
                for source in SOURCES}
    reference = histories[("SA", "fast")]
    signature = [(row["stamp_ns"], row["pose_xy"]) for row in reference]
    route_equal = all([(row["stamp_ns"], row["pose_xy"]) for row in history] == signature
                      for history in histories.values())
    wind_equal = all([row["wind_uv"] for row in histories[("SA", transport)]]
                     == [row["wind_uv"] for row in histories[("HF", transport)]]
                     for transport in TRANSPORTS)
    if not route_equal or not wind_equal:
        raise ValueError("DISTRIBUTED_CROSSED_CONTEXT_ALIGNMENT_FAILED")
    step_ns = {right["stamp_ns"] - left["stamp_ns"] for left, right in zip(reference, reference[1:])}
    if len(step_ns) != 1:
        raise ValueError("DISTRIBUTED_HISTORY_CADENCE")
    dt_s = step_ns.pop() / 1e9

    station_indices = []
    station_weights = []
    station_raw_indices = []
    for station in route_rule["stations"]:
        indices = [np.asarray(pair["endpoint_route_indices_zero_based"], dtype=int) - 1
                   for pair in station["pairs"]]
        weights = [np.asarray(pair["contrast_weights"], dtype=float) for pair in station["pairs"]]
        station_indices.append(indices)
        station_weights.append(weights)
        station_raw_indices.append(np.concatenate(indices))

    def observed_station(source: str, transport: str, station_id: int) -> tuple[np.ndarray, np.ndarray, bool]:
        gas = np.asarray([row["gas_ppm"] for row in histories[(source, transport)]], dtype=float)
        indices = station_indices[station_id]
        contrast = np.asarray([weight @ gas[index]
                               for weight, index in zip(station_weights[station_id], indices)])
        raw = gas[station_raw_indices[station_id]]
        active = bool(np.max(raw) > NATIVE_GAS_THRESHOLD_PPM)
        return contrast, raw, active

    predictions = {transport: predict_all(histories[("SA", transport)], candidates, parameter, dt_s)
                   for transport in TRANSPORTS}
    predicted_station = {}
    predicted_raw_station = {}
    for transport in TRANSPORTS:
        for station_id in range(len(station_indices)):
            predicted_station[(transport, station_id)] = np.stack([
                weight @ predictions[transport][index]
                for weight, index in zip(station_weights[station_id], station_indices[station_id])
            ])
            predicted_raw_station[(transport, station_id)] = predictions[transport][station_raw_indices[station_id]]

    nearest = {source: int(np.argmin(np.linalg.norm(candidates - truth_xy[source], axis=1))) for source in SOURCES}
    evaluations = []
    observed_cache = {}
    for transport in TRANSPORTS:
        for source in SOURCES:
            paired_total = np.zeros(len(candidates), dtype=float)
            raw_total = np.zeros(len(candidates), dtype=float)
            single_station = []
            active_stations = []
            station_detail = []
            for station_id in range(len(station_indices)):
                observed, raw, active = observed_station(source, transport, station_id)
                observed_cache[(source, transport, station_id)] = observed
                detail = {
                    "station_id": station_id + 1,
                    "active_by_native_0p1ppm": active,
                    "max_endpoint_ppm": float(np.max(raw)),
                    "observed_contrast_ppm": observed.tolist(),
                }
                if active:
                    active_stations.append(station_id)
                    paired_loss, amplitude = station_profiled_loss(
                        observed, predicted_station[(transport, station_id)])
                    raw_loss, _ = station_profiled_loss(
                        raw, predicted_raw_station[(transport, station_id)])
                    paired_total += paired_loss
                    raw_total += raw_loss
                    truth_station_rank = rank_interval(paired_loss, nearest[source])
                    single_station.append(truth_station_rank)
                    detail.update({
                        "truth_rank_interval_paired": truth_station_rank,
                        "truth_profiled_amplitude": float(amplitude[nearest[source]]),
                    })
                station_detail.append(detail)
            if active_stations:
                truth_paired_rank = rank_interval(paired_total, nearest[source])
                truth_raw_rank = rank_interval(raw_total, nearest[source])
                best_index = int(np.argmin(paired_total))
            else:
                truth_paired_rank = [1, len(candidates)]
                truth_raw_rank = [1, len(candidates)]
                best_index = 0
            evaluations.append({
                "actual_source": source,
                "transport": transport,
                "active_station_count": len(active_stations),
                "active_station_ids": [index + 1 for index in active_stations],
                "station_detail": station_detail,
                "truth_xy_evaluator_only": truth_xy[source].tolist(),
                "truth_nearest_candidate_xy": candidates[nearest[source]].tolist(),
                "truth_rank_interval_distributed_paired": truth_paired_rank,
                "truth_rank_interval_same_endpoint_raw": truth_raw_rank,
                "single_active_station_truth_ranks": single_station,
                "best_candidate_xy": candidates[best_index].tolist(),
                "best_candidate_error_to_truth_m": float(np.linalg.norm(candidates[best_index] - truth_xy[source])),
            })

    observed_source_difference = {}
    predicted_source_difference = {}
    provider_cosine = {}
    for transport in TRANSPORTS:
        observed_source_difference[transport] = np.concatenate([
            observed_cache[("SA", transport, station_id)] - observed_cache[("HF", transport, station_id)]
            for station_id in range(len(station_indices))
        ])
        predicted_source_difference[transport] = np.concatenate([
            predicted_station[(transport, station_id)][:, nearest["SA"]]
            - predicted_station[(transport, station_id)][:, nearest["HF"]]
            for station_id in range(len(station_indices))
        ])
        provider_cosine[transport] = cosine(observed_source_difference[transport],
                                            predicted_source_difference[transport])
    source_main = 0.5 * (observed_source_difference["fast"] + observed_source_difference["slow"])
    interaction = 0.5 * (observed_source_difference["fast"] - observed_source_difference["slow"])
    transport_cosine = cosine(observed_source_difference["fast"], observed_source_difference["slow"])

    station_support_pass = all(row["active_station_count"] >= 2 for row in evaluations)
    full_support_pass = all(row["truth_rank_interval_distributed_paired"] == [1, 1] for row in evaluations)
    contrast_non_degrade = all(
        row["truth_rank_interval_distributed_paired"][1] <= row["truth_rank_interval_same_endpoint_raw"][1]
        for row in evaluations)
    contrast_strict = any(
        row["truth_rank_interval_distributed_paired"][1] < row["truth_rank_interval_same_endpoint_raw"][1]
        for row in evaluations)
    shared_source_load_bearing = all(
        any(rank != [1, 1] for rank in row["single_active_station_truth_ranks"])
        for row in evaluations)
    physical_capacity = transport_cosine is not None and transport_cosine > 0.0 \
        and float(np.linalg.norm(source_main)) > float(np.linalg.norm(interaction))
    provider_direction_pass = all(value is not None and value > 0.0 for value in provider_cosine.values())
    passed = all((station_support_pass, full_support_pass, contrast_non_degrade, contrast_strict,
                  shared_source_load_bearing, physical_capacity, provider_direction_pass))
    verdict = "GO_TO_ONE_H03_CLOSED_LOOP_SCREEN" if passed else "NO_GO_NO_CLOSED_LOOP_DISTRIBUTED_OPERATOR"

    input_paths = [route_rule_path, candidate_path, loho_path]
    for source in SOURCES:
        for transport in TRANSPORTS:
            input_paths.extend((raw_root / f"H03_{source}_{transport}/CASE_MANIFEST.json",
                                raw_root / f"H03_{source}_{transport}/measured_history.jsonl",
                                raw_root / f"H03_{source}_{transport}/candidate_forward_input.jsonl"))
    result = {
        "contract": "M1R_H03_DISTRIBUTED_PAIRED_GATE_V1_20260913",
        "status": "OFFLINE_CAUSAL_MEASUREMENT_PREMISE_NOT_CLOSED_LOOP",
        "parameter_search": False,
        "source_truth_runtime_input": False,
        "candidate_count": len(candidates),
        "same_route_all_worlds": route_equal,
        "same_wind_within_transport": wind_equal,
        "native_gas_threshold_ppm": NATIVE_GAS_THRESHOLD_PPM,
        "one_shared_source_per_run": True,
        "one_nonnegative_scale_per_active_station": True,
        "observed_source_difference": {key: value.tolist() for key, value in observed_source_difference.items()},
        "observed_source_difference_cosine_fast_slow": transport_cosine,
        "observed_source_main_norm": float(np.linalg.norm(source_main)),
        "observed_source_by_transport_interaction_norm": float(np.linalg.norm(interaction)),
        "provider_observed_source_difference_cosine": provider_cosine,
        "complete_support_evaluation": evaluations,
        "gates": {
            "at_least_two_physical_active_stations_every_world": "PASS" if station_support_pass else "FAIL",
            "physical_source_over_transport_capacity": "PASS" if physical_capacity else "FAIL",
            "heldout_provider_direction": "PASS" if provider_direction_pass else "FAIL",
            "all_sources_all_transports_unique_full_support_rank1": "PASS" if full_support_pass else "FAIL",
            "paired_contrast_non_degrade_same_endpoint_raw": "PASS" if contrast_non_degrade else "FAIL",
            "paired_contrast_strictly_load_bearing": "PASS" if contrast_strict else "FAIL",
            "shared_source_across_stations_load_bearing": "PASS" if shared_source_load_bearing else "FAIL",
            "verdict": verdict,
        },
        "claim_boundary": (
            "Only all gates passing permits one failed-H03 closed-loop screen.  A local contrast, "
            "a single active station, or improvement on only one transport is insufficient."
        ),
        "inputs": [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in input_paths],
        "code_sha256": sha256(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result["gates"]))


if __name__ == "__main__":
    main()
