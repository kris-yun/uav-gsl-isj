#!/usr/bin/env python3
"""Export sparse 2-D concentration/wind snapshots from a saved GADEN realization.

Purpose:
    M7 O0 analytical mechanism-splitting falsification.

This exporter uses GADEN's own PlaybackSimulation + SampleConcentration/SampleWind
rather than interpolating robot-path measurements.

Requires:
    gaden_core built with GENERATE_PYTHON_BINDINGS=ON
    importable gaden_py module

Example:
    python export_gaden_playback_slices.py \
      --config-dir /path/to/environment_configuration \
      --realization-dir /path/to/FilamentSimulation_... \
      --height 0.20 \
      --iterations 200,240,280,320,360 \
      --out /tmp/o0_export.npz

Notes:
- This script assumes the supplied config-dir can be read by the installed
  gaden_core version. If the user's historical ROS scenario is not directly in
  gaden_core project format, do NOT silently rebuild the geometry. Use the
  corresponding canonical environment configuration or sample through the
  existing GADEN playback ROS stack and document that route.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from gaden_py import gaden


def parse_iterations(raw: str) -> list[int]:
    vals = sorted({int(x.strip()) for x in raw.split(",") if x.strip()})
    if not vals:
        raise ValueError("No iterations provided")
    if vals[0] < 0:
        raise ValueError("Iterations must be nonnegative")
    return vals


def v3(x: float, y: float, z: float):
    return gaden.Vector3(float(x), float(y), float(z))


def v3i(i: int, j: int, k: int):
    return gaden.Vector3i(int(i), int(j), int(k))


def closest_z_index(env, height: float) -> int:
    nz = int(env.description.dimensions.z)
    candidates = []
    for iz in range(nz):
        p = env.coordsOfCellCenter(v3i(0, 0, iz))
        candidates.append(abs(float(p.z) - height))
    return int(np.argmin(candidates))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config-dir", required=True)
    ap.add_argument("--realization-dir", required=True)
    ap.add_argument("--height", type=float, required=True)
    ap.add_argument("--iterations", required=True,
                    help="comma-separated saved playback iteration numbers")
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", default="")
    args = ap.parse_args()

    iterations = parse_iterations(args.iterations)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    config_meta = gaden.EnvironmentConfigMetadata(args.config_dir)
    rr = config_meta.ReadDirectory()
    # cppyy enum/string formatting differs by build, so preserve but do not
    # enforce a fragile Python equality check here.
    env_config = gaden.Preprocessing.Preprocess(config_meta)
    env = env_config.environment

    iz = closest_z_index(env, args.height)
    nx = int(env.description.dimensions.x)
    ny = int(env.description.dimensions.y)

    # Build the 2-D geometry once.
    xyz = []
    ij = []
    occupancy = []
    free_mask = []

    free_state = gaden.Environment.CellState.Free
    outlet_state = gaden.Environment.CellState.Outlet

    for ix in range(nx):
        for iy in range(ny):
            idx = v3i(ix, iy, iz)
            p = env.coordsOfCellCenter(idx)
            state = env.at(idx)
            xyz.append([float(p.x), float(p.y), float(p.z)])
            ij.append([ix, iy])
            occupancy.append(int(state))
            free_mask.append(bool(state == free_state or state == outlet_state))

    xyz = np.asarray(xyz, dtype=np.float32)
    ij = np.asarray(ij, dtype=np.int32)
    occupancy = np.asarray(occupancy, dtype=np.uint8)
    free_mask = np.asarray(free_mask, dtype=bool)

    # Start playback at the first requested iteration and advance sequentially.
    params = gaden.PlaybackSimulation.Parameters()
    params.startIteration = int(iterations[0])
    params.resultsDirectory = args.realization_dir

    loop = gaden.LoopConfig()
    loop.loop = False

    sim = gaden.PlaybackSimulation(params, env_config, loop)

    concentration_frames = []
    wind_frames = []
    loaded_iterations = []

    target_set = set(iterations)
    current = iterations[0]
    last = iterations[-1]

    while current <= last:
        sim.AdvanceTimestep()

        if current in target_set:
            c = np.full(len(xyz), np.nan, dtype=np.float32)
            w = np.full((len(xyz), 3), np.nan, dtype=np.float32)

            for n, pxyz in enumerate(xyz):
                if not free_mask[n]:
                    c[n] = 0.0
                    w[n] = 0.0
                    continue

                point = v3(*pxyz)
                c[n] = float(sim.SampleConcentration(point))

                # SampleWind(point) follows the wind index loaded from the saved
                # playback iteration.
                ww = sim.SampleWind(point)
                w[n] = [float(ww.x), float(ww.y), float(ww.z)]

            concentration_frames.append(c)
            wind_frames.append(w)
            loaded_iterations.append(current)

        current += 1

    concentration = np.stack(concentration_frames, axis=0)
    wind = np.stack(wind_frames, axis=0)

    if loaded_iterations != iterations:
        raise RuntimeError(
            f"Requested iterations {iterations}, exported {loaded_iterations}"
        )

    np.savez_compressed(
        out_path,
        iterations=np.asarray(loaded_iterations, dtype=np.int32),
        xyz=xyz,
        ij=ij,
        occupancy=occupancy,
        free_mask=free_mask,
        concentration=concentration,
        wind=wind,
        z_index=np.asarray([iz], dtype=np.int32),
        requested_height=np.asarray([args.height], dtype=np.float32),
    )

    manifest = {
        "config_dir": str(Path(args.config_dir).resolve()),
        "realization_dir": str(Path(args.realization_dir).resolve()),
        "iterations": loaded_iterations,
        "requested_height_m": args.height,
        "z_index": iz,
        "grid_nx": nx,
        "grid_ny": ny,
        "num_plane_cells": int(nx * ny),
        "num_free_or_outlet_cells": int(free_mask.sum()),
        "read_directory_result": str(rr),
        "output_npz": str(out_path.resolve()),
        "concentration_shape": list(concentration.shape),
        "wind_shape": list(wind.shape),
        "method": "gaden.PlaybackSimulation + SampleConcentration + SampleWind",
    }

    manifest_path = (
        Path(args.manifest)
        if args.manifest
        else out_path.with_suffix(".manifest.json")
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
