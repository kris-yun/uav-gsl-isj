#!/usr/bin/env python3
"""Evaluate the prospective H01 fixed-U transport-coherence premise.

Six predictive and seven prospectively frozen observation realizations share
the exact same source placement U0, wind context, source strength, sensor and
route.  Independent inference is over the seven observation realizations;
source ranks and two fixed routes are aggregated within each realization.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np

from ctt_h01_wind_bank_io import (
    FIRST_PASSAGE_THRESHOLD_PPM,
    STOP_SAMPLES,
    read_physical,
    sensor_forward,
    sha256_file,
)
from materialize_ctt_h01_fixed_u_transport_gate import (
    CONTRACT as BANK_CONTRACT,
    HELD_MEMBERS,
    K_BY_MEMBER,
    PASS as BANK_PASS,
    PREDICTIVE_MEMBERS,
    ROUTES,
    SOURCE_COUNT,
)


CONTRACT = "CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_V2"
PASS = "CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_PASS"
NO_GO = "CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_NO_GO"
EVALUATION_ROUTES = (4004, 4005)
ROUTE_TO_STREAM = {route: index for index, route in enumerate(ROUTES)}
NULL_REPLICATES = 256
ALPHA = 0.01
TOLERANCE = 1.0e-12
ABSOLUTE_RANK_MAX_EXCLUSIVE = 0.35


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + ".tmp.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as target:
            target.write(value)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"CTT_FIXED_U8_EVAL_JSON_OBJECT_REQUIRED:{path}")
    return payload


def load_stops(path: Path) -> list[np.ndarray]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"CTT_FIXED_U8_EVAL_EMPTY_SCHEDULE:{path}")
    stops = []
    for stop_id in sorted({int(row["stop_id"]) for row in rows}):
        indices = np.asarray([
            index for index, row in enumerate(rows)
            if int(row["stop_id"]) == stop_id and int(row["is_moving"]) == 0
        ], dtype=np.int64)
        if not len(indices):
            continue
        # The frozen trajectory generator may keep the UAV stationary beyond
        # the 80-sample sensing block, while a final truncated stop may contain
        # fewer than 80 samples.  Every authoritative CTT first-passage reader
        # uses the first 80 stationary samples and excludes incomplete blocks.
        if len(indices) < STOP_SAMPLES:
            continue
        stops.append(indices[:STOP_SAMPLES])
    if len(stops) < 3:
        raise ValueError(f"CTT_FIXED_U8_EVAL_TOO_FEW_STOPS:{path}:{len(stops)}")
    return stops


def detection(path: Path, stream_index: int, stops: list[np.ndarray]) -> np.ndarray:
    streams = read_physical(path)
    if len(streams) != len(ROUTES):
        raise ValueError(f"CTT_FIXED_U8_EVAL_STREAM_COUNT_FAIL:{path}:{len(streams)}")
    measured = sensor_forward(streams[stream_index])
    return np.asarray([
        bool(np.any(measured[indices] > FIRST_PASSAGE_THRESHOLD_PPM))
        for indices in stops
    ], dtype=np.bool_)


def log_mean_exp(values: np.ndarray, axis: int) -> np.ndarray:
    maximum = np.max(values, axis=axis, keepdims=True)
    return np.squeeze(maximum, axis=axis) + np.log(
        np.mean(np.exp(values - maximum), axis=axis)
    )


def score_matrices(predictive: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return [observation-source,candidate-source] coherent and redraw scores."""
    predictive = np.asarray(predictive, dtype=np.bool_)
    observed = np.asarray(observed, dtype=np.bool_)
    if (
        predictive.ndim != 3 or predictive.shape[1] != len(PREDICTIVE_MEMBERS)
        or observed.ndim != 2 or predictive.shape[0] != observed.shape[0]
        or predictive.shape[2] != observed.shape[1]
    ):
        raise ValueError(f"CTT_FIXED_U8_EVAL_SCORE_SHAPE_FAIL:{predictive.shape}:{observed.shape}")
    # Frozen one-realization Jeffreys posterior predictive: miss=.25, hit=.75.
    probability = (0.5 + predictive.astype(np.float64)) / 2.0
    if set(np.unique(probability)) - {0.25, 0.75}:
        raise AssertionError("CTT_FIXED_U8_EVAL_NONFROZEN_PROBABILITY")
    y = observed.astype(np.float64)
    # Matrix products avoid allocating [observation,source,K,stop] for every
    # deterministic destruction replicate.
    source_count, k_count, stop_count = probability.shape
    log_probability = np.log(probability).reshape(source_count * k_count, stop_count)
    log_complement = np.log1p(-probability).reshape(source_count * k_count, stop_count)
    per_k = (
        y @ log_probability.T + (1.0 - y) @ log_complement.T
    ).reshape(len(y), source_count, k_count)
    coherent = log_mean_exp(per_k, axis=2)
    mean_probability = probability.mean(axis=1)
    redraw = (
        y[:, None, :] * np.log(mean_probability)[None, :, :]
        + (1.0 - y[:, None, :]) * np.log1p(-mean_probability)[None, :, :]
    ).sum(axis=2)
    return coherent, redraw


