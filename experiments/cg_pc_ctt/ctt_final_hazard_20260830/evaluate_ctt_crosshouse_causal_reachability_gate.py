#!/usr/bin/env python3
"""Frozen cross-House causal-reachability premise Gate.

This evaluator reads the audited PF-DEI V3 native bank exactly once.  It does
not invoke GADEN, train a model, consume a PMFS posterior, or inspect a
historical localization outcome.  Candidate native concentration is passed
through the run-persistent sensor before one ever/never event is extracted per
completed physical stop.  Predictive nuisance is marginalized within each
stop; no turbulent member identity is coupled across stops.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np


CONTRACT = "CTT_CAUSAL_REACHABILITY_CROSSHOUSE_GATE_V1"
PASS = "CTT_CAUSAL_REACHABILITY_CROSSHOUSE_PREMISE_PASS"
NO_GO = "CTT_CAUSAL_REACHABILITY_CROSSHOUSE_PREMISE_NO_GO"
HOUSES = ("H01", "H02", "H03")
HOUSE_DIR = {"H01": "House01", "H02": "House02", "H03": "House03"}
SOURCE_COUNTS = {"H01": 210, "H02": 201, "H03": 206}
PREDICTIVE_MEMBERS = tuple(range(8))
OBSERVATION_MEMBERS = tuple(range(4))
SEEDS = tuple(range(10))
STOP_SAMPLES = 80
THRESHOLD_PPM = 0.1
DT_S = 0.2
TAU_S = 1.2
DELAY_SAMPLES = 2
JEFFREYS = 0.5
NULL_REPLICATES = 256
MAGIC = b"PFV3STR1"
U32 = struct.Struct("<I")
TOL = 1.0e-12


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_multistream_verified(path: Path, expected_sha256: str) -> list[np.ndarray]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError(f"CTT_REACHABILITY_SHARD_HASH_FAIL:{path}")
    if len(raw) < 12 or raw[:8] != MAGIC:
        raise ValueError(f"CTT_REACHABILITY_BAD_MAGIC:{path}")
    (count,) = U32.unpack_from(raw, 8)
    offset = 12
    header_end = offset + 4 * count
    if count == 0 or header_end > len(raw):
        raise ValueError(f"CTT_REACHABILITY_BAD_HEADER:{path}")
    lengths = struct.unpack_from(f"<{count}I", raw, offset)
    expected = header_end + 4 * sum(lengths)
    if any(length == 0 for length in lengths) or expected != len(raw):
        raise ValueError(f"CTT_REACHABILITY_BAD_LENGTHS:{path}")
    flat = np.frombuffer(raw, dtype="<f4", offset=header_end)
    if not np.isfinite(flat).all() or np.any(flat < 0.0):
        raise ValueError(f"CTT_REACHABILITY_BAD_PPM:{path}")
    result = []
    start = 0
    for length in lengths:
        result.append(flat[start : start + length].copy())
        start += length
    return result


def historical_schedule(root: Path, house: str, seed: int) -> Path:
    directory = HOUSE_DIR[house]
    return (
        root / directory / f"seed{seed}" / "off" / "runtime"
        / f"{directory}_seed{seed}_off_off" / "sim_pose_trace.csv"
    )


def load_complete_stops(path: Path) -> tuple[int, list[np.ndarray]]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows or "is_moving" not in rows[0]:
        raise ValueError(f"CTT_REACHABILITY_SCHEDULE_SCHEMA_FAIL:{path}")
    moving = np.asarray([int(row["is_moving"]) for row in rows], dtype=np.int8)
    stops: list[np.ndarray] = []
    start = None
    for index, value in enumerate(moving):
        if value == 0 and start is None:
            start = index
        if value != 0 and start is not None:
            if index - start >= STOP_SAMPLES:
                stops.append(np.arange(start, start + STOP_SAMPLES, dtype=np.int64))
            start = None
    if start is not None and len(moving) - start >= STOP_SAMPLES:
        stops.append(np.arange(start, start + STOP_SAMPLES, dtype=np.int64))
    if len(stops) < 3:
        raise ValueError(f"CTT_REACHABILITY_TOO_FEW_STOPS:{path}:{len(stops)}")
    return len(rows), stops


def sensor_events_and_first_passage(
    physical: np.ndarray, stops: list[np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the authoritative delayed first-order sensor without stop resets.

    physical has shape [source, member, time].  The recurrence is vectorized
    over source/member but retains the authoritative operation order in time.
    """
    values = np.asarray(physical, dtype=np.float32)
    if values.ndim != 3 or not np.isfinite(values).all() or np.any(values < 0.0):
        raise ValueError("CTT_REACHABILITY_PHYSICAL_TENSOR_FAIL")
    time_to_stop = np.full(values.shape[2], -1, dtype=np.int32)
    time_to_phase = np.full(values.shape[2], -1, dtype=np.int16)
    for stop, indices in enumerate(stops):
        if len(indices) != STOP_SAMPLES or indices[-1] >= values.shape[2]:
            raise ValueError("CTT_REACHABILITY_STOP_INDEX_FAIL")
        time_to_stop[indices] = stop
        time_to_phase[indices] = np.arange(STOP_SAMPLES, dtype=np.int16)
    events = np.zeros(values.shape[:2] + (len(stops),), dtype=np.bool_)
    first = np.full(values.shape[:2] + (len(stops),), STOP_SAMPLES, dtype=np.int16)
    alpha = math.exp(-DT_S / TAU_S)
    state = np.zeros(values.shape[:2], dtype=np.float64)
    for time in range(values.shape[2]):
        target = values[:, :, time - DELAY_SAMPLES] if time >= DELAY_SAMPLES else 0.0
        state = alpha * state + (1.0 - alpha) * target
        stop = int(time_to_stop[time])
        if stop < 0:
            continue
        hit = state > THRESHOLD_PPM
        newly = hit & ~events[:, :, stop]
        if np.any(newly):
            first[:, :, stop][newly] = time_to_phase[time]
        events[:, :, stop] |= hit
    return events, first


