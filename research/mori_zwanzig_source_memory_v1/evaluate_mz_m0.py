#!/usr/bin/env python3
"""Evaluate whether finite memory is load-bearing for source identity in MZ Gate M0."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

SEEDS = [2026092403, 2026092404, 2026092405]
MEMORY_ORDERS = [2, 4, 8, 16]
RIDGES = [1e-6, 1e-4, 1e-2, 1.0, 100.0]
DECIMATE = 4  # 0.5 s raw -> 2.0 s model cadence


def load_bank(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 180:
        raise ValueError(f"expected 180 M0 sources, got {len(rows)}")
    return rows


def load_histories(root: Path, rows):
    out = {}
    reference_iterations = None
    reference_times = None
    for seed in SEEDS:
        out[seed] = {}
        for r in rows:
            sid = r["source_id"]
            p = root / f"seed_{seed}" / f"{sid}.npz"
            if not p.is_file():
                raise FileNotFoundError(p)
            with np.load(p, allow_pickle=False) as z:
                it = z["iteration_index"].astype(np.int64)
                t = z["time_s"].astype(np.float64)
                x = z["probe_ppm"].astype(np.float64)
            if x.ndim != 2 or x.shape[1] != 30 or x.shape[0] < 500:
                raise ValueError(f"{p}: invalid history shape {x.shape}")
            if not np.isfinite(x).all() or (x < 0).any():
                raise ValueError(f"{p}: invalid concentrations")
            if reference_iterations is None:
                reference_iterations, reference_times = it, t
            else:
                if not np.array_equal(reference_iterations, it):
                    raise ValueError(f"{p}: iteration contract drift")
                if not np.allclose(reference_times, t, rtol=0, atol=1e-12):
                    raise ValueError(f"{p}: time contract drift")
            out[seed][sid] = x[::DECIMATE]
    dt = float(np.median(np.diff(reference_times[::DECIMATE])))
    if abs(dt - 2.0) > 1e-9:
        raise ValueError(f"expected 2.0 s modeling cadence, got {dt}")
    return out, dt


def fit_pca(reference_arrays):
    all_x = np.concatenate(reference_arrays, axis=0)
    mu = all_x.mean(axis=0)
    sigma = all_x.std(axis=0)
    sigma = np.where(sigma > 1e-8, sigma, 1.0)
    q = (all_x - mu) / sigma
    _, s, vt = np.linalg.svd(q, full_matrices=False)
    var = s * s
    frac = np.cumsum(var) / max(float(var.sum()), 1e-30)
    k95 = int(np.searchsorted(frac, 0.95) + 1)
    k = max(3, min(10, k95))
    components = vt[:k]
    return mu, sigma, components, float(frac[k - 1]), k95


def transform(x, mu, sigma, components):
    return ((x - mu) / sigma) @ components.T


def design(seq: np.ndarray, order: int, warmup: int | None = None):
    if warmup is None:
        warmup = order
    if warmup < order:
        raise ValueError("warmup must be >= order")
    if len(seq) <= warmup:
        raise ValueError("sequence shorter than warmup")
    # Predict z[t] from z[t-1],...,z[t-order], with oldest-to-newest blocks.
    ys = seq[warmup:]
    xs = []
    for t in range(warmup, len(seq)):
        xs.append(np.concatenate([seq[t - lag] for lag in range(order, 0, -1)]))
    return np.asarray(xs, dtype=np.float64), np.asarray(ys, dtype=np.float64)


def fit_ridge_from_sequences(sequences, order: int, lam: float):
    xparts, yparts = [], []
    for seq in sequences:
        x, y = design(seq, order)
        xparts.append(x)
        yparts.append(y)
    x = np.concatenate(xparts, axis=0)
    y = np.concatenate(yparts, axis=0)
    xm, ym = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - xm, y - ym
    gram = xc.T @ xc
    cross = xc.T @ yc
    gram.flat[:: gram.shape[0] + 1] += lam
    try:
        bmat = np.linalg.solve(gram, cross)
    except np.linalg.LinAlgError:
        bmat = np.linalg.lstsq(gram, cross, rcond=1e-10)[0]
    intercept = ym - xm @ bmat
    return bmat, intercept


def ridge_path_validation(train_seq, val_seq, order: int, lambdas, warmup: int | None = None):
    x, y = design(train_seq, order)
    xm, ym = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - xm, y - ym
    gram = xc.T @ xc
    cross = xc.T @ yc
    eigval, eigvec = np.linalg.eigh(gram)
    eigval = np.clip(eigval, 0.0, None)
    proj = eigvec.T @ cross

    xv, yv = design(val_seq, order, warmup=warmup)
    den = float(np.sum(yv * yv)) + 1e-12
    errors = []
    for lam in lambdas:
        coef = eigvec @ (proj / (eigval[:, None] + lam))
        intercept = ym - xm @ coef
        pred = xv @ coef + intercept
        errors.append(float(np.sum((yv - pred) ** 2) / den))
    return errors


def choose_memory_hyperparams(z_by_seed, source_ids, ref_a, ref_b):
    table = []
    best = None
    for order in MEMORY_ORDERS:
        sums = np.zeros(len(RIDGES), dtype=np.float64)
        n = 0
        for sid in source_ids:
            for train_seed, val_seed in ((ref_a, ref_b), (ref_b, ref_a)):
                errs = ridge_path_validation(
                    z_by_seed[train_seed][sid],
                    z_by_seed[val_seed][sid],
                    order,
                    RIDGES,
                )
                sums += np.asarray(errs)
                n += 1
        means = sums / n
        for lam, err in zip(RIDGES, means):
            row = {"order": order, "ridge": lam, "reference_cv_error": float(err)}
            table.append(row)
            key = (float(err), order, -math.log10(lam))
            if best is None or key < best[0]:
                best = (key, order, lam)
    assert best is not None
    return int(best[1]), float(best[2]), table


def choose_markov_ridge(z_by_seed, source_ids, ref_a, ref_b, common_warmup):
    sums = np.zeros(len(RIDGES), dtype=np.float64)
    n = 0
    for sid in source_ids:
        for train_seed, val_seed in ((ref_a, ref_b), (ref_b, ref_a)):
            errs = ridge_path_validation(
                z_by_seed[train_seed][sid],
                z_by_seed[val_seed][sid],
                1,
                RIDGES,
                warmup=common_warmup,
            )
            sums += np.asarray(errs)
            n += 1
    means = sums / n
    # tie-break to stronger regularization
    idx = min(range(len(RIDGES)), key=lambda i: (float(means[i]), -math.log10(RIDGES[i])))
    table = [
        {"order": 1, "ridge": float(lam), "reference_cv_error": float(err)}
        for lam, err in zip(RIDGES, means)
    ]
    return float(RIDGES[idx]), table


def score_candidate_models(target_seq, models, order, common_warmup):
    x, y = design(target_seq, order, warmup=common_warmup)
    sids = list(models)
    scores = np.empty(len(sids), dtype=np.float64)
    for i, sid in enumerate(sids):
        coef, intercept = models[sid]
        pred = x @ coef + intercept
        den = float(np.sum(y * y)) + 1e-12
        scores[i] = float(np.sum((y - pred) ** 2) / den)
    return {sid: float(score) for sid, score in zip(sids, scores)}


def rank(scores, truth):
    ordered = sorted(scores.items(), key=lambda kv: (kv[1], kv[0]))
    r = 1 + next(i for i, (sid, _) in enumerate(ordered) if sid == truth)
    return r, ordered[0][0], ordered[:10]


def true_model_error(target_seq, model, order, common_warmup):
    x, y = design(target_seq, order, warmup=common_warmup)
    coef, intercept = model
    pred = x @ coef + intercept
    return float(np.sum((y - pred) ** 2) / (np.sum(y * y) + 1e-12))


def summarize(records, prefix):
    ranks = np.asarray([r[f"{prefix}_rank"] for r in records], dtype=np.float64)
    errs = np.asarray([r[f"{prefix}_true_model_error"] for r in records], dtype=np.float64)
    pos = np.asarray([r[f"{prefix}_top1_position_error_m"] for r in records], dtype=np.float64)
    return {
        "n": int(len(records)),
        "top1_rate": float(np.mean(ranks <= 1)),
        "top3_rate": float(np.mean(ranks <= 3)),
        "top10_rate": float(np.mean(ranks <= 10)),
        "median_truth_rank": float(np.median(ranks)),
        "mean_log_truth_rank": float(np.mean(np.log(ranks))),
        "median_top1_position_error_m": float(np.median(pos)),
        "median_true_model_prediction_error": float(np.median(errs)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-bank", type=Path, required=True)
    ap.add_argument("--history-root", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--out-csv", type=Path, required=True)
    args = ap.parse_args()

    rows = load_bank(args.source_bank)
    source_ids = [r["source_id"] for r in rows]
    coords = {r["source_id"]: np.array([float(r["x_m"]), float(r["y_m"])]) for r in rows}
    histories, model_dt = load_histories(args.history_root, rows)

    result = {
        "mode": "MZ_M0_FINITE_MEMORY_SOURCE_RETRIEVAL",
        "source_count": len(rows),
        "seeds": SEEDS,
        "raw_cadence_s": 0.5,
        "model_cadence_s": model_dt,
        "memory_orders": MEMORY_ORDERS,
        "ridge_grid": RIDGES,
        "folds": {},
    }
    all_records = []

    for heldout in SEEDS:
        refs = [s for s in SEEDS if s != heldout]
        ref_arrays = [histories[s][sid] for s in refs for sid in source_ids]
        mu, sigma, components, retained_fraction, raw_k95 = fit_pca(ref_arrays)

        z_by_seed = {s: {} for s in SEEDS}
        for s in SEEDS:
            for sid in source_ids:
                z_by_seed[s][sid] = transform(histories[s][sid], mu, sigma, components)

        order, mem_lam, mem_cv = choose_memory_hyperparams(
            z_by_seed, source_ids, refs[0], refs[1]
        )
        markov_lam, markov_cv = choose_markov_ridge(
            z_by_seed, source_ids, refs[0], refs[1], common_warmup=order
        )

        mem_models = {
            sid: fit_ridge_from_sequences(
                [z_by_seed[refs[0]][sid], z_by_seed[refs[1]][sid]],
                order,
                mem_lam,
            )
            for sid in source_ids
        }
        markov_models = {
            sid: fit_ridge_from_sequences(
                [z_by_seed[refs[0]][sid], z_by_seed[refs[1]][sid]],
                1,
                markov_lam,
            )
            for sid in source_ids
        }

        fold_records = []
        for truth in source_ids:
            target = z_by_seed[heldout][truth]
            mem_scores = score_candidate_models(target, mem_models, order, order)
            markov_scores = score_candidate_models(target, markov_models, 1, order)
            mem_rank, mem_top, _ = rank(mem_scores, truth)
            mark_rank, mark_top, _ = rank(markov_scores, truth)
            rec = {
                "heldout_seed": heldout,
                "truth_source_id": truth,
                "memory_rank": mem_rank,
                "markov_rank": mark_rank,
                "memory_top1_source_id": mem_top,
                "markov_top1_source_id": mark_top,
                "memory_top1_position_error_m": float(np.linalg.norm(coords[mem_top] - coords[truth])),
                "markov_top1_position_error_m": float(np.linalg.norm(coords[mark_top] - coords[truth])),
                "memory_true_model_error": true_model_error(target, mem_models[truth], order, order),
                "markov_true_model_error": true_model_error(target, markov_models[truth], 1, order),
            }
            fold_records.append(rec)
            all_records.append(rec)

        mem_sum = summarize(fold_records, "memory")
        mark_sum = summarize(fold_records, "markov")
        pred_improve = (
            1.0 - mem_sum["median_true_model_prediction_error"]
            / max(mark_sum["median_true_model_prediction_error"], 1e-30)
        )
        result["folds"][str(heldout)] = {
            "reference_seeds": refs,
            "pca_components": int(components.shape[0]),
            "pca_raw_k95": int(raw_k95),
            "pca_retained_variance_fraction": retained_fraction,
            "selected_memory_order": order,
            "selected_memory_seconds": float(order * model_dt),
            "selected_memory_ridge": mem_lam,
            "selected_markov_ridge": markov_lam,
            "memory_reference_cv": mem_cv,
            "markov_reference_cv": markov_cv,
            "memory": mem_sum,
            "markov": mark_sum,
            "prediction_error_relative_improvement": float(pred_improve),
        }

    mem_all = summarize(all_records, "memory")
    mark_all = summarize(all_records, "markov")
    improved = np.mean([r["memory_rank"] < r["markov_rank"] for r in all_records])
    worsened = np.mean([r["memory_rank"] > r["markov_rank"] for r in all_records])
    top3_gain = mem_all["top3_rate"] - mark_all["top3_rate"]
    if mark_all["mean_log_truth_rank"] <= 1e-15:
        log_rank_improve = 0.0
    else:
        log_rank_improve = (
            mark_all["mean_log_truth_rank"] - mem_all["mean_log_truth_rank"]
        ) / mark_all["mean_log_truth_rank"]

    checks = {
        "nontrivial_memory_all_folds": all(
            result["folds"][str(s)]["selected_memory_order"] > 1 for s in SEEDS
        ),
        "prediction_improvement_ge_10pct_all_folds": all(
            result["folds"][str(s)]["prediction_error_relative_improvement"] >= 0.10
            for s in SEEDS
        ),
        "top3_gain_ge_10pp": bool(top3_gain >= 0.10),
        "mean_log_rank_improvement_ge_20pct": bool(log_rank_improve >= 0.20),
        "rank_improved_gt_50pct": bool(improved > 0.50),
        "rank_worsened_lt_25pct": bool(worsened < 0.25),
        "no_fold_top10_collapse": all(
            result["folds"][str(s)]["memory"]["top10_rate"]
            >= result["folds"][str(s)]["markov"]["top10_rate"]
            for s in SEEDS
        ),
    }
    passed = all(checks.values())
    result["pooled"] = {
        "memory": mem_all,
        "markov": mark_all,
        "top3_rate_gain": float(top3_gain),
        "mean_log_rank_relative_improvement": float(log_rank_improve),
        "rank_improved_fraction": float(improved),
        "rank_worsened_fraction": float(worsened),
    }
    result["checks"] = checks
    result["decision"] = (
        "MZ_M0_PASS_MEMORY_IS_LOAD_BEARING"
        if passed else
        "MZ_M0_FAIL_STOP_MEMORY_MAINLINE"
    )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fields = list(all_records[0].keys())
    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_records)

    print(json.dumps({
        "decision": result["decision"],
        "source_count": len(rows),
        "tests": len(all_records),
        "memory_top3": mem_all["top3_rate"],
        "markov_top3": mark_all["top3_rate"],
        "top3_gain": top3_gain,
        "memory_median_rank": mem_all["median_truth_rank"],
        "markov_median_rank": mark_all["median_truth_rank"],
        "checks": checks,
        "out": str(args.out_json),
    }, indent=2))
    return 0 if passed else 10


if __name__ == "__main__":
    raise SystemExit(main())
