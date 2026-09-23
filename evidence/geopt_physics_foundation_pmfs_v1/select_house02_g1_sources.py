#!/usr/bin/env python3
"""Reproduce the frozen House02 M6 G1 source selection from occupancy geometry only."""

import argparse
import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt


def farthest(points, eligible_rows, anchors, remaining):
    rem = sorted(remaining)
    A = points[anchors]
    d2 = ((points[rem, None, :] - A[None, :, :]) ** 2).sum(axis=2)
    md = d2.min(axis=1)
    best = md.max()
    ties = [rem[k] for k, v in enumerate(md) if abs(v - best) <= 1e-12]
    return min(ties, key=lambda idx: (
        int(eligible_rows[idx]["grid_i"]),
        int(eligible_rows[idx]["grid_j"]),
    ))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("measured_hit_probability_csv")
    ap.add_argument("--clearance-m", type=float, default=0.6)
    args = ap.parse_args()

    df = pd.read_csv(args.measured_hit_probability_csv)
    free = df["occupancy"].astype(str).str.lower().ne("obstacle")

    ni = int(df["grid_i"].max()) + 1
    nj = int(df["grid_j"].max()) + 1
    mask = np.zeros((nj, ni), dtype=bool)
    world = {}

    for row, ok in zip(df.to_dict("records"), free):
        i, j = int(row["grid_i"]), int(row["grid_j"])
        mask[j, i] = bool(ok)
        world[(j, i)] = (float(row["x"]), float(row["y"]))

    xs = np.sort(df["x"].unique())
    ys = np.sort(df["y"].unique())
    dx = float(np.median(np.diff(xs)))
    dy = float(np.median(np.diff(ys)))

    clearance = distance_transform_edt(mask, sampling=(dy, dx))

    eligible = []
    for j in range(nj):
        for i in range(ni):
            if mask[j, i] and clearance[j, i] >= args.clearance_m:
                x, y = world[(j, i)]
                eligible.append(dict(
                    grid_i=i, grid_j=j, x=x, y=y,
                    clearance_m=float(clearance[j, i]),
                ))

    P = np.asarray([[r["x"], r["y"]] for r in eligible], dtype=float)
    centroid = P.mean(axis=0)
    start = int(np.argmin(((P - centroid) ** 2).sum(axis=1)))

    train = [start]
    remaining = set(range(len(eligible))) - {start}
    while len(train) < 8:
        idx = farthest(P, eligible, train, remaining)
        train.append(idx)
        remaining.remove(idx)

    test = []
    while len(test) < 2:
        idx = farthest(P, eligible, train + test, remaining)
        test.append(idx)
        remaining.remove(idx)

    val = []
    while len(val) < 2:
        idx = farthest(P, eligible, train + test + val, remaining)
        val.append(idx)
        remaining.remove(idx)

    for split, ids in [("train", train), ("val", val), ("test", test)]:
        for order, idx in enumerate(ids, 1):
            r = eligible[idx]
            print(
                split, order, r["grid_i"], r["grid_j"],
                f'{r["x"]:.15g}', f'{r["y"]:.15g}',
                f'{r["clearance_m"]:.15g}', sep=","
            )


if __name__ == "__main__":
    main()
