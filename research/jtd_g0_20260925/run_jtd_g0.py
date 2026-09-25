#!/usr/bin/env python3
"""Frozen JTD-G0 FULL versus marginal-preserving SHUFFLED null."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sklearn
import yaml
from sklearn.covariance import OAS
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


BASE = "e527beea07c33cdbc362d156545409245f029968"
FOLDS = ([0, 4, 8, 12], [1, 5, 9, 13], [2, 6, 10, 14], [3, 7, 11, 15])
BLOCKS = ((0, 1), (2, 3), (4, 5), (6, 7), (8, 9))
N_SOURCE, N_REP, N_SHUFFLE, DIM = 18, 16, 200, 10
JITTER = 1e-10


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, records: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def fit_density(reference: np.ndarray, diagonal: bool = False) -> list[tuple[np.ndarray, np.ndarray, float, float]]:
    models = []
    for source in range(N_SOURCE):
        fit = OAS(assume_centered=False, store_precision=False).fit(reference[source])
        covariance = fit.covariance_.copy()
        if diagonal:
            covariance = np.diag(np.diag(covariance))
        jitter = JITTER * max(1.0, float(np.trace(covariance)) / covariance.shape[0])
        covariance.flat[::covariance.shape[0] + 1] += jitter
        lower = np.linalg.cholesky(covariance)
        models.append((fit.location_.copy(), lower, float(np.log(np.diag(lower)).sum()), float(fit.shrinkage_)))
    return models


def log_likelihood(models: list, targets: np.ndarray) -> np.ndarray:
    output = np.empty((len(targets), N_SOURCE), dtype=np.float64)
    d = targets.shape[1]
    for source, (mu, lower, half_logdet, _) in enumerate(models):
        projected = np.linalg.solve(lower, (targets - mu).T)
        output[:, source] = -0.5 * (d * np.log(2 * np.pi) + np.sum(projected ** 2, axis=0)) - half_logdet
    return output


def block_product_likelihood(reference: np.ndarray, targets: np.ndarray) -> np.ndarray:
    out = np.zeros((len(targets), N_SOURCE), dtype=np.float64)
    for block in range(5):
        sl = slice(2 * block, 2 * block + 2)
        out += log_likelihood(fit_density(reference[:, :, sl]), targets[:, sl])
    return out


def evaluate(loglik: np.ndarray, truth: np.ndarray, coordinates: np.ndarray) -> dict[str, np.ndarray]:
    peak = loglik.max(axis=1, keepdims=True)
    logden = peak + np.log(np.exp(loglik - peak).sum(axis=1, keepdims=True))
    logpost = loglik - logden
    target = np.arange(len(truth))
    rank = 1 + np.sum(loglik > loglik[target, truth, None], axis=1)
    map_source = np.argmax(loglik, axis=1)
    data = {"nll": -logpost[target, truth], "posterior_true": np.exp(logpost[target, truth]),
            "rank": rank, "top1": rank == 1, "top3": rank <= 3,
            "map_source": map_source,
            "map_error_m": np.linalg.norm(coordinates[map_source] - coordinates[truth], axis=1)}
    if not np.isfinite(data["nll"]).all():
        raise RuntimeError("posterior numerical failure")
    return data


def derangement(seed: int, n: int = 12) -> np.ndarray:
    rng = np.random.default_rng(seed)
    identity = np.arange(n)
    for _ in range(1000):
        p = rng.permutation(n)
        if np.all(p != identity):
            return p.astype(np.uint8)
    raise RuntimeError(f"derangement generation failure: {seed}")


def bootstrap_ci(delta: np.ndarray, draws: int, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    means = np.empty(draws)
    for i in range(draws):
        s = rng.integers(0, N_SOURCE, size=N_SOURCE)
        r = rng.integers(0, N_REP, size=(N_SOURCE, N_REP))
        means[i] = delta[s[:, None], r].mean()
    return tuple(float(x) for x in np.quantile(means, [0.025, 0.975]))


def figure(path: Path, kind: str, data: np.ndarray, other: np.ndarray | None = None) -> None:
    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=160)
    if kind == "null":
        ax.hist(data, bins=25, color="#6c8ebf")
        ax.axvline(float(other[0]), color="#b23a48", lw=2, label="FULL")
        ax.set_xlabel("Mean held-out truth-source NLL")
        ax.legend()
    elif kind == "source":
        ax.bar(np.arange(1, N_SOURCE + 1), data, color="#537895")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xlabel("Frozen R0 source index")
        ax.set_ylabel("Paired delta NLL")
    elif kind == "fold":
        ax.bar(np.arange(4), data, color="#537895")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(np.arange(4), [f"F{i}" for i in range(4)])
        ax.set_ylabel("Paired delta NLL")
    else:
        ax.bar([0, 1], [float(data[0]), float(other[0])], color=["#b23a48", "#6c8ebf"])
        ax.set_xticks([0, 1], ["FULL", "SHUFFLED median"])
        ax.set_ylabel("Median truth rank")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root, out = args.repo, args.out
    frozen = root / "research/jtd_g0_20260925/frozen_package"
    config_path = frozen / "config/jtd_g0_frozen.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config["base"]["commit"] == BASE
    assert config["representation"]["n_blocks"] == 5 and config["representation"]["pca_components_per_block"] == 2
    assert config["null"]["n_shuffles"] == N_SHUFFLE and config["null"]["anchor_block"] == 0
    assert config["cv"]["folds"] == {f"F{i}": fold for i, fold in enumerate(FOLDS)}
    audit_path = out / "audit/R0_INPUT_AUDIT.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if not audit["input_contract_pass"] or audit["base_commit"] != BASE:
        raise RuntimeError("A0 input contract is not PASS")
    cache = out / "cache/canonical_r0.npz"
    if sha(cache) != audit["canonical_cache_sha256"]:
        raise RuntimeError("canonical R0 cache hash drift")
    with np.load(cache, allow_pickle=False) as z:
        x = z["X"].copy()
        ids = z["source_ids"].tolist()
        xy = z["source_xy"].copy()
        realization_ids = z["realization_ids"].tolist()
        assert str(z["observable_name"]) == "raw_ppm_2x2_pooled_mean"
        assert str(z["base_commit"]) == BASE
    if x.shape != (N_SOURCE, N_REP, 10, 30):
        raise RuntimeError("canonical shape drift")
    for name in ("config", "metrics", "models", "figures", "logs"):
        (out / name).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_path, out / "config/frozen_config.yaml")
    write_json(out / "config/folds.json", {f"F{i}": {"eval": fold, "reference": [r for r in range(16) if r not in fold]}
                                                 for i, fold in enumerate(FOLDS)})
    full = {k: np.empty((N_SOURCE, N_REP), dtype=np.float64 if k in ("nll", "posterior_true", "map_error_m") else np.int16)
            for k in ("nll", "posterior_true", "rank", "top1", "top3", "map_source", "map_error_m")}
    null = {k: np.empty((N_SHUFFLE, N_SOURCE, N_REP), dtype=np.float64 if k in ("nll", "posterior_true", "map_error_m") else np.int16)
            for k in full}
    control = {name: {k: np.empty((N_SOURCE, N_REP), dtype=np.float64 if k == "nll" else np.int16)
                      for k in ("nll", "rank", "top3")}
               for name in ("DIAG-COV", "BLOCK-PRODUCT")}
    seed_matrix = np.empty((4, N_SHUFFLE, N_SOURCE, 4), dtype=np.int64)
    permutations = np.empty((4, N_SHUFFLE, N_SOURCE, 4, 12), dtype=np.uint8)
    pca_manifest, model_manifest = [], []
    pca_means = np.empty((4, 5, 60)); pca_scales = np.empty((4, 5, 60)); pca_components = np.empty((4, 5, 2, 60))
    ref_ix_all = []
    for fi, eval_ix in enumerate(FOLDS):
        ref_ix = [r for r in range(N_REP) if r not in eval_ix]
        ref_ix_all.append(ref_ix)
        z = np.empty((N_SOURCE, N_REP, DIM), dtype=np.float64)
        for block, (t0, t1) in enumerate(BLOCKS):
            raw = x[:, :, [t0, t1], :].reshape(N_SOURCE, N_REP, 60)
            training = raw[:, ref_ix].reshape(N_SOURCE * 12, 60)
            if np.count_nonzero(np.var(training, axis=0) > 0) < 2:
                raise RuntimeError(f"fewer than two nonzero-variance features: F{fi} block{block}")
            scaler = StandardScaler().fit(training)
            standardized = scaler.transform(raw.reshape(N_SOURCE * N_REP, 60))
            pca = PCA(n_components=2, svd_solver="full").fit(scaler.transform(training))
            z[:, :, 2 * block:2 * block + 2] = pca.transform(standardized).reshape(N_SOURCE, N_REP, 2)
            pca_means[fi, block] = scaler.mean_; pca_scales[fi, block] = scaler.scale_
            pca_components[fi, block] = pca.components_
            pca_manifest.append({"fold": fi, "block": block, "time_indices": [t0, t1],
                                 "reference_count": N_SOURCE * 12,
                                 "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
                                 "nonzero_variance_features": int(np.count_nonzero(np.var(training, axis=0) > 0))})
        reference, targets = z[:, ref_ix], z[:, eval_ix].reshape(N_SOURCE * 4, DIM)
        truth = np.repeat(np.arange(N_SOURCE), 4)
        fit = fit_density(reference)
        prediction = evaluate(log_likelihood(fit, targets), truth, xy)
        for k in full:
            full[k][:, eval_ix] = prediction[k].reshape(N_SOURCE, 4)
        model_manifest.append({"fold": fi, "full_oas_shrinkage_by_source": [m[3] for m in fit],
                               "jitter_rule": "1e-10*max(1,trace(covariance)/d)"})
        diag = evaluate(log_likelihood(fit_density(reference, diagonal=True), targets), truth, xy)
        product = evaluate(block_product_likelihood(reference, targets), truth, xy)
        for name, vals in (("DIAG-COV", diag), ("BLOCK-PRODUCT", product)):
            for k in control[name]:
                control[name][k][:, eval_ix] = vals[k].reshape(N_SOURCE, 4)
        for mi in range(N_SHUFFLE):
            shuffled = reference.copy()
            for source in range(N_SOURCE):
                for b in range(1, 5):
                    seed = config["null"]["base_seed"] + 100000 * fi + 1000 * mi + 10 * source + b
                    perm = derangement(seed)
                    seed_matrix[fi, mi, source, b - 1] = seed
                    permutations[fi, mi, source, b - 1] = perm
                    sl = slice(2 * b, 2 * b + 2)
                    shuffled[source, :, sl] = reference[source, perm, sl]
                    if not np.array_equal(np.sort(shuffled[source, :, sl], axis=0), np.sort(reference[source, :, sl], axis=0)):
                        raise RuntimeError("SHUFFLED block marginal changed")
                    if np.any(perm == np.arange(12)):
                        raise RuntimeError("SHUFFLED derangement violation")
                if not np.allclose(shuffled[source].mean(axis=0), reference[source].mean(axis=0), atol=1e-12):
                    raise RuntimeError("SHUFFLED source mean drift")
                if not np.allclose(shuffled[source].var(axis=0), reference[source].var(axis=0), atol=1e-12):
                    raise RuntimeError("SHUFFLED source variance drift")
                off = np.cov(reference[source].T)[:2, 2:]
                if np.linalg.norm(off) > 1e-12 and np.allclose(np.cov(shuffled[source].T)[:2, 2:], off, atol=1e-12, rtol=0):
                    raise RuntimeError("SHUFFLED cross-block covariance did not change")
            prediction = evaluate(log_likelihood(fit_density(shuffled), targets), truth, xy)
            for k in null:
                null[k][mi, :, eval_ix] = prediction[k].reshape(N_SOURCE, 4)
        print(f"F{fi} complete: full_mean_nll={full['nll'][:,eval_ix].mean():.8f}", flush=True)
    np.savez_compressed(out / "models/pca_transforms.npz", mean=pca_means, scale=pca_scales, components=pca_components)
    write_json(out / "models/pca_manifest.json", {"fold_blocks": pca_manifest, "transforms_sha256": sha(out / "models/pca_transforms.npz")})
    write_json(out / "models/model_manifest.json", {"full_models": model_manifest, "covariance": "sklearn OAS source-specific",
                                                      "null_models_per_fold": N_SHUFFLE, "source_count": N_SOURCE})
    np.savez_compressed(out / "config/null_permutations.npz", permutations=permutations)
    write_json(out / "config/shuffle_seeds.json", {"base_seed": config["null"]["base_seed"],
                                                     "formula": "base+100000*fold+1000*shuffle+10*source+block",
                                                     "block_index_range": [1, 2, 3, 4],
                                                     "seeds": seed_matrix.tolist(),
                                                     "permutations_sha256": sha(out / "config/null_permutations.npz"),
                                                     "derangement_non_anchor_changed_fraction": 1.0})
    null_mean = null["nll"].mean(axis=(1, 2))
    full_mean = float(full["nll"].mean())
    null_median = float(np.median(null_mean))
    rel_gain = (null_median - full_mean) / null_median
    p_emp = (1 + int(np.sum(null_mean <= full_mean))) / (N_SHUFFLE + 1)
    delta = np.median(null["nll"], axis=0) - full["nll"]
    ci_low, ci_high = bootstrap_ci(delta, config["bootstrap"]["draws"], config["bootstrap"]["seed"])
    fold_delta = [float(delta[:, ix].mean()) for ix in FOLDS]
    source_delta = delta.mean(axis=1)
    loso = [(float((delta.sum() - delta[s].sum()) / ((N_SOURCE - 1) * N_REP))) for s in range(N_SOURCE)]
    full_median_rank = float(np.median(full["rank"]))
    null_median_rank = float(np.median(np.median(null["rank"], axis=(1, 2))))
    full_top3 = float(full["top3"].mean())
    null_top3 = float(np.median(null["top3"].mean(axis=(1, 2))))
    metrics_for_gate = {"input_contract_pass": True, "relative_nll_gain": float(rel_gain), "empirical_p": float(p_emp),
                        "bootstrap_ci_low": ci_low, "bootstrap_ci_high": ci_high, "fold_delta_nll": fold_delta,
                        "positive_source_count": int(np.sum(source_delta > 0)),
                        "loso_positive_count": int(np.sum(np.array(loso) > 0)),
                        "full_median_truth_rank": full_median_rank, "null_median_truth_rank": null_median_rank,
                        "full_top3": full_top3, "null_median_top3": null_top3}
    write_json(out / "metrics/metrics_for_frozen_gate.json", metrics_for_gate)
    label = subprocess.check_output([sys.executable, str(frozen / "scripts/decision_gate.py"),
                                     str(out / "metrics/metrics_for_frozen_gate.json")], text=True).strip()
    target_rows = []
    fold_of_rep = {r: fi for fi, ix in enumerate(FOLDS) for r in ix}
    for s in range(N_SOURCE):
        for r in range(N_REP):
            target_rows.append({"source_index": s, "source_id": ids[s], "realization_index": r,
                                "realization_id": realization_ids[s][r], "fold": fold_of_rep[r],
                                **{k: float(full[k][s, r]) if k in ("nll", "posterior_true", "map_error_m") else int(full[k][s, r])
                                   for k in full}})
    write_csv(out / "metrics/target_metrics_full.csv", target_rows, list(target_rows[0]))
    null_rows = []
    for m in range(N_SHUFFLE):
        for s in range(N_SOURCE):
            for r in range(N_REP):
                null_rows.append({"shuffle": m, "source_index": s, "source_id": ids[s],
                                  "realization_index": r, "fold": fold_of_rep[r],
                                  **{k: float(null[k][m, s, r]) if k in ("nll", "posterior_true", "map_error_m") else int(null[k][m, s, r])
                                     for k in null}})
    write_csv(out / "metrics/target_metrics_null_long.csv", null_rows, list(null_rows[0]))
    replicate_rows = [{"shuffle": m, "mean_nll": float(null_mean[m]),
                       "median_truth_rank": float(np.median(null["rank"][m])),
                       "top1": float(null["top1"][m].mean()), "top3": float(null["top3"][m].mean())}
                      for m in range(N_SHUFFLE)]
    write_csv(out / "metrics/null_replicate_summary.csv", replicate_rows, list(replicate_rows[0]))
    fold_rows = [{"fold": fi, "full_mean_nll": float(full["nll"][:, ix].mean()),
                  "null_median_mean_nll": float(np.median(null["nll"][:, :, ix].mean(axis=(1, 2)))),
                  "paired_mean_delta_nll": fold_delta[fi]} for fi, ix in enumerate(FOLDS)]
    write_csv(out / "metrics/fold_summary.csv", fold_rows, list(fold_rows[0]))
    source_rows = [{"source_index": s, "source_id": ids[s], "full_mean_nll": float(full["nll"][s].mean()),
                    "null_median_mean_nll": float(np.median(null["nll"][:, s].mean(axis=1))),
                    "paired_mean_delta_nll": float(source_delta[s]), "positive": int(source_delta[s] > 0)}
                   for s in range(N_SOURCE)]
    write_csv(out / "metrics/source_summary.csv", source_rows, list(source_rows[0]))
    loso_rows = [{"excluded_source_index": s, "excluded_source_id": ids[s],
                  "paired_mean_delta_nll": loso[s], "positive": int(loso[s] > 0)} for s in range(N_SOURCE)]
    write_csv(out / "metrics/leave_one_source_out.csv", loso_rows, list(loso_rows[0]))
    for name, pred in (("confusion_full.csv", full["map_source"]),
                       ("confusion_null_median.csv", null["map_source"])):
        if pred.ndim == 2:
            table = np.zeros((N_SOURCE, N_SOURCE), dtype=int)
            for s in range(N_SOURCE):
                table[s] = np.bincount(pred[s].astype(int), minlength=N_SOURCE)
        else:
            tables = np.zeros((N_SHUFFLE, N_SOURCE, N_SOURCE), dtype=int)
            for m in range(N_SHUFFLE):
                for s in range(N_SOURCE):
                    tables[m, s] = np.bincount(pred[m, s].astype(int), minlength=N_SOURCE)
            table = np.median(tables, axis=0)
        confusion_rows = [{"true_source_id": ids[s], "predicted_source_id": ids[p], "count": float(table[s, p])}
                          for s in range(N_SOURCE) for p in range(N_SOURCE)]
        write_csv(out / "metrics" / name, confusion_rows, list(confusion_rows[0]))
    controls = [{"model": "FULL", "mean_nll": full_mean, "median_truth_rank": full_median_rank, "top3": full_top3}]
    for name, vals in control.items():
        controls.append({"model": name, "mean_nll": float(vals["nll"].mean()),
                         "median_truth_rank": float(np.median(vals["rank"])), "top3": float(vals["top3"].mean())})
    write_csv(out / "metrics/control_models_summary.csv", controls, list(controls[0]))
    figure(out / "figures/nll_null_distribution.png", "null", null_mean, np.array([full_mean]))
    figure(out / "figures/source_delta_nll.png", "source", source_delta)
    figure(out / "figures/fold_delta_nll.png", "fold", np.array(fold_delta))
    figure(out / "figures/rank_full_vs_null.png", "rank", np.array([full_median_rank]), np.array([null_median_rank]))
    env = {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
           "sklearn": sklearn.__version__, "matplotlib": matplotlib.__version__,
           "working_model": "source-specific OAS Gaussian in 10D PCA representation",
           "threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
           "base_commit": BASE,
           "code_commit_at_execution": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()}
    write_json(out / "logs/environment.txt", env)
    (out / "logs/run.log").write_text("A0 PASS; four folds and 200 deranged nulls/fold completed.\n"
                                       "All block marginals, means, variances and derangements checked.\n"
                                       f"Frozen decision: {label}\n", encoding="utf-8")
    summary = {"decision": label, "base_commit": BASE,
               "final_commit": "See final branch HEAD and review package git_state.txt; self-reference is impossible",
               "input_contract_pass": True, "n_sources": N_SOURCE, "n_realizations_per_source": N_REP,
               "full_mean_nll": full_mean, "null_median_mean_nll": null_median,
               "relative_nll_gain": float(rel_gain), "empirical_p": float(p_emp),
               "bootstrap_ci_low": ci_low, "bootstrap_ci_high": ci_high,
               "fold_delta_nll": fold_delta, "positive_source_count": int(np.sum(source_delta > 0)),
               "loso_positive_count": int(np.sum(np.array(loso) > 0)),
               "full_median_truth_rank": full_median_rank, "null_median_truth_rank": null_median_rank,
               "full_top3": full_top3, "null_median_top3": null_top3,
               "full_top1": float(full["top1"].mean()),
               "null_median_top1": float(np.median(null["top1"].mean(axis=(1, 2)))),
               "paired_delta_nll_mean": float(delta.mean()), "paired_delta_nll_median": float(np.median(delta)),
               "null_replicates": N_SHUFFLE, "cv_folds": 4,
               "no_closed_loop": True, "no_dense_expansion": True, "no_new_plume_generation": True,
               "evidence_zip_sha256": "See external SHA256 sidecar and final report; ZIP self-reference is impossible"}
    write_json(out / "JTD_G0_MACHINE_SUMMARY.json", summary)
    decision_md = ["# JTD-G0 frozen decision", "", f"Decision: `{label}`", "",
                   f"Base R0 commit: `{BASE}`; A0 input contract: PASS (18 x 16 full realizations).", "",
                   "Ordered 10 x 30 raw pooled ppm was verified by exact re-extraction of all 288 cubes.", "",
                   f"FULL mean NLL: {full_mean:.9g}; median SHUFFLED mean NLL: {null_median:.9g}.",
                   f"Relative gain: {rel_gain:.6g}; empirical p: {p_emp:.6g}.",
                   f"Paired hierarchical-bootstrap 95% CI: [{ci_low:.9g}, {ci_high:.9g}].",
                   f"Four fold paired deltas: {fold_delta}.",
                   f"Positive sources: {int(np.sum(source_delta > 0))}/18; positive leave-one-source-out: {int(np.sum(np.array(loso) > 0))}/18.",
                   f"Median truth rank FULL / null: {full_median_rank:.6g} / {null_median_rank:.6g}.",
                   f"Top-3 FULL / null: {full_top3:.6g} / {null_top3:.6g}.", "",
                   "Allowed claim: only the frozen 18-source R0 discovery-gate outcome under this Gaussian working model.",
                   "Forbidden claim: dense-source, real-flight, or general path-likelihood validation.",
                   "No closed loop, dense expansion, new plume, or hyperparameter rescue was run.",
                   "Final commit and ZIP SHA256 are reported externally after immutable artifacts are committed and packaged.", ""]
    (out / "JTD_G0_DECISION_20260925.md").write_text("\n".join(decision_md), encoding="utf-8")
    paths = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "MANIFEST_SHA256.txt")
    (out / "MANIFEST_SHA256.txt").write_text("".join(f"{sha(p)}  {p.relative_to(out).as_posix()}\n" for p in paths), encoding="utf-8")
    print(label)
    print(json.dumps({"full_mean_nll": full_mean, "null_median_mean_nll": null_median,
                      "relative_nll_gain": rel_gain, "empirical_p": p_emp,
                      "fold_delta_nll": fold_delta, "positive_source_count": int(np.sum(source_delta > 0))}, sort_keys=True))


if __name__ == "__main__":
    main()
