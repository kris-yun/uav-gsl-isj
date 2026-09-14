#!/usr/bin/env python3
"""Small route-protocol transfer diagnostic for AVESM.

Fits the physical-distance hit kernels on VGR factorial episodes and evaluates
held-out R3C route replays.  R3C is a different route/acquisition package but
shares the frozen R3B physical realization; therefore this is not an
independent simulation confirmation.
"""
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


def bid(d):
    for i in range(len(BINS) - 1):
        if BINS[i] <= d < BINS[i + 1]:
            return i
    return len(BINS) - 2


def xy(r):
    return float(r.get("position_x", r.get("x"))), float(r.get("position_y", r.get("y")))


def dist(r, c):
    x, y = xy(r)
    return math.hypot(x - c[0], y - c[1])


def fit(rows, c):
    n = [[1.0, 1.0] for _ in range(len(BINS) - 1)]
    for r in rows:
        n[bid(dist(r, c))][int(float(r["gas_hit"]) > 0)] += 1.0
    return [[a / sum(row) for a in row] for row in n]


def score(rows, models, coords, sources):
    le = {s: 0.0 for s in sources}
    for r in rows:
        y = int(float(r["gas_hit"]) > 0)
        p = {s: models[s][bid(dist(r, coords[s]))][y] for s in sources}
        for s in sources:
            q = sum(p[u] for u in sources if u != s) / (len(sources) - 1)
            le[s] += math.log(q / p[s])
    return le


def shuffle(rows, seed):
    out = [dict(r) for r in rows]
    ys = [r["gas_hit"] for r in out]
    random.Random(seed).shuffle(ys)
    for r, y in zip(out, ys):
        r["gas_hit"] = y
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True, type=Path)
    ap.add_argument("--eval", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    train_rows = [load(p) for p in sorted(args.train.glob("*.csv"))]
    train_rows = [r for rows in train_rows for r in rows]
    coords = {}
    for r in train_rows:
        coords[r["source_id"]] = (float(r["source_x"]), float(r["source_y"]))
    sources = sorted(coords)
    models = {s: fit([r for r in train_rows if r["source_id"] == s], coords[s]) for s in sources}
    eval_files = []
    for p in sorted(args.eval.glob("S_*__W_altfast__R3C_*.csv")):
        name = p.name
        route = name.split("__")[2]
        if route not in {"R3C_00", "R3C_10"}:
            continue
        src = name.split("__")[0]
        if src in sources:
            eval_files.append((src, route, p))
    margins, controls, crosses = [], [], []
    per_episode = []
    for i, (true, route, p) in enumerate(eval_files):
        rows = load(p)
        le = score(rows, models, coords, sources)
        rival = max((s for s in sources if s != true), key=lambda s: le[s])
        m = le[rival] - le[true]
        ctl = score(shuffle(rows, 9000 + i), models, coords, sources)
        cm = ctl[rival] - ctl[true]
        margins.append(m)
        controls.append(cm)
        crosses.append(max(le.values()) >= math.log(20.0))
        per_episode.append({"source": true, "route": route, "inverse_e_margin": m, "destructive_margin": cm, "true_rank": 1 + sum(le[s] > le[true] for s in sources if s != true)})
    mm = sum(margins) / len(margins) if margins else None
    cm = sum(controls) / len(controls) if controls else None
    checks = {
        "intact_margin_positive": bool(margins) and mm > 0,
        "destructive_control_reduces_margin": bool(margins) and bool(controls) and abs(cm) < abs(mm),
        "null_threshold_cross_rate_below_0_1": bool(crosses) and sum(crosses) / len(crosses) < 0.1,
    }
    result = {
        "status": "PASS_ROUTE_TRANSFER_DIAGNOSTIC" if all(checks.values()) else "ROUTE_TRANSFER_NO_GO",
        "n_eval_episodes": len(margins),
        "mean_inverse_e_margin": mm,
        "mean_destructive_margin": cm,
        "null_threshold_cross_rate": sum(crosses) / len(crosses) if crosses else None,
        "checks": checks,
        "per_episode": per_episode,
        "boundary": "route/acquisition transfer only; R3C shares the frozen R3B physical realization and is not independent cross-simulation confirmation",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
