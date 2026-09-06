#!/usr/bin/env python3
"""Frozen performance evaluator for the CSTAR seed12 cross-House screen.

This tool does not launch experiments and does not tune thresholds from outcomes.
Primary metric: 240 s localization error AUC (lower is better).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

GT = {"H01": (-0.40, -2.90), "H02": (0.0, -1.0), "H03": (-0.45, 1.90)}
ARMS = ("A0", "F00", "F10", "F11")
COMPARISONS = (
    ("A0", "F00", "M1_PICR_INCREMENT"),
    ("F00", "F10", "M3_PHS_INCREMENT"),
    ("F10", "F11", "M2_CPO_INCREMENT"),
    ("A0", "F11", "FULL_CSTAR_INCREMENT"),
)
HORIZON_S = 240.0
TOL = 1.0e-12


def metrics(path: Path, house: str) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    gx, gy = GT[house]
    points: list[tuple[float, float]] = []
    for row in rows:
        try:
            if row.get("estimate_available", "true").lower() not in ("true", "1"):
                continue
            t = float(row["sim_time"])
            x = float(row["estimate_x"])
            y = float(row["estimate_y"])
        except (KeyError, TypeError, ValueError):
            continue
        if all(map(math.isfinite, (t, x, y))) and -TOL <= t <= HORIZON_S + TOL:
            points.append((min(max(t, 0.0), HORIZON_S), math.hypot(x - gx, y - gy)))
    if not points:
        raise RuntimeError(f"CSTAR_NO_SOURCE_ESTIMATE:{path}")
    points.sort()
    unique: list[tuple[float, float]] = []
    for item in points:
        if unique and abs(item[0] - unique[-1][0]) <= TOL:
            unique[-1] = item
        else:
            unique.append(item)
    t = np.asarray([p[0] for p in unique], dtype=np.float64)
    error = np.asarray([p[1] for p in unique], dtype=np.float64)
    t_aug = np.concatenate([[0.0], t, [HORIZON_S]])
    e_aug = np.concatenate([[error[0]], error, [error[-1]]])
    auc = float(np.sum(0.5 * (e_aug[1:] + e_aug[:-1]) * np.diff(t_aug)))
    reached = np.flatnonzero(error <= 2.0)
    return {
        "final_error_m": float(error[-1]),
        "error_auc_m_s": auc,
        "time_to_2m_s": float(t[reached[0]]) if reached.size else HORIZON_S,
        "estimate_points": int(error.size),
    }


def compare(records: list[dict], left: str, right: str) -> dict:
    pairs = []
    for house in GT:
        l = next(r for r in records if r["house"] == house and r["arm"] == left)
        r = next(r for r in records if r["house"] == house and r["arm"] == right)
        delta = r["error_auc_m_s"] - l["error_auc_m_s"]
        rel = delta / l["error_auc_m_s"] if l["error_auc_m_s"] > 0 else float("nan")
        pairs.append({
            "house": house,
            "left_auc": l["error_auc_m_s"],
            "right_auc": r["error_auc_m_s"],
            "delta_auc": delta,
            "relative_delta": rel,
            "improved": delta < -TOL,
            "worsened": delta > TOL,
            "left_final_error_m": l["final_error_m"],
            "right_final_error_m": r["final_error_m"],
        })
    left_mean = float(np.mean([p["left_auc"] for p in pairs]))
    right_mean = float(np.mean([p["right_auc"] for p in pairs]))
    return {
        "left": left,
        "right": right,
        "left_mean_auc": left_mean,
        "right_mean_auc": right_mean,
        "mean_delta_auc": right_mean - left_mean,
        "relative_mean_improvement": (left_mean - right_mean) / left_mean if left_mean > 0 else None,
        "wins": sum(p["improved"] for p in pairs),
        "losses": sum(p["worsened"] for p in pairs),
        "ties": sum(not p["improved"] and not p["worsened"] for p in pairs),
        "pairs": pairs,
    }


def incremental_pass(comp: dict) -> bool:
    # Development screen, not final multi-seed paper proof: require directional
    # cross-House support rather than one lucky House carrying the mean.
    return comp["wins"] >= 2 and comp["mean_delta_auc"] < 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.seed != 12:
        raise RuntimeError("CSTAR_DEVELOPMENT_SCREEN_SEED_MUST_BE_12")

    records = []
    for house in GT:
        for arm in ARMS:
            path = args.run_root / f"{house}_seed{args.seed}_{arm}" / "source_estimate_trace.csv"
            if not path.is_file():
                raise RuntimeError(f"CSTAR_MISSING_TRACE:{path}")
            records.append({"house": house, "seed": args.seed, "arm": arm, **metrics(path, house)})

    comparisons = {label: compare(records, left, right) for left, right, label in COMPARISONS}
    module_gates = {
        "M1_increment_directional": incremental_pass(comparisons["M1_PICR_INCREMENT"]),
        "M3_increment_directional": incremental_pass(comparisons["M3_PHS_INCREMENT"]),
        "M2_increment_directional": incremental_pass(comparisons["M2_CPO_INCREMENT"]),
    }
    full = comparisons["FULL_CSTAR_INCREMENT"]
    full_gate = bool(
        full["wins"] >= 2
        and full["mean_delta_auc"] < 0.0
        and (full["relative_mean_improvement"] or 0.0) >= 0.10
    )
    passed = all(module_gates.values()) and full_gate
    report = {
        "contract": "CSTAR_SEED12_CROSSHOUSE_PERFORMANCE_V1",
        "scope": "spent/development one-seed cross-House screen; not final multi-seed paper proof",
        "seed": args.seed,
        "houses": list(GT),
        "arms": list(ARMS),
        "primary_metric": "240s localization error AUC m*s lower-is-better",
        "records": records,
        "comparisons": comparisons,
        "module_gates": module_gates,
        "full_method_gate": {
            "requires_wins_at_least_2_of_3": full["wins"] >= 2,
            "requires_mean_auc_improvement": full["mean_delta_auc"] < 0.0,
            "requires_relative_mean_improvement_at_least_10pct": (full["relative_mean_improvement"] or 0.0) >= 0.10,
            "pass": full_gate,
        },
        "pass": passed,
        "verdict": "CSTAR_SEED12_CROSSHOUSE_SCREEN=PASS" if passed else "CSTAR_SEED12_CROSSHOUSE_SCREEN=NO_GO",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
