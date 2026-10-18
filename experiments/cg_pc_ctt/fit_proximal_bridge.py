#!/usr/bin/env python3
"""Minimal cross-fitted proximal/IV bridge baseline for CG-PC-CTT.

This is intentionally small and falsifiable. It does NOT attempt to recover the
hidden plume realization U. It estimates an outcome bridge with a two-stage
ridge IV surrogate and reports held-out moment residuals.

Input long-form CSV: one row per observed event/window and candidate query.
Required semantic groups (prefixes configurable):
  y                 scalar observed deployable outcome/encounter target
  group_id          route/world split unit (never used as a feature)
  b_*               bridge regressors B(R_t, s, C_t)
  z_*               treatment/source-side proxy/instruments from M1 for queried s
  c_*               optional deployable context covariates
  gate_pass          optional; if present, default trains/evaluates only PASS rows

CRITICAL anti-leakage rule:
- z_* may depend on queried candidate and M1 physics.
- source-independent R/history embodied in b_* must be identical across candidate
  copies of the same event except for explicitly candidate-query terms.
- truth source, route ID, wind ID, plume seed, simulator phase, future samples,
  oracle fields must never enter b_*, z_* or c_*.

This script is a baseline test, not a theorem-level proximal estimator.
A positive result is only evidence to justify a richer bridge implementation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--y-col", default="y")
    p.add_argument("--group-col", default="group_id")
    p.add_argument("--bridge-prefix", default="b_")
    p.add_argument("--instrument-prefix", default="z_")
    p.add_argument("--context-prefix", default="c_")
    p.add_argument("--gate-col", default="gate_pass")
    p.add_argument("--include-gate-fail", action="store_true")
    p.add_argument("--splits", type=int, default=5)
    p.add_argument("--ridge-stage1", type=float, default=1.0)
    p.add_argument("--ridge-stage2", type=float, default=1.0)
    p.add_argument("--negative-control", choices=["none","shuffle_z_within_group"], default="none")
    p.add_argument("--seed", type=int, default=20260827)
    return p.parse_args()


def prefixed(df, prefix):
    return [c for c in df.columns if c.startswith(prefix) and pd.api.types.is_numeric_dtype(df[c])]


def shuffled_instruments(Z, groups, rng):
    Z2 = Z.copy()
    # Break candidate/event instrument alignment while preserving group distribution.
    for g in np.unique(groups):
        idx = np.flatnonzero(groups == g)
        if len(idx) > 1:
            Z2[idx] = Z2[rng.permutation(idx)]
    return Z2


def main():
    a = parse_args()
    df = pd.read_csv(a.input)
    for col in [a.y_col, a.group_col]:
        if col not in df:
            raise ValueError(f"missing required column {col}")
    if a.gate_col in df and not a.include_gate_fail:
        df = df[df[a.gate_col].astype(bool)].copy()
    if len(df) == 0:
        raise ValueError("no rows after gate filtering")

    bcols = prefixed(df, a.bridge_prefix)
    zcols = prefixed(df, a.instrument_prefix)
    ccols = prefixed(df, a.context_prefix)
    if not bcols or not zcols:
        raise ValueError(f"need bridge ({a.bridge_prefix}*) and instrument ({a.instrument_prefix}*) columns")

    B = df[bcols].to_numpy(float)
    Z = df[zcols].to_numpy(float)
    C = df[ccols].to_numpy(float) if ccols else np.zeros((len(df),0), float)
    y = df[a.y_col].to_numpy(float)
    groups = df[a.group_col].astype(str).to_numpy()

    rng = np.random.default_rng(a.seed)
    if a.negative_control == "shuffle_z_within_group":
        Z = shuffled_instruments(Z, groups, rng)

    n_groups = len(np.unique(groups))
    n_splits = min(a.splits, n_groups)
    if n_splits < 2:
        raise ValueError("need >=2 unique groups for held-out evaluation")

    pred = np.full(len(df), np.nan)
    fold_id = np.full(len(df), -1, int)
    moment_norm = []

    splitter = GroupKFold(n_splits=n_splits)
    for fold, (tr, te) in enumerate(splitter.split(B, y, groups)):
        # Fit scalers only on train. Context C is allowed if deployable.
        sc_b = StandardScaler().fit(B[tr])
        sc_z = StandardScaler().fit(np.hstack([Z[tr], C[tr]]))
        Bs_tr = sc_b.transform(B[tr])
        Bs_te = sc_b.transform(B[te])
        IZ_tr = sc_z.transform(np.hstack([Z[tr], C[tr]]))
        IZ_te = sc_z.transform(np.hstack([Z[te], C[te]]))

        # Stage 1: project every bridge regressor onto observed instruments/proxies.
        stage1 = Ridge(alpha=a.ridge_stage1, fit_intercept=True)
        stage1.fit(IZ_tr, Bs_tr)
        Bhat_tr = stage1.predict(IZ_tr)
        Bhat_te = stage1.predict(IZ_te)

        # Stage 2: outcome bridge using projected regressors plus deployable context.
        X2_tr = np.hstack([Bhat_tr, C[tr]])
        X2_te = np.hstack([Bhat_te, C[te]])
        stage2 = Ridge(alpha=a.ridge_stage2, fit_intercept=True)
        stage2.fit(X2_tr, y[tr])
        pred[te] = stage2.predict(X2_te)
        fold_id[te] = fold

        # Held-out conditional moment audit: E[Z*(Y-h)] should approach 0.
        resid = y[te] - pred[te]
        Zte = IZ_te[:, : Z.shape[1]]
        moments = (Zte * resid[:,None]).mean(axis=0)
        moment_norm.append(float(np.linalg.norm(moments)))

    resid = y - pred
    mse = float(np.mean(resid**2))
    mae = float(np.mean(np.abs(resid)))
    corr = float(np.corrcoef(y, pred)[0,1]) if np.std(y)>0 and np.std(pred)>0 else 0.0

    out = df.copy()
    out["bridge_pred"] = pred
    out["bridge_resid"] = resid
    out["bridge_fold"] = fold_id
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.output, index=False)

    summary = {
        "n_rows": int(len(df)),
        "n_groups": int(n_groups),
        "n_splits": int(n_splits),
        "bridge_cols": bcols,
        "instrument_cols": zcols,
        "context_cols": ccols,
        "negative_control": a.negative_control,
        "heldout_mse": mse,
        "heldout_mae": mae,
        "heldout_corr": corr,
        "heldout_moment_norm_mean": float(np.mean(moment_norm)),
        "heldout_moment_norm_per_fold": moment_norm,
    }
    print(json.dumps(summary, indent=2))
    Path(a.output + ".summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
