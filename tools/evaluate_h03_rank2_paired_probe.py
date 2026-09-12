#!/usr/bin/env python3
"""Evaluate the frozen H03 three-direction paired-response premise."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from screen_h03_paired_position_premise import candidate_support, predict_all, profiled_losses, rank_interval


SOURCES = ("SA", "HF")
TRANSPORTS = ("fast", "slow")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def cosine(left: np.ndarray, right: np.ndarray) -> float | None:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return None if denominator == 0.0 else float(left @ right / denominator)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    raw_root = args.raw_root.resolve()
    route_rule_path = repo / "evidence/m1r_h03_rank2_paired_probe_20260913/route/ROUTE_RULE.json"
    candidate_path = repo / "evidence/cstar_current_runtime_assets240_20260907/maps/H03/candidate.csv"
    loho_path = repo / "evidence/cstar_joint_development_20260908/CROSSED_PLUME_LOHO_SIGN.json"
    route_rule = json.loads(route_rule_path.read_text(encoding="utf-8"))
    loho = json.loads(loho_path.read_text(encoding="utf-8"))
    parameter = next(fold["selected_parameter"] for fold in loho["folds"]
                     if fold["heldout_house"] == "H03")
    candidates = candidate_support(candidate_path)
    histories = {(source, transport): rows(raw_root / f"H03_{source}_{transport}/measured_history.jsonl")
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
        raise ValueError("RANK2_CROSSED_CONTEXT_ALIGNMENT_FAILED")

    step_ns = {right["stamp_ns"] - left["stamp_ns"] for left, right in zip(reference, reference[1:])}
    if len(step_ns) != 1:
        raise ValueError("RANK2_HISTORY_CADENCE")
    dt_s = step_ns.pop() / 1.0e9
    endpoint_indices = [[index - 1 for index in cycle["endpoint_route_indices_zero_based"]]
                        for cycle in route_rule["pairs"]]
    weights = [np.asarray(cycle["contrast_weights"], dtype=float) for cycle in route_rule["pairs"]]

    def observed_vector(source: str, transport: str) -> np.ndarray:
        gas = np.asarray([row["gas_ppm"] for row in histories[(source, transport)]], dtype=float)
        return np.asarray([weight @ gas[index] for weight, index in zip(weights, endpoint_indices)])

    observed = {(source, transport): observed_vector(source, transport)
                for source in SOURCES for transport in TRANSPORTS}
    source_difference = {transport: observed[("SA", transport)] - observed[("HF", transport)]
                         for transport in TRANSPORTS}
    source_main = 0.5 * (source_difference["fast"] + source_difference["slow"])
    interaction = 0.5 * (source_difference["fast"] - source_difference["slow"])

    predictions = {transport: predict_all(histories[("SA", transport)], candidates, parameter, dt_s)
                   for transport in TRANSPORTS}
    predicted_contrasts = {
        transport: np.stack([weight @ predictions[transport][index]
                             for weight, index in zip(weights, endpoint_indices)])
        for transport in TRANSPORTS
    }
    evaluations = []
    provider_direction_matches = []
    for transport in TRANSPORTS:
        nearest = {source: int(np.argmin(np.linalg.norm(candidates - truth_xy[source], axis=1)))
                   for source in SOURCES}
        predicted_difference = (predicted_contrasts[transport][:, nearest["SA"]]
                                - predicted_contrasts[transport][:, nearest["HF"]])
        provider_direction_matches.append(cosine(source_difference[transport], predicted_difference))
        for source in SOURCES:
            loss, amplitude = profiled_losses(observed[(source, transport)], predicted_contrasts[transport])
            truth_index = nearest[source]
            best_index = int(np.argmin(loss))
            evaluations.append({
                "actual_source": source,
                "transport": transport,
                "observed_contrast_ppm": observed[(source, transport)].tolist(),
                "truth_xy_evaluator_only": truth_xy[source].tolist(),
                "truth_nearest_candidate_xy": candidates[truth_index].tolist(),
                "truth_rank_interval": rank_interval(loss, truth_index),
                "truth_loss": float(loss[truth_index]),
                "truth_profiled_amplitude": float(amplitude[truth_index]),
                "best_candidate_xy": candidates[best_index].tolist(),
                "best_candidate_error_to_truth_m": float(np.linalg.norm(candidates[best_index] - truth_xy[source])),
                "best_loss": float(loss[best_index]),
            })

    physical_capacity = (cosine(source_difference["fast"], source_difference["slow"]) or -1.0) > 0.0 \
        and float(np.linalg.norm(source_main)) > float(np.linalg.norm(interaction))
    provider_direction_pass = all(value is not None and value > 0.0 for value in provider_direction_matches)
    full_support_pass = all(row["truth_rank_interval"] == [1, 1] for row in evaluations)
    verdict = ("GO_TO_ONE_H03_CLOSED_LOOP_SCREEN" if physical_capacity and provider_direction_pass and full_support_pass
               else "NO_GO_NO_CLOSED_LOOP_CURRENT_RANK2_OPERATOR")
    input_paths = [route_rule_path, candidate_path, loho_path]
    for source in SOURCES:
        for transport in TRANSPORTS:
            input_paths.extend((raw_root / f"H03_{source}_{transport}/CASE_MANIFEST.json",
                                raw_root / f"H03_{source}_{transport}/measured_history.jsonl",
                                raw_root / f"H03_{source}_{transport}/candidate_forward_input.jsonl"))
    result = {
        "contract": "M1R_H03_RANK2_PAIRED_PROBE_GATE_V1_20260913",
        "status": "OFFLINE_SOURCE_RESPONSE_PREMISE_NOT_CLOSED_LOOP",
        "parameter_search": False,
        "source_truth_runtime_input": False,
        "source_world_coordinates_evaluator_only": {key: value.tolist() for key, value in truth_xy.items()},
        "same_route_all_worlds": route_equal,
        "same_wind_within_transport": wind_equal,
        "candidate_count": len(candidates),
        "measurement_operator_rank": route_rule["measurement_operator_rank"],
        "direction_condition_number": route_rule["direction_condition_number"],
        "observed_source_difference": {key: value.tolist() for key, value in source_difference.items()},
        "observed_source_difference_cosine_fast_slow": cosine(source_difference["fast"], source_difference["slow"]),
        "observed_source_main_norm": float(np.linalg.norm(source_main)),
        "observed_source_by_transport_interaction_norm": float(np.linalg.norm(interaction)),
        "provider_observed_source_difference_cosine": dict(zip(TRANSPORTS, provider_direction_matches)),
        "complete_support_evaluation": evaluations,
        "gates": {
            "physical_source_over_transport_capacity": "PASS" if physical_capacity else "FAIL",
            "heldout_provider_direction": "PASS" if provider_direction_pass else "FAIL",
            "all_sources_all_transports_unique_full_support_rank1": "PASS" if full_support_pass else "FAIL",
            "verdict": verdict,
        },
        "claim_boundary": (
            "Only a three-part PASS permits one H03 closed-loop development screen. "
            "A physical contrast or near-source best candidate alone is not a causal localization PASS."
        ),
        "inputs": [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in input_paths],
        "code_sha256": sha256(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result["gates"]))


if __name__ == "__main__":
    main()