def score_reachability(train_events: np.ndarray, observed_events: np.ndarray) -> np.ndarray:
    """Return [observation_source, candidate_source], larger is better."""
    train = np.asarray(train_events, dtype=np.bool_)
    observed = np.asarray(observed_events, dtype=np.bool_)
    if train.ndim != 3 or train.shape[1] != 8 or observed.shape != (train.shape[0], train.shape[2]):
        raise ValueError(f"CTT_REACHABILITY_SCORE_SHAPE_FAIL:{train.shape}:{observed.shape}")
    probability = (train.sum(axis=1, dtype=np.float64) + JEFFREYS) / (train.shape[1] + 2.0 * JEFFREYS)
    log_hit = np.log(probability)
    log_miss = np.log1p(-probability)
    return observed.astype(np.float64) @ log_hit.T + (~observed).astype(np.float64) @ log_miss.T


def score_first_passage(train_first: np.ndarray, observed_first: np.ndarray) -> np.ndarray:
    """Report-only exact-phase ablation using a Jeffreys categorical model."""
    train = np.asarray(train_first, dtype=np.int16)
    observed = np.asarray(observed_first, dtype=np.int16)
    source_count, member_count, stop_count = train.shape
    if member_count != 8 or observed.shape != (source_count, stop_count):
        raise ValueError("CTT_REACHABILITY_FIRST_PASSAGE_SHAPE_FAIL")
    probability = np.empty((source_count, stop_count, STOP_SAMPLES + 1), dtype=np.float64)
    denominator = member_count + JEFFREYS * (STOP_SAMPLES + 1)
    for label in range(STOP_SAMPLES + 1):
        probability[:, :, label] = (np.sum(train == label, axis=1) + JEFFREYS) / denominator
    result = np.zeros((source_count, source_count), dtype=np.float64)
    for stop in range(stop_count):
        result += np.log(probability[:, stop, observed[:, stop]].T)
    return result


