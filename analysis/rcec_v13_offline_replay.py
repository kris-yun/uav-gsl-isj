#!/usr/bin/env python3
"""RCEC V13 offline replay on revealed V11 multiseed evidence.

This is a development-only audit. Method scoring never reads source truth.
Truth enters only in the final external PMFS top-5% metric.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata

TRUTH = {"House01": (-0.4, -2.9), "House02": (0.0, -1.0), "House03": (-0.45, 1.9)}
EPS = 1e-300


def normal_rank(values: np.ndarray) -> np.ndarray:
    ranks = rankdata(np.asarray(values, dtype=float), method="average")
    return norm.ppf((ranks - 0.5) / len(ranks))


def top5_metric(free, probability, truth):
    p = np.maximum(np.asarray(probability, dtype=float), 0.0); p /= p.sum()
    k = max(1, math.ceil(0.05 * len(p)))
    top = np.argpartition(-p, k - 1)[:k]; w = p[top]
    x = free.x.to_numpy(float); y = free.y.to_numpy(float)
    ex = float(np.sum(x[top] * w) / np.sum(w)); ey = float(np.sum(y[top] * w) / np.sum(w))
    mx = float(np.sum(x * p)); my = float(np.sum(y * p))
    var = float(np.sum(p * ((x - mx) ** 2 + (y - my) ** 2)))
    return math.hypot(ex - truth[0], ey - truth[1]), var


def candidate_geometry(measured, candidates):
    free = measured[measured["occupancy"] == "Free"].reset_index(drop=True)
    gi, gj = free.grid_i.to_numpy(), free.grid_j.to_numpy()
    indicator = np.zeros((len(candidates), len(free)), dtype=float)
    density = np.zeros_like(indicator)
    for j, row in candidates.iterrows():
        oi, oj, si, sj = map(int, row.candidate_id.replace("quadtree_", "").split("_"))
        mask = (gi >= oi) & (gi < oi + si) & (gj >= oj) & (gj < oj + sj)
        n = int(mask.sum())
        if n <= 0: raise ValueError(f"candidate has no free cells: {row.candidate_id}")
        indicator[j, mask] = 1.0; density[j, mask] = 1.0 / n
    return free, indicator, density


def candidate_mass_from_grid(free, indicator, path):
    grid = pd.read_csv(path)
    p = free[["x", "y"]].merge(grid[["x", "y", "source_probability"]], on=["x", "y"], how="left").source_probability.fillna(0.0).to_numpy(float)
    p = np.maximum(p, 0.0); p /= p.sum()
    return indicator @ p


def candidate_posterior(prior, score):
    logm = np.log(np.maximum(np.asarray(prior, float), EPS)) + np.asarray(score, float)
    m = np.exp(logm - np.max(logm)); return m / m.sum()


def catastrophe(off, on):
    return (on - off) >= 1.0 and (off - on) / off <= -0.25


def summarize(df, col):
    imp = (df.off_error_m - df[col]) / df.off_error_m
    return {
        "pooled_improvement_vs_frozen_off": float((df.off_error_m.sum() - df[col].sum()) / df.off_error_m.sum()),
        "improved_pairs": int((df[col] < df.off_error_m).sum()),
        "pair_count": int(len(df)),
        "catastrophic_regressions": int(sum(catastrophe(o, n) for o, n in zip(df.off_error_m, df[col]))),
        "worst_pair_improvement_fraction": float(imp.min()),
        "per_house": {h: {"pooled_improvement": float((p.off_error_m.sum() - p[col].sum()) / p.off_error_m.sum()), "improved_pairs": int((p[col] < p.off_error_m).sum()), "pair_count": int(len(p))} for h, p in df.groupby("house")},
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("multiseed_root", type=Path); ap.add_argument("--output", type=Path, required=True); args = ap.parse_args()
    root = args.multiseed_root; matrix = pd.read_csv(root / "V11_MULTISEED_15PAIR_MATRIX.csv")
    records = []; replay_max = 0.0
    for _, baseline in matrix.iterrows():
        house, seed = str(baseline.house), int(baseline.seed)
        run = root / f"{house}_seed{seed}_on_me_aci"
        if not run.exists(): continue
        tadm = run / "tadm"; updates = [int(x) for x in pd.read_csv(tadm / "meaci_update_summary.csv").source_update_id]
        history = []; candidate_ids = None
        for update in updates:
            c = pd.read_csv(tadm / f"meaci_candidate_scores_update_{update:04d}.csv").reset_index(drop=True)
            measured = pd.read_csv(run / f"context_bank/source_update_{update:04d}/measured_hit_probability.csv")
            free, indicator, density = candidate_geometry(measured, c)
            ids = tuple(c.candidate_id)
            if candidate_ids is None: candidate_ids = ids
            elif ids != candidate_ids: raise ValueError(f"candidate identity drift: {house}/{seed}/u{update}")
            even = c.even_normal_rank.to_numpy(float); odd = c.odd_normal_rank.to_numpy(float); v11 = c.temporal_rank_channel.to_numpy(float)
            after = c.native_shadow_mass.to_numpy(float)
            prev = run / f"context_bank/source_update_{update - 1:04d}/source_posterior.csv"
            before = candidate_mass_from_grid(free, indicator, prev) if update > 1 and prev.exists() else c.geometry_prior_mass.to_numpy(float)
            native_rank = normal_rank(np.log(np.maximum(after, EPS)) - np.log(np.maximum(before, EPS)))
            crei = np.minimum.reduce([native_rank, even, odd]); history.append(crei)
            prior = c.geometry_prior_mass.to_numpy(float)
            v11_grid = candidate_posterior(prior, v11) @ density
            archived = pd.read_csv(tadm / f"meaci_source_posterior_update_{update:04d}.csv")
            archived_grid = free[["x", "y"]].merge(archived[["x", "y", "source_probability"]], on=["x", "y"], how="left").source_probability.fillna(0.0).to_numpy(float)
            replay_max = max(replay_max, float(np.max(np.abs(v11_grid - archived_grid))))
            if update == updates[-1]:
                crei_grid = candidate_posterior(prior, crei) @ density
                med = np.median(np.stack(history, axis=0), axis=0); rcec_grid = candidate_posterior(prior, med) @ density
        e1, v1 = top5_metric(free, v11_grid, TRUTH[house]); e2, v2 = top5_metric(free, crei_grid, TRUTH[house]); e3, v3 = top5_metric(free, rcec_grid, TRUTH[house])
        records.append({"house": house, "seed": seed, "off_error_m": float(baseline.off_error_m), "identifiable_score_snapshots": len(history), "A1_V11_STOUFFER_error_m": e1, "A1_V11_STOUFFER_variance_m2": v1, "A2_CREI_NATIVE_INCREMENT_error_m": e2, "A2_CREI_NATIVE_INCREMENT_variance_m2": v2, "A3_RCEC_TEMPORAL_MEDIAN_error_m": e3, "A3_RCEC_TEMPORAL_MEDIAN_variance_m2": v3})
    if replay_max > 1e-12: raise SystemExit(f"V11 replay integrity failed: {replay_max}")
    df = pd.DataFrame(records).sort_values(["house", "seed"])
    summary = {"contract": "RCEC_V13_NATIVE_INCREMENT_OFFLINE_AUDIT_V2", "status": "DEVELOPMENT_VISIBLE_OFFLINE_ONLY_NOT_CONFIRMATORY", "truth_used_in_scoring": False, "truth_used_in_external_evaluation_only": True, "raw_pairs_available": int(len(df)), "v11_reconstruction_max_abs": replay_max, "temporal_median_release_gate": "none", "arms": {"A1_V11_STOUFFER": summarize(df, "A1_V11_STOUFFER_error_m"), "A2_CREI_NATIVE_INCREMENT": summarize(df, "A2_CREI_NATIVE_INCREMENT_error_m"), "A3_RCEC_TEMPORAL_MEDIAN": summarize(df, "A3_RCEC_TEMPORAL_MEDIAN_error_m")}}
    args.output.mkdir(parents=True, exist_ok=True); df.to_csv(args.output / "rcec_v13_offline_pairs.csv", index=False); (args.output / "rcec_v13_offline_summary.json").write_text(json.dumps(summary, indent=2)); print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
