#!/usr/bin/env python3
"""Transport-uncertainty-whitened identifiability/completeness gate.

Expected input is a long-form CSV with one row per
(context, candidate, transport_member) and numeric feature columns.

Required columns (renamable by CLI):
  context_id,candidate_id,transport_member
Feature columns are either supplied with --feature-cols or selected by prefix.

For every context this script estimates:
  mu_s        : mean response feature for each candidate across transport members
  Sigma_tr    : pooled within-candidate transport covariance
  W           : regularized inverse square-root of Sigma_tr
  M_tilde     : centered candidate means after whitening
  sigma       : singular values of M_tilde / sqrt(K)
  gamma_r     : sigma_r / sigma_1  (relative conditioning)
  alpha_r     : sigma_r            (absolute weakest retained contrast strength)

The default retained contrast order r=3 matches the existing 4-source
observability protocol (S-1=3). For a local hard-negative candidate set,
use --contrast-order min(3,K-1) explicitly if K<4.

IMPORTANT:
- gamma/alpha are diagnostics/gates, not source labels or posterior evidence.
- Thresholds MUST be calibrated on development contexts only and frozen before
  held-out evaluation.
- This implementation never uses source truth to compute the gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Long-form M1 ensemble CSV")
    p.add_argument("--output", required=True, help="Per-context gate CSV")
    p.add_argument("--context-col", default="context_id")
    p.add_argument("--candidate-col", default="candidate_id")
    p.add_argument("--member-col", default="transport_member")
    p.add_argument("--feature-prefix", default="f_", help="Auto-select numeric columns starting with this prefix")
    p.add_argument("--feature-cols", default="", help="Comma-separated explicit feature columns")
    p.add_argument("--contrast-order", type=int, default=3, help="Retained source-contrast mode r (1-indexed)")
    p.add_argument("--ridge-rel", type=float, default=1e-3, help="Relative ridge added to transport covariance trace/d")
    p.add_argument("--eig-floor-rel", type=float, default=1e-8, help="Eigenvalue floor relative to largest covariance eigenvalue")
    p.add_argument("--gamma-threshold", type=float, default=None, help="Optional frozen threshold; do not tune on test")
    p.add_argument("--alpha-threshold", type=float, default=None, help="Optional frozen threshold; do not tune on test")
    p.add_argument("--candidate-list", default="", help="Optional comma-separated candidate IDs for local hard-negative gate")
    p.add_argument("--meta-output", default="", help="Optional JSON metadata path")
    return p.parse_args()


def select_features(df: pd.DataFrame, args: argparse.Namespace) -> list[str]:
    if args.feature_cols:
        cols = [x.strip() for x in args.feature_cols.split(",") if x.strip()]
    else:
        cols = [c for c in df.columns if c.startswith(args.feature_prefix) and pd.api.types.is_numeric_dtype(df[c])]
    if not cols:
        raise ValueError("No feature columns found. Use --feature-cols or --feature-prefix.")
    return cols


def inv_sqrt_cov(cov: np.ndarray, ridge_rel: float, eig_floor_rel: float) -> tuple[np.ndarray, dict]:
    d = cov.shape[0]
    scale = float(np.trace(cov) / max(d, 1))
    if not np.isfinite(scale) or scale <= 0:
        scale = 1.0
    cov_reg = cov + np.eye(d) * (ridge_rel * scale)
    vals, vecs = np.linalg.eigh(cov_reg)
    vmax = float(max(vals.max(), 1e-15))
    floor = eig_floor_rel * vmax
    vals_clip = np.maximum(vals, floor)
    W = (vecs * (1.0 / np.sqrt(vals_clip))) @ vecs.T
    return W, {
        "cov_trace_over_d": scale,
        "cov_eig_min": float(vals.min()),
        "cov_eig_max": float(vals.max()),
        "cov_condition_reg": float(vals_clip.max() / vals_clip.min()),
    }


def context_gate(g: pd.DataFrame, candidate_col: str, member_col: str, feat: list[str], r: int,
                 ridge_rel: float, eig_floor_rel: float) -> dict:
    # Require balanced-enough member replication candidate-wise.
    grouped = list(g.groupby(candidate_col, sort=True))
    if len(grouped) < r + 1:
        raise ValueError(f"Need at least {r+1} candidates for contrast order r={r}; got {len(grouped)}")

    mus = []
    residual_blocks = []
    member_counts = []
    candidate_ids = []
    for cid, cg in grouped:
        X = cg[feat].to_numpy(float)
        if len(X) < 2:
            raise ValueError(f"Candidate {cid} has <2 transport members")
        mu = X.mean(axis=0)
        mus.append(mu)
        residual_blocks.append(X - mu)
        member_counts.append(len(X))
        candidate_ids.append(str(cid))

    MU = np.vstack(mus)
    R = np.vstack(residual_blocks)
    # Pooled within-candidate covariance, using residual dof.
    denom = max(sum(n - 1 for n in member_counts), 1)
    cov = (R.T @ R) / denom
    W, cov_meta = inv_sqrt_cov(cov, ridge_rel, eig_floor_rel)

    MUc = MU - MU.mean(axis=0, keepdims=True)
    Mwhite = MUc @ W.T
    # Normalize by sqrt(K) so alpha has a stable RMS-like scale across local candidate set sizes.
    svals = np.linalg.svd(Mwhite / np.sqrt(len(Mwhite)), compute_uv=False)
    s1 = float(svals[0]) if len(svals) else 0.0
    sr = float(svals[r - 1]) if len(svals) >= r else 0.0
    gamma = float(sr / s1) if s1 > 0 else 0.0

    # Pairwise Mahalanobis candidate separation is a useful secondary, label-free audit statistic.
    sq = np.sum(Mwhite * Mwhite, axis=1, keepdims=True)
    d2 = np.maximum(sq + sq.T - 2 * (Mwhite @ Mwhite.T), 0.0)
    tri = d2[np.triu_indices(len(Mwhite), 1)]
    pair_min = float(np.sqrt(tri.min())) if len(tri) else 0.0
    pair_median = float(np.median(np.sqrt(tri))) if len(tri) else 0.0

    out = {
        "n_candidates": len(grouped),
        "n_features": len(feat),
        "member_min": int(min(member_counts)),
        "member_max": int(max(member_counts)),
        "contrast_order": int(r),
        "sigma1": s1,
        "alpha": sr,
        "gamma": gamma,
        "pairwise_whitened_min": pair_min,
        "pairwise_whitened_median": pair_median,
        **cov_meta,
    }
    for i, sv in enumerate(svals[: min(8, len(svals))], start=1):
        out[f"sigma{i}"] = float(sv)
    return out


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input)
    required = [args.context_col, args.candidate_col, args.member_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    feat = select_features(df, args)

    if args.candidate_list:
        keep = {x.strip() for x in args.candidate_list.split(",") if x.strip()}
        df = df[df[args.candidate_col].astype(str).isin(keep)].copy()
        if df.empty:
            raise ValueError("--candidate-list removed all rows")

    rows = []
    failures = []
    for ctx, g in df.groupby(args.context_col, sort=True):
        try:
            r = context_gate(g, args.candidate_col, args.member_col, feat, args.contrast_order,
                             args.ridge_rel, args.eig_floor_rel)
            r[args.context_col] = ctx
            if args.gamma_threshold is not None:
                r["pass_gamma"] = bool(r["gamma"] >= args.gamma_threshold)
            if args.alpha_threshold is not None:
                r["pass_alpha"] = bool(r["alpha"] >= args.alpha_threshold)
            if args.gamma_threshold is not None and args.alpha_threshold is not None:
                r["gate_pass"] = bool(r["pass_gamma"] and r["pass_alpha"])
            rows.append(r)
        except Exception as e:
            failures.append({args.context_col: str(ctx), "error": str(e)})

    if not rows:
        raise RuntimeError(f"No context produced a valid gate row. First failures: {failures[:5]}")
    out = pd.DataFrame(rows)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    meta = {
        "input": str(args.input),
        "n_input_rows": int(len(df)),
        "n_context_ok": int(len(out)),
        "n_context_failed": int(len(failures)),
        "feature_columns": feat,
        "contrast_order": args.contrast_order,
        "ridge_rel": args.ridge_rel,
        "eig_floor_rel": args.eig_floor_rel,
        "gamma_threshold": args.gamma_threshold,
        "alpha_threshold": args.alpha_threshold,
        "failures": failures[:100],
    }
    if args.meta_output:
        Path(args.meta_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.meta_output).write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(json.dumps({
        "contexts": len(out),
        "gamma_median": float(out.gamma.median()),
        "alpha_median": float(out.alpha.median()),
        "gamma_q10_q90": [float(out.gamma.quantile(.1)), float(out.gamma.quantile(.9))],
        "alpha_q10_q90": [float(out.alpha.quantile(.1)), float(out.alpha.quantile(.9))],
        "gate_pass_rate": float(out.gate_pass.mean()) if "gate_pass" in out else None,
        "failures": len(failures),
    }, indent=2))


if __name__ == "__main__":
    main()
