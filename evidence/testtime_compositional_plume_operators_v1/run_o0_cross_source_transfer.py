#!/usr/bin/env python3
"""Cross-source analytical O0 transfer test for M7.

Calibrate the analytical split on source/case A only, freeze D, then evaluate:
- held-out transitions of A;
- all available transitions of B;
with the same transport implementation and D.

Both NPZ files must be exported on the same House geometry / sensor-height grid.
They may correspond to different source locations. Wind fields are supplied by
each realization itself and are *inputs* to the same advection operator.

No source-specific tuning is allowed for B.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

from run_o0_analytical_split import predict, metric_row


def load_case(path: str):
    d = np.load(path)
    xyz = d["xyz"]
    ij = d["ij"]
    free_flat = d["free_mask"].astype(bool)
    Cflat = d["concentration"].astype(float)
    Wflat = d["wind"].astype(float)
    iterations = d["iterations"].astype(int)

    nx = int(ij[:, 0].max()) + 1
    ny = int(ij[:, 1].max()) + 1
    C = Cflat.reshape(len(Cflat), nx, ny)
    W = Wflat.reshape(len(Wflat), nx, ny, 3)
    free = free_flat.reshape(nx, ny)

    Xflat = xyz[:, 0].reshape(nx, ny)
    Yflat = xyz[:, 1].reshape(nx, ny)
    xs = Xflat[:, 0]
    ys = Yflat[0, :]

    return {
        "path": str(Path(path).resolve()),
        "xyz": xyz,
        "ij": ij,
        "C": C,
        "W": W,
        "free": free,
        "xs": xs,
        "ys": ys,
        "iterations": iterations,
        "nx": nx,
        "ny": ny,
    }


def geometry_equal(a, b, atol=1e-7):
    return (
        a["nx"] == b["nx"]
        and a["ny"] == b["ny"]
        and np.array_equal(a["free"], b["free"])
        and np.allclose(a["xs"], b["xs"], atol=atol, rtol=0)
        and np.allclose(a["ys"], b["ys"], atol=atol, rtol=0)
    )


def scoring_mask(case, source_xy, radius):
    X, Y = np.meshgrid(case["xs"], case["ys"], indexing="ij")
    far = np.hypot(X - source_xy[0], Y - source_xy[1]) >= radius
    return case["free"] & far


def evaluate_case(case, Dstar, dt, source_xy, radius, label, transition_ids):
    mask = scoring_mask(case, source_xy, radius)
    variants = [
        "persistence",
        "advection",
        "advection_wall",
        "diffusion",
        "advdiff",
        "strang_wall",
    ]
    rows = []

    for t in transition_ids:
        if t < 0 or t + 1 >= len(case["C"]):
            continue

        for variant in variants:
            pred = predict(
                case["C"][t],
                case["W"][t],
                case["free"],
                case["xs"],
                case["ys"],
                dt,
                Dstar,
                variant,
            )
            m = metric_row(case["C"][t + 1], pred, mask, case["xs"], case["ys"])
            rows.append({
                "case": label,
                "transition": t,
                "iteration_from": int(case["iterations"][t]),
                "iteration_to": int(case["iterations"][t + 1]),
                "variant": variant,
                "D": Dstar,
                **m,
            })

        # Wrong-wind spatial-permutation null.
        rng = np.random.default_rng(20260923 + 101 * t)
        wf = case["W"][t].reshape(-1, 3).copy()
        wrong = wf[rng.permutation(len(wf))].reshape(case["nx"], case["ny"], 3)
        pred = predict(
            case["C"][t],
            wrong,
            case["free"],
            case["xs"],
            case["ys"],
            dt,
            Dstar,
            "strang_wall",
        )
        m = metric_row(case["C"][t + 1], pred, mask, case["xs"], case["ys"])
        rows.append({
            "case": label,
            "transition": t,
            "iteration_from": int(case["iterations"][t]),
            "iteration_to": int(case["iterations"][t + 1]),
            "variant": "strang_wall_WIND_SHUFFLE_NULL",
            "D": Dstar,
            **m,
        })

    return rows


def mean_by_variant(rows):
    out = {}
    variants = sorted({r["variant"] for r in rows})
    for v in variants:
        rr = [r for r in rows if r["variant"] == v]
        out[v] = {
            k: float(np.nanmean([x[k] for x in rr]))
            for k in ("rel_l2", "log_mae", "rmse", "centroid_error_m")
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-a", required=True)
    ap.add_argument("--case-b", required=True)
    ap.add_argument("--source-a-x", type=float, required=True)
    ap.add_argument("--source-a-y", type=float, required=True)
    ap.add_argument("--source-b-x", type=float, required=True)
    ap.add_argument("--source-b-y", type=float, required=True)
    ap.add_argument("--dt", type=float, required=True)
    ap.add_argument("--exclude-source-radius", type=float, default=0.50)
    ap.add_argument("--diffusivities", default="0.001,0.003,0.01,0.03,0.1")
    ap.add_argument("--a-calibration-fraction", type=float, default=0.35)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    A = load_case(args.case_a)
    B = load_case(args.case_b)
    if not geometry_equal(A, B):
        raise RuntimeError(
            "Case A/B geometry grids differ. Cross-source transfer requires the same House/grid."
        )

    nA = len(A["C"]) - 1
    nB = len(B["C"]) - 1
    if nA < 3 or nB < 2:
        raise ValueError("Insufficient snapshot transitions")

    n_cal = max(1, min(nA - 1, int(math.floor(nA * args.a_calibration_fraction))))
    cal_ids = list(range(n_cal))
    evalA_ids = list(range(n_cal, nA))
    evalB_ids = list(range(nB))

    Ds = [float(x) for x in args.diffusivities.split(",") if x.strip()]
    maskA = scoring_mask(
        A,
        (args.source_a_x, args.source_a_y),
        args.exclude_source_radius,
    )

    # Calibrate D on A only.
    D_scores = []
    for Dval in Ds:
        vals = []
        for t in cal_ids:
            p = predict(
                A["C"][t], A["W"][t], A["free"], A["xs"], A["ys"],
                args.dt, Dval, "strang_wall",
            )
            vals.append(
                metric_row(A["C"][t + 1], p, maskA, A["xs"], A["ys"])["log_mae"]
            )
        D_scores.append((float(np.mean(vals)), Dval))

    D_scores.sort()
    best_cal, Dstar = D_scores[0]

    rowsA = evaluate_case(
        A, Dstar, args.dt,
        (args.source_a_x, args.source_a_y),
        args.exclude_source_radius,
        "A_HELDOUT",
        evalA_ids,
    )
    rowsB = evaluate_case(
        B, Dstar, args.dt,
        (args.source_b_x, args.source_b_y),
        args.exclude_source_radius,
        "B_CROSS_SOURCE",
        evalB_ids,
    )

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows = rowsA + rowsB
    with (out / "O0_CROSS_SOURCE_METRICS.tsv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "case_a": A["path"],
        "case_b": B["path"],
        "same_geometry": True,
        "source_a_xy": [args.source_a_x, args.source_a_y],
        "source_b_xy": [args.source_b_x, args.source_b_y],
        "dt_seconds": args.dt,
        "exclude_source_radius_m": args.exclude_source_radius,
        "D_panel": Ds,
        "D_calibration_case": "A only",
        "A_calibration_transition_indices": cal_ids,
        "A_heldout_transition_indices": evalA_ids,
        "B_cross_source_transition_indices": evalB_ids,
        "D_scores": [{"D": D, "mean_cal_log_mae": s} for s, D in D_scores],
        "selected_D": Dstar,
        "selected_D_cal_log_mae": best_cal,
        "A_heldout_mean": mean_by_variant(rowsA),
        "B_cross_source_mean": mean_by_variant(rowsB),
    }

    (out / "O0_CROSS_SOURCE_SUMMARY.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
