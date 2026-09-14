#!/usr/bin/env python3
"""Small cross-context transfer gate for AVESM (train W_fast, test other winds)."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path


def load(p):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fit_transition(rows):
    c = [[1.0, 1.0], [1.0, 1.0]]
    prev = None
    for r in rows:
        y = int(float(r["gas_hit"]) > 0)
        if prev is not None:
            c[prev][y] += 1
        prev = y
    return [[v / sum(row) for v in row] for row in c]


def score(rows, models, sources):
    le = {s: 0.0 for s in sources}
    prev = None
    trace = []
    for r in rows:
        y = int(float(r["gas_hit"]) > 0)
        for s in sources:
            ps = 0.5 if prev is None else models[s][prev][y]
            others = [u for u in sources if u != s]
            q = sum(0.5 if prev is None else models[u][prev][y] for u in others) / len(others)
            le[s] += math.log(q / ps)
        trace.append(dict(le))
        prev = y
    return trace


def shuffle(rows, seed):
    out = [dict(r) for r in rows]
    ys = [r["gas_hit"] for r in out]
    random.Random(seed).shuffle(ys)
    for r, y in zip(out, ys):
        r["gas_hit"] = y
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", required=True, type=Path)
    ap.add_argument("--train-wind", default="W_fast,W_slow")
    ap.add_argument("--eval-winds", default="W_altfast")
    ap.add_argument("--train-seed", type=int, default=20260817)
    ap.add_argument("--eval-seed", type=int, default=20260818)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    eval_winds = args.eval_winds.split(",")
    data = {}
    for p in sorted(args.episodes.glob("*.csv")):
        rows = load(p)
        if rows:
            r0 = rows[0]
            data[(r0["wind_id"], r0["trajectory_id"], r0["source_id"], int(r0["plume_seed"]))] = rows
    train_winds = args.train_wind.split(",")
    sources = sorted({k[2] for k in data if k[0] in train_winds and k[3] == args.train_seed})
    models = {s: fit_transition([r for k, rows in data.items() if k[0] in train_winds and k[2] == s and k[3] == args.train_seed for r in rows]) for s in sources}
    margins = defaultdict(list)
    control = defaultdict(list)
    crosses = defaultdict(list)
    for wind in eval_winds:
        for traj in ("T_diag_A", "T_diag_B"):
            for true in sources:
                rows = data.get((wind, traj, true, args.eval_seed))
                if rows is None:
                    continue
                tr = score(rows, models, sources)
                rival = next(s for s in sources if s != true)
                margins[wind].append(tr[-1][rival] - tr[-1][true])
                crosses[wind].append(max(x[true] for x in tr) >= math.log(20.0))
                ctr = score(shuffle(rows, 7000 + len(control[wind])), models, sources)
                control[wind].append(ctr[-1][rival] - ctr[-1][true])
    summary = {}
    for wind in eval_winds:
        m = margins[wind]
        c = control[wind]
        summary[wind] = {
            "n_episodes": len(m),
            "mean_inverse_e_margin": sum(m) / len(m) if m else None,
            "mean_destructive_margin": sum(c) / len(c) if c else None,
            "null_threshold_cross_rate": sum(crosses[wind]) / len(crosses[wind]) if crosses[wind] else None,
            "margin_positive": bool(m) and sum(m) / len(m) > 0,
            "control_reduces_margin": bool(m) and bool(c) and abs(sum(c) / len(c)) < abs(sum(m) / len(m)),
            "null_rate_below_0_1": bool(crosses[wind]) and sum(crosses[wind]) / len(crosses[wind]) < 0.1,
        }
    result = {
        "status": "PASS_CROSS_CONTEXT_DIAGNOSTIC" if summary and all(all(v[k] for k in ("margin_positive", "control_reduces_margin", "null_rate_below_0_1")) for v in summary.values()) else "CROSS_CONTEXT_NO_GO",
        "train_winds": train_winds,
        "eval_winds": eval_winds,
        "train_seed": args.train_seed,
        "eval_seed": args.eval_seed,
        "source_ids": sources,
        "summary": summary,
        "boundary": "development-only transfer gate; no PMFS confirmation or closed-loop claim",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
