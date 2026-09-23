#!/usr/bin/env python3
"""Build frozen geometry, wind-slice, and source-map context artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_occupancy(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    headers: dict[str, list[float]] = {}
    data_start = 0
    for i, line in enumerate(lines):
        if not line.startswith("#"):
            data_start = i
            break
        toks = line[1:].split()
        if toks:
            headers[toks[0]] = [float(x) for x in toks[1:]]
    nx, ny, nz = map(int, headers["num_cells"])
    # Legacy GADEN occupancy files use a standalone ';' separator between
    # z-slices; it is not a cell value.
    values = np.fromiter(
        (int(x) for line in lines[data_start:] if line.strip() != ";"
         for x in line.split()),
        dtype=np.int8,
    )
    expected = nx * ny * nz
    if values.size != expected:
        raise ValueError(f"occupancy values {values.size} != {expected}")
    # Each legacy slice has nx rows of length ny.  This matches GADEN's
    # linear index x + y*nx + z*nx*ny after the explicit transpose below.
    return headers, values.reshape((nz, nx, ny))


def read_wind(path: Path, nx: int, ny: int, nz: int) -> np.ndarray:
    n = nx * ny * nz
    raw = np.fromfile(path, dtype="<f8")
    if raw.size != 3 * n:
        raise ValueError(f"wind file {path} has {raw.size} doubles, expected {3*n}")
    fields = raw.reshape((3, nz, ny, nx))
    # Return [z, x, y, component], the same horizontal convention as the
    # concentration extractor and occupancy parser.
    return fields.transpose(1, 3, 2, 0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("occupancy", type=Path)
    ap.add_argument("wind_w1", type=Path)
    ap.add_argument("wind_w2", type=Path)
    ap.add_argument("out", type=Path)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    headers, occ = read_occupancy(args.occupancy)
    nx, ny, nz = map(int, headers["num_cells"])
    env_min = headers["env_min(m)"]
    cell = float(headers["cell_size(m)"][0])
    z = 0.20
    z_index = int(round((z - env_min[2]) / cell))
    if not 0 <= z_index < nz:
        raise ValueError(f"sensor z index {z_index} outside 0..{nz-1}")
    # Export in the same [x,y] indexing used by the official extractor.
    obstacle = occ[z_index, :, :].astype(np.uint8)
    np.save(out / "obstacle_mask_z0p20.npy", obstacle, allow_pickle=False)
    w1 = read_wind(args.wind_w1, nx, ny, nz)[z_index, :, :, :].astype(np.float32)
    w2 = read_wind(args.wind_w2, nx, ny, nz)[z_index, :, :, :].astype(np.float32)
    np.save(out / "wind_W1_z0p20.npy", w1, allow_pickle=False)
    np.save(out / "wind_W2_z0p20.npy", w2, allow_pickle=False)
    min_x, min_y = env_min[:2]
    sources = {"S1": (-2.242730141, -2.200880051, 0.20), "S2": (-4.342730045, 2.899120331, 0.20)}
    source_maps = {}
    for sid, (sx, sy, sz) in sources.items():
        ix = int(np.floor((sx - min_x) / cell))
        iy = int(np.floor((sy - min_y) / cell))
        m = np.zeros((nx, ny), dtype=np.uint8)
        if not (0 <= ix < nx and 0 <= iy < ny):
            raise ValueError(f"{sid} outside grid: {(ix, iy)}")
        if obstacle[ix, iy] != 0:
            raise ValueError(f"{sid} maps to occupied cell {(ix, iy)}")
        m[ix, iy] = 1
        np.save(out / f"source_map_{sid}.npy", m, allow_pickle=False)
        source_maps[sid] = {"xyz_m": [sx, sy, sz], "grid_xy": [ix, iy], "free": True}
    metadata = {
        "occupancy_path": str(args.occupancy),
        "occupancy_sha256": sha256(args.occupancy),
        "dimensions_xyz": [nx, ny, nz],
        "env_min_m": env_min,
        "cell_m": cell,
        "sensor_z_m": z,
        "sensor_z_index": z_index,
        "obstacle_mask_shape_xy": list(obstacle.shape),
        "wind_W1_path": str(args.wind_w1),
        "wind_W1_sha256": sha256(args.wind_w1),
        "wind_W2_path": str(args.wind_w2),
        "wind_W2_sha256": sha256(args.wind_w2),
        "source_maps": source_maps,
    }
    (out / "context_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"dimensions_xyz": [nx, ny, nz], "sensor_z_index": z_index, "source_maps": source_maps}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
