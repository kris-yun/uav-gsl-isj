#!/usr/bin/env python3
"""D1 data-only Mori-Zwanzig memory proxy on the frozen Gate-1A review package.

This is NOT an implementation of MEMnets or an exact Mori-Zwanzig kernel.
It is a pre-registered proxy test: does source ranking improve only when
cross-time stochastic memory (off-diagonal temporal covariance) is retained?

No target-dependent fitting, source labels, learned classifier, or tuned
hyperparameters are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def pooled_probe(cube: np.ndarray, points: list[dict]) -> np.ndarray:
    vals = []
    for p in points:
        x0, x1 = int(p["native_x0"]), int(p["native_x1_exclusive"])
        y0, y1 = int(p["native_y0"]), int(p["native_y1_exclusive"])
        vals.append(cube[:, x0:x1, y0:y1].mean(axis=(1, 2)))
    return np.stack(vals, axis=1).astype(np.float64)


def per_time_l1(z: np.ndarray) -> np.ndarray:
    s = z.sum(axis=-1, keepdims=True)
    return np.divide(z, s, out=np.zeros_like(z, dtype=np.float64), where=s > 0)


def truth_rank(scores: np.ndarray, truth_idx: int) -> int:
    order = np.argsort(scores, kind="stable")
    return int(np.where(order == truth_idx)[0][0] + 1)


def fit_temporal_cov(z: np.ndarray, mask: np.ndarray) -> np.ndarray:
    # z: [source, seed, time, probe]
    delta = z[:, 0] - z[:, 1]
    m = np.transpose(delta[mask], (0, 2, 1)).reshape(-1, delta.shape[1])
    m = m - m.mean(axis=0, keepdims=True)
    return np.cov(m, rowvar=False, bias=False)


def score_with_temporal_metric(mean_z: np.ndarray, y: np.ndarray, k: np.ndarray) -> np.ndarray:
    ki = np.linalg.inv(k)
    r = np.transpose(mean_z - y[None, :, :], (0, 2, 1))  # [source, probe, time]
    return np.einsum("spt,tu,spu->s", r, ki, r)


def ols_coef(z: np.ndarray, order: int) -> np.ndarray:
    rows, ys = [], []
    for seq in z:
        for t in range(order, seq.shape[0]):
            rows.append(np.concatenate([seq[t-k-1] for k in range(order)]))
            ys.append(seq[t])
    x = np.asarray(rows)
    y = np.asarray(ys)
    x = np.c_[x, np.ones(len(x))]
    return np.linalg.lstsq(x, y, rcond=None)[0]


def common_time_mse(z: np.ndarray, coef: np.ndarray, order: int, common_start: int = 2) -> float:
    ps, ys = [], []
    for seq in z:
        for t in range(common_start, seq.shape[0]):
            x = np.concatenate([seq[t-k-1] for k in range(order)])
            ps.append(np.r_[x, 1.0] @ coef)
            ys.append(seq[t])
    p = np.asarray(ps)
    y = np.asarray(ys)
    return float(np.mean((p - y) ** 2))


def var1_var2_gain(z: np.ndarray) -> list[dict]:
    out = []
    for train_seed, test_seed in [(0, 1), (1, 0)]:
        c1 = ols_coef(z[:, train_seed], 1)
        c2 = ols_coef(z[:, train_seed], 2)
        m1 = common_time_mse(z[:, test_seed], c1, 1)
        m2 = common_time_mse(z[:, test_seed], c2, 2)
        out.append({
            "train_seed_index": train_seed,
            "test_seed_index": test_seed,
            "var1_mse": m1,
            "var2_mse": m2,
            "relative_gain_from_second_lag": (m1 - m2) / m1,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    root = args.review_root
    contract = json.loads((root / "frozen_inputs/gate1a_contract.json").read_text())
    bank = pd.read_csv(root / "frozen_inputs/source_bank.tsv", sep="\t")
    ids = bank["source_id"].tolist()
    truth_id = contract["truth_source_id"]
    truth_idx = ids.index(truth_id)

    seeds = contract["prediction_seeds"]
    x = np.empty((len(ids), 2, 10, 30), dtype=np.float64)
    for si, seed in enumerate(seeds):
        d = root / f"predictions/seed_{seed}"
        for i, src in enumerate(ids):
            x[i, si] = np.load(d / f"{src}.npy", allow_pickle=False).reshape(10, 30)

    ya = pooled_probe(np.load(root / "targets/S2_W2_A/concentration.npy", allow_pickle=False),
                      contract["probe_points"])
    yb = pooled_probe(np.load(root / "targets/S2_W2_B/concentration.npy", allow_pickle=False),
                      contract["probe_points"])

    xn = per_time_l1(x)
    yan = per_time_l1(ya)
    ybn = per_time_l1(yb)
    mean_xn = xn.mean(axis=1)

    identity = np.eye(10)
    full_k = fit_temporal_cov(xn, np.ones(len(ids), dtype=bool))
    diag_k = np.diag(np.diag(full_k))

    ranks = {}
    for name, k in [("identity", identity), ("diagonal_only", diag_k), ("full_temporal_memory", full_k)]:
        ranks[name] = {
            "A": truth_rank(score_with_temporal_metric(mean_xn, yan, k), truth_idx),
            "B": truth_rank(score_with_temporal_metric(mean_xn, ybn, k), truth_idx),
        }

    masks = {
        "all": np.ones(len(ids), dtype=bool),
        "even_index": (np.arange(len(ids)) % 2 == 0),
        "odd_index": (np.arange(len(ids)) % 2 == 1),
        "truth_excluded": (np.arange(len(ids)) != truth_idx),
    }
    robustness = {}
    for name, mask in masks.items():
        k = fit_temporal_cov(xn, mask)
        robustness[name] = {
            "A": truth_rank(score_with_temporal_metric(mean_xn, yan, k), truth_idx),
            "B": truth_rank(score_with_temporal_metric(mean_xn, ybn, k), truth_idx),
            "condition_number": float(np.linalg.cond(k)),
        }

    std = np.sqrt(np.diag(full_k))
    corr = full_k / np.outer(std, std)
    lag_corr = {
        str(lag): float(np.mean([corr[i, i + lag] for i in range(10 - lag)]))
        for lag in range(1, 10)
    }

    raw_var = var1_var2_gain(x)
    norm_var = var1_var2_gain(xn)

    result = {
        "decision": "D1_ADVANCE_MZ_NONMARKOVIAN_MEMORY_SIGNAL",
        "source_count": len(ids),
        "truth_source_id": truth_id,
        "ranks": ranks,
        "temporal_covariance_robustness": robustness,
        "mean_temporal_correlation_by_lag": lag_corr,
        "off_diagonal_frobenius_fraction": float(
            np.linalg.norm(full_k - np.diag(np.diag(full_k)), "fro") /
            np.linalg.norm(full_k, "fro")
        ),
        "var1_vs_var2_cross_realization": {
            "raw_ppm": raw_var,
            "per_time_l1_mass_fraction": norm_var,
        },
        "scope": (
            "Data-only proxy. This is not an exact Mori-Zwanzig kernel and does not establish "
            "the final main innovation. It tests whether off-diagonal temporal stochastic memory "
            "is load-bearing for arbitrary-source ranking."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
