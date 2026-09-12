#!/usr/bin/env python3
"""Build a source/gas-blind three-direction H03 paired-measurement route."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from cstar_build_map_cover_routes import astar, graph, nearest, resample
from screen_h03_paired_position_premise import route_motifs


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rotate(vector: np.ndarray, degrees: float) -> np.ndarray:
    angle = math.radians(degrees)
    matrix = np.asarray(((math.cos(angle), -math.sin(angle)),
                         (math.sin(angle), math.cos(angle))))
    return matrix @ vector


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output_root = args.output_root.resolve()
    route_path = output_root / "H03/history_route.csv"
    rule_path = output_root / "ROUTE_RULE.json"
    if output_root.exists():
        raise FileExistsError(output_root)

    asset_root = repo / "evidence/cstar_current_runtime_assets240_20260907"
    manifest_path = asset_root / "manifests/H03.json"
    candidate_path = asset_root / "maps/H03/candidate.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    history_paths = [asset_root / episode["history_trace_path"] for episode in manifest["m1_episodes"]]
    histories = [
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for path in history_paths
    ]
    route_signatures = [
        [(row["stamp_ns"], row["pose_xy"]) for row in history]
        for history in histories
    ]
    if any(signature != route_signatures[0] for signature in route_signatures[1:]):
        raise ValueError("SOURCE_TRANSPORT_ROUTE_NOT_IDENTICAL")
    reference = histories[0]
    step_ns = {int(right["stamp_ns"]) - int(left["stamp_ns"])
               for left, right in zip(reference, reference[1:])}
    if len(step_ns) != 1:
        raise ValueError("NONUNIFORM_ROUTE_CLOCK")
    dt_s = step_ns.pop() / 1.0e9

    with candidate_path.open(encoding="utf-8", newline="") as handle:
        points = [(float(row["x"]), float(row["y"])) for row in csv.DictReader(handle)]
    point_array = np.asarray(points, dtype=float)
    neighbors = graph(points)
    motifs = route_motifs(reference, dt_s)
    if not motifs:
        raise ValueError("NO_GEOMETRY_PRIMARY_CYCLE")
    primary_motif = max(motifs, key=lambda row: (row["a_to_b_distance_m"], -row["indices_zero_based"][0]))
    primary_pose = np.asarray(primary_motif["pose_xy"], dtype=float)
    primary_a_target = 0.5 * (primary_pose[0] + primary_pose[3])
    primary_b_target = 0.5 * (primary_pose[1] + primary_pose[2])
    primary_a_index = nearest(points, primary_a_target)
    primary_b_index = nearest(points, primary_b_target)
    primary_a = point_array[primary_a_index]
    primary_b = point_array[primary_b_index]
    primary_vector = primary_b - primary_a
    primary_length = float(np.linalg.norm(primary_vector))
    primary_unit = primary_vector / primary_length
    center = 0.5 * (primary_a + primary_b)

    local_indices = np.where(np.linalg.norm(point_array - center, axis=1) < 1.4)[0]

    def choose_pair(degrees: float) -> tuple[int, int, dict]:
        target = rotate(primary_unit, degrees)
        geometry = []
        for offset, left in enumerate(local_indices):
            for right in local_indices[offset + 1:]:
                delta = point_array[right] - point_array[left]
                length = float(np.linalg.norm(delta))
                if not 0.5 <= length <= 1.1:
                    continue
                midpoint_distance = float(np.linalg.norm(0.5 * (point_array[left] + point_array[right]) - center))
                alignment_loss = 1.0 - abs(float(delta @ target) / length)
                score = alignment_loss + midpoint_distance + 0.2 * abs(length - primary_length)
                geometry.append((score, left, right, alignment_loss, midpoint_distance, length))
        geometry.sort()
        evaluated = []
        for score, left, right, alignment_loss, midpoint_distance, length in geometry[:300]:
            path_indices = astar(points, neighbors, int(left), int(right))
            path_length = sum(math.dist(points[a], points[b]) for a, b in zip(path_indices, path_indices[1:]))
            total_score = score + 0.5 * max(0.0, path_length - 1.1)
            evaluated.append((total_score, left, right, alignment_loss, midpoint_distance,
                              length, path_length, path_indices))
        if not evaluated:
            raise ValueError(f"NO_ORTHOGONAL_PAIR:{degrees}")
        selected = min(evaluated)
        _, left, right, alignment_loss, midpoint_distance, length, path_length, path_indices = selected
        if float((point_array[right] - point_array[left]) @ target) < 0.0:
            left, right = right, left
            path_indices = list(reversed(path_indices))
        return int(left), int(right), {
            "target_rotation_degrees": degrees,
            "alignment_loss": alignment_loss,
            "midpoint_distance_from_primary_m": midpoint_distance,
            "euclidean_length_m": length,
            "astar_length_m": path_length,
            "selection_reads_gas_or_source": False,
        }

    second_a, second_b, second_meta = choose_pair(60.0)
    third_a, third_b, third_meta = choose_pair(120.0)
    pair_specs = [
        (primary_a_index, primary_b_index, {
            "target_rotation_degrees": 0.0,
            "geometry_origin": "longest pre-existing admissible route motif",
            "selection_reads_gas_or_source": False,
        }),
        (second_a, second_b, second_meta),
        (third_a, third_b, third_meta),
    ]

    route_xy = [tuple(reference[0]["pose_xy"])]
    prefix_end = primary_motif["indices_zero_based"][0]
    route_xy.extend(tuple(row["pose_xy"]) for row in reference[:prefix_end + 1])
    max_speed_m_s = 0.3
    minimum_gap_steps = math.ceil(1.2 / dt_s)

    def move_to(target_index: int, forced_steps: int | None = None) -> tuple[int, float]:
        current = np.asarray(route_xy[-1], dtype=float)
        start_index = nearest(points, current)
        path_indices = astar(points, neighbors, start_index, target_index)
        polyline = [tuple(current)]
        if math.dist(polyline[-1], points[start_index]) > 1e-12:
            polyline.append(points[start_index])
        polyline.extend(points[index] for index in path_indices[1:])
        length = sum(math.dist(a, b) for a, b in zip(polyline, polyline[1:]))
        steps = max(minimum_gap_steps, math.ceil(length / (max_speed_m_s * dt_s) - 1e-12))
        if forced_steps is not None:
            steps = forced_steps
            if length / (steps * dt_s) > max_speed_m_s + 1e-12:
                raise ValueError("FORCED_CYCLE_SPEED_EXCEEDED")
        sampled, _ = resample(polyline, steps + 1)
        route_xy.extend(sampled[1:])
        return steps, length

    cycles = []
    for pair_index, (a_index, b_index, metadata) in enumerate(pair_specs, start=1):
        transition_steps, transition_length = move_to(a_index)
        start_index = len(route_xy) - 1
        forward_path = astar(points, neighbors, a_index, b_index)
        forward_length = sum(math.dist(points[a], points[b]) for a, b in zip(forward_path, forward_path[1:]))
        gap_steps = max(minimum_gap_steps, math.ceil(forward_length / (max_speed_m_s * dt_s) - 1e-12))
        first_b_gap, _ = move_to(b_index, forced_steps=gap_steps)
        route_xy.extend([points[b_index]] * gap_steps)
        second_b_index = len(route_xy) - 1
        return_gap, _ = move_to(a_index, forced_steps=gap_steps)
        endpoint_indices = [start_index, start_index + first_b_gap, second_b_index,
                            second_b_index + return_gap]
        if [endpoint_indices[index + 1] - endpoint_indices[index] for index in range(3)] != [gap_steps] * 3:
            raise ValueError("CYCLE_NOT_EQUALLY_SPACED")
        cycles.append({
            "cycle_id": pair_index,
            "a_xy": point_array[a_index].tolist(),
            "b_xy": point_array[b_index].tolist(),
            "endpoint_route_indices_zero_based": endpoint_indices,
            "endpoint_times_s": [index * dt_s for index in endpoint_indices],
            "contrast_weights": [0.5, -0.5, -0.5, 0.5],
            "gap_steps": gap_steps,
            "gap_s": gap_steps * dt_s,
            "cycle_duration_s": 3.0 * gap_steps * dt_s,
            "astar_a_to_b_length_m": forward_length,
            "maximum_segment_average_speed_m_s": forward_length / (gap_steps * dt_s),
            "pre_cycle_transition_steps": transition_steps,
            "pre_cycle_transition_length_m": transition_length,
            **metadata,
        })

    directions = np.asarray([
        (np.asarray(cycle["b_xy"]) - np.asarray(cycle["a_xy"]))
        / np.linalg.norm(np.asarray(cycle["b_xy"]) - np.asarray(cycle["a_xy"]))
        for cycle in cycles
    ])
    singular_values = np.linalg.svd(directions, compute_uv=False)
    route_path.parent.mkdir(parents=True)
    with route_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("t_sim_s", "x", "y", "z"))
        writer.writerows((round(index * dt_s, 9), xy[0], xy[1], 0.3)
                         for index, xy in enumerate(route_xy))
    step_distances = [math.dist(a, b) for a, b in zip(route_xy, route_xy[1:])]
    rule = {
        "contract": "M1R_H03_RANK2_PAIRED_ROUTE_V1_20260913",
        "status": "PRE_EXPERIMENT_SOURCE_GAS_BLIND_FREEZE",
        "house": "H03",
        "source_or_gas_values_used_for_design": False,
        "design_inputs": "shared route geometry and source-independent free-space candidate map only",
        "dt_s": dt_s,
        "z_m": 0.3,
        "prefix_source": "shared H03 source-blind map-cover route",
        "prefix_end_original_history_index_zero_based": prefix_end,
        "frames_including_t0": len(route_xy),
        "end_time_s": (len(route_xy) - 1) * dt_s,
        "maximum_step_m": max(step_distances),
        "maximum_average_speed_m_s": max(step_distances) / dt_s,
        "pairs": cycles,
        "direction_matrix": directions.tolist(),
        "direction_singular_values": singular_values.tolist(),
        "direction_condition_number": float(singular_values[0] / singular_values[-1]),
        "measurement_operator_rank": int(np.linalg.matrix_rank(directions)),
        "selection_rule": (
            "retain the longest existing geometry-admissible line; add map-feasible lines at 60 and 120 degrees "
            "using fixed alignment+midpoint+length+detour objective"
        ),
        "inputs": [
            {"path": str(path.relative_to(repo)), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in [manifest_path, candidate_path, *history_paths]
        ],
        "route": {"path": str(route_path.relative_to(output_root)), "sha256": sha256(route_path),
                  "bytes": route_path.stat().st_size},
        "code_sha256": sha256(Path(__file__)),
    }
    rule_path.write_text(json.dumps(rule, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"route": str(route_path), "frames": len(route_xy),
                      "end_time_s": rule["end_time_s"], "condition": rule["direction_condition_number"]}))


if __name__ == "__main__":
    main()
