#!/usr/bin/env python3
"""Build a bounded source/gas-blind dual-feasible route candidate set."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import deque
from pathlib import Path

import numpy as np

from audit_occupancy_native_parity import CustomOccupancy
from build_house02_global_dual_route import (
    ALTITUDE,
    ANGLES,
    SEPARATION,
    angular_gap,
    components,
    edge_is_feasible,
    exact_baseline_is_free,
    feasible_angles,
    point_state,
    resample_polyline,
    wind_cross_angle,
)


CANDIDATE_BUDGET = 12
START_SEARCH_BUDGET = 24
BASE_DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def deterministic_starts(component, xy_by_cell, count):
    ordered = sorted(component, key=lambda cell: (cell[1], cell[0]))
    selected = [ordered[0]]
    coordinates = np.asarray([xy_by_cell[cell] for cell in ordered], dtype=float)
    minimum_squared = np.sum((coordinates - np.asarray(xy_by_cell[selected[0]])) ** 2, axis=1)
    while len(selected) < count:
        maximum = float(minimum_squared.max())
        candidates = [ordered[index] for index in np.flatnonzero(np.isclose(minimum_squared, maximum, rtol=0.0, atol=1e-12))]
        chosen = min(candidates, key=lambda cell: (cell[1], cell[0]))
        selected.append(chosen)
        squared = np.sum((coordinates - np.asarray(xy_by_cell[chosen])) ** 2, axis=1)
        minimum_squared = np.minimum(minimum_squared, squared)
    return selected


def build_adjacency(component, xy_by_cell, occupancy):
    adjacency = {cell: [] for cell in component}
    for cell in sorted(component):
        for dx, dy in ((1, 0), (0, 1)):
            neighbor = (cell[0] + dx, cell[1] + dy)
            if neighbor in component and edge_is_feasible(occupancy, xy_by_cell[cell], xy_by_cell[neighbor]):
                adjacency[cell].append(neighbor)
                adjacency[neighbor].append(cell)
    return adjacency


def direction_orders():
    orders = []
    for reverse in (False, True):
        base = BASE_DIRECTIONS if not reverse else tuple(reversed(BASE_DIRECTIONS))
        for offset in range(4):
            orders.append(base[offset:] + base[:offset])
    return orders


def dfs_walk(start, adjacency, direction_order):
    rank = {direction: index for index, direction in enumerate(direction_order)}

    def ordered_neighbors(cell):
        return sorted(
            adjacency[cell],
            key=lambda neighbor: (rank[(neighbor[0] - cell[0], neighbor[1] - cell[1])], neighbor),
        )

    visited, walk = {start}, [start]
    stack = [(start, iter(ordered_neighbors(start)))]
    while stack:
        _, iterator = stack[-1]
        try:
            neighbor = next(iterator)
        except StopIteration:
            stack.pop()
            if stack:
                walk.append(stack[-1][0])
            continue
        if neighbor in visited:
            continue
        visited.add(neighbor)
        walk.append(neighbor)
        stack.append((neighbor, iter(ordered_neighbors(neighbor))))
    return walk, visited


def angle_change(first, second):
    return abs(math.atan2(math.sin(second - first), math.cos(second - first)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--wind", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
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
    graph_components = components(graph_nodes)
    graph_largest = graph_components[0]
    adjacency = {cell: [neighbor for neighbor in adjacency[cell] if neighbor in graph_largest] for cell in graph_largest}
    starts = deterministic_starts(graph_largest, xy_by_cell, START_SEARCH_BUDGET)
    orders = direction_orders()
    wind_policies = []
    for wind_path in args.wind:
        ideal, rule = wind_cross_angle(wind_path)
        wind_policies.append({"wind_id": wind_path.stem, "input_sha256": sha256_file(wind_path), "ideal_crosswind_angle_deg": ideal, "rule": rule})
    candidates = []
    pair_fields = ("t_sim_s", "step", "x", "y", "z", "yaw", "vx", "vy", "vz", "wind_id", "baseline_angle_deg", "baseline_length_m")
    center_fields = ("t_sim_s", "step", "x", "y", "z", "yaw", "vx", "vy", "vz")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for start_index, start in enumerate(starts):
        candidate_index = len(candidates)
        route_id = f"AO_{candidate_index:02d}"
        direction_order = orders[start_index % len(orders)]
        walk, visited = dfs_walk(start, adjacency, direction_order)
        center, traversal_length, duration = resample_polyline([xy_by_cell[cell] for cell in walk])
        center_rows = list(center)
        plus_rows, minus_rows = [], []
        valid = len(center_rows) == 750
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
        if len(plus_rows) != 2250 or len(minus_rows) != 2250:
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
            "resampled_path_length_m": (len(center_rows) - 1) * 0.2 * 0.35,
            "total_absolute_heading_change_rad": heading_change,
            "duration_s": duration,
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
        "schema": "OBSERVABILITY_ROUTE_CANDIDATE_FREEZE_V1",
        "candidate_budget": CANDIDATE_BUDGET,
        "deterministic_start_search_budget": START_SEARCH_BUDGET,
        "candidate_count": len(candidates),
        "selection_inputs": ["House02 occupancy", "2 m formation feasibility", "connectivity", "0.4 m altitude", "0.35 m/s speed", "150 s duration", "recorded deployable wind"],
        "gas_read": False,
        "source_identity_or_coordinates_read": False,
        "candidate_start_rule": "deterministic Euclidean farthest-point starts on the largest geometry-valid graph; lexicographic ties",
        "candidate_traversal_rule": "DFS with eight deterministic cardinal neighbor orders",
        "occupancy_sha256": occupancy.sha256,
        "separation_m": SEPARATION,
        "altitude_m": ALTITUDE,
        "duration_s": 150.0,
        "cadence_s": 0.2,
        "speed_mps": 0.35,
        "wind_policies": wind_policies,
        "all_candidates_geometry_valid": all(candidate["geometry_valid"] for candidate in candidates),
        "candidates": candidates,
    }
    (args.out_dir / "CANDIDATE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "all_candidates_geometry_valid": manifest["all_candidates_geometry_valid"]}))


if __name__ == "__main__":
    main()
