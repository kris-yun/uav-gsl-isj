#!/usr/bin/env python3
"""Frozen 168-source JTD-G1A: FULL, BP, MBD, DIAG, SHUFFLED."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy
import sklearn
from scipy.special import logsumexp
from scipy.stats import trim_mean
from sklearn.covariance import OAS
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

S, R, K, B, N_NULL, D = 168, 16, 12, 5, 200, 10
FOLDS = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15))
MODELS = ("FULL", "BLOCK_PRODUCT", "MATCHED_BLOCK_DIAG", "DIAG_COV")
JITTER = 1e-10


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")


def write_csv(path: Path, data: list[dict]) -> None:
    if not data:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)


def density(reference: np.ndarray, kind: str = "FULL") -> dict:
    """Exact G0 OAS and jitter; MBD takes FULL's already stabilized covariance."""
    s, _, d = reference.shape
    mu = np.empty((s, d)); cov = np.empty((s, d, d)); shrink = np.empty(s)
    for source in range(s):
        fit = OAS(assume_centered=False, store_precision=False).fit(reference[source])
        mu[source] = fit.location_
        c = fit.covariance_.copy()
        if kind == "DIAG_COV":
            c = np.diag(np.diag(c))
        c.flat[::d+1] += JITTER*max(1.0, float(np.trace(c))/d)
        cov[source] = c
        shrink[source] = fit.shrinkage_
    return prepare_density(mu, cov, shrink)


def prepare_density(mu: np.ndarray, cov: np.ndarray, shrink: np.ndarray) -> dict:
    sign, logdet = np.linalg.slogdet(cov)
    if not np.all(sign == 1):
        raise RuntimeError("nonpositive fitted covariance")
    return {"mu": mu, "cov": cov, "prec": np.linalg.inv(cov), "logdet": logdet,
            "shrinkage": shrink, "condition": np.linalg.cond(cov)}


def matched_block_diag(full: dict) -> dict:
    c = np.zeros_like(full["cov"])
    for block in range(B):
        sl = slice(2*block, 2*block+2)
        c[:, sl, sl] = full["cov"][:, sl, sl]
    assert np.array_equal(full["mu"], full["mu"])
    for block in range(B):
        sl = slice(2*block, 2*block+2)
        assert np.array_equal(c[:, sl, sl], full["cov"][:, sl, sl])
    return prepare_density(full["mu"].copy(), c, full["shrinkage"].copy())


def gaussian_loglik(targets: np.ndarray, model: dict, outer: np.ndarray | None = None) -> np.ndarray:
    mu, prec, logdet = model["mu"], model["prec"], model["logdet"]
    d = targets.shape[1]
    if outer is None:
        outer = np.einsum("ti,tj->tij", targets, targets).reshape(len(targets), d*d)
    p_mu = np.einsum("sij,sj->si", prec, mu)
    quadratic = outer @ prec.reshape(len(mu), d*d).T - 2*(targets @ p_mu.T) + np.einsum("si,si->s", mu, p_mu)
    return -0.5*(d*np.log(2*np.pi) + quadratic + logdet)


def block_product_loglik(reference: np.ndarray, targets: np.ndarray) -> tuple[np.ndarray, list[dict]]:
    out = np.zeros((len(targets), S))
    models = []
    for block in range(B):
        sl = slice(2*block, 2*block+2)
        model = density(reference[:, :, sl])
        out += gaussian_loglik(targets[:, sl], model)
        models.append(model)
    return out, models


