#!/usr/bin/env python3
"""Frozen cross-House field gate for the CTPI-G2 M2 L0 solver.

The predictor uses only carrier geometry, the free-cell mask, and wind files.
GADEN peak fields are read only as held-out evaluation targets.  Candidate
source placements are the complete set of free cells inside each region-valued
carrier; no source position is recovered from a GADEN/bank argmax.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np


DIFFUSIVITY_M2_S = 0.01
CELL_SIZE_M = 0.3
TOTAL_TIME_S = 300.0
TIME_STEP_S = 1.0
WIND_STATE_COUNT = 11
CARRIER_RE = re.compile(r"^quadtree_(\d+)_(\d+)_(\d+)_(\d+)$")
HOUSE = {
    "H01": {
        "scenario": "House01",
        "fine": (87, 114, 33),
        "coarse": (29, 38),
        "z_index": 13,
        "wind_relative": "gas_simulations/2,4-1_fast/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30/wind",
    },
    "H02": {
        "scenario": "House02",
        "fine": (83, 119, 26),
        "coarse": (27, 39),
        "z_index": 13,
        "wind_relative": "gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind",
    },
    "H03": {
        "scenario": "House03",
        "fine": (138, 83, 25),
        "coarse": (46, 27),
        "z_index": 12,
        "wind_relative": "gas_simulations/1-2,5_fast/FilamentSimulation_gasType_10_sourcePosition_-0.45_1.90_-0.10/wind",
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def carrier_rect(carrier_id: str) -> tuple[int, int, int, int]:
    match = CARRIER_RE.fullmatch(carrier_id)
    if match is None:
        raise ValueError(f"CTPI_G2_M2_CARRIER_ID:{carrier_id}")
    return tuple(int(value) for value in match.groups())  # type: ignore[return-value]


def load_cells(path: Path) -> list[dict[str, float | int]]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    cells = [{
        "stream": int(row["stream_ordinal"]),
        "native": int(row["native_cell_index"]),
        "x": float(row["x"]),
        "y": float(row["y"]),
    } for row in rows]
    if [row["stream"] for row in cells] != list(range(len(cells))):
        raise ValueError("CTPI_G2_M2_CELL_STREAM_ORDER")
    return cells


def load_wind(scenario_root: Path, house: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    spec = HOUSE[house]
    fnx, fny, fnz = spec["fine"]
    nx, ny = spec["coarse"]
    z_index = int(spec["z_index"])
    wind_root = scenario_root / str(spec["scenario"]) / str(spec["wind_relative"])
    u_out = np.empty((WIND_STATE_COUNT, nx, ny), dtype=np.float64)
    v_out = np.empty_like(u_out)
    hashes: list[str] = []
    cell_count = fnx * fny * fnz
    for state in range(WIND_STATE_COUNT):
        path = wind_root / f"wind_iteration_{state}"
        raw = np.fromfile(path, dtype=np.float64)
        if raw.size < 2 * cell_count:
            raise ValueError(f"CTPI_G2_M2_WIND_SIZE:{path}:{raw.size}")
        u = raw[:cell_count].reshape(fnx, fny, fnz)[:, :, z_index]
        v = raw[cell_count:2 * cell_count].reshape(fnx, fny, fnz)[:, :, z_index]
        u_blocks = u[:nx * 3, :ny * 3].reshape(nx, 3, ny, 3)
        v_blocks = v[:nx * 3, :ny * 3].reshape(nx, 3, ny, 3)
        u_out[state] = np.nanmean(u_blocks, axis=(1, 3))
        v_out[state] = np.nanmean(v_blocks, axis=(1, 3))
        hashes.append(sha256_file(path))
    return u_out, v_out, hashes


def advance(concentration: np.ndarray, u: np.ndarray, v: np.ndarray,
            source_ij: tuple[int, int], free: np.ndarray) -> np.ndarray:
    left = np.roll(concentration, 1, axis=0); left[0, :] = 0.0
    right = np.roll(concentration, -1, axis=0); right[-1, :] = 0.0
    down = np.roll(concentration, 1, axis=1); down[:, 0] = 0.0
    up = np.roll(concentration, -1, axis=1); up[:, -1] = 0.0
    dc_dx = np.where(u >= 0.0, (concentration - left) / CELL_SIZE_M,
                     (right - concentration) / CELL_SIZE_M)
    dc_dy = np.where(v >= 0.0, (concentration - down) / CELL_SIZE_M,
                     (up - concentration) / CELL_SIZE_M)
    advection = -u * dc_dx - v * dc_dy
    laplacian = (left + right + down + up - 4.0 * concentration) / (CELL_SIZE_M ** 2)
    updated = concentration + TIME_STEP_S * (
        advection + DIFFUSIVITY_M2_S * laplacian
    )
    updated = np.maximum(updated, 0.0)
    updated[source_ij] += TIME_STEP_S
    updated[~free] = 0.0
    return updated


def numerical_peak(source_ij: tuple[int, int], free: np.ndarray,
                   wind_u: np.ndarray, wind_v: np.ndarray) -> np.ndarray:
    concentration = np.zeros_like(free, dtype=np.float64)
    peak = np.zeros_like(concentration)
    steps = int(TOTAL_TIME_S / TIME_STEP_S)
    # Preserve the spent L0 contract exactly: floor(steps/11) per wind state.
    segment_steps = steps // WIND_STATE_COUNT
    for state in range(WIND_STATE_COUNT):
        for _ in range(segment_steps):
            concentration = advance(concentration, wind_u[state], wind_v[state], source_ij, free)
            np.maximum(peak, concentration, out=peak)
    return peak


def plume_peak(source_xy: tuple[float, float], action_x: np.ndarray, action_y: np.ndarray,
               wind_u: np.ndarray, wind_v: np.ndarray) -> np.ndarray:
    result = np.zeros_like(action_x)
    for u, v in zip(np.mean(wind_u, axis=(1, 2)), np.mean(wind_v, axis=(1, 2))):
        speed = float(np.hypot(u, v))
        cd, sd = (float(u / speed), float(v / speed)) if speed > 1.0e-6 else (1.0, 0.0)
        dx = (action_x - source_xy[0]) * cd + (action_y - source_xy[1]) * sd
        dy = -(action_x - source_xy[0]) * sd + (action_y - source_xy[1]) * cd
        response = np.zeros_like(dx)
        valid = dx > 0.15
        sigma = 0.5 * dx[valid] + 0.3
        response[valid] = np.exp(-(dy[valid] ** 2) / (2.0 * sigma ** 2)) / (sigma * dx[valid])
        np.maximum(result, response, out=result)
    return result


def normalized_shape(value: np.ndarray) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    maximum = float(np.max(array))
    if not np.isfinite(maximum) or maximum <= 0.0:
        raise ValueError("CTPI_G2_M2_ZERO_FIELD")
    return array / maximum


def field_metrics(prediction: np.ndarray, target: np.ndarray) -> tuple[float, float]:
    observed = normalized_shape(target)
    prediction_maximum = float(np.max(prediction))
    if not np.isfinite(prediction_maximum) or prediction_maximum < 0.0:
        raise ValueError("CTPI_G2_M2_INVALID_PREDICTION_FIELD")
    if prediction_maximum == 0.0:
        return 0.0, float(np.mean(observed ** 2))
    predicted = normalized_shape(prediction)
    if float(np.std(predicted)) <= 0.0 or float(np.std(observed)) <= 0.0:
        correlation = 0.0
    else:
        correlation = float(np.corrcoef(predicted, observed)[0, 1])
    mse = float(np.mean((predicted - observed) ** 2))
    return correlation, mse


def evaluate_house(bank_root: Path, scenario_root: Path, house: str,
                   prediction_output_dir: Path | None = None) -> dict[str, Any]:
    root = bank_root / house
    summary = json.loads((root / "bank_summary.json").read_text(encoding="utf-8"))
    cells = load_cells(root / "cell_manifest.csv")
    nx, ny = HOUSE[house]["coarse"]
    free = np.zeros((nx, ny), dtype=np.bool_)
    stream_for_native: dict[int, int] = {}
    xy_for_native: dict[int, tuple[float, float]] = {}
    for cell in cells:
        native = int(cell["native"])
        free[native % nx, native // nx] = True
        stream_for_native[native] = int(cell["stream"])
        xy_for_native[native] = (float(cell["x"]), float(cell["y"]))
    action_x = np.asarray([cell["x"] for cell in cells], dtype=np.float64)
    action_y = np.asarray([cell["y"] for cell in cells], dtype=np.float64)

    wind_u, wind_v, wind_hashes = load_wind(scenario_root, house)
    carriers = sorted(path.stem for path in (root / "worlds" / "member_00").glob("*.bin"))
    carrier_count, member_count, cell_count = int(summary["carrier_count"]), int(summary["member_count"]), len(cells)
    if len(carriers) != carrier_count:
        raise ValueError(f"CTPI_G2_M2_CARRIER_COUNT:{house}")
    raw_peak = np.fromfile(root / "g2m1_peak_field.bin", dtype=np.float32, offset=20)
    if raw_peak.size != carrier_count * member_count * cell_count:
        raise ValueError(f"CTPI_G2_M2_PEAK_SIZE:{house}")
    target_peak = raw_peak.reshape(carrier_count, member_count, cell_count)

    records: list[dict[str, Any]] = []
    numerical_fields = np.empty((carrier_count, cell_count), dtype=np.float32)
    plume_fields = np.empty_like(numerical_fields)
    placement_histogram: dict[str, int] = {}
    for carrier_index, carrier in enumerate(carriers):
        oi, oj, sx, sy = carrier_rect(carrier)
        placements = [native for native in stream_for_native
                      if oi <= native % nx < oi + sx and oj <= native // nx < oj + sy]
        placements.sort()
        if not placements:
            raise ValueError(f"CTPI_G2_M2_NO_FREE_PLACEMENT:{house}:{carrier}")
        placement_histogram[str(len(placements))] = placement_histogram.get(str(len(placements)), 0) + 1
        numerical = np.zeros(cell_count, dtype=np.float64)
        plume = np.zeros(cell_count, dtype=np.float64)
        for native in placements:
            peak_grid = numerical_peak((native % nx, native // nx), free, wind_u, wind_v)
            numerical += np.asarray([
                peak_grid[int(cell["native"]) % nx, int(cell["native"]) // nx]
                for cell in cells
            ])
            plume += plume_peak(xy_for_native[native], action_x, action_y, wind_u, wind_v)
        numerical /= float(len(placements))
        plume /= float(len(placements))
        numerical_fields[carrier_index] = numerical
        plume_fields[carrier_index] = plume
        target_members = [member for member in target_peak[carrier_index]
                          if float(np.max(member)) > 0.0]
        if not target_members:
            raise ValueError(f"CTPI_G2_M2_ALL_ZERO_TARGET_MEMBERS:{house}:{carrier}")
        target = np.mean(np.asarray([normalized_shape(member) for member in target_members]), axis=0)
        numerical_corr, numerical_mse = field_metrics(numerical, target)
        plume_corr, plume_mse = field_metrics(plume, target)
        records.append({
            "carrier_id": carrier,
            "free_placement_count": len(placements),
            "nonzero_target_member_count": len(target_members),
            "zero_target_member_count": member_count - len(target_members),
            "numerical_zero_prediction": bool(float(np.max(numerical)) == 0.0),
            "plume_zero_prediction": bool(float(np.max(plume)) == 0.0),
            "numerical_correlation": numerical_corr,
            "plume_correlation": plume_corr,
            "numerical_mse": numerical_mse,
            "plume_mse": plume_mse,
        })
        if (carrier_index + 1) % 25 == 0 or carrier_index + 1 == carrier_count:
            print(f"CTPI_G2_M2_PROGRESS={house}:{carrier_index + 1}/{carrier_count}", flush=True)

    numerical_corr = np.asarray([row["numerical_correlation"] for row in records])
    plume_corr = np.asarray([row["plume_correlation"] for row in records])
    numerical_mse = np.asarray([row["numerical_mse"] for row in records])
    plume_mse = np.asarray([row["plume_mse"] for row in records])
    criteria = {
        "median_correlation_strictly_better_than_plume": bool(np.median(numerical_corr) > np.median(plume_corr)),
        "median_mse_strictly_lower_than_plume": bool(np.median(numerical_mse) < np.median(plume_mse)),
        "carrier_correlation_wins_exceed_losses": bool(np.count_nonzero(numerical_corr > plume_corr) > np.count_nonzero(numerical_corr < plume_corr)),
        "carrier_mse_wins_exceed_losses": bool(np.count_nonzero(numerical_mse < plume_mse) > np.count_nonzero(numerical_mse > plume_mse)),
    }
    zero_target_members = int(sum(row["zero_target_member_count"] for row in records))
    numerical_zero_predictions = int(sum(row["numerical_zero_prediction"] for row in records))
    plume_zero_predictions = int(sum(row["plume_zero_prediction"] for row in records))
    prediction_artifact = None
    if prediction_output_dir is not None:
        prediction_output_dir.mkdir(parents=True, exist_ok=True)
        prediction_path = prediction_output_dir / f"{house}_M2_FIELDS_V1.npz"
        np.savez_compressed(
            prediction_path,
            house=np.asarray(house),
            carrier_ids=np.asarray(carriers),
            native_cells=np.asarray([cell["native"] for cell in cells], dtype=np.int64),
            action_x=action_x,
            action_y=action_y,
            numerical_fields=numerical_fields,
            plume_fields=plume_fields,
            gaden_peak_fields=target_peak,
        )
        prediction_artifact = {
            "path": str(prediction_path),
            "sha256": sha256_file(prediction_path),
            "shape": [carrier_count, cell_count],
        }
    return {
        "house": house,
        "held_out": house in {"H02", "H03"},
        "carrier_count": carrier_count,
        "free_placement_rule": "all free native cells inside carrier, uniform weights",
        "free_placement_count_histogram": placement_histogram,
        "zero_target_member_count": zero_target_members,
        "zero_target_rule": "exclude from normalized-shape mean because an all-zero field has no defined spatial shape; require at least one nonzero member per carrier",
        "numerical_zero_prediction_count": numerical_zero_predictions,
        "plume_zero_prediction_count": plume_zero_predictions,
        "zero_prediction_metric_rule": "retain carrier; assign correlation 0 and MSE mean(target_normalized squared)",
        "prediction_artifact": prediction_artifact,
        "numerical_median_correlation": float(np.median(numerical_corr)),
        "plume_median_correlation": float(np.median(plume_corr)),
        "numerical_median_mse": float(np.median(numerical_mse)),
        "plume_median_mse": float(np.median(plume_mse)),
        "correlation_wins_losses_ties": [
            int(np.count_nonzero(numerical_corr > plume_corr)),
            int(np.count_nonzero(numerical_corr < plume_corr)),
            int(np.count_nonzero(numerical_corr == plume_corr)),
        ],
        "mse_wins_losses_ties": [
            int(np.count_nonzero(numerical_mse < plume_mse)),
            int(np.count_nonzero(numerical_mse > plume_mse)),
            int(np.count_nonzero(numerical_mse == plume_mse)),
        ],
        "criteria": criteria,
        "pass": all(criteria.values()),
        "input_sha256": {
            "bank_summary": sha256_file(root / "bank_summary.json"),
            "cell_manifest": sha256_file(root / "cell_manifest.csv"),
            "gaden_peak_field": sha256_file(root / "g2m1_peak_field.bin"),
            "wind_iterations": wind_hashes,
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank-root", type=Path, required=True)
    parser.add_argument("--scenario-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--houses", nargs="+", choices=sorted(HOUSE), default=["H02", "H03"])
    parser.add_argument("--prediction-output-dir", type=Path)
    args = parser.parse_args()
    results = [evaluate_house(args.bank_root, args.scenario_root, house,
                              args.prediction_output_dir) for house in args.houses]
    held_out = [result for result in results if result["held_out"]]
    passed = bool(held_out) and all(result["pass"] for result in held_out)
    report = {
        "contract": "CTPI_G2_M2_CROSSHOUSE_FIELD_GATE_V1",
        "status": "PASS" if passed else "NO_GO",
        "formula": {
            "diffusivity_m2_s": DIFFUSIVITY_M2_S,
            "cell_size_m": CELL_SIZE_M,
            "total_time_s_requested": TOTAL_TIME_S,
            "time_step_s": TIME_STEP_S,
            "wind_state_count": WIND_STATE_COUNT,
            "steps_per_wind_state": int(TOTAL_TIME_S / TIME_STEP_S) // WIND_STATE_COUNT,
            "actual_integrated_time_s": (int(TOTAL_TIME_S / TIME_STEP_S) // WIND_STATE_COUNT) * WIND_STATE_COUNT * TIME_STEP_S,
        },
        "truth_access": "GADEN peak fields used only after predictions, as evaluation targets",
        "candidate_source_access": "carrier geometry plus free cell manifest only; no bank argmax",
        "baseline": "current G2 Gaussian plume response with identical U|S marginalization",
        "houses": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CTPI_G2_M2_CROSSHOUSE_FIELD_GATE={'PASS' if passed else 'NO_GO'}:{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
