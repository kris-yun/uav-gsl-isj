#!/usr/bin/env python3
"""M5 L1 hard gate: simple Gaussian models before any generative world model.

Frozen before reading L1 transition outcomes.

Arms
----
B0: local drift, zero-mean residual.
B1: global full-covariance Gaussian residual.
B2: tiny source-blind context-conditioned full-covariance Gaussian.
B3: exported GADEN-known-physics deterministic endpoint + global Gaussian residual.

Development seed fits all parameters. Independent validation seed is opened only
for final metrics/nulls. No source ID/source coordinate enters B1/B2/B3.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from pathlib import Path

import numpy as np
import torch
from scipy.stats import kurtosis, skew
from torch import nn
from torch.nn import functional as F

SEED = 20260924
EPOCHS = 30
BATCH = 4096
LR = 2e-3

# Frozen materiality thresholds.
MIN_B2_NLL_GAIN_NAT_PER_DIM = 0.10
MAX_GAUSSIAN_ABS_SKEW = 0.50
MAX_GAUSSIAN_ABS_EXCESS_KURT = 1.00
MAX_GAUSSIAN_ABS_LAG1 = 0.10
MAX_CONTEXT_ENERGY_RATIO = 1.50
MIN_CONTEXT_SHUFFLE_NLL_DAMAGE_PER_DIM = 0.03


FEATURES = [
    "wind_x0", "wind_y0", "wind_z0", "wind_speed0",
    "wall_dist_m", "wall_dir_x", "wall_dir_y", "wall_dir_z",
    "sigma0", "delta_s",
]


def read_gz(path: Path):
    rows = []
    with gzip.open(path, "rt", newline="") as f:
        rd = csv.DictReader(f)
        for r in rd:
            rows.append(r)
    if not rows:
        raise ValueError(f"empty transition file {path}")
    return rows


def arr(rows, names):
    return np.asarray([[float(r[n]) for n in names] for r in rows], dtype=np.float64)


def ids_and_frames(rows):
    ids = np.asarray([int(r["pseudo_id"]) for r in rows], dtype=np.int64)
    fr = np.asarray([int(r["frame0"]) for r in rows], dtype=np.int64)
    return ids, fr


def gaussian_fit(r):
    mu = r.mean(axis=0)
    c = np.cov(r, rowvar=False)
    c = c + np.eye(3) * max(1e-8, 1e-6 * float(np.trace(c) / 3.0))
    return mu, c


def gaussian_nll(r, mu, cov):
    inv = np.linalg.inv(cov)
    sign, logdet = np.linalg.slogdet(cov)
    if sign <= 0:
        raise ValueError("non-PD covariance")
    d = r - mu
    q = np.einsum("ni,ij,nj->n", d, inv, d)
    return 0.5 * (q + logdet + 3.0 * math.log(2.0 * math.pi))


def whiten_global(r, mu, cov):
    L = np.linalg.cholesky(cov)
    return np.linalg.solve(L, (r - mu).T).T


class TinyConditionalGaussian(nn.Module):
    """~650 parameter 10->32->9 model: mean3 + Cholesky6."""

    def __init__(self, d):
        super().__init__()
        self.fc1 = nn.Linear(d, 32)
        self.fc2 = nn.Linear(32, 9)

    def params(self, x):
        h = torch.tanh(self.fc1(x))
        o = self.fc2(h)
        mu = o[:, :3]
        raw = o[:, 3:]
        L = torch.zeros((len(x), 3, 3), dtype=x.dtype, device=x.device)
        L[:, 0, 0] = F.softplus(raw[:, 0]) + 1e-4
        L[:, 1, 0] = raw[:, 1]
        L[:, 1, 1] = F.softplus(raw[:, 2]) + 1e-4
        L[:, 2, 0] = raw[:, 3]
        L[:, 2, 1] = raw[:, 4]
        L[:, 2, 2] = F.softplus(raw[:, 5]) + 1e-4
        return mu, L

    def nll(self, x, y):
        mu, L = self.params(x)
        d = (y - mu).unsqueeze(-1)
        z = torch.linalg.solve_triangular(L, d, upper=False).squeeze(-1)
        logdet = torch.log(torch.diagonal(L, dim1=1, dim2=2)).sum(1)
        return 0.5 * (z * z).sum(1) + logdet + 1.5 * math.log(2.0 * math.pi)

    def whiten(self, x, y):
        mu, L = self.params(x)
        d = (y - mu).unsqueeze(-1)
        return torch.linalg.solve_triangular(L, d, upper=False).squeeze(-1)


def train_b2(xdev, rdev):
    xm = xdev.mean(0)
    xs = xdev.std(0)
    xs[xs < 1e-8] = 1.0
    xn = (xdev - xm) / xs
    torch.manual_seed(SEED)
    model = TinyConditionalGaussian(xdev.shape[1]).double()
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    X = torch.from_numpy(xn)
    Y = torch.from_numpy(rdev)
    gen = torch.Generator().manual_seed(SEED)
    losses = []
    for ep in range(EPOCHS):
        order = torch.randperm(len(X), generator=gen)
        total = 0.0
        count = 0
        model.train()
        for start in range(0, len(X), BATCH):
            idx = order[start : start + BATCH]
            loss = model.nll(X[idx], Y[idx]).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0)
            opt.step()
            total += float(loss.detach()) * len(idx)
            count += len(idx)
        losses.append(total / count)
    return model, xm, xs, losses


def b2_eval(model, xm, xs, x, r):
    X = torch.from_numpy((x - xm) / xs).double()
    Y = torch.from_numpy(r).double()
    model.eval()
    with torch.no_grad():
        nll = model.nll(X, Y).cpu().numpy()
        z = model.whiten(X, Y).cpu().numpy()
    return nll, z


def normality(z):
    sk = skew(z, axis=0, bias=False, nan_policy="omit")
    ku = kurtosis(z, axis=0, fisher=True, bias=False, nan_policy="omit")
    return {
        "skew": sk.tolist(),
        "excess_kurtosis": ku.tolist(),
        "max_abs_skew": float(np.nanmax(np.abs(sk))),
        "max_abs_excess_kurtosis": float(np.nanmax(np.abs(ku))),
    }


def lag1(z, ids, frames):
    order = np.lexsort((frames, ids))
    zz, ii, ff = z[order], ids[order], frames[order]
    ok = (ii[1:] == ii[:-1]) & (ff[1:] == ff[:-1] + 1)
    vals = []
    for d in range(3):
        if ok.sum() < 10:
            vals.append(float("nan"))
        else:
            a, b = zz[:-1, d][ok], zz[1:, d][ok]
            vals.append(float(np.corrcoef(a, b)[0, 1]))
    return {
        "pairs": int(ok.sum()),
        "corr_xyz": vals,
        "max_abs": float(np.nanmax(np.abs(vals))),
    }


def context_energy_ratios(z, x):
    e = np.sum(z * z, axis=1)
    result = {}
    # wall distance, wind speed, sigma/age.
    for name, j in (("wall_dist", 4), ("wind_speed", 3), ("sigma", 8)):
        q = np.quantile(x[:, j], [0, .25, .5, .75, 1.0])
        means = []
        for k in range(4):
            lo, hi = q[k], q[k + 1]
            mask = (x[:, j] >= lo) & (x[:, j] <= hi if k == 3 else x[:, j] < hi)
            means.append(float(np.mean(e[mask])) if mask.any() else float("nan"))
        finite = [m for m in means if np.isfinite(m) and m > 0]
        ratio = max(finite) / min(finite) if finite else float("nan")
        result[name] = {"quartile_edges": q.tolist(), "mean_whitened_energy": means, "max_min_ratio": ratio}
    return result


def shuffle_damage(model, xm, xs, x, r):
    rng = np.random.default_rng(SEED)
    base, _ = b2_eval(model, xm, xs, x, r)
    result = {}
    groups = {
        "wind": [0, 1, 2, 3],
        "wall": [4, 5, 6, 7],
        "age": [8],
    }
    for name, idx in groups.items():
        xx = x.copy()
        perm = rng.permutation(len(xx))
        xx[:, idx] = xx[perm][:, idx]
        n, _ = b2_eval(model, xm, xs, xx, r)
        result[name] = {
            "delta_nll_per_sample": float(n.mean() - base.mean()),
            "delta_nll_per_dim": float((n.mean() - base.mean()) / 3.0),
        }
    return result


def finite_b3(rows):
    return np.asarray(
        [
            int(r["b3_pred_alive"]) == 1
            and all(np.isfinite(float(r[n])) for n in ("b3_res_x", "b3_res_y", "b3_res_z"))
            for r in rows
        ],
        dtype=bool,
    )


def rmse(r):
    return float(np.sqrt(np.mean(np.sum(r * r, axis=1))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", type=Path, required=True)
    ap.add_argument("--val", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    dev = read_gz(args.dev)
    val = read_gz(args.val)
    xdev = arr(dev, FEATURES)
    xval = arr(val, FEATURES)
    r0dev = arr(dev, ["b0_res_x", "b0_res_y", "b0_res_z"])
    r0val = arr(val, ["b0_res_x", "b0_res_y", "b0_res_z"])
    idsval, framesval = ids_and_frames(val)

    # B0/B1.
    mu1, cov1 = gaussian_fit(r0dev)
    nll1_val = gaussian_nll(r0val, mu1, cov1)

    # B2.
    b2, xm, xs, losses = train_b2(xdev, r0dev)
    nll2_dev, z2_dev = b2_eval(b2, xm, xs, xdev, r0dev)
    nll2_val, z2_val = b2_eval(b2, xm, xs, xval, r0val)

    # B3 only where deterministic physics predicts survival and reality survived.
    m3d = finite_b3(dev)
    m3v = finite_b3(val)
    r3dev = arr(dev, ["b3_res_x", "b3_res_y", "b3_res_z"])[m3d]
    r3val = arr(val, ["b3_res_x", "b3_res_y", "b3_res_z"])[m3v]
    if len(r3dev) < 100 or len(r3val) < 100:
        raise RuntimeError("too few B3-surviving transitions")
    mu3, cov3 = gaussian_fit(r3dev)
    nll3_val = gaussian_nll(r3val, mu3, cov3)
    z3_val = whiten_global(r3val, mu3, cov3)
    ids3 = idsval[m3v]
    fr3 = framesval[m3v]
    x3 = xval[m3v]

    norm2 = normality(z2_val)
    lag2 = lag1(z2_val, idsval, framesval)
    ctx2 = context_energy_ratios(z2_val, xval)
    norm3 = normality(z3_val)
    lag3 = lag1(z3_val, ids3, fr3)
    ctx3 = context_energy_ratios(z3_val, x3)
    nulls = shuffle_damage(b2, xm, xs, xval, r0val)

    b1 = float(nll1_val.mean())
    b2v = float(nll2_val.mean())
    b3v = float(nll3_val.mean())
    b2_gain_dim = (b1 - b2v) / 3.0

    b2_gaussian = (
        norm2["max_abs_skew"] <= MAX_GAUSSIAN_ABS_SKEW
        and norm2["max_abs_excess_kurtosis"] <= MAX_GAUSSIAN_ABS_EXCESS_KURT
        and lag2["max_abs"] <= MAX_GAUSSIAN_ABS_LAG1
        and max(v["max_min_ratio"] for v in ctx2.values()) <= MAX_CONTEXT_ENERGY_RATIO
    )
    b3_gaussian = (
        norm3["max_abs_skew"] <= MAX_GAUSSIAN_ABS_SKEW
        and norm3["max_abs_excess_kurtosis"] <= MAX_GAUSSIAN_ABS_EXCESS_KURT
        and lag3["max_abs"] <= MAX_GAUSSIAN_ABS_LAG1
        and max(v["max_min_ratio"] for v in ctx3.values()) <= MAX_CONTEXT_ENERGY_RATIO
    )

    null_damage = max(v["delta_nll_per_dim"] for v in nulls.values())
    structured_after_simple = (not b2_gaussian) and (not b3_gaussian)
    context_supported = null_damage >= MIN_CONTEXT_SHUFFLE_NLL_DAMAGE_PER_DIM

    if b3_gaussian or b2_gaussian:
        decision = "GAUSSIAN_SUFFICIENT_M5_MAIN_NO_GO"
    elif (
        b2_gain_dim >= MIN_B2_NLL_GAIN_NAT_PER_DIM
        and structured_after_simple
        and context_supported
    ):
        decision = "GENERATIVE_NEEDED_ADVANCE_TO_L2"
    else:
        decision = "NO_ROBUST_GENERATIVE_SIGNAL_M5_MAIN_NO_GO"

    result = {
        "gate": "M5_L1_GENERATIVE_NECESSITY",
        "frozen_thresholds": {
            "min_b2_nll_gain_nat_per_dim": MIN_B2_NLL_GAIN_NAT_PER_DIM,
            "max_gaussian_abs_skew": MAX_GAUSSIAN_ABS_SKEW,
            "max_gaussian_abs_excess_kurtosis": MAX_GAUSSIAN_ABS_EXCESS_KURT,
            "max_gaussian_abs_lag1": MAX_GAUSSIAN_ABS_LAG1,
            "max_context_energy_ratio": MAX_CONTEXT_ENERGY_RATIO,
            "min_context_shuffle_nll_damage_per_dim": MIN_CONTEXT_SHUFFLE_NLL_DAMAGE_PER_DIM,
        },
        "counts": {
            "dev_transitions": len(dev),
            "val_transitions": len(val),
            "dev_b3_alive": int(m3d.sum()),
            "val_b3_alive": int(m3v.sum()),
        },
        "B0": {
            "dev_rmse_m": rmse(r0dev),
            "val_rmse_m": rmse(r0val),
        },
        "B1_global_gaussian": {
            "val_mean_nll": b1,
            "val_nll_per_dim": b1 / 3.0,
            "mu": mu1.tolist(),
            "cov": cov1.tolist(),
        },
        "B2_context_gaussian": {
            "trainable_parameters": sum(p.numel() for p in b2.parameters()),
            "epochs": EPOCHS,
            "loss_first": losses[0],
            "loss_last": losses[-1],
            "val_mean_nll": b2v,
            "val_nll_per_dim": b2v / 3.0,
            "gain_vs_B1_nat_per_dim": b2_gain_dim,
            "normality": norm2,
            "lag1": lag2,
            "context_energy": ctx2,
            "destructive_context_shuffles": nulls,
            "gaussian_sufficient": b2_gaussian,
        },
        "B3_known_physics_plus_gaussian": {
            "val_mean_nll": b3v,
            "val_nll_per_dim": b3v / 3.0,
            "dev_rmse_m": rmse(r3dev),
            "val_rmse_m": rmse(r3val),
            "predicted_survival_fraction_dev": float(m3d.mean()),
            "predicted_survival_fraction_val": float(m3v.mean()),
            "mu": mu3.tolist(),
            "cov": cov3.tolist(),
            "normality": norm3,
            "lag1": lag3,
            "context_energy": ctx3,
            "gaussian_sufficient": b3_gaussian,
        },
        "decision_logic": {
            "B2_material_gain": b2_gain_dim >= MIN_B2_NLL_GAIN_NAT_PER_DIM,
            "structured_after_B2_and_B3": structured_after_simple,
            "context_null_damage_supported": context_supported,
            "max_context_shuffle_damage_nat_per_dim": null_damage,
        },
        "decision": decision,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=True) + "\n")
    print(json.dumps(result, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
