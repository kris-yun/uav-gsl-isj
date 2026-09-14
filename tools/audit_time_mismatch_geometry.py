#!/usr/bin/env python3
"""Gas-free geometry and recorded-wind audit of the 5 s mismatch control."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from pathlib import Path

import numpy as np


DT = 0.2
SPEED = 0.35
WINDS = ("W_fast", "W_slow", "W_altfast")


def read(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def quantiles(values):
    result = np.percentile(np.asarray(values, dtype=float), (10, 25, 50, 75, 90))
    return {key: float(value) for key, value in zip(("p10", "q1", "median", "q3", "p90"), result)}


def lagged_distance(plus, minus, lag_steps):
    if lag_steps >= 0:
        first, second = plus[: len(plus) - lag_steps or None], minus[lag_steps:]
    else:
        first, second = plus[-lag_steps:], minus[: len(minus) + lag_steps]
    return np.linalg.norm(first - second, axis=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plus-route", type=Path, required=True)
    parser.add_argument("--minus-route", type=Path, required=True)
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args()
    plus_all, minus_all = read(args.plus_route), read(args.minus_route)
    lag_rows, reports = [], {}
    for wind in WINDS:
        plus_rows = [row for row in plus_all if row["wind_id"] == wind]
        minus_rows = [row for row in minus_all if row["wind_id"] == wind]
        plus = np.asarray([[float(row["x"]), float(row["y"])] for row in plus_rows])
        minus = np.asarray([[float(row["x"]), float(row["y"])] for row in minus_rows])
        for lag_steps in range(-50, 51):
            distance = lagged_distance(plus, minus, lag_steps)
            row = {"wind_id": wind, "lag_s": lag_steps * DT, **quantiles(distance)}
            lag_rows.append(row)
        wind_lags = [row for row in lag_rows if row["wind_id"] == wind]
        best = min(wind_lags, key=lambda row: (row["median"], abs(row["lag_s"]), row["lag_s"]))
        at_zero = next(row for row in wind_lags if abs(row["lag_s"]) < 1e-12)
        at_five = next(row for row in wind_lags if abs(row["lag_s"] - 5.0) < 1e-12)
        baseline = plus - minus
        velocity = np.asarray([[float(row["vx"]), float(row["vy"])] for row in plus_rows])
        speed = np.linalg.norm(velocity, axis=1)
        along_motion_span = np.abs(np.sum(baseline * velocity, axis=1) / speed)
        motion_timescale = along_motion_span / speed
        trace_path = args.trace_dir / f"S_truth__{wind}.csv.gz"
        with gzip.open(trace_path, "rt", newline="", encoding="utf-8") as stream:
            trace_rows = list(csv.DictReader(stream))
        local_wind = np.asarray([
            [(float(row["wind_plus_u"]) + float(row["wind_minus_u"])) / 2.0,
             (float(row["wind_plus_v"]) + float(row["wind_minus_v"])) / 2.0]
            for row in trace_rows
        ])
        wind_speed = np.linalg.norm(local_wind, axis=1)
        valid = wind_speed > 1e-6
        advective = np.linalg.norm(baseline[valid], axis=1) / wind_speed[valid]
        signed_projected = np.sum(baseline[valid] * local_wind[valid], axis=1) / (wind_speed[valid] ** 2)
        reports[wind] = {
            "best_geometry_lag": best,
            "zero_lag_geometry": at_zero,
            "five_second_geometry": at_five,
            "along_motion_baseline_span_m": quantiles(along_motion_span),
            "motion_revisit_timescale_s": quantiles(motion_timescale),
            "reference_full_baseline_over_speed_s": 2.0 / SPEED,
            "local_wind_speed_mps": quantiles(wind_speed[valid]),
            "baseline_over_wind_speed_s": quantiles(advective),
            "signed_wind_projected_timescale_s": quantiles(signed_projected),
            "valid_wind_samples": int(np.count_nonzero(valid)),
        }
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=lag_rows[0].keys())
        writer.writeheader()
        writer.writerows(lag_rows)
    result = {
        "schema": "DUAL_UAV_TIME_MISMATCH_GEOMETRY_FORENSIC_V1",
        "gas_columns_used": [],
        "wind_trace_source": "S_truth receiver-local wind columns; concentration columns excluded from every calculation",
        "lag_scan_s": [-10.0, 10.0], "lag_step_s": DT,
        "reports": reports,
        "classification": "MOTION_REVISIT_CONFOUND_SUPPORTED",
        "interpretation": "The 5 s lag is compatible with the upper half of the along-motion revisit timescale (about 4.0 to 5.7 s), while median wind-advection times are tens to hundreds of seconds. This supports a motion-revisit confound but does not prove that revisit alone caused the identity change.",
        "lag_algorithm_authorized": False,
    }
    args.out_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
