#!/usr/bin/env python3
"""Frozen JTD-B1 G0-faithful source-specific OAS reference-depth audit."""
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
from scipy.stats import trim_mean
from sklearn.covariance import OAS
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

N_SOURCE, N_REP, N_NULL, DIM = 18, 16, 200, 10
DEPTHS = (3, 4, 6, 8, 10, 12)
FOLDS = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15))
LOCK_SHA = "12be883cb09fd387f9e0effc8cb0cb65b423be66a4ff1b34c3ea81648d9cf200"
CANONICAL_SHA = "7b231e88d78ca0742d9406e3673e242f8133eff543bcd0bb0c0f5363b15fe302"
G0_BASE_SEED, BOOTSTRAP_SEED, BOOTSTRAP_DRAWS = 2026092501, 2026092502, 5000
G0_COMMIT = "170d0ccddc559c97744af5409ec1e3642bcfa743"
R0_COMMIT = "e527beea07c33cdbc362d156545409245f029968"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fit_density(reference: np.ndarray) -> tuple[list[tuple[np.ndarray, np.ndarray, float]], list[float]]:
    # Same source-specific sklearn OAS, mean and jitter rule as G0.
    models, shrinkage = [], []
    for source in range(N_SOURCE):
        fit = OAS(assume_centered=False, store_precision=False).fit(reference[source])
        covariance = fit.covariance_.copy()
        jitter = 1e-10 * max(1.0, float(np.trace(covariance)) / covariance.shape[0])
        covariance.flat[::covariance.shape[0] + 1] += jitter
        lower = np.linalg.cholesky(covariance)
        models.append((fit.location_.copy(), lower, float(np.log(np.diag(lower)).sum())))
        shrinkage.append(float(fit.shrinkage_))
    return models, shrinkage


