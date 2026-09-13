#!/usr/bin/env python3
"""Map-only House02 2 m aperture map and deterministic dual-UAV route."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import deque
from pathlib import Path

import numpy as np

from audit_occupancy_native_parity import CustomOccupancy


DT = 0.2
SPEED = 0.35
TARGET_DURATION = 150.0
ALTITUDE = 0.4
SEPARATION = 2.0
CAP = 5.0
ANGLE_STEP_DEG = 5
ANGLES = tuple(range(0, 180, ANGLE_STEP_DEG))
ANGLE_RADIANS = np.radians(np.asarray(ANGLES, dtype=np.float32))
ANGLE_COS = np.cos(ANGLE_RADIANS)[:, None]
ANGLE_SIN = np.sin(ANGLE_RADIANS)[:, None]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_state(occupancy: CustomOccupancy, x: float, y: float, z: float = ALTITUDE) -> int:
    return occupancy.query((x, y, z))[0]


def feasible_angles(occupancy: CustomOccupancy, x: float, y: float):
    # Quarter-cell sampling avoids accepting a baseline that only appears free
    # because a 0.05 m sample lands on the favorable side of a cell boundary.
    step = np.float32(float(occupancy.cell) / 4.0)
    half_spans = np.arange(step, np.float32(CAP / 2.0) + step / 2.0, step, dtype=np.float32)[None, :]
    x0, y0 = np.float32(x), np.float32(y)
    plus_x = x0 + ANGLE_COS * half_spans
    plus_y = y0 + ANGLE_SIN * half_spans
    minus_x = x0 - ANGLE_COS * half_spans
    minus_y = y0 - ANGLE_SIN * half_spans

    def states(xs, ys):
        ix = ((xs - occupancy.minimum[0]) / occupancy.cell).astype(np.int64)
        iy = ((ys - occupancy.minimum[1]) / occupancy.cell).astype(np.int64)
        iz = int((np.float32(ALTITUDE) - occupancy.minimum[2]) / occupancy.cell)
        valid = (ix >= 0) & (ix < occupancy.dimensions[0]) & (iy >= 0) & (iy < occupancy.dimensions[1])
        output = np.full(ix.shape, 3, dtype=np.uint8)
        output[valid] = occupancy.cells[iz, iy[valid], ix[valid]]
        return output

    corridor_free = (states(plus_x, plus_y) == 0) & (states(minus_x, minus_y) == 0)
    prefix = np.cumprod(corridor_free, axis=1, dtype=np.uint8)
    half_counts = prefix.sum(axis=1)
    spans = np.minimum(np.float32(CAP), np.float32(2.0) * step * half_counts)
    feasible = tuple(angle for angle, span in zip(ANGLES, spans) if float(span) + 1e-7 >= SEPARATION)
    return feasible, float(spans.max(initial=0.0))


def compress_angles(angles):
    if not angles:
        return ""
    runs = []
    start = previous = angles[0]
    for angle in angles[1:]:
        if angle == previous + ANGLE_STEP_DEG:
            previous = angle
            continue
        runs.append((start, previous))
        start = previous = angle
    runs.append((start, previous))
    return ";".join(str(first) if first == last else f"{first}-{last}" for first, last in runs)


def components(nodes):
    remaining = set(nodes)
    found = []
    directions = ((-1, 0), (0, -1), (0, 1), (1, 0))
    while remaining:
        start = min(remaining)
        queue = deque([start])
        component = {start}
        remaining.remove(start)
        while queue:
            x, y = queue.popleft()
            for dx, dy in directions:
                neighbor = (x + dx, y + dy)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        found.append(component)
    return sorted(found, key=lambda component: (-len(component), min(component)))


def edge_is_feasible(occupancy, first_xy, second_xy):
    for fraction in (0.25, 0.5, 0.75):
        x = first_xy[0] + fraction * (second_xy[0] - first_xy[0])
        y = first_xy[1] + fraction * (second_xy[1] - first_xy[1])
        angles, _ = feasible_angles(occupancy, x, y)
        if not angles:
            return False
    return True


def dfs_walk(component, xy_by_cell, occupancy):
    start = min(component, key=lambda cell: (cell[1], cell[0]))
    directions = ((1, 0), (0, 1), (-1, 0), (0, -1))

    def neighbors(cell):
        values = []
        for dx, dy in directions:
            neighbor = (cell[0] + dx, cell[1] + dy)
            if neighbor in component and edge_is_feasible(occupancy, xy_by_cell[cell], xy_by_cell[neighbor]):
                values.append(neighbor)
        return values

    visited = {start}
    walk = [start]
    stack = [(start, iter(neighbors(start)))]
    while stack:
        current, iterator = stack[-1]
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
        stack.append((neighbor, iter(neighbors(neighbor))))
    return walk, visited


def resample_polyline(points):
    segments = []
    for first, second in zip(points, points[1:]):
        length = math.hypot(second[0] - first[0], second[1] - first[1])
        if length > 1e-12:
            segments.append((first, second, length))
    total_length = sum(segment[2] for segment in segments)
    duration = min(TARGET_DURATION, total_length / SPEED)
    sample_count = min(750, int(math.floor(duration / DT + 1e-9)) + 1)
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
        samples.append({"t_sim_s": time_s, "step": index + 1, "x": x, "y": y, "z": ALTITUDE, "yaw": math.atan2(vy, vx), "vx": vx, "vy": vy, "vz": 0.0})
    return samples, total_length, duration


def angular_gap(first, second):
    delta = abs((first - second) % 180.0)
    return min(delta, 180.0 - delta)


def exact_baseline_is_free(occupancy: CustomOccupancy, x: float, y: float, angle_deg: float) -> bool:
    """Validate the serialized 2 m segment with parity-qualified scalar indexing."""
    radians = math.radians(angle_deg)
    direction = np.asarray((math.cos(radians), math.sin(radians), 0.0), dtype=np.float64)
    center = np.asarray((x, y, ALTITUDE), dtype=np.float64)
    minus = center - direction * (SEPARATION / 2.0)
    plus = center + direction * (SEPARATION / 2.0)
    serialized_distance = float(np.linalg.norm(plus - minus))
    count = max(3, int(math.ceil(serialized_distance / 0.025)) + 1)
    return all(
        occupancy.query(minus + fraction * (plus - minus))[0] == 0
        for fraction in np.linspace(0.0, 1.0, count)
    )


def wind_cross_angle(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        vectors = np.asarray([(float(row["raw_wind_u"]), float(row["raw_wind_v"])) for row in csv.DictReader(stream)])
    active = np.linalg.norm(vectors, axis=1) > 1e-6
    if not np.any(active):
        return 0.0, "MAP_FRAME_X_FALLBACK"
    median = np.median(vectors[active], axis=0)
    along = math.degrees(math.atan2(median[1], median[0])) % 180.0
    return (along + 90.0) % 180.0, "MEDIAN_PAST_DEPLOYABLE_WIND_CROSS_DIRECTION"


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--wind", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    occupancy = CustomOccupancy(args.occupancy)
    nx, ny, _ = occupancy.dimensions
    z_index = int((np.float32(ALTITUDE) - occupancy.minimum[2]) / occupancy.cell)
    map_rows = []
    feasible_cells = set()
    xy_by_cell = {}
    angles_by_cell = {}
    max_span_by_cell = {}
    for ix in range(nx):
        for iy in range(ny):
            x = float(occupancy.minimum[0] + (np.float32(ix) + np.float32(0.5)) * occupancy.cell)
            y = float(occupancy.minimum[1] + (np.float32(iy) + np.float32(0.5)) * occupancy.cell)
            if point_state(occupancy, x, y) != 0:
                continue
            angles, maximum = feasible_angles(occupancy, x, y)
            cell = (ix, iy)
            xy_by_cell[cell] = (x, y)
            angles_by_cell[cell] = angles
            max_span_by_cell[cell] = maximum
            if angles:
                feasible_cells.add(cell)
            map_rows.append({"center_ix": ix, "center_iy": iy, "center_x": x, "center_y": y, "center_z": ALTITUDE, "number_feasible_orientations": len(angles), "maximum_safe_span_m": maximum, "feasible_orientation_intervals_deg": compress_angles(angles)})
    args.out_dir.mkdir(parents=True, exist_ok=True)
    map_path = args.out_dir / "FORMATION_FEASIBILITY_MAP_2M.csv.gz"
    with gzip.open(map_path, "wt", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=map_rows[0].keys())
        writer.writeheader()
        writer.writerows(map_rows)
    found_components = components(feasible_cells)
    largest = found_components[0] if found_components else set()
    summary = {
        "schema": "HOUSE02_2M_GLOBAL_FORMATION_FEASIBILITY_V1",
        "occupancy_sha256": occupancy.sha256,
        "altitude_m": ALTITUDE,
        "z_cell_index": z_index,
        "separation_m": SEPARATION,
        "practical_cap_m": CAP,
        "orientation_grid_deg": list(ANGLES),
        "geometry_semantics": "POINT_RECEIVER_WITH_FREE_CENTERLINE_CORRIDOR",
        "free_center_cells": len(map_rows),
        "formation_feasible_center_cells": len(feasible_cells),
        "formation_feasible_fraction": len(feasible_cells) / len(map_rows) if map_rows else 0.0,
        "connected_component_count": len(found_components),
        "largest_component_cells": len(largest),
        "largest_component_area_m2": len(largest) * float(occupancy.cell) ** 2,
        "HOUSE02_2M_GLOBAL_FEASIBILITY": "PASS" if largest else "NO_GO",
    }
    (args.out_dir / "FORMATION_FEASIBILITY_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not largest:
        print(json.dumps(summary))
        return

    walk, visited = dfs_walk(largest, xy_by_cell, occupancy)
    points = [xy_by_cell[cell] for cell in walk]
    center_samples, traversal_length, achievable_duration = resample_polyline(points)
    route_valid = len(center_samples) > 0
    center_rows = []
    plus_rows = []
    minus_rows = []
    wind_policies = []
    for wind_path in args.wind:
        wind_id = wind_path.stem
        ideal, rule = wind_cross_angle(wind_path)
        wind_policies.append({"wind_id": wind_id, "input_sha256": sha256_file(wind_path), "ideal_crosswind_angle_deg": ideal, "rule": rule})
        for sample in center_samples:
            angles, _ = feasible_angles(occupancy, sample["x"], sample["y"])
            if not angles:
                route_valid = False
                continue
            ordered_angles = sorted(angles, key=lambda angle: (angular_gap(angle, ideal), angle))
            selected = next(
                (angle for angle in ordered_angles if exact_baseline_is_free(occupancy, sample["x"], sample["y"], angle)),
                None,
            )
            if selected is None:
                route_valid = False
                continue
            direction = (math.cos(math.radians(selected)), math.sin(math.radians(selected)))
            common = {**sample, "wind_id": wind_id, "baseline_angle_deg": selected, "baseline_length_m": SEPARATION}
            plus_rows.append({**common, "x": sample["x"] + direction[0] * SEPARATION / 2.0, "y": sample["y"] + direction[1] * SEPARATION / 2.0})
            minus_rows.append({**common, "x": sample["x"] - direction[0] * SEPARATION / 2.0, "y": sample["y"] - direction[1] * SEPARATION / 2.0})
    for sample in center_samples:
        center_rows.append(sample)
    center_fields = ("t_sim_s", "step", "x", "y", "z", "yaw", "vx", "vy", "vz")
    pair_fields = ("t_sim_s", "step", "x", "y", "z", "yaw", "vx", "vy", "vz", "wind_id", "baseline_angle_deg", "baseline_length_m")
    write_csv(args.out_dir / "FORMATION_CENTER_ROUTE.csv", center_fields, center_rows)
    write_csv(args.out_dir / "FORMATION_PLUS_ROUTE.csv", pair_fields, plus_rows)
    write_csv(args.out_dir / "FORMATION_MINUS_ROUTE.csv", pair_fields, minus_rows)
    policy = {
        "schema": "HOUSE02_SOURCE_BLIND_FORMATION_POLICY_V1",
        "route_inputs": ["occupancy", "connectivity", "fixed altitude", "0.35 m/s speed", "2.0 m formation feasibility"],
        "forbidden_inputs_read": [],
        "gas_read": False,
        "source_identity_read": False,
        "component_rule": "largest 4-connected feasible component, lexicographic tie break",
        "route_rule": "deterministic DFS coverage walk with geometry-valid quarter/midpoint edges",
        "orientation_rule": "feasible 5-degree angle nearest frozen crosswind; smaller angle tie break",
        "wind_policies": wind_policies,
        "center_samples": len(center_rows),
        "per_wind_pair_samples": len(plus_rows) // len(args.wind),
        "traversal_cells_visited": len(visited),
        "traversal_polyline_length_m": traversal_length,
        "achievable_duration_s": achievable_duration,
        "target_150s_achieved": len(center_rows) == 750,
        "all_python_geometry_checks_pass": route_valid and len(plus_rows) == len(center_rows) * len(args.wind),
        "status": "PRE_NATIVE_GEOMETRY_PASS" if route_valid and len(center_rows) == 750 else "NO_GO_ROUTE",
    }
    (args.out_dir / "FORMATION_POLICY_FREEZE.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**summary, **policy}))


if __name__ == "__main__":
    main()
