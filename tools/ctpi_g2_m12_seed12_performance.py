#!/usr/bin/env python3
"""Post-run evaluation for the frozen three-House seed-12 M1/M2 screen."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


GT = {"H01": (-0.40, -2.90), "H02": (0.0, -1.0), "H03": (-0.45, 1.90)}
ARMS = ("A0", "F00", "F01")
COMPARISONS = (
    ("A0", "F00", "M1_F00_vs_A0"),
    ("F00", "F01", "M2_F01_vs_F00"),
    ("A0", "F01", "M1_M2_F01_vs_A0"),
)
TOL = 1.0e-12


def metrics(path: Path, house: str, horizon: float = 240.0) -> dict[str, float | int]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    gx, gy = GT[house]
    points = []
    for row in rows:
        try:
            if row.get("estimate_available", "true").lower() not in ("true", "1"):
                continue
            t = float(row["sim_time"])
            x = float(row["estimate_x"])
            y = float(row["estimate_y"])
        except (KeyError, ValueError):
            continue
        if all(map(math.isfinite, (t, x, y))) and -TOL <= t <= horizon + TOL:
            points.append((min(max(t, 0.0), horizon), math.hypot(x - gx, y - gy)))
    if not points:
        raise RuntimeError(f"CTPI_G2_M12_NO_ESTIMATE:{path}")
    points.sort()
    unique = []
    for item in points:
        if unique and abs(item[0] - unique[-1][0]) <= TOL:
            unique[-1] = item
        else:
            unique.append(item)
    t = np.asarray([p[0] for p in unique], dtype=np.float64)
    error = np.asarray([p[1] for p in unique], dtype=np.float64)
    t_aug = np.concatenate([[0.0], t, [horizon]])
    e_aug = np.concatenate([[error[0]], error, [error[-1]]])
    auc = float(np.sum(0.5 * (e_aug[1:] + e_aug[:-1]) * np.diff(t_aug)))
    reached = np.flatnonzero(error <= 2.0)
    return {
        "final_error_m": float(error[-1]),
        "error_auc_m_s": auc,
        "time_to_2m_s": float(t[reached[0]]) if reached.size else horizon,
        "estimate_points": int(error.size),
    }


def comparison(records: list[dict], left: str, right: str) -> dict:
    result = {}
    for metric in ("error_auc_m_s", "final_error_m", "time_to_2m_s"):
        pairs = []
        for house in GT:
            lval = next(r[metric] for r in records if r["house"] == house and r["arm"] == left)
            rval = next(r[metric] for r in records if r["house"] == house and r["arm"] == right)
            pairs.append({
                "house": house,
                "left": lval,
                "right": rval,
                "delta": rval - lval,
                "improved": rval < lval - TOL,
                "worsened": rval > lval + TOL,
            })
        result[metric] = {
            "left_mean": float(np.mean([p["left"] for p in pairs])),
            "right_mean": float(np.mean([p["right"] for p in pairs])),
            "mean_delta": float(np.mean([p["delta"] for p in pairs])),
            "wins": sum(p["improved"] for p in pairs),
            "losses": sum(p["worsened"] for p in pairs),
            "ties": sum(not p["improved"] and not p["worsened"] for p in pairs),
            "pairs": pairs,
        }
    return result


def module_pass(comp: dict) -> bool:
    auc = comp["error_auc_m_s"]
    final = comp["final_error_m"]
    return auc["wins"] >= 2 and auc["mean_delta"] < 0.0 and final["losses"] < 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.seed != 12:
        raise RuntimeError("CTPI_G2_M12_SEED_MUST_BE_12")

    records = []
    for house in GT:
        for arm in ARMS:
            records.append({
                "house": house,
                "seed": args.seed,
                "arm": arm,
                **metrics(args.run_root / f"{house}_seed{args.seed}_{arm}/source_estimate_trace.csv", house),
            })
    comparisons = {label: comparison(records, left, right) for left, right, label in COMPARISONS}
    gates = {
        "M1_crosshouse_seed12_screen": module_pass(comparisons["M1_F00_vs_A0"]),
        "M2_crosshouse_seed12_screen": module_pass(comparisons["M2_F01_vs_F00"]),
    }
    passed = all(gates.values())
    report = {
        "contract": "CTPI_G2_M1_M2_SEED12_CROSSHOUSE_PERFORMANCE_V1",
        "seed": args.seed,
        "houses": list(GT),
        "arms": list(ARMS),
        "horizon_s": 240.0,
        "records": records,
        "comparisons": comparisons,
        "gates": gates,
        "pass": passed,
        "interpretation": "cross-House one-seed screen; not final multi-seed paper-level proof",
        "verdict": "CTPI_G2_M12_SEED12_SCREEN=PASS" if passed else "CTPI_G2_M12_SEED12_SCREEN=NO_GO",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["verdict"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
