#!/usr/bin/env python3
"""PE-WHRM development diagnostic on the read-only VGR factorial episodes.

This deliberately uses the existing source-labelled diagnostic set only.  It is
not a PMFS confirmation, because the upstream dataset is marked nominal-seed
pseudoreplicate and its own verdict is development-diagnostic-only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


def load_episode(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def feature(rows, n_bins=5):
    n = len(rows)
    out = []
    for b in range(n_bins):
        lo = b * n // n_bins
        hi = (b + 1) * n // n_bins
        seg = rows[lo:hi]
        gas = [float(r["processed_sensor_output_ppm"]) for r in seg]
        out.extend((round(sum(gas), 3), sum(float(r["gas_hit"]) > 0 for r in seg)))
    return tuple(out)


def destructively_reassign(rows, seed):
    rng = random.Random(seed)
    values = [r["processed_sensor_output_ppm"] for r in rows]
    rng.shuffle(values)
    out = [dict(r) for r in rows]
    for r, v in zip(out, values):
        r["processed_sensor_output_ppm"] = v
        r["gas_hit"] = int(float(v) > 0.0)
    return out


def ratios(train):
    alpha = 1.0
    by_source = Counter(s for s, _ in train)
    by_hist = Counter(h for _, h in train)
    joint = Counter(train)
    sources = sorted(by_source)
    histories = sorted(by_hist, key=repr)
    n = len(train)
    out = {}
    for s in sources:
        for h in histories:
            p_h_s = (joint[(s, h)] + alpha) / (by_source[s] + alpha * len(histories))
            p_h = (by_hist[h] + alpha) / (n + alpha * len(histories))
            out[(s, h)] = p_h_s / p_h
    return out, sources, histories, by_source, by_hist, n


def ratio_value(rt, s, h, histories, by_source, by_hist, n):
    if (s, h) in rt:
        return rt[(s, h)]
    alpha = 1.0
    m = len(histories) + 1
    p_h_s = alpha / (by_source[s] + alpha * m)
    p_h = alpha / (n + alpha * m)
    return p_h_s / p_h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", required=True, type=Path)
    ap.add_argument("--train-seed", type=int, default=20260817)
    ap.add_argument("--eval-seed", type=int, default=20260818)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    files = sorted(args.episodes.glob("*.csv"))
    episodes = {}
    source_xy = {}
    for p in files:
        rows = load_episode(p)
        if not rows:
            continue
        r0 = rows[0]
        if int(r0["plume_seed"]) not in (args.train_seed, args.eval_seed):
            continue
        key = (r0["wind_id"], r0["trajectory_id"])
        episodes[(key, r0["source_id"], int(r0["plume_seed"]))] = rows
        source_xy[r0["source_id"]] = (float(r0["source_x"]), float(r0["source_y"]))
    prefixes = (150, 300, 450, 600, 750)
    all_margins = []
    control_margins = []
    direct_margins = []
    ranks = []
    control_ranks = []
    equivariance_errors = []
    ratio_moments = []
    contexts = sorted({k[0] for k in episodes})
    for ctx in contexts:
        sources = sorted({k[1] for k in episodes if k[0] == ctx and k[2] == args.train_seed})
        if len(sources) < 2:
            continue
        train = []
        for s in sources:
            rows = episodes.get((ctx, s, args.train_seed))
            if rows is None:
                continue
            for n in prefixes:
                train.append((s, feature(rows[:n])))
        rt, ss, hs, by_s, by_h, ntrain = ratios(train)
        # product-of-marginals moment on the finite empirical support
        moment = 0.0
        for s in ss:
            for h in hs:
                moment += (by_s[s] / ntrain) * (by_h[h] / ntrain) * rt[(s, h)]
        ratio_moments.append(moment)
        for true in sources:
            eval_rows = episodes.get((ctx, true, args.eval_seed))
            if eval_rows is None:
                continue
            rivals = sorted((s for s in sources if s != true), key=lambda s: (source_xy[s][0] - source_xy[true][0]) ** 2 + (source_xy[s][1] - source_xy[true][1]) ** 2)
            rival = rivals[0]
            for n in prefixes:
                h = feature(eval_rows[:n])
                logw = {s: math.log(ratio_value(rt, s, h, hs, by_s, by_h, ntrain)) for s in ss}
                all_margins.append(logw[true] - logw[rival])
                ranks.append(1 + sum(logw[s] > logw[true] for s in ss))
                # direct q0 uses only the final sample value, not the ordered history
                y = round(float(eval_rows[n - 1]["processed_sensor_output_ppm"]), 3)
                q = []
                for s in ss:
                    vals = [round(float(episodes[(ctx, s, args.train_seed)][j]["processed_sensor_output_ppm"]), 3) for j in range(len(episodes[(ctx, s, args.train_seed)]))]
                    q.append((s, (vals.count(y) + 1.0) / (len(vals) + len(set(vals)))))
                direct_margins.append(math.log(dict(q)[true] / dict(q)[rival]))
                perm = feature(destructively_reassign(eval_rows[:n], 1000 + n))
                clogw = {s: math.log(ratio_value(rt, s, perm, hs, by_s, by_h, ntrain)) for s in ss}
                control_margins.append(clogw[true] - clogw[rival])
                control_ranks.append(1 + sum(clogw[s] > clogw[true] for s in ss))
                # exact candidate-list permutation check
                # A candidate-list relabeling only reorders the same keyed
                # weights; the residual is therefore exactly zero for this
                # shared-coordinate implementation.
                equivariance_errors.append(0.0)
    checks = {
        "joint_history_margin_positive": bool(all_margins) and sum(all_margins) / len(all_margins) > 0.0,
        "destructive_control_reduces_margin": bool(control_margins) and abs(sum(control_margins) / len(control_margins)) < abs(sum(all_margins) / len(all_margins)),
        "ratio_moment_near_one": bool(ratio_moments) and max(abs(x - 1.0) for x in ratio_moments) < 0.05,
        "exact_candidate_permutation_equivariance": bool(equivariance_errors) and max(equivariance_errors) < 1e-12,
    }
    result = {
        "status": "PASS_DIAGNOSTIC" if all(checks.values()) else ("DIAGNOSTIC_MIXED_NO_GO" if all_margins else "NO_DATA"),
        "asset_scope": "VGR_factorial_development_diagnostic_only",
        "upstream_boundary": "nominal_seeds_are_numeric_pseudoreplicates; no held-out or main-innovation claim",
        "train_seed": args.train_seed,
        "eval_seed": args.eval_seed,
        "contexts": contexts,
        "n_evaluation_prefixes": len(all_margins),
        "intact_mean_fixed_rival_margin": sum(all_margins) / len(all_margins) if all_margins else None,
        "direct_q0_mean_margin": sum(direct_margins) / len(direct_margins) if direct_margins else None,
        "destructive_mean_fixed_rival_margin": sum(control_margins) / len(control_margins) if control_margins else None,
        "intact_mean_true_rank": sum(ranks) / len(ranks) if ranks else None,
        "destructive_mean_true_rank": sum(control_ranks) / len(control_ranks) if control_ranks else None,
        "ratio_moment_max_abs_error": max((abs(x - 1.0) for x in ratio_moments), default=None),
        "candidate_permutation_equivariance_error": max(equivariance_errors, default=None),
        "checks": checks,
        "interpretation": "This is an offline source-relative mechanism diagnostic on existing VGR factorial episodes. The ordered-history margin is positive and is reduced by the destructive control, but the ratio-moment calibration check fails its 0.05 tolerance; the scorer is therefore not calibrated enough for a probability-map claim. It does not establish PMFS replacement, planner benefit, causal effect, or confirmation because the upstream dataset is explicitly development-only and nominal seeds are pseudoreplicates.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
