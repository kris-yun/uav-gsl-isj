#!/usr/bin/env python3
"""Small cross-fitted AVESM gate on independent current-runtime realizations.

The route is fixed before this evaluator sees any source coordinate.  Each
candidate's Bernoulli distance model is fitted on a different RNG realization
of that candidate and evaluated on the held-out realization.  The script is a
mechanism gate, not a confirmation claim: with two held-out realizations it
can falsify the route/model contract but cannot establish benchmark-level
performance.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


BINS = (0.0, 0.8, 1.2, 2.0, 3.0, 5.0, 99.0)
COORDS = {"A": (-0.6, 1.95), "B": (-0.4, -2.9)}
HIT_THRESHOLD_PPM = 0.1
LOG20 = math.log(20.0)


def load(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def bin_id(distance: float) -> int:
    for i in range(len(BINS) - 1):
        if BINS[i] <= distance < BINS[i + 1]:
            return i
    return len(BINS) - 2


def distance(row, xy) -> float:
    x, y = row["pose_xy"]
    return math.hypot(float(x) - xy[0], float(y) - xy[1])


def fit(rows, xy, threshold):
    # Jeffreys/Laplace-safe smoothing is fixed before evaluation.
    counts = [[1.0, 1.0] for _ in range(len(BINS) - 1)]
    for row in rows:
        b = bin_id(distance(row, xy))
        y = int(float(row["gas_ppm"]) > threshold)
        counts[b][y] += 1.0
    return [[v / sum(pair) for v in pair] for pair in counts]


def score(rows, models, candidates, threshold, kappa):
    log_e = {s: 0.0 for s in candidates}
    trace = []
    for row in rows:
        y = int(float(row["gas_ppm"]) > threshold)
        p = {s: models[s][bin_id(distance(row, COORDS[s]))][y] for s in candidates}
        for s in candidates:
            rivals = [u for u in candidates if u != s]
            q = sum(p[u] for u in rivals) / len(rivals)
            # Safe power tempering: for 0 < kappa <= 1, concavity preserves
            # the e-value expectation bound when the base factor is valid.
            log_e[s] += kappa * math.log(q / p[s])
        trace.append(dict(log_e))
    return trace


def shuffled(rows, seed):
    out = [dict(row) for row in rows]
    values = [row["gas_ppm"] for row in out]
    random.Random(seed).shuffle(values)
    for row, value in zip(out, values):
        row["gas_ppm"] = value
    return out


def margin(trace, true_source):
    rival = next(s for s in trace[-1] if s != true_source)
    return trace[-1][rival] - trace[-1][true_source]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a-train", type=Path, required=True)
    ap.add_argument("--a-eval", type=Path, required=True)
    ap.add_argument("--b-train", type=Path, required=True)
    ap.add_argument("--b-eval", type=Path, required=True)
    ap.add_argument("--hit-threshold", type=float, default=HIT_THRESHOLD_PPM)
    ap.add_argument("--kappa", type=float, default=1.0)
    ap.add_argument("--permutation-count", type=int, default=100)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    train = {"A": load(args.a_train), "B": load(args.b_train)}
    eval_rows = {"A": load(args.a_eval), "B": load(args.b_eval)}
    threshold = args.hit_threshold
    if not 0.0 < args.kappa <= 1.0:
        ap.error("--kappa must be in (0,1]")
    if args.permutation_count < 1:
        ap.error("--permutation-count must be positive")
    kappa = args.kappa
    models = {s: fit(train[s], COORDS[s], threshold) for s in ("A", "B")}
    intact = {}
    controls = {}
    null_crosses = {}
    null_final_e = {}
    permutation_errors = []
    for true_source in ("A", "B"):
        tr = score(eval_rows[true_source], models, ("A", "B"), threshold, kappa)
        tr_reordered = score(eval_rows[true_source], models, ("B", "A"), threshold, kappa)
        permutation_errors.extend(abs(x["A"] - y["A"]) for x, y in zip(tr, tr_reordered))
        permutation_errors.extend(abs(x["B"] - y["B"]) for x, y in zip(tr, tr_reordered))
        perm_traces = [score(shuffled(eval_rows[true_source], 9100 + ord(true_source) * 1000 + i), models, ("A", "B"), threshold, kappa) for i in range(args.permutation_count)]
        perm_margins = [margin(x, true_source) for x in perm_traces]
        intact[true_source] = {"margin_rival_minus_true": margin(tr, true_source), "true_log_e_max": max(x[true_source] for x in tr)}
        controls[true_source] = {
            "mean_margin_rival_minus_true": sum(perm_margins) / len(perm_margins),
            "mean_absolute_margin": sum(abs(x) for x in perm_margins) / len(perm_margins),
            "threshold_cross_rate": sum(max(x[true_source] for x in trc) >= LOG20 for trc in perm_traces) / len(perm_traces),
        }
        null_crosses[true_source] = max(x[true_source] for x in tr) >= LOG20
        null_final_e[true_source] = math.exp(tr[-1][true_source])

    intact_margins = [v["margin_rival_minus_true"] for v in intact.values()]
    control_abs_margins = [v["mean_absolute_margin"] for v in controls.values()]
    intact_abs_margins = [abs(x) for x in intact_margins]
    permutation_cross_rates = [v["threshold_cross_rate"] for v in controls.values()]
    checks = {
        "heldout_true_source_margin_positive_both": all(x > 0 for x in intact_margins),
        "shuffle_reduces_mean_absolute_margin": all(c < i for c, i in zip(control_abs_margins, intact_abs_margins)),
        "heldout_null_threshold_cross_rate_below_0_1": sum(null_crosses.values()) / 2 < 0.1,
        "permutation_threshold_cross_rate_below_0_1": all(x < 0.1 for x in permutation_cross_rates),
        "candidate_list_permutation_error_below_1e-12": max(permutation_errors) < 1e-12,
        "heldout_null_mean_final_e_at_most_one": sum(null_final_e.values()) / 2 <= 1.0,
    }
    result = {
        "contract": "AVESM_CROSS_FITTED_DISTANCE_E_VALUE_GATE_V1",
        "status": "PASS_MECHANISM_GATE" if all(checks.values()) else "NO_GO_MECHANISM_GATE",
        "route": "House01 occupancy-bounds serpentine sweep; source-blind route file",
        "candidate_coordinates": COORDS,
        "hit_threshold_ppm": threshold,
        "kappa": kappa,
        "train_eval_separation": "seed1234 -> seed20260915 per candidate",
        "heldout": intact,
        "permutation_control": controls,
        "null_threshold_crosses": null_crosses,
        "null_final_e": null_final_e,
        "permutation_count": args.permutation_count,
        "checks": checks,
        "scope": "bounded current-runtime mechanism gate only; not PMFS confirmation or closed-loop evidence",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS_MECHANISM_GATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
