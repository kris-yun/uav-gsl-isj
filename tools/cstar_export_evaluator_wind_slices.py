#!/usr/bin/env python3
"""Export a map-aligned GADEN wind slice for evaluator-side C2 diagnostics.

This tool is intentionally outside PMFS runtime ingress.  Raw GADEN volumes
are hidden simulator state: they may establish that a prospective sparse
filament provider respects the same grid, time order and navigation slice as
the evaluator, but they must never be passed to online M1 scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "ctpi_cstar"))
from environment_runtime import Grid3D, decode_wind, numeric_sequence, sha256  # noqa: E402


def require(condition: bool, tag: str) -> None:
    if not condition:
        raise ValueError("CSTAR_EVALUATOR_WIND_SLICE:" + tag)


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alignment", required=True, type=Path)
    parser.add_argument("--house", required=True, choices=("H01", "H02", "H03"))
    parser.add_argument("--occupancy", required=True, type=Path)
    parser.add_argument("--wind-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    alignment = json.loads(args.alignment.read_text(encoding="utf-8"))
    row = alignment["houses"][args.house]
    require(sha256(args.occupancy) == row["occupancy_sha256"], "OCCUPANCY_HASH")
    grid = Grid3D.from_occupancy(args.occupancy)
    z_index = int(row["z_index"])
    require(0 <= z_index < grid.dimensions[2], "Z_INDEX")
    require(abs((grid.minimum[2] + (z_index + 0.5) * grid.cell_size) -
                float(row["navigation_height_m"])) <= grid.cell_size * 0.51, "NAVIGATION_SLICE")
    files = numeric_sequence(args.wind_dir, "wind_iteration_")
    require(len(files) == 11, "WIND_SEQUENCE_COUNT")

    nx, ny, nz = grid.dimensions
    cells = nx * ny * nz
    layers: list[np.ndarray] = []
    wind_records: list[dict[str, object]] = []
    start = z_index * nx * ny
    end = start + nx * ny
    for index, path in enumerate(files):
        vectors, record = decode_wind(path, cells)
        layer = np.ascontiguousarray(vectors[start:end].reshape(ny, nx, 3), dtype="<f4")
        require(np.isfinite(layer).all(), "NONFINITE_LAYER")
        layers.append(layer)
        wind_records.append({"index": index, **record})
    wind_uvz = np.stack(layers, axis=0)
    require(wind_uvz.shape == (11, ny, nx, 3), "SLICE_SHAPE")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output, wind_uvz=wind_uvz)
    output_hash = hashlib.sha256(args.output.read_bytes()).hexdigest()
    manifest = {
        "contract": "CSTAR_EVALUATOR_WIND_SLICE_V1",
        "purpose": "evaluator-only GADEN alignment diagnostic; forbidden online M1 input",
        "house": args.house,
        "geometry_identity": row["geometry_identity"],
        "occupancy_sha256": row["occupancy_sha256"],
        "grid": {"minimum": grid.minimum, "maximum": grid.maximum,
                 "dimensions": grid.dimensions, "cell_size_m": grid.cell_size},
        "z_index": z_index,
        "navigation_height_m": row["navigation_height_m"],
        "array": {"name": "wind_uvz", "shape": list(wind_uvz.shape), "dtype": "float32",
                  "flat_index": "x + nx*y + nx*ny*z", "sha256": hashlib.sha256(wind_uvz.tobytes()).hexdigest()},
        "wind_files": wind_records,
        "output": {"path": str(args.output.resolve()), "sha256": output_hash},
    }
    manifest_path = args.output.with_suffix(args.output.suffix + ".manifest.json")
    manifest_path.write_text(canonical_json(manifest) + "\n", encoding="utf-8")
    print("CSTAR_EVALUATOR_WIND_SLICE=PASS")
    print(manifest_path)


if __name__ == "__main__":
    main()
