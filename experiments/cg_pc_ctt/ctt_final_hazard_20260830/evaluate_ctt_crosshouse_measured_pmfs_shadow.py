#!/usr/bin/env python3
"""Frozen measured-only CTT reachability shadow against native PMFS.

This is the second, fixed-trajectory gate for the two-module method.  The
candidate channel is the already-audited native GADEN ``do(S=s)`` bank passed
through the run-persistent sensor (M1).  One right-censored ever/never event is
formed for each completed physical stop and the eight transport members are
marginalised *inside that stop* before evidence is accumulated (M2).

Historical observations are read only from ``measured_gas_ppm``.  The method
posterior is ``q0_geometry * L_reachability``; it neither reads nor multiplies
the native PMFS posterior.  Native posteriors are used only as a comparator.
All 150 method posteriors are frozen and hashed before any truth/case-result is
opened.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from evaluate_ctt_crosshouse_causal_reachability_gate import (
    DELAY_SAMPLES,
    DT_S,
    HOUSE_DIR,
    HOUSES,
    JEFFREYS,
    SEEDS,
    SOURCE_COUNTS,
    STOP_SAMPLES,
    TAU_S,
    THRESHOLD_PPM,
    domain_permutation,
    historical_schedule,
    load_complete_stops,
    read_multistream_verified,
    sensor_events_and_first_passage,
    sha256_file,
)


CONTRACT = "CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_V1"
GO = "CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_PASS_TO_RUNTIME"
NO_GO = "CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_NO_GO"
INVALID = "CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_INVALID"
PREDICTIVE_MEMBERS = tuple(range(8))
SOURCE_UPDATES = 5
NULL_REPLICATES = 256
TOL = 1.0e-12


def canonical_array_sha256(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        value = np.asarray(array, dtype="<f8", order="C")
        digest.update(np.asarray(value.shape, dtype="<u8").tobytes())
        digest.update(value.tobytes())
    return digest.hexdigest()


def stable_softmax(log_mass: np.ndarray) -> np.ndarray:
    values = np.asarray(log_mass, dtype=np.float64)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("CTT_SHADOW_SOFTMAX_INPUT_FAIL")
    values = values - np.max(values)
    result = np.exp(values)
    total = float(np.sum(result))
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("CTT_SHADOW_SOFTMAX_NORMALIZATION_FAIL")
    return result / total


def rank_desc(values: np.ndarray, truth: int) -> float:
    """Exact-equality midrank, descending."""
    row = np.asarray(values, dtype=np.float64)
    if row.ndim != 1 or not np.isfinite(row).all() or not 0 <= truth < len(row):
        raise ValueError("CTT_SHADOW_RANK_INPUT_FAIL")
    target = row[truth]
    above = int(np.count_nonzero(row > target))
    equal = int(np.count_nonzero(row == target))
    return float(1.0 + above + 0.5 * (equal - 1))


def tie_key(cell_index: int, mode: str) -> int:
    if mode == "ascending":
        return cell_index
    if mode == "descending":
        return -cell_index
    if mode.startswith("sha256_"):
        replicate = int(mode.split("_", 1)[1])
        return int.from_bytes(hashlib.sha256(
            f"CTT-SHADOW-TIE-V1|{replicate}|{cell_index}".encode()
        ).digest()[:8], "big", signed=True)
    raise ValueError(f"CTT_SHADOW_UNKNOWN_TIE_MODE:{mode}")


def endpoint(
    rows: list[dict[str, str]], probability: np.ndarray, truth_xy: tuple[float, float],
    *, tie_mode: str,
) -> dict[str, float]:
    """Reproduce PMFS top-5% ExpectedValue and its tie-symmetric guard.

    The official branch uses native ``cell_index`` order for stable sorting.
    The guard fractionally includes every cell tied at the top-5% boundary,
    making the result independent of CSV row order without changing the
    probability field.
    """
    mass = np.asarray(probability, dtype=np.float64)
    if len(rows) != len(mass) or len(rows) == 0 or np.any(mass < 0.0) or not np.isfinite(mass).all():
        raise ValueError("CTT_SHADOW_ENDPOINT_INPUT_FAIL")
    mass = mass / np.sum(mass)
    count = int(math.ceil(len(rows) * 0.05 - 1.0e-15))
    cell_index = np.asarray([int(row["cell_index"]) for row in rows], dtype=np.int64)
    x = np.asarray([float(row["x"]) for row in rows], dtype=np.float64)
    y = np.asarray([float(row["y"]) for row in rows], dtype=np.float64)
    if tie_mode == "symmetric":
        sorted_mass = np.sort(mass)[::-1]
        boundary = sorted_mass[count - 1]
        inclusion = np.zeros(len(rows), dtype=np.float64)
        inclusion[mass > boundary] = 1.0
        ties = mass == boundary
        remaining = count - int(np.count_nonzero(mass > boundary))
        tie_count = int(np.count_nonzero(ties))
        if not 0 < remaining <= tie_count:
            raise ValueError("CTT_SHADOW_TIE_BOUNDARY_FAIL")
        inclusion[ties] = remaining / tie_count
        weights = mass * inclusion
        selected_equivalent = float(np.sum(inclusion))
    else:
        # The secondary key is consulted only for exactly equal probability;
        # it cannot change the ordering of unequal source evidence.
        secondary = np.asarray([tie_key(int(value), tie_mode) for value in cell_index], dtype=np.int64)
        selected = np.lexsort((secondary, -mass))[:count]
        weights = np.zeros(len(rows), dtype=np.float64)
        weights[selected] = mass[selected]
        selected_equivalent = float(len(selected))
    total = float(np.sum(weights))
    if total <= 0.0:
        raise ValueError("CTT_SHADOW_EMPTY_ENDPOINT")
    estimate_x = float(np.sum(x * weights) / total)
    estimate_y = float(np.sum(y * weights) / total)
    selected_variance = float(np.sum(weights * ((x - estimate_x) ** 2 + (y - estimate_y) ** 2)) / total)
    full_mean_x = float(np.sum(x * mass))
    full_mean_y = float(np.sum(y * mass))
    full_variance = float(np.sum(mass * ((x - full_mean_x) ** 2 + (y - full_mean_y) ** 2)))
    return {
        "estimate_x": estimate_x,
        "estimate_y": estimate_y,
        "error_m": float(math.hypot(estimate_x - truth_xy[0], estimate_y - truth_xy[1])),
        "variance_m2": full_variance,
        "selected_variance_m2": selected_variance,
        "selected_cell_equivalent": selected_equivalent,
        "tie_mode": tie_mode,
    }


def load_support(path: Path) -> dict[str, dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    result: dict[str, dict[str, Any]] = {}
    for house in HOUSES:
        house_rows = [row for row in rows if row["house"] == house]
        carriers = sorted({row["carrier_id"] for row in house_rows})
        if len(carriers) != SOURCE_COUNTS[house]:
            raise ValueError(f"CTT_SHADOW_SUPPORT_CARRIER_COUNT:{house}:{len(carriers)}")
        source_index = {carrier: index for index, carrier in enumerate(carriers)}
        key_to_source: dict[tuple[int, int], int] = {}
        key_to_xy: dict[tuple[int, int], tuple[float, float]] = {}
        free_cells = np.zeros(len(carriers), dtype=np.int64)
        for row in house_rows:
            key = (int(row["pmfs_grid_i"]), int(row["pmfs_grid_j"]))
            if key in key_to_source:
                raise ValueError(f"CTT_SHADOW_SUPPORT_DUPLICATE_CELL:{house}:{key}")
            source_id = source_index[row["carrier_id"]]
            key_to_source[key] = source_id
            key_to_xy[key] = (float(row["pmfs_x"]), float(row["pmfs_y"]))
            free_cells[source_id] += 1
        if len(key_to_source) != len(house_rows) or np.any(free_cells <= 0):
            raise ValueError(f"CTT_SHADOW_SUPPORT_COVERAGE:{house}")
        q0 = free_cells.astype(np.float64) / np.sum(free_cells)
        result[house] = {
            "carriers": carriers,
            "source_index": source_index,
            "key_to_source": key_to_source,
            "key_to_xy": key_to_xy,
            "free_cells": free_cells,
            "q0": q0,
            "free_cell_count": len(house_rows),
        }
    return result


def historical_case_root(root: Path, house: str, seed: int) -> Path:
    directory = HOUSE_DIR[house]
    return root / directory / f"seed{seed}" / "off"


def runtime_root(root: Path, house: str, seed: int) -> Path:
    directory = HOUSE_DIR[house]
    return historical_case_root(root, house, seed) / "runtime" / f"{directory}_seed{seed}_off_off"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def read_sensor_measured_only(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Select exactly two authorised columns; never construct sensor row dicts."""
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.reader(source)
        header = next(reader)
        if header.count("t_sim_s") != 1 or header.count("measured_gas_ppm") != 1:
            raise ValueError(f"CTT_SHADOW_SENSOR_SCHEMA_FAIL:{path}")
        time_index = header.index("t_sim_s")
        measured_index = header.index("measured_gas_ppm")
        selected = [(float(row[time_index]), float(row[measured_index])) for row in reader]
    if not selected:
        raise ValueError(f"CTT_SHADOW_SENSOR_EMPTY:{path}")
    return (
        np.asarray([row[0] for row in selected], dtype=np.float64),
        np.asarray([row[1] for row in selected], dtype=np.float64),
    )


