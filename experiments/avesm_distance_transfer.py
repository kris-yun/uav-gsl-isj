#!/usr/bin/env python3
"""Small physical-feature transfer gate: AVESM with source-distance models."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path


BINS = (0.0, 0.8, 1.2, 2.0, 3.0, 5.0, 99.0)


def load(p):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def bin_id(d):
    for i in range(len(BINS) - 1):
        if BINS[i] <= d < BINS[i + 1]:
            return i
    return len(BINS) - 2


def distance(r, xy):
    return math.hypot(float(r["position_x"]) - xy[0], float(r["position_y"]) - xy[1])


def fit(rows, xy):
    counts = [[1.0, 1.0] for _ in range(len(BINS) - 1)]
    for r in rows:
        b = bin_id(distance(r, xy))
        y = int(float(r["gas_hit"]) > 0)
        counts[b][y] += 1
    return [[v / sum(row) for v in row] for row in counts]


def score(rows, models, coords, sources):
    le = {s: 0.0 for s in sources}
    trace = []
    for r in rows:
        y = int(float(r["gas_hit"]) > 0)
        py = {}
        for s in sources:
            p = models[s][bin_id(distance(r, coords[s]))][y]
            py[s] = p
        for s in sources:
            q = sum(py[u] for u in sources if u != s) / (len(sources) - 1)
            le[s] += math.log(q / py[s])
        trace.append(dict(le))
    return trace


def shuffled(rows, seed):
    out = [dict(r) for r in rows]
    ys = [r["gas_hit"] for r in out]
    random.Random(seed).shuffle(ys)
    for r, y in zip(out, ys):
        r["gas_hit"] = y
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", required=True, type=Path)
    ap.add_argument("--train-winds", default="W_fast,W_slow")
    ap.add_argument("--eval-wind", default="W_altfast")
    ap.add_argument("--train-seed", type=int, default=20260817)
    ap.add_argument("--eval-seed", type=int, default=20260818)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    train_winds = args.train_winds.split(",")
    data = {}
    coords = {}
    for p in sorted(args.episodes.glob("*.csv")):
        rows = load(p)
        if rows:
            r0 = rows[0]
            key = (r0["wind_id"], r0["trajectory_id"], r0["source_id"], int(r0["plume_seed"]))
            data[key] = rows
            coords[r0["source_id"]] = (float(r0["source_x"]), float(r0["source_y"]))
    sources = sorted({k[2] for k in data if k[0] in train_winds and k[3] == args.train_seed})
    models = {s: fit([r for k, rows in data.items() if k[0] in train_winds and k[2] == s and k[3] == args.train_seed for r in rows], coords[s]) for s in sources}
    margins, controls, crosses = [], [], []
    for traj in ("T_diag_A", "T_diag_B"):
        for true in sources:
            rows = data.get((args.eval_wind, traj, true, args.eval_seed))
            if rows is None:
                continue
            tr = score(rows, models, coords, sources)
            rival = next(s for s in sources if s != true)
            margins.append(tr[-1][rival] - tr[-1][true])
            crosses.append(max(x[true] for x in tr) >= math.log(20.0))
            ctr = score(shuffled(rows, 8000 + len(controls)), models, coords, sources)
            controls.append(ctr[-1][rival] - ctr[-1][true])
    mm = sum(margins) / len(margins) if margins else None
    cm = sum(controls) / len(controls) if controls else None
    checks = {
        "intact_margin_positive": bool(margins) and mm > 0,
        "destructive_control_reduces_margin": bool(margins) and bool(controls) and abs(cm) < abs(mm),
        "null_cross_rate_below_0_1": bool(crosses) and sum(crosses) / len(crosses) < 0.1,
    }
    result = {
        "status": "PASS_DISTANCE_TRANSFER" if all(checks.values()) else "DISTANCE_TRANSFER_NO_GO",
        "train_winds": train_winds,
        "eval_wind": args.eval_wind,
        "n_eval_episodes": len(margins),
        "mean_inverse_e_margin": mm,
        "mean_destructive_margin": cm,
        "null_threshold_cross_rate": sum(crosses) / len(crosses) if crosses else None,
        "checks": checks,
        "boundary": "development-only transfer gate; no PMFS confirmation or closed-loop claim",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
