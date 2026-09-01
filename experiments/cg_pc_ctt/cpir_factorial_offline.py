#!/usr/bin/env python3
"""Frozen-bank CPIR 2x2 factorial offline evaluator.

Stage 1 reads only frozen predictive banks and historical measurement tapes,
then freezes F00/F01/F10/F11 and STOP-PERMUTE posteriors. Stage 2 verifies the
Stage-1 hashes before reading authoritative PMFS posteriors or source truth.
It never invokes GADEN, trains a model, changes a scientific parameter, or
starts a closed-loop process.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any

import numpy as np

from cpir_three_module_shadow import (
    ALPHA,
    DELAY_SAMPLES,
    DT_S,
    HOUSES,
    HOUSE_DIR,
    MEMBER_COUNT,
    SOURCE_UPDATES,
    STOP_SAMPLES,
    THRESHOLD_PPM,
    BankHouse,
    carrier_scores,
    endpoint,
    load_case,
    projection,
    rank_desc,
    read_csv,
    sha256_file,
)


CONTRACT = "CPIR_FACTORIAL_OFFLINE_V1"
HORIZON_S = 300.0
LOCALIZATION_THRESHOLD_M = 2.0
PAIR_TOL = 1.0e-12
PREREG_NAME = "CPIR_FACTORIAL_OFFLINE_PREREGISTRATION_20260901.json"
ARMS = ("F00", "F01", "F10", "F11")
OUTPUT_ARMS = ("A0", "F00", "F01", "F10", "F11", "STOP_PERMUTE")


def posterior_diagnostics(mass: np.ndarray) -> tuple[float, float]:
    value = np.asarray(mass, dtype=np.float64)
    if value.ndim != 1 or np.any(value < 0) or not np.isfinite(value).all():
        raise RuntimeError("CPIR_FACTORIAL_POSTERIOR_INPUT")
    total = float(np.sum(value))
    if not math.isfinite(total) or total <= 0.0:
        raise RuntimeError("CPIR_FACTORIAL_POSTERIOR_MASS")
    value = value / total
    positive = value[value > 0.0]
    return float(-np.sum(positive * np.log(positive))), float(np.max(value))


def normalized_rank(values: np.ndarray, truth_index: int) -> float:
    if len(values) <= 1:
        raise RuntimeError("CPIR_FACTORIAL_RANK_SUPPORT")
    return float((rank_desc(values, truth_index) - 1.0) / (len(values) - 1.0))


def trapezoid_auc(times: np.ndarray, values: np.ndarray) -> float:
    x = np.asarray(times, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if (x.ndim != 1 or y.ndim != 1 or len(x) != len(y) or len(x) < 2 or
            not np.isfinite(x).all() or not np.isfinite(y).all() or
            np.any(np.diff(x) <= 0.0)):
        raise RuntimeError("CPIR_FACTORIAL_AUC_INPUT")
    return float(np.sum(np.diff(x) * (y[:-1] + y[1:]) * 0.5))


def time_to_threshold(times: np.ndarray, errors: np.ndarray) -> tuple[float, bool]:
    x = np.asarray(times, dtype=np.float64)
    y = np.asarray(errors, dtype=np.float64)
    hits = np.flatnonzero(y <= LOCALIZATION_THRESHOLD_M)
    if len(hits):
        return float(x[int(hits[0])]), True
    return HORIZON_S, False


def exact_sign_p(wins: int, losses: int) -> float:
    n = int(wins + losses)
    if n == 0:
        return 1.0
    return float(sum(math.comb(n, k) for k in range(int(wins), n + 1)) / (2 ** n))


def paired_direction(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    """Test whether the right arm is lower/better than the left arm."""
    x = np.asarray(left, dtype=np.float64)
    y = np.asarray(right, dtype=np.float64)
    if x.shape != y.shape or x.ndim != 1 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise RuntimeError("CPIR_FACTORIAL_PAIRED_INPUT")
    wins = int(np.count_nonzero(y < x - PAIR_TOL))
    losses = int(np.count_nonzero(y > x + PAIR_TOL))
    ties = int(len(x) - wins - losses)
    return {
        "pairs": int(len(x)),
        "left_mean": float(np.mean(x)),
        "right_mean": float(np.mean(y)),
        "mean_difference_left_minus_right": float(np.mean(x - y)),
        "relative_improvement": float((np.sum(x) - np.sum(y)) / np.sum(x))
        if float(np.sum(x)) != 0.0 else None,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "one_sided_exact_sign_p": exact_sign_p(wins, losses),
        "clear_increment": bool(
            float(np.mean(y)) < float(np.mean(x)) and
            wins > losses and exact_sign_p(wins, losses) <= 0.05
        ),
        "worsening_one_sided_exact_sign_p": exact_sign_p(losses, wins),
        "significant_worsening": bool(
            float(np.mean(y)) > float(np.mean(x)) and
            exact_sign_p(losses, wins) <= 0.05
        ),
    }


def deterministic_nonidentity_permutation(
    count: int, house: str, seed: int, update_id: int
) -> np.ndarray:
    if count < 2:
        raise RuntimeError("CPIR_FACTORIAL_STOP_PERMUTE_TOO_SHORT")
    domain = f"CPIR_FACTORIAL_STOP_PERMUTE_V1:{house}:{seed}:{update_id}"
    keys = [hashlib.sha256(f"{domain}:{index}".encode("utf-8")).digest()
            for index in range(count)]
    order = np.asarray(sorted(range(count), key=lambda index: keys[index]), dtype=np.int64)
    if np.array_equal(order, np.arange(count, dtype=np.int64)):
        order = np.roll(order, 1)
    return order


def read_route_streams(path: Path, expected_sha256: str) -> list[np.ndarray]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_SHARD_HASH:{path}")
    if len(raw) < 12 or raw[:8] != b"PFV3STR1":
        raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_SHARD_MAGIC:{path}")
    (count,) = struct.unpack_from("<I", raw, 8)
    header_end = 12 + 4 * count
    if count == 0 or header_end > len(raw):
        raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_SHARD_HEADER:{path}")
    lengths = struct.unpack_from(f"<{count}I", raw, 12)
    if any(length <= 0 for length in lengths) or header_end + 4 * sum(lengths) != len(raw):
        raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_SHARD_LENGTH:{path}")
    flat = np.frombuffer(raw, dtype="<f4", offset=header_end)
    if not np.isfinite(flat).all() or np.any(flat < 0.0):
        raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_SHARD_VALUES:{path}")
    streams = []
    start = 0
    for length in lengths:
        streams.append(flat[start:start + length].copy())
        start += length
    return streams


def build_factorial_events(
    bank: BankHouse, cases: list[Any], route_bank_root: Path,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Use full-grid values, with exact-route fallback only for missing motion."""
    route_manifest_path = route_bank_root / "bank_shard_manifest.csv"
    route_summary_path = route_bank_root / "bank_summary.json"
    route_manifest = read_csv(route_manifest_path)
    route_summary = json.loads(route_summary_path.read_text(encoding="utf-8"))
    if route_summary.get("contract") != "PF_DEI_V3_HISTORICAL_NATIVE_BANK_V1":
        raise RuntimeError("CPIR_FACTORIAL_ROUTE_BANK_CONTRACT")
    rows = [row for row in route_manifest
            if row["house"] == bank.house and row["split"] == "train"]
    row_by_key = {(row["carrier_id"], int(row["member_id"])): row for row in rows}
    expected_keys = {(carrier, member) for carrier in bank.carriers for member in range(MEMBER_COUNT)}
    if set(row_by_key) != expected_keys:
        raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_BANK_CARRIER_SET:{bank.house}")
    schedule_hashes = route_summary["trajectory_schedule_sha256"][bank.house + "_train"]
    schedule_lengths = route_summary["trajectory_lengths"][bank.house + "_train"]
    for case in cases:
        pose_path = case.runtime / "sim_pose_trace.csv"
        if (sha256_file(pose_path) != schedule_hashes[case.seed] or
                len(read_csv(pose_path)) != int(schedule_lengths[case.seed])):
            raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_SCHEDULE:{bank.house}:{case.seed}")
    max_stops = max(len(case.stops) for case in cases)
    raw = np.zeros((len(cases), len(bank.carriers), MEMBER_COUNT, max_stops), dtype=np.bool_)
    stateful = np.zeros_like(raw)
    supported_streams = np.unique(np.concatenate([
        case.stream_indices[case.stream_indices >= 0] for case in cases
    ]))
    stream_position = {int(stream): row for row, stream in enumerate(supported_streams)}
    overlap_values_checked = 0
    overlap_exact_mismatches = 0
    overlap_max_abs = 0.0
    fallback_values_used = 0
    fallback_nonzero_values = 0
    first_mismatch = None
    from cpir_three_module_shadow import read_world_streams
    for carrier_index, carrier in enumerate(bank.carriers):
        for member in range(MEMBER_COUNT):
            full_values = read_world_streams(
                bank.world_paths[carrier_index][member], supported_streams
            )
            route_row = row_by_key[(carrier, member)]
            route_streams = read_route_streams(
                route_bank_root / route_row["relative_path"], route_row["sha256"]
            )
            for case_index, case in enumerate(cases):
                route_tape = np.asarray(route_streams[case.seed][:1500], dtype=np.float32)
                if len(route_tape) != 1500:
                    raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_TAPE_LENGTH:{bank.house}:{case.seed}")
                supported_positions = np.flatnonzero(case.stream_indices >= 0)
                rows_for_case = np.asarray([
                    stream_position[int(case.stream_indices[position])]
                    for position in supported_positions
                ], dtype=np.int64)
                full_tape = full_values[rows_for_case, supported_positions]
                route_overlap = route_tape[supported_positions]
                difference = np.abs(full_tape.astype(np.float64) - route_overlap.astype(np.float64))
                mismatch = full_tape != route_overlap
                overlap_values_checked += int(len(supported_positions))
                overlap_exact_mismatches += int(np.count_nonzero(mismatch))
                if len(difference):
                    overlap_max_abs = max(overlap_max_abs, float(np.max(difference)))
                if np.any(mismatch) and first_mismatch is None:
                    offset = int(np.flatnonzero(mismatch)[0])
                    first_mismatch = {
                        "carrier_id": carrier, "member_id": member,
                        "seed": case.seed, "sample_index": int(supported_positions[offset]),
                        "fullgrid": float(full_tape[offset]),
                        "route": float(route_overlap[offset]),
                    }
                physical = route_tape.copy()
                physical[supported_positions] = full_tape
                fallback_positions = np.flatnonzero(case.stream_indices < 0)
                fallback = physical[fallback_positions]
                fallback_values_used += int(len(fallback))
                fallback_nonzero_values += int(np.count_nonzero(fallback))
                for stop_index, stop in enumerate(case.stops):
                    raw[case_index, carrier_index, member, stop_index] = bool(
                        np.max(physical[stop]) > THRESHOLD_PPM
                    )
                stop_for_time = np.full(1500, -1, dtype=np.int64)
                for stop_index, stop in enumerate(case.stops):
                    stop_for_time[stop] = stop_index
                sensor_state = 0.0; delay_one = 0.0; delay_two = 0.0
                for time in range(1500):
                    target = delay_two
                    delay_two = delay_one
                    delay_one = float(physical[time])
                    sensor_state = ALPHA * sensor_state + (1.0 - ALPHA) * target
                    stop_index = int(stop_for_time[time])
                    if stop_index >= 0 and sensor_state > THRESHOLD_PPM:
                        stateful[case_index, carrier_index, member, stop_index] = True
            completed = carrier_index * MEMBER_COUNT + member + 1
            if completed % 100 == 0 or completed == len(bank.carriers) * MEMBER_COUNT:
                print(f"CPIR_FACTORIAL_EVENT_PROGRESS={bank.house}:{completed}/{len(bank.carriers) * MEMBER_COUNT}", flush=True)
    audit = {
        "contract": "CPIR_FACTORIAL_FULLGRID_ROUTE_COVERAGE_INTERFACE_V1",
        "fullgrid_bank_summary_sha256": bank.summary_sha256,
        "route_bank_summary_sha256": sha256_file(route_summary_path),
        "route_bank_manifest_sha256": sha256_file(route_manifest_path),
        "overlap_values_checked": overlap_values_checked,
        "overlap_exact_mismatches": overlap_exact_mismatches,
        "overlap_max_abs_ppm": overlap_max_abs,
        "fallback_motion_values_used": fallback_values_used,
        "fallback_nonzero_values": fallback_nonzero_values,
        "first_mismatch": first_mismatch,
        "verdict": "CPIR_FACTORIAL_COVERAGE_INTERFACE_PASS"
        if overlap_exact_mismatches == 0 else "CPIR_FACTORIAL_COVERAGE_INTERFACE_INVALID",
    }
    if overlap_exact_mismatches:
        raise RuntimeError(f"CPIR_FACTORIAL_FULLGRID_ROUTE_PARITY:{bank.house}:{first_mismatch}")
    return raw, stateful, audit


