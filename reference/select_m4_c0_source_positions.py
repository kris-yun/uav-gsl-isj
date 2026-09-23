#!/usr/bin/env python3
"""Deterministic source-blind source-position selector for M4 C0.

Input
-----
A PMFS measured_hit_probability.csv containing at least:
grid_i, grid_j, x, y, occupancy.

Selection
---------
1. Compute geometric clearance to obstacle cells AND map boundary.
2. Keep free cells with clearance >= --min-clearance-m.
3. Choose the eligible cell nearest the eligible-set centroid.
4. Add points by deterministic farthest-point sampling.

No gas probability, source posterior, source truth, or candidate rank is used.

The output is only a 2-D proposal. The caller MUST validate every (x,y,z)
against the actual GADEN 3-D occupancy before simulation.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="measured_hit_probability.csv")
    p.add_argument("--output", required=True, help="output source_positions.csv")
    p.add_argument("--count", type=int, default=4)
    p.add_argument("--min-clearance-m", type=float, default=0.9)
    p.add_argument(
        "--z",
        type=float,
        required=True,
        help="predeclared benchmark source plane; do not infer from truth x/y",
    )
    return p.parse_args()


def d2(a, b):
    return (a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2


def main():
    args = parse_args()

    with open(args.input, newline="") as f:
        rows = list(csv.DictReader(f))

    required = {"grid_i", "grid_j", "x", "y", "occupancy"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit(f"missing required columns: {sorted(required)}")

    points = []
    obstacles = []
    for r in rows:
        p = {
            "grid_i": int(r["grid_i"]),
            "grid_j": int(r["grid_j"]),
            "x": float(r["x"]),
            "y": float(r["y"]),
            "occupancy": r["occupancy"],
        }
        if r["occupancy"].strip().lower() == "obstacle":
            obstacles.append(p)
        else:
            points.append(p)

    if len(points) < args.count:
        raise SystemExit("not enough free cells")
    if not obstacles:
        raise SystemExit("no obstacle cells found; cannot compute clearance")

    xmin = min(float(r["x"]) for r in rows)
    xmax = max(float(r["x"]) for r in rows)
    ymin = min(float(r["y"]) for r in rows)
    ymax = max(float(r["y"]) for r in rows)

    eligible = []
    for p in points:
        obs_clear = math.sqrt(min(d2(p, q) for q in obstacles))
        boundary_clear = min(
            p["x"] - xmin,
            xmax - p["x"],
            p["y"] - ymin,
            ymax - p["y"],
        )
        clearance = min(obs_clear, boundary_clear)
        if clearance + 1e-12 >= args.min_clearance_m:
            q = dict(p)
            q["clearance_m"] = clearance
            eligible.append(q)

    if len(eligible) < args.count:
        raise SystemExit(
            f"only {len(eligible)} cells satisfy clearance "
            f">= {args.min_clearance_m} m"
        )

    cx = sum(p["x"] for p in eligible) / len(eligible)
    cy = sum(p["y"] for p in eligible) / len(eligible)

    def centroid_key(p):
        return (
            (p["x"] - cx) ** 2 + (p["y"] - cy) ** 2,
            p["x"],
            p["y"],
            p["grid_i"],
            p["grid_j"],
        )

    selected = [min(eligible, key=centroid_key)]
    selected_keys = {(selected[0]["grid_i"], selected[0]["grid_j"])}

    while len(selected) < args.count:
        best = None
        best_key = None
        for p in eligible:
            key0 = (p["grid_i"], p["grid_j"])
            if key0 in selected_keys:
                continue
            min_d2 = min(d2(p, q) for q in selected)
            # Maximize minimum separation. Ties resolve lexicographically.
            key = (
                min_d2,
                -p["x"],
                -p["y"],
                -p["grid_i"],
                -p["grid_j"],
            )
            if best is None or key > best_key:
                best, best_key = p, key
        selected.append(best)
        selected_keys.add((best["grid_i"], best["grid_j"]))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "intervention_id",
        "grid_i",
        "grid_j",
        "x",
        "y",
        "z",
        "clearance_m",
        "selection_rule",
        "requires_gaden_3d_validation",
    ]
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, p in enumerate(selected, start=1):
            w.writerow(
                {
                    "intervention_id": f"S{i}",
                    "grid_i": p["grid_i"],
                    "grid_j": p["grid_j"],
                    "x": f'{p["x"]:.9f}',
                    "y": f'{p["y"]:.9f}',
                    "z": f"{args.z:.9f}",
                    "clearance_m": f'{p["clearance_m"]:.9f}',
                    "selection_rule": (
                        f"clearance>={args.min_clearance_m}m;"
                        "centroid_start;farthest_point"
                    ),
                    "requires_gaden_3d_validation": "true",
                }
            )

    print(f"eligible={len(eligible)} selected={len(selected)}")
    for i, p in enumerate(selected, start=1):
        print(
            f"S{i}: grid=({p['grid_i']},{p['grid_j']}) "
            f"xy=({p['x']:.6f},{p['y']:.6f}) "
            f"clearance={p['clearance_m']:.3f}m z={args.z:.3f}"
        )


if __name__ == "__main__":
    main()
