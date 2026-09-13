#!/usr/bin/env python3
"""Freeze a source-blind dual-receiver geometry from map, route, and wind only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


class Occupancy:
    def __init__(self, path: Path):
        lines = path.read_text(encoding="utf-8").splitlines()
        meta = {}
        for line in lines[:4]:
            key, *values = line.split()
            meta[key.split("(")[0]] = values
        self.minimum = np.asarray(list(map(float, meta["#env_min"])))
        self.maximum = np.asarray(list(map(float, meta["#env_max"])))
        self.dimensions = tuple(map(int, meta["#num_cells"]))
        self.cell = float(meta["#cell_size"][0])
        layers, rows = [], []
        for line in lines[4:]:
            if not line.strip():
                continue
            if line.strip() == ";":
                layers.append(rows)
                rows = []
            else:
                rows.append(list(map(int, line.split())))
        if rows:
            layers.append(rows)
        self.cells = np.asarray(layers, dtype=np.uint8).transpose(0, 2, 1)
        if self.cells.shape != (self.dimensions[2], self.dimensions[1], self.dimensions[0]):
            raise ValueError(f"occupancy shape mismatch: {self.cells.shape}")

    def state(self, point: np.ndarray) -> int:
        # GADEN converts the float vector to glm::ivec3.  GLM truncates toward
        # zero; np.floor disagrees just outside a negative map boundary.
        scaled = (np.asarray(point, dtype=np.float32) - self.minimum.astype(np.float32)) / np.float32(self.cell)
        index = scaled.astype(int)
        if any(value < 0 or value >= limit for value, limit in zip(index, self.dimensions)):
            return 3
        x, y, z = index
        return int(self.cells[z, y, x])

    def corridor_free(self, center: np.ndarray, direction: np.ndarray, length: float) -> bool:
        count = max(3, int(math.ceil(length / (self.cell / 2.0))) + 1)
        for displacement in np.linspace(-length / 2.0, length / 2.0, count):
            point = center + np.asarray([direction[0] * displacement, direction[1] * displacement, 0.0])
            if self.state(point) != 0:
                return False
        return True


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--wind", action="append", type=Path, required=True)
    parser.add_argument("--safe-separation-m", type=float, default=2.0)
    parser.add_argument("--practical-cap-m", type=float, default=5.0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    occupancy = Occupancy(args.occupancy)
    route = read_csv(args.route)
    centers = np.asarray([[float(row["x"]), float(row["y"]), float(row["z"])] for row in route])
    wind_reports = []
    wind_maxima = []

    for wind_path in args.wind:
        rows = read_csv(wind_path)
        vectors = np.asarray([[float(row["raw_wind_u"]), float(row["raw_wind_v"])] for row in rows])
        active = np.linalg.norm(vectors, axis=1) > 1e-6
        if not np.any(active):
            along = np.asarray([1.0, 0.0])
            orientation_rule = "MAP_FRAME_X_FALLBACK"
        else:
            along = np.median(vectors[active], axis=0)
            along = along / np.linalg.norm(along)
            orientation_rule = "MEDIAN_DEPLOYABLE_WIND_CROSS_DIRECTION"
        cross = np.asarray([-along[1], along[0]])
        candidates = np.arange(2.0 * occupancy.cell, args.practical_cap_m + occupancy.cell / 2.0, occupancy.cell)
        usable_counts = []
        for length in candidates:
            usable_counts.append(sum(occupancy.corridor_free(center, cross, float(length)) for center in centers))
        possible = [float(length) for length, count in zip(candidates, usable_counts) if count > 0]
        maximum = max(possible) if possible else 0.0
        wind_maxima.append(maximum)
        wind_reports.append({
            "wind_input": wind_path.name,
            "orientation_rule": orientation_rule,
            "along_wind_unit": along.tolist(),
            "cross_wind_unit": cross.tolist(),
            "maximum_span_with_any_free_corridor_m": maximum,
            "usable_samples_at_safe_separation": int(sum(occupancy.corridor_free(center, cross, args.safe_separation_m) for center in centers)),
            "route_samples": len(centers),
        })

    r_min = max(2.0 * occupancy.cell, args.safe_separation_m)
    r_max = min(wind_maxima) if wind_maxima else 0.0
    feasible = r_max > r_min
    scales = [r_min, math.sqrt(r_min * r_max), r_max] if feasible else []
    center_states = [occupancy.state(point) for point in centers]
    result = {
        "schema": "DUAL_UAV_SOURCE_BLIND_FORMATION_FREEZE_V1",
        "gas_or_source_values_read": False,
        "center_route_selection_rule": "LEXICOGRAPHIC_FIRST_EXISTING_FROZEN_ROUTE",
        "center_route": args.route.stem,
        "center_route_sha256": sha256_file(args.route),
        "occupancy_sha256": sha256_file(args.occupancy),
        "gas_grid_spacing_m": occupancy.cell,
        "declared_safe_receiver_separation_m": args.safe_separation_m,
        "declared_practical_formation_cap_m": args.practical_cap_m,
        "r_min_m": r_min,
        "r_max_m": r_max,
        "logarithmic_scales_m": scales,
        "center_route_free_samples": int(sum(state == 0 for state in center_states)),
        "center_route_blocked_samples": int(sum(state != 0 for state in center_states)),
        "center_route_samples": len(center_states),
        "wind_geometry": wind_reports,
        "status": "PASS_GEOMETRY_FROZEN" if feasible else "STOP_RMAX_NOT_GREATER_THAN_RMIN",
        "stop_reason": None if feasible else "Existing frozen route and House02 free-space geometry cannot support the declared large-UAV separation in every wind orientation.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "r_min_m": r_min, "r_max_m": r_max}))


if __name__ == "__main__":
    main()
