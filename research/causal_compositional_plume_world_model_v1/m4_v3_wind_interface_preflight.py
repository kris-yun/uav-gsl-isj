#!/usr/bin/env python3
"""M4-v3 W0 wind-interface preflight.

This is a source-blind interface audit, not a plume/localization experiment.
Canonical contract: map-frame Cartesian DOWNWIND vector in m/s.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def wrap(a: float) -> float:
    return math.atan2(math.sin(a), math.cos(a))


def angle_error(a: float, b: float) -> float:
    return abs(wrap(a - b))


def vector(speed: float, direction_downwind_map: float):
    return (
        float(speed) * math.cos(direction_downwind_map),
        float(speed) * math.sin(direction_downwind_map),
    )


def cosine(a, b):
    an = math.hypot(*a)
    bn = math.hypot(*b)
    if an <= 0 or bn <= 0:
        return float("nan")
    return (a[0] * b[0] + a[1] * b[1]) / (an * bn)


def audit_vgr_trace(path: Path):
    n = 0
    max_angle = 0.0
    max_speed_err = 0.0
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            u = float(row["wind_u"])
            v = float(row["wind_v"])
            d = float(row["wind_direction_rad"])
            s = float(row["wind_speed"])
            max_angle = max(max_angle, angle_error(d, math.atan2(v, u)))
            max_speed_err = max(max_speed_err, abs(s - math.hypot(u, v)))
            n += 1
    if n == 0:
        raise ValueError("empty wind trace")
    return {
        "rows": n,
        "max_wrapped_angle_error_rad": max_angle,
        "max_speed_error_mps": max_speed_err,
        "contract": "trace direction is atan2(v,u): map-frame downwind",
        "pass": max_angle < 1e-3 and max_speed_err < 1e-3,
    }


def historical_semantic_conflict():
    # Four axis cases. Historical VGR publishes downwind angle directly.
    # GMRF-wind 2.0 subscriber treats that same angle as upwind and adds pi.
    cases = []
    for name, angle in (("+x", 0.0), ("+y", math.pi / 2),
                        ("-x", math.pi), ("-y", -math.pi / 2)):
        truth = vector(1.0, angle)
        pmfs = vector(1.0, angle)               # direct downwind use
        gmrf_sub = vector(1.0, wrap(angle + math.pi))  # erroneous second reversal
        cases.append({
            "case": name,
            "canonical_downwind": truth,
            "pmfs_interpretation": pmfs,
            "gmrf_subscriber_interpretation": gmrf_sub,
            "pmfs_cosine": cosine(pmfs, truth),
            "gmrf_subscriber_cosine": cosine(gmrf_sub, truth),
        })
    return {
        "cases": cases,
        "pmfs_all_aligned": all(x["pmfs_cosine"] > 0.999 for x in cases),
        "gmrf_subscriber_all_reversed": all(x["gmrf_subscriber_cosine"] < -0.999 for x in cases),
    }


def audit_observed_pairs(path: Path, min_cos: float, min_ratio: float, max_ratio: float):
    """CSV columns: in_u,in_v,out_u,out_v. For future W0 live/service fixtures."""
    rows = []
    with path.open(newline="") as f:
        for i, r in enumerate(csv.DictReader(f), 1):
            iv = (float(r["in_u"]), float(r["in_v"]))
            ov = (float(r["out_u"]), float(r["out_v"]))
            ni = math.hypot(*iv)
            no = math.hypot(*ov)
            c = cosine(iv, ov)
            ratio = no / ni if ni > 0 else float("nan")
            ok = (
                ni > 0 and math.isfinite(c) and c > min_cos
                and min_ratio <= ratio <= max_ratio
            )
            rows.append({"row": i, "cosine": c, "magnitude_ratio": ratio, "pass": ok})
    return {
        "rows": rows,
        "pass": bool(rows) and all(x["pass"] for x in rows),
        "thresholds": {
            "min_cosine": min_cos,
            "min_magnitude_ratio": min_ratio,
            "max_magnitude_ratio": max_ratio,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vgr-wind-trace", type=Path)
    ap.add_argument("--observed-pairs", type=Path)
    ap.add_argument("--min-cosine", type=float, default=0.95)
    ap.add_argument("--min-ratio", type=float, default=0.5)
    ap.add_argument("--max-ratio", type=float, default=1.5)
    args = ap.parse_args()

    result = {
        "canonical_contract": {
            "frame": "map",
            "direction": "downwind_flow_toward",
            "representation": "cartesian_u_v",
            "units": "m/s",
        },
        "historical_semantic_conflict": historical_semantic_conflict(),
    }
    if args.vgr_wind_trace:
        result["vgr_trace"] = audit_vgr_trace(args.vgr_wind_trace)
    if args.observed_pairs:
        result["w0_observed_cell_gate"] = audit_observed_pairs(
            args.observed_pairs, args.min_cosine, args.min_ratio, args.max_ratio
        )

    mandatory = [
        result["historical_semantic_conflict"]["pmfs_all_aligned"],
        result["historical_semantic_conflict"]["gmrf_subscriber_all_reversed"],
    ]
    if "vgr_trace" in result:
        mandatory.append(result["vgr_trace"]["pass"])
    if "w0_observed_cell_gate" in result:
        mandatory.append(result["w0_observed_cell_gate"]["pass"])
    result["pass"] = all(mandatory)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["pass"] else 2)


if __name__ == "__main__":
    main()