def evaluate(models: list, targets: np.ndarray, truth: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    loglik = np.empty((len(targets), N_SOURCE), dtype=np.float64)
    for source, (mu, lower, half_logdet) in enumerate(models):
        projected = np.linalg.solve(lower, (targets - mu).T)
        loglik[:, source] = -0.5 * (DIM * np.log(2*np.pi) + np.sum(projected**2, axis=0)) - half_logdet
    peak = loglik.max(axis=1, keepdims=True)
    logden = peak + np.log(np.exp(loglik - peak).sum(axis=1, keepdims=True))
    nll = -(loglik - logden)[np.arange(len(truth)), truth]
    rank = 1 + np.sum(loglik > loglik[np.arange(len(truth)), truth, None], axis=1)
    if not np.isfinite(nll).all():
        raise ValueError("nonfinite posterior NLL")
    return nll, rank


def derangement(seed: int, depth: int) -> np.ndarray:
    # Exact G0 rejection sampler; K=12 uses G0 seeds verbatim.
    rng = np.random.default_rng(seed)
    identity = np.arange(depth)
    for _ in range(1000):
        perm = rng.permutation(depth)
        if np.all(perm != identity):
            return perm.astype(np.uint8)
    raise RuntimeError(f"derangement failure: {seed}")


def null_seed(depth: int, subpanel: int, fold: int, null_id: int,
              source: int, block: int) -> int:
    g0 = G0_BASE_SEED + 100000*fold + 1000*null_id + 10*source + block
    return g0 if depth == 12 else g0 + 10_000_000*depth + 1_000_000*subpanel


def bootstrap(delta: np.ndarray) -> tuple[float, float]:
    # Shape: source x unique target realization x subpanel. Sample source,
    # then original target realization; keep repeated subpanels as a cluster.
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = np.empty(BOOTSTRAP_DRAWS)
    for draw in range(BOOTSTRAP_DRAWS):
        source = rng.integers(0, N_SOURCE, N_SOURCE)
        target = rng.integers(0, N_REP, (N_SOURCE, N_REP))
        means[draw] = delta[source[:, None], target].mean()
    return tuple(float(v) for v in np.quantile(means, (0.025, 0.975)))


def read_g0_csv(full_path: Path, null_path: Path) -> tuple[np.ndarray, np.ndarray]:
    full = np.full((N_SOURCE, N_REP), np.nan)
    null = np.full((N_NULL, N_SOURCE, N_REP), np.nan)
    with full_path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            full[int(row["source_index"]), int(row["realization_index"])] = float(row["nll"])
    with null_path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            null[int(row["shuffle"]), int(row["source_index"]), int(row["realization_index"])] = float(row["nll"])
    if not np.isfinite(full).all() or not np.isfinite(null).all():
        raise ValueError("G0 parity evidence incomplete")
    return full, null


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--g0-audit", type=Path, required=True)
    parser.add_argument("--subpanel-lock", type=Path, required=True)
    parser.add_argument("--g0-full-csv", type=Path, required=True)
    parser.add_argument("--g0-null-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if (args.out / "JTD_B1_RESULT.json").exists() or (args.out / "panels").exists():
        raise ValueError("refuse existing B1 score output")
    audit = json.loads(args.g0_audit.read_text(encoding="utf-8"))
    if not audit.get("input_contract_pass") or not audit.get("all_288_raw_cube_reextractions_exact"):
        raise ValueError("G0 R0 raw input audit not PASS")
    if audit["base_commit"] != R0_COMMIT or audit["canonical_cache_sha256"] != CANONICAL_SHA:
        raise ValueError("R0/G0 input provenance drift")
    if sha(args.cache) != CANONICAL_SHA or sha(args.subpanel_lock) != LOCK_SHA:
        raise ValueError("canonical cache or preregistered subpanel lock SHA drift")
    lock = json.loads(args.subpanel_lock.read_text(encoding="utf-8"))
    if tuple(lock["depths"]) != DEPTHS or len(lock["panels"]) != 64:
        raise ValueError("subpanel lock shape drift")
    with np.load(args.cache, allow_pickle=False) as loaded:
        x = loaded["X"].copy()
        source_ids = loaded["source_ids"].tolist()
        realization_ids = loaded["realization_ids"].tolist()
        if str(loaded["observable_name"]) != "raw_ppm_2x2_pooled_mean":
            raise ValueError("input observable drift")
    if x.shape != (N_SOURCE, N_REP, 10, 30) or not np.isfinite(x).all():
        raise ValueError("canonical R0 tensor invalid")
    g0_full, g0_null = read_g0_csv(args.g0_full_csv, args.g0_null_csv)
    target_rows, panel_rows, panel_provenance = [], [], []
    k12_full = np.full((N_SOURCE, N_REP), np.nan)
    k12_null = np.full((N_NULL, N_SOURCE, N_REP), np.nan)
    for item in lock["panels"]:
        fi, depth, subpanel = item["fold"], item["depth"], item["subpanel"]
        eval_ix, ref_ix = item["targets_zero_based"], item["references_zero_based"]
        if eval_ix != list(FOLDS[fi]) or len(ref_ix) != depth or set(eval_ix) & set(ref_ix):
            raise ValueError("subpanel lock evaluation/reference mismatch")
        z = np.empty((N_SOURCE, N_REP, DIM), dtype=np.float64)
        block_variance = []
        for block in range(5):
            t0, t1 = 2*block, 2*block+1
            raw = x[:, :, [t0, t1], :].reshape(N_SOURCE, N_REP, 60)
            training = raw[:, ref_ix].reshape(N_SOURCE*depth, 60)
            if np.count_nonzero(np.var(training, axis=0) > 0) < 2:
                raise ValueError(f"PCA lacks two nonzero features: F{fi} K{depth} P{subpanel} B{block}")
            scaler = StandardScaler().fit(training)
            standardized = scaler.transform(raw.reshape(N_SOURCE*N_REP, 60))
            pca = PCA(n_components=2, svd_solver="full").fit(scaler.transform(training))
            z[:, :, 2*block:2*block+2] = pca.transform(standardized).reshape(N_SOURCE, N_REP, 2)
            block_variance.append(pca.explained_variance_ratio_.tolist())
        reference = z[:, ref_ix]
        targets = z[:, eval_ix].reshape(N_SOURCE*4, DIM)
        truth = np.repeat(np.arange(N_SOURCE), 4)
        full_model, shrinkages = fit_density(reference)
        full_nll, full_rank = evaluate(full_model, targets, truth)
        null_nll = np.empty((N_NULL, N_SOURCE*4))
        null_rank = np.empty((N_NULL, N_SOURCE*4), dtype=np.uint8)
        perm_hasher = hashlib.sha256()
        for mi in range(N_NULL):
            shuffled = reference.copy()
            for source in range(N_SOURCE):
                for block in range(1, 5):
                    seed = null_seed(depth, subpanel, fi, mi, source, block)
                    perm = derangement(seed, depth)
                    perm_hasher.update(seed.to_bytes(8, "little"))
                    perm_hasher.update(perm.tobytes())
                    sl = slice(2*block, 2*block+2)
                    shuffled[source, :, sl] = reference[source, perm, sl]
                    if not np.array_equal(np.sort(shuffled[source, :, sl], axis=0),
                                          np.sort(reference[source, :, sl], axis=0)):
                        raise ValueError("SHUFFLED block marginal changed")
            if not np.allclose(shuffled.mean(axis=1), reference.mean(axis=1), atol=1e-12, rtol=0):
                raise ValueError("SHUFFLED source mean changed")
            null_model, _ = fit_density(shuffled)
            null_nll[mi], null_rank[mi] = evaluate(null_model, targets, truth)
        null_median = np.median(null_nll, axis=0)
        null_rank_median = np.median(null_rank, axis=0)
        panel_delta = null_median-full_nll
        path = args.out / "panels" / f"F{fi}_K{depth:02d}_P{subpanel}.npz"
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, full_nll=full_nll.reshape(N_SOURCE, 4),
                            full_rank=full_rank.reshape(N_SOURCE, 4),
                            null_nll=null_nll.reshape(N_NULL, N_SOURCE, 4),
                            null_rank=null_rank.reshape(N_NULL, N_SOURCE, 4))
        for source in range(N_SOURCE):
            for pos, rep in enumerate(eval_ix):
                target_rows.append({"depth": depth, "fold": fi, "subpanel": subpanel,
                                    "source_index": source, "source_id": source_ids[source],
                                    "realization_index": rep, "realization_id": realization_ids[source][rep],
                                    "full_truth_nll": float(full_nll[4*source+pos]),
                                    "shuffled_median_truth_nll": float(null_median[4*source+pos]),
                                    "delta_nll": float(panel_delta[4*source+pos]),
                                    "full_truth_rank": int(full_rank[4*source+pos]),
                                    "shuffled_median_truth_rank": float(null_rank_median[4*source+pos]),
                                    "full_top3": int(full_rank[4*source+pos] <= 3),
                                    "shuffled_median_top3": int(null_rank_median[4*source+pos] <= 3)})
        panel_rows.append({"depth": depth, "fold": fi, "subpanel": subpanel,
                           "reference_replicates_zero_based": ",".join(map(str, ref_ix)),
                           "target_replicates_zero_based": ",".join(map(str, eval_ix)),
                           "mean_delta_nll": float(panel_delta.mean()),
                           "full_mean_nll": float(full_nll.mean()),
                           "shuffled_target_median_mean_nll": float(null_median.mean()),
                           "positive": int(panel_delta.mean() > 0)})
        panel_provenance.append({"depth": depth, "fold": fi, "subpanel": subpanel,
                                 "panel_scores_sha256": sha(path),
                                 "permutation_seed_digest": perm_hasher.hexdigest(),
                                 "full_oas_shrinkage_by_source": shrinkages,
                                 "pca_explained_variance_by_block": block_variance})
        if depth == 12:
            for source in range(N_SOURCE):
                for pos, rep in enumerate(eval_ix):
                    k12_full[source, rep] = full_nll[4*source+pos]
                    k12_null[:, source, rep] = null_nll[:, 4*source+pos]
        print(f"F{fi} K{depth} P{subpanel} complete", flush=True)
    if not np.isfinite(k12_full).all() or not np.isfinite(k12_null).all():
        raise ValueError("K12 parity arrays incomplete")
    full_maxdiff = float(np.max(np.abs(k12_full-g0_full)))
    null_maxdiff = float(np.max(np.abs(k12_null-g0_null)))
    k12_parity = bool(np.allclose(k12_full, g0_full, atol=1e-6, rtol=1e-8)
                      and np.allclose(k12_null, g0_null, atol=1e-6, rtol=1e-8))
    write_csv(args.out / "JTD_B1_TARGETS.csv", target_rows)
    write_csv(args.out / "JTD_B1_FOLD_SUBPANELS.csv", panel_rows)
    write_json(args.out / "JTD_B1_PANEL_PROVENANCE.json", panel_provenance)
    depth_rows, source_rows, depth_result = [], [], {}
    for depth in DEPTHS:
        subset = [r for r in target_rows if r["depth"] == depth]
        panels = [r for r in panel_rows if r["depth"] == depth]
        n_panel = 1 if depth == 12 else 3
        delta = np.full((N_SOURCE, N_REP, n_panel), np.nan)
        full = np.full_like(delta, np.nan)
        null = np.full_like(delta, np.nan)
        ranks = np.full_like(delta, np.nan)
        top3 = np.full_like(delta, np.nan)
        for row in subset:
            s, r, p = row["source_index"], row["realization_index"], row["subpanel"]
            delta[s, r, p] = row["delta_nll"]
            full[s, r, p] = row["full_truth_nll"]
            null[s, r, p] = row["shuffled_median_truth_nll"]
            ranks[s, r, p] = row["full_truth_rank"]
            top3[s, r, p] = row["full_top3"]
        if any(not np.isfinite(a).all() for a in (delta, full, null, ranks, top3)):
            raise ValueError(f"incomplete target matrix: K{depth}")
        flat = delta.ravel()
        ci_low, ci_high = bootstrap(delta)
        positive = np.flatnonzero(flat > 0)
        positive = positive[np.argsort(flat[positive])[::-1]]
        drop_count = math.ceil(0.05*len(flat))
        retained = np.delete(flat, positive[:drop_count])
        relative = float((null.mean()-full.mean())/null.mean())
        source_means = delta.mean(axis=(1, 2))
        panel_min = float(min(p["mean_delta_nll"] for p in panels))
        gates = {"R1": bool(ci_low > 0),
                 "R2": bool(all(p["mean_delta_nll"] > 0 for p in panels)),
                 "R3": bool(np.sum(source_means > 0) >= 14),
                 "R4": bool(trim_mean(flat, 0.2) > 0),
                 "R5": bool(retained.mean() > 0),
                 "R6": bool(relative >= 0.10)}
        reliable = bool(all(gates.values()))
        record = {"depth": depth, "reliable": reliable, "gates": gates,
                  "n_fold_subpanels": len(panels), "n_target_panel_rows": len(subset),
                  "mean_delta_nll": float(flat.mean()),
                  "median_delta_nll": float(np.median(flat)),
                  "trimmed_20_mean_delta_nll": float(trim_mean(flat, 0.2)),
                  "bootstrap_95_ci": [ci_low, ci_high],
                  "relative_mean_nll_improvement": relative,
                  "positive_source_count": int(np.sum(source_means > 0)),
                  "positive_target_fraction": float(np.mean(flat > 0)),
                  "minimum_fold_subpanel_mean_delta_nll": panel_min,
                  "g5_drop_count": int(min(drop_count, len(positive))),
                  "g5_retained_mean_delta_nll": float(retained.mean()),
                  "full_mean_nll": float(full.mean()),
                  "full_truth_nll_p95": float(np.quantile(full, 0.95)),
                  "full_truth_nll_p99": float(np.quantile(full, 0.99)),
                  "shuffled_target_median_mean_nll": float(null.mean()),
                  "full_mean_truth_rank": float(ranks.mean()),
                  "full_top3_fraction": float(top3.mean())}
        depth_result[str(depth)] = record
        depth_rows.append({k: (json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v)
                           for k, v in record.items()})
        for source in range(N_SOURCE):
            source_rows.append({"depth": depth, "source_index": source,
                                "source_id": source_ids[source],
                                "mean_delta_nll": float(source_means[source]),
                                "positive": int(source_means[source] > 0),
                                "full_mean_nll": float(full[source].mean()),
                                "shuffled_target_median_mean_nll": float(null[source].mean())})
    write_csv(args.out / "JTD_B1_DEPTH_SUMMARY.csv", depth_rows)
    write_csv(args.out / "JTD_B1_SOURCES_BY_DEPTH.csv", source_rows)
    reliable_depths = [k for k in DEPTHS if depth_result[str(k)]["reliable"]]
    k_min = min(reliable_depths) if reliable_depths else None
    if not k12_parity or not depth_result["12"]["reliable"]:
        decision = "JTD_B1_FAIL_IMPLEMENTATION_OR_CONTRACT_DRIFT"
    elif k_min is not None and k_min <= 10:
        decision = "JTD_B1_PASS_REFERENCE_DEPTH_IDENTIFIED"
    else:
        decision = "JTD_B1_HOLD_REQUIRES_G0_DEPTH"
    result = {"decision": decision, "K_min": k_min, "reliable_depths": reliable_depths,
              "depths": depth_result, "k12_g0_parity": {"pass": k12_parity,
                  "full_nll_max_abs_diff": full_maxdiff, "null_nll_max_abs_diff": null_maxdiff,
                  "tolerance": "atol=1e-6, rtol=1e-8"},
              "n_sources": N_SOURCE, "n_realizations_per_source": N_REP,
              "new_plume_runs": 0, "e2_data_read": False, "sealed_data_read": False,
              "dense_expansion": False, "closed_loop": False,
              "g0_commit": G0_COMMIT, "r0_commit": R0_COMMIT,
              "input_cache_sha256": sha(args.cache),
              "subpanel_lock_sha256": sha(args.subpanel_lock),
              "g0_full_csv_sha256": sha(args.g0_full_csv),
              "g0_null_csv_sha256": sha(args.g0_null_csv)}
    write_json(args.out / "JTD_B1_RESULT.json", result)
    write_json(args.out / "JTD_B1_METHOD_PROVENANCE.json", {
        "source_model": "per-source sklearn OAS(assume_centered=False), G0 jitter and uniform-prior posterior",
        "pca": "per-panel training-only StandardScaler + PCA(n_components=2,svd_solver='full') per 2-time raw-ppm block",
        "null": "G0 rejection-sampled within-source derangement for blocks 2-5; anchor block 1 fixed",
        "null_count_per_fold_subpanel": N_NULL,
        "null_seed_rule": "G0 base+100000*fold+1000*null+10*source+block; for K<12 add 10000000*K+1000000*subpanel; K12 exact G0 seeds",
        "bootstrap": "5000 paired hierarchical draws, seed 2026092502; resample sources and unique target realizations, retain all subpanel repetitions as cluster",
        "g5": "remove ceil(5% of target-panel rows) largest strictly positive deltas",
        "relative_gain_denominator": "mean of target-level shuffled-median truth NLL",
        "runtime": {"python": sys.version, "platform": platform.platform(),
                    "numpy": np.__version__, "sklearn": sklearn.__version__,
                    "threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}}})
    files = sorted(p for p in args.out.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    (args.out / "SHA256SUMS").write_bytes("".join(
        f"{sha(p)}  {p.relative_to(args.out).as_posix()}\n" for p in files).encode("ascii"))
    print(decision, "K_min", k_min)


if __name__ == "__main__":
    main()
