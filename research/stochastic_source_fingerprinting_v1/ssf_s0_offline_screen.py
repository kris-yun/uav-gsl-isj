#!/usr/bin/env python3
"""Reproduce SSF-v1 S0 screening from the frozen Bi-Green Gate-1A review package.

No GADEN execution and no target-driven hyperparameter tuning are performed.
The core tests are:
  1) parity-fold source-held-out cross-seed retrieval;
  2) contiguous-quadrant covariance transfer;
  3) temporal-only covariance transfer;
  4) S2 A/B truth-fold-excluded rank;
  5) paired source bootstrap;
  6) internal-variability eigenspace mechanism audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import subspace_angles
from sklearn.covariance import LedoitWolf, OAS


EXPECTED_ARCHIVE_SHA = "9f2c4e93c3833b00dd82d3f53a21e2286f23afdf3e5087328fc094cada1ba2be"
SEED_C = 2026092401
SEED_D = 2026092402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def find_root(path: Path):
    if path.is_dir():
        if (path / "frozen_inputs").is_dir():
            return path, None
        kids = [p for p in path.iterdir() if p.is_dir() and (p / "frozen_inputs").is_dir()]
        if len(kids) == 1:
            return kids[0], None
        raise FileNotFoundError("could not locate review-package root")
    if sha256(path) != EXPECTED_ARCHIVE_SHA:
        raise ValueError("review archive SHA-256 mismatch")
    td = tempfile.TemporaryDirectory(prefix="ssf_s0_")
    with tarfile.open(path, "r:gz") as tf:
        tf.extractall(td.name)
    base = Path(td.name)
    kids = [p for p in base.iterdir() if p.is_dir() and (p / "frozen_inputs").is_dir()]
    if len(kids) != 1:
        raise FileNotFoundError("archive did not contain one review root")
    return kids[0], td


def target_vector(root: Path, cell: str, contract: dict) -> np.ndarray:
    a = np.load(root / "targets" / cell / "concentration.npy", allow_pickle=False)
    vals = []
    for p in contract["probe_points"]:
        x0, x1 = int(p["native_x0"]), int(p["native_x1_exclusive"])
        y0, y1 = int(p["native_y0"]), int(p["native_y1_exclusive"])
        vals.append(a[:, x0:x1, y0:y1].mean(axis=(1, 2)))
    return np.stack(vals, axis=1).reshape(-1).astype(np.float64)


def sqeuclid(q: np.ndarray, g: np.ndarray) -> np.ndarray:
    return ((q[:, None, :] - g[None, :, :]) ** 2).sum(axis=2)


def ranks(dist: np.ndarray, truth: np.ndarray) -> np.ndarray:
    order = np.argsort(dist, axis=1, kind="stable")
    inv = np.empty_like(order)
    inv[np.arange(order.shape[0])[:, None], order] = np.arange(order.shape[1])[None, :]
    return inv[np.arange(len(truth)), truth] + 1


def metrics(r: np.ndarray) -> dict:
    return {
        "top1": float(np.mean(r <= 1)),
        "top3": float(np.mean(r <= 3)),
        "top10": float(np.mean(r <= 10)),
        "median_rank": float(np.median(r)),
        "mean_rank": float(np.mean(r)),
        "p90_rank": float(np.quantile(r, 0.90)),
    }


def paired_bootstrap(base_cd, base_dc, new_cd, new_dc, k: int, nboot: int = 20000):
    base = ((base_cd <= k).astype(float) + (base_dc <= k).astype(float)) / 2
    new = ((new_cd <= k).astype(float) + (new_dc <= k).astype(float)) / 2
    d = new - base
    rng = np.random.default_rng(20260924)
    vals = []
    remaining = nboot
    while remaining:
        m = min(1000, remaining)
        idx = rng.integers(0, len(d), size=(m, len(d)))
        vals.append(d[idx].mean(axis=1))
        remaining -= m
    vals = np.concatenate(vals)
    return {
        "delta": float(d.mean()),
        "ci95": [float(x) for x in np.quantile(vals, [0.025, 0.975])],
        "bootstrap_nonpositive_fraction": float(np.mean(vals <= 0)),
    }


def full_cov_cv(xc, xd, delta, folds, estimator="lw"):
    n = len(xc)
    b_cd = np.zeros(n, dtype=int)
    b_dc = np.zeros(n, dtype=int)
    w_cd = np.zeros(n, dtype=int)
    w_dc = np.zeros(n, dtype=int)
    for f in np.unique(folds):
        te = np.where(folds == f)[0]
        tr = np.where(folds != f)[0]
        est = LedoitWolf().fit(delta[tr]) if estimator == "lw" else OAS().fit(delta[tr])
        p = est.precision_
        b_cd[te] = ranks(sqeuclid(xc[te], xd), te)
        b_dc[te] = ranks(sqeuclid(xd[te], xc), te)

        diff = xc[te, None, :] - xd[None, :, :]
        score = np.einsum("qgd,df,qgf->qg", diff, p, diff, optimize=True)
        w_cd[te] = ranks(score, te)

        diff = xd[te, None, :] - xc[None, :, :]
        score = np.einsum("qgd,df,qgf->qg", diff, p, diff, optimize=True)
        w_dc[te] = ranks(score, te)
    return b_cd, b_dc, w_cd, w_dc


def temporal_cov_cv(xc, xd, delta, folds):
    n = len(xc)
    r_cd = np.zeros(n, dtype=int)
    r_dc = np.zeros(n, dtype=int)
    for f in np.unique(folds):
        te = np.where(folds == f)[0]
        tr = np.where(folds != f)[0]
        dm = delta[tr].reshape(-1, 10, 30)
        xt = dm.transpose(0, 2, 1).reshape(-1, 10)
        pt = LedoitWolf().fit(xt).precision_

        def score(q, g):
            out = np.empty((len(q), len(g)))
            for i in range(len(q)):
                rr = (q[i][None, :] - g).reshape(len(g), 10, 30)
                out[i] = np.einsum("ntp,tu,nup->n", rr, pt, rr, optimize=True)
            return out

        r_cd[te] = ranks(score(xc[te], xd), te)
        r_dc[te] = ranks(score(xd[te], xc), te)
    return r_cd, r_dc


def target_rank(y, mu, precision, truth_idx):
    z = np.log1p(y)
    diff = mu - z
    score = np.einsum("nd,df,nf->n", diff, precision, diff, optimize=True)
    order = np.argsort(score)
    return int(np.where(order == truth_idx)[0][0] + 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    root, td = find_root(args.review)
    bank = pd.read_csv(root / "frozen_inputs" / "source_bank.tsv", sep="\t")
    contract = json.loads((root / "frozen_inputs" / "gate1a_contract.json").read_text())
    sids = bank["source_id"].tolist()
    if len(sids) != 630:
        raise ValueError(f"expected 630 sources, got {len(sids)}")
    sid_to_i = {s: i for i, s in enumerate(sids)}

    c = np.stack([
        np.load(root / "predictions" / f"seed_{SEED_C}" / f"{s}.npy", allow_pickle=False)
        for s in sids
    ]).astype(np.float64)
    d = np.stack([
        np.load(root / "predictions" / f"seed_{SEED_D}" / f"{s}.npy", allow_pickle=False)
        for s in sids
    ]).astype(np.float64)

    xc, xd = np.log1p(c), np.log1p(d)
    delta = xc - xd
    mu = (xc + xd) / 2

    pi = bank["pmfs_i"].to_numpy(int)
    pj = bank["pmfs_j"].to_numpy(int)
    parity = (pi % 2) * 2 + (pj % 2)

    xm = float(np.median(bank["x_m"]))
    ym = float(np.median(bank["y_m"]))
    quadrant = ((bank["x_m"].to_numpy() > xm).astype(int) * 2
                + (bank["y_m"].to_numpy() > ym).astype(int))

    pb_cd, pb_dc, pw_cd, pw_dc = full_cov_cv(xc, xd, delta, parity, "lw")
    _, _, po_cd, po_dc = full_cov_cv(xc, xd, delta, parity, "oas")
    qb_cd, qb_dc, qw_cd, qw_dc = full_cov_cv(xc, xd, delta, quadrant, "lw")
    qt_cd, qt_dc = temporal_cov_cv(xc, xd, delta, quadrant)

    truth = sid_to_i[contract["truth_source_id"]]
    truth_fold = int(parity[truth])
    tr = np.where(parity != truth_fold)[0]
    truth_est = LedoitWolf().fit(delta[tr])
    target_a = target_vector(root, "S2_W2_A", contract)
    target_b = target_vector(root, "S2_W2_B", contract)

    def euclid_target_rank(y):
        z = np.log1p(y)
        score = ((mu - z) ** 2).sum(axis=1)
        order = np.argsort(score)
        return int(np.where(order == truth)[0][0] + 1)

    evals, evecs = np.linalg.eigh(truth_est.covariance_)
    ii = np.argsort(evals)[::-1]
    evals = evals[ii]
    evecs = evecs[:, ii]
    cov_cum = np.cumsum(evals) / evals.sum()

    def mode_audit(y):
        z = np.log1p(y)
        residual = z - mu[truth]
        coeff2 = (evecs.T @ residual) ** 2
        weighted = coeff2 / evals
        raw = {}
        w = {}
        for k in (10, 50, 100):
            raw[str(k)] = float(coeff2[:k].sum() / coeff2.sum())
            w[str(k)] = float(weighted[:k].sum() / weighted.sum())
        return {"raw_residual_fraction": raw, "precision_weighted_fraction": w}

    quad_cov = []
    for f in np.unique(quadrant):
        quad_cov.append(LedoitWolf().fit(delta[quadrant == f]).covariance_)
    hetero = []
    for i in range(4):
        for j in range(i + 1, 4):
            ci, cj = quad_cov[i], quad_cov[j]
            rel = np.linalg.norm(ci - cj, "fro") / (
                (np.linalg.norm(ci, "fro") + np.linalg.norm(cj, "fro")) / 2
            )
            ei, vi = np.linalg.eigh(ci)
            ej, vj = np.linalg.eigh(cj)
            ui = vi[:, np.argsort(ei)[-10:]]
            uj = vj[:, np.argsort(ej)[-10:]]
            ang = np.degrees(subspace_angles(ui, uj))
            hetero.append({
                "quadrants": [i, j],
                "relative_frobenius": float(rel),
                "top10_subspace_mean_angle_deg": float(ang.mean()),
                "top10_subspace_max_angle_deg": float(ang.max()),
            })

    result = {
        "decision": "SSF_V1_S0_HOLD_SOURCE_CONDITIONED_VARIABILITY_REQUIRED",
        "review_package_expected_sha256": EXPECTED_ARCHIVE_SHA,
        "source_count": 630,
        "representation": "log1p",
        "parity_fold_sizes": np.bincount(parity).tolist(),
        "quadrant_fold_sizes": np.bincount(quadrant).tolist(),
        "parity_cv": {
            "baseline": {"C_to_D": metrics(pb_cd), "D_to_C": metrics(pb_dc)},
            "ledoit_wolf": {"C_to_D": metrics(pw_cd), "D_to_C": metrics(pw_dc)},
            "oas": {"C_to_D": metrics(po_cd), "D_to_C": metrics(po_dc)},
            "paired_bootstrap_ledoit_wolf": {
                f"top{k}": paired_bootstrap(pb_cd, pb_dc, pw_cd, pw_dc, k)
                for k in (1, 3, 10)
            },
        },
        "truth_fold_excluded_S2": {
            "truth_source_id": contract["truth_source_id"],
            "truth_parity_fold": truth_fold,
            "log1p_euclidean": {
                "S2_W2_A_rank": euclid_target_rank(target_a),
                "S2_W2_B_rank": euclid_target_rank(target_b),
            },
            "ledoit_wolf_internal_variability": {
                "S2_W2_A_rank": target_rank(target_a, mu, truth_est.precision_, truth),
                "S2_W2_B_rank": target_rank(target_b, mu, truth_est.precision_, truth),
            },
        },
        "mechanism": {
            "covariance_variance_explained": {
                "top10": float(cov_cum[9]),
                "top50": float(cov_cum[49]),
                "top100": float(cov_cum[99]),
            },
            "S2_W2_A": mode_audit(target_a),
            "S2_W2_B": mode_audit(target_b),
        },
        "contiguous_quadrant_cv": {
            "baseline": {"C_to_D": metrics(qb_cd), "D_to_C": metrics(qb_dc)},
            "shared_full_ledoit_wolf": {
                "C_to_D": metrics(qw_cd), "D_to_C": metrics(qw_dc)
            },
            "temporal_only_ledoit_wolf": {
                "C_to_D": metrics(qt_cd), "D_to_C": metrics(qt_dc)
            },
            "paired_bootstrap_temporal_top3": paired_bootstrap(
                qb_cd, qb_dc, qt_cd, qt_dc, 3
            ),
        },
        "quadrant_covariance_heterogeneity": hetero,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "decision": result["decision"],
        "parity_baseline_top3": [
            result["parity_cv"]["baseline"]["C_to_D"]["top3"],
            result["parity_cv"]["baseline"]["D_to_C"]["top3"],
        ],
        "parity_whitened_top3": [
            result["parity_cv"]["ledoit_wolf"]["C_to_D"]["top3"],
            result["parity_cv"]["ledoit_wolf"]["D_to_C"]["top3"],
        ],
        "quadrant_shared_top3": [
            result["contiguous_quadrant_cv"]["shared_full_ledoit_wolf"]["C_to_D"]["top3"],
            result["contiguous_quadrant_cv"]["shared_full_ledoit_wolf"]["D_to_C"]["top3"],
        ],
        "quadrant_temporal_top3": [
            result["contiguous_quadrant_cv"]["temporal_only_ledoit_wolf"]["C_to_D"]["top3"],
            result["contiguous_quadrant_cv"]["temporal_only_ledoit_wolf"]["D_to_C"]["top3"],
        ],
        "S2_ranks": result["truth_fold_excluded_S2"],
        "out": str(args.out),
    }, indent=2))
    if td is not None:
        td.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
