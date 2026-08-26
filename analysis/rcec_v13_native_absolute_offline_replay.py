#!/usr/bin/env python3
"""RCEC V13 v2 fixed-trajectory shadow replay on revealed V11 evidence.

Development-only audit. Method scoring never reads source truth. Truth enters
only in the final external PMFS top-5% metric.

A1: frozen V11 Stouffer score.
A2: native-absolute CREI:
    z_native = normal-rank(current native_shadow_mass)
    c = min(z_native, z_even, z_odd)
A3: candidate-wise median of all identifiable CREI snapshots.

The native view is the current post-native/pre-RCEC PMFS candidate ordering.
No previous injected V11/RCEC posterior enters M2.

The input trajectories were produced by archived V11 runs, so outputs are
fixed-trajectory shadow evidence, not a dynamic RCEC closed-loop replay.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata

TRUTH = {
    "House01": (-0.4, -2.9),
    "House02": (0.0, -1.0),
    "House03": (-0.45, 1.9),
}
EPS = 1e-300


def normal_rank(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    ranks = rankdata(values, method="average")
    return norm.ppf((ranks - 0.5) / len(ranks))


def top5_metric(free: pd.DataFrame, probability: np.ndarray, truth: tuple[float, float]):
    p = np.maximum(np.asarray(probability, dtype=float), 0.0)
    if not np.isfinite(p).all() or not p.sum() > 0:
        raise ValueError("invalid posterior")
    p /= p.sum()
    k = max(1, math.ceil(0.05 * len(p)))
    top = np.argpartition(-p, k - 1)[:k]
    w = p[top]
    x = free.x.to_numpy(float)
    y = free.y.to_numpy(float)
    ex = float(np.sum(x[top] * w) / np.sum(w))
    ey = float(np.sum(y[top] * w) / np.sum(w))
    mean_x = float(np.sum(x * p))
    mean_y = float(np.sum(y * p))
    variance = float(np.sum(p * ((x - mean_x) ** 2 + (y - mean_y) ** 2)))
    return {
        "error_m": math.hypot(ex - truth[0], ey - truth[1]),
        "top5_x": ex,
        "top5_y": ey,
        "variance_m2": variance,
    }


def candidate_geometry(measured: pd.DataFrame, candidates: pd.DataFrame):
    free = measured[measured["occupancy"] == "Free"].reset_index(drop=True)
    gi, gj = free.grid_i.to_numpy(), free.grid_j.to_numpy()
    density = np.zeros((len(candidates), len(free)), dtype=float)
    for j, row in candidates.iterrows():
        oi, oj, si, sj = map(int, row.candidate_id.replace("quadtree_", "").split("_"))
        mask = (gi >= oi) & (gi < oi + si) & (gj >= oj) & (gj < oj + sj)
        count = int(mask.sum())
        if count <= 0:
            raise ValueError(f"candidate has no free cells: {row.candidate_id}")
        density[j, mask] = 1.0 / count
    if np.max(np.abs(density.sum(axis=1) - 1.0)) > 1e-12:
        raise ValueError("candidate density normalization failed")
    return free, density


def candidate_posterior(prior_mass: np.ndarray, score: np.ndarray):
    logm = np.log(np.maximum(np.asarray(prior_mass, float), EPS)) + np.asarray(score, float)
    mass = np.exp(logm - np.max(logm))
    return mass / mass.sum()


def catastrophe(off: float, on: float):
    improvement = (off - on) / off
    return (on - off) >= 1.0 and improvement <= -0.25


def summarize_arm(df: pd.DataFrame, column: str):
    values = df[column]
    improvement = (df.off_error_m - values) / df.off_error_m
    by_house = {}
    for house, part in df.groupby("house"):
        by_house[house] = {
            "pair_count": int(len(part)),
            "error_sum_m": float(part[column].sum()),
            "off_error_sum_m": float(part.off_error_m.sum()),
            "pooled_improvement": float((part.off_error_m.sum() - part[column].sum()) / part.off_error_m.sum()),
            "improved_pairs": int((part[column] < part.off_error_m).sum()),
        }
    return {
        "error_sum_m": float(values.sum()),
        "pooled_improvement_vs_frozen_off": float((df.off_error_m.sum() - values.sum()) / df.off_error_m.sum()),
        "improved_pairs": int((values < df.off_error_m).sum()),
        "pair_count": int(len(df)),
        "catastrophic_regressions": int(sum(catastrophe(o, n) for o, n in zip(df.off_error_m, values))),
        "worst_pair_improvement_fraction": float(improvement.min()),
        "median_pair_improvement_fraction": float(improvement.median()),
        "per_house": by_house,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("multiseed_root", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.multiseed_root
    matrix = pd.read_csv(root / "V11_MULTISEED_15PAIR_MATRIX.csv")

    records = []
    replay_max = 0.0
    candidate_id_drift = 0

    for _, baseline in matrix.iterrows():
        house, seed = str(baseline.house), int(baseline.seed)
        run = root / f"{house}_seed{seed}_on_me_aci"
        if not run.exists():
            continue
        tadm = run / "tadm"
        updates = [int(x) for x in pd.read_csv(tadm / "meaci_update_summary.csv").source_update_id]
        consensus_history = []
        candidate_ids = None
        latest = None

        for update in updates:
            candidates = pd.read_csv(tadm / f"meaci_candidate_scores_update_{update:04d}.csv").reset_index(drop=True)
            measured = pd.read_csv(run / f"context_bank/source_update_{update:04d}/measured_hit_probability.csv")
            free, density = candidate_geometry(measured, candidates)
            ids = tuple(candidates.candidate_id)
            if candidate_ids is None:
                candidate_ids = ids
            elif ids != candidate_ids:
                candidate_id_drift += 1
                raise ValueError(f"candidate identity drift: {house}/{seed}/u{update}")

            even = candidates.even_normal_rank.to_numpy(float)
            odd = candidates.odd_normal_rank.to_numpy(float)
            v11_score = candidates.temporal_rank_channel.to_numpy(float)

            native_absolute_mass = candidates.native_shadow_mass.to_numpy(float)
            native_absolute_rank = normal_rank(native_absolute_mass)
            crei = np.minimum.reduce([native_absolute_rank, even, odd])
            consensus_history.append(crei)

            # Exact replay of the archived V11 score/pseudo-posterior mapping.
            prior = candidates.geometry_prior_mass.to_numpy(float)
            v11_candidate = candidate_posterior(prior, v11_score)
            v11_grid = v11_candidate @ density
            archived = pd.read_csv(tadm / f"meaci_source_posterior_update_{update:04d}.csv")
            archived_grid = free[["x", "y"]].merge(
                archived[["x", "y", "source_probability"]], on=["x", "y"], how="left"
            ).source_probability.fillna(0.0).to_numpy(float)
            replay_max = max(replay_max, float(np.max(np.abs(v11_grid - archived_grid))))

            if update == updates[-1]:
                native_file = pd.read_csv(tadm / f"meaci_native_shadow_update_{update:04d}.csv")
                native_grid = free[["x", "y"]].merge(
                    native_file[["x", "y", "source_probability"]], on=["x", "y"], how="left"
                ).source_probability.fillna(0.0).to_numpy(float)
                native_grid = np.maximum(native_grid, 0.0)
                native_grid /= native_grid.sum()

                crei_grid = candidate_posterior(prior, crei) @ density
                temporal_median = np.median(np.stack(consensus_history, axis=0), axis=0)
                rcec_grid = candidate_posterior(prior, temporal_median) @ density
                latest = (free, native_grid, v11_grid, crei_grid, rcec_grid, len(consensus_history))

        free, native_grid, v11_grid, crei_grid, rcec_grid, snapshots = latest
        truth = TRUTH[house]
        arms = {
            "A0_NATIVE_SHADOW": native_grid,
            "A1_V11_STOUFFER": v11_grid,
            "A2_CREI_NATIVE_ABSOLUTE": crei_grid,
            "A3_RCEC_TEMPORAL_MEDIAN": rcec_grid,
        }
        row = {
            "house": house,
            "seed": seed,
            "off_error_m": float(baseline.off_error_m),
            "identifiable_score_snapshots": snapshots,
        }
        for name, grid in arms.items():
            metrics = top5_metric(free, grid, truth)
            row[name + "_error_m"] = metrics["error_m"]
            row[name + "_variance_m2"] = metrics["variance_m2"]
        records.append(row)

    if replay_max > 1e-12:
        raise SystemExit(f"V11 replay integrity failed: {replay_max}")

    df = pd.DataFrame(records).sort_values(["house", "seed"])
    summary = {
        "contract": "RCEC_V13_NATIVE_ABSOLUTE_FIXED_TRAJECTORY_AUDIT_V3",
        "status": "DEVELOPMENT_VISIBLE_OFFLINE_ONLY_NOT_CONFIRMATORY",
        "truth_used_in_scoring": False,
        "truth_used_in_external_evaluation_only": True,
        "raw_pairs_available": int(len(df)),
        "candidate_id_drift_count": int(candidate_id_drift),
        "v11_reconstruction_max_abs": replay_max,
        "temporal_memory_gate": "none; median is defined for every identifiable snapshot count",
        "native_view": "normal rank of current post-native/pre-RCEC PMFS candidate mass",
        "trajectory_contract": "archived V11 fixed trajectory; not a dynamic RCEC closed-loop replay",
        "arms": {},
    }
    arm_columns = {
        "A0_NATIVE_SHADOW": "A0_NATIVE_SHADOW_error_m",
        "A1_V11_STOUFFER": "A1_V11_STOUFFER_error_m",
        "A2_CREI_NATIVE_ABSOLUTE": "A2_CREI_NATIVE_ABSOLUTE_error_m",
        "A3_RCEC_TEMPORAL_MEDIAN": "A3_RCEC_TEMPORAL_MEDIAN_error_m",
    }
    for arm, col in arm_columns.items():
        summary["arms"][arm] = summarize_arm(df, col)

    stress = df[(df.house == "House01") & (df.seed == 653959)]
    if len(stress) == 1:
        r = stress.iloc[0]
        summary["revealed_catastrophic_stress_case"] = {
            "house": "House01",
            "seed": 653959,
            "off_error_m": float(r.off_error_m),
            "v11_error_m": float(r.A1_V11_STOUFFER_error_m),
            "crei_error_m": float(r.A2_CREI_NATIVE_ABSOLUTE_error_m),
            "rcec_error_m": float(r.A3_RCEC_TEMPORAL_MEDIAN_error_m),
        }

    args.output.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output / "rcec_v13_native_absolute_pairs_v3.csv", index=False)
    (args.output / "rcec_v13_native_absolute_summary_v3.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