def midrank_desc(scores: np.ndarray) -> np.ndarray:
    values = np.asarray(scores, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != values.shape[1] or not np.isfinite(values).all():
        raise ValueError("CTT_REACHABILITY_RANK_INPUT_FAIL")
    result = np.empty_like(values)
    for row_index, row in enumerate(values):
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


def domain_permutation(size: int, label: str) -> np.ndarray:
    seed = int.from_bytes(hashlib.sha256(("CTT-REACHABILITY-V1|" + label).encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    identity = np.arange(size)
    for _ in range(32):
        value = rng.permutation(size)
        if not np.array_equal(value, identity):
            return value
    raise AssertionError(f"CTT_REACHABILITY_IDENTITY_PERMUTATION:{label}")


def empirical_lower_p(observed: float, null_values: np.ndarray) -> float:
    null_values = np.asarray(null_values, dtype=np.float64)
    return float((1 + np.count_nonzero(null_values <= observed)) / (len(null_values) + 1))


def summarize_rank(rank: np.ndarray, source_count: int) -> dict:
    values = np.asarray(rank, dtype=np.float64)
    normalized = (values - 1.0) / (source_count - 1.0)
    return {
        "cases": int(values.size),
        "mean_normalized_rank": float(normalized.mean()),
        "median_rank": float(np.median(values)),
        "top1": float(np.mean(values <= 1.0)),
        "top5": float(np.mean(values <= 5.0)),
        "top10": float(np.mean(values <= 10.0)),
    }


def validate_inputs(bank_root: Path, historical_root: Path, prereg: dict) -> tuple[dict, list[dict], dict]:
    summary_path = bank_root / "bank_summary.json"
    audit_path = bank_root / "bank_audit_summary.json"
    manifest_path = bank_root / "bank_shard_manifest.csv"
    frozen = prereg["frozen_inputs"]
    if (
        sha256_file(summary_path) != frozen["bank_summary_sha256"]
        or sha256_file(audit_path) != frozen["bank_audit_sha256"]
        or sha256_file(manifest_path) != frozen["bank_shard_manifest_sha256"]
    ):
        raise SystemExit("CTT_REACHABILITY_FROZEN_INPUT_HASH_FAIL")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if (
        summary.get("contract") != frozen["bank_contract"]
        or audit.get("verdict") != "PF_DEI_V3_NATIVE_BANK_AUDIT_PASS"
        or audit.get("shard_count") != frozen["bank_shards"]
        or audit.get("total_stream_samples") != frozen["bank_samples"]
        or audit.get("total_size_bytes") != frozen["bank_bytes"]
    ):
        raise SystemExit("CTT_REACHABILITY_BANK_AUDIT_FAIL")
    with manifest_path.open(newline="", encoding="utf-8") as source:
        manifest = list(csv.DictReader(source))
    if len(manifest) != frozen["bank_shards"]:
        raise SystemExit("CTT_REACHABILITY_MANIFEST_COUNT_FAIL")
    schedules = {}
    for house in HOUSES:
        train_hash = summary["trajectory_schedule_sha256"][house + "_train"]
        reserved_hash = summary["trajectory_schedule_sha256"][house + "_reserved"]
        train_length = summary["trajectory_lengths"][house + "_train"]
        reserved_length = summary["trajectory_lengths"][house + "_reserved"]
        schedules[house] = []
        for seed in SEEDS:
            path = historical_schedule(historical_root, house, seed)
            digest = sha256_file(path)
            length, stops = load_complete_stops(path)
            if not (
                digest == train_hash[seed] == reserved_hash[seed]
                and length == train_length[seed] == reserved_length[seed]
            ):
                raise SystemExit(f"CTT_REACHABILITY_SCHEDULE_MAPPING_FAIL:{house}:{seed}")
            schedules[house].append({"path": path, "sha256": digest, "length": length, "stops": stops})
    return summary, manifest, schedules


def materialize_house(
    bank_root: Path, house: str, manifest: list[dict], schedules: list[dict]
) -> tuple[list[np.ndarray], list[np.ndarray], list[str], int]:
    rows = [row for row in manifest if row["house"] == house]
    carriers = sorted({row["carrier_id"] for row in rows})
    expected_sources = SOURCE_COUNTS[house]
    if len(carriers) != expected_sources:
        raise SystemExit(f"CTT_REACHABILITY_CARRIER_COUNT_FAIL:{house}:{len(carriers)}")
    source_index = {carrier: index for index, carrier in enumerate(carriers)}
    arrays = {
        "train": [np.empty((expected_sources, 8, item["length"]), dtype=np.float32) for item in schedules],
        "reserved": [np.empty((expected_sources, 4, item["length"]), dtype=np.float32) for item in schedules],
    }
    seen = set()
    for count, row in enumerate(rows, start=1):
        split = row["split"]
        member = int(row["member_id"])
        if split not in arrays or member >= arrays[split][0].shape[1]:
            raise SystemExit(f"CTT_REACHABILITY_MEMBER_FAIL:{house}:{split}:{member}")
        key = (split, member, row["carrier_id"])
        if key in seen:
            raise SystemExit(f"CTT_REACHABILITY_DUPLICATE_SHARD:{key}")
        seen.add(key)
        path = bank_root / row["relative_path"]
        if not path.is_file() or path.stat().st_size != int(row["size_bytes"]):
            raise SystemExit(f"CTT_REACHABILITY_SHARD_FILE_FAIL:{path}")
        streams = read_multistream_verified(path, row["sha256"])
        if len(streams) < 10:
            raise SystemExit(f"CTT_REACHABILITY_STREAM_COUNT_FAIL:{path}:{len(streams)}")
        source = source_index[row["carrier_id"]]
        for seed in SEEDS:
            if len(streams[seed]) != schedules[seed]["length"]:
                raise SystemExit(f"CTT_REACHABILITY_STREAM_LENGTH_FAIL:{path}:{seed}")
            arrays[split][seed][source, member] = streams[seed]
        if count % 500 == 0 or count == len(rows):
            print(f"CTT_REACHABILITY_LOAD_{house}={count}/{len(rows)}", flush=True)
    expected_keys = expected_sources * (8 + 4)
    if len(seen) != expected_keys:
        raise SystemExit(f"CTT_REACHABILITY_SHARD_COVERAGE_FAIL:{house}:{len(seen)}:{expected_keys}")
    train = []
    reserved = []
    for seed in SEEDS:
        train.append(sensor_events_and_first_passage(arrays["train"][seed], schedules[seed]["stops"]))
        reserved.append(sensor_events_and_first_passage(arrays["reserved"][seed], schedules[seed]["stops"]))
    return train, reserved, carriers, len(seen)


def evaluate_house(house: str, train: list, reserved: list, carriers: list[str]) -> dict:
    source_count = len(carriers)
    identity = np.arange(source_count)
    rank_matrices = []
    first_rank_matrices = []
    case_rows = []
    unit_case_ranks = {member: [] for member in OBSERVATION_MEMBERS}
    unit_first_ranks = {member: [] for member in OBSERVATION_MEMBERS}
    invariance_max = {"candidate": 0.0, "source": 0.0, "member": 0.0}
    candidate_perm = domain_permutation(source_count, f"INV-CANDIDATE|{house}")
    source_perm = domain_permutation(source_count, f"INV-SOURCE|{house}")
    for seed in SEEDS:
        train_events, train_first = train[seed]
        reserved_events, reserved_first = reserved[seed]
        for member in OBSERVATION_MEMBERS:
            observed = reserved_events[:, member]
            observed_first = reserved_first[:, member]
            score = score_reachability(train_events, observed)
            rank = midrank_desc(score)
            phase_score = score_first_passage(train_first, observed_first)
            phase_rank = midrank_desc(phase_score)
            rank_matrices.append({"seed": seed, "member": member, "rank": rank})
            first_rank_matrices.append(phase_rank)
            true_rank = rank[identity, identity]
            true_phase_rank = phase_rank[identity, identity]
            unit_case_ranks[member].append(true_rank)
            unit_first_ranks[member].append(true_phase_rank)
            for truth, carrier in enumerate(carriers):
                case_rows.append({
                    "house": house, "seed": seed, "observation_member": member,
                    "truth_carrier_index": truth, "truth_carrier_id": carrier,
                    "reachability_rank": float(true_rank[truth]),
                    "reachability_normalized_rank": float((true_rank[truth] - 1.0) / (source_count - 1.0)),
                    "first_passage_rank_report_only": float(true_phase_rank[truth]),
                    "first_passage_normalized_rank_report_only": float((true_phase_rank[truth] - 1.0) / (source_count - 1.0)),
                    "true_reachability_score": float(score[truth, truth]),
                    "true_first_passage_score_report_only": float(phase_score[truth, truth]),
                })
            if seed == 0 and member == 0:
                candidate_score = score_reachability(train_events[candidate_perm], observed)
                restored = np.empty_like(candidate_score); restored[:, candidate_perm] = candidate_score
                source_score = score_reachability(train_events, observed[source_perm])
                member_score = score_reachability(train_events[:, ::-1], observed)
                invariance_max["candidate"] = float(np.max(np.abs(score - restored)))
                invariance_max["source"] = float(np.max(np.abs(source_score - score[source_perm])))
                invariance_max["member"] = float(np.max(np.abs(member_score - score)))
    unit_rows = []
    for member in OBSERVATION_MEMBERS:
        ranks = np.concatenate(unit_case_ranks[member])
        phase = np.concatenate(unit_first_ranks[member])
        unit_rows.append({
            "house": house, "observation_member": member,
            "cases": int(ranks.size),
            "mean_normalized_rank": float(((ranks - 1.0) / (source_count - 1.0)).mean()),
            "first_passage_mean_normalized_rank_report_only": float(((phase - 1.0) / (source_count - 1.0)).mean()),
        })
    observed_house_mean = float(np.mean([row["mean_normalized_rank"] for row in unit_rows]))
    null = np.empty(NULL_REPLICATES, dtype=np.float64)
    for replicate in range(NULL_REPLICATES):
        mapping = domain_permutation(source_count, f"NULL-SOURCE|{house}|{replicate}")
        unit_null = []
        for member in OBSERVATION_MEMBERS:
            values = []
            for item in rank_matrices:
                if item["member"] == member:
                    values.append(item["rank"][identity, mapping])
            ranks = np.concatenate(values)
            unit_null.append(float(((ranks - 1.0) / (source_count - 1.0)).mean()))
        null[replicate] = float(np.mean(unit_null))
    all_rank = np.asarray([row["reachability_rank"] for row in case_rows])
    all_phase = np.asarray([row["first_passage_rank_report_only"] for row in case_rows])
    return {
        "house": house,
        "source_count": source_count,
        "cases": case_rows,
        "units": unit_rows,
        "reachability": summarize_rank(all_rank, source_count),
        "first_passage_report_only": summarize_rank(all_phase, source_count),
        "observed_house_mean": observed_house_mean,
        "source_label_null": null,
        "source_label_empirical_p": empirical_lower_p(observed_house_mean, null),
        "invariance_max_abs": invariance_max,
    }


def selftest() -> None:
    sources, members, stops, time = 4, 8, 3, 260
    physical = np.zeros((sources, members, time), dtype=np.float32)
    stop_indices = [np.arange(10, 90), np.arange(95, 175), np.arange(180, 260)]
    for source in range(sources):
        for member in range(members):
            for stop, indices in enumerate(stop_indices):
                if (source + stop + member % 2) % 3 == 0:
                    physical[source, member, indices[10:]] = 1.0 + source
    events, first = sensor_events_and_first_passage(physical, stop_indices)
    assert events.shape == (sources, members, stops) and first.shape == events.shape
    observed = events[:, 0]
    score = score_reachability(events, observed)
    assert np.isfinite(score).all()
    assert np.array_equal(score, score_reachability(events[:, ::-1], observed))
    permutation = np.asarray([2, 0, 3, 1])
    permuted = score_reachability(events[permutation], observed)
    restored = np.empty_like(permuted); restored[:, permutation] = permuted
    assert np.array_equal(score, restored)
    row_score = score_reachability(events, observed[permutation])
    assert np.array_equal(row_score, score[permutation])
    phase = score_first_passage(first, first[:, 0])
    assert phase.shape == score.shape and np.isfinite(phase).all()
    ranks = midrank_desc(score)
    assert np.all((ranks >= 1.0) & (ranks <= sources))
    print("CTT_CAUSAL_REACHABILITY_EVALUATOR_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--bank-root", type=Path)
    parser.add_argument("--historical-root", type=Path)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if any(value is None for value in (args.bank_root, args.historical_root, args.preregistration, args.output)):
        raise SystemExit("CTT_REACHABILITY_REQUIRED_ARGUMENT_MISSING")
    if args.output.exists():
        raise SystemExit(f"CTT_REACHABILITY_REFUSE_OVERWRITE:{args.output}")
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    if prereg.get("contract") != CONTRACT or prereg.get("status") != "PREREGISTERED_BEFORE_REACHABILITY_SCORE_READ":
        raise SystemExit("CTT_REACHABILITY_PREREGISTRATION_FAIL")
    summary, manifest, schedules = validate_inputs(args.bank_root, args.historical_root, prereg)
    args.output.mkdir(parents=True)
    freeze = {
        "contract": "CTT_CAUSAL_REACHABILITY_EVALUATION_FREEZE_V1",
        "status": "FROZEN_BEFORE_PHYSICAL_SHARD_READ",
        "preregistration_sha256": sha256_file(args.preregistration),
        "evaluator_sha256": sha256_file(Path(__file__)),
        "bank_summary_sha256": sha256_file(args.bank_root / "bank_summary.json"),
        "bank_audit_sha256": sha256_file(args.bank_root / "bank_audit_summary.json"),
        "bank_shard_manifest_sha256": sha256_file(args.bank_root / "bank_shard_manifest.csv"),
        "schedule_sha256": {house: [item["sha256"] for item in schedules[house]] for house in HOUSES},
        "complete_stop_counts": {house: [len(item["stops"]) for item in schedules[house]] for house in HOUSES},
    }
    freeze_path = args.output / "EVALUATION_FREEZE.json"
    freeze_path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    reports = []
    all_cases = []
    all_units = []
    verified_shards = 0
    for house in HOUSES:
        train, reserved, carriers, shard_count = materialize_house(
            args.bank_root, house, manifest, schedules[house]
        )
        verified_shards += shard_count
        report = evaluate_house(house, train, reserved, carriers)
        all_cases.extend(report.pop("cases"))
        all_units.extend(report.pop("units"))
        reports.append(report)
        print(f"CTT_REACHABILITY_SCORE_{house}=PASS", flush=True)
    if verified_shards != prereg["frozen_inputs"]["bank_shards"]:
        raise SystemExit(f"CTT_REACHABILITY_VERIFIED_SHARDS_FAIL:{verified_shards}")

    pooled_observed = float(np.mean([row["mean_normalized_rank"] for row in all_units]))
    pooled_null = np.empty(NULL_REPLICATES, dtype=np.float64)
    null_rows = []
    for replicate in range(NULL_REPLICATES):
        values = [float(report["source_label_null"][replicate]) for report in reports]
        pooled_null[replicate] = float(np.mean(values))
        null_rows.append({
            "replicate": replicate,
            **{report["house"] + "_mean_normalized_rank": values[index] for index, report in enumerate(reports)},
            "pooled_mean_normalized_rank": pooled_null[replicate],
        })
    pooled_p = empirical_lower_p(pooled_observed, pooled_null)
    unit_values = np.asarray([row["mean_normalized_rank"] for row in all_units], dtype=np.float64)
    invariance_max = max(
        value
        for report in reports
        for value in report["invariance_max_abs"].values()
    )
    rules = {
        "pooled_mean_normalized_rank_lt_0p30": pooled_observed < 0.30,
        "each_house_mean_normalized_rank_lt_0p35": all(report["observed_house_mean"] < 0.35 for report in reports),
        "all_12_units_mean_normalized_rank_lt_0p50": bool(np.all(unit_values < 0.50)),
        "at_least_9_of_12_units_mean_normalized_rank_lt_0p35": int(np.count_nonzero(unit_values < 0.35)) >= 9,
        "pooled_source_label_empirical_p_le_0p01": pooled_p <= 0.01,
        "each_house_source_label_empirical_p_le_0p01": all(report["source_label_empirical_p"] <= 0.01 for report in reports),
        "all_invariances_le_1e_12": invariance_max <= TOL,
        "schedule_hash_mapping_pass": True,
        "bank_audit_pass": True,
    }
    verdict = PASS if all(rules.values()) else NO_GO
    for report in reports:
        report["source_label_null"] = {
            "replicates": NULL_REPLICATES,
            "empirical_lower_tail_p": report["source_label_empirical_p"],
        }
        report.pop("source_label_empirical_p")
    summary_out = {
        "contract": CONTRACT,
        "verdict": verdict,
        "premise_only": True,
        "closed_loop_authorized": False,
        "modules": prereg["scientific_modules"],
        "verified_shards": verified_shards,
        "independent_units": 12,
        "pooled_mean_normalized_rank": pooled_observed,
        "pooled_source_label_empirical_lower_tail_p": pooled_p,
        "units_below_0p35": int(np.count_nonzero(unit_values < 0.35)),
        "units_below_0p50": int(np.count_nonzero(unit_values < 0.50)),
        "houses": reports,
        "hard_pass_rules": rules,
        "max_invariance_abs": invariance_max,
        "first_passage_is_report_only": True,
        "input_hashes": {
            "preregistration": sha256_file(args.preregistration),
            "evaluator": sha256_file(Path(__file__)),
            "evaluation_freeze": sha256_file(freeze_path),
            "bank_summary": sha256_file(args.bank_root / "bank_summary.json"),
            "bank_audit": sha256_file(args.bank_root / "bank_audit_summary.json"),
            "bank_shard_manifest": sha256_file(args.bank_root / "bank_shard_manifest.csv"),
        },
        "downstream": prereg["downstream"],
    }
    with (args.output / "CASES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(all_cases[0])); writer.writeheader(); writer.writerows(all_cases)
    with (args.output / "INDEPENDENT_UNITS.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(all_units[0])); writer.writeheader(); writer.writerows(all_units)
    with (args.output / "SOURCE_LABEL_NULLS.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(null_rows[0])); writer.writeheader(); writer.writerows(null_rows)
    (args.output / "SUMMARY.json").write_text(json.dumps(summary_out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "VERDICT.txt").write_text(verdict + "\n", encoding="utf-8")
    print(json.dumps(summary_out, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