def load_observed_case(historical_root: Path, house: str, seed: int, schedule: dict[str, Any]) -> dict[str, Any]:
    runtime = runtime_root(historical_root, house, seed)
    sensor_path = runtime / "sensor_trace.csv"
    pose_path = runtime / "sim_pose_trace.csv"
    timing_path = runtime / "context_bank" / "source_update_timing.csv"
    sensor_time, measured = read_sensor_measured_only(sensor_path)
    pose = read_csv(pose_path)
    timing = read_csv(timing_path)
    if len(sensor_time) != schedule["length"] or len(pose) != schedule["length"] or len(timing) != SOURCE_UPDATES:
        raise ValueError(f"CTT_SHADOW_HISTORICAL_LENGTH_FAIL:{house}:{seed}")
    pose_time = np.asarray([float(row["t_sim_s"]) for row in pose], dtype=np.float64)
    if np.max(np.abs(sensor_time - pose_time)) > 1.0e-9:
        raise ValueError(f"CTT_SHADOW_SENSOR_POSE_TIME_FAIL:{house}:{seed}")
    if not np.isfinite(measured).all() or np.any(measured < 0.0):
        raise ValueError(f"CTT_SHADOW_MEASURED_PPM_FAIL:{house}:{seed}")
    stops = schedule["stops"]
    events = np.asarray([np.any(measured[index] > THRESHOLD_PPM) for index in stops], dtype=np.bool_)
    update_times = np.asarray([float(row["sim_time"]) for row in timing], dtype=np.float64)
    if not np.all(np.diff(update_times) > 0.0):
        raise ValueError(f"CTT_SHADOW_UPDATE_TIME_FAIL:{house}:{seed}")
    visible: list[np.ndarray] = []
    for update_id, update_time in enumerate(update_times, start=1):
        indices = np.asarray(
            [index for index, stop in enumerate(stops) if sensor_time[stop[-1]] <= update_time + TOL],
            dtype=np.int64,
        )
        if len(indices) != 3 * update_id:
            raise ValueError(f"CTT_SHADOW_VISIBLE_STOP_FAIL:{house}:{seed}:{update_id}:{len(indices)}")
        visible.append(indices)
    posterior_paths = [
        runtime / "context_bank" / f"source_update_{update_id:04d}" / "source_posterior.csv"
        for update_id in range(1, SOURCE_UPDATES + 1)
    ]
    hashes = {
        "sensor_trace": sha256_file(sensor_path),
        "sim_pose_trace": sha256_file(pose_path),
        "source_update_timing": sha256_file(timing_path),
    }
    return {
        "runtime": runtime,
        "sensor_time": sensor_time,
        "measured_ppm": measured,
        "observed_events": events,
        "timing": timing,
        "visible": visible,
        "posterior_paths": posterior_paths,
        "hashes": hashes,
    }


