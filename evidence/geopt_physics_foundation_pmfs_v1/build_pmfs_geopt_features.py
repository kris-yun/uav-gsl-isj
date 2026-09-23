#!/usr/bin/env python3
"""Build a GeoPT-compatible 2-D PMFS House feature tensor.

Scientific use:
- interface/runtime probe only when historical R2 wind is supplied;
- scientific training/evaluation must use recovered Native ground-truth wind.

Inputs:
  measured_hit_probability.csv
  estimated_wind.csv

Output:
  NPZ with:
    x          [N,3]  model coordinate input
    fx         [N,11] GeoPT physical feature input
    cell_index [N]
"""

import argparse
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hit", required=True)
    ap.add_argument("--wind", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--target-x-extent", type=float, default=5.0)
    args = ap.parse_args()

    hit = pd.read_csv(args.hit)
    wind = pd.read_csv(args.wind)

    free = hit[hit["occupancy"] == "Free"].copy()
    obs = hit[hit["occupancy"] == "Obstacle"].copy()

    xy = free[["x", "y"]].to_numpy(float)
    oxy = obs[["x", "y"]].to_numpy(float)

    tree = cKDTree(oxy)
    dist, idx = tree.query(xy, k=1)
    nearest = oxy[idx]
    direction = xy - nearest
    direction /= np.maximum(dist[:, None], 1e-12)

    x_extent = float(hit["x"].max() - hit["x"].min())
    scale = args.target_x_extent / x_extent

    # GeoPT-like normalization/alignment for a 2-D sensor-height pilot.
    pos = np.column_stack([
        (xy[:, 0] - hit["x"].mean()) * scale,
        (xy[:, 1] - hit["y"].min()) * scale,
        np.zeros(len(free)),
    ])

    geom = np.column_stack([
        pos,
        dist * scale,
        direction[:, 0],
        direction[:, 1],
        np.zeros(len(free)),
    ])

    fw = free[["cell_index", "x", "y"]].merge(
        wind,
        on=["cell_index", "x", "y"],
        how="left",
        validate="one_to_one",
    )
    if fw[["wind_x", "wind_y"]].isna().any().any():
        raise RuntimeError("wind file does not cover every free cell")

    w = fw[["wind_x", "wind_y"]].to_numpy(float)
    speed = np.linalg.norm(w, axis=1)
    unit_w = np.zeros((len(w), 3), dtype=float)
    nz = speed > 1e-12
    unit_w[nz, :2] = w[nz] / speed[nz, None]

    dynamics = np.column_stack([unit_w, speed])
    fx = np.column_stack([geom, dynamics])

    if fx.shape[1] != 11:
        raise AssertionError(f"expected 11-D fx, got {fx.shape}")

    np.savez(
        args.out,
        x=pos.astype(np.float32),
        fx=fx.astype(np.float32),
        cell_index=free["cell_index"].to_numpy(),
    )

    print(f"full_cells={len(hit)}")
    print(f"free_tokens={len(free)}")
    print(f"obstacle_cells={len(obs)}")
    print(f"x_shape={pos.shape}")
    print(f"fx_shape={fx.shape}")
    print(f"scale={scale:.9g}")


if __name__ == "__main__":
    main()
