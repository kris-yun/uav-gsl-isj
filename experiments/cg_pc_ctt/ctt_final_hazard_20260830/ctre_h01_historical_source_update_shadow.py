#!/usr/bin/env python3
"""Frozen H01 fixed-trajectory CTRE replay at actual PMFS source updates.

This script never runs GADEN, trains a model, or changes a planner.  It maps
the frozen coherent reachability likelihood back to the native 626 free PMFS
cells and reproduces the formal ``ExpectedValue(grid, 0.05)`` endpoint.
Truth is read only after each source score/posterior has been formed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import tarfile

import numpy as np

ROOT = "CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827/results/House01"
SENSOR_DELAY = 2
DT_S = 0.2
SENSOR_TAU_S = 1.2
STOP_SAMPLES = 80


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_member(tf: tarfile.TarFile, member: str) -> list[dict]:
    source = tf.extractfile(member)
    if source is None:
        raise ValueError(f"CTRE_MISSING_MEMBER:{member}")
    return list(csv.DictReader(io.StringIO(source.read().decode("utf-8"))))


def unique_member(tf: tarfile.TarFile, prefix: str, suffix: str) -> str:
    hits = [name for name in tf.getnames() if name.startswith(prefix) and name.endswith(suffix)]
    if len(hits) != 1:
        raise ValueError(f"CTRE_MEMBER_CARDINALITY:{prefix}:{suffix}:{len(hits)}")
    return hits[0]


def sensor_forward(physical: np.ndarray) -> np.ndarray:
    concentration = np.asarray(physical, dtype=np.float64)
    alpha = math.exp(-DT_S / SENSOR_TAU_S)
    output = np.zeros(concentration.shape[:-1] + (concentration.shape[-1] + SENSOR_DELAY,), dtype=np.float64)
    for index in range(1, output.shape[-1]):
        value = concentration[..., index - SENSOR_DELAY] if index >= SENSOR_DELAY else 0.0
        output[..., index] = alpha * output[..., index - 1] + (1.0 - alpha) * value
    return output[..., SENSOR_DELAY:]


def completed_stops(pose: list[dict], aligned_time: np.ndarray) -> list[np.ndarray]:
    if len(pose) != len(aligned_time):
        raise ValueError("CTRE_POSE_TIME_ALIGNMENT")
    result: list[np.ndarray] = []
    current: list[int] = []
    for index, row in enumerate(pose):
        stationary = int(row["is_moving"]) == 0
        if stationary and (not current or index == current[-1] + 1):
            current.append(index)
        elif stationary:
            if len(current) >= STOP_SAMPLES:
                result.append(np.asarray(current[:STOP_SAMPLES], dtype=np.int64))
            current = [index]
        else:
            if len(current) >= STOP_SAMPLES:
                result.append(np.asarray(current[:STOP_SAMPLES], dtype=np.int64))
            current = []
    if len(current) >= STOP_SAMPLES:
        result.append(np.asarray(current[:STOP_SAMPLES], dtype=np.int64))
    if not result or any(np.any(np.diff(index) != 1) for index in result):
        raise ValueError("CTRE_STOP_EXTRACTION")
    return result


def log_mean_exp(values: np.ndarray, axis: int) -> np.ndarray:
    maximum = np.max(values, axis=axis, keepdims=True)
    return np.squeeze(maximum, axis=axis) + np.log(np.mean(np.exp(values - maximum), axis=axis))


def ctre_scores(predicted: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    probability = (0.5 + predicted.astype(np.float64)) / 2.0
    y = observed.astype(np.float64)
    per_member = (
        y[None, None, :] * np.log(probability)
        + (1.0 - y[None, None, :]) * np.log1p(-probability)
    ).sum(axis=2)
    coherent = log_mean_exp(per_member, axis=1)
    mean_probability = probability.mean(axis=1)
    stopwise = (
        y[None, :] * np.log(mean_probability)
        + (1.0 - y[None, :]) * np.log1p(-mean_probability)
    ).sum(axis=1)
    return coherent, stopwise


def posterior(prior: np.ndarray, log_likelihood: np.ndarray) -> np.ndarray:
    log_mass = np.log(prior) + log_likelihood
    log_mass -= np.max(log_mass)
    mass = np.exp(log_mass)
    return mass / np.sum(mass)


def rank_desc(values: np.ndarray, truth: int) -> int:
    target = float(values[truth])
    tolerance = 1e-12 * (1.0 + abs(target))
    return 1 + int(np.count_nonzero(values > target + tolerance))


def carrier_id_for_cell(cell_index: int, width: int, height: int) -> str:
    x_index = cell_index % width
    y_index = cell_index // width
    x_origin = 2 * (x_index // 2)
    y_origin = 2 * (y_index // 2)
    x_size = min(2, width - x_origin)
    y_size = min(2, height - y_origin)
    return f"quadtree_{x_origin}_{y_origin}_{x_size}_{y_size}"


def carrier_mass_from_cells(rows: list[dict], source_index: dict[str, int],
                            width: int, height: int) -> np.ndarray:
    mass = np.zeros(len(source_index), dtype=np.float64)
    for row in rows:
        carrier_id = carrier_id_for_cell(int(row["cell_index"]), width, height)
        if carrier_id not in source_index:
            raise ValueError(f"CTRE_CELL_OUTSIDE_SUPPORT:{carrier_id}")
        mass[source_index[carrier_id]] += float(row["source_probability"])
    total = np.sum(mass)
    if not np.isfinite(total) or total <= 0:
        raise ValueError("CTRE_INVALID_NATIVE_MASS")
    return mass / total


def carrier_to_cells(carrier_mass: np.ndarray, rows: list[dict], source_index: dict[str, int],
                     free_cells: np.ndarray, width: int, height: int) -> np.ndarray:
    cell_mass = np.empty(len(rows), dtype=np.float64)
    seen = np.zeros(len(source_index), dtype=np.int64)
    for index, row in enumerate(rows):
        source = source_index[carrier_id_for_cell(int(row["cell_index"]), width, height)]
        cell_mass[index] = carrier_mass[source] / free_cells[source]
        seen[source] += 1
    if not np.array_equal(seen, free_cells):
        raise ValueError("CTRE_FREE_CELL_COUNT_MISMATCH")
    return cell_mass / np.sum(cell_mass)


def formal_location_error(rows: list[dict], probability: np.ndarray, truth_xy: tuple[float, float]) -> float:
    count = int(math.ceil(len(rows) * 0.05 - 1e-15))
    order = np.argsort(-probability, kind="stable")[:count]
    x = np.asarray([float(row["x"]) for row in rows], dtype=np.float64)
    y = np.asarray([float(row["y"]) for row in rows], dtype=np.float64)
    weight = probability[order]
    estimate_x = float(np.sum(x[order] * weight) / np.sum(weight))
    estimate_y = float(np.sum(y[order] * weight) / np.sum(weight))
    return float(math.hypot(estimate_x - truth_xy[0], estimate_y - truth_xy[1]))


def load_support(path: Path) -> tuple[list[str], np.ndarray]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    rows.sort(key=lambda row: int(row["carrier_index"]))
    if len(rows) != 210 or [int(row["carrier_index"]) for row in rows] != list(range(210)):
        raise ValueError("CTRE_SUPPORT_CONTRACT")
    return [row["carrier_id"] for row in rows], np.asarray([int(row["free_cells"]) for row in rows])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--bank-dir", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"CTRE_REFUSE_OVERWRITE:{args.output}")
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    if prereg.get("contract") != "CTRE_H01_HISTORICAL_SOURCE_UPDATE_SHADOW_V1":
        raise SystemExit("CTRE_PREREGISTRATION_CONTRACT")
    expected = prereg["inputs"]
    if sha256_file(args.archive) != expected["archive_sha256"]:
        raise SystemExit("CTRE_ARCHIVE_HASH")
    if sha256_file(args.support) != expected["support_sha256"]:
        raise SystemExit("CTRE_SUPPORT_HASH")
    if sha256_file(args.mapping) != expected["mapping_sha256"]:
        raise SystemExit("CTRE_MAPPING_HASH")

    support_ids, free_cells = load_support(args.support)
    rows_out: list[dict] = []
    final_rows: list[dict] = []
    with tarfile.open(args.archive, "r:gz") as tf:
        names = tf.getnames()
        for seed in range(10):
            bank_path = args.bank_dir / f"H01_seed{seed}_candidate_physical.npz"
            if sha256_file(bank_path) != expected["bank_view_sha256"][str(seed)]:
                raise SystemExit(f"CTRE_BANK_HASH:{seed}")
            with np.load(bank_path, allow_pickle=False) as bank:
                physical = np.asarray(bank["candidate_physical_ppm"], dtype=np.float64)
                source_ids = np.asarray(bank["source_id"]).astype(str)
                prior = np.asarray(bank["geometry_prior"], dtype=np.float64)
                bank_time = np.asarray(bank["sample_time_s"], dtype=np.float64)
            if physical.shape[:2] != (210, 8) or list(source_ids) != support_ids:
                raise ValueError(f"CTRE_BANK_SHAPE_OR_ORDER:{seed}")
            prior /= np.sum(prior)
            source_index = {source_id: index for index, source_id in enumerate(source_ids)}
            truth_index = source_index["quadtree_22_16_2_2"]

            prefix = f"{ROOT}/seed{seed}/off/runtime/"
            sensor_member = unique_member(tf, prefix, "/sensor_trace.csv")
            pose_member = unique_member(tf, prefix, "/sim_pose_trace.csv")
            timing_member = unique_member(tf, prefix, "/context_bank/source_update_timing.csv")
            sensor = read_csv_member(tf, sensor_member)
            pose = read_csv_member(tf, pose_member)
            timing = read_csv_member(tf, timing_member)
            if len(sensor) != len(pose):
                raise ValueError(f"CTRE_SENSOR_POSE_LENGTH:{seed}")
            sensor_time = np.asarray([float(row["t_sim_s"]) for row in sensor])
            pose_time = np.asarray([float(row["t_sim_s"]) for row in pose])
            if np.max(np.abs(sensor_time - pose_time)) > 1e-9:
                raise ValueError(f"CTRE_SENSOR_POSE_TIME:{seed}")
            aligned_time = sensor_time[SENSOR_DELAY:]
            measured = np.asarray([float(row["measured_gas_ppm"]) for row in sensor])[SENSOR_DELAY:]
            aligned_pose = pose[SENSOR_DELAY:]
            if physical.shape[2] != len(aligned_time) or np.max(np.abs(bank_time - sensor_time[:-SENSOR_DELAY])) > 1e-9:
                raise ValueError(f"CTRE_BANK_TIME:{seed}")
            candidate_measured = sensor_forward(physical)
            stops = completed_stops(aligned_pose, aligned_time)
            observed_detection = np.asarray([np.any(measured[index] > 0.1) for index in stops], dtype=np.bool_)
            candidate_detection = np.asarray([
                np.any(candidate_measured[:, :, index] > 0.1, axis=2) for index in stops
            ], dtype=np.bool_).transpose(1, 2, 0)
            # candidate_detection is [source, member, stop].

            case_member = f"{ROOT}/seed{seed}/off/case_result.json"
            case = json.loads(tf.extractfile(case_member).read().decode("utf-8"))
            truth_xy = tuple(float(value) for value in case["truth_eval_only"])
            for update in timing:
                update_id = int(update["source_update_id"])
                update_time = float(update["sim_time"])
                visible = [index for index, stop in enumerate(stops) if aligned_time[stop[-1]] <= update_time + 1e-12]
                if len(visible) != 3 * update_id:
                    raise ValueError(f"CTRE_VISIBLE_STOP_CONTRACT:{seed}:{update_id}:{len(visible)}")
                coherent, stopwise = ctre_scores(
                    candidate_detection[:, :, visible], observed_detection[visible])
                coherent_posterior = posterior(prior, coherent)
                stopwise_posterior = posterior(prior, stopwise)

                update_suffix = f"/context_bank/source_update_{update_id:04d}/source_posterior.csv"
                native_member = unique_member(tf, prefix, update_suffix)
                native_cells = read_csv_member(tf, native_member)
                width = int(update["grid_width"])
                height = int(update["grid_height"])
                native_cell_mass = np.asarray([float(row["source_probability"]) for row in native_cells])
                native_cell_mass /= np.sum(native_cell_mass)
                native_carrier = carrier_mass_from_cells(native_cells, source_index, width, height)
                coherent_cells = carrier_to_cells(
                    coherent_posterior, native_cells, source_index, free_cells, width, height)
                stopwise_cells = carrier_to_cells(
                    stopwise_posterior, native_cells, source_index, free_cells, width, height)
                row = {
                    "seed": seed,
                    "source_update_id": update_id,
                    "source_update_time_s": update_time,
                    "visible_physical_stops": len(visible),
                    "observed_hit_stops": int(np.sum(observed_detection[visible])),
                    "native_true_rank": rank_desc(native_carrier, truth_index),
                    "ctre_raw_true_rank": rank_desc(coherent, truth_index),
                    "ctre_posterior_true_rank": rank_desc(coherent_posterior, truth_index),
                    "stopwise_posterior_true_rank": rank_desc(stopwise_posterior, truth_index),
                    "native_formal_error_m": formal_location_error(native_cells, native_cell_mass, truth_xy),
                    "ctre_formal_error_m": formal_location_error(native_cells, coherent_cells, truth_xy),
                    "stopwise_formal_error_m": formal_location_error(native_cells, stopwise_cells, truth_xy),
                }
                rows_out.append(row)
                if update_id == 5:
                    parity = abs(row["native_formal_error_m"] - float(case["primary_error_m"]))
                    if parity > 1e-10:
                        raise ValueError(f"CTRE_NATIVE_FORMAL_PARITY:{seed}:{parity}")
                    final_rows.append(row)
            print(f"CTRE_HISTORICAL_SEED={seed} PASS", flush=True)

    pmfs = np.asarray([row["native_formal_error_m"] for row in final_rows])
    ctre = np.asarray([row["ctre_formal_error_m"] for row in final_rows])
    improved = ctre < pmfs - 1e-12
    catastrophe = (ctre > pmfs + 1.0) & (ctre > 1.5 * pmfs)
    pooled = float((np.sum(pmfs) - np.sum(ctre)) / np.sum(pmfs))
    gate = prereg["go_rule"]
    passed = bool(
        len(final_rows) == int(gate["valid_pairs"])
        and pooled >= float(gate["minimum_pooled_relative_improvement"])
        and int(np.sum(improved)) >= int(gate["minimum_improved_pairs"])
        and int(np.sum(catastrophe)) <= int(gate["maximum_catastrophic_regressions"])
    )
    verdict = "CTRE_GO_TO_FROZEN_H01_CLOSED_LOOP_PILOT" if passed else "CTRE_HISTORICAL_SHADOW_NO_GO"
    report = {
        "contract": prereg["contract"],
        "development_only": True,
        "fixed_trajectory": True,
        "closed_loop_authorized": False,
        "gaden_runs": 0,
        "neural_training": False,
        "method_parameters_changed_after_outcome": False,
        "summary": {
            "valid_pairs": len(final_rows),
            "pmfs_mean_error_m": float(np.mean(pmfs)),
            "ctre_mean_error_m": float(np.mean(ctre)),
            "pooled_relative_improvement": pooled,
            "improved_pairs": int(np.sum(improved)),
            "catastrophic_regressions": int(np.sum(catastrophe)),
        },
        "by_update": rows_out,
        "final_pairs": final_rows,
        "input_hashes": {
            "archive": sha256_file(args.archive),
            "support": sha256_file(args.support),
            "mapping": sha256_file(args.mapping),
            "preregistration": sha256_file(args.preregistration),
        },
        "verdict": verdict,
    }
    args.output.mkdir(parents=True)
    with (args.output / "CASES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows_out[0]))
        writer.writeheader()
        writer.writerows(rows_out)
    (args.output / "SUMMARY.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "VERDICT.txt").write_text(verdict + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "verdict": verdict}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