def build_route_diagnostic_events(
    bank: BankHouse, cases: list[Any], route_bank_root: Path,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Coverage-complete fixed-tape diagnostic using frozen route shards."""
    manifest_path = route_bank_root / "bank_shard_manifest.csv"
    summary_path = route_bank_root / "bank_summary.json"
    manifest = read_csv(manifest_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("contract") != "PF_DEI_V3_HISTORICAL_NATIVE_BANK_V1":
        raise RuntimeError("CPIR_FACTORIAL_ROUTE_BANK_CONTRACT")
    rows = [row for row in manifest
            if row["house"] == bank.house and row["split"] == "train"]
    row_by_key = {(row["carrier_id"], int(row["member_id"])): row for row in rows}
    expected_keys = {(carrier, member) for carrier in bank.carriers for member in range(MEMBER_COUNT)}
    if set(row_by_key) != expected_keys:
        raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_BANK_CARRIER_SET:{bank.house}")
    schedule_hashes = summary["trajectory_schedule_sha256"][bank.house + "_train"]
    schedule_lengths = summary["trajectory_lengths"][bank.house + "_train"]
    for case in cases:
        pose_path = case.runtime / "sim_pose_trace.csv"
        if (sha256_file(pose_path) != schedule_hashes[case.seed] or
                len(read_csv(pose_path)) != int(schedule_lengths[case.seed])):
            raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_SCHEDULE:{bank.house}:{case.seed}")
    max_stops = max(len(case.stops) for case in cases)
    raw = np.zeros((len(cases), len(bank.carriers), MEMBER_COUNT, max_stops), dtype=np.bool_)
    stateful = np.zeros_like(raw)
    values_checked = 0
    for carrier_index, carrier in enumerate(bank.carriers):
        for member in range(MEMBER_COUNT):
            row = row_by_key[(carrier, member)]
            streams = read_route_streams(route_bank_root / row["relative_path"], row["sha256"])
            for case_index, case in enumerate(cases):
                physical = np.asarray(streams[case.seed][:1500], dtype=np.float32)
                if len(physical) != 1500:
                    raise RuntimeError(f"CPIR_FACTORIAL_ROUTE_TAPE_LENGTH:{bank.house}:{case.seed}")
                values_checked += len(physical)
                for stop_index, stop in enumerate(case.stops):
                    raw[case_index, carrier_index, member, stop_index] = bool(
                        np.max(physical[stop]) > THRESHOLD_PPM
                    )
                stop_for_time = np.full(1500, -1, dtype=np.int64)
                for stop_index, stop in enumerate(case.stops):
                    stop_for_time[stop] = stop_index
                sensor_state = 0.0; delay_one = 0.0; delay_two = 0.0
                for time in range(1500):
                    target = delay_two
                    delay_two = delay_one
                    delay_one = float(physical[time])
                    sensor_state = ALPHA * sensor_state + (1.0 - ALPHA) * target
                    stop_index = int(stop_for_time[time])
                    if stop_index >= 0 and sensor_state > THRESHOLD_PPM:
                        stateful[case_index, carrier_index, member, stop_index] = True
            completed = carrier_index * MEMBER_COUNT + member + 1
            if completed % 500 == 0 or completed == len(bank.carriers) * MEMBER_COUNT:
                print(f"CPIR_FACTORIAL_ROUTE_PROGRESS={bank.house}:{completed}/{len(bank.carriers) * MEMBER_COUNT}", flush=True)
    audit = {
        "contract": "CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_INPUT_V1",
        "route_bank_summary_sha256": sha256_file(summary_path),
        "route_bank_manifest_sha256": sha256_file(manifest_path),
        "verified_shards": len(rows),
        "physical_values_consumed": values_checked,
        "schedule_hashes_verified": 10,
        "fullgrid_runtime_claim": False,
        "verdict": "CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_INPUT_PASS",
    }
    return raw, stateful, audit


def freeze_stage(
    bank_root: Path, historical_root: Path, support_path: Path,
    route_bank_root: Path, prereg_path: Path, output: Path,
    physical_backend: str,
) -> dict[str, Any]:
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    if prereg.get("contract") != CONTRACT or not str(prereg.get("status", "")).startswith("PREREGISTERED_"):
        raise RuntimeError("CPIR_FACTORIAL_PREREG_CONTRACT")
    prereg_backend = prereg.get("physical_backend", "fullgrid_hybrid")
    if prereg_backend != physical_backend:
        raise RuntimeError(
            f"CPIR_FACTORIAL_PREREG_BACKEND:{prereg_backend}:{physical_backend}"
        )
    if physical_backend == "route_diagnostic":
        expected_route = prereg.get("frozen_input_hashes", {}).get("route_bank", {})
        actual_route = {
            "bank_summary_sha256": sha256_file(route_bank_root / "bank_summary.json"),
            "bank_shard_manifest_sha256": sha256_file(
                route_bank_root / "bank_shard_manifest.csv"
            ),
        }
        if expected_route != actual_route:
            raise RuntimeError(
                f"CPIR_FACTORIAL_ROUTE_PREREG_HASH:{expected_route}:{actual_route}"
            )
    support_rows = read_csv(support_path)
    output.mkdir(parents=True, exist_ok=False)
    bank_hashes: dict[str, dict[str, str]] = {}
    coverage_interface: dict[str, Any] = {}
    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        expected_house_hash = prereg.get("frozen_input_hashes", {}).get(
            "fullgrid_bank_summary_sha256", {}
        ).get(house)
        if expected_house_hash is not None and expected_house_hash != bank.summary_sha256:
            raise RuntimeError(
                f"CPIR_FACTORIAL_FULLGRID_PREREG_HASH:{house}:"
                f"{expected_house_hash}:{bank.summary_sha256}"
            )
        cases = [load_case(historical_root, house, seed, bank, strict_full_coverage=False)
                 for seed in range(10)]
        if physical_backend == "route_diagnostic":
            raw, stateful, coverage_interface[house] = build_route_diagnostic_events(
                bank, cases, route_bank_root
            )
        else:
            raw, stateful, coverage_interface[house] = build_factorial_events(
                bank, cases, route_bank_root
            )
        if any(len(case.stops) != raw.shape[-1] for case in cases):
            raise RuntimeError(f"CPIR_FACTORIAL_STOP_COUNT_DRIFT:{house}")
        q_raw = (raw.sum(axis=2) + 0.5) / (MEMBER_COUNT + 1.0)
        q_stateful = (stateful.sum(axis=2) + 0.5) / (MEMBER_COUNT + 1.0)
        records: list[dict[str, Any]] = []
        posterior: dict[str, list[np.ndarray]] = {name: [] for name in (*ARMS, "STOP_PERMUTE")}
        for case_index, case in enumerate(cases):
            for update_id, visible in enumerate(case.visible, start=1):
                _, f00 = carrier_scores(bank.q0, q_raw[case_index], case.observed_events,
                                        visible, "count_only")
                _, f01 = carrier_scores(bank.q0, q_raw[case_index], case.observed_events,
                                        visible, "stop_resolved")
                _, f10 = carrier_scores(bank.q0, q_stateful[case_index], case.observed_events,
                                        visible, "count_only")
                _, f11 = carrier_scores(bank.q0, q_stateful[case_index], case.observed_events,
                                        visible, "stop_resolved")
                permutation = deterministic_nonidentity_permutation(
                    len(visible), house, case.seed, update_id
                )
                q_permuted = q_raw[case_index].copy()
                q_permuted[:, visible] = q_raw[case_index][:, visible[permutation]]
                _, stop_permute = carrier_scores(
                    bank.q0, q_permuted, case.observed_events, visible, "stop_resolved"
                )
                for name, value in {
                    "F00": f00, "F01": f01, "F10": f10, "F11": f11,
                    "STOP_PERMUTE": stop_permute,
                }.items():
                    posterior[name].append(value)
                records.append({
                    "house": house,
                    "seed": case.seed,
                    "update_id": update_id,
                    "update_time_s": float(case.update_times[update_id - 1]),
                    "visible_stops": [int(value) for value in visible],
                    "stop_permutation": [int(value) for value in permutation],
                    "observed_events": [bool(value) for value in case.observed_events],
                })
        np.savez_compressed(
            output / f"{house}_FACTORIAL.npz",
            q_raw=q_raw,
            q_stateful=q_stateful,
            observed=np.stack([case.observed_events for case in cases]),
            carrier_ids=np.asarray(bank.carriers),
            cell_indices=bank.cell_indices,
            cell_to_carrier=bank.cell_to_carrier,
            carrier_cell_counts=bank.carrier_cell_counts,
            **{name.lower(): np.stack(values) for name, values in posterior.items()},
        )
        (output / f"{house}_CASE_META.json").write_text(
            json.dumps({"house": house, "update_records": records}, indent=2) + "\n",
            encoding="utf-8",
        )
        bank_hashes[house] = {
            "bank_summary_sha256": bank.summary_sha256,
            "cell_manifest_sha256": sha256_file(bank.root / "cell_manifest.csv"),
        }
        print(f"CPIR_FACTORIAL_STAGE1_{house}=PASS", flush=True)
    files = {
        path.name: sha256_file(path)
        for path in sorted(output.iterdir()) if path.is_file()
    }
    manifest: dict[str, Any] = {
        "contract": CONTRACT,
        "status": "F00_F01_F10_F11_FROZEN_BEFORE_A0_AND_TRUTH",
        "preregistration_sha256": sha256_file(prereg_path),
        "support_sha256": sha256_file(support_path),
        "bank_hashes": bank_hashes,
        "coverage_interface": coverage_interface,
        "bank_root": str(bank_root),
        "historical_root": str(historical_root),
        "physical_backend": physical_backend,
        "files": files,
        "formula": {
            "dt_s": DT_S, "alpha": ALPHA, "delay_samples": DELAY_SAMPLES,
            "threshold_ppm": THRESHOLD_PPM, "stop_samples": STOP_SAMPLES,
            "member_count": MEMBER_COUNT,
        },
    }
    manifest["semantic_freeze_sha256"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode("utf-8")
    ).hexdigest()
    (output / "FACTORIAL_STAGE1_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def align_cell_mass(rows: list[dict[str, str]], bank: BankHouse) -> np.ndarray:
    by_cell = {int(row["cell_index"]): float(row["source_probability"]) for row in rows}
    if set(by_cell) != set(int(value) for value in bank.cell_indices):
        raise RuntimeError(f"CPIR_FACTORIAL_CELL_SET:{bank.house}")
    mass = np.asarray([by_cell[int(value)] for value in bank.cell_indices], dtype=np.float64)
    if np.any(mass < 0.0) or not np.isfinite(mass).all() or float(np.sum(mass)) <= 0.0:
        raise RuntimeError(f"CPIR_FACTORIAL_CELL_MASS:{bank.house}")
    return mass / float(np.sum(mass))


def metric_record(
    bank: BankHouse, cell_rows: list[dict[str, str]], cell_mass: np.ndarray,
    truth: tuple[float, float], truth_carrier: int, truth_cell_row: int,
) -> dict[str, float]:
    mass = np.asarray(cell_mass, dtype=np.float64)
    carrier_mass = np.bincount(
        bank.cell_to_carrier, weights=mass, minlength=len(bank.carriers)
    )
    result = endpoint(cell_rows, mass, truth)
    entropy, maximum = posterior_diagnostics(mass)
    return {
        "error_m": float(result["error_m"]),
        "true_carrier_rank": rank_desc(carrier_mass, truth_carrier),
        "true_source_normalized_rank": normalized_rank(carrier_mass, truth_carrier),
        "true_cell_rank": rank_desc(mass, truth_cell_row),
        "true_cell_normalized_rank": normalized_rank(mass, truth_cell_row),
        "posterior_entropy_nats": entropy,
        "max_posterior_probability": maximum,
    }


def calibration(values: np.ndarray, observed: np.ndarray) -> dict[str, Any]:
    q = np.asarray(values, dtype=np.float64)
    y = np.asarray(observed, dtype=np.float64)
    if q.shape != y.shape or q.ndim != 1 or np.any(q <= 0.0) or np.any(q >= 1.0):
        raise RuntimeError("CPIR_FACTORIAL_CALIBRATION_INPUT")
    nll = -(y * np.log(q) + (1.0 - y) * np.log1p(-q))
    brier = (q - y) ** 2
    bins = []
    ece = 0.0
    edges = np.linspace(0.0, 1.0, 6)
    for index in range(5):
        mask = ((q >= edges[index]) & (q < edges[index + 1]))
        if index == 4:
            mask = (q >= edges[index]) & (q <= edges[index + 1])
        count = int(np.count_nonzero(mask))
        if count:
            mean_q = float(np.mean(q[mask])); rate = float(np.mean(y[mask]))
            gap = abs(mean_q - rate)
            ece += count / len(q) * gap
        else:
            mean_q = None; rate = None; gap = None
        bins.append({"lower": float(edges[index]), "upper": float(edges[index + 1]),
                     "count": count, "mean_prediction": mean_q,
                     "observed_rate": rate, "absolute_gap": gap})
    hit = y == 1.0; no_hit = ~hit
    return {
        "events": int(len(q)), "hits": int(np.count_nonzero(hit)),
        "no_hits": int(np.count_nonzero(no_hit)),
        "mean_nll": float(np.mean(nll)), "mean_brier": float(np.mean(brier)),
        "ece_5bin": float(ece),
        "hit_mean_predicted_hit_probability": float(np.mean(q[hit])) if np.any(hit) else None,
        "hit_mean_nll": float(np.mean(nll[hit])) if np.any(hit) else None,
        "no_hit_mean_predicted_hit_probability": float(np.mean(q[no_hit])) if np.any(no_hit) else None,
        "no_hit_mean_predicted_no_hit_probability": float(np.mean(1.0 - q[no_hit])) if np.any(no_hit) else None,
        "no_hit_mean_nll": float(np.mean(nll[no_hit])) if np.any(no_hit) else None,
        "bins": bins,
    }


def comparison(
    case_rows: list[dict[str, Any]], left_arm: str, right_arm: str, metric: str,
) -> dict[str, Any]:
    lookup = {(row["house"], int(row["seed"]), row["arm"]): row for row in case_rows}
    keys = [(house, seed) for house in HOUSES for seed in range(10)]
    left = np.asarray([float(lookup[(house, seed, left_arm)][metric]) for house, seed in keys])
    right = np.asarray([float(lookup[(house, seed, right_arm)][metric]) for house, seed in keys])
    result = paired_direction(left, right)
    by_house: dict[str, Any] = {}
    improved_houses = 0
    stable_reverse_houses = []
    for house in HOUSES:
        hkeys = [(house, seed) for seed in range(10)]
        hx = np.asarray([float(lookup[(h, seed, left_arm)][metric]) for h, seed in hkeys])
        hy = np.asarray([float(lookup[(h, seed, right_arm)][metric]) for h, seed in hkeys])
        item = paired_direction(hx, hy)
        item["stable_reverse"] = bool(
            item["right_mean"] > item["left_mean"] and item["losses"] >= 8
        )
        if item["right_mean"] < item["left_mean"]:
            improved_houses += 1
        if item["stable_reverse"]:
            stable_reverse_houses.append(house)
        by_house[house] = item
    result["by_house"] = by_house
    result["improved_house_count"] = improved_houses
    result["stable_reverse_houses"] = stable_reverse_houses
    result["cross_house_repeatable"] = bool(
        improved_houses >= 2 and not stable_reverse_houses
    )
    return result


def evaluate_stage(
    bank_root: Path, historical_root: Path, support_path: Path,
    prereg_path: Path, stage1: Path, output: Path,
) -> dict[str, Any]:
    manifest_path = stage1 / "FACTORIAL_STAGE1_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("contract") != CONTRACT or
            manifest.get("status") != "F00_F01_F10_F11_FROZEN_BEFORE_A0_AND_TRUTH"):
        raise RuntimeError("CPIR_FACTORIAL_STAGE1_CONTRACT")
    if manifest.get("preregistration_sha256") != sha256_file(prereg_path):
        raise RuntimeError("CPIR_FACTORIAL_PREREG_HASH")
    if manifest.get("support_sha256") != sha256_file(support_path):
        raise RuntimeError("CPIR_FACTORIAL_SUPPORT_HASH")
    for name, digest in manifest.get("files", {}).items():
        path = stage1 / name
        if not path.is_file() or sha256_file(path) != digest:
            raise RuntimeError(f"CPIR_FACTORIAL_STAGE1_HASH:{name}")
    support_rows = read_csv(support_path)
    output.mkdir(parents=True, exist_ok=False)
    update_rows: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    mechanism_case_rows: list[dict[str, Any]] = []
    mechanism_event_rows: list[dict[str, Any]] = []
    a0_final_snapshot_max_abs = 0.0
    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        cases = [load_case(historical_root, house, seed, bank, strict_full_coverage=False)
                 for seed in range(10)]
        frozen = np.load(stage1 / f"{house}_FACTORIAL.npz")
        cell_rows = [
            {"cell_index": str(int(cell)), "x": str(float(x)), "y": str(float(y))}
            for cell, x, y in zip(bank.cell_indices, bank.cell_x, bank.cell_y)
        ]
        prior_cell = projection(bank.q0, bank.cell_to_carrier, bank.carrier_cell_counts)
        for case_index, case in enumerate(cases):
            result_path = case.runtime.parent.parent / "case_result.json"
            final_path = case.runtime.parent.parent / "final_posterior.csv"
            native_result = json.loads(result_path.read_text(encoding="utf-8"))
            truth = tuple(float(value) for value in native_result["truth_eval_only"])
            true_ix = int((truth[0] - float(case.timing["origin_x"])) /
                          float(case.timing["cell_size"]))
            true_iy = int((truth[1] - float(case.timing["origin_y"])) /
                          float(case.timing["cell_size"]))
            true_native = true_ix + true_iy * int(case.timing["grid_width"])
            if true_native not in bank.cell_to_stream:
                raise RuntimeError(f"CPIR_FACTORIAL_TRUTH_SUPPORT:{house}:{case.seed}")
            truth_cell_row = bank.cell_to_stream[true_native]
            truth_carrier = int(bank.cell_to_carrier[truth_cell_row])
            prior_metric = metric_record(
                bank, cell_rows, prior_cell, truth, truth_carrier, truth_cell_row
            )
            series: dict[str, list[dict[str, float]]] = {arm: [] for arm in OUTPUT_ARMS}
            for update_index in range(SOURCE_UPDATES):
                record_index = case_index * SOURCE_UPDATES + update_index
                update_dir = case.runtime / "context_bank" / f"source_update_{update_index + 1:04d}"
                a0_mass = align_cell_mass(read_csv(update_dir / "source_posterior.csv"), bank)
                arm_mass = {"A0": a0_mass}
                for arm in (*ARMS, "STOP_PERMUTE"):
                    carrier_mass = np.asarray(frozen[arm.lower()][record_index], dtype=np.float64)
                    arm_mass[arm] = projection(
                        carrier_mass, bank.cell_to_carrier, bank.carrier_cell_counts
                    )
                for arm in OUTPUT_ARMS:
                    item = metric_record(
                        bank, cell_rows, arm_mass[arm], truth,
                        truth_carrier, truth_cell_row,
                    )
                    series[arm].append(item)
                    update_rows.append({
                        "house": house, "seed": case.seed,
                        "update_id": update_index + 1,
                        "update_time_s": float(case.update_times[update_index]),
                        "arm": arm, **item,
                    })
            a0_final_mass = align_cell_mass(read_csv(final_path), bank)
            final_native = metric_record(
                bank, cell_rows, a0_final_mass, truth, truth_carrier, truth_cell_row
            )
            parity_delta = abs(final_native["error_m"] - float(native_result["primary_error_m"]))
            if parity_delta > 1.0e-8:
                raise RuntimeError(f"CPIR_FACTORIAL_A0_ENDPOINT_PARITY:{house}:{case.seed}:{parity_delta}")
            a0_last_mass = align_cell_mass(
                read_csv(case.runtime / "context_bank" / "source_update_0005" / "source_posterior.csv"), bank
            )
            a0_final_snapshot_max_abs = max(
                a0_final_snapshot_max_abs,
                float(np.max(np.abs(a0_final_mass - a0_last_mass))),
            )
            for arm in OUTPUT_ARMS:
                final_item = final_native if arm == "A0" else series[arm][-1]
                errors = np.asarray(
                    [prior_metric["error_m"]] + [item["error_m"] for item in series[arm]] +
                    [final_item["error_m"]], dtype=np.float64
                )
                times = np.asarray(
                    [0.0] + [float(value) for value in case.update_times] + [HORIZON_S],
                    dtype=np.float64,
                )
                if times[-2] >= HORIZON_S:
                    raise RuntimeError(f"CPIR_FACTORIAL_UPDATE_AFTER_HORIZON:{house}:{case.seed}")
                threshold_time, reached = time_to_threshold(times, errors)
                case_rows.append({
                    "house": house, "seed": case.seed, "arm": arm,
                    "final_error_m": final_item["error_m"],
                    "error_auc_m_s": trapezoid_auc(times, errors),
                    "time_to_2m_s": threshold_time,
                    "threshold_reached": int(reached),
                    "final_true_source_normalized_rank": final_item["true_source_normalized_rank"],
                    "final_true_cell_normalized_rank": final_item["true_cell_normalized_rank"],
                    "final_posterior_entropy_nats": final_item["posterior_entropy_nats"],
                    "final_max_posterior_probability": final_item["max_posterior_probability"],
                })
            observed = np.asarray(frozen["observed"][case_index], dtype=np.float64)
            q_raw = np.asarray(frozen["q_raw"][case_index, truth_carrier], dtype=np.float64)
            q_state = np.asarray(frozen["q_stateful"][case_index, truth_carrier], dtype=np.float64)
            raw_nll = -(observed * np.log(q_raw) + (1.0 - observed) * np.log1p(-q_raw))
            state_nll = -(observed * np.log(q_state) + (1.0 - observed) * np.log1p(-q_state))
            raw_brier = (q_raw - observed) ** 2
            state_brier = (q_state - observed) ** 2
            mechanism_case_rows.append({
                "house": house, "seed": case.seed,
                "raw_event_nll": float(np.mean(raw_nll)),
                "persistent_event_nll": float(np.mean(state_nll)),
                "raw_brier": float(np.mean(raw_brier)),
                "persistent_brier": float(np.mean(state_brier)),
                "events": int(len(observed)), "hits": int(np.sum(observed)),
            })
            for stop in range(len(observed)):
                mechanism_event_rows.append({
                    "house": house, "seed": case.seed, "stop_id": stop + 1,
                    "observed_hit": int(observed[stop]),
                    "raw_predicted_hit_probability": float(q_raw[stop]),
                    "persistent_predicted_hit_probability": float(q_state[stop]),
                    "raw_event_nll": float(raw_nll[stop]),
                    "persistent_event_nll": float(state_nll[stop]),
                    "raw_brier": float(raw_brier[stop]),
                    "persistent_brier": float(state_brier[stop]),
                })

    comparisons: dict[str, Any] = {}
    metric_names = (
        "final_error_m", "error_auc_m_s", "time_to_2m_s",
        "final_true_source_normalized_rank",
    )
    for label, left, right in (
        ("M1_F00_vs_A0", "A0", "F00"),
        ("M3_F01_vs_F00", "F00", "F01"),
        ("M2_F11_vs_F01", "F01", "F11"),
        ("M2_INTERACTION_F10_vs_F00", "F00", "F10"),
        ("M3_STATEFUL_F11_vs_F10", "F10", "F11"),
        ("M3_CONTROL_F01_vs_STOP_PERMUTE", "STOP_PERMUTE", "F01"),
    ):
        comparisons[label] = {
            metric: comparison(case_rows, left, right, metric)
            for metric in metric_names
        }

    raw_values = np.asarray([row["raw_predicted_hit_probability"] for row in mechanism_event_rows])
    state_values = np.asarray([row["persistent_predicted_hit_probability"] for row in mechanism_event_rows])
    observed_values = np.asarray([row["observed_hit"] for row in mechanism_event_rows])
    raw_calibration = calibration(raw_values, observed_values)
    persistent_calibration = calibration(state_values, observed_values)
    raw_case_nll = np.asarray([row["raw_event_nll"] for row in mechanism_case_rows])
    state_case_nll = np.asarray([row["persistent_event_nll"] for row in mechanism_case_rows])
    raw_case_brier = np.asarray([row["raw_brier"] for row in mechanism_case_rows])
    state_case_brier = np.asarray([row["persistent_brier"] for row in mechanism_case_rows])
    nll_comparison = paired_direction(raw_case_nll, state_case_nll)
    brier_comparison = paired_direction(raw_case_brier, state_case_brier)
    mechanism_by_house: dict[str, Any] = {}
    mechanism_stable_reverse_houses: set[str] = set()
    for house in HOUSES:
        indices = np.asarray([
            index for index, row in enumerate(mechanism_case_rows)
            if row["house"] == house
        ], dtype=np.int64)
        house_nll = paired_direction(raw_case_nll[indices], state_case_nll[indices])
        house_brier = paired_direction(raw_case_brier[indices], state_case_brier[indices])
        for item in (house_nll, house_brier):
            item["stable_reverse"] = bool(
                item["right_mean"] > item["left_mean"] and item["losses"] >= 8
            )
            if item["stable_reverse"]:
                mechanism_stable_reverse_houses.add(house)
        house_events = [row for row in mechanism_event_rows if row["house"] == house]
        mechanism_by_house[house] = {
            "raw": calibration(
                np.asarray([row["raw_predicted_hit_probability"] for row in house_events]),
                np.asarray([row["observed_hit"] for row in house_events]),
            ),
            "persistent": calibration(
                np.asarray([row["persistent_predicted_hit_probability"] for row in house_events]),
                np.asarray([row["observed_hit"] for row in house_events]),
            ),
            "paired_tape_nll": house_nll,
            "paired_tape_brier": house_brier,
        }
    m2_prediction_pass = bool(
        persistent_calibration["mean_nll"] < raw_calibration["mean_nll"] and
        persistent_calibration["mean_brier"] < raw_calibration["mean_brier"] and
        (nll_comparison["one_sided_exact_sign_p"] <= 0.05 or
         brier_comparison["one_sided_exact_sign_p"] <= 0.05) and
        persistent_calibration["ece_5bin"] <= raw_calibration["ece_5bin"] and
        not mechanism_stable_reverse_houses
    )
    mechanism = {
        "raw": raw_calibration,
        "persistent": persistent_calibration,
        "paired_tape_nll": nll_comparison,
        "paired_tape_brier": brier_comparison,
        "by_house": mechanism_by_house,
        "stable_reverse_houses": sorted(mechanism_stable_reverse_houses),
        "pass": m2_prediction_pass,
    }

    def eligible(label: str, metrics: tuple[str, ...]) -> list[str]:
        return [metric for metric in metrics
                if comparisons[label][metric]["clear_increment"] and
                comparisons[label][metric]["cross_house_repeatable"]]

    m1_selected = eligible("M1_F00_vs_A0", metric_names)
    m1_final = comparisons["M1_F00_vs_A0"]["final_error_m"]
    m1_pass = bool(m1_selected and not m1_final["significant_worsening"])

    m2_selected = eligible(
        "M2_F11_vs_F01", ("final_error_m", "error_auc_m_s", "time_to_2m_s")
    )
    m2_final = comparisons["M2_F11_vs_F01"]["final_error_m"]
    m2_pass = bool(
        m2_prediction_pass and m2_selected and
        not m2_final["significant_worsening"] and
        not m2_final["stable_reverse_houses"]
    )

    m3_selected = eligible(
        "M3_F01_vs_F00", ("final_error_m", "error_auc_m_s")
    )
    m3_rank_direction = bool(
        comparisons["M3_F01_vs_F00"]["final_true_source_normalized_rank"]["right_mean"] <
        comparisons["M3_F01_vs_F00"]["final_true_source_normalized_rank"]["left_mean"]
    )
    m3_final = comparisons["M3_F01_vs_F00"]["final_error_m"]
    m3_control_selected = [
        metric for metric in ("final_error_m", "error_auc_m_s")
        if comparisons["M3_CONTROL_F01_vs_STOP_PERMUTE"][metric]["clear_increment"]
    ]
    m3_control_rank_direction = bool(
        comparisons["M3_CONTROL_F01_vs_STOP_PERMUTE"]["final_true_source_normalized_rank"]["right_mean"] <
        comparisons["M3_CONTROL_F01_vs_STOP_PERMUTE"]["final_true_source_normalized_rank"]["left_mean"]
    )
    m3_pass = bool(
        m3_selected and m3_rank_direction and not m3_final["significant_worsening"] and
        m3_control_selected and m3_control_rank_direction
    )

    lookup = {(row["house"], int(row["seed"]), row["arm"]): row for row in case_rows}
    pooled_means = {
        metric: {
            arm: float(np.mean([
                lookup[(house, seed, arm)][metric]
                for house in HOUSES for seed in range(10)
            ]))
            for arm in ("A0", "F00", "F01", "F11")
        }
        for metric in ("final_error_m", "error_auc_m_s")
    }
    monotone_metrics = [
        metric for metric, means in pooled_means.items()
        if means["A0"] > means["F00"] > means["F01"] > means["F11"]
    ]
    overall_pass = bool(m1_pass and m2_pass and m3_pass and monotone_metrics)
    module_gates = {
        "M1": {"pass": m1_pass, "selected_increment_metrics": m1_selected,
               "verdict": "M1_CAUSAL_PHYSICAL_INTERVENTION_PASS" if m1_pass else "M1_CAUSAL_PHYSICAL_INTERVENTION_NO_GO"},
        "M2": {"pass": m2_pass, "prediction_gate_pass": m2_prediction_pass,
               "selected_increment_metrics": m2_selected,
               "verdict": "M2_PERSISTENT_SENSOR_MAIN_MODULE_PASS" if m2_pass else "M2_PERSISTENT_SENSOR_MAIN_MODULE_NO_GO"},
        "M3": {"pass": m3_pass, "selected_increment_metrics": m3_selected,
               "stop_permute_increment_metrics": m3_control_selected,
               "rank_same_direction": m3_rank_direction,
               "stop_permute_rank_same_direction": m3_control_rank_direction,
               "verdict": "M3_STOP_RESOLVED_MAIN_MODULE_PASS" if m3_pass else "M3_STOP_RESOLVED_MAIN_MODULE_NO_GO"},
    }

    def write_csv(name: str, rows: list[dict[str, Any]]) -> None:
        with (output / name).open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)

    write_csv("PER_UPDATE_METRICS.csv", update_rows)
    write_csv("CASE_METRICS.csv", case_rows)
    write_csv("M2_MECHANISM_CASES.csv", mechanism_case_rows)
    write_csv("M2_MECHANISM_EVENTS.csv", mechanism_event_rows)
    physical_backend = str(manifest.get("physical_backend", "fullgrid_hybrid"))
    if physical_backend == "route_diagnostic":
        final_verdict = (
            "CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_THREE_MODULE_PASS"
            if overall_pass else "CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_NO_GO"
        )
    else:
        final_verdict = "CPIR_FACTORIAL_OFFLINE_PASS_TO_PARITY" if overall_pass else "CPIR_FACTORIAL_OFFLINE_NO_GO"
    report: dict[str, Any] = {
        "contract": CONTRACT,
        "status": "FACTORIAL_OFFLINE_COMPLETE",
        "verdict": final_verdict,
        "closed_loop": False,
        "gaden_runs": 0,
        "neural_training": False,
        "scientific_parameters_changed": False,
        "physical_backend": physical_backend,
        "parity_or_closed_loop_authorized": bool(
            overall_pass and physical_backend != "route_diagnostic"
        ),
        "case_count": 30,
        "update_rows": len(update_rows),
        "module_gates": module_gates,
        "m2_predictive_mechanism": mechanism,
        "comparisons": comparisons,
        "pooled_progression": pooled_means,
        "monotone_progression_metrics": monotone_metrics,
        "a0_final_vs_update5_posterior_max_abs": a0_final_snapshot_max_abs,
        "stage1_manifest_sha256": sha256_file(manifest_path),
        "preregistration_sha256": sha256_file(prereg_path),
        "support_sha256": sha256_file(support_path),
        "notes": [
            "A0 and all factorial arms use the same historical measurement tape and source-update times.",
            "AUC includes the common t=0 prior and carries the final posterior to 300 s.",
            "This is fixed-trajectory offline evidence, not closed loop.",
            "A route_diagnostic backend can reject modules but cannot authorize full-grid runtime parity or closed loop.",
        ],
    }
    (output / "SUMMARY.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    verdict_lines = [final_verdict] + [module_gates[name]["verdict"] for name in ("M1", "M2", "M3")]
    (output / "VERDICT.txt").write_text("\n".join(verdict_lines) + "\n", encoding="utf-8")
    return report


def selftest() -> None:
    assert math.isclose(trapezoid_auc(np.asarray([0.0, 1.0, 2.0]),
                                      np.asarray([2.0, 1.0, 0.0])), 2.0)
    time, reached = time_to_threshold(np.asarray([0.0, 10.0, 300.0]),
                                      np.asarray([5.0, 1.5, 1.5]))
    assert reached and time == 10.0
    time, reached = time_to_threshold(np.asarray([0.0, 10.0, 300.0]),
                                      np.asarray([5.0, 3.0, 2.1]))
    assert not reached and time == 300.0
    assert exact_sign_p(5, 0) == 0.03125
    assert paired_direction(np.arange(1.0, 7.0), np.arange(0.0, 6.0))["clear_increment"]
    for count in range(2, 16):
        permutation = deterministic_nonidentity_permutation(count, "H01", 0, 1)
        assert sorted(permutation.tolist()) == list(range(count))
        assert not np.array_equal(permutation, np.arange(count))
    cal = calibration(np.asarray([0.1, 0.9]), np.asarray([0.0, 1.0]))
    assert math.isclose(cal["mean_brier"], 0.01)
    print("CPIR_FACTORIAL_OFFLINE_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--stage", choices=("1", "2"))
    parser.add_argument("--bank-root", type=Path)
    parser.add_argument("--historical-root", type=Path)
    parser.add_argument("--route-bank-root", type=Path)
    parser.add_argument("--physical-backend", choices=("fullgrid_hybrid", "route_diagnostic"),
                        default="fullgrid_hybrid")
    parser.add_argument("--support", type=Path)
    parser.add_argument("--prereg", type=Path,
                        default=Path(__file__).resolve().parents[2] / "docs" / PREREG_NAME)
    parser.add_argument("--stage1", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest(); return 0
    if not args.stage or not args.bank_root or not args.historical_root or not args.support or not args.output:
        parser.error("--stage/--bank-root/--historical-root/--support/--output required")
    if args.output.exists():
        raise SystemExit(f"CPIR_FACTORIAL_REFUSE_OVERWRITE:{args.output}")
    if args.stage == "1":
        if not args.route_bank_root:
            parser.error("--route-bank-root required for Stage 1 motion-coverage interface")
        freeze_stage(
            args.bank_root, args.historical_root, args.support,
            args.route_bank_root, args.prereg, args.output,
            args.physical_backend,
        )
    else:
        if not args.stage1:
            parser.error("--stage1 required for stage 2")
        report = evaluate_stage(
            args.bank_root, args.historical_root, args.support,
            args.prereg, args.stage1, args.output,
        )
        print(json.dumps({
            "verdict": report["verdict"],
            "module_gates": report["module_gates"],
            "pooled_progression": report["pooled_progression"],
        }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
