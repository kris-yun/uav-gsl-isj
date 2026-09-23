#!/usr/bin/env python3
"""Analytical O0 transport-splitting probe for M7.

Input:
    NPZ produced by export_gaden_playback_slices.py

Goal:
    Test whether explicit wind advection + diffusion + obstacle handling explains
    held-out short-horizon plume transport better than persistence BEFORE any
    neural operator is trained.

Important:
- This is a transport test, not source inference.
- Cells inside a predeclared radius around the true simulation source are
  excluded from scoring so continuous source injection does not become a hidden
  fitted parameter.
- Diffusivity is selected only on a calibration prefix, then frozen.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates


def reshape(v, nx, ny):
    return np.asarray(v).reshape(nx, ny, *np.asarray(v).shape[1:])


def semi_lagrangian(
    c,
    wind,
    free,
    xs,
    ys,
    dt,
    block_walls: bool,
):
    """Backtrace concentration by the spatial wind field."""
    nx, ny = c.shape
    dx = float(np.median(np.diff(xs)))
    dy = float(np.median(np.diff(ys)))

    X, Y = np.meshgrid(xs, ys, indexing="ij")
    xp = X - dt * wind[..., 0]
    yp = Y - dt * wind[..., 1]

    fi = (xp - xs[0]) / dx
    fj = (yp - ys[0]) / dy

    pred = map_coordinates(
        c,
        [fi, fj],
        order=1,
        mode="constant",
        cval=0.0,
    )

    if block_walls:
        # Lightweight line-of-sight blocker.
        # Check 1/4, 1/2, 3/4 points on the backtrace against the occupancy grid.
        valid_path = free.copy()
        for a in (0.25, 0.50, 0.75):
            xq = X + a * (xp - X)
            yq = Y + a * (yp - Y)
            iq = np.rint((xq - xs[0]) / dx).astype(int)
            jq = np.rint((yq - ys[0]) / dy).astype(int)
            inb = (iq >= 0) & (iq < nx) & (jq >= 0) & (jq < ny)
            step_free = np.zeros_like(free)
            step_free[inb] = free[iq[inb], jq[inb]]
            valid_path &= step_free
        pred[~valid_path] = 0.0

    pred[~free] = 0.0
    pred[pred < 0] = 0.0
    return pred


def free_space_laplacian(c, free, dx, dy):
    """No-flux graph-like 4-neighbour Laplacian.

    Obstacle/out-of-domain neighbours contribute zero normal flux rather than
    acting as zero-concentration Dirichlet cells.
    """
    out = np.zeros_like(c, dtype=float)

    for di, dj, h2 in ((1, 0, dx * dx), (-1, 0, dx * dx),
                       (0, 1, dy * dy), (0, -1, dy * dy)):
        neigh = np.roll(c, shift=(di, dj), axis=(0, 1))
        neigh_free = np.roll(free, shift=(di, dj), axis=(0, 1))

        # Prevent np.roll wrap-around from becoming a physical neighbour.
        valid = neigh_free.copy()
        if di == 1:
            valid[0, :] = False
        elif di == -1:
            valid[-1, :] = False
        elif dj == 1:
            valid[:, 0] = False
        elif dj == -1:
            valid[:, -1] = False

        m = free & valid
        out[m] += (neigh[m] - c[m]) / h2

    out[~free] = 0.0
    return out


def diffuse_no_flux(c, free, D, dt, dx, dy):
    if D <= 0 or dt <= 0:
        return c.copy()

    # Stable explicit substep target for 2-D diffusion.
    denom = max(dx * dx, dy * dy)
    max_dt = 0.20 * denom / max(D, 1e-15)
    n = max(1, int(math.ceil(dt / max_dt)))
    h = dt / n

    out = c.astype(float).copy()
    for _ in range(n):
        out += D * h * free_space_laplacian(out, free, dx, dy)
        out[~free] = 0.0
        out[out < 0] = 0.0
    return out


def predict(c, wind, free, xs, ys, dt, D, variant):
    dx = float(np.median(np.diff(xs)))
    dy = float(np.median(np.diff(ys)))

    if variant == "persistence":
        z = c.copy()

    elif variant == "advection":
        z = semi_lagrangian(c, wind, free, xs, ys, dt, block_walls=False)

    elif variant == "advection_wall":
        z = semi_lagrangian(c, wind, free, xs, ys, dt, block_walls=True)

    elif variant == "diffusion":
        z = diffuse_no_flux(c, free, D, dt, dx, dy)

    elif variant == "advdiff":
        z = semi_lagrangian(c, wind, free, xs, ys, dt, block_walls=False)
        z = diffuse_no_flux(z, free, D, dt, dx, dy)

    elif variant == "strang_wall":
        z = diffuse_no_flux(c, free, D, dt / 2, dx, dy)
        z = semi_lagrangian(z, wind, free, xs, ys, dt, block_walls=True)
        z = diffuse_no_flux(z, free, D, dt / 2, dx, dy)

    else:
        raise ValueError(variant)

    z[~free] = 0.0
    return z


def metric_row(y, p, mask, xs, ys):
    yt = y[mask].astype(float)
    pt = p[mask].astype(float)

    eps = 1e-12
    rel_l2 = float(np.linalg.norm(pt - yt) / max(np.linalg.norm(yt), eps))
    log_mae = float(np.mean(np.abs(np.log1p(pt) - np.log1p(yt))))
    rmse = float(np.sqrt(np.mean((pt - yt) ** 2)))

    X, Y = np.meshgrid(xs, ys, indexing="ij")
    ymass = np.maximum(y, 0.0)
    pmass = np.maximum(p, 0.0)
    ymass = np.where(mask, ymass, 0.0)
    pmass = np.where(mask, pmass, 0.0)

    def centroid(m):
        z = float(m.sum())
        if z <= eps:
            return np.array([np.nan, np.nan])
        return np.array([(m * X).sum() / z, (m * Y).sum() / z])

    cy = centroid(ymass)
    cp = centroid(pmass)
    centroid_error = float(np.linalg.norm(cp - cy)) if np.all(np.isfinite([*cy, *cp])) else float("nan")

    return {
        "rel_l2": rel_l2,
        "log_mae": log_mae,
        "rmse": rmse,
        "centroid_error_m": centroid_error,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--dt", type=float, required=True,
                    help="seconds between consecutive exported snapshots")
    ap.add_argument("--source-x", type=float, required=True)
    ap.add_argument("--source-y", type=float, required=True)
    ap.add_argument("--exclude-source-radius", type=float, default=0.50)
    ap.add_argument("--diffusivities", default="0.001,0.003,0.01,0.03,0.1")
    ap.add_argument("--calibration-fraction", type=float, default=0.35)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    d = np.load(args.input)
    xyz = d["xyz"]
    ij = d["ij"]
    free_flat = d["free_mask"].astype(bool)
    Cflat = d["concentration"].astype(float)
    Wflat = d["wind"].astype(float)
    iterations = d["iterations"]

    nx = int(ij[:, 0].max()) + 1
    ny = int(ij[:, 1].max()) + 1

    C = Cflat.reshape(len(Cflat), nx, ny)
    W = Wflat.reshape(len(Wflat), nx, ny, 3)
    free = free_flat.reshape(nx, ny)

    # Coordinates are regular by construction from GADEN cell centres.
    Xflat = xyz[:, 0].reshape(nx, ny)
    Yflat = xyz[:, 1].reshape(nx, ny)
    xs = Xflat[:, 0]
    ys = Yflat[0, :]

    X, Y = np.meshgrid(xs, ys, indexing="ij")
    source_far = np.hypot(X - args.source_x, Y - args.source_y) >= args.exclude_source_radius
    score_mask = free & source_far

    Ds = [float(x) for x in args.diffusivities.split(",") if x.strip()]
    n_trans = len(C) - 1
    if n_trans < 3:
        raise ValueError("Need at least 4 exported snapshots")

    n_cal = max(1, min(n_trans - 1, int(math.floor(n_trans * args.calibration_fraction))))
    cal_ids = list(range(n_cal))
    eval_ids = list(range(n_cal, n_trans))

    # Select D source-blind on calibration transitions using the physically
    # strongest declared baseline only.
    D_scores = []
    for Dval in Ds:
        vals = []
        for t in cal_ids:
            pred = predict(C[t], W[t], free, xs, ys, args.dt, Dval, "strang_wall")
            vals.append(metric_row(C[t + 1], pred, score_mask, xs, ys)["log_mae"])
        D_scores.append((float(np.mean(vals)), Dval))

    D_scores.sort()
    best_cal_score, Dstar = D_scores[0]

    variants = [
        "persistence",
        "advection",
        "advection_wall",
        "diffusion",
        "advdiff",
        "strang_wall",
    ]

    rows = []
    for t in eval_ids:
        for variant in variants:
            pred = predict(C[t], W[t], free, xs, ys, args.dt, Dstar, variant)
            m = metric_row(C[t + 1], pred, score_mask, xs, ys)
            rows.append({
                "transition": t,
                "iteration_from": int(iterations[t]),
                "iteration_to": int(iterations[t + 1]),
                "variant": variant,
                "D": Dstar,
                **m,
            })

        # Destructive wrong-wind null: spatially permute wind vectors with a
        # deterministic per-transition RNG while preserving their marginal set.
        rng = np.random.default_rng(20260923 + t)
        wf = W[t].reshape(-1, 3).copy()
        perm = rng.permutation(len(wf))
        wrong_wind = wf[perm].reshape(nx, ny, 3)
        pred = predict(C[t], wrong_wind, free, xs, ys, args.dt, Dstar, "strang_wall")
        m = metric_row(C[t + 1], pred, score_mask, xs, ys)
        rows.append({
            "transition": t,
            "iteration_from": int(iterations[t]),
            "iteration_to": int(iterations[t + 1]),
            "variant": "strang_wall_WIND_SHUFFLE_NULL",
            "D": Dstar,
            **m,
        })

    csv_path = out / "O0_METRICS.tsv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "input": str(Path(args.input).resolve()),
        "dt_seconds": args.dt,
        "source_xy": [args.source_x, args.source_y],
        "exclude_source_radius_m": args.exclude_source_radius,
        "diffusivity_panel": Ds,
        "calibration_transition_indices": cal_ids,
        "evaluation_transition_indices": eval_ids,
        "D_selection": [{"D": Dv, "mean_cal_log_mae": sc} for sc, Dv in D_scores],
        "selected_D": Dstar,
        "selected_D_cal_log_mae": best_cal_score,
        "mean_eval": {},
    }

    for variant in [*variants, "strang_wall_WIND_SHUFFLE_NULL"]:
        subset = [r for r in rows if r["variant"] == variant]
        summary["mean_eval"][variant] = {
            key: float(np.nanmean([r[key] for r in subset]))
            for key in ("rel_l2", "log_mae", "rmse", "centroid_error_m")
        }

    (out / "O0_SUMMARY.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
