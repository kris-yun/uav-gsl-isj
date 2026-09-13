#!/usr/bin/env python3
"""One-shot LMBT premise test on a frozen single-channel trace.

The scoring path never reads true_gas_ppm or the source coordinates.  Source
truth is parsed only after all arm scores have been frozen in memory, for the
evaluator report.  Full CFD wind is explicitly an oracle diagnostic input.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


DT_S = 0.2
TAU_S = 1.2
DEAD_S = 0.4
THRESHOLD_PPM = 0.1
BACK_DT_S = 0.4
MAX_AGE_S = 80.0
BASE_SPREAD_M = 0.2
KAPPAS = (0.01, 0.03, 0.1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inverse_sensor(measured: np.ndarray, dt: float = DT_S,
                   tau: float = TAU_S) -> np.ndarray:
    """Invert the frozen equal-rise/recovery, zero-noise first-order state."""
    measured = np.asarray(measured, dtype=np.float64)
    if measured.ndim != 1 or measured.size == 0 or not np.isfinite(measured).all():
        raise ValueError("LMBT_BAD_MEASURED_SIGNAL")
    alpha = math.exp(-dt / tau)
    previous = np.r_[0.0, measured[:-1]]
    latent = (measured - alpha * previous) / (1.0 - alpha)
    # Tiny negative values arise from decimal CSV rounding.  Larger negatives
    # would invalidate the exact V1 sensor contract.
    if float(latent.min()) < -2.0e-4:
        raise ValueError(f"LMBT_SENSOR_INVERSE_NEGATIVE:{latent.min()}")
    return np.maximum(latent, 0.0)


def whiff_peaks(signal: np.ndarray, threshold: float = THRESHOLD_PPM) -> list[int]:
    above = np.asarray(signal) > threshold
    peaks: list[int] = []
    start = None
    for i, flag in enumerate(np.r_[above, False]):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            stop = i
            peaks.append(start + int(np.argmax(signal[start:stop])))
            start = None
    return peaks


@dataclass(frozen=True)
class Event:
    time_s: float
    trace_step: int
    xyz: tuple[float, float, float]
    local_wind_xyz: tuple[float, float, float]


@dataclass
class WindField:
    velocity: np.ndarray


@dataclass
class RuntimeWind:
    fields: dict[int, WindField]
    grid: object


@dataclass(frozen=True)
class WindSchedule:
    indices: tuple[int, ...]
    first_gaden_iteration: int

    def at(self, trace_step: int) -> int:
        if 1 <= trace_step <= len(self.indices):
            return self.indices[trace_step - 1]
        # Only pre-trace ages are needed. Before the replay seam, native fields
        # 1..10 were each held for two simulation frames.
        absolute_iteration = self.first_gaden_iteration + trace_step - 1
        return (absolute_iteration // 2) % 10 + 1


def load_runtime_wind(realization: Path, occupancy: Path,
                      environment_runtime_py: Path) -> RuntimeWind:
    spec = importlib.util.spec_from_file_location("lmbt_environment_runtime",
                                                  environment_runtime_py)
    if spec is None or spec.loader is None:
        raise ImportError("LMBT_ENVIRONMENT_RUNTIME_IMPORT")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    reader = module.NumericWindReader(realization, occupancy)
    if len(reader.files) != 11:
        raise ValueError("LMBT_EXPECTED_RUNTIME_WIND_FIELDS_0_TO_10")
    fields = {
        index: WindField(velocity=np.asarray(reader.vectors(index)[0], dtype=np.float64))
        for index in range(11)
    }
    return RuntimeWind(fields=fields, grid=reader.grid)


def query_velocity(runtime_wind: RuntimeWind, index: int,
                   xyz: np.ndarray) -> np.ndarray:
    flat_index = runtime_wind.grid.flat_index(tuple(map(float, xyz)))
    return np.asarray(runtime_wind.fields[index].velocity[flat_index], dtype=np.float64)


def load_events(trace_dir: Path, memory_on: bool) -> tuple[list[Event], dict]:
    sensor_path = trace_dir / "sensor_trace.csv"
    wind_path = trace_dir / "wind_trace.csv"
    sensor_cols = ["t_sim_s", "step", "x", "y", "z", "measured_gas_ppm"]
    wind_cols = ["t_sim_s", "step", "x", "y", "z", "wind_u", "wind_v", "wind_w"]
    sensor = pd.read_csv(sensor_path, usecols=sensor_cols)
    wind = pd.read_csv(wind_path, usecols=wind_cols)
    if len(sensor) != len(wind) or not np.allclose(sensor.t_sim_s, wind.t_sim_s):
        raise ValueError("LMBT_SENSOR_WIND_CLOCK_MISMATCH")

    measured = sensor.measured_gas_ppm.to_numpy(np.float64)
    if memory_on:
        signal = inverse_sensor(measured)
        event_times = sensor.t_sim_s.to_numpy(np.float64) - DEAD_S
    else:
        signal = measured
        event_times = sensor.t_sim_s.to_numpy(np.float64)

    events: list[Event] = []
    for peak in whiff_peaks(signal):
        event_time = float(event_times[peak])
        if event_time < 0.0:
            continue
        receptor = int(np.argmin(np.abs(sensor.t_sim_s.to_numpy() - event_time)))
        row = wind.iloc[receptor]
        events.append(Event(
            time_s=event_time,
            trace_step=int(row.step),
            xyz=(float(row.x), float(row.y), float(row.z)),
            local_wind_xyz=(float(row.wind_u), float(row.wind_v), float(row.wind_w)),
        ))
    if len(events) < 2:
        raise ValueError(f"LMBT_TOO_FEW_WHIFFS:{len(events)}")
    audit = {
        "memory_on": memory_on,
        "event_count": len(events),
        "event_times_s": [event.time_s for event in events],
        "scoring_columns": sensor_cols + wind_cols,
        "true_gas_column_read": False,
    }
    return events, audit


def infer_wind_schedule(runtime_wind: RuntimeWind,
                        trace_dir: Path) -> tuple[WindSchedule, dict]:
    wind = pd.read_csv(trace_dir / "wind_trace.csv")
    indices = []
    errors = []
    for row in wind.itertuples(index=False):
        xyz = np.asarray([row.x, row.y, row.z], dtype=np.float64)
        expected = np.asarray([row.wind_u, row.wind_v, row.wind_w], dtype=np.float64)
        per_field = {
            index: float(np.linalg.norm(query_velocity(runtime_wind, index, xyz) - expected))
            for index in range(0, 11)
        }
        best = min(per_field, key=lambda index: (per_field[index], index))
        indices.append(best)
        errors.append(per_field[best])
    schedule = WindSchedule(tuple(indices), int(wind.iloc[0].iteration))
    result = {
        "samples": len(errors),
        "median_vector_error_m_s": float(np.median(errors)),
        "max_vector_error_m_s": float(np.max(errors)),
        "mapping": "per-step nearest CFD field 0..10 from allowed local wind; native periodic extrapolation only before trace start",
        "field_counts": {str(index): int(np.sum(np.asarray(indices) == index)) for index in range(0, 11)},
    }
    if result["median_vector_error_m_s"] > 1.0e-4 or result["max_vector_error_m_s"] > 2.0e-3:
        raise ValueError(f"LMBT_WIND_SEQUENCE_NOT_BOUND:{result}")
    return schedule, result


def backward_paths(events: list[Event], runtime_wind: RuntimeWind | None,
                   schedule: WindSchedule | None, candidate_xy: np.ndarray,
                   reversed_sequence: bool = False,
                   local_ray: bool = False) -> list[tuple[np.ndarray, np.ndarray]]:
    lower = candidate_xy.min(axis=0) - 0.5
    upper = candidate_xy.max(axis=0) + 0.5
    steps = int(MAX_AGE_S / BACK_DT_S)
    output: list[tuple[np.ndarray, np.ndarray]] = []
    for event in events:
        xyz = np.asarray(event.xyz, dtype=np.float64)
        positions = []
        ages = []
        for step in range(1, steps + 1):
            past_step = event.trace_step - int(round(step * BACK_DT_S / DT_S))
            if local_ray:
                velocity = np.asarray(event.local_wind_xyz, dtype=np.float64)
            else:
                assert schedule is not None
                index = schedule.at(past_step)
                if reversed_sequence:
                    index = 10 - index
                assert runtime_wind is not None
                velocity = query_velocity(runtime_wind, index, xyz)
            # V1 is a navigation-height source footprint.  Preserve z and use
            # the horizontal components of the exact 3-D runtime wind cell.
            xyz[:2] = xyz[:2] - velocity[:2] * BACK_DT_S
            if np.any(xyz[:2] < lower) or np.any(xyz[:2] > upper):
                break
            positions.append(xyz[:2].copy())
            ages.append(step * BACK_DT_S)
        if not positions:
            positions = [np.asarray(event.xyz[:2], dtype=np.float64)]
            ages = [BACK_DT_S]
        output.append((np.asarray(positions), np.asarray(ages)))
    return output


def pooled_log_score(paths: list[tuple[np.ndarray, np.ndarray]],
                     candidate_xy: np.ndarray, kappa: float) -> np.ndarray:
    pooled = np.zeros(len(candidate_xy), dtype=np.float64)
    epsilon = 1.0e-300
    for positions, ages in paths:
        footprint = np.zeros(len(candidate_xy), dtype=np.float64)
        for start in range(0, len(candidate_xy), 1024):
            stop = min(start + 1024, len(candidate_xy))
            delta = candidate_xy[start:stop, None, :] - positions[None, :, :]
            distance2 = np.sum(delta * delta, axis=2)
            variance = BASE_SPREAD_M ** 2 + 2.0 * kappa * ages[None, :]
            kernel = np.exp(-0.5 * distance2 / variance) / variance
            footprint[start:stop] = np.mean(kernel, axis=1)
        footprint /= max(float(footprint.max()), epsilon)
        pooled += np.log(np.maximum(footprint, epsilon))
    return pooled / len(paths)


def freeze_arm_scores(events: list[Event], runtime_wind: RuntimeWind | None,
                      schedule: WindSchedule | None, candidate_xy: np.ndarray,
                      reversed_sequence: bool = False,
                      local_ray: bool = False) -> dict[float, np.ndarray]:
    paths = backward_paths(events, runtime_wind, schedule, candidate_xy,
                           reversed_sequence=reversed_sequence, local_ray=local_ray)
    return {kappa: pooled_log_score(paths, candidate_xy, kappa) for kappa in KAPPAS}


def parse_truth_after_scoring(manifest_path: Path) -> tuple[float, float]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    match = re.search(r"sourcePosition_(-?\d+(?:\.\d+)?)_(-?\d+(?:\.\d+)?)_",
                      manifest["realization"])
    if not match:
        raise ValueError("LMBT_SOURCE_TRUTH_PARSE")
    return float(match.group(1)), float(match.group(2))


def evaluate(scores: np.ndarray, candidate_xy: np.ndarray,
             truth_xy: tuple[float, float]) -> dict:
    truth = np.asarray(truth_xy, dtype=np.float64)
    truth_index = int(np.argmin(np.sum((candidate_xy - truth) ** 2, axis=1)))
    order = np.argsort(-scores, kind="stable")
    rank = int(np.flatnonzero(order == truth_index)[0]) + 1
    map_index = int(order[0])
    return {
        "true_candidate_index": truth_index,
        "true_candidate_xy": candidate_xy[truth_index].tolist(),
        "true_rank": rank,
        "candidate_count": len(candidate_xy),
        "normalized_true_rank": (rank - 1) / max(len(candidate_xy) - 1, 1),
        "map_xy": candidate_xy[map_index].tolist(),
        "map_error_m": float(np.linalg.norm(candidate_xy[map_index] - truth)),
        "true_log_score": float(scores[truth_index]),
        "best_log_score": float(scores[map_index]),
        "true_best_margin": float(scores[truth_index] - scores[map_index]),
    }


def selftest() -> None:
    latent = np.asarray([0.0, 0.0, 0.4, 0.8, 0.2, 0.0])
    alpha = math.exp(-DT_S / TAU_S)
    state = 0.0
    measured = []
    for value in latent:
        state = alpha * state + (1.0 - alpha) * value
        measured.append(state)
    recovered = inverse_sensor(np.asarray(measured))
    if not np.allclose(recovered, latent, atol=1.0e-12):
        raise AssertionError("LMBT_INVERSE_SELFTEST")
    if whiff_peaks(np.asarray([0.0, 0.2, 0.4, 0.0, 0.3, 0.0])) != [2, 4]:
        raise AssertionError("LMBT_WHIFF_SELFTEST")
    schedule = WindSchedule((6, 6, 7, 7), 1050)
    for trace_step, expected in ((1, 6), (3, 7), (0, 5), (-1, 5)):
        if schedule.at(trace_step) != expected:
            raise AssertionError("LMBT_WIND_SCHEDULE_SELFTEST")
    print("LMBT_SELFTEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--trace-dir", type=Path)
    parser.add_argument("--realization", type=Path)
    parser.add_argument("--occupancy", type=Path)
    parser.add_argument("--environment-runtime-py", type=Path)
    parser.add_argument("--candidate-csv", type=Path)
    parser.add_argument("--prereg", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    required = (args.trace_dir, args.realization, args.occupancy,
                args.environment_runtime_py, args.candidate_csv, args.prereg, args.out)
    if any(value is None for value in required):
        parser.error("formal run requires trace-dir, wind-root, candidate-csv, prereg, out")
    if args.out.exists():
        raise FileExistsError("LMBT_REFUSE_OVERWRITE_FORMAL_RESULT")

    prereg = json.loads(args.prereg.read_text(encoding="utf-8"))
    if prereg.get("contract") != "LMBT_H03_SEED11_ORACLE_WIND_PREMISE_V1":
        raise ValueError("LMBT_PREREG_CONTRACT")
    candidate_xy = pd.read_csv(args.candidate_csv, usecols=["x", "y"]).to_numpy(np.float64)
    runtime_wind = load_runtime_wind(args.realization, args.occupancy,
                                     args.environment_runtime_py)
    wind_schedule, wind_binding = infer_wind_schedule(runtime_wind, args.trace_dir)
    memory_events, memory_audit = load_events(args.trace_dir, memory_on=True)
    raw_events, raw_audit = load_events(args.trace_dir, memory_on=False)

    # Freeze every score before opening the evaluator-only source truth.
    frozen = {
        "LMBT_MEMORY_ON_ACTUAL_WIND": freeze_arm_scores(
            memory_events, runtime_wind, wind_schedule, candidate_xy),
        "LMBT_MEMORY_OFF_ACTUAL_WIND": freeze_arm_scores(
            raw_events, runtime_wind, wind_schedule, candidate_xy),
        "LMBT_MEMORY_ON_REVERSED_WIND_SEQUENCE": freeze_arm_scores(
            memory_events, runtime_wind, wind_schedule, candidate_xy, reversed_sequence=True),
        "LOCAL_WIND_RAY_MEMORY_ON": freeze_arm_scores(
            memory_events, None, None, candidate_xy, local_ray=True),
    }
    truth_xy = parse_truth_after_scoring(args.trace_dir / "formal_runtime_manifest.json")
    results = {
        arm: {str(kappa): evaluate(scores, candidate_xy, truth_xy)
              for kappa, scores in by_kappa.items()}
        for arm, by_kappa in frozen.items()
    }
    medians = {
        arm: float(np.median([row["normalized_true_rank"] for row in by_kappa.values()]))
        for arm, by_kappa in results.items()
    }
    actual = medians["LMBT_MEMORY_ON_ACTUAL_WIND"]
    checks = {
        "actual_wind_top_decile": actual <= 0.10,
        "actual_beats_reversed_wind": actual < medians["LMBT_MEMORY_ON_REVERSED_WIND_SEQUENCE"],
        "actual_beats_local_ray": actual < medians["LOCAL_WIND_RAY_MEMORY_ON"],
        "memory_attribution": actual < medians["LMBT_MEMORY_OFF_ACTUAL_WIND"],
    }
    primary_pass = all(checks[name] for name in (
        "actual_wind_top_decile", "actual_beats_reversed_wind", "actual_beats_local_ray"))
    report = {
        "contract": prereg["contract"],
        "verdict": "LMBT_ORACLE_WIND_PREMISE_PASS" if primary_pass else "LMBT_ORACLE_WIND_PREMISE_NO_GO",
        "sensor_memory_verdict": "LMBT_SENSOR_MEMORY_ATTRIBUTION_PASS" if checks["memory_attribution"]
                                  else "LMBT_SENSOR_MEMORY_ATTRIBUTION_NO_GO",
        "claim_boundary": prereg["claim_if_pass"] if primary_pass else prereg["stop_rule"],
        "truth_read_after_all_arm_scores": True,
        "truth_xy_evaluator_only": list(truth_xy),
        "wind_binding": wind_binding,
        "event_audit": {"memory_on": memory_audit, "memory_off": raw_audit},
        "median_normalized_true_rank": medians,
        "checks": checks,
        "results": results,
        "input_hashes": {
            "sensor_trace.csv": sha256(args.trace_dir / "sensor_trace.csv"),
            "wind_trace.csv": sha256(args.trace_dir / "wind_trace.csv"),
            "formal_runtime_manifest.json": sha256(args.trace_dir / "formal_runtime_manifest.json"),
            "candidate.csv": sha256(args.candidate_csv),
            "prereg": sha256(args.prereg),
            "script": sha256(Path(__file__)),
            "occupancy": sha256(args.occupancy),
            "environment_runtime.py": sha256(args.environment_runtime_py),
            "runtime_wind": {
                path.name: sha256(path)
                for path in sorted((args.realization / "wind").glob("wind_iteration_*"))
            },
        },
        "limitations": [
            "simulation-known full CFD wind is evaluator-only and unavailable in real flight",
            "one development trace only; no cross-House or held-out claim",
            "nearest-mesh velocity lookup and isotropic diffusion are premise approximations",
            "no PMFS or planner integration was evaluated",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    print(report["sensor_memory_verdict"])
    print(json.dumps(medians, sort_keys=True))


if __name__ == "__main__":
    main()
