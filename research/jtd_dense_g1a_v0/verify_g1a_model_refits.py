#!/usr/bin/env python3
"""Independent Gaussian refit audit using Cholesky, not scorer precision algebra."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular
from scipy.special import logsumexp
from sklearn.covariance import OAS
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

FOLDS = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15))
S, R = 168, 16


def fit_one(data: np.ndarray, mode: str) -> tuple[np.ndarray, np.ndarray]:
    fitted = OAS(assume_centered=False, store_precision=False).fit(data)
    covariance = fitted.covariance_.copy()
    if mode == "diag":
        covariance = np.diag(np.diag(covariance))
    d = covariance.shape[0]
    covariance.flat[::d+1] += 1e-10 * max(1.0, float(np.trace(covariance))/d)
    return fitted.location_.copy(), covariance


def score(targets: np.ndarray, models: list[tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
    output = np.empty((len(targets), len(models)))
    for source, (mean, covariance) in enumerate(models):
        lower = np.linalg.cholesky(covariance)
        projected = solve_triangular(lower, (targets-mean).T, lower=True, check_finite=False)
        output[:, source] = -0.5*(len(mean)*np.log(2*np.pi)+np.sum(projected*projected, axis=0)) - np.log(np.diag(lower)).sum()
    return output


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--tensor", type=Path, required=True)
    p.add_argument("--posteriors", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    x = np.load(a.tensor, allow_pickle=False)
    with np.load(a.posteriors, allow_pickle=False) as z:
        stored = z["logpost"]
    assert x.shape == (S, R, 10, 30) and stored.shape == (4, S, R, S)
    differences = []
    mbd_block_exact_count = 0
    for fi, eval_ix in enumerate(FOLDS):
        ref_ix = [r for r in range(R) if r not in eval_ix]
        z = np.empty((S, R, 10))
        for b in range(5):
            raw = x[:, :, [2*b, 2*b+1], :].reshape(S, R, 60)
            train = raw[:, ref_ix].reshape(S*12, 60)
            scaler = StandardScaler().fit(train)
            pca = PCA(n_components=2, svd_solver="full").fit(scaler.transform(train))
            z[:, :, 2*b:2*b+2] = pca.transform(scaler.transform(raw.reshape(S*R, 60))).reshape(S, R, 2)
        ref = z[:, ref_ix]
        targets = z[:, list(eval_ix)].reshape(S*4, 10)
        full_models = [fit_one(ref[s], "full") for s in range(S)]
        full = score(targets, full_models)
        diag = score(targets, [fit_one(ref[s], "diag") for s in range(S)])
        bp = np.zeros_like(full)
        for b in range(5):
            sl = slice(2*b, 2*b+2)
            bp += score(targets[:, sl], [fit_one(ref[s, :, sl], "full") for s in range(S)])
        mbd_models = []
        for mean, covariance in full_models:
            c = np.zeros_like(covariance)
            for b in range(5):
                sl = slice(2*b, 2*b+2)
                c[sl, sl] = covariance[sl, sl]
                if not np.array_equal(c[sl, sl], covariance[sl, sl]):
                    raise AssertionError("MBD block marginal changed")
                mbd_block_exact_count += 1
            mbd_models.append((mean, c))
        mbd = score(targets, mbd_models)
        for mi, (name, ll) in enumerate((('FULL', full), ('BLOCK_PRODUCT', bp), ('MATCHED_BLOCK_DIAG', mbd), ('DIAG_COV', diag))):
            logpost = ll-logsumexp(ll, axis=1, keepdims=True)
            saved = stored[mi, :, list(eval_ix), :].transpose(1, 0, 2).reshape(S*4, S)
            max_abs = float(np.max(np.abs(logpost-saved)))
            if max_abs > 1e-5:
                raise AssertionError(f"{name} fold {fi} refit mismatch {max_abs}")
            differences.append({"fold": fi, "model": name, "max_abs_logposterior_difference": max_abs})
        print(f"G1A_INDEPENDENT_REFIT_FOLD {fi+1}/4", flush=True)
    output = {"independent_model_refits": "PASS", "fold_model_checks": differences,
              "max_abs_logposterior_difference": max(q["max_abs_logposterior_difference"] for q in differences),
              "matched_block_marginal_exact_checks": mbd_block_exact_count,
              "method": "Separate StandardScaler/PCA/OAS fits; Cholesky triangular solves and logsumexp; MBD constructed only from FULL stabilized block marginals."}
    a.out.write_text(json.dumps(output, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("JTD_G1A_INDEPENDENT_MODEL_REFITS_PASS", flush=True)


if __name__ == "__main__":
    main()
