#!/usr/bin/env python3
"""Offline-only V11 paper-contribution audit.

This script never runs inside the online estimator.  It consumes archived V10/V11
outputs and produces truth-external mechanism ablations for the paper:

C2: force the frozen conditional score on H02 early single-hit-site histories to
    test what the spatial replication gate prevented;
C3: compare V10 and V11 on H02/824201 to quantify posterior reversibility on
    the exact later 24-event block.

Truth is read only by this offline evaluator after scores are produced.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

SPREADS = (0.25, 0.5, 1.0)
DECAYS = (4.0, 8.0, 16.0)
UPSTREAM = (1.0, 2.0)
SLOPES = (0.5, 1.0, 2.0)
CELL = 0.3


def normal_quantile(probability: float) -> float:
    # Peter J. Acklam approximation, matching the online implementation.
    p = min(max(probability, 1e-12), 1.0 - 1e-12)
    a = (-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
         1.383577518672690e2, -3.066479806614716e1, 2.506628277459239)
    b = (-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
         6.680131188771972e1, -1.328068155288572e1)
    c = (-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838,
         -2.549732539343734, 4.374664141464968, 2.938163982698783)
    d = (7.784695709041462e-3, 3.224671290700398e-1,
         2.445134137142996, 3.754408661907416)
    low = 0.02425
    high = 1.0 - low
    if p < low:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    if p > high:
        q = math.sqrt(-2.0 * math.log(1.0-p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    q = p - 0.5
    r = q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0)


def log_mean_exp(values: list[float]) -> float:
    m = max(values)
    return m + math.log(sum(math.exp(v-m) for v in values) / len(values))


def conditional_score(events: pd.DataFrame, sx: float, sy: float, parity: int) -> float:
    indices = [i for i in range(len(events)) if parity < 0 or i % 2 == parity]
    hits = [1 if float(events.iloc[i]["hit"]) > 0.5 else 0 for i in indices]
    k = sum(hits)
    if k <= 0 or k >= len(indices):
        return float("nan")
    components: list[float] = []
    for spread in SPREADS:
        for decay in DECAYS:
            for upstream in UPSTREAM:
                bases = []
                for i in indices:
                    e = events.iloc[i]
                    wd = float(e["wind_direction"])
                    ux, uy = math.cos(wd), math.sin(wd)
                    dx, dy = float(e["x"])-sx, float(e["y"])-sy
                    downstream = dx*ux + dy*uy
                    crosswind = -dx*uy + dy*ux
                    positive = max(downstream, 0.0)
                    width = CELL + spread * positive
                    bases.append(-0.5*(crosswind/width)**2
                                 - math.log1p(positive/decay)
                                 - upstream*max(-downstream, 0.0)/CELL)
                for slope in SLOPES:
                    dynamic = [-math.inf] * (k+1)
                    dynamic[0] = 0.0
                    observed = 0.0
                    for processed, (base, hit) in enumerate(zip(bases, hits), start=1):
                        psi = slope * base
                        if hit:
                            observed += psi
                        for count in range(min(k, processed), 0, -1):
                            dynamic[count] = float(np.logaddexp(dynamic[count], dynamic[count-1] + psi))
                    components.append(observed - dynamic[k])
    return log_mean_exp(components)


def normal_ranks(values: list[float], ids: list[str]) -> np.ndarray:
    order = sorted(range(len(values)), key=lambda i: (values[i], ids[i]))
    result = np.zeros(len(values), dtype=float)
    begin = 0
    while begin < len(values):
        end = begin + 1
        while end < len(values) and abs(values[order[end]] - values[order[begin]]) <= 1e-12:
            end += 1
        average_rank = 0.5 * ((begin + 1) + end)
        z = normal_quantile((average_rank - 0.5) / len(values))
        for j in range(begin, end):
            result[order[j]] = z
        begin = end
    return result


def forced_single_site_ablation(v11_qual: Path) -> dict:
    run = v11_qual / "House02_seed825201_on_me_aci"
    evaluation = json.loads((run / "meaci_evaluation.json").read_text())
    tx, ty = map(float, evaluation["truth"])
    carrier = pd.read_csv(run / "tadm/meaci_candidate_scores_update_0003.csv")
    carrier = carrier[["candidate_id", "x", "y", "geometry_prior_mass"]].copy()
    ids = carrier["candidate_id"].astype(str).tolist()
    out = []
    for update in (1, 2):
        abstention = pd.read_csv(run / f"tadm/meaci_abstention_update_{update:04d}.csv").iloc[0]
        events = pd.read_csv(run / f"tadm/meaci_events_update_{update:04d}.csv")
        even = [conditional_score(events, float(r.x), float(r.y), 0) for _, r in carrier.iterrows()]
        odd = [conditional_score(events, float(r.x), float(r.y), 1) for _, r in carrier.iterrows()]
        z_even = normal_ranks(even, ids)
        z_odd = normal_ranks(odd, ids)
        score = (z_even + z_odd) / math.sqrt(2.0)
        prior = carrier["geometry_prior_mass"].to_numpy(float)
        logw = np.log(prior) + score
        logw -= np.max(logw)
        weight = np.exp(logw)
        weight /= weight.sum()
        distances = np.hypot(carrier["x"].to_numpy(float)-tx, carrier["y"].to_numpy(float)-ty)
        nearest = int(np.argmin(distances))
        top = int(np.argmax(weight))
        rank = int(pd.Series(score).rank(method="min", ascending=False).iloc[nearest])
        mx = float(np.sum(weight * carrier["x"].to_numpy(float)))
        my = float(np.sum(weight * carrier["y"].to_numpy(float)))
        out.append({
            "update": update,
            "abstention_reason": str(abstention["reason"]),
            "event_count": int(abstention["event_count"]),
            "even_hits": int(abstention["even_hits"]),
            "odd_hits": int(abstention["odd_hits"]),
            "hit_site_count": int(abstention["hit_site_count"]),
            "forced_top_candidate": ids[top],
            "forced_top_distance_to_truth_m": float(distances[top]),
            "nearest_truth_candidate_rank": rank,
            "candidate_count": len(carrier),
            "forced_candidate_mean_error_m": math.hypot(mx-tx, my-ty),
        })
    return {"contract": "V11_C2_SPATIAL_REPLICATION_OFFLINE_ABLATION_V1", "updates": out}


def vector(path: Path) -> np.ndarray:
    return pd.read_csv(path)["source_probability"].to_numpy(float)


def same_numeric_events(v10: pd.DataFrame, v11: pd.DataFrame) -> dict:
    cols = ("x", "y", "hit", "concentration", "wind_direction")
    return {c: float(np.max(np.abs(v10[c].to_numpy(float)-v11[c].to_numpy(float)))) for c in cols}


def reversible_ablation(v10_raw: Path, v11_phase1: Path) -> dict:
    v10 = v10_raw / "House02_seed824201_on_me_aci"
    v11 = v11_phase1 / "House02_seed824201_on_me_aci"
    e10 = json.loads((v10 / "meaci_evaluation.json").read_text())
    e11 = json.loads((v11 / "meaci_evaluation.json").read_text())
    p10_u3 = vector(v10 / "tadm/meaci_source_posterior_update_0003.csv")
    p10_u4 = vector(v10 / "context_bank/source_update_0004/source_posterior.csv")
    p11_u3 = vector(v11 / "tadm/meaci_source_posterior_update_0003.csv")
    p11_u4 = vector(v11 / "tadm/meaci_source_posterior_update_0004.csv")
    v10_new = pd.read_csv(v10 / "tadm/meaci_events_update_0004.csv")
    v11_cumulative = pd.read_csv(v11 / "tadm/meaci_events_update_0004.csv")
    v11_new = v11_cumulative.tail(len(v10_new)).reset_index(drop=True)
    return {
        "contract": "V11_C3_REVERSIBILITY_SAME_SEED_OFFLINE_ABLATION_V1",
        "seed": 824201,
        "v10_error_m": float(e10["meaci"]["pmfs_top5_error_m"]),
        "v11_error_m": float(e11["meaci"]["pmfs_top5_error_m"]),
        "v10_truth_candidate_rank": int(e10["ranks"]["meaci_rank"]),
        "v11_truth_candidate_rank": int(e11["ranks"]["meaci_rank"]),
        "v10_update3_to_update4_max_abs_posterior_change": float(np.max(np.abs(p10_u3-p10_u4))),
        "v11_update3_to_update4_max_abs_posterior_change": float(np.max(np.abs(p11_u3-p11_u4))),
        "v11_update3_to_update4_l1_posterior_change": float(np.sum(np.abs(p11_u3-p11_u4))),
        "new_update4_event_count": len(v10_new),
        "v10_v11_new_update4_event_max_abs_differences": same_numeric_events(v10_new, v11_new),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--v11-qual", type=Path, required=True,
                   help="meaci_v11_qualification_20260825 directory")
    p.add_argument("--v11-phase1", type=Path, required=True,
                   help="meaci_v11_phase1_h02_20260825 directory")
    p.add_argument("--v10-raw", type=Path, required=True,
                   help="meaci_v10_heldout_full300_20260824 directory")
    p.add_argument("--output", type=Path, default=Path("v11_offline_contribution_audit.json"))
    args = p.parse_args()
    result = {
        "status": "OFFLINE_EXPLORATORY_NOT_NEW_HELDOUT_EVIDENCE",
        "contribution_2": forced_single_site_ablation(args.v11_qual),
        "contribution_3": reversible_ablation(args.v10_raw, args.v11_phase1),
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
