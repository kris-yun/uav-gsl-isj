#!/usr/bin/env python3
"""Independent G1A output and frozen-gate recomputation from saved arrays."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import trim_mean

MODELS = ("FULL", "BLOCK_PRODUCT", "MATCHED_BLOCK_DIAG", "DIAG_COV")
S, R, N = 168, 16, 200


def close(got: float, expected: float, label: str, tol: float = 1e-8) -> float:
    diff = abs(float(got)-float(expected))
    if diff > tol*max(1, abs(float(expected))):
        raise AssertionError(f"{label}: {got} != {expected}")
    return diff


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--science", type=Path, required=True)
    p.add_argument("--panel", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = json.loads((a.science / "JTD_G1A_RESULT.json").read_text(encoding="utf-8"))
    with a.panel.open(newline="", encoding="utf-8") as f:
        panel = list(csv.DictReader(f, delimiter="\t"))
    with (a.science / "JTD_G1A_SOURCE_SUMMARY.csv").open(newline="", encoding="utf-8") as f:
        source_csv = list(csv.DictReader(f))
    with (a.science / "JTD_G1A_TARGET_METRICS.csv").open(newline="", encoding="utf-8") as f:
        target_csv = list(csv.DictReader(f))
    assert len(panel) == S and len(source_csv) == S and len(target_csv) == 4*S*R
    with np.load(a.science / "JTD_G1A_COMPLETE_POSTERIORS.npz", allow_pickle=False) as z:
        lp = z["logpost"]
        posterior = z["posterior"]
        assert tuple(z["model_names"].tolist()) == MODELS
        assert z["source_ids"].tolist() == [x["source_id"] for x in panel]
    with np.load(a.science / "JTD_G1A_SCORE_ARRAYS.npz", allow_pickle=False) as z:
        nll = z["nll"]; rank = z["rank"]
        null_nll = z["null_nll"]; null_rank = z["null_rank"]
    assert lp.shape == posterior.shape == (4, S, R, S)
    assert nll.shape == rank.shape == (4, S, R)
    assert null_nll.shape == null_rank.shape == (N, S, R)
    assert np.isfinite(lp).all() and np.isfinite(nll).all() and np.isfinite(null_nll).all()
    assert np.allclose(np.exp(lp), posterior, atol=1e-15, rtol=1e-12)
    assert np.allclose(posterior.sum(axis=3), 1, atol=1e-10, rtol=0)
    truth_lp = lp[:, np.arange(S)[:, None], np.arange(R)[None, :], np.arange(S)[:, None]]
    assert np.allclose(-truth_lp, nll, atol=1e-8, rtol=1e-10)
    recalculated_rank = 1+np.sum(lp > truth_lp[:, :, :, None], axis=3)
    assert np.array_equal(recalculated_rank, rank)
    xy = np.array([[float(q["x_m"]), float(q["y_m"])] for q in panel])
    dist = np.linalg.norm(xy[:, None, :]-xy[None, :, :], axis=2)
    dist_no_self = dist.copy(); np.fill_diagonal(dist_no_self, np.inf)
    nearest = np.argmin(dist_no_self, axis=1)
    with (a.science / "JTD_G1A_FROZEN_NEAREST_NEIGHBORS.csv").open(newline="", encoding="utf-8") as f:
        nearest_rows = list(csv.DictReader(f))
    assert [int(q["nearest_index"]) for q in nearest_rows] == nearest.tolist()
    max_metric_diff = 0.0
    for mi, name in enumerate(MODELS):
        pred = posterior[mi]
        ptrue = pred[np.arange(S)[:, None], np.arange(R)[None, :], np.arange(S)[:, None]]
        brier = (pred*pred).sum(axis=2)-2*ptrue+1
        mass_05 = np.einsum("src,sc->sr", pred, dist <= .5+1e-12)
        mass_10 = np.einsum("src,sc->sr", pred, dist <= 1+1e-12)
        expected_distance = np.einsum("src,sc->sr", pred, dist)
        map_ix = pred.argmax(axis=2)
        map_error = dist[np.arange(S)[:, None], map_ix]
        nn_logodds = lp[mi, np.arange(S)[:, None], np.arange(R)[None, :], np.arange(S)[:, None]] - \
                     lp[mi, np.arange(S)[:, None], np.arange(R)[None, :], nearest[:, None]]
        observed = result["models"][name]
        metrics = {
            "mean_truth_nll": nll[mi].mean(), "mean_truth_rank": rank[mi].mean(),
            "top1": (rank[mi] == 1).mean(), "top3": (rank[mi] <= 3).mean(),
            "top5": (rank[mi] <= 5).mean(), "mean_brier": brier.mean(),
            "mean_mass_0p5m": mass_05.mean(), "mean_mass_1p0m": mass_10.mean(),
            "mean_expected_distance_m": expected_distance.mean(),
            "mean_map_distance_error_m": map_error.mean(),
            "nearest_neighbor_confusion_rate": (map_ix == nearest[:, None]).mean(),
            "mean_truth_vs_nearest_logodds": nn_logodds.mean(),
        }
        for key, value in metrics.items():
            max_metric_diff = max(max_metric_diff, close(value, observed[key], f"{name}.{key}"))
        rows = target_csv[mi*S*R:(mi+1)*S*R]
        assert all(q["model"] == name for q in rows)
        for row in rows:
            s, r = int(row["source_index"]), int(row["realization_index"])
            assert row["source_id"] == panel[s]["source_id"]
            close(float(row["truth_nll"]), nll[mi, s, r], "target truth_nll")
            assert int(row["truth_rank"]) == int(rank[mi, s, r])
            close(float(row["brier"]), brier[s, r], "target brier")
            close(float(row["posterior_mass_0p5m"]), mass_05[s, r], "target mass_0p5m")
            close(float(row["posterior_mass_1p0m"]), mass_10[s, r], "target mass_1p0m")
            close(float(row["posterior_expected_distance_m"]), expected_distance[s, r], "target expected_distance")
            close(float(row["map_distance_error_m"]), map_error[s, r], "target map_error")
            close(float(row["truth_vs_nearest_logodds"]), nn_logodds[s, r], "target nn_logodds")
    bp = nll[1]-nll[0]; mbd = nll[2]-nll[0]
    src_bp, src_mbd = bp.mean(axis=1), mbd.mean(axis=1)
    for s, row in enumerate(source_csv):
        assert row["source_id"] == panel[s]["source_id"]
        close(float(row["mean_delta_bp"]), src_bp[s], "source delta_bp")
        close(float(row["mean_delta_mbd"]), src_mbd[s], "source delta_mbd")
    with np.load(a.science / "JTD_G1A_BOOTSTRAP_5000.npz", allow_pickle=False) as z:
        boot_bp, boot_mbd = z["bp"], z["mbd"]
    rng = np.random.default_rng(2026092502)
    draw_ix = rng.integers(0, S, size=(5000, S))
    assert np.array_equal(boot_bp, src_bp[draw_ix].mean(axis=1))
    assert np.array_equal(boot_mbd, src_mbd[draw_ix].mean(axis=1))
    ci_bp, ci_mbd = np.quantile(boot_bp, (.025, .975)), np.quantile(boot_mbd, (.025, .975))
    for name, delta, src, ci in (("delta_bp", bp, src_bp, ci_bp), ("delta_mbd", mbd, src_mbd, ci_mbd)):
        observed = result[name]
        close(observed["source_panel_mean"], src.mean(), name+" mean")
        assert int(observed["positive_source_count"]) == int((src > 0).sum())
        assert np.allclose(observed["source_sensitivity_ci_95"], ci, atol=1e-12)
        close(observed["trimmed_20_mean"], trim_mean(delta.ravel(), .2), name+" trim")
        flat = delta.ravel()
        positive_sorted = np.flatnonzero(flat > 0)
        positive_sorted = positive_sorted[np.argsort(flat[positive_sorted])[::-1]]
        for percent in (1, 5):
            removed = positive_sorted[:math.ceil(len(flat)*percent/100)]
            close(observed[f"remove_top_positive_{percent}pct_mean"], np.delete(flat, removed).mean(), name+" tail")
    null_aggregate = null_nll.mean(axis=(1, 2))
    assert np.allclose(null_aggregate, [float(q["aggregate_mean_truth_nll"]) for q in csv.DictReader(
        (a.science / "JTD_G1A_SHUFFLED_NULL_SUMMARY.csv").open(encoding="utf-8"))])
    continuity = np.median(null_nll, axis=0)-nll[0]
    close(result["shuffled_continuity"]["mean_targetwise_full_vs_median_null_delta"], continuity.mean(), "null delta")
    close(result["shuffled_continuity"]["trimmed_20_targetwise_delta"], trim_mean(continuity.ravel(), .2), "null trim")
    m = result["models"]
    f, b = m["FULL"], m["BLOCK_PRODUCT"]
    improvement = [b["mean_brier"]-f["mean_brier"], f["mean_mass_1p0m"]-b["mean_mass_1p0m"],
                   b["mean_expected_distance_m"]-f["mean_expected_distance_m"]]
    baseline = [b["mean_brier"], b["mean_mass_1p0m"], b["mean_expected_distance_m"]]
    g1 = bool(src_bp.mean() > 0 and ci_bp[0] > 0)
    g2 = bool(src_mbd.mean() > 0 and ci_mbd[0] > 0)
    g3 = bool((src_bp > 0).sum() >= math.ceil(.6*S) and (src_mbd > 0).sum() >= math.ceil(.6*S))
    bp_flat = bp.ravel(); order = np.flatnonzero(bp_flat > 0)
    order = order[np.argsort(bp_flat[order])[::-1]]
    g4 = bool(trim_mean(bp_flat, .2) > 0 and np.delete(bp_flat, order[:math.ceil(.05*len(bp_flat))]).mean() > 0)
    g5 = bool(nll[0].mean() < np.median(null_aggregate))
    g6 = bool(any(v > 0 for v in improvement) and all((-v)/abs(base) <= .05 for v, base in zip(improvement, baseline)))
    gates = {f"G{i}": flag for i, flag in enumerate((g1,g2,g3,g4,g5,g6), 1)}
    assert gates == result["gates"]
    decision = ("JTD_G1A_GO_DENSE_PROBABILISTIC_UTILITY_AND_CROSSBLOCK_CONTRIBUTION" if all(gates.values()) else
                "JTD_G1A_HOLD_SCORE_UTILITY_TRADEOFF" if all((g1,g2,g3,g4,g5)) else
                "JTD_G1A_STOP_DENSE_UTILITY_OR_MECHANISM_NOT_CONFIRMED")
    assert decision == result["decision"]
    output = {"independent_recomputation": "PASS", "decision": decision, "gates": gates,
              "source_count": S, "target_count": S*R, "posterior_rows_checked": 4*S*R,
              "source_rows_checked": S, "null_aggregate_count": N,
              "delta_bp": float(src_bp.mean()), "delta_mbd": float(src_mbd.mean()),
              "ci_bp": ci_bp.tolist(), "ci_mbd": ci_mbd.tolist(),
              "positive_sources_bp": int((src_bp > 0).sum()), "positive_sources_mbd": int((src_mbd > 0).sum()),
              "max_aggregate_metric_abs_diff": max_metric_diff,
              "calculation_boundary": "Recomputed from saved complete posteriors and null scores; model refits audited separately."}
    a.out.write_bytes((json.dumps(output, indent=2, sort_keys=True)+"\n").encode("utf-8"))
    print("JTD_G1A_INDEPENDENT_RECOMPUTATION_PASS", decision)


if __name__ == "__main__":
    main()
