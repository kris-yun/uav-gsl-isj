#!/usr/bin/env python3
"""Frozen JTD-B0 R=4 bridge. Uses only the audited R0/G0 canonical tensor."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import sys
from pathlib import Path

import numpy as np
import sklearn
from scipy.special import logsumexp
from scipy.stats import trim_mean
from sklearn.covariance import OAS
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

G0_COMMIT = "170d0ccddc559c97744af5409ec1e3642bcfa743"
R0_COMMIT = "e527beea07c33cdbc362d156545409245f029968"
CANONICAL_SHA = "7b231e88d78ca0742d9406e3673e242f8133eff543bcd0bb0c0f5363b15fe302"
N_SOURCE, N_REP, N_NULL, N_BLOCK, DIM = 18, 16, 200, 5, 10
BOOTSTRAP_DRAWS, BOOTSTRAP_SEED = 5000, 2026092502
DROP_COUNT = math.ceil(0.05 * N_SOURCE * N_REP)  # conservative 15/288


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def posterior_metrics(means: np.ndarray, covariance: np.ndarray, targets: np.ndarray,
                      truth: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    covariance = covariance.copy()
    jitter = 1e-10 * max(1.0, float(np.trace(covariance)) / DIM)
    covariance.flat[::DIM + 1] += jitter
    lower = np.linalg.cholesky(covariance)
    diff = targets[:, None, :] - means[None, :, :]
    solved = np.linalg.solve(lower, diff.reshape(-1, DIM).T).T.reshape(len(targets), N_SOURCE, DIM)
    loglik = -0.5 * np.sum(solved ** 2, axis=2)
    logpost = loglik - logsumexp(loglik, axis=1, keepdims=True)
    nll = -logpost[np.arange(len(truth)), truth]
    rank = 1 + (loglik > loglik[np.arange(len(truth)), truth, None]).sum(axis=1)
    if not np.isfinite(nll).all():
        raise ValueError("nonfinite posterior")
    return nll, rank, np.array([jitter])


def pooled_oas(training: np.ndarray, means: np.ndarray) -> tuple[np.ndarray, float]:
    residual = (training - means[:, None, :]).reshape(N_SOURCE * 3, DIM)
    fitted = OAS(assume_centered=False, store_precision=False).fit(residual)
    return fitted.covariance_, float(fitted.shrinkage_)


def permutation(q: int, fold: int, null_id: int, source: int, block: int) -> np.ndarray:
    key = f"JTD-B0|q={q}|fold={fold}|null={null_id}|source={source}|block={block}"
    bit = hashlib.sha256(key.encode("ascii")).digest()[0] & 1
    return np.array((1, 2, 0) if bit == 0 else (2, 0, 1), dtype=np.int8)


def bootstrap(delta: np.ndarray) -> tuple[float, float]:
    # Paired source-stratified hierarchical resampling: 18 source strata retained,
    # each drawing its 16 targets with replacement; source strata then resampled.
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = np.empty(BOOTSTRAP_DRAWS)
    for i in range(BOOTSTRAP_DRAWS):
        source = rng.integers(0, N_SOURCE, N_SOURCE)
        rep = rng.integers(0, N_REP, (N_SOURCE, N_REP))
        means[i] = delta[source[:, None], rep].mean()
    return tuple(float(x) for x in np.quantile(means, (0.025, 0.975)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--g0-audit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise ValueError("refuse nonempty output directory")
    audit = json.loads(args.g0_audit.read_text(encoding="utf-8"))
    if not audit.get("input_contract_pass") or not audit.get("all_288_raw_cube_reextractions_exact"):
        raise ValueError("G0 raw R0 audit is not PASS")
    if audit["base_commit"] != R0_COMMIT or audit["canonical_cache_sha256"] != CANONICAL_SHA:
        raise ValueError("G0 input contract/hash drift")
    if sha(args.cache) != CANONICAL_SHA:
        raise ValueError("R0 canonical cache SHA mismatch")
    with np.load(args.cache, allow_pickle=False) as loaded:
        x = loaded["X"].copy()
        source_ids = loaded["source_ids"].tolist()
        realization_ids = loaded["realization_ids"].tolist()
        if str(loaded["observable_name"]) != "raw_ppm_2x2_pooled_mean":
            raise ValueError("G0 feature input mismatch")
    if x.shape != (N_SOURCE, N_REP, 10, 30) or not np.isfinite(x).all() or (x < 0).any():
        raise ValueError("canonical R0 tensor invalid")
    args.out.mkdir(parents=True)
    full_nll = np.empty((N_SOURCE, N_REP))
    null_nll = np.empty((N_SOURCE, N_REP))
    full_rank = np.empty((N_SOURCE, N_REP), dtype=int)
    null_median_rank = np.empty((N_SOURCE, N_REP))
    fold_manifest = []
    for q in range(4):
        quartet = list(range(4 * q, 4 * q + 4))
        for fold, target_rep in enumerate(quartet):
            train_reps = [r for r in quartet if r != target_rep]
            z_train = np.empty((N_SOURCE, 3, DIM))
            z_target = np.empty((N_SOURCE, DIM))
            pca_blocks = []
            for block in range(N_BLOCK):
                raw_train = x[:, train_reps, 2*block:2*block+2, :].reshape(N_SOURCE * 3, 60)
                raw_target = x[:, target_rep, 2*block:2*block+2, :].reshape(N_SOURCE, 60)
                if np.count_nonzero(np.var(raw_train, axis=0) > 0) < 2:
                    raise ValueError(f"PCA block variance absent: Q{q+1}, fold{fold}, block{block}")
                scaler = StandardScaler().fit(raw_train)
                pca = PCA(n_components=2, svd_solver="full").fit(scaler.transform(raw_train))
                z_train[:, :, 2*block:2*block+2] = pca.transform(scaler.transform(raw_train)).reshape(N_SOURCE, 3, 2)
                z_target[:, 2*block:2*block+2] = pca.transform(scaler.transform(raw_target))
                pca_blocks.append({"block": block + 1, "time_indices_zero_based": [2*block, 2*block+1],
                                   "explained_variance_ratio": pca.explained_variance_ratio_.tolist()})
            means = z_train.mean(axis=1)
            covariance, shrinkage = pooled_oas(z_train, means)
            truth = np.arange(N_SOURCE)
            nll, rank, _ = posterior_metrics(means, covariance, z_target, truth)
            full_nll[:, target_rep] = nll
            full_rank[:, target_rep] = rank
            null_nll_fold = np.empty((N_NULL, N_SOURCE))
            null_rank_fold = np.empty((N_NULL, N_SOURCE))
            for null_id in range(N_NULL):
                shuffled = z_train.copy()
                for source in range(N_SOURCE):
                    for block in range(1, N_BLOCK):
                        sl = slice(2*block, 2*block+2)
                        perm = permutation(q+1, fold+1, null_id, source, block+1)
                        shuffled[source, :, sl] = z_train[source][perm][:, sl]
                        if not np.array_equal(np.sort(shuffled[source, :, sl], axis=0),
                                              np.sort(z_train[source, :, sl], axis=0)):
                            raise ValueError("SHUFFLED block marginal drift")
                if not np.allclose(shuffled.mean(axis=1), means, atol=1e-12, rtol=0):
                    raise ValueError("SHUFFLED source mean drift")
                null_covariance, _ = pooled_oas(shuffled, means)
                null_nll_fold[null_id], null_rank_fold[null_id], _ = posterior_metrics(
                    means, null_covariance, z_target, truth)
            null_nll[:, target_rep] = np.median(null_nll_fold, axis=0)
            null_median_rank[:, target_rep] = np.median(null_rank_fold, axis=0)
            fold_manifest.append({"quartet": q+1, "fold": fold+1,
                                  "target_replicate": target_rep+1,
                                  "train_replicates": [r+1 for r in train_reps],
                                  "full_oas_shrinkage": shrinkage, "pca": pca_blocks,
                                  "full_mean_nll": float(nll.mean()),
                                  "null_target_median_mean_nll": float(np.median(null_nll_fold, axis=0).mean())})
            print(f"Q{q+1} fold{fold+1} complete", flush=True)
    delta = null_nll - full_nll
    ci_low, ci_high = bootstrap(delta)
    flat = delta.ravel()
    positive_order = np.flatnonzero(flat > 0)
    positive_order = positive_order[np.argsort(flat[positive_order])[::-1]]
    removed = positive_order[:DROP_COUNT]
    retained = np.delete(flat, removed)
    full_mean = float(full_nll.mean())
    null_mean = float(null_nll.mean())
    relative_gain = float((null_mean - full_mean) / null_mean)
    source_delta = delta.mean(axis=1)
    quartet_delta = np.array([delta[:, 4*q:4*q+4].mean() for q in range(4)])
    gates = {
        "B0_G1": bool(flat.mean() > 0 and ci_low > 0),
        "B0_G2": bool(np.all(quartet_delta > 0)),
        "B0_G3": bool(np.sum(source_delta > 0) >= 14),
        "B0_G4": bool(trim_mean(flat, 0.2) > 0),
        "B0_G5": bool(retained.mean() > 0),
        "B0_G6": bool(relative_gain >= 0.10),
    }
    decision = ("JTD_B0_PASS_R4_ESTIMATOR_BRIDGE" if all(gates.values())
                else "JTD_B0_FAIL_R4_ESTIMATOR_NOT_RELIABLE")
    target_rows = []
    for source in range(N_SOURCE):
        for rep in range(N_REP):
            target_rows.append({"source_index": source+1, "source_id": source_ids[source],
                                "replicate": rep+1, "realization_id": realization_ids[source][rep],
                                "quartet": rep//4+1, "fold": rep%4+1,
                                "full_truth_nll": float(full_nll[source, rep]),
                                "shuffled_median_truth_nll": float(null_nll[source, rep]),
                                "delta_nll": float(delta[source, rep]),
                                "full_truth_rank": int(full_rank[source, rep]),
                                "shuffled_median_truth_rank": float(null_median_rank[source, rep]),
                                "full_top3": int(full_rank[source, rep] <= 3),
                                "shuffled_median_top3": float(null_median_rank[source, rep] <= 3)})
    write_csv(args.out / "JTD_B0_TARGETS.csv", target_rows)
    source_rows = [{"source_index": s+1, "source_id": source_ids[s],
                    "mean_delta_nll": float(source_delta[s]),
                    "positive": int(source_delta[s] > 0),
                    "full_mean_nll": float(full_nll[s].mean()),
                    "shuffled_median_mean_nll": float(null_nll[s].mean())} for s in range(N_SOURCE)]
    write_csv(args.out / "JTD_B0_SOURCES.csv", source_rows)
    quartet_rows = [{"quartet": q+1, "mean_delta_nll": float(quartet_delta[q]),
                     "positive": int(quartet_delta[q] > 0),
                     "full_mean_nll": float(full_nll[:, 4*q:4*q+4].mean()),
                     "shuffled_median_mean_nll": float(null_nll[:, 4*q:4*q+4].mean())} for q in range(4)]
    write_csv(args.out / "JTD_B0_QUARTETS.csv", quartet_rows)
    manifest = {"input_cache_sha256": sha(args.cache), "g0_audit_sha256": sha(args.g0_audit),
                "g0_commit": G0_COMMIT, "r0_commit": R0_COMMIT,
                "null_count_per_fold": N_NULL,
                "null_key": "JTD-B0|q={1..4}|fold={1..4}|null={0..199}|source={0..17}|block={2..5}",
                "null_bit_rule": "SHA256 ASCII digest first byte & 1; 0 -> [1,2,0], 1 -> [2,0,1]",
                "covariance": "pooled within-source OAS, assume_centered=False, jitter=1e-10*max(1,trace(cov)/10)",
                "pca": "raw ppm; training-only StandardScaler; full SVD PCA 2 per contiguous 2-time block",
                "bootstrap": {"draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED,
                              "method": "hierarchical paired source/target resampling"},
                "g5_drop_count": DROP_COUNT,
                "g5_rounding": "ceil(0.05*288)=15 largest positive deltas",
                "relative_gain_denominator": "mean of per-target shuffled-median truth NLL",
                "folds": fold_manifest,
                "runtime": {"python": sys.version, "platform": platform.platform(),
                            "numpy": np.__version__, "sklearn": sklearn.__version__,
                            "threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}}}
    write_json(args.out / "JTD_B0_NULL_PROVENANCE.json", manifest)
    result = {"decision": decision, "gates": gates, "n_sources": N_SOURCE, "n_realizations": N_REP,
              "n_targets": N_SOURCE*N_REP, "full_mean_nll": full_mean,
              "shuffled_target_median_mean_nll": null_mean,
              "mean_delta_nll": float(flat.mean()), "median_delta_nll": float(np.median(flat)),
              "trimmed_10_mean_delta_nll": float(trim_mean(flat, 0.1)),
              "trimmed_20_mean_delta_nll": float(trim_mean(flat, 0.2)),
              "relative_mean_nll_improvement": relative_gain,
              "bootstrap_95_ci": [ci_low, ci_high],
              "positive_source_count": int(np.sum(source_delta > 0)),
              "positive_target_fraction": float(np.mean(flat > 0)),
              "quartet_mean_deltas": quartet_delta.tolist(),
              "g5_removed_positive_targets": len(removed),
              "g5_retained_mean_delta_nll": float(retained.mean()),
              "full_mean_truth_rank": float(full_rank.mean()),
              "shuffled_median_mean_truth_rank": float(null_median_rank.mean()),
              "full_top3_fraction": float(np.mean(full_rank <= 3)),
              "shuffled_median_top3_fraction": float(np.mean(null_median_rank <= 3)),
              "no_new_plume": True, "no_e2_data": True, "no_dense_expansion": True}
    write_json(args.out / "JTD_B0_RESULT.json", result)
    files = sorted(p for p in args.out.iterdir() if p.is_file())
    (args.out / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.name}\n" for p in files), encoding="utf-8")
    print(decision)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
