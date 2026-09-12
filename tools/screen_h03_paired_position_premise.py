#!/usr/bin/env python3
"""H03-only evaluator gate for a paired-position measurement operator.

The gate first enumerates ABBA-like cycles from route geometry alone.  It then
checks (a) whether real crossed source/transport responses contain a robust
source contrast and (b) whether the already frozen H01+H02-selected provider
can turn those contrasts into source evidence over the complete H03 support.
It does not select an online action or modify PMFS.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


SOURCE_IDS = ("SA", "SB")
TRANSPORT_IDS = ("fast", "slow")
WEIGHTS = np.asarray((0.5, -0.5, -0.5, 0.5), dtype=float)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def candidate_support(path: Path) -> np.ndarray:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    xy = np.asarray([[float(row["x"]), float(row["y"])] for row in rows], dtype=float)
    origin = xy.min(axis=0)
    index = np.rint((xy - origin) / 0.1).astype(int)
    keep = (index[:, 0] % 3 == 0) & (index[:, 1] % 3 == 0)
    return xy[keep]


def causal_mean(values: np.ndarray, window: int) -> np.ndarray:
    cumulative = np.vstack((np.zeros((1, values.shape[1])), np.cumsum(values, axis=0)))
    result = np.empty_like(values)
    for index in range(len(values)):
        start = max(0, index - window + 1)
        result[index] = (cumulative[index + 1] - cumulative[start]) / (index + 1 - start)
    return result


def predict_all(rows: list[dict], candidates: np.ndarray, parameter: dict, dt_s: float) -> np.ndarray:
    pose = np.asarray([row["pose_xy"] for row in rows], dtype=float)
    raw_wind = np.asarray([row["wind_uv"] for row in rows], dtype=float)
    wind_window = round(float(parameter["wind_window_s"]) / dt_s)
    wind = causal_mean(raw_wind, wind_window)
    speed = np.linalg.norm(wind, axis=1)
    unit = float(parameter["direction_sign"]) * wind / np.maximum(speed[:, None], 1e-8)
    displacement = pose[:, None, :] - candidates[None, :, :]
    along = np.sum(displacement * unit[:, None, :], axis=2)
    cross = displacement[:, :, 0] * unit[:, None, 1] - displacement[:, :, 1] * unit[:, None, 0]
    sigma = float(parameter["sigma0"]) + float(parameter["spread"]) * np.maximum(along, 0.0)
    response = np.where(
        along > 0.0,
        np.exp(-0.5 * (cross / sigma) ** 2)
        / np.maximum(along + 0.3, 0.3) ** float(parameter["distance_power"]),
        0.0,
    )
    alpha = 1.0 - math.exp(-dt_s / float(parameter["tau_s"]))
    state = np.zeros(len(candidates), dtype=float)
    filtered = np.empty_like(response)
    for index in range(len(response)):
        state += alpha * (response[index] - state)
        filtered[index] = state
    return filtered


def route_motifs(rows: list[dict], dt_s: float) -> list[dict]:
    # Constants are fixed by the 0.1 m map grid, PMFS 0.3 m source scale, and
    # the known 1.2 s sensor time constant.  No gas/source value enters here.
    spatial_bin_m = 0.1
    minimum_separation_m = 0.3
    minimum_cycle_s = 3.6
    maximum_cycle_s = 12.0
    keys = [
        (round(float(row["pose_xy"][0]) / spatial_bin_m),
         round(float(row["pose_xy"][1]) / spatial_bin_m))
        for row in rows
    ]
    maximum_gap = math.floor(maximum_cycle_s / (3.0 * dt_s) + 1e-9)
    motifs = []
    for gap in range(1, maximum_gap + 1):
        duration = 3.0 * gap * dt_s
        if duration + 1e-9 < minimum_cycle_s:
            continue
        for start in range(len(keys) - 3 * gap):
            indices = [start + offset * gap for offset in range(4)]
            a1, b1, b2, a2 = (keys[index] for index in indices)
            separation = math.dist(rows[indices[0]]["pose_xy"], rows[indices[1]]["pose_xy"])
            if a1 == a2 and b1 == b2 and a1 != b1 and separation + 1e-12 >= minimum_separation_m:
                motifs.append({
                    "indices_zero_based": indices,
                    "times_s": [float(rows[index]["t_sim_s"]) for index in indices],
                    "gap_samples": gap,
                    "cycle_duration_s": duration,
                    "a_bin": list(a1),
                    "b_bin": list(b1),
                    "a_to_b_distance_m": separation,
                    "pose_xy": [rows[index]["pose_xy"] for index in indices],
                })
    return motifs


def contrast(values: np.ndarray, indices: list[int]) -> np.ndarray:
    return WEIGHTS @ values[indices]


def profiled_losses(observed: np.ndarray, predicted: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    energy = np.sum(predicted * predicted, axis=0) + 1e-12
    amplitude = np.maximum(0.0, predicted.T @ observed) / energy
    residual = predicted * amplitude[None, :] - observed[:, None]
    return np.sum(residual * residual, axis=0), amplitude


def rank_interval(losses: np.ndarray, index: int, tolerance: float = 1e-12) -> list[int]:
    value = float(losses[index])
    return [int(np.sum(losses < value - tolerance)) + 1,
            int(np.sum(losses <= value + tolerance))]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    asset_root = repo / "evidence/cstar_current_runtime_assets240_20260907"
    manifest_path = asset_root / "manifests/H03.json"
    candidate_path = asset_root / "maps/H03/candidate.csv"
    loho_path = repo / "evidence/cstar_joint_development_20260908/CROSSED_PLUME_LOHO_SIGN.json"
    provider_path = repo / "experiments/ctpi_cstar/screen_crossed_plume_evidence.py"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    loho = json.loads(loho_path.read_text(encoding="utf-8"))
    parameter = next(fold["selected_parameter"] for fold in loho["folds"]
                     if fold["heldout_house"] == "H03")
    if "direction_sign" not in parameter:
        raise ValueError("SIGNED_LOHO_PARAMETER_REQUIRED")

    rows_by: dict[tuple[str, str], list[dict]] = {}
    truth_xy: dict[str, np.ndarray] = {}
    input_paths = [manifest_path, candidate_path, loho_path, provider_path]
    for episode in manifest["m1_episodes"]:
        source_id = episode["source_id"]
        transport_id = episode["transport_intervention_id"].rsplit("_", 1)[-1]
        path = asset_root / episode["history_trace_path"]
        if sha256(path) != episode["history_trace_sha256"]:
            raise ValueError(f"HISTORY_HASH_MISMATCH:{episode['episode_id']}")
        rows_by[(source_id, transport_id)] = read_jsonl(path)
        truth_xy[source_id] = np.asarray(episode["source_xyz_m"][:2], dtype=float)
        input_paths.append(path)
    if set(rows_by) != {(source, transport) for source in SOURCE_IDS for transport in TRANSPORT_IDS}:
        raise ValueError("H03_FACTORIAL_INCOMPLETE")

    reference = rows_by[("SA", "fast")]
    trace_steps_ns = [int(right["stamp_ns"]) - int(left["stamp_ns"])
                      for left, right in zip(reference, reference[1:])]
    if not trace_steps_ns or len(set(trace_steps_ns)) != 1 or trace_steps_ns[0] <= 0:
        raise ValueError("NONUNIFORM_HISTORY_CADENCE")
    # raw_dt_s describes the underlying simulator cadence.  The stored
    # measured-history trace is decimated and must use its own timestamp step.
    dt_s = trace_steps_ns[0] / 1.0e9
    timestamp_pose = [(row["stamp_ns"], row["pose_xy"]) for row in reference]
    route_equal = all(
        [(row["stamp_ns"], row["pose_xy"]) for row in rows] == timestamp_pose
        for rows in rows_by.values()
    )
    wind_equal_within_transport = all(
        [row["wind_uv"] for row in rows_by[("SA", transport)]]
        == [row["wind_uv"] for row in rows_by[("SB", transport)]]
        for transport in TRANSPORT_IDS
    )
    if not route_equal or not wind_equal_within_transport:
        raise ValueError("CROSSED_CONTEXT_ALIGNMENT_FAILED")

    motifs = route_motifs(reference, dt_s)
    if not motifs:
        raise ValueError("NO_GEOMETRY_ADMISSIBLE_MOTIFS")
    candidates = candidate_support(candidate_path)
    predictions = {
        transport: predict_all(rows_by[("SA", transport)], candidates, parameter, dt_s)
        for transport in TRANSPORT_IDS
    }

    motif_capacity = []
    direction_rows = []
    for motif in motifs:
        indices = motif["indices_zero_based"]
        pose = np.asarray(motif["pose_xy"], dtype=float)
        a_center = 0.5 * (pose[0] + pose[3])
        b_center = 0.5 * (pose[1] + pose[2])
        direction = b_center - a_center
        direction_rows.append(direction / np.linalg.norm(direction))
        observed = {
            f"{source}_{transport}": float(contrast(
                np.asarray([row["gas_ppm"] for row in rows_by[(source, transport)]], dtype=float), indices))
            for source in SOURCE_IDS for transport in TRANSPORT_IDS
        }
        source_difference = {
            transport: observed[f"SA_{transport}"] - observed[f"SB_{transport}"]
            for transport in TRANSPORT_IDS
        }
        source_main = 0.5 * (source_difference["fast"] + source_difference["slow"])
        interaction = 0.5 * (source_difference["fast"] - source_difference["slow"])
        predicted_source_difference = {}
        for transport in TRANSPORT_IDS:
            source_responses = {}
            for source in SOURCE_IDS:
                nearest = int(np.argmin(np.linalg.norm(candidates - truth_xy[source], axis=1)))
                source_responses[source] = float(contrast(predictions[transport][:, nearest], indices))
            predicted_source_difference[transport] = source_responses["SA"] - source_responses["SB"]
        motif_capacity.append({
            **motif,
            "observed_contrast_ppm": observed,
            "observed_source_difference": source_difference,
            "observed_source_main_effect": source_main,
            "observed_source_by_transport_interaction": interaction,
            "observed_same_sign_across_transport": source_difference["fast"] * source_difference["slow"] > 0.0,
            "observed_source_dominates_interaction": abs(source_main) > abs(interaction),
            "provider_source_difference": predicted_source_difference,
            "provider_matches_observed_sign": all(
                predicted_source_difference[transport] * source_difference[transport] > 0.0
                for transport in TRANSPORT_IDS
            ),
        })

    direction_singular_values = np.linalg.svd(np.asarray(direction_rows), compute_uv=False)
    direction_energy = direction_singular_values ** 2

    historical_false_xy = np.asarray((8.15, -1.413), dtype=float)
    evaluations = []
    motif_indices = [motif["indices_zero_based"] for motif in motifs]
    raw_indices = np.asarray([index for motif in motif_indices for index in motif], dtype=int)
    for transport in TRANSPORT_IDS:
        predicted_contrast = np.stack([
            contrast(predictions[transport], indices) for indices in motif_indices
        ])
        predicted_raw = predictions[transport][raw_indices]
        for source in SOURCE_IDS:
            measured = np.asarray([row["gas_ppm"] for row in rows_by[(source, transport)]], dtype=float)
            observed_contrast = np.asarray([contrast(measured, indices) for indices in motif_indices])
            observed_raw = measured[raw_indices]
            losses, amplitude = profiled_losses(observed_contrast, predicted_contrast)
            raw_losses, _ = profiled_losses(observed_raw, predicted_raw)
            truth_index = int(np.argmin(np.linalg.norm(candidates - truth_xy[source], axis=1)))
            false_index = int(np.argmin(np.linalg.norm(candidates - historical_false_xy, axis=1)))
            best_index = int(np.argmin(losses))
            evaluations.append({
                "actual_source": source,
                "transport": transport,
                "truth_nearest_candidate_xy": candidates[truth_index].tolist(),
                "truth_rank_interval_paired": rank_interval(losses, truth_index),
                "truth_rank_interval_raw_16_samples": rank_interval(raw_losses, truth_index),
                "truth_loss_paired": float(losses[truth_index]),
                "truth_profiled_amplitude": float(amplitude[truth_index]),
                "best_candidate_xy": candidates[best_index].tolist(),
                "best_loss_paired": float(losses[best_index]),
                "historical_h03_false_xy_evaluator_only": historical_false_xy.tolist(),
                "historical_false_nearest_candidate_xy": candidates[false_index].tolist(),
                "historical_false_rank_interval_paired": rank_interval(losses, false_index),
                "historical_false_loss_paired": float(losses[false_index]),
            })

    capacity_pass = all(
        row["observed_same_sign_across_transport"]
        and row["observed_source_dominates_interaction"]
        and row["provider_matches_observed_sign"]
        for row in motif_capacity
    )
    sa_full_support_pass = all(
        row["truth_rank_interval_paired"][0] == 1 and row["truth_rank_interval_paired"][1] == 1
        for row in evaluations if row["actual_source"] == "SA"
    )
    result = {
        "contract": "M1R_H03_PAIRED_POSITION_PREMISE_V1_20260913",
        "status": "H03_EXISTING_ROUTE_EVALUATOR_ONLY",
        "parameter_search": False,
        "source_truth_runtime_input": False,
        "geometry_motif_selection_reads_gas_or_source": False,
        "source_labels_used_only_for_capacity_and_rank_evaluation": True,
        "same_route_all_four_worlds": route_equal,
        "same_wind_within_each_crossed_source_pair": wind_equal_within_transport,
        "provider_parameter_source": "H03-held-out LOHO selection using H01+H02 labels",
        "provider_parameter": parameter,
        "cadence_correction": {
            "manifest_raw_simulator_dt_s": float(manifest["raw_dt_s"]),
            "stored_history_dt_s": dt_s,
            "stored_history_is_decimated_from_raw": not math.isclose(
                dt_s, float(manifest["raw_dt_s"]), rel_tol=0.0, abs_tol=1e-12),
            "wind_window_samples": round(float(parameter["wind_window_s"]) / dt_s),
            "sensor_alpha": 1.0 - math.exp(-dt_s / float(parameter["tau_s"])),
        },
        "measurement_operator": {
            "weights": WEIGHTS.tolist(),
            "property": "sum(weights)=0 and equal spacing gives sum(weights*time)=0",
            "spatial_bin_m": 0.1,
            "minimum_a_to_b_distance_m": 0.3,
            "cycle_duration_s": [3.6, 12.0],
            "motif_count": len(motifs),
        },
        "motif_capacity": motif_capacity,
        "directional_observability": {
            "unit_a_to_b_directions": np.asarray(direction_rows).tolist(),
            "singular_values": direction_singular_values.tolist(),
            "condition_number": float(direction_singular_values[0] / direction_singular_values[-1]),
            "second_direction_energy_fraction": float(direction_energy[-1] / np.sum(direction_energy)),
            "interpretation": "descriptive only; geometry-admissible motifs are almost one-dimensional",
        },
        "complete_candidate_count": len(candidates),
        "complete_support_evaluation": evaluations,
        "gates": {
            "physical_contrast_capacity": "PASS" if capacity_pass else "FAIL",
            "failed_h03_sa_full_support_identification": "PASS" if sa_full_support_pass else "FAIL",
            "verdict": "GO_TO_NEW_ACTION_DESIGN" if capacity_pass and sa_full_support_pass
                       else "NO_GO_CURRENT_PAIRED_OPERATOR_INSUFFICIENT_FULL_SUPPORT_SEPARATION",
        },
        "claim_boundary": (
            "A capacity PASS only shows that the crossed H03 asset contains a paired contrast. "
            "The full-support gate requires unique truth ranking in both transports before any active ROS run."
        ),
        "inputs": [{"path": str(path.relative_to(repo)), "bytes": path.stat().st_size, "sha256": sha256(path)}
                   for path in input_paths],
        "code_sha256": sha256(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"motifs": len(motifs), **result["gates"]}))


if __name__ == "__main__":
    main()