def normalize(loglik: np.ndarray, truth: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    logpost = loglik - logsumexp(loglik, axis=1, keepdims=True)
    nll = -logpost[np.arange(len(truth)), truth]
    rank = 1 + np.sum(loglik > loglik[np.arange(len(truth)), truth, None], axis=1)
    if not np.isfinite(nll).all():
        raise RuntimeError("nonfinite posterior NLL")
    return logpost, nll, rank


def tail_stats(delta: np.ndarray) -> dict:
    flat = delta.reshape(-1)
    positive = np.flatnonzero(flat > 0)
    order = positive[np.argsort(flat[positive])[::-1]]
    out = {"target_mean": float(np.mean(flat)), "trimmed_10_mean": float(trim_mean(flat, 0.1)),
           "trimmed_20_mean": float(trim_mean(flat, 0.2)),
           "largest_positive_target_delta": float(np.max(flat)),
           "largest_negative_target_delta": float(np.min(flat))}
    for pct in (1, 5):
        count = math.ceil(len(flat)*pct/100)
        removed = order[:count]
        out[f"remove_top_positive_{pct}pct_count"] = len(removed)
        out[f"remove_top_positive_{pct}pct_mean"] = float(np.delete(flat, removed).mean())
    return out


def bootstrap_source_means(source_means: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(2026092502)
    indices = rng.integers(0, S, size=(5000, S))
    return source_means[indices].mean(axis=1)


def main() -> None:
    p = argparse.ArgumentParser()
    for name in ("tensor", "panel", "a0", "null-dir", "out"):
        p.add_argument("--"+name, type=Path, required=True)
    a = p.parse_args()
    if a.out.exists() and any(a.out.iterdir()):
        raise RuntimeError("refuse nonempty G1A science output")
    audit = json.loads(a.a0.read_text(encoding="utf-8"))
    lock = json.loads((a.null_dir / "JTD_G1A_NULL_LOCK.json").read_text(encoding="utf-8"))
    if audit["decision"] != "JTD_G1A_A0_COMPATIBLE" or sha(a.a0) != lock["a0_sha256"]:
        raise RuntimeError("A0 incompatible or lock drift")
    if sha(a.tensor) != audit["checks"][4]["expected_sha256"] or sha(a.panel) != lock["panel_sha256"]:
        raise RuntimeError("D1R tensor/panel hash drift")
    if sha(a.null_dir / "JTD_G1A_NULL_DERANGEMENTS.npy") != lock["derangement_file_sha256"]:
        raise RuntimeError("null derangement hash drift")
    x = np.load(a.tensor, allow_pickle=False)
    perms = np.load(a.null_dir / "JTD_G1A_NULL_DERANGEMENTS.npy", allow_pickle=False, mmap_mode="r")
    with a.panel.open(newline="", encoding="utf-8") as f:
        panel = list(csv.DictReader(f, delimiter="\t"))
    if x.shape != (S, R, 10, 30) or x.dtype != np.float64 or len(panel) != S or perms.shape != (4, N_NULL, S, 4, K):
        raise RuntimeError("frozen shape mismatch")
    if not np.isfinite(x).all() or np.any(x < 0):
        raise RuntimeError("invalid raw ppm")
    ids = [r["source_id"] for r in panel]
    xy = np.array([[float(r["x_m"]), float(r["y_m"])] for r in panel])
    distance = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=2)
    distance_no_self = distance.copy(); np.fill_diagonal(distance_no_self, np.inf)
    nearest = np.argmin(distance_no_self, axis=1)
    nearest_rows = [{"source_index": s, "source_id": ids[s], "nearest_index": int(nearest[s]),
                     "nearest_id": ids[int(nearest[s])], "distance_m": float(distance[s, nearest[s]])}
                    for s in range(S)]
    a.out.mkdir(parents=True)
    write_csv(a.out / "JTD_G1A_FROZEN_NEAREST_NEIGHBORS.csv", nearest_rows)
    truth = np.repeat(np.arange(S), 4)
    logpost = np.full((len(MODELS), S, R, S), np.nan)
    nll = np.full((len(MODELS), S, R), np.nan)
    rank = np.zeros((len(MODELS), S, R), dtype=np.int16)
    null_nll = np.full((N_NULL, S, R), np.nan)
    null_rank = np.zeros((N_NULL, S, R), dtype=np.int16)
    fold_rows, model_provenance, wrong_neighbor_rows = [], [], []
    full_gaussian_terms = []
    for fi, eval_ix_tuple in enumerate(FOLDS):
        eval_ix = list(eval_ix_tuple)
        ref_ix = [r for r in range(R) if r not in eval_ix]
        z = np.empty((S, R, D))
        pca_info = []
        for block in range(B):
            t0, t1 = 2*block, 2*block+1
            raw = x[:, :, [t0, t1], :].reshape(S, R, 60)
            training = raw[:, ref_ix].reshape(S*K, 60)
            if np.count_nonzero(np.var(training, axis=0) > 0) < 2:
                raise RuntimeError(f"PCA block {block} invalid")
            scaler = StandardScaler().fit(training)
            pca = PCA(n_components=2, svd_solver="full").fit(scaler.transform(training))
            z[:, :, 2*block:2*block+2] = pca.transform(scaler.transform(raw.reshape(S*R, 60))).reshape(S, R, 2)
            pca_info.append({"block": block, "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
                             "reference_count": S*K})
        reference = z[:, ref_ix]
        targets = z[:, eval_ix].reshape(S*4, D)
        outer = np.einsum("ti,tj->tij", targets, targets).reshape(S*4, D*D)
        full = density(reference)
        mbd = matched_block_diag(full)
        diag = density(reference, "DIAG_COV")
        bp_loglik, bp_models = block_product_loglik(reference, targets)
        predictions = (gaussian_loglik(targets, full, outer), bp_loglik,
                       gaussian_loglik(targets, mbd, outer), gaussian_loglik(targets, diag, outer))
        fold_lp = []
        for mi, ll in enumerate(predictions):
            lp, nl, ra = normalize(ll, truth)
            logpost[mi, :, eval_ix, :] = lp.reshape(S, 4, S).transpose(1, 0, 2)
            nll[mi, :, eval_ix] = nl.reshape(S, 4).T
            rank[mi, :, eval_ix] = ra.reshape(S, 4).T
            fold_lp.append(lp)
        full_map = np.argmax(predictions[0], axis=1)
        for target_ix in np.flatnonzero((full_map != truth) & (full_map == nearest[truth])):
            source, pred = int(truth[target_ix]), int(full_map[target_ix])
            r = eval_ix[target_ix % 4]
            vector = targets[target_ix]
            quad = []
            for candidate in (source, pred):
                v = vector-full["mu"][candidate]
                quad.append(float(v @ full["prec"][candidate] @ v))
            row = {"fold": fi, "source_index": source, "source_id": ids[source], "realization_index": r,
                   "neighbor_index": pred, "neighbor_id": ids[pred],
                   "full_true_vs_neighbor_logodds": float(fold_lp[0][target_ix, source]-fold_lp[0][target_ix, pred]),
                   "full_quadratic_true": quad[0], "full_quadratic_neighbor": quad[1],
                   "full_logdet_true": float(full["logdet"][source]), "full_logdet_neighbor": float(full["logdet"][pred]),
                   "full_quadratic_logodds_contribution": float(-0.5*(quad[0]-quad[1])),
                   "full_logdet_logodds_contribution": float(-0.5*(full["logdet"][source]-full["logdet"][pred])),
                   "full_oas_shrinkage_true": float(full["shrinkage"][source]),
                   "full_oas_shrinkage_neighbor": float(full["shrinkage"][pred]),
                   "full_cov_condition_true": float(full["condition"][source]),
                   "full_cov_condition_neighbor": float(full["condition"][pred])}
            for mi, name in enumerate(MODELS[:3]):
                tag = name.lower()
                row[f"{tag}_posterior_true"] = float(np.exp(fold_lp[mi][target_ix, source]))
                row[f"{tag}_posterior_neighbor"] = float(np.exp(fold_lp[mi][target_ix, pred]))
            wrong_neighbor_rows.append(row)
        model_provenance.append({"fold": fi, "reference_indices_zero_based": ref_ix, "target_indices_zero_based": eval_ix,
                                 "full_shrinkage": full["shrinkage"].tolist(), "pca_blocks": pca_info,
                                 "full_cov_condition": full["condition"].tolist()})
        full_gaussian_terms.append({"fold": fi, "mean_sha256": hashlib.sha256(full["mu"].tobytes()).hexdigest(),
                                    "covariance_sha256": hashlib.sha256(full["cov"].tobytes()).hexdigest()})
        for null_id in range(N_NULL):
            shuffled = reference.copy()
            for source in range(S):
                for block in range(1, B):
                    permutation = perms[fi, null_id, source, block-1].astype(int)
                    if np.any(permutation == np.arange(K)) or sorted(permutation.tolist()) != list(range(K)):
                        raise RuntimeError("null derangement invalid")
                    sl = slice(2*block, 2*block+2)
                    shuffled[source, :, sl] = reference[source, permutation, sl]
            if not np.allclose(shuffled.mean(axis=1), reference.mean(axis=1), atol=1e-12, rtol=0):
                raise RuntimeError("null mean drift")
            null_model = density(shuffled)
            _, nl, ra = normalize(gaussian_loglik(targets, null_model, outer), truth)
            null_nll[null_id, :, eval_ix] = nl.reshape(S, 4).T
            null_rank[null_id, :, eval_ix] = ra.reshape(S, 4).T
        fold_rows.append({"fold": fi, "reference_count_per_source": K, "target_count_per_source": 4,
                          "full_mean_nll": float(nll[0, :, eval_ix].mean()),
                          "bp_mean_nll": float(nll[1, :, eval_ix].mean()),
                          "mbd_mean_nll": float(nll[2, :, eval_ix].mean()),
                          "diag_mean_nll": float(nll[3, :, eval_ix].mean()),
                          "mean_delta_bp": float((nll[1, :, eval_ix]-nll[0, :, eval_ix]).mean()),
                          "mean_delta_mbd": float((nll[2, :, eval_ix]-nll[0, :, eval_ix]).mean())})
        print(f"JTD_G1A_FOLD_DONE {fi+1}/4 FULL_NLL={fold_rows[-1]['full_mean_nll']:.6f}", flush=True)
    if not np.isfinite(logpost).all() or not np.isfinite(nll).all() or not np.isfinite(null_nll).all():
        raise RuntimeError("G1A output matrix incomplete")
    np.savez_compressed(a.out / "JTD_G1A_COMPLETE_POSTERIORS.npz", logpost=logpost, posterior=np.exp(logpost),
                        model_names=np.asarray(MODELS), source_ids=np.asarray(ids))
    np.savez_compressed(a.out / "JTD_G1A_SCORE_ARRAYS.npz", nll=nll, rank=rank, null_nll=null_nll, null_rank=null_rank)
    target_rows, nn_rows, source_rows = [], [], []
    spatial = {}
    for mi, name in enumerate(MODELS):
        p = np.exp(logpost[mi])
        truth_ix = np.arange(S)[:, None, None]
        p_true = p[np.arange(S)[:, None], np.arange(R)[None, :], np.arange(S)[:, None]]
        brier = np.sum(p*p, axis=2) - 2*p_true + 1.0
        mass_05 = np.einsum("src,sc->sr", p, distance <= 0.5 + 1e-12)
        mass_10 = np.einsum("src,sc->sr", p, distance <= 1.0 + 1e-12)
        expected_dist = np.einsum("src,sc->sr", p, distance)
        map_ix = np.argmax(logpost[mi], axis=2)
        map_error = distance[np.arange(S)[:, None], map_ix]
        nn_prob = p[np.arange(S)[:, None], np.arange(R)[None, :], nearest[:, None]]
        nn_logodds = logpost[mi, np.arange(S)[:, None], np.arange(R)[None, :], np.arange(S)[:, None]] - \
                     logpost[mi, np.arange(S)[:, None], np.arange(R)[None, :], nearest[:, None]]
        spatial[name] = {"brier": brier, "mass_05": mass_05, "mass_10": mass_10,
                         "expected_distance": expected_dist, "map_error": map_error,
                         "map_ix": map_ix, "nearest_confusion": map_ix == nearest[:, None],
                         "nearest_logodds": nn_logodds, "p_true": p_true, "p_nearest": nn_prob}
        for s in range(S):
            for r in range(R):
                target_rows.append({"model": name, "source_index": s, "source_id": ids[s], "realization_index": r,
                                    "fold": r % 4, "truth_nll": float(nll[mi, s, r]), "truth_rank": int(rank[mi, s, r]),
                                    "top1": int(rank[mi, s, r] == 1), "top3": int(rank[mi, s, r] <= 3),
                                    "top5": int(rank[mi, s, r] <= 5), "brier": float(brier[s, r]),
                                    "posterior_mass_0p5m": float(mass_05[s, r]), "posterior_mass_1p0m": float(mass_10[s, r]),
                                    "posterior_expected_distance_m": float(expected_dist[s, r]),
                                    "map_distance_error_m": float(map_error[s, r]),
                                    "map_source_id": ids[int(map_ix[s, r])],
                                    "nearest_neighbor_confusion": int(map_ix[s, r] == nearest[s]),
                                    "truth_vs_nearest_logodds": float(nn_logodds[s, r])})
    for s in range(S):
        for r in range(R):
            row = {"source_index": s, "source_id": ids[s], "realization_index": r,
                   "nearest_index": int(nearest[s]), "nearest_id": ids[int(nearest[s])],
                   "nearest_distance_m": float(distance[s, nearest[s]])}
            for name in MODELS:
                tag = name.lower()
                row[f"{tag}_truth_vs_nearest_logodds"] = float(spatial[name]["nearest_logodds"][s, r])
                row[f"{tag}_map_is_nearest"] = int(spatial[name]["nearest_confusion"][s, r])
                row[f"{tag}_posterior_true"] = float(spatial[name]["p_true"][s, r])
                row[f"{tag}_posterior_nearest"] = float(spatial[name]["p_nearest"][s, r])
            nn_rows.append(row)
    delta_bp = nll[1]-nll[0]
    delta_mbd = nll[2]-nll[0]
    src_bp = delta_bp.mean(axis=1)
    src_mbd = delta_mbd.mean(axis=1)
    for s in range(S):
        source_rows.append({"source_index": s, "source_id": ids[s], "x_m": float(xy[s, 0]), "y_m": float(xy[s, 1]),
                            "mean_delta_bp": float(src_bp[s]), "mean_delta_mbd": float(src_mbd[s]),
                            "positive_bp": int(src_bp[s] > 0), "positive_mbd": int(src_mbd[s] > 0),
                            "full_mean_nll": float(nll[0, s].mean()), "bp_mean_nll": float(nll[1, s].mean()),
                            "mbd_mean_nll": float(nll[2, s].mean()),
                            "full_top1": float((rank[0, s] == 1).mean()), "bp_top1": float((rank[1, s] == 1).mean())})
    write_csv(a.out / "JTD_G1A_TARGET_METRICS.csv", target_rows)
    write_csv(a.out / "JTD_G1A_SOURCE_SUMMARY.csv", source_rows)
    write_csv(a.out / "JTD_G1A_FOLD_SUMMARY.csv", fold_rows)
    write_csv(a.out / "JTD_G1A_NEAREST_NEIGHBOR_DIAGNOSTICS.csv", nn_rows)
    write_csv(a.out / "JTD_G1A_GAUSSIAN_WRONG_NEIGHBOR_DECOMPOSITION.csv", wrong_neighbor_rows)
    boot_bp, boot_mbd = bootstrap_source_means(src_bp), bootstrap_source_means(src_mbd)
    np.savez_compressed(a.out / "JTD_G1A_BOOTSTRAP_5000.npz", bp=boot_bp, mbd=boot_mbd)
    ci_bp, ci_mbd = np.quantile(boot_bp, (0.025, 0.975)), np.quantile(boot_mbd, (0.025, 0.975))
    null_mean = null_nll.mean(axis=(1, 2))
    null_target_median = np.median(null_nll, axis=0)
    null_cont_delta = null_target_median - nll[0]
    write_csv(a.out / "JTD_G1A_SHUFFLED_NULL_SUMMARY.csv",
              [{"null_id": i, "aggregate_mean_truth_nll": float(null_mean[i]),
                "mean_truth_rank": float(null_rank[i].mean()), "top3_fraction": float((null_rank[i] <= 3).mean())}
               for i in range(N_NULL)])
    spatial_summary = {}
    for mi, name in enumerate(MODELS):
        z = spatial[name]
        spatial_summary[name] = {"mean_truth_nll": float(nll[mi].mean()), "mean_truth_rank": float(rank[mi].mean()),
                                 "top1": float((rank[mi] == 1).mean()), "top3": float((rank[mi] <= 3).mean()),
                                 "top5": float((rank[mi] <= 5).mean()), "mean_brier": float(z["brier"].mean()),
                                 "mean_mass_0p5m": float(z["mass_05"].mean()), "mean_mass_1p0m": float(z["mass_10"].mean()),
                                 "mean_expected_distance_m": float(z["expected_distance"].mean()),
                                 "mean_map_distance_error_m": float(z["map_error"].mean()),
                                 "nearest_neighbor_confusion_rate": float(z["nearest_confusion"].mean()),
                                 "mean_truth_vs_nearest_logodds": float(z["nearest_logodds"].mean())}
    utility = {}
    for metric, better in (("mean_brier", "lower"), ("mean_mass_1p0m", "higher"), ("mean_expected_distance_m", "lower")):
        f, b = spatial_summary["FULL"][metric], spatial_summary["BLOCK_PRODUCT"][metric]
        improvement = (b-f) if better == "lower" else (f-b)
        relative_worsening = (-improvement)/abs(b) if b != 0 else (math.inf if improvement < 0 else 0.0)
        utility[metric] = {"full": f, "bp": b, "absolute_improvement": improvement,
                           "relative_worsening": relative_worsening,
                           "improves": bool(improvement > 0), "worsens_more_than_5pct": bool(relative_worsening > 0.05)}
    g1 = bool(src_bp.mean() > 0 and ci_bp[0] > 0)
    g2 = bool(src_mbd.mean() > 0 and ci_mbd[0] > 0)
    g3 = bool(np.sum(src_bp > 0) >= math.ceil(0.6*S) and np.sum(src_mbd > 0) >= math.ceil(0.6*S))
    tails_bp, tails_mbd = tail_stats(delta_bp), tail_stats(delta_mbd)
    g4 = bool(tails_bp["trimmed_20_mean"] > 0 and tails_bp["remove_top_positive_5pct_mean"] > 0)
    g5 = bool(nll[0].mean() < np.median(null_mean))
    g6 = bool(any(v["improves"] for v in utility.values()) and not any(v["worsens_more_than_5pct"] for v in utility.values()))
    gates = {f"G{i}": v for i, v in enumerate((g1, g2, g3, g4, g5, g6), start=1)}
    if all(gates.values()):
        decision = "JTD_G1A_GO_DENSE_PROBABILISTIC_UTILITY_AND_CROSSBLOCK_CONTRIBUTION"
    elif all((g1, g2, g3, g4, g5)):
        decision = "JTD_G1A_HOLD_SCORE_UTILITY_TRADEOFF"
    else:
        decision = "JTD_G1A_STOP_DENSE_UTILITY_OR_MECHANISM_NOT_CONFIRMED"
    overlap = audit["r0_g0_panel_intersection_ids"]
    overlap_ix = [ids.index(source_id) for source_id in overlap]
    other_ix = [s for s in range(S) if s not in overlap_ix]
    result = {
        "decision": decision, "gates": gates, "source_count": S, "realizations_per_source": R,
        "target_count": S*R, "fold_count": 4, "reference_per_source_per_fold": K,
        "a0_sha256": sha(a.a0), "null_lock_sha256": sha(a.null_dir / "JTD_G1A_NULL_LOCK.json"),
        "tensor_sha256": sha(a.tensor), "panel_sha256": sha(a.panel),
        "models": spatial_summary,
        "delta_bp": {"source_panel_mean": float(src_bp.mean()), "source_sensitivity_ci_95": ci_bp.tolist(),
                     "positive_source_count": int(np.sum(src_bp > 0)), "positive_source_fraction": float(np.mean(src_bp > 0)),
                     "fold_means": [r["mean_delta_bp"] for r in fold_rows], **tails_bp},
        "delta_mbd": {"source_panel_mean": float(src_mbd.mean()), "source_sensitivity_ci_95": ci_mbd.tolist(),
                      "positive_source_count": int(np.sum(src_mbd > 0)), "positive_source_fraction": float(np.mean(src_mbd > 0)),
                      "fold_means": [r["mean_delta_mbd"] for r in fold_rows], **tails_mbd},
        "shuffled_continuity": {"median_aggregate_null_mean_nll": float(np.median(null_mean)),
                                "full_mean_nll": float(nll[0].mean()),
                                "mean_targetwise_full_vs_median_null_delta": float(null_cont_delta.mean()),
                                "trimmed_20_targetwise_delta": float(trim_mean(null_cont_delta.ravel(), 0.2)),
                                "positive_source_count": int(np.sum(null_cont_delta.mean(axis=1) > 0))},
        "spatial_utility_vs_bp": utility,
        "original_g0_18_panel_intersection": {"count": len(overlap_ix), "ids": overlap,
                                              "overlap_delta_bp_mean": float(src_bp[overlap_ix].mean()),
                                              "other_167_delta_bp_mean": float(src_bp[other_ix].mean()),
                                              "overlap_delta_mbd_mean": float(src_mbd[overlap_ix].mean()),
                                              "other_167_delta_mbd_mean": float(src_mbd[other_ix].mean())},
        "wrong_nearest_neighbor_decomposition_rows": len(wrong_neighbor_rows),
        "software": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                     "sklearn": sklearn.__version__},
        "interpretation_boundary": "Frozen historical D1R bank assessment; not a fresh blinded confirmation. Source bootstrap is a panel sensitivity interval, not full learning-procedure confidence interval.",
    }
    write_json(a.out / "JTD_G1A_RESULT.json", result)
    write_json(a.out / "JTD_G1A_MODEL_PROVENANCE.json", {"folds": model_provenance,
                                                       "full_gaussian_terms": full_gaussian_terms,
                                                       "brier_definition": "sum over all 168 classes of (p-onehot)^2",
                                                       "nearest_tie_rule": "first minimum in frozen panel order",
                                                       "tail_removal_rule": "ceil(percent of 2688 targets), largest strictly positive deltas"})
    print(decision, flush=True)
    print("GATES", json.dumps(gates, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
