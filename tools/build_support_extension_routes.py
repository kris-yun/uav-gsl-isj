#!/usr/bin/env python3
"""Build the frozen map-only dual-UAV routes for the support-extension test."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from audit_occupancy_native_parity import CustomOccupancy
from build_house02_global_dual_route import (
    ALTITUDE,
    SEPARATION,
    angular_gap,
    components,
    edge_is_feasible,
    exact_baseline_is_free,
    feasible_angles,
    point_state,
    wind_cross_angle,
)
from build_observability_route_candidates import (
    BASE_DIRECTIONS,
    CANDIDATE_BUDGET,
    START_SEARCH_BUDGET,
    angle_change,
    build_adjacency,
    deterministic_starts,
    direction_orders,
    dfs_walk,
)


DT = 0.2
SPEED = 0.35
EXTENDED_HORIZON_S = 222.8
EXPECTED_SAMPLES = 1115


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fields, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def resample_polyline_duration(points):
    segments = []
    for first, second in zip(points, points[1:]):
        length = math.hypot(second[0] - first[0], second[1] - first[1])
        if length > 1e-12:
            segments.append((first, second, length))
    total_length = sum(segment[2] for segment in segments)
    if total_length / SPEED + 1e-9 < EXTENDED_HORIZON_S:
        raise RuntimeError(f"map walk is shorter than frozen horizon: {total_length / SPEED:.3f}s")
    sample_count = EXPECTED_SAMPLES
    samples = []
    segment_index = 0
    segment_start_distance = 0.0
    for index in range(sample_count):
        time_s = index * DT
        target = min(time_s * SPEED, max(0.0, total_length - 1e-9))
        while segment_index + 1 < len(segments) and segment_start_distance + segments[segment_index][2] < target:
            segment_start_distance += segments[segment_index][2]
            segment_index += 1
        first, second, length = segments[segment_index]
        fraction = 0.0 if length == 0 else (target - segment_start_distance) / length
        x = first[0] + fraction * (second[0] - first[0])
        y = first[1] + fraction * (second[1] - first[1])
        vx = SPEED * (second[0] - first[0]) / length
        vy = SPEED * (second[1] - first[1]) / length
        samples.append({
            "t_sim_s": time_s, "step": index + 1, "x": x, "y": y,
            "z": ALTITUDE, "yaw": math.atan2(vy, vx),
            "vx": vx, "vy": vy, "vz": 0.0,
        })
    return samples, total_length


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--wind", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if len(args.wind) != 2:
        raise RuntimeError("exactly W_fast and W_slow must be supplied")

    occupancy = CustomOccupancy(args.occupancy)
    nx, ny, _ = occupancy.dimensions
    feasible_cells, xy_by_cell = set(), {}
    for ix in range(nx):
        for iy in range(ny):
            x = float(occupancy.minimum[0] + (np.float32(ix) + np.float32(0.5)) * occupancy.cell)
            y = float(occupancy.minimum[1] + (np.float32(iy) + np.float32(0.5)) * occupancy.cell)
            if point_state(occupancy, x, y) == 0:
                angles, _ = feasible_angles(occupancy, x, y)
                if angles:
                    feasible_cells.add((ix, iy))
                    xy_by_cell[(ix, iy)] = (x, y)
    largest = components(feasible_cells)[0]
    adjacency = build_adjacency(largest, xy_by_cell, occupancy)
    graph_nodes = {cell for cell, neighbors in adjacency.items() if neighbors}
    graph_largest = components(graph_nodes)[0]
    adjacency = {cell: [neighbor for neighbor in adjacency[cell] if neighbor in graph_largest] for cell in graph_largest}
    starts = deterministic_starts(graph_largest, xy_by_cell, START_SEARCH_BUDGET)
    orders = direction_orders()
    wind_policies = []
    for wind_path in args.wind:
        ideal, rule = wind_cross_angle(wind_path)
        wind_policies.append({
            "wind_id": wind_path.stem,
            "input_sha256": sha256_file(wind_path),
            "ideal_crosswind_angle_deg": ideal,
            "rule": rule,
        })

    center_fields = ("t_sim_s", "step", "x", "y", "z", "yaw", "vx", "vy", "vz")
    pair_fields = center_fields + ("wind_id", "baseline_angle_deg", "baseline_length_m")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    candidates = []
    for start_index, start in enumerate(starts):
        route_id = f"AO_{len(candidates):02d}"
        direction_order = orders[start_index % len(orders)]
        walk, visited = dfs_walk(start, adjacency, direction_order)
        center_rows, traversal_length = resample_polyline_duration([xy_by_cell[cell] for cell in walk])
        plus_rows, minus_rows = [], []
        valid = len(center_rows) == EXPECTED_SAMPLES
        for policy in wind_policies:
            for sample in center_rows:
                angles, _ = feasible_angles(occupancy, sample["x"], sample["y"])
                ordered_angles = sorted(angles, key=lambda angle: (angular_gap(angle, policy["ideal_crosswind_angle_deg"]), angle))
                selected = next((angle for angle in ordered_angles if exact_baseline_is_free(occupancy, sample["x"], sample["y"], angle)), None)
                if selected is None:
                    valid = False
                    continue
                radians = math.radians(selected)
                direction = (math.cos(radians), math.sin(radians))
                common = {**sample, "wind_id": policy["wind_id"], "baseline_angle_deg": selected, "baseline_length_m": SEPARATION}
                plus_rows.append({**common, "x": sample["x"] + direction[0], "y": sample["y"] + direction[1]})
                minus_rows.append({**common, "x": sample["x"] - direction[0], "y": sample["y"] - direction[1]})
        candidate_dir = args.out_dir / route_id
        write_csv(candidate_dir / "CENTER.csv", center_fields, center_rows)
        write_csv(candidate_dir / "PLUS.csv", pair_fields, plus_rows)
        write_csv(candidate_dir / "MINUS.csv", pair_fields, minus_rows)
        heading_change = sum(angle_change(float(first["yaw"]), float(second["yaw"])) for first, second in zip(center_rows, center_rows[1:]))
        if any(point_state(occupancy, row["x"], row["y"]) != 0 for row in center_rows):
            valid = False
        if len(plus_rows) != EXPECTED_SAMPLES * len(wind_policies) or len(minus_rows) != EXPECTED_SAMPLES * len(wind_policies):
            valid = False
        candidate = {
            "route_id": route_id,
            "deterministic_start_search_index": start_index,
            "start_cell": list(start),
            "start_xy": list(xy_by_cell[start]),
            "neighbor_direction_order": [list(value) for value in direction_order],
            "center_samples": len(center_rows),
            "per_wind_pair_samples": len(plus_rows) // len(wind_policies),
            "graph_cells_visited": len(visited),
            "traversal_polyline_length_m": traversal_length,
            "resampled_path_length_m": (len(center_rows) - 1) * DT * SPEED,
            "total_absolute_heading_change_rad": heading_change,
            "duration_s": (len(center_rows) - 1) * DT,
            "geometry_valid": valid,
            "center_sha256": sha256_file(candidate_dir / "CENTER.csv"),
            "plus_sha256": sha256_file(candidate_dir / "PLUS.csv"),
            "minus_sha256": sha256_file(candidate_dir / "MINUS.csv"),
        }
        if valid:
            candidates.append(candidate)
            print(json.dumps(candidate), flush=True)
            if len(candidates) == CANDIDATE_BUDGET:
                break
        else:
            print(json.dumps({"rejected_geometry_only_candidate": route_id, "deterministic_start_search_index": start_index}), flush=True)

    if len(candidates) != CANDIDATE_BUDGET:
        raise RuntimeError(f"only {len(candidates)} valid candidates from {START_SEARCH_BUDGET} deterministic starts")
    manifest = {
        "schema": "SUPPORT_EXTENSION_ROUTE_CANDIDATE_FREEZE_V1",
        "candidate_budget": CANDIDATE_BUDGET,
        "deterministic_start_search_budget": START_SEARCH_BUDGET,
        "candidate_count": len(candidates),
        "selection_inputs": ["House02 occupancy", "2 m formation feasibility", "connectivity", "0.4 m altitude", "0.35 m/s speed", "222.8 s horizon", "recorded deployable wind"],
        "gas_read": False,
        "raw_cache_read": False,
        "source_identity_or_coordinates_read": False,
        "candidate_start_rule": "deterministic Euclidean farthest-point starts on the largest geometry-valid graph; lexicographic ties",
        "candidate_traversal_rule": "DFS with eight deterministic cardinal neighbor orders",
        "occupancy_sha256": occupancy.sha256,
        "separation_m": SEPARATION,
        "altitude_m": ALTITUDE,
        "duration_s": EXTENDED_HORIZON_S,
        "expected_samples": EXPECTED_SAMPLES,
        "cadence_s": DT,
        "speed_mps": SPEED,
        "wind_policies": wind_policies,
        "all_candidates_geometry_valid": all(candidate["geometry_valid"] for candidate in candidates),
        "candidates": candidates,
    }
    (args.out_dir / "CANDIDATE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "all_candidates_geometry_valid": manifest["all_candidates_geometry_valid"]}))


if __name__ == "__main__":
    main()