def map_native_cells(rows: list[dict[str, str]], timing: dict[str, str], support: dict[str, Any]) -> dict[str, Any]:
    width = int(timing["grid_width"])
    height = int(timing["grid_height"])
    expected = support["key_to_source"]
    seen: set[tuple[int, int]] = set()
    cell_to_source = np.empty(len(rows), dtype=np.int64)
    exported_indices = [int(row["cell_index"]) for row in rows]
    if exported_indices != sorted(exported_indices) or len(exported_indices) != len(set(exported_indices)):
        raise ValueError("CTT_SHADOW_NATIVE_CELL_ORDER_FAIL")
    for row_index, row in enumerate(rows):
        cell = int(row["cell_index"])
        key = (cell % width, cell // width)
        if not (0 <= key[0] < width and 0 <= key[1] < height) or key not in expected or key in seen:
            raise ValueError(f"CTT_SHADOW_NATIVE_CELL_MAPPING_FAIL:{key}")
        seen.add(key)
        expected_xy = support["key_to_xy"][key]
        if max(abs(float(row["x"]) - expected_xy[0]), abs(float(row["y"]) - expected_xy[1])) > 1.0e-5:
            raise ValueError(f"CTT_SHADOW_NATIVE_CELL_COORDINATE_FAIL:{key}")
        cell_to_source[row_index] = expected[key]
    if seen != set(expected) or len(rows) != support["free_cell_count"]:
        raise ValueError(f"CTT_SHADOW_NATIVE_CELL_COVERAGE_FAIL:{len(seen)}:{len(expected)}")
    native_cell = np.asarray([float(row["source_probability"]) for row in rows], dtype=np.float64)
    if np.any(native_cell < 0.0) or not np.isfinite(native_cell).all() or np.sum(native_cell) <= 0.0:
        raise ValueError("CTT_SHADOW_NATIVE_PROBABILITY_FAIL")
    native_cell /= np.sum(native_cell)
    native_carrier = np.bincount(
        cell_to_source, weights=native_cell, minlength=len(support["carriers"])
    ).astype(np.float64)
    if abs(float(np.sum(native_carrier)) - 1.0) > TOL:
        raise ValueError("CTT_SHADOW_NATIVE_CARRIER_MASS_FAIL")
    return {"cell_to_source": cell_to_source, "native_cell": native_cell, "native_carrier": native_carrier}


def carrier_to_cells(carrier_mass: np.ndarray, mapping: dict[str, Any], support: dict[str, Any]) -> np.ndarray:
    mass = np.asarray(carrier_mass, dtype=np.float64)
    result = mass[mapping["cell_to_source"]] / support["free_cells"][mapping["cell_to_source"]]
    if abs(float(np.sum(result)) - 1.0) > TOL:
        raise ValueError("CTT_SHADOW_METHOD_CELL_MASS_FAIL")
    return result


def true_support_indices(
    truth_xy: tuple[float, float], timing: dict[str, str], rows: list[dict[str, str]],
    mapping: dict[str, Any], support: dict[str, Any],
) -> tuple[int, int]:
    origin_x = float(timing["origin_x"])
    origin_y = float(timing["origin_y"])
    cell_size = float(timing["cell_size"])
    key = (
        int(math.floor((truth_xy[0] - origin_x) / cell_size)),
        int(math.floor((truth_xy[1] - origin_y) / cell_size)),
    )
    if key not in support["key_to_source"]:
        raise ValueError(f"CTT_SHADOW_TRUTH_OUTSIDE_SUPPORT:{key}")
    truth_source = int(support["key_to_source"][key])
    truth_cells = [index for index, row in enumerate(rows) if (
        int(row["cell_index"]) % int(timing["grid_width"]),
        int(row["cell_index"]) // int(timing["grid_width"]),
    ) == key]
    if len(truth_cells) != 1 or mapping["cell_to_source"][truth_cells[0]] != truth_source:
        raise ValueError("CTT_SHADOW_TRUTH_MAPPING_FAIL")
    return truth_source, truth_cells[0]


def member_rows_for_house(manifest: list[dict[str, str]], house: str) -> list[dict[str, str]]:
    rows = [row for row in manifest if row["house"] == house and row["split"] == "train"]
    expected = SOURCE_COUNTS[house] * len(PREDICTIVE_MEMBERS)
    if len(rows) != expected:
        raise ValueError(f"CTT_SHADOW_TRAIN_SHARD_COUNT_FAIL:{house}:{len(rows)}:{expected}")
    return rows


def exact_persistent_sensor_tape_matches(physical: np.ndarray, measured: np.ndarray) -> int:
    values = np.asarray(physical, dtype=np.float32)
    observation = np.asarray(measured, dtype=np.float64)
    if values.ndim != 3 or values.shape[2] != len(observation):
        raise ValueError("CTT_SHADOW_EXACT_TAPE_SHAPE_FAIL")
    alpha = math.exp(-DT_S / TAU_S)
    state = np.zeros(values.shape[:2], dtype=np.float64)
    matches = np.ones(values.shape[:2], dtype=np.bool_)
    for time in range(values.shape[2]):
        target = values[:, :, time - DELAY_SAMPLES] if time >= DELAY_SAMPLES else 0.0
        state = alpha * state + (1.0 - alpha) * target
        # Historical sensor_trace is serialized to six decimal places.  Exact
        # tape identity is therefore defined in that authoritative stored
        # representation, not in an unavailable pre-serialization float.
        matches &= np.round(state, 6) == np.round(observation[time], 6)
    return int(np.count_nonzero(matches))


def materialize_train_house(
    bank_root: Path, house: str, manifest: list[dict[str, str]], schedules: list[dict[str, Any]],
    measured_tapes: list[np.ndarray],
) -> tuple[list[tuple[np.ndarray, np.ndarray]], list[str], int, list[int]]:
    rows = member_rows_for_house(manifest, house)
    carriers = sorted({row["carrier_id"] for row in rows})
    if len(carriers) != SOURCE_COUNTS[house]:
        raise ValueError(f"CTT_SHADOW_CARRIER_COUNT_FAIL:{house}")
    source_index = {carrier: index for index, carrier in enumerate(carriers)}
    physical = [
        np.empty((len(carriers), len(PREDICTIVE_MEMBERS), schedule["length"]), dtype=np.float32)
        for schedule in schedules
    ]
    seen: set[tuple[str, int]] = set()
    for count, row in enumerate(rows, start=1):
        member = int(row["member_id"])
        key = (row["carrier_id"], member)
        if member not in PREDICTIVE_MEMBERS or key in seen:
            raise ValueError(f"CTT_SHADOW_TRAIN_SHARD_ID_FAIL:{house}:{key}")
        seen.add(key)
        path = bank_root / row["relative_path"]
        if not path.is_file() or path.stat().st_size != int(row["size_bytes"]):
            raise ValueError(f"CTT_SHADOW_TRAIN_SHARD_FILE_FAIL:{path}")
        streams = read_multistream_verified(path, row["sha256"])
        if len(streams) < len(SEEDS):
            raise ValueError(f"CTT_SHADOW_STREAM_COUNT_FAIL:{path}")
        source = source_index[row["carrier_id"]]
        for seed in SEEDS:
            if len(streams[seed]) != schedules[seed]["length"]:
                raise ValueError(f"CTT_SHADOW_STREAM_LENGTH_FAIL:{house}:{seed}:{path}")
            physical[seed][source, member] = streams[seed]
        if count % 500 == 0 or count == len(rows):
            print(f"CTT_SHADOW_LOAD_{house}={count}/{len(rows)}", flush=True)
    if len(seen) != len(rows):
        raise ValueError(f"CTT_SHADOW_TRAIN_COVERAGE_FAIL:{house}")
    exact_matches = [
        exact_persistent_sensor_tape_matches(physical[seed], measured_tapes[seed]) for seed in SEEDS
    ]
    events = [sensor_events_and_first_passage(physical[seed], schedules[seed]["stops"]) for seed in SEEDS]
    return events, carriers, len(rows), exact_matches


def probability_and_log_terms(train_events: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train = np.asarray(train_events, dtype=np.bool_)
    if train.ndim != 3 or train.shape[1] != len(PREDICTIVE_MEMBERS):
        raise ValueError("CTT_SHADOW_TRAIN_EVENTS_SHAPE_FAIL")
    probability = (np.sum(train, axis=1, dtype=np.float64) + JEFFREYS) / (
        train.shape[1] + 2.0 * JEFFREYS
    )
    return probability, np.log(probability), np.log1p(-probability)


def per_stop_log_likelihood(train_events: np.ndarray, observed_events: np.ndarray) -> np.ndarray:
    _, log_hit, log_miss = probability_and_log_terms(train_events)
    observed = np.asarray(observed_events, dtype=np.bool_)
    if observed.shape != (train_events.shape[2],):
        raise ValueError("CTT_SHADOW_OBSERVED_EVENT_SHAPE_FAIL")
    return np.where(observed[None, :], log_hit, log_miss)


def count_only_score(train_events: np.ndarray, observed_events: np.ndarray, visible: np.ndarray) -> np.ndarray:
    """Frozen count-only temporal control from the preregistration.

    Stop identity is discarded.  Each candidate is represented only by its
    mean reachability probability over the visible prefix and the observed
    tape only by its number of reached stops.
    """
    probability, _, _ = probability_and_log_terms(train_events)
    selected = probability[:, visible]
    pbar = np.mean(selected, axis=1)
    reached = int(np.count_nonzero(np.asarray(observed_events)[visible]))
    count = len(visible)
    return reached * np.log(pbar) + (count - reached) * np.log1p(-pbar)


def stop_label_permuted_score(
    train_events: np.ndarray, observed_events: np.ndarray, visible: np.ndarray,
    *, house: str, seed: int, update_id: int,
) -> np.ndarray:
    """Frozen non-identity candidate-stop-label permutation control."""
    if len(visible) < 2:
        raise ValueError("CTT_SHADOW_STOP_PERMUTE_TOO_SHORT")
    permutation = domain_permutation(
        len(visible), f"SHADOW-STOP-PERMUTE|{house}|{seed}|{update_id}"
    )
    probability, _, _ = probability_and_log_terms(train_events)
    candidate = probability[:, visible[permutation]]
    observed = np.asarray(observed_events, dtype=np.bool_)[visible]
    return np.sum(np.where(observed[None, :], np.log(candidate), np.log1p(-candidate)), axis=1)


def stratified_permutation(free_cells: np.ndarray, house: str, replicate: int) -> np.ndarray:
    """Permute source labels only within equal free-cell-count strata."""
    counts = np.asarray(free_cells, dtype=np.int64)
    result = np.arange(len(counts), dtype=np.int64)
    changed = False
    for value in sorted(set(int(item) for item in counts)):
        members = np.flatnonzero(counts == value)
        if len(members) < 2:
            continue
        local = domain_permutation(
            len(members), f"SHADOW-STRATIFIED-NULL|{house}|{replicate}|{value}"
        )
        result[members] = members[local]
        changed |= not np.array_equal(local, np.arange(len(members)))
    if not changed:
        raise ValueError(f"CTT_SHADOW_STRATIFIED_NULL_IDENTITY:{house}:{replicate}")
    return result


def input_freeze(
    bank_root: Path, historical_root: Path, support_path: Path,
    premise_verdict_path: Path, premise_summary_path: Path, prereg: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    frozen = prereg["frozen_inputs"]
    if str(historical_root.resolve()) != frozen["historical_root"]:
        raise SystemExit("CTT_SHADOW_HISTORICAL_ROOT_FREEZE_FAIL")
    premise = prereg["premise_dependency"]
    if (
        sha256_file(premise_verdict_path) != premise["verdict_sha256"]
        or sha256_file(premise_summary_path) != premise["summary_sha256"]
        or premise_verdict_path.read_text(encoding="utf-8").strip() != premise["required_verdict"]
    ):
        raise SystemExit("CTT_SHADOW_PREMISE_DEPENDENCY_FAIL")
    paths = {
        "bank_summary": bank_root / "bank_summary.json",
        "bank_audit": bank_root / "bank_audit_summary.json",
        "bank_shard_manifest": bank_root / "bank_shard_manifest.csv",
        "region_support_manifest": support_path,
    }
    for key, path in paths.items():
        expected = frozen.get(key + "_sha256")
        if expected is not None and sha256_file(path) != expected:
            raise SystemExit(f"CTT_SHADOW_FROZEN_INPUT_HASH_FAIL:{key}")
    summary = json.loads(paths["bank_summary"].read_text(encoding="utf-8"))
    audit = json.loads(paths["bank_audit"].read_text(encoding="utf-8"))
    if (
        summary.get("contract") != frozen["bank_contract"]
        or audit.get("verdict") != "PF_DEI_V3_NATIVE_BANK_AUDIT_PASS"
        or int(audit.get("shard_count", -1)) != int(frozen["bank_shards"])
        or int(audit.get("total_stream_samples", -1)) != int(frozen["bank_samples"])
        or int(audit.get("total_size_bytes", -1)) != int(frozen["bank_bytes"])
    ):
        raise SystemExit("CTT_SHADOW_BANK_AUDIT_FAIL")
    with paths["bank_shard_manifest"].open(newline="", encoding="utf-8") as source:
        manifest = list(csv.DictReader(source))
    schedules: dict[str, list[dict[str, Any]]] = {}
    historical_hashes: dict[str, Any] = {}
    for house in HOUSES:
        schedules[house] = []
        historical_hashes[house] = {}
        train_hashes = summary["trajectory_schedule_sha256"][house + "_train"]
        train_lengths = summary["trajectory_lengths"][house + "_train"]
        for seed in SEEDS:
            path = historical_schedule(historical_root, house, seed)
            digest = sha256_file(path)
            length, stops = load_complete_stops(path)
            if digest != train_hashes[seed] or length != train_lengths[seed]:
                raise SystemExit(f"CTT_SHADOW_SCHEDULE_MAPPING_FAIL:{house}:{seed}")
            item = {"path": path, "sha256": digest, "length": length, "stops": stops}
            schedules[house].append(item)
            observed = load_observed_case(historical_root, house, seed, item)
            historical_hashes[house][str(seed)] = observed["hashes"]
    freeze = {
        "contract": "CTT_CAUSAL_REACHABILITY_MEASURED_PMFS_INPUT_FREEZE_V1",
        "status": "FROZEN_BEFORE_TRAIN_SHARD_OR_TRUTH_READ",
        "hashes": {key: sha256_file(path) for key, path in paths.items()},
        "schedule_hashes": {
            house: [item["sha256"] for item in schedules[house]] for house in HOUSES
        },
        "historical_measured_only_hashes": historical_hashes,
        "premise_dependency_hashes": {
            "verdict": sha256_file(premise_verdict_path),
            "summary": sha256_file(premise_summary_path),
        },
    }
    return summary, manifest, schedules, freeze


def evaluate_pregroundtruth(
    bank_root: Path, historical_root: Path, manifest: list[dict[str, str]],
    schedules: dict[str, list[dict[str, Any]]], support_all: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Stage 1: build every score/posterior without comparator or truth."""
    records: list[dict[str, Any]] = []
    verified_shards = 0
    for house in HOUSES:
        support = support_all[house]
        observed_cases = [
            load_observed_case(historical_root, house, seed, schedules[house][seed])
            for seed in SEEDS
        ]
        train_by_seed, carriers, shards, exact_matches = materialize_train_house(
            bank_root, house, manifest, schedules[house],
            [item["measured_ppm"] for item in observed_cases],
        )
        verified_shards += shards
        if carriers != support["carriers"]:
            raise ValueError(f"CTT_SHADOW_BANK_SUPPORT_ORDER_FAIL:{house}")
        q0 = support["q0"]
        for seed in SEEDS:
            observed = observed_cases[seed]
            train_events, _ = train_by_seed[seed]
            ll_stop = per_stop_log_likelihood(train_events, observed["observed_events"])
            online_log_mass = np.log(q0)
            consumed: set[int] = set()
            for update_index, (timing, visible) in enumerate(zip(
                observed["timing"], observed["visible"]
            ), start=1):
                new = [int(index) for index in visible if int(index) not in consumed]
                if len(new) != 3:
                    raise ValueError(f"CTT_SHADOW_NEW_STOP_COUNT_FAIL:{house}:{seed}:{update_index}:{len(new)}")
                consumed.update(new)
                score = np.sum(ll_stop[:, visible], axis=1)
                batch = stable_softmax(np.log(q0) + score)
                online_log_mass = np.log(stable_softmax(online_log_mass + np.sum(ll_stop[:, new], axis=1)))
                online = np.exp(online_log_mass)
                max_online_batch = float(np.max(np.abs(online - batch)))
                if max_online_batch > TOL:
                    raise ValueError(f"CTT_SHADOW_ONLINE_BATCH_FAIL:{house}:{seed}:{update_index}:{max_online_batch}")
                count_score = count_only_score(
                    train_events, observed["observed_events"], visible
                )
                permuted_score = stop_label_permuted_score(
                    train_events, observed["observed_events"], visible,
                    house=house, seed=seed, update_id=update_index,
                )
                records.append({
                    "house": house,
                    "seed": seed,
                    "update_id": update_index,
                    "update_time_s": float(timing["sim_time"]),
                    "visible_stops": visible.copy(),
                    "observed_hit_stops": int(np.sum(observed["observed_events"][visible])),
                    "historical_measured_tape_exact_train_member_matches": exact_matches[seed],
                    "timing": timing,
                    "raw_score": score.copy(),
                    "count_only_score": count_score,
                    "stop_label_permute_score": permuted_score,
                    "q0_carrier": q0.copy(),
                    "method_carrier": batch.copy(),
                    "count_only_carrier": stable_softmax(np.log(q0) + count_score),
                    "stop_label_permute_carrier": stable_softmax(np.log(q0) + permuted_score),
                    "max_online_batch_abs": max_online_batch,
                })
        del train_by_seed
        print(f"CTT_SHADOW_PREGROUNDTRUTH_{house}=PASS", flush=True)
    if len(records) != len(HOUSES) * len(SEEDS) * SOURCE_UPDATES:
        raise ValueError(f"CTT_SHADOW_RECORD_COUNT_FAIL:{len(records)}")
    return records, verified_shards


def pretruth_digest(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(f"{record['house']}|{record['seed']}|{record['update_id']}\n".encode())
        for key in (
            "raw_score", "count_only_score", "stop_label_permute_score",
            "q0_carrier", "method_carrier", "count_only_carrier",
            "stop_label_permute_carrier",
        ):
            value = np.asarray(record[key], dtype="<f8", order="C")
            digest.update(key.encode() + b"\0")
            digest.update(value.tobytes())
    return digest.hexdigest()


STAGE1_ARRAY_KEYS = (
    "raw_score", "count_only_score", "stop_label_permute_score",
    "q0_carrier", "method_carrier", "count_only_carrier",
    "stop_label_permute_carrier",
)


def write_stage1_artifact(
    output: Path, records: list[dict[str, Any]], preregistration: Path,
    evaluator: Path, verified_shards: int, input_freeze_sha256: str,
) -> dict[str, Any]:
    arrays: dict[str, np.ndarray] = {}
    metadata: list[dict[str, Any]] = []
    for house in HOUSES:
        subset = [row for row in records if row["house"] == house]
        if len(subset) != len(SEEDS) * SOURCE_UPDATES:
            raise ValueError(f"CTT_SHADOW_STAGE1_HOUSE_COUNT_FAIL:{house}:{len(subset)}")
        for key in STAGE1_ARRAY_KEYS:
            arrays[f"{house}_{key}"] = np.stack([np.asarray(row[key]) for row in subset])
        for local_index, row in enumerate(subset):
            metadata.append({
                "house": house,
                "local_index": local_index,
                "seed": int(row["seed"]),
                "update_id": int(row["update_id"]),
                "update_time_s": float(row["update_time_s"]),
                "visible_stops": [int(value) for value in row["visible_stops"]],
                "observed_hit_stops": int(row["observed_hit_stops"]),
                "historical_measured_tape_exact_train_member_matches": int(
                    row["historical_measured_tape_exact_train_member_matches"]
                ),
                "timing": row["timing"],
                "max_online_batch_abs": float(row["max_online_batch_abs"]),
            })
    npz_path = output / "METHOD_POSTERIORS.npz"
    np.savez_compressed(npz_path, **arrays)
    manifest = {
        "contract": "CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_STAGE1_V1",
        "status": "ALL_150_METHOD_SCORES_AND_POSTERIORS_FROZEN_BEFORE_NATIVE_OR_TRUTH_READ",
        "parent_contract": CONTRACT,
        "records": len(records),
        "verified_training_shards": verified_shards,
        "pretruth_posterior_sha256": pretruth_digest(records),
        "artifact_sha256": sha256_file(npz_path),
        "preregistration_sha256": sha256_file(preregistration),
        "evaluator_sha256": sha256_file(evaluator),
        "input_freeze_sha256": input_freeze_sha256,
        "array_keys": list(STAGE1_ARRAY_KEYS),
        "metadata": metadata,
    }
    manifest_path = output / "METHOD_POSTERIORS_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "STAGE1_SHA256.txt").write_text(
        f"{sha256_file(npz_path)}  METHOD_POSTERIORS.npz\n"
        f"{sha256_file(manifest_path)}  METHOD_POSTERIORS_MANIFEST.json\n",
        encoding="utf-8",
    )
    return manifest


def load_stage1_artifact(
    stage1: Path, preregistration: Path, expected_manifest_sha256: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    npz_path = stage1 / "METHOD_POSTERIORS.npz"
    manifest_path = stage1 / "METHOD_POSTERIORS_MANIFEST.json"
    freeze_path = stage1 / "INPUT_FREEZE.json"
    if sha256_file(manifest_path) != expected_manifest_sha256:
        raise SystemExit("CTT_SHADOW_STAGE1_MANIFEST_EXTERNAL_HASH_FAIL")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("contract") != "CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_STAGE1_V1"
        or manifest.get("status") != "ALL_150_METHOD_SCORES_AND_POSTERIORS_FROZEN_BEFORE_NATIVE_OR_TRUTH_READ"
        or manifest.get("records") != 150
        or manifest.get("artifact_sha256") != sha256_file(npz_path)
        or manifest.get("preregistration_sha256") != sha256_file(preregistration)
        or manifest.get("evaluator_sha256") != sha256_file(Path(__file__))
        or manifest.get("input_freeze_sha256") != sha256_file(freeze_path)
    ):
        raise SystemExit("CTT_SHADOW_STAGE1_ARTIFACT_HASH_OR_CONTRACT_FAIL")
    records: list[dict[str, Any]] = []
    with np.load(npz_path, allow_pickle=False) as archive:
        for item in manifest["metadata"]:
            house = item["house"]
            index = int(item["local_index"])
            row: dict[str, Any] = {key: value for key, value in item.items() if key != "local_index"}
            for key in STAGE1_ARRAY_KEYS:
                row[key] = np.asarray(archive[f"{house}_{key}"][index], dtype=np.float64)
            records.append(row)
    if pretruth_digest(records) != manifest["pretruth_posterior_sha256"]:
        raise SystemExit("CTT_SHADOW_STAGE1_SEMANTIC_HASH_FAIL")
    return records, manifest


def evaluate_after_truth(
    records: list[dict[str, Any]], historical_root: Path,
    support_all: dict[str, dict[str, Any]], prereg: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Stage 2: read comparator/truth only after Stage-1 artifact verification."""
    rows_out: list[dict[str, Any]] = []
    final_internal: list[dict[str, Any]] = []
    case_cache: dict[tuple[str, int], dict[str, Any]] = {}
    comparator_hashes: dict[str, str] = {}
    for record in records:
        house, seed = record["house"], int(record["seed"])
        support = support_all[house]
        runtime = runtime_root(historical_root, house, seed)
        native_path = runtime / "context_bank" / f"source_update_{int(record['update_id']):04d}" / "source_posterior.csv"
        native_rows = read_csv(native_path)
        comparator_hashes[f"{house}_seed{seed}_update{record['update_id']}"] = sha256_file(native_path)
        mapping = map_native_cells(native_rows, record["timing"], support)
        carrier_fields = {
            "full": record["method_carrier"],
            "count_only": record["count_only_carrier"],
            "stop_label_permute": record["stop_label_permute_carrier"],
            "q0": record["q0_carrier"],
        }
        cell_fields = {
            name: carrier_to_cells(value, mapping, support)
            for name, value in carrier_fields.items()
        }
        key = (house, seed)
        if key not in case_cache:
            case_path = historical_case_root(historical_root, house, seed) / "case_result.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            if not case.get("valid") or case.get("primary_metric") != "PMFS_ExpectedValue_top_5_percent":
                raise ValueError(f"CTT_SHADOW_CASE_RESULT_FAIL:{house}:{seed}")
            case["sha256"] = sha256_file(case_path)
            case_cache[key] = case
        case = case_cache[key]
        truth_xy = tuple(float(value) for value in case["truth_eval_only"])
        truth_source, truth_cell = true_support_indices(
            truth_xy, record["timing"], native_rows, mapping, support
        )
        endpoint_fields: dict[str, dict[str, float]] = {}
        modes = ("ascending", "descending", "symmetric", *(f"sha256_{index}" for index in range(16)))
        for channel, cells in {"native": mapping["native_cell"], **cell_fields}.items():
            for mode in modes:
                endpoint_fields[f"{channel}_{mode}"] = endpoint(native_rows, cells, truth_xy, tie_mode=mode)
        output = {
            "house": house,
            "seed": seed,
            "source_update_id": int(record["update_id"]),
            "source_update_time_s": float(record["update_time_s"]),
            "visible_physical_stops": len(record["visible_stops"]),
            "observed_hit_stops": int(record["observed_hit_stops"]),
            "historical_measured_tape_exact_train_member_matches": int(
                record["historical_measured_tape_exact_train_member_matches"]
            ),
            "truth_carrier_id": support["carriers"][truth_source],
            "truth_carrier_index": truth_source,
            "native_true_cell_rank": rank_desc(mapping["native_cell"], truth_cell),
            "native_carrier_true_rank": rank_desc(mapping["native_carrier"], truth_source),
            "geometry_q0_true_rank": rank_desc(record["q0_carrier"], truth_source),
            "raw_reachability_true_rank": rank_desc(record["raw_score"], truth_source),
            "method_posterior_true_rank": rank_desc(record["method_carrier"], truth_source),
            "count_only_posterior_true_rank": rank_desc(record["count_only_carrier"], truth_source),
            "stop_label_permute_posterior_true_rank": rank_desc(record["stop_label_permute_carrier"], truth_source),
            "max_online_batch_abs": float(record["max_online_batch_abs"]),
        }
        for channel in ("native", "full", "count_only", "stop_label_permute", "q0"):
            for mode in modes:
                output[f"{channel}_{mode}_error_m"] = endpoint_fields[f"{channel}_{mode}"]["error_m"]
                output[f"{channel}_{mode}_variance_m2"] = endpoint_fields[f"{channel}_{mode}"]["variance_m2"]
                output[f"{channel}_{mode}_selected_variance_m2"] = endpoint_fields[f"{channel}_{mode}"]["selected_variance_m2"]
        rows_out.append(output)
        if record["update_id"] == SOURCE_UPDATES:
            parity = abs(endpoint_fields["native_ascending"]["error_m"] - float(case["primary_error_m"]))
            if parity > float(prereg["hard_go_rules"]["native_final_error_parity_max_abs_m"]):
                raise ValueError(f"CTT_SHADOW_NATIVE_FINAL_PARITY_FAIL:{house}:{seed}:{parity}")
            final_internal.append({
                **record, **output, "truth_xy": truth_xy,
                "native_rows": native_rows, "mapping": mapping,
                "case_sha256": case["sha256"],
            })

    null_rows: list[dict[str, Any]] = []
    native = np.asarray([row["native_ascending_error_m"] for row in final_internal])
    method = np.asarray([row["full_ascending_error_m"] for row in final_internal])
    native_sym = np.asarray([row["native_symmetric_error_m"] for row in final_internal])
    method_sym = np.asarray([row["full_symmetric_error_m"] for row in final_internal])
    observed_pooled = float((np.sum(native) - np.sum(method)) / np.sum(native))
    observed_pooled_sym = float((np.sum(native_sym) - np.sum(method_sym)) / np.sum(native_sym))
    null_pooled = np.empty(NULL_REPLICATES, dtype=np.float64)
    null_pooled_sym = np.empty(NULL_REPLICATES, dtype=np.float64)
    stratified_pooled = np.empty(NULL_REPLICATES, dtype=np.float64)
    stratified_pooled_sym = np.empty(NULL_REPLICATES, dtype=np.float64)
    for replicate in range(NULL_REPLICATES):
        null_method, null_method_sym = [], []
        strat_method, strat_method_sym = [], []
        for item in final_internal:
            house = item["house"]
            support = support_all[house]
            permutation = domain_permutation(len(support["carriers"]), f"SHADOW-NULL|{house}|{replicate}")
            stratified = stratified_permutation(support["free_cells"], house, replicate)
            for label_map, target, target_sym in (
                (permutation, null_method, null_method_sym),
                (stratified, strat_method, strat_method_sym),
            ):
                carrier = stable_softmax(np.log(item["q0_carrier"]) + item["raw_score"][label_map])
                cells = carrier_to_cells(carrier, item["mapping"], support)
                target.append(endpoint(item["native_rows"], cells, item["truth_xy"], tie_mode="ascending")["error_m"])
                target_sym.append(endpoint(item["native_rows"], cells, item["truth_xy"], tie_mode="symmetric")["error_m"])
        null_pooled[replicate] = float((np.sum(native) - np.sum(null_method)) / np.sum(native))
        null_pooled_sym[replicate] = float((np.sum(native_sym) - np.sum(null_method_sym)) / np.sum(native_sym))
        stratified_pooled[replicate] = float((np.sum(native) - np.sum(strat_method)) / np.sum(native))
        stratified_pooled_sym[replicate] = float((np.sum(native_sym) - np.sum(strat_method_sym)) / np.sum(native_sym))
        null_rows.append({
            "replicate": replicate,
            "unrestricted_ascending_pooled_relative_improvement": null_pooled[replicate],
            "unrestricted_symmetric_pooled_relative_improvement": null_pooled_sym[replicate],
            "free_count_stratified_ascending_pooled_relative_improvement": stratified_pooled[replicate],
            "free_count_stratified_symmetric_pooled_relative_improvement": stratified_pooled_sym[replicate],
        })
    upper_p = lambda null, observed: float((1 + np.count_nonzero(null >= observed)) / (NULL_REPLICATES + 1))

    final_rows = [{key: value for key, value in item.items() if not isinstance(value, (np.ndarray, list, dict, Path, tuple))}
                  for item in final_internal]
    return rows_out, final_rows, null_rows, {
        "unrestricted_ascending_empirical_upper_tail_p": upper_p(null_pooled, observed_pooled),
        "unrestricted_symmetric_empirical_upper_tail_p": upper_p(null_pooled_sym, observed_pooled_sym),
        "free_count_stratified_ascending_empirical_upper_tail_p": upper_p(stratified_pooled, observed_pooled),
        "free_count_stratified_symmetric_empirical_upper_tail_p": upper_p(stratified_pooled_sym, observed_pooled_sym),
        "source_label_null_replicates": NULL_REPLICATES,
        "case_result_sha256": {f"{house}_seed{seed}": case["sha256"] for (house, seed), case in case_cache.items()},
        "native_source_posterior_sha256": comparator_hashes,
    }


def aggregate(
    rows: list[dict[str, Any]], final_rows: list[dict[str, Any]], null_info: dict[str, Any],
    prereg: dict[str, Any], verified_shards: int, pretruth_sha256: str,
) -> dict[str, Any]:
    def metrics(subset: list[dict[str, Any]], mode: str, channel: str = "full") -> dict[str, Any]:
        native = np.asarray([row[f"native_{mode}_error_m"] for row in subset], dtype=np.float64)
        method = np.asarray([row[f"{channel}_{mode}_error_m"] for row in subset], dtype=np.float64)
        relative = (native - method) / native
        catastrophe = (method > native + 1.0) & (method > 1.5 * native)
        native_collapse = (native > 2.0) & (np.asarray([row[f"native_{mode}_variance_m2"] for row in subset]) < 1.0)
        method_collapse = (method > 2.0) & (np.asarray([row[f"{channel}_{mode}_variance_m2"] for row in subset]) < 1.0)
        return {
            "pairs": len(subset),
            "native_mean_error_m": float(np.mean(native)),
            "method_mean_error_m": float(np.mean(method)),
            "pooled_relative_improvement": float((np.sum(native) - np.sum(method)) / np.sum(native)),
            "median_pair_relative_improvement": float(np.median(relative)),
            "improved_pairs": int(np.count_nonzero(method < native - TOL)),
            "tied_pairs": int(np.count_nonzero(np.abs(method - native) <= TOL)),
            "regressed_pairs": int(np.count_nonzero(method > native + TOL)),
            "catastrophic_regressions": int(np.count_nonzero(catastrophe)),
            "native_false_confident_collapses": int(np.count_nonzero(native_collapse)),
            "method_false_confident_collapses": int(np.count_nonzero(method_collapse)),
            "new_false_confident_collapses": int(np.count_nonzero(method_collapse & ~native_collapse)),
        }

    primary_modes = ("ascending", "descending", "symmetric")
    overall = {mode: metrics(final_rows, mode) for mode in primary_modes}
    by_house = {
        house: {mode: metrics([row for row in final_rows if row["house"] == house], mode) for mode in primary_modes}
        for house in HOUSES
    }
    random_sensitivity = {}
    for index in range(16):
        mode = f"sha256_{index}"
        random_sensitivity[mode] = {
            "overall": metrics(final_rows, mode),
            "by_house": {
                house: metrics([row for row in final_rows if row["house"] == house], mode)
                for house in HOUSES
            },
        }
    random_worst = {
        "minimum_pooled_relative_improvement": min(
            item["overall"]["pooled_relative_improvement"] for item in random_sensitivity.values()
        ),
        "minimum_improved_pairs": min(
            item["overall"]["improved_pairs"] for item in random_sensitivity.values()
        ),
        "minimum_house_pooled_relative_improvement": min(
            house_item["pooled_relative_improvement"]
            for item in random_sensitivity.values() for house_item in item["by_house"].values()
        ),
        "maximum_catastrophic_regressions": max(
            item["overall"]["catastrophic_regressions"] for item in random_sensitivity.values()
        ),
    }
    temporal_controls = {
        channel: {mode: metrics(final_rows, mode, channel) for mode in ("ascending", "symmetric")}
        for channel in ("count_only", "stop_label_permute")
    }
    gate = prereg["hard_go_rules"]
    asc, desc, sym = overall["ascending"], overall["descending"], overall["symmetric"]
    full_error = {
        mode: sum(float(row[f"full_{mode}_error_m"]) for row in final_rows)
        for mode in ("ascending", "symmetric")
    }
    control_error = {
        channel: {
            mode: sum(float(row[f"{channel}_{mode}_error_m"]) for row in final_rows)
            for mode in ("ascending", "symmetric")
        }
        for channel in ("count_only", "stop_label_permute")
    }
    rules = {
        "150_updates_and_30_final_pairs": len(rows) == 150 and len(final_rows) == 30,
        "official_pooled_improvement": asc["pooled_relative_improvement"] >= float(gate["official_pooled_relative_improvement_at_least"]),
        "reverse_pooled_improvement": desc["pooled_relative_improvement"] >= float(gate["reverse_order_pooled_relative_improvement_at_least"]),
        "symmetric_pooled_improvement": sym["pooled_relative_improvement"] >= float(gate["tie_symmetrized_pooled_relative_improvement_at_least"]),
        "official_improved_pairs": asc["improved_pairs"] >= int(gate["official_improved_pairs_at_least"]),
        "reverse_improved_pairs": desc["improved_pairs"] >= int(gate["reverse_order_improved_pairs_at_least"]),
        "symmetric_improved_pairs": sym["improved_pairs"] >= int(gate["tie_symmetrized_improved_pairs_at_least"]),
        "official_each_house": all(by_house[h]["ascending"]["pooled_relative_improvement"] >= float(gate["official_each_house_pooled_relative_improvement_at_least"]) for h in HOUSES),
        "reverse_each_house": all(by_house[h]["descending"]["pooled_relative_improvement"] >= float(gate["reverse_order_each_house_pooled_relative_improvement_at_least"]) for h in HOUSES),
        "symmetric_each_house": all(by_house[h]["symmetric"]["pooled_relative_improvement"] >= float(gate["tie_symmetrized_each_house_pooled_relative_improvement_at_least"]) for h in HOUSES),
        "official_median": asc["median_pair_relative_improvement"] >= float(gate["official_median_relative_improvement_at_least"]),
        "reverse_median": desc["median_pair_relative_improvement"] >= float(gate["reverse_order_median_relative_improvement_at_least"]),
        "symmetric_median": sym["median_pair_relative_improvement"] >= float(gate["tie_symmetrized_median_relative_improvement_at_least"]),
        "official_catastrophes": asc["catastrophic_regressions"] <= int(gate["official_catastrophic_regressions_at_most"]),
        "reverse_catastrophes": desc["catastrophic_regressions"] <= int(gate["reverse_order_catastrophic_regressions_at_most"]),
        "symmetric_catastrophes": sym["catastrophic_regressions"] <= int(gate["tie_symmetrized_catastrophic_regressions_at_most"]),
        "no_new_false_confident_collapse": max(asc["new_false_confident_collapses"], desc["new_false_confident_collapses"], sym["new_false_confident_collapses"]) <= int(gate["new_false_confident_collapses_at_most"]),
        "official_source_label_p": null_info["unrestricted_ascending_empirical_upper_tail_p"] <= float(gate["official_source_label_empirical_p_at_most"]),
        "symmetric_source_label_p": null_info["unrestricted_symmetric_empirical_upper_tail_p"] <= float(gate["tie_symmetrized_source_label_empirical_p_at_most"]),
        "free_count_stratified_source_label_p": max(null_info["free_count_stratified_ascending_empirical_upper_tail_p"], null_info["free_count_stratified_symmetric_empirical_upper_tail_p"]) <= float(gate["free_cell_count_stratified_source_label_empirical_p_at_most"]),
        "full_no_worse_than_count_only": all(full_error[mode] <= control_error["count_only"][mode] + TOL for mode in full_error),
        "full_no_worse_than_stop_label_permute": all(full_error[mode] <= control_error["stop_label_permute"][mode] + TOL for mode in full_error),
        "online_equals_batch": max(float(row["max_online_batch_abs"]) for row in rows) <= TOL,
        "historical_measured_tape_exact_train_member_matches_zero": sum(
            int(row["historical_measured_tape_exact_train_member_matches"])
            for row in rows if int(row["source_update_id"]) == 1
        ) == int(gate["historical_measured_tape_exact_train_member_matches"]),
    }
    return {
        "verdict": GO if all(rules.values()) else NO_GO,
        "overall": overall,
        "by_house": by_house,
        "fixed_random_tie_sensitivity": random_sensitivity,
        "fixed_random_tie_worst_case": random_worst,
        "temporal_controls": temporal_controls,
        "hard_pass_rules": rules,
        "source_label_null": {
            "replicates": NULL_REPLICATES,
            **{key: value for key, value in null_info.items() if key.endswith("empirical_upper_tail_p")},
        },
        "verified_training_shards": verified_shards,
        "pretruth_posterior_sha256": pretruth_sha256,
    }


def selftest() -> None:
    import tempfile

    probability = np.asarray([0.1, 0.2, 0.3, 0.4])
    assert np.allclose(stable_softmax(np.log(probability)), probability)
    assert rank_desc(np.asarray([1.0, 1.0, 0.0]), 0) == 1.5
    rows = [
        {"cell_index": str(index), "x": str(float(index)), "y": "0"}
        for index in range(40)
    ]
    mass = np.zeros(40); mass[:4] = 0.25
    official = endpoint(rows, mass, (0.0, 0.0), tie_mode="ascending")
    reverse = endpoint(rows, mass, (0.0, 0.0), tie_mode="descending")
    symmetric = endpoint(rows, mass, (0.0, 0.0), tie_mode="symmetric")
    assert official["selected_cell_equivalent"] == 2.0
    assert abs(symmetric["selected_cell_equivalent"] - 2.0) < TOL
    assert official["estimate_x"] == 0.5 and reverse["estimate_x"] == 2.5 and symmetric["estimate_x"] == 1.5
    for index in range(16):
        assert math.isfinite(endpoint(rows, mass, (0.0, 0.0), tie_mode=f"sha256_{index}")["error_m"])
    events = np.tile(np.asarray([
        [[True, False], [True, True]],
        [[False, False], [False, True]],
    ], dtype=np.bool_), (1, 4, 1))
    ll = per_stop_log_likelihood(events, np.asarray([True, False]))
    assert ll.shape == (2, 2) and np.isfinite(ll).all()
    batch = stable_softmax(np.log(np.asarray([0.5, 0.5])) + np.sum(ll, axis=1))
    online = stable_softmax(np.log(stable_softmax(np.log(np.asarray([0.5, 0.5])) + ll[:, 0])) + ll[:, 1])
    assert np.max(np.abs(batch - online)) <= TOL
    count = count_only_score(events, np.asarray([True, False]), np.asarray([0, 1]))
    permuted = stop_label_permuted_score(
        events, np.asarray([True, False]), np.asarray([0, 1]), house="H01", seed=0, update_id=1
    )
    assert count.shape == (2,) and permuted.shape == (2,)
    mapping = stratified_permutation(np.asarray([1, 1, 2, 2]), "H01", 0)
    assert set(mapping[:2]) == {0, 1} and set(mapping[2:]) == {2, 3}
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        sensor = temporary / "sensor.csv"
        sensor.write_text(
            "t_sim_s,forbidden_column,measured_gas_ppm,other\n0.2,FORBIDDEN,0.3,x\n",
            encoding="utf-8",
        )
        time, measured = read_sensor_measured_only(sensor)
        assert np.array_equal(time, [0.2]) and np.array_equal(measured, [0.3])
        prereg = temporary / "prereg.json"
        prereg.write_text("{}\n", encoding="utf-8")
        freeze = temporary / "INPUT_FREEZE.json"
        freeze.write_text("{}\n", encoding="utf-8")
        synthetic: list[dict[str, Any]] = []
        for house in HOUSES:
            source_count = SOURCE_COUNTS[house]
            for seed in SEEDS:
                for update_id in range(1, SOURCE_UPDATES + 1):
                    row: dict[str, Any] = {
                        "house": house, "seed": seed, "update_id": update_id,
                        "update_time_s": float(update_id),
                        "visible_stops": np.arange(3 * update_id),
                        "observed_hit_stops": update_id,
                        "historical_measured_tape_exact_train_member_matches": 0,
                        "timing": {"grid_width": "1"},
                        "max_online_batch_abs": 0.0,
                    }
                    for key in STAGE1_ARRAY_KEYS:
                        row[key] = np.full(source_count, 1.0 / source_count)
                    synthetic.append(row)
        manifest = write_stage1_artifact(
            temporary, synthetic, prereg, Path(__file__), 4936, sha256_file(freeze)
        )
        loaded, loaded_manifest = load_stage1_artifact(
            temporary, prereg, sha256_file(temporary / "METHOD_POSTERIORS_MANIFEST.json")
        )
        assert manifest["artifact_sha256"] == loaded_manifest["artifact_sha256"]
        assert len(loaded) == 150 and pretruth_digest(loaded) == pretruth_digest(synthetic)
    print("CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--stage", choices=("1", "2"))
    parser.add_argument("--bank-root", type=Path)
    parser.add_argument("--historical-root", type=Path)
    parser.add_argument("--source-support", type=Path)
    parser.add_argument("--premise-verdict", type=Path)
    parser.add_argument("--premise-summary", type=Path)
    parser.add_argument("--stage1-root", type=Path)
    parser.add_argument("--stage1-manifest-sha256")
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    common = (args.stage, args.historical_root, args.source_support, args.preregistration, args.output)
    if any(value is None for value in common):
        raise SystemExit("CTT_SHADOW_REQUIRED_ARGUMENT_MISSING")
    if args.output.exists():
        raise SystemExit(f"CTT_SHADOW_REFUSE_OVERWRITE:{args.output}")
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    if (
        prereg.get("contract") != CONTRACT
        or prereg.get("status") != "PREREGISTERED_BEFORE_HISTORICAL_MEASURED_SCORE_OR_ERROR_READ"
    ):
        raise SystemExit("CTT_SHADOW_PREREGISTRATION_FAIL")
    if sha256_file(args.source_support) != prereg["frozen_inputs"]["region_support_manifest_sha256"]:
        raise SystemExit("CTT_SHADOW_SOURCE_SUPPORT_HASH_FAIL")
    support_all = load_support(args.source_support)
    if args.stage == "1":
        if (
            args.bank_root is None or args.stage1_root is not None
            or args.premise_verdict is None or args.premise_summary is None
        ):
            raise SystemExit("CTT_SHADOW_STAGE1_ARGUMENT_FAIL")
        summary, manifest, schedules, freeze = input_freeze(
            args.bank_root, args.historical_root, args.source_support,
            args.premise_verdict, args.premise_summary, prereg
        )
        args.output.mkdir(parents=True)
        freeze["preregistration_sha256"] = sha256_file(args.preregistration)
        freeze["evaluator_sha256"] = sha256_file(Path(__file__))
        freeze_path = args.output / "INPUT_FREEZE.json"
        freeze_path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        records, verified_shards = evaluate_pregroundtruth(
            args.bank_root, args.historical_root, manifest, schedules, support_all
        )
        stage1 = write_stage1_artifact(
            args.output, records, args.preregistration, Path(__file__), verified_shards,
            sha256_file(freeze_path),
        )
        print(json.dumps({
            "stage": 1,
            "status": stage1["status"],
            "records": stage1["records"],
            "artifact_sha256": stage1["artifact_sha256"],
            "manifest_sha256": sha256_file(args.output / "METHOD_POSTERIORS_MANIFEST.json"),
            "pretruth_posterior_sha256": stage1["pretruth_posterior_sha256"],
        }, indent=2), flush=True)
        return 0

    if args.stage1_root is None or args.bank_root is not None:
        raise SystemExit("CTT_SHADOW_STAGE2_ARGUMENT_FAIL")
    if args.stage1_manifest_sha256 is None:
        raise SystemExit("CTT_SHADOW_STAGE2_MANIFEST_HASH_REQUIRED")
    records, stage1 = load_stage1_artifact(
        args.stage1_root, args.preregistration, args.stage1_manifest_sha256
    )
    args.output.mkdir(parents=True)
    rows, final_rows, null_rows, null_info = evaluate_after_truth(
        records, args.historical_root, support_all, prereg
    )
    result = aggregate(
        rows, final_rows, null_info, prereg,
        int(stage1["verified_training_shards"]), stage1["pretruth_posterior_sha256"],
    )
    report = {
        "contract": CONTRACT,
        "fixed_trajectory_development_only": True,
        "closed_loop_effectiveness_established": False,
        "runtime_and_paired_trial_authorized": result["verdict"] == GO,
        "gaden_runs": 0,
        "neural_training": False,
        "observations": "historical measured_gas_ppm only",
        "method_posterior": "geometry q0 times frozen per-stop reachability likelihood",
        "native_pmfs_posterior_consumed_by_method": False,
        "modules": prereg["scientific_modules"],
        **result,
        "input_hashes": {
            "preregistration": sha256_file(args.preregistration),
            "evaluator": sha256_file(Path(__file__)),
            "stage1_artifact": stage1["artifact_sha256"],
            "stage1_manifest": sha256_file(args.stage1_root / "METHOD_POSTERIORS_MANIFEST.json"),
            "case_results": null_info["case_result_sha256"],
            "native_source_posteriors": null_info["native_source_posterior_sha256"],
        },
    }
    with (args.output / "UPDATES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (args.output / "FINAL_PAIRS.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(final_rows[0])); writer.writeheader(); writer.writerows(final_rows)
    with (args.output / "SOURCE_LABEL_NULLS.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(null_rows[0])); writer.writeheader(); writer.writerows(null_rows)
    (args.output / "SUMMARY.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "VERDICT.txt").write_text(result["verdict"] + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "overall": result["overall"], "by_house": result["by_house"]}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