def online_coherent(predictive: np.ndarray, observed: np.ndarray) -> np.ndarray:
    probability = (0.5 + np.asarray(predictive, dtype=np.float64)) / 2.0
    y = np.asarray(observed, dtype=np.float64)
    accumulated = np.zeros((len(y), predictive.shape[0], predictive.shape[1]), dtype=np.float64)
    for stop in range(predictive.shape[2]):
        accumulated += (
            y[:, None, None, stop] * np.log(probability)[None, :, :, stop]
            + (1.0 - y[:, None, None, stop]) * np.log1p(-probability)[None, :, :, stop]
        )
    return log_mean_exp(accumulated, axis=2)


def midrank_desc_matrix(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 2 or scores.shape[1] < 2 or not np.isfinite(scores).all():
        raise ValueError("CTT_FIXED_U8_EVAL_RANK_INPUT_FAIL")
    result = np.empty_like(scores)
    for row_index, row in enumerate(scores):
        order = np.argsort(-row, kind="stable")
        position = 0
        while position < len(order):
            end = position + 1
            value = row[order[position]]
            while end < len(order) and row[order[end]] == value:
                end += 1
            result[row_index, order[position:end]] = 1.0 + position + 0.5 * (end - position - 1)
            position = end
    return result


def positive_sign_test(unit_improvement: np.ndarray) -> dict:
    value = np.asarray(unit_improvement, dtype=np.float64)
    wins = int(np.count_nonzero(value > 0.0))
    losses = int(np.count_nonzero(value < 0.0))
    ties = int(np.count_nonzero(value == 0.0))
    count = wins + losses
    p = (
        sum(math.comb(count, k) for k in range(wins, count + 1)) / (2 ** count)
        if count else 1.0
    )
    return {
        "unit": "prospective_observation_transport_realization",
        "units": len(value),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "one_sided_exact_p": float(p),
    }


def empirical_upper_p(observed: float, null: np.ndarray) -> float:
    return float((1 + np.count_nonzero(np.asarray(null) >= observed)) / (len(null) + 1))


def summarize_rank(rank: np.ndarray) -> dict:
    rank = np.asarray(rank, dtype=np.float64)
    normalized = (rank - 1.0) / (SOURCE_COUNT - 1.0)
    return {
        "cases": len(rank), "mean_normalized_rank": float(normalized.mean()),
        "median_rank": float(np.median(rank)), "top5": float(np.mean(rank <= 5.0)),
        "top10": float(np.mean(rank <= 10.0)),
    }


def read_factorial_manifest(
    formal_bank: Path, fixed_bank: Path, expected_hash: str,
) -> tuple[list[str], dict[tuple[str, int], Path]]:
    manifest = fixed_bank / "FACTORIAL_SHA256.tsv"
    if sha256_file(manifest) != expected_hash:
        raise ValueError("CTT_FIXED_U8_EVAL_FACTORIAL_MANIFEST_HASH_FAIL")
    with manifest.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    if len(rows) != SOURCE_COUNT * len(K_BY_MEMBER):
        raise ValueError(f"CTT_FIXED_U8_EVAL_FACTORIAL_COVERAGE_FAIL:{len(rows)}")
    carriers = sorted({row["carrier_id"] for row in rows})
    if len(carriers) != SOURCE_COUNT:
        raise ValueError("CTT_FIXED_U8_EVAL_CARRIER_COUNT_FAIL")
    paths: dict[tuple[str, int], Path] = {}
    xyz: dict[str, tuple[str, str, str]] = {}
    for row in rows:
        carrier = row["carrier_id"]
        member = int(row["transport_member"])
        key = (carrier, member)
        if key in paths or member not in range(len(K_BY_MEMBER)):
            raise ValueError(f"CTT_FIXED_U8_EVAL_FACTORIAL_KEY_FAIL:{key}")
        if int(row["u_member"]) != 0 or int(row["transport_seed"]) != K_BY_MEMBER[member]:
            raise ValueError(f"CTT_FIXED_U8_EVAL_FACTOR_IDENTITY_FAIL:{key}")
        coordinates = (row["x"], row["y"], row["z"])
        if carrier in xyz and xyz[carrier] != coordinates:
            raise ValueError(f"CTT_FIXED_U8_EVAL_U_NOT_FIXED:{carrier}")
        xyz[carrier] = coordinates
        expected_root = "prospective_fixed_u"
        if row["storage_root"] != expected_root:
            raise ValueError(f"CTT_FIXED_U8_EVAL_STORAGE_ROOT_FAIL:{key}")
        root = fixed_bank
        path = root / row["relative_path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise ValueError(f"CTT_FIXED_U8_EVAL_SHARD_HASH_FAIL:{key}")
        paths[key] = path
    if set(paths) != {
        (carrier, member)
        for carrier in carriers
        for member in range(len(K_BY_MEMBER))
    }:
        raise ValueError("CTT_FIXED_U8_EVAL_FACTORIAL_KEY_COVERAGE_FAIL")
    return carriers, paths


def transport_unit_statistic(
    stratum_delta: list[tuple[int, int, np.ndarray]],
) -> tuple[np.ndarray, float]:
    """Aggregate sources and fixed routes within each observation realization."""
    units = []
    for observation_member in HELD_MEMBERS:
        arrays = [
            np.asarray(delta, dtype=np.float64)
            for route, member, delta in stratum_delta
            if member == observation_member and route in EVALUATION_ROUTES
        ]
        if len(arrays) != len(EVALUATION_ROUTES):
            raise ValueError(
                f"CTT_FIXED_U8_EVAL_TRANSPORT_UNIT_COVERAGE:{observation_member}"
            )
        if any(array.shape != (SOURCE_COUNT,) for array in arrays):
            raise ValueError("CTT_FIXED_U8_EVAL_TRANSPORT_UNIT_SHAPE")
        units.append(float(np.mean(np.concatenate(arrays))))
    result = np.asarray(units, dtype=np.float64)
    if result.shape != (len(HELD_MEMBERS),):
        raise ValueError("CTT_FIXED_U8_EVAL_TRANSPORT_UNIT_COUNT")
    return result, float(result.mean())


def selftest() -> None:
    with tempfile.TemporaryDirectory() as directory:
        schedule = Path(directory) / "schedule.csv"
        with schedule.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=("stop_id", "is_moving"))
            writer.writeheader()
            # Complete, overlong and incomplete physical stops exercise the
            # exact frozen block extraction rule used by prior CTT audits.
            for stop_id, count in ((1, STOP_SAMPLES), (2, STOP_SAMPLES + 10),
                                   (3, STOP_SAMPLES - 1), (4, STOP_SAMPLES)):
                writer.writerows(
                    {"stop_id": stop_id, "is_moving": 0} for _ in range(count)
                )
        extracted = load_stops(schedule)
        assert len(extracted) == 3
        assert all(len(indices) == STOP_SAMPLES for indices in extracted)
        assert int(extracted[1][-1] - extracted[1][0] + 1) == STOP_SAMPLES
    predictive = np.asarray([
        [[1, 0, 1], [1, 0, 1], [1, 0, 1], [0, 1, 0], [0, 1, 0], [0, 1, 0]],
        [[0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 0, 1], [1, 0, 1], [1, 0, 1]],
        [[1, 1, 0], [1, 1, 0], [0, 0, 1], [0, 0, 1], [1, 0, 0], [0, 1, 1]],
    ], dtype=np.bool_)
    observed = np.asarray([[1, 0, 1], [0, 1, 0], [1, 1, 0]], dtype=np.bool_)
    coherent, redraw = score_matrices(predictive, observed)
    assert np.max(np.abs(coherent - online_coherent(predictive, observed))) <= TOLERANCE
    swapped_coherent, swapped_redraw = score_matrices(predictive[:, ::-1], observed)
    assert np.array_equal(coherent, swapped_coherent)
    assert np.array_equal(redraw, swapped_redraw)
    permutation = np.asarray([2, 0, 1])
    row_coherent, row_redraw = score_matrices(predictive[permutation], observed)
    restored_coherent = np.empty_like(row_coherent)
    restored_redraw = np.empty_like(row_redraw)
    restored_coherent[:, permutation] = row_coherent
    restored_redraw[:, permutation] = row_redraw
    assert np.array_equal(coherent, restored_coherent)
    assert np.array_equal(redraw, restored_redraw)
    ranks = midrank_desc_matrix(np.asarray([[2.0, 2.0, 1.0]]))
    assert np.array_equal(ranks, np.asarray([[1.5, 1.5, 3.0]]))
    sign = positive_sign_test(np.asarray([1.0, 1.0, -1.0, 0.0]))
    assert sign["wins"] == 2 and sign["losses"] == 1 and sign["ties"] == 1
    unit_rows = []
    for route in EVALUATION_ROUTES:
        for member in HELD_MEMBERS:
            unit_rows.append((route, member, np.full(SOURCE_COUNT, member + route)))
    units, overall = transport_unit_statistic(unit_rows)
    assert len(units) == len(HELD_MEMBERS) and np.isclose(overall, units.mean())
    print("CTT_H01_FIXED_U_TRANSPORT_GATE_EVALUATOR_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-bank", type=Path)
    parser.add_argument("--fixed-bank", type=Path)
    parser.add_argument("--placement-manifest", type=Path)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--null-maps", type=Path)
    parser.add_argument("--evaluation-addendum", type=Path)
    parser.add_argument("--schedule-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    required = (
        "formal_bank", "fixed_bank", "placement_manifest", "preregistration",
        "null_maps", "evaluation_addendum", "schedule_root", "output",
    )
    missing = [name for name in required if getattr(args, name) is None]
    if missing:
        raise SystemExit("CTT_FIXED_U8_EVAL_MISSING_ARGUMENTS:" + ",".join(missing))
    if args.output.exists():
        raise SystemExit(f"CTT_FIXED_U8_EVAL_REFUSE_OVERWRITE:{args.output}")

    fixed_summary_path = args.fixed_bank / "bank_summary.json"
    formal_summary_path = args.formal_bank / "bank_summary.json"
    fixed_summary = load_json(fixed_summary_path)
    if not (
        fixed_summary.get("contract") == BANK_CONTRACT
        and fixed_summary.get("verdict") == BANK_PASS
        and fixed_summary.get("scientific_scope")
        == "fixed_U0_6_predictive_to_7_prospective_observation_K"
        and fixed_summary.get("predictive_members") == list(PREDICTIVE_MEMBERS)
        and fixed_summary.get("held_members") == list(HELD_MEMBERS)
        and fixed_summary.get("transport_seed_by_member") == list(K_BY_MEMBER)
    ):
        raise SystemExit("CTT_FIXED_U8_EVAL_BANK_CONTRACT_FAIL")
    if fixed_summary["input_hashes"]["formal_bank_summary"] != sha256_file(formal_summary_path):
        raise SystemExit("CTT_FIXED_U8_EVAL_FORMAL_SUMMARY_LINK_FAIL")
    if fixed_summary["input_hashes"]["placement_manifest"] != sha256_file(args.placement_manifest):
        raise SystemExit("CTT_FIXED_U8_EVAL_PLACEMENT_LINK_FAIL")
    formal_summary = load_json(formal_summary_path)
    if formal_summary.get("contract") != "CTT_H01_WIND_CONDITIONED_NATIVE_BANK_V1":
        raise SystemExit("CTT_FIXED_U8_EVAL_FORMAL_BANK_FAIL")
    preregistration = load_json(args.preregistration)
    if (
        preregistration.get("contract") != CONTRACT
        or preregistration.get("status") != "PREREGISTERED_NOT_RUN"
        or preregistration.get("closed_loop_authorized") is not False
        or preregistration.get("destruction_controls", {}).get("deterministic_null_replicates")
        != NULL_REPLICATES
        or preregistration.get("pass_rules", {}).get("absolute_ordering", {}).get(
            "mean_normalized_true_carrier_midrank_coherent_max_exclusive"
        ) != ABSOLUTE_RANK_MAX_EXCLUSIVE
    ):
        raise SystemExit("CTT_FIXED_U8_EVAL_PREREGISTRATION_CONTRACT_FAIL")
    if preregistration.get("scope", {}).get("independent_inference_units") != len(
        HELD_MEMBERS
    ):
        raise SystemExit("CTT_FIXED_U8_EVAL_INFERENCE_UNIT_CONTRACT_FAIL")
    null_maps = load_json(args.null_maps)
    null_contract = "CTT_M2_FIXED_U_PROSPECTIVE_K_NULL_MAPS_V3"
    addendum = load_json(args.evaluation_addendum)
    unchanged = addendum.get("scientific_changes", {})
    if (
        null_maps.get("contract") != null_contract
        or null_maps.get("replicates") != NULL_REPLICATES
        or null_maps.get("source_count") != SOURCE_COUNT
        or null_maps.get("predictive_K_count") != len(PREDICTIVE_MEMBERS)
        or null_maps.get("routes") != list(EVALUATION_ROUTES)
        or addendum.get("contract")
        != "CTT_M2_FIXED_U_PROSPECTIVE_K_EVALUATION_REPAIR_V1"
        or addendum.get("status")
        != "FROZEN_AFTER_PHYSICAL_MATERIALIZATION_BEFORE_ANY_SOURCE_SCORE_OR_OUTCOME_READ"
        or addendum.get("original_generation_preregistration_sha256")
        != sha256_file(args.preregistration)
        or addendum.get("physical_bank", {}).get("bank_summary_sha256")
        != sha256_file(fixed_summary_path)
        or addendum.get("active_evaluation_null_map", {}).get("sha256")
        != sha256_file(args.null_maps)
        or addendum.get("active_evaluation_null_map", {}).get("contract")
        != null_contract
        or any(value is not False for value in unchanged.values())
    ):
        raise SystemExit("CTT_FIXED_U8_EVAL_REPAIR_CONTRACT_FAIL")

    schedules = {
        route: args.schedule_root / "H01" / "reserved" / f"trajectory_seed_{route}.csv"
        for route in ROUTES
    }
    schedule_hashes = [sha256_file(schedules[route]) for route in ROUTES]
    if fixed_summary["input_hashes"]["schedules"] != schedule_hashes:
        raise SystemExit("CTT_FIXED_U8_EVAL_SCHEDULE_HASH_FAIL")
    if fixed_summary["input_hashes"]["preregistration"] != sha256_file(args.preregistration):
        raise SystemExit("CTT_FIXED_U8_EVAL_PREREGISTRATION_LINK_FAIL")
    frozen = preregistration.get("frozen_inputs_sha256", {})
    frozen_checks = {
        "placement_manifest": sha256_file(args.placement_manifest),
        "existing_bank_summary": sha256_file(formal_summary_path),
        "existing_bank_file_sha_manifest": sha256_file(args.formal_bank / "FILE_SHA256.tsv"),
        "route_4004": schedule_hashes[3], "route_4005": schedule_hashes[4],
    }
    for name, digest in frozen_checks.items():
        if frozen.get(name) != digest:
            raise SystemExit(f"CTT_FIXED_U8_EVAL_PREREGISTERED_HASH_FAIL:{name}")
    stops = {route: load_stops(schedules[route]) for route in EVALUATION_ROUTES}
    for route in EVALUATION_ROUTES:
        if null_maps.get("stop_count_by_route", {}).get(str(route)) != len(stops[route]):
            raise SystemExit(f"CTT_FIXED_U8_EVAL_NULL_STOP_COUNT_FAIL:{route}")
    carriers, paths = read_factorial_manifest(
        args.formal_bank, args.fixed_bank, fixed_summary["factorial_manifest_sha256"]
    )

    args.output.mkdir(parents=True)
    evaluation_freeze = {
        "contract": "CTT_M2_FIXED_U_EIGHT_K_EVALUATION_FREEZE_V1",
        "status": "FROZEN_BEFORE_PHYSICAL_SEQUENCE_READ",
        "preregistration_sha256": sha256_file(args.preregistration),
        "null_maps_sha256": sha256_file(args.null_maps),
        "evaluation_addendum_sha256": sha256_file(args.evaluation_addendum),
        "evaluator_sha256": sha256_file(Path(__file__)),
        "fixed_bank_summary_sha256": sha256_file(fixed_summary_path),
        "factorial_manifest_sha256": sha256_file(args.fixed_bank / "FACTORIAL_SHA256.tsv"),
        "null_seeds": null_maps["seeds"],
        "transport_inference_units": len(HELD_MEMBERS),
    }
    atomic_text(
        args.output / "EVALUATION_FREEZE.json",
        json.dumps(evaluation_freeze, indent=2, sort_keys=True) + "\n",
    )

    detected: dict[int, np.ndarray] = {}
    for route in EVALUATION_ROUTES:
        tensor = np.empty(
            (len(K_BY_MEMBER), SOURCE_COUNT, len(stops[route])), dtype=np.bool_
        )
        for member in range(len(K_BY_MEMBER)):
            for source, carrier in enumerate(carriers):
                tensor[member, source] = detection(
                    paths[(carrier, member)], ROUTE_TO_STREAM[route], stops[route]
                )
        detected[route] = tensor
        print(f"CTT_FIXED_U8_LOAD_ROUTE={route} PASS", flush=True)

    strata = []
    case_rows = []
    max_online = 0.0
    max_k_swap = 0.0
    max_row = 0.0
    candidate_permutation = np.asarray(
        null_maps["candidate_permutation_invariance"], dtype=np.int64
    )
    identity = np.arange(SOURCE_COUNT)
    for route in EVALUATION_ROUTES:
        predictive = np.transpose(detected[route][list(PREDICTIVE_MEMBERS)], (1, 0, 2))
        for observation_member in HELD_MEMBERS:
            observed = detected[route][observation_member]
            coherent, redraw = score_matrices(predictive, observed)
            coherent_rank = midrank_desc_matrix(coherent)
            redraw_rank = midrank_desc_matrix(redraw)
            max_online = max(max_online, float(np.max(np.abs(coherent - online_coherent(predictive, observed)))))
            k_coherent, k_redraw = score_matrices(predictive[:, ::-1, :], observed)
            max_k_swap = max(
                max_k_swap, float(np.max(np.abs(coherent - k_coherent))),
                float(np.max(np.abs(redraw - k_redraw))),
            )
            row_coherent, row_redraw = score_matrices(predictive[candidate_permutation], observed)
            restored_coherent = np.empty_like(row_coherent)
            restored_redraw = np.empty_like(row_redraw)
            restored_coherent[:, candidate_permutation] = row_coherent
            restored_redraw[:, candidate_permutation] = row_redraw
            max_row = max(
                max_row, float(np.max(np.abs(coherent - restored_coherent))),
                float(np.max(np.abs(redraw - restored_redraw))),
            )
            stratum = {
                "route": route, "observation_member": observation_member,
                "predictive": predictive, "observed": observed,
                "coherent_rank_matrix": coherent_rank, "redraw_rank_matrix": redraw_rank,
                "coherent_scores": coherent, "redraw_scores": redraw,
            }
            strata.append(stratum)
            for truth, carrier in enumerate(carriers):
                coherent_value = float(coherent_rank[truth, truth])
                redraw_value = float(redraw_rank[truth, truth])
                case_rows.append({
                    "carrier_index": truth, "carrier_id": carrier, "route": route,
                    "observation_member": observation_member,
                    "coherent_rank": coherent_value, "redraw_rank": redraw_value,
                    "coherent_normalized_rank": (coherent_value - 1.0) / (SOURCE_COUNT - 1.0),
                    "redraw_normalized_rank": (redraw_value - 1.0) / (SOURCE_COUNT - 1.0),
                    "normalized_rank_improvement": (redraw_value - coherent_value) / (SOURCE_COUNT - 1.0),
                    "true_coherent_score": float(coherent[truth, truth]),
                    "true_redraw_score": float(redraw[truth, truth]),
                })

    observed_delta = [
        (
            item["route"], item["observation_member"],
            (
                item["redraw_rank_matrix"][identity, identity]
                - item["coherent_rank_matrix"][identity, identity]
            ) / (SOURCE_COUNT - 1.0),
        )
        for item in strata
    ]
    transport_improvement, primary = transport_unit_statistic(observed_delta)
    sign = positive_sign_test(transport_improvement)
    coherent_case_rank = np.asarray([row["coherent_rank"] for row in case_rows])
    redraw_case_rank = np.asarray([row["redraw_rank"] for row in case_rows])
    route_report = {}
    route_nonreverse = True
    for route in EVALUATION_ROUTES:
        route_arrays = [delta for r, _, delta in observed_delta if r == route]
        route_mean = float(np.mean(np.concatenate(route_arrays)))
        nonreverse = route_mean >= 0.0
        route_report[str(route)] = {
            "mean_normalized_rank_improvement": route_mean,
            "nonreverse": nonreverse,
        }
        route_nonreverse &= nonreverse

    null_rows = []
    source_null = np.empty(NULL_REPLICATES)
    stop_null = np.empty(NULL_REPLICATES)
    k_null = np.empty(NULL_REPLICATES)
    for replicate in range(NULL_REPLICATES):
        observation_source_permutation = np.asarray(
            null_maps["observation_source_association"][replicate], dtype=np.int64
        )
        source_delta = []
        stop_delta = []
        for item in strata:
            source_delta.append((
                item["route"], item["observation_member"],
                (
                    item["redraw_rank_matrix"][observation_source_permutation, identity]
                    - item["coherent_rank_matrix"][observation_source_permutation, identity]
                ) / (SOURCE_COUNT - 1.0),
            ))
            stop_permutation = np.asarray(
                null_maps["candidate_stop_association"][replicate][str(item["route"])],
                dtype=np.int64,
            )
            stop_predictive = item["predictive"][:, :, stop_permutation]
            stop_coherent, stop_redraw = score_matrices(
                stop_predictive, item["observed"]
            )
            stop_coherent_rank = midrank_desc_matrix(stop_coherent)
            stop_redraw_rank = midrank_desc_matrix(stop_redraw)
            stop_delta.append((
                item["route"], item["observation_member"],
                (
                    stop_redraw_rank[identity, identity]
                    - stop_coherent_rank[identity, identity]
                ) / (SOURCE_COUNT - 1.0),
            ))
        _, source_null[replicate] = transport_unit_statistic(source_delta)
        _, stop_null[replicate] = transport_unit_statistic(stop_delta)

        k_delta = []
        for route in EVALUATION_ROUTES:
            base = next(item for item in strata if item["route"] == route)
            permuted = np.empty_like(base["predictive"])
            for stop in range(permuted.shape[2]):
                permutation = np.asarray(
                    null_maps["predictive_K_identity"][replicate][str(route)][stop],
                    dtype=np.int64,
                )
                permuted[:, :, stop] = base["predictive"][:, permutation, stop]
            for observation_member in HELD_MEMBERS:
                item = next(
                    entry for entry in strata
                    if entry["route"] == route and entry["observation_member"] == observation_member
                )
                null_coherent, _ = score_matrices(permuted, item["observed"])
                null_rank = midrank_desc_matrix(null_coherent)
                k_delta.append((
                    route, observation_member,
                    (
                        item["redraw_rank_matrix"][identity, identity]
                        - null_rank[identity, identity]
                    ) / (SOURCE_COUNT - 1.0),
                ))
        _, k_null[replicate] = transport_unit_statistic(k_delta)
        null_rows.append({
            "replicate": replicate,
            "observation_source_association_mean_transport_improvement": float(
                source_null[replicate]
            ),
            "candidate_stop_association_mean_transport_improvement": float(
                stop_null[replicate]
            ),
            "k_identity_mean_transport_improvement": float(k_null[replicate]),
        })
        if (replicate + 1) % 32 == 0:
            print(f"CTT_FIXED_U8_NULL_PROGRESS={replicate + 1}/{NULL_REPLICATES}", flush=True)

    source_p = empirical_upper_p(primary, source_null)
    stop_p = empirical_upper_p(primary, stop_null)
    k_p = empirical_upper_p(primary, k_null)
    invariance = {
        "online_batch_max_abs": max_online,
        "global_k_swap_max_abs": max_k_swap,
        "candidate_row_max_abs": max_row,
        "tolerance": TOLERANCE,
        "pass": bool(max(max_online, max_k_swap, max_row) <= TOLERANCE),
    }
    coherent_summary = summarize_rank(coherent_case_rank)
    redraw_summary = summarize_rank(redraw_case_rank)
    passed = bool(
        primary > 0.0
        and np.all(transport_improvement > 0.0)
        and sign["one_sided_exact_p"] <= ALPHA
        and source_p <= ALPHA and stop_p <= ALPHA and k_p <= ALPHA
        and coherent_summary["mean_normalized_rank"] < ABSOLUTE_RANK_MAX_EXCLUSIVE
        and route_nonreverse and invariance["pass"]
    )
    verdict = PASS if passed else NO_GO

    with (args.output / "CASES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(case_rows[0]))
        writer.writeheader()
        writer.writerows(case_rows)
    with (args.output / "NULLS.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(null_rows[0]))
        writer.writeheader()
        writer.writerows(null_rows)
    transport_rows = [
        {
            "observation_member": int(member),
            "observation_seed": int(K_BY_MEMBER[member]),
            "mean_normalized_rank_improvement": float(transport_improvement[index]),
        }
        for index, member in enumerate(HELD_MEMBERS)
    ]
    with (args.output / "TRANSPORT_UNITS.csv").open(
        "w", newline="", encoding="utf-8"
    ) as target:
        writer = csv.DictWriter(target, fieldnames=list(transport_rows[0]))
        writer.writeheader()
        writer.writerows(transport_rows)

    report = {
        "contract": CONTRACT, "verdict": verdict, "premise_only": True,
        "closed_loop_authorized": False,
        "factorial_design": {
            "fixed_u_member": 0, "predictive_members": list(PREDICTIVE_MEMBERS),
            "held_members": list(HELD_MEMBERS), "transport_seeds": list(K_BY_MEMBER),
            "routes": list(EVALUATION_ROUTES), "cases": len(case_rows),
            "independent_transport_units": len(HELD_MEMBERS),
        },
        "coherent": coherent_summary, "per_stop_redraw": redraw_summary,
        "primary": {
            "statistic": "mean prospective-transport-unit normalized-rank improvement redraw-minus-coherent",
            "value": primary,
            "transport_unit_improvements": [
                float(value) for value in transport_improvement
            ],
            "all_seven_strictly_positive": bool(np.all(transport_improvement > 0.0)),
            "transport_exact_sign_test": sign,
            "route_nonreverse": route_nonreverse,
            "routes": route_report,
        },
        "nulls": {
            "replicates": NULL_REPLICATES,
            "null_map_sha256": sha256_file(args.null_maps),
            "observation_source_association": {"empirical_upper_p": source_p},
            "candidate_stop_association": {"empirical_upper_p": stop_p},
            "predictive_K_identity": {"empirical_upper_p": k_p},
        },
        "invariance": invariance,
        "input_hashes": {
            "evaluator": sha256_file(Path(__file__)),
            "fixed_bank_summary": sha256_file(fixed_summary_path),
            "factorial_manifest": sha256_file(args.fixed_bank / "FACTORIAL_SHA256.tsv"),
            "formal_bank_summary": sha256_file(formal_summary_path),
            "placement_manifest": sha256_file(args.placement_manifest),
            "schedules": {str(route): sha256_file(schedules[route]) for route in ROUTES},
            "preregistration": sha256_file(args.preregistration),
            "null_maps": sha256_file(args.null_maps),
            "evaluation_addendum": sha256_file(args.evaluation_addendum),
            "evaluation_freeze": sha256_file(args.output / "EVALUATION_FREEZE.json"),
        },
        "downstream_rule": (
            "PASS supports only the fixed-U transport-coherence premise; it does not override "
            "the existing G0 NO-GO and cannot authorize closed loop."
        ),
    }
    atomic_text(args.output / "SUMMARY.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    atomic_text(args.output / "VERDICT.txt", verdict + "\n")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
