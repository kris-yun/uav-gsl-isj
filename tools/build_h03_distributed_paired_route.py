#!/usr/bin/env python3
"""Build a source/gas-blind distributed H03 paired-intervention route."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from cstar_build_map_cover_routes import astar, graph, nearest, resample
from screen_h03_paired_position_premise import candidate_support


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rotate(vector: np.ndarray, degrees: float) -> np.ndarray:
    angle = math.radians(degrees)
    matrix = np.asarray(((math.cos(angle), -math.sin(angle)),
                         (math.sin(angle), math.cos(angle))))
    return matrix @ vector


def path_length(points: list[tuple[float, float]], indices: list[int]) -> float:
    return sum(math.dist(points[a], points[b]) for a, b in zip(indices, indices[1:]))


def checked_astar(points: list[tuple[float, float]], neighbors: list[list[int]],
                  start: int, goal: int) -> list[int]:
    indices = astar(points, neighbors, start, goal)
    if indices[0] != start or indices[-1] != goal:
        raise ValueError("ASTAR_ENDPOINT_MISMATCH")
    if any(math.dist(points[a], points[b]) > math.sqrt(2.0) * 0.1 + 1e-9
           for a, b in zip(indices, indices[1:])):
        raise ValueError(f"DISCONNECTED_FREE_SPACE:{start}:{goal}")
    return indices


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise FileExistsError(output_root)

    asset_root = repo / "evidence/cstar_current_runtime_assets240_20260907"
    manifest_path = asset_root / "manifests/H03.json"
    candidate_path = asset_root / "maps/H03/candidate.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    history_paths = [asset_root / row["history_trace_path"] for row in manifest["m1_episodes"]]
    histories = [[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
                 for path in history_paths]
    signatures = [[(row["stamp_ns"], row["pose_xy"]) for row in history] for history in histories]
    if any(signature != signatures[0] for signature in signatures[1:]):
        raise ValueError("SOURCE_TRANSPORT_ROUTE_NOT_IDENTICAL")
    reference = histories[0]
    dt_values = {int(right["stamp_ns"]) - int(left["stamp_ns"])
                 for left, right in zip(reference, reference[1:])}
    if len(dt_values) != 1:
        raise ValueError("NONUNIFORM_ROUTE_CLOCK")
    dt_s = dt_values.pop() / 1e9

    with candidate_path.open(encoding="utf-8", newline="") as handle:
        points = [(float(row["x"]), float(row["y"])) for row in csv.DictReader(handle)]
    point_array = np.asarray(points, dtype=float)
    support = candidate_support(candidate_path)
    neighbors = graph(points)

    # Fixed 60 s source-blind warm-up follows the already frozen map-cover route.
    warmup_end = int(round(60.0 / dt_s))
    route_xy = [tuple(row["pose_xy"]) for row in reference[:warmup_end + 1]]

    # Three map-spread centers use only the source-independent support.  The
    # first is closest to the support centroid; subsequent centers maximize
    # distance from the selected set.  This is the project's existing map-cover
    # rule, reduced to the smallest number of stations that can test sharing.
    selected_support = [int(np.argmin(np.linalg.norm(support - support.mean(axis=0), axis=1)))]
    while len(selected_support) < 3:
        distance = np.min(np.linalg.norm(support[:, None, :] - support[selected_support][None, :, :], axis=2), axis=1)
        distance[selected_support] = -1.0
        selected_support.append(int(np.argmax(distance)))
    center_indices = [nearest(points, support[index]) for index in selected_support]

    # Visit the three centers in the shortest map-feasible order from the end
    # of warm-up.  Only six permutations exist, so this is exact and fixed.
    current_index = nearest(points, route_xy[-1])
    order_candidates = []
    for order in itertools.permutations(center_indices):
        total = 0.0
        left = current_index
        feasible = True
        for right in order:
            try:
                total += path_length(points, checked_astar(points, neighbors, left, right))
            except ValueError:
                feasible = False
                break
            left = right
        if feasible:
            order_candidates.append((total, order))
    if not order_candidates:
        raise ValueError("NO_FEASIBLE_CENTER_ORDER")
    _, ordered_centers = min(order_candidates)

    max_speed_m_s = 0.3
    minimum_gap_steps = math.ceil(1.2 / dt_s)

    def move_to(target_index: int, forced_steps: int | None = None) -> tuple[int, float]:
        current = np.asarray(route_xy[-1], dtype=float)
        start_index = nearest(points, current)
        indices = checked_astar(points, neighbors, start_index, target_index)
        polyline = [tuple(current)]
        if math.dist(polyline[-1], points[start_index]) > 1e-12:
            polyline.append(points[start_index])
        polyline.extend(points[index] for index in indices[1:])
        length = sum(math.dist(a, b) for a, b in zip(polyline, polyline[1:]))
        steps = max(minimum_gap_steps, math.ceil(length / (max_speed_m_s * dt_s) - 1e-12))
        if forced_steps is not None:
            steps = forced_steps
            if length / (steps * dt_s) > max_speed_m_s + 1e-12:
                raise ValueError("FORCED_CYCLE_SPEED_EXCEEDED")
        sampled, _ = resample(polyline, steps + 1)
        route_xy.extend(sampled[1:])
        return steps, length

    def choose_pair(center_index: int, degrees: float) -> tuple[int, int, dict]:
        center = point_array[center_index]
        target = rotate(np.asarray((1.0, 0.0)), degrees)
        local = np.where(np.linalg.norm(point_array - center, axis=1) <= 0.85)[0]
        choices = []
        for offset, left in enumerate(local):
            for right in local[offset + 1:]:
                delta = point_array[right] - point_array[left]
                length = float(np.linalg.norm(delta))
                if not 0.5 <= length <= 0.9:
                    continue
                midpoint_error = float(np.linalg.norm(0.5 * (point_array[left] + point_array[right]) - center))
                if midpoint_error > 0.3:
                    continue
                alignment_loss = 1.0 - abs(float(delta @ target) / length)
                if alignment_loss > 0.12:
                    continue
                try:
                    indices = checked_astar(points, neighbors, int(left), int(right))
                except ValueError:
                    continue
                travel = path_length(points, indices)
                score = alignment_loss + midpoint_error + 0.2 * abs(length - 0.7) + 0.5 * max(0.0, travel - 1.0)
                choices.append((score, int(left), int(right), alignment_loss, midpoint_error, length, travel))
        if not choices:
            raise ValueError(f"NO_PAIR_AT_CENTER:{center.tolist()}:{degrees}")
        _, left, right, alignment_loss, midpoint_error, length, travel = min(choices)
        if float((point_array[right] - point_array[left]) @ target) < 0.0:
            left, right = right, left
        return left, right, {
            "target_absolute_degrees": degrees,
            "alignment_loss": alignment_loss,
            "midpoint_distance_from_center_m": midpoint_error,
            "euclidean_length_m": length,
            "astar_length_m": travel,
        }

    station_records = []
    all_directions = []
    for station_id, center_index in enumerate(ordered_centers, start=1):
        station = {"station_id": station_id, "center_xy": point_array[center_index].tolist(), "pairs": []}
        for direction_id, degrees in enumerate((0.0, 60.0, 120.0), start=1):
            a_index, b_index, meta = choose_pair(center_index, degrees)
            transition_steps, transition_length = move_to(a_index)
            start_index = len(route_xy) - 1
            ab_path = checked_astar(points, neighbors, a_index, b_index)
            ab_length = path_length(points, ab_path)
            gap_steps = max(minimum_gap_steps, math.ceil(ab_length / (max_speed_m_s * dt_s) - 1e-12))
            first_b_gap, _ = move_to(b_index, forced_steps=gap_steps)
            route_xy.extend([points[b_index]] * gap_steps)
            second_b_index = len(route_xy) - 1
            return_gap, _ = move_to(a_index, forced_steps=gap_steps)
            endpoint_indices = [start_index, start_index + first_b_gap,
                                second_b_index, second_b_index + return_gap]
            if np.diff(endpoint_indices).tolist() != [gap_steps] * 3:
                raise ValueError("CYCLE_NOT_EQUALLY_SPACED")
            direction = (point_array[b_index] - point_array[a_index]) / np.linalg.norm(point_array[b_index] - point_array[a_index])
            all_directions.append(direction)
            station["pairs"].append({
                "direction_id": direction_id,
                "a_xy": point_array[a_index].tolist(),
                "b_xy": point_array[b_index].tolist(),
                "unit_a_to_b": direction.tolist(),
                "endpoint_route_indices_zero_based": endpoint_indices,
                "endpoint_times_s": [index * dt_s for index in endpoint_indices],
                "contrast_weights": [0.5, -0.5, -0.5, 0.5],
                "gap_steps": gap_steps,
                "gap_s": gap_steps * dt_s,
                "pre_cycle_transition_steps": transition_steps,
                "pre_cycle_transition_length_m": transition_length,
                "maximum_segment_average_speed_m_s": ab_length / (gap_steps * dt_s),
                **meta,
            })
        station_records.append(station)

    route_path = output_root / "H03/history_route.csv"
    route_path.parent.mkdir(parents=True)
    with route_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("t_sim_s", "x", "y", "z"))
        writer.writerows((round(index * dt_s, 9), xy[0], xy[1], 0.3)
                         for index, xy in enumerate(route_xy))
    distances = [math.dist(a, b) for a, b in zip(route_xy, route_xy[1:])]
    station_condition = []
    for station in station_records:
        matrix = np.asarray([pair["unit_a_to_b"] for pair in station["pairs"]])
        singular = np.linalg.svd(matrix, compute_uv=False)
        station["direction_singular_values"] = singular.tolist()
        station["direction_condition_number"] = float(singular[0] / singular[-1])
        station["measurement_operator_rank"] = int(np.linalg.matrix_rank(matrix))
        station_condition.append(station["direction_condition_number"])

    rule = {
        "contract": "M1R_H03_DISTRIBUTED_PAIRED_ROUTE_V1_20260913",
        "status": "PRE_EXPERIMENT_SOURCE_GAS_BLIND_FREEZE",
        "house": "H03",
        "source_or_gas_values_used_for_design": False,
        "design_inputs": "shared source-blind route geometry and source-independent free-space candidate map only",
        "dt_s": dt_s,
        "z_m": 0.3,
        "warmup": {"source": "existing H03 source-blind map-cover route", "duration_s": 60.0,
                   "end_original_history_index_zero_based": warmup_end},
        "center_selection": "three-point farthest sampling from candidate-support centroid; exact shortest feasible visit order",
        "station_count": 3,
        "stations": station_records,
        "profiled_nuisance_contract": "one nonnegative response scale per station, one shared source identity over all stations",
        "frames_including_t0": len(route_xy),
        "end_time_s": (len(route_xy) - 1) * dt_s,
        "maximum_step_m": max(distances),
        "maximum_average_speed_m_s": max(distances) / dt_s,
        "maximum_station_direction_condition_number": max(station_condition),
        "all_station_measurement_operator_rank": min(station["measurement_operator_rank"] for station in station_records),
        "inputs": [{"path": str(path.relative_to(repo)), "sha256": sha256(path), "bytes": path.stat().st_size}
                   for path in [manifest_path, candidate_path, *history_paths]],
        "route": {"path": str(route_path.relative_to(output_root)), "sha256": sha256(route_path),
                  "bytes": route_path.stat().st_size},
        "code_sha256": sha256(Path(__file__)),
    }
    (output_root / "ROUTE_RULE.json").write_text(json.dumps(rule, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"centers": [station["center_xy"] for station in station_records],
                      "end_time_s": rule["end_time_s"], "frames": len(route_xy),
                      "max_condition": rule["maximum_station_direction_condition_number"]}))


if __name__ == "__main__":
    main()
