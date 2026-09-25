#!/usr/bin/env python3
"""Independent B1 CSV/panel-score replay, including G0 K=12 parity."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import trim_mean

DEPTHS = (3, 4, 6, 8, 10, 12)
FOLDS = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def close(a: float, b: float, field: str) -> None:
    if not np.isclose(a, b, atol=1e-9, rtol=0):
        raise ValueError(f"independent B1 mismatch {field}: {a}, {b}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--g0-full-csv", type=Path, required=True)
    parser.add_argument("--g0-null-csv", type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    result = json.loads((out / "JTD_B1_RESULT.json").read_text(encoding="utf-8"))
    lock = json.loads((out / "JTD_B1_SUBPANEL_LOCK.json").read_text(encoding="utf-8"))
    targets = rows(out / "JTD_B1_TARGETS.csv")
    panels = rows(out / "JTD_B1_FOLD_SUBPANELS.csv")
    source_rows = rows(out / "JTD_B1_SOURCES_BY_DEPTH.csv")
    if len(targets) != 4*(3*5+1)*18*4 or len(panels) != 64 or len(source_rows) != 6*18:
        raise ValueError("B1 output cardinality drift")
    locked = {(p["depth"], p["fold"], p["subpanel"]): p for p in lock["panels"]}
    if len(locked) != 64:
        raise ValueError("subpanel lock cardinality drift")
    for p in panels:
        depth, fold, panel = (int(p[k]) for k in ("depth", "fold", "subpanel"))
        frozen = locked[(depth, fold, panel)]
        if p["reference_replicates_zero_based"] != ",".join(map(str, frozen["references_zero_based"])):
            raise ValueError("reference subpanel drift")
        if p["target_replicates_zero_based"] != ",".join(map(str, FOLDS[fold])):
            raise ValueError("target fold drift")
    for p in lock["panels"]:
        depth, fold, panel = (p[k] for k in ("depth", "fold", "subpanel"))
        path = out / "panels" / f"F{fold}_K{depth:02d}_P{panel}.npz"
        with np.load(path, allow_pickle=False) as z:
            full = z["full_nll"]
            null = z["null_nll"]
            ranks = z["full_rank"]
            if full.shape != (18, 4) or null.shape != (200, 18, 4):
                raise ValueError("panel score shape drift")
            panel_targets = [r for r in targets if (int(r["depth"]), int(r["fold"]), int(r["subpanel"])) ==
                             (depth, fold, panel)]
            if len(panel_targets) != 72:
                raise ValueError("target panel rows drift")
            for row in panel_targets:
                s = int(row["source_index"])
                rep = int(row["realization_index"])
                pos = FOLDS[fold].index(rep)
                close(float(row["full_truth_nll"]), float(full[s, pos]), "panel FULL")
                close(float(row["shuffled_median_truth_nll"]),
                      float(np.median(null[:, s, pos])), "panel null median")
                close(float(row["delta_nll"]),
                      float(np.median(null[:, s, pos]) - full[s, pos]), "panel delta")
                if int(row["full_truth_rank"]) != int(ranks[s, pos]):
                    raise ValueError("panel truth rank mismatch")
            mean_delta = float(np.mean(np.median(null, axis=0)-full))
            csv_panel = next(r for r in panels if (int(r["depth"]), int(r["fold"]), int(r["subpanel"])) ==
                             (depth, fold, panel))
            close(mean_delta, float(csv_panel["mean_delta_nll"]), "panel mean")
    verified_depths = {}
    for depth in DEPTHS:
        count = 1 if depth == 12 else 3
        delta = np.full((18, 16, count), np.nan)
        full = np.full_like(delta, np.nan)
        null = np.full_like(delta, np.nan)
        rank = np.full_like(delta, np.nan)
        top3 = np.full_like(delta, np.nan)
        for row in targets:
            if int(row["depth"]) != depth:
                continue
            s, rep, panel = (int(row[k]) for k in ("source_index", "realization_index", "subpanel"))
            if not np.isnan(delta[s, rep, panel]):
                raise ValueError("duplicate B1 target-panel row")
            delta[s, rep, panel] = float(row["delta_nll"])
            full[s, rep, panel] = float(row["full_truth_nll"])
            null[s, rep, panel] = float(row["shuffled_median_truth_nll"])
            rank[s, rep, panel] = float(row["full_truth_rank"])
            top3[s, rep, panel] = float(row["full_top3"])
        if any(not np.isfinite(arr).all() for arr in (delta, full, null, rank, top3)):
            raise ValueError(f"incomplete B1 K={depth} target cube")
        rng = np.random.default_rng(2026092502)
        boot = []
        for _ in range(5000):
            sources = rng.integers(0, 18, 18)
            reps = rng.integers(0, 16, (18, 16))
            sampled = [delta[int(sources[i]), int(reps[i, j]), p]
                       for i in range(18) for j in range(16) for p in range(count)]
            boot.append(float(np.mean(sampled)))
        ci = np.quantile(boot, (0.025, 0.975))
        flat = delta.ravel()
        positives = sorted((float(v) for v in flat if v > 0), reverse=True)
        removed = positives[:math.ceil(0.05*len(flat))]
        retained = list(float(v) for v in flat)
        for value in removed:
            retained.remove(value)
        mean_by_source = delta.mean(axis=(1, 2))
        panel_means = [float(r["mean_delta_nll"]) for r in panels if int(r["depth"]) == depth]
        relative = float((null.mean()-full.mean())/null.mean())
        gates = {"R1": bool(ci[0] > 0), "R2": bool(all(v > 0 for v in panel_means)),
                 "R3": bool(sum(v > 0 for v in mean_by_source) >= 14),
                 "R4": bool(trim_mean(flat, 0.2) > 0),
                 "R5": bool(np.mean(retained) > 0),
                 "R6": bool(relative >= 0.10)}
        expected = result["depths"][str(depth)]
        if gates != expected["gates"] or bool(all(gates.values())) != expected["reliable"]:
            raise ValueError(f"K={depth} reliability gate mismatch")
        comparisons = {"mean_delta_nll": float(flat.mean()),
                       "median_delta_nll": float(np.median(flat)),
                       "trimmed_20_mean_delta_nll": float(trim_mean(flat, 0.2)),
                       "relative_mean_nll_improvement": relative,
                       "g5_retained_mean_delta_nll": float(np.mean(retained)),
                       "full_mean_nll": float(full.mean()),
                       "full_truth_nll_p95": float(np.quantile(full, 0.95)),
                       "full_truth_nll_p99": float(np.quantile(full, 0.99)),
                       "shuffled_target_median_mean_nll": float(null.mean()),
                       "full_mean_truth_rank": float(rank.mean()),
                       "full_top3_fraction": float(top3.mean()),
                       "minimum_fold_subpanel_mean_delta_nll": float(min(panel_means))}
        for key, value in comparisons.items():
            close(value, float(expected[key]), f"K={depth} {key}")
        if not np.allclose(ci, expected["bootstrap_95_ci"], atol=1e-9, rtol=0):
            raise ValueError(f"K={depth} bootstrap mismatch")
        if int(sum(mean_by_source > 0)) != expected["positive_source_count"]:
            raise ValueError(f"K={depth} source count mismatch")
        for source in range(18):
            entry = next(r for r in source_rows if int(r["depth"]) == depth and int(r["source_index"]) == source)
            close(float(entry["mean_delta_nll"]), float(mean_by_source[source]), "source mean")
        verified_depths[str(depth)] = {"gates": gates, "reliable": all(gates.values()),
                                       "bootstrap_95_ci": ci.tolist(), "metrics": comparisons}
    # Reconstruct K12 arrays from saved per-panel null NLL and compare the
    # independently archived G0 long-form scores, not just aggregate means.
    g0_full = np.full((18, 16), np.nan)
    g0_null = np.full((200, 18, 16), np.nan)
    for row in rows(args.g0_full_csv):
        g0_full[int(row["source_index"]), int(row["realization_index"])] = float(row["nll"])
    for row in rows(args.g0_null_csv):
        g0_null[int(row["shuffle"]), int(row["source_index"]), int(row["realization_index"])] = float(row["nll"])
    k12_full = np.full_like(g0_full, np.nan)
    k12_null = np.full_like(g0_null, np.nan)
    for fold, reps in enumerate(FOLDS):
        with np.load(out / "panels" / f"F{fold}_K12_P0.npz", allow_pickle=False) as z:
            for pos, rep in enumerate(reps):
                k12_full[:, rep] = z["full_nll"][:, pos]
                k12_null[:, :, rep] = z["null_nll"][:, :, pos]
    if any(not np.isfinite(a).all() for a in (g0_full, g0_null, k12_full, k12_null)):
        raise ValueError("G0/K12 parity incomplete")
    max_full = float(np.max(np.abs(k12_full-g0_full)))
    max_null = float(np.max(np.abs(k12_null-g0_null)))
    close(max_full, result["k12_g0_parity"]["full_nll_max_abs_diff"], "G0 FULL max diff")
    close(max_null, result["k12_g0_parity"]["null_nll_max_abs_diff"], "G0 NULL max diff")
    if not np.allclose(k12_full, g0_full, atol=1e-6, rtol=1e-8) or not np.allclose(k12_null, g0_null, atol=1e-6, rtol=1e-8):
        raise ValueError("K12 does not reproduce G0")
    reliable = [k for k in DEPTHS if verified_depths[str(k)]["reliable"]]
    k_min = min(reliable) if reliable else None
    decision = ("JTD_B1_FAIL_IMPLEMENTATION_OR_CONTRACT_DRIFT" if 12 not in reliable else
                "JTD_B1_PASS_REFERENCE_DEPTH_IDENTIFIED" if k_min is not None and k_min <= 10 else
                "JTD_B1_HOLD_REQUIRES_G0_DEPTH")
    if decision != result["decision"] or k_min != result["K_min"]:
        raise ValueError("final B1 decision/K_min mismatch")
    verification = {"independent_recomputation_pass": True, "decision": decision,
                    "K_min": k_min, "verified_depths": verified_depths,
                    "k12_full_nll_max_abs_diff": max_full,
                    "k12_null_nll_max_abs_diff": max_null,
                    "target_rows": len(targets), "panel_files": len(lock["panels"]),
                    "targets_csv_sha256": sha(out / "JTD_B1_TARGETS.csv"),
                    "subpanel_lock_sha256": sha(out / "JTD_B1_SUBPANEL_LOCK.json")}
    (out / "JTD_B1_INDEPENDENT_VERIFICATION.json").write_bytes(
        (json.dumps(verification, indent=2, sort_keys=True)+"\n").encode("utf-8"))
    print(decision, "K_min", k_min, "INDEPENDENT_VERIFICATION_PASS")


if __name__ == "__main__":
    main()
