#!/usr/bin/env python3
"""Frozen performance evaluator for the CSTAR seed12 cross-House screen.

Primary metric: 240 s localization-error AUC (lower is better).

Revision 2026-09-06:
- never sort/repair malformed source-estimate traces;
- never back-fill an estimate into time before that estimate existed;
- require an explicit available estimate at t=0 and a terminal row at t=240;
- integrate by causal zero-order hold from each estimate to the next estimate;
- reject unavailable/malformed/conflicting rows instead of rewarding missing data.
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
TOL = 1.0e-9


def parse_bool(value: str, label: str) -> bool:
    v = str(value).strip().lower()
    if v in ("true", "1"):
        return True
    if v in ("false", "0"):
        return False
    raise RuntimeError(f"CSTAR_BAD_BOOLEAN:{label}:{value}")


def validate_case_audit(path: Path, house: str, arm: str, seed: int) -> dict:
    if not path.is_file():
        raise RuntimeError(f"CSTAR_CASE_AUDIT_MISSING:{path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    required = [
        "contract", "house", "arm", "seed", "terminal_ok",
        "sim_start_s", "sim_end_s", "git_sha",
    ]
    missing = [k for k in required if k not in obj]
    if missing:
        raise RuntimeError(f"CSTAR_CASE_AUDIT_FIELDS_MISSING:{path}:{','.join(missing)}")
    if obj["contract"] != "CSTAR_CASE_AUDIT_V1":
        raise RuntimeError(f"CSTAR_CASE_AUDIT_CONTRACT:{path}:{obj['contract']}")
    if obj["house"] != house or obj["arm"] != arm or obj["seed"] != seed:
        raise RuntimeError(f"CSTAR_CASE_AUDIT_IDENTITY:{path}")
    if obj["terminal_ok"] is not True:
        raise RuntimeError(f"CSTAR_CASE_NOT_TERMINAL_OK:{path}")
    start = float(obj["sim_start_s"]); end = float(obj["sim_end_s"])
    if not math.isfinite(start) or not math.isfinite(end):
        raise RuntimeError(f"CSTAR_CASE_BAD_SIM_TIME:{path}")
    if abs(start) > TOL:
        raise RuntimeError(f"CSTAR_CASE_SIM_START_NOT_ZERO:{path}:{start}")
    if end + TOL < HORIZON_S:
        raise RuntimeError(f"CSTAR_CASE_SIM_END_BEFORE_HORIZON:{path}:{end}")
    return obj


def metrics(path: Path, house: str) -> dict:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise RuntimeError(f"CSTAR_SOURCE_TRACE_EMPTY_HEADER:{path}")
        required = {"sim_time", "estimate_available", "estimate_x", "estimate_y"}
        missing = sorted(required - set(reader.fieldnames))
        if missing:
            raise RuntimeError(f"CSTAR_SOURCE_TRACE_MISSING_COLUMNS:{path}:{','.join(missing)}")
        rows = list(reader)
    if not rows:
        raise RuntimeError(f"CSTAR_NO_SOURCE_ESTIMATE_ROWS:{path}")

    gx, gy = GT[house]
    points: list[tuple[float, float]] = []
    last_t = None
    for line_no, row in enumerate(rows, start=2):
        try:
            t = float(row["sim_time"])
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"CSTAR_SOURCE_TRACE_BAD_TIME:{path}:{line_no}") from exc
        if not math.isfinite(t):
            raise RuntimeError(f"CSTAR_SOURCE_TRACE_NONFINITE_TIME:{path}:{line_no}")
        if last_t is not None:
            if abs(t - last_t) <= TOL:
                raise RuntimeError(f"CSTAR_SOURCE_TRACE_DUPLICATE_TIME:{path}:{line_no}:{t}")
            if t < last_t:
                raise RuntimeError(f"CSTAR_SOURCE_TRACE_OUT_OF_ORDER:{path}:{line_no}:{t}:{last_t}")
        last_t = t
        available = parse_bool(row["estimate_available"], f"{path}:{line_no}:estimate_available")
        if not available:
            raise RuntimeError(f"CSTAR_SOURCE_TRACE_ESTIMATE_UNAVAILABLE:{path}:{line_no}:{t}")
        try:
            x = float(row["estimate_x"]); y = float(row["estimate_y"])
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"CSTAR_SOURCE_TRACE_BAD_ESTIMATE:{path}:{line_no}") from exc
        if not all(map(math.isfinite, (x, y))):
            raise RuntimeError(f"CSTAR_SOURCE_TRACE_NONFINITE_ESTIMATE:{path}:{line_no}")
        if t < -TOL:
            raise RuntimeError(f"CSTAR_SOURCE_TRACE_NEGATIVE_TIME:{path}:{line_no}:{t}")
        if t <= HORIZON_S + TOL:
            points.append((min(max(t, 0.0), HORIZON_S), math.hypot(x - gx, y - gy)))

    if not points:
        raise RuntimeError(f"CSTAR_NO_SOURCE_ESTIMATE_IN_HORIZON:{path}")
    if abs(points[0][0]) > TOL:
        raise RuntimeError(f"CSTAR_SOURCE_TRACE_MISSING_T0_ESTIMATE:{path}:{points[0][0]}")
    if abs(points[-1][0] - HORIZON_S) > TOL:
        raise RuntimeError(f"CSTAR_SOURCE_TRACE_MISSING_T240_ESTIMATE:{path}:{points[-1][0]}")

    t = np.asarray([p[0] for p in points], dtype=np.float64)
    error = np.asarray([p[1] for p in points], dtype=np.float64)
    dt = np.diff(t)
    if np.any(dt <= 0.0):
        raise RuntimeError(f"CSTAR_SOURCE_TRACE_NONPOSITIVE_INTERVAL:{path}")
    # Causal zero-order hold: estimate at t_i owns [t_i, t_{i+1}).
    # No future estimate contributes to earlier time.
    auc = float(np.sum(error[:-1] * dt))
    reached = np.flatnonzero(error <= 2.0)
    return {
        "final_error_m": float(error[-1]),
        "error_auc_m_s": auc,
        "time_to_2m_s": float(t[reached[0]]) if reached.size else HORIZON_S,
        "estimate_points": int(error.size),
        "trace_start_s": float(t[0]),
        "trace_end_s": float(t[-1]),
        "auc_interpolation": "causal_zero_order_hold_no_backward_fill",
        "estimate_coverage_fraction": 1.0,
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
            case_dir = args.run_root / f"{house}_seed{args.seed}_{arm}"
            validate_case_audit(case_dir / "CSTAR_CASE_AUDIT.json", house, arm, args.seed)
            path = case_dir / "source_estimate_trace.csv"
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
        "revision": "CAUSAL_AUC_NO_BACKWARD_FILL_20260906",
        "scope": "development one-seed cross-House screen; not final multi-seed paper proof",
        "seed": args.seed,
        "houses": list(GT),
        "arms": list(ARMS),
        "primary_metric": "240s localization error AUC m*s lower-is-better",
        "trace_acceptance": "strict t=0 and t=240 available estimates; no malformed/unavailable rows",
        "auc_interpolation": "causal zero-order hold from current estimate only",
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
