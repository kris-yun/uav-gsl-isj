#!/usr/bin/env python3
"""One-shot H03 gate for Time-Arrow Ordinal Response Likelihood (TAORL).

TAORL changes candidate-relative evidence before Bayesian accumulation.  It
compares within-window concentration ranks and profiles a hardware-bounded
first-order sensor time constant.  A reverse-time filter is the causal negative
control.  Source truth is opened only after every arm score is frozen.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata


OUTPUT_DT_S = 1.0
WINDOW_S = 30.0
TAU_GRID_S = (0.5, 1.0, 2.0, 4.0, 6.5)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_provider(path: Path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("taorl_provider", path)
    if spec is None or spec.loader is None:
        raise ImportError("TAORL_PROVIDER_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_candidates(path: Path) -> np.ndarray:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    points = np.asarray([[float(row["x"]), float(row["y"])] for row in rows], dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 2:
        raise ValueError("TAORL_BAD_CANDIDATE_SUPPORT")
    return points


def load_rows(sensor_path: Path, wind_path: Path) -> tuple[list[dict], np.ndarray, dict]:
    sensor = pd.read_csv(sensor_path)
    wind = pd.read_csv(wind_path)
    required_sensor = {"t_sim_s", "step", "x", "y", "measured_gas_ppm"}
    required_wind = {"t_sim_s", "step", "x", "y", "wind_u", "wind_v"}
    if not required_sensor.issubset(sensor) or not required_wind.issubset(wind):
        raise ValueError("TAORL_TRACE_COLUMNS")
    if len(sensor) != len(wind) or not np.allclose(sensor.t_sim_s, wind.t_sim_s):
        raise ValueError("TAORL_SENSOR_WIND_CLOCK_MISMATCH")
    native_dt = float(np.median(np.diff(sensor.t_sim_s.to_numpy(np.float64))))
    stride = int(round(OUTPUT_DT_S / native_dt))
    if stride < 1 or not math.isclose(stride * native_dt, OUTPUT_DT_S, abs_tol=1e-9):
        raise ValueError("TAORL_CANNOT_BIND_ONE_HZ")
    take = np.arange(stride - 1, len(sensor), stride, dtype=int)
    sensor = sensor.iloc[take].reset_index(drop=True)
    wind = wind.iloc[take].reset_index(drop=True)
    if len(sensor) < 2 * int(WINDOW_S / OUTPUT_DT_S):
        raise ValueError("TAORL_TRACE_TOO_SHORT")
    rows = [
        {
            "t_sim_s": float(s.t_sim_s),
            "stamp_ns": int(round(float(s.t_sim_s) * 1e9)),
            "pose_xy": [float(s.x), float(s.y)],
            "wind_uv": [float(w.wind_u), float(w.wind_v)],
        }
        for s, w in zip(sensor.itertuples(index=False), wind.itertuples(index=False))
    ]
    measured = sensor.measured_gas_ppm.to_numpy(np.float64)
    if not np.isfinite(measured).all() or np.any(measured < 0.0):
        raise ValueError("TAORL_BAD_MEASURED_SIGNAL")
    audit = {
        "native_samples": int(len(take) * stride),
        "one_hz_samples": int(len(take)),
        "native_dt_s": native_dt,
        "one_hz_selection": "last native sample in each non-overlapping one-second interval",
        "true_gas_column_read": False,
    }
    return rows, measured, audit


def instantaneous_response(rows: list[dict], candidates: np.ndarray,
                           parameter: dict, provider) -> np.ndarray:
    instant = dict(parameter)
    instant["tau_s"] = 1.0e-6
    return provider.predict_all(rows, candidates, instant, OUTPUT_DT_S)


def first_order(values: np.ndarray, tau_s: float, reverse: bool = False) -> np.ndarray:
    work = values[::-1] if reverse else values
    alpha = math.exp(-OUTPUT_DT_S / tau_s)
    state = np.zeros(work.shape[1], dtype=np.float64)
    out = np.empty_like(work)
    for index, value in enumerate(work):
        state = alpha * state + (1.0 - alpha) * value
        out[index] = state
    return out[::-1] if reverse else out


def ordinal_loss(measured: np.ndarray, predicted: np.ndarray,
                 window_samples: int | None) -> np.ndarray:
    if window_samples is None:
        slices = [slice(0, len(measured))]
    else:
        slices = [slice(start, min(start + window_samples, len(measured)))
                  for start in range(0, len(measured), window_samples)
                  if min(start + window_samples, len(measured)) - start >= 2]
    total = np.zeros(predicted.shape[1], dtype=np.float64)
    count = 0
    for window in slices:
        y = measured[window]
        x = predicted[window]
        m = rankdata(y, method="average") / len(y)
        e = rankdata(x, axis=0, method="average") / len(y)
        total += np.sum((e - m[:, None]) ** 2, axis=0)
        count += len(y)
    return total / count


def profiled_raw_loss(measured: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    centered_y = measured - measured.mean()
    centered_x = predicted - predicted.mean(axis=0, keepdims=True)
    scale = np.sum(centered_x * centered_y[:, None], axis=0) / (
        np.sum(centered_x * centered_x, axis=0) + 1.0e-15
    )
    scale = np.maximum(scale, 0.0)
    residual = centered_x * scale[None, :] - centered_y[:, None]
    return np.mean(residual * residual, axis=0)


def profile_dynamics(measured: np.ndarray, instant: np.ndarray,
                     reverse: bool) -> tuple[np.ndarray, np.ndarray]:
    losses = np.stack([
        ordinal_loss(measured, first_order(instant, tau, reverse=reverse),
                     int(round(WINDOW_S / OUTPUT_DT_S)))
        for tau in TAU_GRID_S
    ])
    best = np.argmin(losses, axis=0)
    return losses[best, np.arange(losses.shape[1])], np.asarray(TAU_GRID_S)[best]


def parse_truth(manifest_path: Path) -> tuple[float, float]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    match = re.search(r"sourcePosition_(-?\d+(?:\.\d+)?)_(-?\d+(?:\.\d+)?)_",
                      manifest["realization"])
    if not match:
        raise ValueError("TAORL_SOURCE_TRUTH_PARSE")
    return float(match.group(1)), float(match.group(2))


def evaluate(loss: np.ndarray, candidates: np.ndarray,
             truth_xy: tuple[float, float]) -> dict:
    truth = np.asarray(truth_xy, dtype=np.float64)
    truth_index = int(np.argmin(np.sum((candidates - truth) ** 2, axis=1)))
    order = np.argsort(loss, kind="stable")
    rank = int(np.flatnonzero(order == truth_index)[0]) + 1
    best = int(order[0])
    return {
        "true_rank": rank,
        "candidate_count": len(candidates),
        "normalized_true_rank": (rank - 1) / max(len(candidates) - 1, 1),
        "true_candidate_xy": candidates[truth_index].tolist(),
        "map_xy": candidates[best].tolist(),
        "map_error_m": float(np.linalg.norm(candidates[best] - truth)),
        "true_loss": float(loss[truth_index]),
        "best_loss": float(loss[best]),
    }


def selftest() -> None:
    latent = np.asarray([[0.0], [0.2], [0.8], [0.1], [0.0]])
    forward = first_order(latent, 1.0)
    reverse = first_order(latent, 1.0, reverse=True)
    if np.allclose(forward, reverse):
        raise AssertionError("TAORL_TIME_ARROW_SELFTEST")
    monotone = np.asarray([0.0, 2.0, 8.0, 1.0, 0.0])
    if not np.allclose(rankdata(latent[:, 0]), rankdata(monotone)):
        raise AssertionError("TAORL_MONOTONE_RANK_SELFTEST")
    print("TAORL_SELFTEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--sensor-trace", type=Path)
    parser.add_argument("--wind-trace", type=Path)
    parser.add_argument("--runtime-manifest", type=Path)
    parser.add_argument("--candidate-csv", type=Path)
    parser.add_argument("--loho-json", type=Path)
    parser.add_argument("--provider-py", type=Path)
    parser.add_argument("--prereg", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    required = (args.sensor_trace, args.wind_trace, args.runtime_manifest,
                args.candidate_csv, args.loho_json, args.provider_py,
                args.prereg, args.out)
    if any(path is None for path in required):
        parser.error("formal run requires every input and --out")
    if args.out.exists():
        raise FileExistsError("TAORL_REFUSE_OVERWRITE_FORMAL_RESULT")
    prereg = json.loads(args.prereg.read_text(encoding="utf-8"))
    if prereg.get("contract") != "TAORL_H03_SEED11_ONE_SHOT_V1":
        raise ValueError("TAORL_PREREG_CONTRACT")
    provider = import_provider(args.provider_py)
    rows, measured, trace_audit = load_rows(args.sensor_trace, args.wind_trace)
    candidates = read_candidates(args.candidate_csv)
    loho = json.loads(args.loho_json.read_text(encoding="utf-8"))
    parameter = next(fold["selected_parameter"] for fold in loho["folds"]
                     if fold["heldout_house"] == "H03")
    instant = instantaneous_response(rows, candidates, parameter, provider)

    # Freeze all candidate evidence without opening source truth.
    forward_loss, forward_tau = profile_dynamics(measured, instant, reverse=False)
    reverse_loss, reverse_tau = profile_dynamics(measured, instant, reverse=True)
    frozen = {
        "RAW_PROFILED_VALUE": profiled_raw_loss(measured, instant),
        "ICRA2026_GLOBAL_EDF": ordinal_loss(measured, instant, None),
        "TAORL_FORWARD_WINDOWED": forward_loss,
        "TAORL_REVERSE_TIME_CONTROL": reverse_loss,
    }
    truth_xy = parse_truth(args.runtime_manifest)
    results = {name: evaluate(loss, candidates, truth_xy) for name, loss in frozen.items()}
    proposed = results["TAORL_FORWARD_WINDOWED"]
    checks = {
        "top_decile": proposed["normalized_true_rank"] <= 0.10,
        "beats_raw_value_rank": proposed["true_rank"] < results["RAW_PROFILED_VALUE"]["true_rank"],
        "beats_icra_global_rank": proposed["true_rank"] < results["ICRA2026_GLOBAL_EDF"]["true_rank"],
        "beats_reverse_time_rank": proposed["true_rank"] < results["TAORL_REVERSE_TIME_CONTROL"]["true_rank"],
        "map_error_below_native_pmfs_8p58m": proposed["map_error_m"] < 8.58,
    }
    passed = all(checks.values())
    truth_index = int(np.argmin(np.sum((candidates - np.asarray(truth_xy)) ** 2, axis=1)))
    report = {
        "contract": prereg["contract"],
        "verdict": "TAORL_H03_DEVELOPMENT_GO" if passed else "TAORL_H03_NO_GO",
        "claim_boundary": prereg["claim_if_pass"] if passed else prereg["stop_rule"],
        "truth_read_after_all_arm_scores": True,
        "truth_xy_evaluator_only": list(truth_xy),
        "trace_audit": trace_audit,
        "hardware_bound_parameters": {
            "output_dt_s": OUTPUT_DT_S,
            "window_s": WINDOW_S,
            "tau_grid_s": list(TAU_GRID_S),
            "tau_upper_derivation": "T90<=15 s and first-order T90=tau*ln(10), hence tau<=6.514 s",
        },
        "provider_parameter_selected_without_H03": parameter,
        "checks": checks,
        "results": results,
        "profiled_tau_at_true_candidate_s": {
            "forward": float(forward_tau[truth_index]),
            "reverse": float(reverse_tau[truth_index]),
        },
        "input_hashes": {
            path.name: sha256(path) for path in (
                args.sensor_trace, args.wind_trace, args.runtime_manifest,
                args.candidate_csv, args.loho_json, args.provider_py, args.prereg,
            )
        },
        "script_sha256": sha256(Path(__file__)),
        "limitations": [
            "one development H03 trace only",
            "the provider is an H01/H02-selected analytic plume approximation",
            "a PASS would not establish cross-dataset or real-flight performance",
            "the 8.58 m PMFS comparison is contextual because this gate freezes the historical trajectory",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    print(json.dumps(checks, sort_keys=True))


if __name__ == "__main__":
    main()
