#!/usr/bin/env python3
"""Frozen JTD-E1 FULL vs within-source marginal-preserving SHUFFLED gate."""
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

ROOT = Path(__file__).resolve().parents[2]
N_ENV, N_SOURCE, N_REF, N_TARGET, N_NULL, DIM = 3, 6, 4, 2, 200, 10


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True)+"\n").encode("utf-8"))


def write_csv(path: Path, values: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def fit_density(reference: np.ndarray) -> tuple[list[tuple[np.ndarray, np.ndarray, float]], list[float]]:
    models, shrinkage = [], []
    for source in range(N_SOURCE):
        fit = OAS(assume_centered=False, store_precision=False).fit(reference[source])
        covariance = fit.covariance_.copy()
        jitter = 1e-10*max(1.0, float(np.trace(covariance))/DIM)
        covariance.flat[::DIM+1] += jitter
        lower = np.linalg.cholesky(covariance)
        models.append((fit.location_.copy(), lower, float(np.log(np.diag(lower)).sum())))
        shrinkage.append(float(fit.shrinkage_))
    return models, shrinkage


def evaluate(models: list, targets: np.ndarray, truth: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    loglik = np.empty((len(targets), N_SOURCE), dtype=np.float64)
    for source, (mu, lower, half_logdet) in enumerate(models):
        projected = np.linalg.solve(lower, (targets-mu).T)
        loglik[:, source] = -0.5*(DIM*np.log(2*np.pi)+np.sum(projected**2, axis=0))-half_logdet
    peak = loglik.max(axis=1, keepdims=True)
    logpost = loglik-peak-np.log(np.exp(loglik-peak).sum(axis=1, keepdims=True))
    nll = -logpost[np.arange(len(truth)), truth]
    rank = 1+np.sum(loglik > loglik[np.arange(len(truth)), truth, None], axis=1)
    if not np.isfinite(nll).all():
        raise RuntimeError("E1 posterior numerical failure")
    return nll, rank, loglik


def source_cluster_bootstrap(delta: np.ndarray) -> np.ndarray:
    # Each of the 18 environment x source units carries both fresh targets.
    rng = np.random.default_rng(2026092502)
    draws = np.empty(5000)
    for i in range(5000):
        units = rng.integers(0, N_SOURCE, size=(N_ENV, N_SOURCE))
        draws[i] = delta[np.arange(N_ENV)[:, None], units, :].mean()
    return draws


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    if (out / "JTD_E1_RESULT.json").exists():
        raise RuntimeError("refuse existing E1 scientific result")
    lock_path = out / "JTD_E1_PRE_RUN_LOCK.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    for name, expected in lock["code_sha256"].items():
        if sha(ROOT / "research/jtd_cross_environment_v0" / name) != expected:
            raise RuntimeError(f"frozen E1 code hash drift: {name}")
    ref_path = out / "JTD_E1_REFERENCE_10x30.npy"
    target_path = out / "JTD_E1_FRESH_TARGETS_10x30.npy"
    perm_path = out / "JTD_E1_NULL_DERANGEMENTS.npy"
    acquisition = json.loads((out / "JTD_E1_TARGET_ACQUISITION.json").read_text(encoding="utf-8"))
    if acquisition["completed_new_plume_runs"] != 36 or acquisition["pre_run_lock_sha256"] != sha(lock_path):
        raise RuntimeError("fresh target acquisition incomplete/lock drift")
    if sha(ref_path) != lock["reference_snapshot_sha256"] or sha(perm_path) != lock["null_derangements_sha256"]:
        raise RuntimeError("frozen reference/null hash drift")
    if sha(target_path) != acquisition["target_vector_sha256"]:
        raise RuntimeError("fresh target vector hash drift")
    reference = np.load(ref_path, allow_pickle=False)
    targets = np.load(target_path, allow_pickle=False)
    permutations = np.load(perm_path, allow_pickle=False)
    if reference.shape != (3, 6, 4, 10, 30) or targets.shape != (3, 6, 2, 10, 30):
        raise RuntimeError("E1 observation tensor shape drift")
    if reference.dtype != np.float32 or targets.dtype != np.float32 or permutations.shape != (3, 200, 6, 4, 4):
        raise RuntimeError("E1 observation/null dtype or shape drift")
    with (out / "JTD_E1_TARGET_MANIFEST.tsv").open(newline="", encoding="utf-8") as stream:
        manifest = list(csv.DictReader(stream, delimiter="\t"))
    if len(manifest) != 36 or sha(out / "JTD_E1_TARGET_MANIFEST.tsv") != acquisition["manifest_sha256"]:
        raise RuntimeError("fresh target manifest drift")
    by_key = {(int(r["environment_index"]), int(r["source_index"]), int(r["target_replicate"])): r for r in manifest}
    if len(by_key) != 36:
        raise RuntimeError("fresh target duplicate/missing key")
    full_nll = np.empty((3, 6, 2))
    full_rank = np.empty((3, 6, 2), dtype=np.int16)
    full_loglik = np.empty((3, 12, 6))
    null_nll = np.empty((3, 200, 6, 2))
    null_rank = np.empty((3, 200, 6, 2), dtype=np.int16)
    null_loglik = np.empty((3, 200, 12, 6))
    model_provenance = []
    for ei in range(N_ENV):
        z_ref = np.empty((N_SOURCE, N_REF, DIM))
        z_target = np.empty((N_SOURCE, N_TARGET, DIM))
        pca_blocks = []
        for block in range(5):
            sl = slice(2*block, 2*block+2)
            raw_ref = reference[ei, :, :, sl, :].reshape(N_SOURCE*N_REF, 60)
            raw_target = targets[ei, :, :, sl, :].reshape(N_SOURCE*N_TARGET, 60)
            if np.count_nonzero(np.var(raw_ref, axis=0) > 0) < 2:
                raise RuntimeError("reference PCA block lacks two dimensions")
            scaler = StandardScaler().fit(raw_ref)
            pca = PCA(n_components=2, svd_solver="full").fit(scaler.transform(raw_ref))
            z_ref[:, :, 2*block:2*block+2] = pca.transform(scaler.transform(raw_ref)).reshape(N_SOURCE, N_REF, 2)
            z_target[:, :, 2*block:2*block+2] = pca.transform(scaler.transform(raw_target)).reshape(N_SOURCE, N_TARGET, 2)
            pca_blocks.append({"block": block+1, "explained_variance_ratio": pca.explained_variance_ratio_.tolist()})
        truth = np.repeat(np.arange(N_SOURCE), N_TARGET)
        flat_target = z_target.reshape(N_SOURCE*N_TARGET, DIM)
        full_models, shrinkage = fit_density(z_ref)
        nll, rank, loglik = evaluate(full_models, flat_target, truth)
        full_nll[ei], full_rank[ei], full_loglik[ei] = nll.reshape(6, 2), rank.reshape(6, 2), loglik
        for null_id in range(N_NULL):
            shuffled = z_ref.copy()
            for source in range(N_SOURCE):
                for block in range(1, 5):
                    perm = permutations[ei, null_id, source, block-1]
                    if sorted(perm.tolist()) != [0, 1, 2, 3] or np.any(perm == np.arange(4)):
                        raise RuntimeError("frozen null derangement invalid")
                    sl = slice(2*block, 2*block+2)
                    shuffled[source, :, sl] = z_ref[source, perm, sl]
                    if not np.array_equal(np.sort(shuffled[source, :, sl], axis=0),
                                          np.sort(z_ref[source, :, sl], axis=0)):
                        raise RuntimeError("null block marginal changed")
            if not np.allclose(shuffled.mean(axis=1), z_ref.mean(axis=1), atol=1e-12, rtol=0):
                raise RuntimeError("null source mean changed")
            models, _ = fit_density(shuffled)
            nll, rank, loglik = evaluate(models, flat_target, truth)
            null_nll[ei, null_id], null_rank[ei, null_id], null_loglik[ei, null_id] = (
                nll.reshape(6, 2), rank.reshape(6, 2), loglik)
        model_provenance.append({"environment_index": ei, "reference_count": 24,
                                 "target_count": 12, "full_oas_shrinkage_by_source": shrinkage,
                                 "pca_blocks": pca_blocks})
        print("JTD_E1_SCORED_ENVIRONMENT", ei, flush=True)
    np.savez_compressed(out / "JTD_E1_RAW_SCORES.npz", full_nll=full_nll,
                        full_rank=full_rank, full_loglik=full_loglik,
                        null_nll=null_nll, null_rank=null_rank, null_loglik=null_loglik)
    null_median = np.median(null_nll, axis=1)
    null_rank_median = np.median(null_rank, axis=1)
    delta = null_median-full_nll
    target_rows, source_rows, env_rows = [], [], []
    for ei in range(3):
        for source in range(6):
            unit = delta[ei, source]
            group = lock["reference_groups"][ei*6+source]
            for target in range(2):
                run = by_key[(ei, source, target)]
                if run["source_id"] != group["source_id"] or int(run["requested_seed"]) != 2026120000+1000*ei+10*source+target:
                    raise RuntimeError("fresh target seed/source label drift")
                target_rows.append({"environment_index": ei, "house": group["house"], "wind": group["wind"],
                                    "source_index": source, "source_id": group["source_id"],
                                    "target_replicate": target, "requested_seed": run["requested_seed"],
                                    "cube_sha256": run["cube_sha256"],
                                    "full_truth_nll": float(full_nll[ei, source, target]),
                                    "shuffled_median_truth_nll": float(null_median[ei, source, target]),
                                    "delta_nll": float(unit[target]),
                                    "full_truth_rank": int(full_rank[ei, source, target]),
                                    "shuffled_median_truth_rank": float(null_rank_median[ei, source, target]),
                                    "full_top3": int(full_rank[ei, source, target] <= 3),
                                    "shuffled_median_top3": int(null_rank_median[ei, source, target] <= 3)})
            source_rows.append({"environment_index": ei, "house": group["house"], "wind": group["wind"],
                                "source_index": source, "source_id": group["source_id"],
                                "mean_delta_nll": float(unit.mean()), "positive": int(unit.mean() > 0),
                                "full_mean_nll": float(full_nll[ei, source].mean()),
                                "shuffled_median_mean_nll": float(null_median[ei, source].mean())})
        env_rows.append({"environment_index": ei, "house": lock["winds"][ei]["house"],
                         "wind": lock["winds"][ei]["wind"],
                         "mean_delta_nll": float(delta[ei].mean()),
                         "median_delta_nll": float(np.median(delta[ei])),
                         "trimmed_20_mean_delta_nll": float(trim_mean(delta[ei].ravel(), 0.2)),
                         "positive_source_count": int(np.sum(delta[ei].mean(axis=1) > 0)),
                         "positive_target_fraction": float(np.mean(delta[ei] > 0)),
                         "full_mean_nll": float(full_nll[ei].mean()),
                         "shuffled_median_mean_nll": float(null_median[ei].mean()),
                         "relative_mean_nll_improvement": float((null_median[ei].mean()-full_nll[ei].mean())/null_median[ei].mean()),
                         "full_mean_truth_rank": float(full_rank[ei].mean()),
                         "shuffled_median_mean_truth_rank": float(null_rank_median[ei].mean()),
                         "full_top3_fraction": float(np.mean(full_rank[ei] <= 3)),
                         "shuffled_median_top3_fraction": float(np.mean(null_rank_median[ei] <= 3))})
    write_csv(out / "JTD_E1_TARGETS.csv", target_rows)
    write_csv(out / "JTD_E1_ENVIRONMENT_SOURCES.csv", source_rows)
    write_csv(out / "JTD_E1_ENVIRONMENTS.csv", env_rows)
    boot = source_cluster_bootstrap(delta)
    with (out / "JTD_E1_BOOTSTRAP_5000.npy").open("wb") as stream:
        np.save(stream, boot, allow_pickle=False)
    ci = np.quantile(boot, (0.025, 0.975))
    flat = delta.ravel()
    positive = np.flatnonzero(flat > 0)
    positive = positive[np.argsort(flat[positive])[::-1]]
    removed = positive[:2]
    remaining = np.delete(flat, removed)
    local_positive = [int(np.sum(delta[ei].mean(axis=1) > 0)) for ei in range(3)]
    env_mean = [float(delta[ei].mean()) for ei in range(3)]
    env_full = [float(full_nll[ei].mean()) for ei in range(3)]
    env_null = [float(null_median[ei].mean()) for ei in range(3)]
    relative = float((null_median.mean()-full_nll.mean())/null_median.mean())
    gates = {"E1_G1": bool(all(v > 0 for v in env_mean)),
             "E1_G2": bool(ci[0] > 0),
             "E1_G3": bool(sum(local_positive) >= 13 and all(v >= 4 for v in local_positive)),
             "E1_G4": bool(trim_mean(flat, 0.2) > 0),
             "E1_G5": bool(remaining.mean() > 0),
             "E1_G6": bool(relative >= 0.10),
             "E1_G7": bool(all(env_full[e] <= 1.10*env_null[e] for e in range(3)))}
    local_failure = [e for e in range(3) if not (env_mean[e] > 0 and local_positive[e] >= 4)]
    if all(gates.values()):
        decision = "JTD_E1_GO_CROSS_ENVIRONMENT_TEMPORAL_DEPENDENCE"
    elif all(gates[g] for g in ("E1_G2", "E1_G4", "E1_G5", "E1_G7")) and len(local_failure) == 1:
        decision = "JTD_E1_HOLD_ENVIRONMENT_HETEROGENEOUS_SIGNAL"
    else:
        decision = "JTD_E1_STOP_TEMPORAL_DEPENDENCE_NOT_GENERAL"
    write_json(out / "JTD_E1_RESULT.json", {
        "decision": decision, "gates": gates, "n_environments": 3, "n_sources_per_environment": 6,
        "reference_realizations_per_source": 4, "fresh_targets_per_source": 2,
        "new_plume_runs": 36, "pooled_mean_delta_nll": float(flat.mean()),
        "pooled_median_delta_nll": float(np.median(flat)),
        "pooled_trimmed_20_mean_delta_nll": float(trim_mean(flat, 0.2)),
        "pooled_relative_mean_nll_improvement": relative,
        "cluster_bootstrap_95_ci": ci.tolist(),
        "positive_environment_source_units": int(sum(local_positive)),
        "positive_sources_by_environment": local_positive,
        "positive_target_fraction": float(np.mean(flat > 0)),
        "environment_mean_deltas": env_mean,
        "environment_full_mean_nll": env_full,
        "environment_shuffled_median_mean_nll": env_null,
        "g5_removed_positive_target_count": len(removed),
        "g5_retained_mean_delta_nll": float(remaining.mean()),
        "largest_positive_target_delta_nll": float(np.max(flat)),
        "largest_negative_target_delta_nll": float(np.min(flat)),
        "full_mean_truth_rank": float(full_rank.mean()),
        "shuffled_median_mean_truth_rank": float(null_rank_median.mean()),
        "full_top3_fraction": float(np.mean(full_rank <= 3)),
        "shuffled_median_top3_fraction": float(np.mean(null_rank_median <= 3)),
        "local_environment_failures": local_failure,
        "pre_run_lock_sha256": sha(lock_path), "reference_sha256": sha(ref_path),
        "target_sha256": sha(target_path), "null_derangements_sha256": sha(perm_path),
        "raw_scores_sha256": sha(out / "JTD_E1_RAW_SCORES.npz"),
        "sealed_data_read": False, "dense_expansion": False, "closed_loop": False})
    write_json(out / "JTD_E1_MODEL_PROVENANCE.json", {
        "model": "G0/B1 source-specific sklearn OAS on 10D reference-only PCA",
        "reference_only_fit": True, "null_count_per_environment": 200,
        "null_median_per_target": True, "bootstrap_draws": 5000,
        "bootstrap_seed": 2026092502, "g5_removed_count": 2,
        "environment_models": model_provenance,
        "runtime": {"python": sys.version, "platform": platform.platform(),
                    "numpy": np.__version__, "sklearn": sklearn.__version__,
                    "threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}}})
    print(decision)


if __name__ == "__main__":
    main()
