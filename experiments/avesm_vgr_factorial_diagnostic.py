#!/usr/bin/env python3
"""Development-only AVESM diagnostic on the read-only VGR factorial episodes."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path


def load(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def transition(rows):
    counts = [[1.0, 1.0], [1.0, 1.0]]
    prev = None
    for r in rows:
        y = int(float(r["gas_hit"]) > 0)
        if prev is not None:
            counts[prev][y] += 1.0
        prev = y
    return [[x / sum(row) for x in row] for row in counts]


def log_e_trace(rows, models, source_ids):
    loge = {s: 0.0 for s in source_ids}
    trace = []
    prev = None
    for r in rows:
        y = int(float(r["gas_hit"]) > 0)
        for s in source_ids:
            p = 0.5 if prev is None else models[s][prev][y]
            others = [u for u in source_ids if u != s]
            q = sum((0.5 if prev is None else models[u][prev][y]) for u in others) / len(others)
            loge[s] += math.log(q / p)
        trace.append(dict(loge))
        prev = y
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
    ap.add_argument("--train-seed", type=int, default=20260817)
    ap.add_argument("--eval-seeds", default="20260818,20260819")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    eval_seeds = [int(x) for x in args.eval_seeds.split(",")]
    eps = {}
    for p in sorted(args.episodes.glob("*.csv")):
        rows = load(p)
        if rows:
            r0 = rows[0]
            eps[(r0["wind_id"], r0["trajectory_id"], r0["source_id"], int(r0["plume_seed"]))] = rows
    margins, control_margins, ranks, control_ranks = [], [], [], []
    null_crosses = []
    contexts = sorted({(k[0], k[1]) for k in eps})
    for ctx in contexts:
        sources = sorted({k[2] for k in eps if k[0:2] == ctx and k[3] == args.train_seed})
        if len(sources) < 2:
            continue
        models = {s: transition(eps[(ctx[0], ctx[1], s, args.train_seed)]) for s in sources}
        for seed in eval_seeds:
            for true in sources:
                rows = eps.get((ctx[0], ctx[1], true, seed))
                if rows is None:
                    continue
                trace = log_e_trace(rows, models, sources)
                rival = next(s for s in sources if s != true)
                margins.append(trace[-1][rival] - trace[-1][true])
                ranks.append(1 + sum(trace[-1][s] < trace[-1][true] for s in sources))
                null_crosses.append(max(x[true] for x in trace) >= math.log(20.0))
                ctrace = log_e_trace(shuffled(rows, 9100 + seed), models, sources)
                control_margins.append(ctrace[-1][rival] - ctrace[-1][true])
                control_ranks.append(1 + sum(ctrace[-1][s] < ctrace[-1][true] for s in sources))
    mean_margin = sum(margins) / len(margins) if margins else None
    mean_control = sum(control_margins) / len(control_margins) if control_margins else None
    checks = {
        "intact_inverse_e_margin_positive": bool(margins) and mean_margin > 0.0,
        "destructive_control_reduces_margin": bool(control_margins) and abs(mean_control) < abs(mean_margin),
        "null_cross_rate_below_0_1": bool(null_crosses) and sum(null_crosses) / len(null_crosses) < 0.1,
    }
    result = {
        "status": "PASS_DIAGNOSTIC" if all(checks.values()) else "DIAGNOSTIC_MIXED_NO_GO",
        "asset_scope": "VGR_factorial_development_diagnostic_only",
        "upstream_boundary": "nominal seeds are pseudoreplicates; no held-out or main-innovation claim",
        "contexts": contexts,
        "n_eval_episodes": len(margins),
        "intact_mean_inverse_e_margin": mean_margin,
        "destructive_mean_inverse_e_margin": mean_control,
        "intact_mean_true_rank": sum(ranks) / len(ranks) if ranks else None,
        "destructive_mean_true_rank": sum(control_ranks) / len(control_ranks) if control_ranks else None,
        "null_threshold_log20_cross_rate": sum(null_crosses) / len(null_crosses) if null_crosses else None,
        "checks": checks,
        "interpretation": "AVESM supplies a sequential source-vs-rival evidence object in this diagnostic, but the upstream dataset remains development-only and pseudoreplicated. This does not authorize PMFS confirmation or closed-loop claims.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
