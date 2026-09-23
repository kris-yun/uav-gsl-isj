#!/usr/bin/env python3
"""Validate predeclared C0.5 source positions against GADEN 3-D occupancy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


SOURCES = (
    {"id": "S1", "x": -2.242730141, "y": -2.200880051, "z": 0.20},
    {"id": "S2", "x": -4.342730045, "y": 2.899120331, "z": 0.20},
)


def load_grid(path: Path):
    lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    env_min = tuple(float(x) for x in lines[0].split()[1:])
    env_max = tuple(float(x) for x in lines[1].split()[1:])
    dims = tuple(int(x) for x in lines[2].split()[1:])
    cell_size = float(lines[3].split()[1])
    values = []
    x_idx = y_idx = z_idx = 0
    for line in lines[4:]:
        if line == ";":
            z_idx += 1
            x_idx = y_idx = 0
            continue
        row = [int(x) for x in line.split()]
        if len(row) != dims[1]:
            raise ValueError(f"{path}: row length {len(row)} != dim_y {dims[1]}")
        values.extend((x_idx, y_idx, z_idx, state) for y_idx, state in enumerate(row))
        x_idx += 1
        y_idx = 0
    if len(values) != math.prod(dims):
        raise ValueError(f"{path}: parsed {len(values)} cells != {math.prod(dims)}")
    # GADEN indexFrom3D is x + y*dim_x + z*dim_x*dim_y.
    cells = {(x, y, z): state for x, y, z, state in values}
    return env_min, env_max, dims, cell_size, cells


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--occupancy", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    env_min, env_max, dims, cell_size, cells = load_grid(args.occupancy)
    results = []
    for source in SOURCES:
        indices = tuple(
            math.floor((source[k] - env_min[i]) / cell_size)
            for i, k in enumerate(("x", "y", "z"))
        )
        in_bounds = all(0 <= indices[k] < dims[k] for k in range(3))
        state = cells.get(indices, 3)
        obstacle_distance = None
        if in_bounds:
            obstacles = [idx for idx, value in cells.items() if value != 0]
            if obstacles:
                obstacle_distance = min(
                    math.sqrt(sum((indices[k] - other[k]) ** 2 for k in range(3)))
                    * cell_size
                    for other in obstacles
                )
        results.append(
            {
                **source,
                "grid_index_xyz": list(indices),
                "in_bounds": in_bounds,
                "cell_state": state,
                "free": bool(in_bounds and state == 0),
                "nearest_nonfree_distance_m": obstacle_distance,
            }
        )
    payload = {
        "occupancy": str(args.occupancy),
        "occupancy_sha256": hashlib.sha256(args.occupancy.read_bytes()).hexdigest(),
        "env_min_m": list(env_min),
        "env_max_m": list(env_max),
        "dims_xyz": list(dims),
        "cell_size_m": cell_size,
        "sources": results,
        "all_free": all(x["free"] for x in results),
        "source_to_source_distance_m": math.dist(
            [SOURCES[0][k] for k in ("x", "y", "z")],
            [SOURCES[1][k] for k in ("x", "y", "z")],
        ),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
