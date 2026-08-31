#!/usr/bin/env python3
"""Two-stage CBPE replay for the frozen causal-temporal PMFS method.

Stage 1 is truth blind.  Three newly completed physical stops are one ordered
source-update block.  Stops are exchangeable *inside* a block through their
hit count K in {0,1,2,3}; block order is retained.  A single predictive
transport member is held coherent across all visible blocks:

    L_s(k_1:J) = M^-1 sum_m prod_j Q[K_s,m,j, k_j].

Q is one source-, House-, seed-, and outcome-independent 4x4 matrix estimated
from every ordered strict leave-one-member-out pair in the frozen predictive
bank, with Jeffreys 1/2 smoothing.  Stage 2 opens native PMFS and truth only
after the complete Stage-1 artifact and its semantic digest are externally
frozen and verified.  It uses the already-tested V2 I-projection to preserve
the native within-carrier conditional.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

import evaluate_ctt_crosshouse_causal_reachability_gate as causal_gate
import evaluate_ctt_crosshouse_measured_pmfs_shadow as v1
import evaluate_ctt_hierarchical_projection_v2 as v2


CONTRACT = "CTT_CBPE_TWO_MODULE_V3"
PASS = "CTT_CBPE_TWO_MODULE_V3_PASS_TO_RUNTIME_PILOT"
NO_GO = "CTT_CBPE_TWO_MODULE_V3_NO_GO"
INVALID = "CTT_CBPE_TWO_MODULE_V3_INVALID"
STAGE1_CONTRACT = CONTRACT + "_STAGE1"
STAGE1_STATUS = "ALL_150_CBPE_POSTERIORS_FROZEN_BEFORE_NATIVE_OR_TRUTH_READ"
PREREG_STATUS = "PREREGISTERED_BEFORE_CBPE_STAGE1_POSTERIORS_OR_V3_OUTCOME_READ"
PREMISE_CONTRACT = "CTT_CBPE_TWO_MODULE_V3_PRETRUTH_PREMISE_ADDENDUM"
PREMISE_STATUS = "FROZEN_BEFORE_CBPE_PREMISE_OR_HISTORICAL_V3_OUTCOME_READ"
PREMISE_PASS = "CTT_CBPE_M2_PRETRUTH_PREMISE_PASS"
PREMISE_NO_GO = "CTT_CBPE_M2_PRETRUTH_PREMISE_NO_GO"
PREMISE_INVALID = "CTT_CBPE_M2_PRETRUTH_PREMISE_INVALID"
INFERENCE_CONTRACT = "CTT_CBPE_TWO_MODULE_V3_INFERENCE_AND_INCREMENTAL_EVIDENCE_ADDENDUM"
INFERENCE_STATUS = "FROZEN_BEFORE_CBPE_PREMISE_OR_HISTORICAL_V3_OUTCOME_READ"

BLOCK_SIZE = 3
BLOCK_STATES = 4
JEFFREYS = 0.5
TOL = 1.0e-12
PRIMARY_MODES = v2.PRIMARY_MODES
RANDOM_MODES = v2.RANDOM_MODES
ALL_MODES = v2.ALL_MODES
NULL_MODES = v2.NULL_MODES
CHANNELS = (
    "identity_reconstruction",
    "conditional_only",
    "full",
    "global_count",
    "block_order_permute",
    "incoherent_per_block",
)
PROJECTION_INVARIANT_KEYS = v2.PROJECTION_INVARIANT_KEYS
STAGE1_ARRAY_KEYS = (
    "cbpe_score",
    "global_count_score",
    "block_order_permute_score",
    "incoherent_per_block_score",
    "q0_carrier",
    "cbpe_carrier",
    "global_count_carrier",
    "block_order_permute_carrier",
    "incoherent_per_block_carrier",
)


def sha256_file(path: Path) -> str:
    return v1.sha256_file(path)


def canonical_array_sha256(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        value = np.asarray(array, dtype="<f8", order="C")
        digest.update(np.asarray(value.shape, dtype="<u8").tobytes())
        digest.update(value.tobytes())
    return digest.hexdigest()


def block_counts(
    events: np.ndarray, authorized_blocks: list[np.ndarray] | None = None
) -> np.ndarray:
    value = np.asarray(events, dtype=np.bool_)
    if value.ndim != 3 or value.shape[1] != len(v1.PREDICTIVE_MEMBERS):
        raise ValueError(f"CTT_CBPE_EVENT_SHAPE_FAIL:{value.shape}")
    if authorized_blocks is None:
        if value.shape[2] != v1.SOURCE_UPDATES * BLOCK_SIZE:
            raise ValueError(f"CTT_CBPE_EVENT_AUTHORIZED_SUPPORT_MISSING:{value.shape}")
        selected = value.reshape(
            value.shape[0], value.shape[1], v1.SOURCE_UPDATES, BLOCK_SIZE
        )
    else:
        if len(authorized_blocks) != v1.SOURCE_UPDATES:
            raise ValueError("CTT_CBPE_AUTHORIZED_BLOCK_COUNT_FAIL")
        selected = np.stack(
            [value[:, :, np.asarray(block, dtype=np.int64)] for block in authorized_blocks],
            axis=2,
        )
        if selected.shape[2:] != (v1.SOURCE_UPDATES, BLOCK_SIZE):
            raise ValueError(f"CTT_CBPE_AUTHORIZED_BLOCK_SHAPE_FAIL:{selected.shape}")
    result = selected.sum(axis=3, dtype=np.int64)
    if np.any((result < 0) | (result >= BLOCK_STATES)):
        raise ValueError("CTT_CBPE_BLOCK_COUNT_RANGE_FAIL")
    return result


def observed_block_counts(
    events: np.ndarray, authorized_blocks: list[np.ndarray]
) -> np.ndarray:
    value = np.asarray(events, dtype=np.bool_)
    if value.ndim != 1 or len(authorized_blocks) != v1.SOURCE_UPDATES:
        raise ValueError(f"CTT_CBPE_OBSERVED_EVENT_SHAPE_FAIL:{value.shape}")
    selected = np.stack([value[np.asarray(block, dtype=np.int64)] for block in authorized_blocks])
    if selected.shape != (v1.SOURCE_UPDATES, BLOCK_SIZE):
        raise ValueError(f"CTT_CBPE_OBSERVED_AUTHORIZED_SUPPORT_FAIL:{selected.shape}")
    return selected.sum(axis=1, dtype=np.int64)


def fit_global_lomo_q(
    tensors: dict[str, list[np.ndarray]],
    *,
    excluded_member: int | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Fit one global Q from all ordered member pairs m != m'."""
    counts = np.zeros((BLOCK_STATES, BLOCK_STATES), dtype=np.int64)
    source_blocks = 0
    ordered_member_pairs = 0
    domain_rows: dict[str, int] = {}
    for house in v1.HOUSES:
        if house not in tensors or len(tensors[house]) != len(v1.SEEDS):
            raise ValueError(f"CTT_CBPE_Q_DOMAIN_HOUSE_FAIL:{house}")
        house_rows = 0
        for seed, tensor in enumerate(tensors[house]):
            value = np.asarray(tensor, dtype=np.int64)
            if value.ndim != 3 or value.shape[1:] != (
                len(v1.PREDICTIVE_MEMBERS), v1.SOURCE_UPDATES
            ):
                raise ValueError(f"CTT_CBPE_Q_TENSOR_SHAPE_FAIL:{house}:{seed}:{value.shape}")
            source_blocks += value.shape[0] * value.shape[2]
            house_rows += value.shape[0] * value.shape[2]
            for left in range(value.shape[1]):
                if excluded_member is not None and left == excluded_member:
                    continue
                a = value[:, left, :].reshape(-1)
                for right in range(value.shape[1]):
                    if left == right or (excluded_member is not None and right == excluded_member):
                        continue
                    b = value[:, right, :].reshape(-1)
                    np.add.at(counts, (a, b), 1)
                    ordered_member_pairs += len(a)
        domain_rows[house] = house_rows
    active_members = len(v1.PREDICTIVE_MEMBERS) - (excluded_member is not None)
    expected_pairs = source_blocks * active_members * (active_members - 1)
    if ordered_member_pairs != expected_pairs or int(np.sum(counts)) != expected_pairs:
        raise ValueError(
            f"CTT_CBPE_Q_STRICT_LOMO_COUNT_FAIL:{ordered_member_pairs}:{expected_pairs}"
        )
    q = (counts.astype(np.float64) + JEFFREYS) / (
        counts.sum(axis=1, keepdims=True, dtype=np.int64).astype(np.float64)
        + BLOCK_STATES * JEFFREYS
    )
    if not np.isfinite(q).all() or np.any(q <= 0.0) or np.max(np.abs(q.sum(axis=1) - 1.0)) > TOL:
        raise ValueError("CTT_CBPE_Q_NORMALIZATION_FAIL")
    domain = {
        "houses": list(v1.HOUSES),
        "trajectory_stream_indices": [int(seed) for seed in v1.SEEDS],
        "carriers_by_house": {
            house: int(tensors[house][0].shape[0]) for house in v1.HOUSES
        },
        "source_blocks_by_house": domain_rows,
        "blocks_per_trajectory": v1.SOURCE_UPDATES,
        "stops_per_block": BLOCK_SIZE,
        "members": list(v1.PREDICTIVE_MEMBERS),
        "excluded_member": excluded_member,
        "ordered_member_pair_rule": "all (m,m_prime) with m != m_prime",
        "ordered_member_pair_rows": int(ordered_member_pairs),
        "source_house_seed_conditioned_tables": False,
        "measured_tape_or_truth_consumed": False,
        "jeffreys_alpha_each_of_four_states": JEFFREYS,
    }
    return q, counts, domain


def _logmeanexp(value: np.ndarray, axis: int) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    maximum = np.max(array, axis=axis, keepdims=True)
    return np.squeeze(maximum, axis=axis) + np.log(np.mean(np.exp(array - maximum), axis=axis))


def coherent_cbpe_score(
    candidate_counts: np.ndarray,
    observed_counts: np.ndarray,
    q: np.ndarray,
    visible_blocks: int,
    *,
    observed_block_order: np.ndarray | None = None,
    predictive_members: np.ndarray | None = None,
) -> np.ndarray:
    candidate = np.asarray(candidate_counts, dtype=np.int64)
    observed = np.asarray(observed_counts, dtype=np.int64)
    matrix = np.asarray(q, dtype=np.float64)
    if candidate.ndim != 3 or candidate.shape[1:] != (
        len(v1.PREDICTIVE_MEMBERS), v1.SOURCE_UPDATES
    ):
        raise ValueError("CTT_CBPE_SCORE_CANDIDATE_SHAPE_FAIL")
    if observed.shape != (v1.SOURCE_UPDATES,) or not 1 <= visible_blocks <= v1.SOURCE_UPDATES:
        raise ValueError("CTT_CBPE_SCORE_OBSERVED_SHAPE_FAIL")
    if observed_block_order is None:
        order = np.arange(visible_blocks, dtype=np.int64)
    else:
        order = np.asarray(observed_block_order, dtype=np.int64)
        if order.shape != (visible_blocks,) or sorted(order.tolist()) != list(range(visible_blocks)):
            raise ValueError("CTT_CBPE_BLOCK_PERMUTATION_FAIL")
    if predictive_members is None:
        members = np.arange(candidate.shape[1], dtype=np.int64)
    else:
        members = np.asarray(predictive_members, dtype=np.int64)
        if members.ndim != 1 or len(set(members.tolist())) != len(members):
            raise ValueError("CTT_CBPE_PREDICTIVE_MEMBER_SET_FAIL")
    log_q = np.log(matrix)
    term = log_q[
        candidate[:, members, :visible_blocks],
        observed[order][None, None, :],
    ]
    return _logmeanexp(np.sum(term, axis=2), axis=1)


def incoherent_per_block_score(
    candidate_counts: np.ndarray, observed_counts: np.ndarray, q: np.ndarray,
    visible_blocks: int, *, predictive_members: np.ndarray | None = None,
) -> np.ndarray:
    candidate = np.asarray(candidate_counts, dtype=np.int64)
    observed = np.asarray(observed_counts, dtype=np.int64)
    log_q = np.log(np.asarray(q, dtype=np.float64))
    members = (
        np.arange(candidate.shape[1], dtype=np.int64)
        if predictive_members is None else np.asarray(predictive_members, dtype=np.int64)
    )
    term = log_q[candidate[:, members, :visible_blocks], observed[None, None, :visible_blocks]]
    return np.sum(_logmeanexp(term, axis=1), axis=1)


def deterministic_block_permutation(house: str, seed: int, update: int) -> np.ndarray:
    if update == 1:
        return np.asarray([0], dtype=np.int64)
    return v1.domain_permutation(update, f"CBPE-BLOCK-ORDER|{house}|{seed}|{update}")


def authorized_stop_support(
    historical_root: Path,
    house: str,
    seed: int,
    schedule: dict[str, Any],
) -> dict[str, Any]:
    """Derive the 15 authorised original stop indices without gas outcomes."""
    pose_rows = v1.read_csv(schedule["path"])
    if len(pose_rows) != schedule["length"] or "t_sim_s" not in pose_rows[0]:
        raise ValueError(f"CTT_CBPE_STOP_SUPPORT_POSE_FAIL:{house}:{seed}")
    pose_time = np.asarray([float(row["t_sim_s"]) for row in pose_rows], dtype=np.float64)
    timing_path = (
        v1.runtime_root(historical_root, house, seed)
        / "context_bank" / "source_update_timing.csv"
    )
    timing = v1.read_csv(timing_path)
    if len(timing) != v1.SOURCE_UPDATES:
        raise ValueError(f"CTT_CBPE_STOP_SUPPORT_UPDATE_COUNT_FAIL:{house}:{seed}")
    update_times = np.asarray([float(row["sim_time"]) for row in timing], dtype=np.float64)
    if not np.all(np.diff(update_times) > 0.0):
        raise ValueError(f"CTT_CBPE_STOP_SUPPORT_UPDATE_ORDER_FAIL:{house}:{seed}")
    prefixes: list[np.ndarray] = []
    blocks: list[np.ndarray] = []
    previous: set[int] = set()
    for update, update_time in enumerate(update_times, start=1):
        visible = np.asarray([
            index
            for index, stop in enumerate(schedule["stops"])
            if pose_time[int(stop[-1])] <= update_time + TOL
        ], dtype=np.int64)
        if len(visible) != BLOCK_SIZE * update:
            raise ValueError(
                f"CTT_CBPE_STOP_SUPPORT_PREFIX_LENGTH_FAIL:{house}:{seed}:{update}:{len(visible)}"
            )
        visible_set = set(int(value) for value in visible)
        if not previous.issubset(visible_set):
            raise ValueError(f"CTT_CBPE_STOP_SUPPORT_NONMONOTONE_FAIL:{house}:{seed}:{update}")
        new = np.asarray(sorted(visible_set - previous), dtype=np.int64)
        if len(new) != BLOCK_SIZE or len(set(new.tolist())) != BLOCK_SIZE:
            raise ValueError(
                f"CTT_CBPE_STOP_SUPPORT_NEW_BLOCK_FAIL:{house}:{seed}:{update}:{len(new)}"
            )
        prefixes.append(visible)
        blocks.append(new)
        previous = visible_set
    union = sorted(previous)
    if len(union) != v1.SOURCE_UPDATES * BLOCK_SIZE:
        raise ValueError(f"CTT_CBPE_STOP_SUPPORT_UNION_FAIL:{house}:{seed}:{len(union)}")
    excluded = sorted(set(range(len(schedule["stops"]))) - set(union))
    if len(excluded) not in (2, 3):
        raise ValueError(f"CTT_CBPE_STOP_SUPPORT_EXCLUDED_COUNT_FAIL:{house}:{seed}:{len(excluded)}")
    return {
        "prefixes": prefixes,
        "blocks": blocks,
        "authorized_union": np.asarray(union, dtype=np.int64),
        "excluded": np.asarray(excluded, dtype=np.int64),
        "timing": timing,
        "timing_path": timing_path,
        "timing_sha256": sha256_file(timing_path),
    }


def validate_predictive_inputs(
    bank_root: Path,
    historical_root: Path,
    source_support: Path,
    causal_premise_verdict: Path,
    causal_premise_summary: Path,
    prereg: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, str]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Validate bank and route schedules without opening a measured tape."""
    frozen = prereg["frozen_inputs"]
    if str(historical_root.resolve()) != frozen["historical_root"]:
        raise SystemExit("CTT_CBPE_HISTORICAL_ROOT_FREEZE_FAIL")
    paths = {
        "bank_summary": bank_root / "bank_summary.json",
        "bank_audit": bank_root / "bank_audit_summary.json",
        "bank_shard_manifest": bank_root / "bank_shard_manifest.csv",
        "region_support_manifest": source_support,
    }
    for key, path in paths.items():
        if sha256_file(path) != frozen[key + "_sha256"]:
            raise SystemExit(f"CTT_CBPE_FROZEN_INPUT_HASH_FAIL:{key}")
    if (
        sha256_file(causal_premise_verdict) != frozen["premise_verdict_sha256"]
        or sha256_file(causal_premise_summary) != frozen["premise_summary_sha256"]
        or causal_premise_verdict.read_text(encoding="utf-8").strip()
        != frozen["premise_verdict_required"]
    ):
        raise SystemExit("CTT_CBPE_CAUSAL_PREMISE_DEPENDENCY_FAIL")
    summary = json.loads(paths["bank_summary"].read_text(encoding="utf-8"))
    audit = json.loads(paths["bank_audit"].read_text(encoding="utf-8"))
    if (
        summary.get("contract") != frozen["bank_contract"]
        or audit.get("verdict") != "PF_DEI_V3_NATIVE_BANK_AUDIT_PASS"
        or int(audit.get("shard_count", -1)) != int(frozen["bank_shards"])
        or int(audit.get("total_stream_samples", -1)) != int(frozen["bank_samples"])
        or int(audit.get("total_size_bytes", -1)) != int(frozen["bank_bytes"])
    ):
        raise SystemExit("CTT_CBPE_BANK_AUDIT_FAIL")
    with paths["bank_shard_manifest"].open(newline="", encoding="utf-8") as source:
        manifest = list(csv.DictReader(source))
    schedules: dict[str, list[dict[str, Any]]] = {}
    for house in v1.HOUSES:
        schedules[house] = []
        train_hashes = summary["trajectory_schedule_sha256"][house + "_train"]
        train_lengths = summary["trajectory_lengths"][house + "_train"]
        for seed in v1.SEEDS:
            path = v1.historical_schedule(historical_root, house, seed)
            digest = sha256_file(path)
            length, stops = v1.load_complete_stops(path)
            if digest != train_hashes[seed] or length != train_lengths[seed]:
                raise SystemExit(f"CTT_CBPE_SCHEDULE_MAPPING_FAIL:{house}:{seed}")
            schedules[house].append({
                "path": path, "sha256": digest, "length": length, "stops": stops,
            })
            schedules[house][-1]["authorized"] = authorized_stop_support(
                historical_root, house, seed, schedules[house][-1]
            )
    freeze = {
        "contract": CONTRACT + "_PREDICTIVE_INPUT_FREEZE",
        "status": "FROZEN_WITHOUT_MEASURED_TAPE_NATIVE_PMFS_OR_TRUTH",
        "hashes": {key: sha256_file(path) for key, path in paths.items()},
        "schedule_hashes": {
            house: [item["sha256"] for item in schedules[house]] for house in v1.HOUSES
        },
        "source_update_timing_hashes": {
            house: [item["authorized"]["timing_sha256"] for item in schedules[house]]
            for house in v1.HOUSES
        },
        "authorized_stop_support": {
            house: [{
                "prefix_lengths": [len(value) for value in item["authorized"]["prefixes"]],
                "blocks": [block.tolist() for block in item["authorized"]["blocks"]],
                "authorized_union": item["authorized"]["authorized_union"].tolist(),
                "excluded": item["authorized"]["excluded"].tolist(),
            } for item in schedules[house]]
            for house in v1.HOUSES
        },
        "causal_premise_verdict_sha256": sha256_file(causal_premise_verdict),
        "causal_premise_summary_sha256": sha256_file(causal_premise_summary),
        "measured_tape_native_pmfs_truth_read": False,
    }
    return summary, manifest, schedules, freeze


def materialize_predictive_counts(
    bank_root: Path,
    manifest: list[dict[str, str]],
    schedules: dict[str, list[dict[str, Any]]],
    support_all: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[np.ndarray]], dict[str, list[np.ndarray]], int]:
    result: dict[str, list[np.ndarray]] = {}
    events_out: dict[str, list[np.ndarray]] = {}
    shards = 0
    for house in v1.HOUSES:
        rows = v1.member_rows_for_house(manifest, house)
        carriers = sorted({row["carrier_id"] for row in rows})
        if carriers != support_all[house]["carriers"]:
            raise ValueError(f"CTT_CBPE_PREDICTIVE_SUPPORT_ORDER_FAIL:{house}")
        source_index = {carrier: index for index, carrier in enumerate(carriers)}
        physical = [
            np.empty(
                (len(carriers), len(v1.PREDICTIVE_MEMBERS), schedule["length"]),
                dtype=np.float32,
            )
            for schedule in schedules[house]
        ]
        seen: set[tuple[str, int]] = set()
        for row in rows:
            member = int(row["member_id"])
            key = (row["carrier_id"], member)
            if member not in v1.PREDICTIVE_MEMBERS or key in seen:
                raise ValueError(f"CTT_CBPE_PREDICTIVE_SHARD_ID_FAIL:{house}:{key}")
            seen.add(key)
            path = bank_root / row["relative_path"]
            if not path.is_file() or path.stat().st_size != int(row["size_bytes"]):
                raise ValueError(f"CTT_CBPE_PREDICTIVE_SHARD_FILE_FAIL:{path}")
            streams = v1.read_multistream_verified(path, row["sha256"])
            if len(streams) < len(v1.SEEDS):
                raise ValueError(f"CTT_CBPE_PREDICTIVE_STREAM_COUNT_FAIL:{path}")
            source = source_index[row["carrier_id"]]
            for seed in v1.SEEDS:
                if len(streams[seed]) != schedules[house][seed]["length"]:
                    raise ValueError(f"CTT_CBPE_PREDICTIVE_STREAM_LENGTH_FAIL:{house}:{seed}")
                physical[seed][source, member] = streams[seed]
        if len(seen) != len(rows):
            raise ValueError(f"CTT_CBPE_PREDICTIVE_COVERAGE_FAIL:{house}")
        events_out[house] = [
            v1.sensor_events_and_first_passage(
                physical[seed], schedules[house][seed]["stops"]
            )[0]
            for seed in v1.SEEDS
        ]
        result[house] = [
            block_counts(
                events_out[house][seed], schedules[house][seed]["authorized"]["blocks"]
            )
            for seed in v1.SEEDS
        ]
        shards += len(rows)
    return result, events_out, shards


def exact_sign_upper_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    return float(sum(math.comb(n, k) for k in range(wins, n + 1)) / (2 ** n))


def normalized_truth_ranks(score: np.ndarray) -> np.ndarray:
    matrix = np.asarray(score, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("CTT_CBPE_PREMISE_SCORE_MATRIX_FAIL")
    ranks = np.asarray([
        v1.rank_desc(matrix[truth], truth) for truth in range(matrix.shape[0])
    ])
    return (ranks - 1.0) / (matrix.shape[0] - 1.0)


def all_candidate_normalized_ranks(score: np.ndarray) -> np.ndarray:
    matrix = np.asarray(score, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("CTT_CBPE_PREMISE_ALL_RANK_MATRIX_FAIL")
    result = np.empty_like(matrix)
    for row_index, row in enumerate(matrix):
        above = np.sum(row[:, None] > row[None, :], axis=0)
        equal = np.sum(row[:, None] == row[None, :], axis=0)
        result[row_index] = (above + 0.5 * (equal - 1.0)) / (len(row) - 1.0)
    return result


def premise_score_matrix(
    candidate: np.ndarray,
    heldout_member: int,
    q_minus: np.ndarray,
    *,
    observed_order: np.ndarray | None = None,
    coherent: bool = True,
) -> np.ndarray:
    value = np.asarray(candidate, dtype=np.int64)
    members = np.asarray(
        [member for member in v1.PREDICTIVE_MEMBERS if member != heldout_member],
        dtype=np.int64,
    )
    observations = value[:, heldout_member, :]
    order = (
        np.arange(v1.SOURCE_UPDATES, dtype=np.int64)
        if observed_order is None else np.asarray(observed_order, dtype=np.int64)
    )
    if order.shape != (v1.SOURCE_UPDATES,) or sorted(order.tolist()) != list(
        range(v1.SOURCE_UPDATES)
    ):
        raise ValueError("CTT_CBPE_PREMISE_BLOCK_ORDER_FAIL")
    # [pseudo-observation source, candidate source, predictive member, block]
    term = np.log(q_minus)[
        value[None, :, members, :], observations[:, None, None, order]
    ]
    if coherent:
        return _logmeanexp(np.sum(term, axis=3), axis=2)
    return np.sum(_logmeanexp(term, axis=2), axis=2)


def premise_invariance_audit(tensors: dict[str, list[np.ndarray]]) -> dict[str, float]:
    base = tensors[v1.HOUSES[0]][0]
    # K is the orbit statistic of the within-block S3 action.
    synthetic_events = np.repeat(base[..., None], BLOCK_SIZE, axis=3) > 0
    within = np.max(np.abs(
        synthetic_events.sum(axis=3) - synthetic_events[..., ::-1].sum(axis=3)
    ))
    heldout = 0
    q, _, _ = fit_global_lomo_q(tensors, excluded_member=heldout)
    matrix = premise_score_matrix(base, heldout, q)
    candidate_perm = v1.domain_permutation(base.shape[0], "CBPE-PREMISE-CANDIDATE-INVARIANCE")
    permuted = premise_score_matrix(base[candidate_perm], heldout, q)
    restored = permuted[np.argsort(candidate_perm)][:, np.argsort(candidate_perm)]
    candidate_max = float(np.max(np.abs(matrix - restored)))

    member_perm = v1.domain_permutation(
        len(v1.PREDICTIVE_MEMBERS), "CBPE-PREMISE-MEMBER-INVARIANCE"
    )
    permuted_tensors = {
        house: [value[:, member_perm, :] for value in routes]
        for house, routes in tensors.items()
    }
    new_heldout = int(np.flatnonzero(member_perm == heldout)[0])
    q_permuted, _, _ = fit_global_lomo_q(
        permuted_tensors, excluded_member=new_heldout
    )
    matrix_permuted = premise_score_matrix(
        permuted_tensors[v1.HOUSES[0]][0], new_heldout, q_permuted
    )
    member_max = float(max(
        np.max(np.abs(q - q_permuted)), np.max(np.abs(matrix - matrix_permuted))
    ))
    return {
        "within_block_permutation_max_abs": float(within),
        "candidate_permutation_max_abs": candidate_max,
        "member_permutation_max_abs": member_max,
    }


def evaluate_pretruth_premise(
    tensors: dict[str, list[np.ndarray]],
    addendum: dict[str, Any],
    inference_addendum: dict[str, Any],
) -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]],
    list[dict[str, Any]], dict[str, Any]
]:
    cluster_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    score_matrices: list[dict[str, Any]] = []
    q_row_max = 0.0
    q_hashes: dict[str, str] = {}
    q_details: dict[str, Any] = {}
    for heldout in v1.PREDICTIVE_MEMBERS:
        q_minus, counts_minus, _ = fit_global_lomo_q(
            tensors, excluded_member=heldout
        )
        q_row_max = max(q_row_max, float(np.max(np.abs(q_minus.sum(axis=1) - 1.0))))
        q_hashes[str(heldout)] = canonical_array_sha256(q_minus, counts_minus)
        q_details[str(heldout)] = {
            "Q": q_minus.tolist(),
            "ordered_strict_LOMO_counts": counts_minus.tolist(),
            "canonical_sha256": q_hashes[str(heldout)],
        }
        for house in v1.HOUSES:
            for seed in v1.SEEDS:
                candidate = tensors[house][seed]
                order = v1.domain_permutation(
                    v1.SOURCE_UPDATES,
                    f"CBPE-PREMISE-BLOCK-ORDER|{house}|{seed}|{heldout}",
                )
                ordered = premise_score_matrix(candidate, heldout, q_minus)
                block_permuted = premise_score_matrix(
                    candidate, heldout, q_minus, observed_order=order
                )
                incoherent = premise_score_matrix(
                    candidate, heldout, q_minus, coherent=False
                )
                ordered_rank = normalized_truth_ranks(ordered)
                permuted_rank = normalized_truth_ranks(block_permuted)
                incoherent_rank = normalized_truth_ranks(incoherent)
                for source in range(candidate.shape[0]):
                    source_rows.append({
                        "house": house,
                        "route_index": int(seed),
                        "heldout_member": int(heldout),
                        "source_index": source,
                        "ordered_normalized_true_source_rank": float(ordered_rank[source]),
                        "block_permute_normalized_true_source_rank": float(
                            permuted_rank[source]
                        ),
                        "incoherent_normalized_true_source_rank": float(
                            incoherent_rank[source]
                        ),
                    })
                cluster_rows.append({
                    "house": house,
                    "route_index": int(seed),
                    "heldout_member": int(heldout),
                    "sources": int(candidate.shape[0]),
                    "ordered_mean_normalized_true_source_rank": float(np.mean(ordered_rank)),
                    "block_permute_mean_normalized_true_source_rank": float(
                        np.mean(permuted_rank)
                    ),
                    "incoherent_mean_normalized_true_source_rank": float(
                        np.mean(incoherent_rank)
                    ),
                    "ordered_minus_block_permute": float(
                        np.mean(ordered_rank) - np.mean(permuted_rank)
                    ),
                    "coherent_minus_incoherent": float(
                        np.mean(ordered_rank) - np.mean(incoherent_rank)
                    ),
                })
                score_matrices.append({
                    "house": house,
                    "ordered_rank_matrix": all_candidate_normalized_ranks(ordered),
                })
    if len(cluster_rows) != 240:
        raise ValueError(f"CTT_CBPE_PREMISE_CLUSTER_COUNT_FAIL:{len(cluster_rows)}")

    observed_mean = float(np.mean([
        row["ordered_mean_normalized_true_source_rank"] for row in cluster_rows
    ]))
    null_rows: list[dict[str, Any]] = []
    for replicate in range(v1.NULL_REPLICATES):
        maps = {
            house: v2.uniform_permutation(
                tensors[house][0].shape[0], f"CBPE-PREMISE-SOURCE-NULL|{house}|{replicate}"
            )
            for house in v1.HOUSES
        }
        cluster_null_means: list[float] = []
        for item in score_matrices:
            rank_matrix = item["ordered_rank_matrix"]
            label_map = maps[item["house"]]
            cluster_null_means.append(
                float(np.mean(rank_matrix[np.arange(len(label_map)), label_map]))
            )
        null_rows.append({
            "replicate": replicate,
            "mean_normalized_true_source_rank": float(np.mean(cluster_null_means)),
        })
    source_null_p = float(
        (1 + np.count_nonzero(
            np.asarray([row["mean_normalized_true_source_rank"] for row in null_rows])
            <= observed_mean
        )) / (v1.NULL_REPLICATES + 1)
    )

    # The eight held-out-member folds of one House-route reuse the same
    # physical design and are diagnostic replicates, not independent trials.
    # Average them first; all inferential sign tests use exactly 30 routes.
    route_rows: list[dict[str, Any]] = []
    for house in v1.HOUSES:
        for seed in v1.SEEDS:
            rows = [
                row for row in cluster_rows
                if row["house"] == house and row["route_index"] == seed
            ]
            if len(rows) != len(v1.PREDICTIVE_MEMBERS):
                raise ValueError(
                    f"CTT_CBPE_PREMISE_ROUTE_FOLD_COUNT_FAIL:{house}:{seed}:{len(rows)}"
                )
            route_rows.append({
                "house": house,
                "route_index": int(seed),
                "heldout_member_folds": len(rows),
                "ordered_mean_normalized_true_source_rank": float(np.mean([
                    row["ordered_mean_normalized_true_source_rank"] for row in rows
                ])),
                "block_permute_mean_normalized_true_source_rank": float(np.mean([
                    row["block_permute_mean_normalized_true_source_rank"] for row in rows
                ])),
                "incoherent_mean_normalized_true_source_rank": float(np.mean([
                    row["incoherent_mean_normalized_true_source_rank"] for row in rows
                ])),
                "ordered_minus_block_permute": float(np.mean([
                    row["ordered_minus_block_permute"] for row in rows
                ])),
                "coherent_minus_incoherent": float(np.mean([
                    row["coherent_minus_incoherent"] for row in rows
                ])),
            })
    inference_gate = inference_addendum["premise_inference"]["hard_go_rules"]
    if len(route_rows) != int(inference_gate["independent_route_clusters_exactly"]):
        raise ValueError(f"CTT_CBPE_PREMISE_ROUTE_COUNT_FAIL:{len(route_rows)}")
    order_delta = np.asarray([
        row["ordered_minus_block_permute"] for row in route_rows
    ])
    coherence_delta = np.asarray([
        row["coherent_minus_incoherent"] for row in route_rows
    ])
    order_sign_p = exact_sign_upper_p(
        int(np.count_nonzero(order_delta < -TOL)),
        int(np.count_nonzero(order_delta > TOL)),
    )
    coherence_sign_p = exact_sign_upper_p(
        int(np.count_nonzero(coherence_delta < -TOL)),
        int(np.count_nonzero(coherence_delta > TOL)),
    )
    by_house = {}
    for house in v1.HOUSES:
        rows = [row for row in route_rows if row["house"] == house]
        by_house[house] = {
            "route_clusters": len(rows),
            "ordered_mean_normalized_true_source_rank": float(np.mean([
                row["ordered_mean_normalized_true_source_rank"] for row in rows
            ])),
            "block_permute_mean_normalized_true_source_rank": float(np.mean([
                row["block_permute_mean_normalized_true_source_rank"] for row in rows
            ])),
            "incoherent_mean_normalized_true_source_rank": float(np.mean([
                row["incoherent_mean_normalized_true_source_rank"] for row in rows
            ])),
        }
    invariants = premise_invariance_audit(tensors)
    gate = addendum["hard_go_rules"]
    rules = {
        "clusters_exactly": len(cluster_rows) == int(gate["clusters_exactly"]),
        "independent_route_clusters_exactly": len(route_rows)
        == int(inference_gate["independent_route_clusters_exactly"]),
        "all_Q_rows_sum": q_row_max <= float(gate["all_Q_rows_sum_max_abs"]),
        "strict_member_LOO": True,
        "within_block_permutation": invariants["within_block_permutation_max_abs"]
        <= float(gate["within_block_permutation_max_abs"]),
        "candidate_permutation": invariants["candidate_permutation_max_abs"]
        <= float(gate["candidate_permutation_max_abs"]),
        "member_permutation": invariants["member_permutation_max_abs"]
        <= float(gate["member_permutation_max_abs"]),
        "ordered_rank": observed_mean
        <= float(gate["ordered_mean_normalized_true_source_rank_at_most"]),
        "each_house_ordered_rank": max(
            value["ordered_mean_normalized_true_source_rank"] for value in by_house.values()
        ) <= float(gate["each_house_ordered_mean_normalized_true_source_rank_at_most"]),
        "source_label_lower_tail_p": source_null_p
        <= float(gate["source_label_empirical_lower_tail_p_at_most"]),
        "ordered_better_than_block_permute": float(np.mean(order_delta)) < 0.0,
        "ordered_vs_block_permute_sign_p": order_sign_p
        <= float(inference_gate[
            "ordered_vs_block_permute_route_cluster_sign_p_at_most"
        ]),
        "coherent_better_than_incoherent": float(np.mean(coherence_delta)) < 0.0,
        "coherent_vs_incoherent_sign_p": coherence_sign_p
        <= float(inference_gate[
            "coherent_vs_incoherent_route_cluster_sign_p_at_most"
        ]),
        "each_house_direction_not_reversed": all(
            value["ordered_mean_normalized_true_source_rank"]
            <= value["block_permute_mean_normalized_true_source_rank"] + TOL
            and value["ordered_mean_normalized_true_source_rank"]
            <= value["incoherent_mean_normalized_true_source_rank"] + TOL
            for value in by_house.values()
        ),
    }
    verdict = PREMISE_PASS if all(rules.values()) else PREMISE_NO_GO
    summary = {
        "contract": PREMISE_CONTRACT,
        "verdict": verdict,
        "diagnostic_LOO_fold_rows": len(cluster_rows),
        "independent_route_clusters": len(route_rows),
        "independent_inference_unit": "House x route after averaging 8 heldout-member folds",
        "ordered_mean_normalized_true_source_rank": observed_mean,
        "source_label_empirical_lower_tail_p": source_null_p,
        "ordered_vs_block_permute": {
            "mean_rank_delta": float(np.mean(order_delta)),
            "wins": int(np.count_nonzero(order_delta < -TOL)),
            "losses": int(np.count_nonzero(order_delta > TOL)),
            "ties": int(np.count_nonzero(np.abs(order_delta) <= TOL)),
            "one_sided_exact_route_cluster_sign_p": order_sign_p,
        },
        "coherent_vs_incoherent": {
            "mean_rank_delta": float(np.mean(coherence_delta)),
            "wins": int(np.count_nonzero(coherence_delta < -TOL)),
            "losses": int(np.count_nonzero(coherence_delta > TOL)),
            "ties": int(np.count_nonzero(np.abs(coherence_delta) <= TOL)),
            "one_sided_exact_route_cluster_sign_p": coherence_sign_p,
        },
        "by_house": by_house,
        "invariants": {"Q_row_sum_max_abs": q_row_max, **invariants},
        "Q_minus_h_sha256": q_hashes,
        "Q_minus_h": q_details,
        "hard_pass_rules": rules,
    }
    return cluster_rows, route_rows, source_rows, null_rows, summary


def pretruth_digest(records: list[dict[str, Any]], q: np.ndarray, q_counts: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(canonical_array_sha256(q, q_counts).encode())
    for record in records:
        digest.update(f"{record['house']}|{record['seed']}|{record['update_id']}\n".encode())
        digest.update(
            json.dumps(
                record["historical_run_input_hashes"], sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )
        for key in STAGE1_ARRAY_KEYS:
            value = np.asarray(record[key], dtype="<f8", order="C")
            digest.update(key.encode() + b"\0" + value.tobytes())
    return digest.hexdigest()


def evaluate_stage1(
    bank_root: Path,
    historical_root: Path,
    manifest: list[dict[str, str]],
    schedules: dict[str, list[dict[str, Any]]],
    support_all: dict[str, dict[str, Any]],
    prefit_q: np.ndarray,
    prefit_q_counts: np.ndarray,
    prefit_q_domain: dict[str, Any],
) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray, dict[str, Any], int]:
    observed_all: dict[str, list[dict[str, Any]]] = {}
    train_events: dict[str, list[np.ndarray]] = {}
    train_counts: dict[str, list[np.ndarray]] = {}
    exact_matches: dict[str, list[int]] = {}
    verified_shards = 0
    for house in v1.HOUSES:
        observed_all[house] = [
            v1.load_observed_case(historical_root, house, seed, schedules[house][seed])
            for seed in v1.SEEDS
        ]
        materialized, carriers, shards, matches = v1.materialize_train_house(
            bank_root,
            house,
            manifest,
            schedules[house],
            [item["measured_ppm"] for item in observed_all[house]],
        )
        if carriers != support_all[house]["carriers"]:
            raise ValueError(f"CTT_CBPE_BANK_SUPPORT_ORDER_FAIL:{house}")
        train_events[house] = [np.asarray(item[0], dtype=np.bool_) for item in materialized]
        train_counts[house] = [
            block_counts(item, schedules[house][seed]["authorized"]["blocks"])
            for seed, item in enumerate(train_events[house])
        ]
        exact_matches[house] = matches
        verified_shards += shards
    check_q, check_counts, check_domain = fit_global_lomo_q(train_counts)
    if (
        np.max(np.abs(check_q - prefit_q)) > TOL
        or not np.array_equal(check_counts, prefit_q_counts)
        or check_domain != prefit_q_domain
    ):
        raise ValueError("CTT_CBPE_PREFIT_Q_RECOMPUTATION_FAIL")
    q, q_counts, q_domain = prefit_q, prefit_q_counts, prefit_q_domain

    records: list[dict[str, Any]] = []
    for house in v1.HOUSES:
        q0 = np.asarray(support_all[house]["q0"], dtype=np.float64)
        for seed in v1.SEEDS:
            observed = observed_all[house][seed]
            observed_counts = observed_block_counts(
                observed["observed_events"], schedules[house][seed]["authorized"]["blocks"]
            )
            candidate_counts = train_counts[house][seed]
            online_member_log = np.zeros(candidate_counts.shape[:2], dtype=np.float64)
            for update, (timing, visible) in enumerate(
                zip(observed["timing"], observed["visible"]), start=1
            ):
                expected_visible = schedules[house][seed]["authorized"]["prefixes"][update - 1]
                if not np.array_equal(np.asarray(visible, dtype=np.int64), expected_visible):
                    raise ValueError(f"CTT_CBPE_VISIBLE_PREFIX_FAIL:{house}:{seed}:{update}")
                score = coherent_cbpe_score(candidate_counts, observed_counts, q, update)
                new_block = update - 1
                online_member_log += np.log(q)[
                    candidate_counts[:, :, new_block], observed_counts[new_block]
                ]
                online_score = _logmeanexp(online_member_log, axis=1)
                score_online_batch_max = float(np.max(np.abs(online_score - score)))
                batch_carrier = v1.stable_softmax(np.log(q0) + score)
                online_carrier = v1.stable_softmax(np.log(q0) + online_score)
                online_batch_max = float(np.max(np.abs(online_carrier - batch_carrier)))
                if score_online_batch_max > TOL or online_batch_max > TOL:
                    raise ValueError(
                        "CTT_CBPE_ONLINE_BATCH_FAIL:"
                        f"{house}:{seed}:{update}:{score_online_batch_max}:{online_batch_max}"
                    )
                global_count = v1.count_only_score(
                    train_events[house][seed], observed["observed_events"], np.asarray(visible)
                )
                block_permutation = deterministic_block_permutation(house, seed, update)
                block_permuted = coherent_cbpe_score(
                    candidate_counts,
                    observed_counts,
                    q,
                    update,
                    observed_block_order=block_permutation,
                )
                incoherent = incoherent_per_block_score(
                    candidate_counts, observed_counts, q, update
                )
                records.append({
                    "house": house,
                    "seed": int(seed),
                    "update_id": update,
                    "update_time_s": float(timing["sim_time"]),
                    "visible_stops": np.asarray(visible, dtype=np.int64),
                    "visible_blocks": update,
                    "observed_hit_stops": int(np.sum(observed["observed_events"][visible])),
                    "observed_block_counts": observed_counts[:update].copy(),
                    "block_order_permutation": block_permutation.copy(),
                    "historical_measured_tape_exact_train_member_matches": int(
                        exact_matches[house][seed]
                    ),
                    "timing": timing,
                    "historical_run_input_hashes": dict(observed["hashes"]),
                    "online_batch_score_max_abs": score_online_batch_max,
                    "online_batch_joint_posterior_max_abs": online_batch_max,
                    "cbpe_score": score,
                    "global_count_score": global_count,
                    "block_order_permute_score": block_permuted,
                    "incoherent_per_block_score": incoherent,
                    "q0_carrier": q0,
                    "cbpe_carrier": batch_carrier,
                    "global_count_carrier": v1.stable_softmax(np.log(q0) + global_count),
                    "block_order_permute_carrier": v1.stable_softmax(
                        np.log(q0) + block_permuted
                    ),
                    "incoherent_per_block_carrier": v1.stable_softmax(
                        np.log(q0) + incoherent
                    ),
                })
    if len(records) != len(v1.HOUSES) * len(v1.SEEDS) * v1.SOURCE_UPDATES:
        raise ValueError(f"CTT_CBPE_STAGE1_RECORD_COUNT_FAIL:{len(records)}")
    return records, q, q_counts, q_domain, verified_shards


def write_stage1_artifact(
    output: Path,
    records: list[dict[str, Any]],
    q: np.ndarray,
    q_counts: np.ndarray,
    q_domain: dict[str, Any],
    preregistration: Path,
    input_freeze_path: Path,
    verified_shards: int,
) -> dict[str, Any]:
    input_freeze = json.loads(input_freeze_path.read_text(encoding="utf-8"))
    arrays: dict[str, np.ndarray] = {
        "GLOBAL_Q": np.asarray(q, dtype=np.float64),
        "GLOBAL_Q_LOMO_COUNTS": np.asarray(q_counts, dtype=np.int64),
    }
    metadata: list[dict[str, Any]] = []
    run_hashes: dict[str, dict[str, str]] = {}
    for house in v1.HOUSES:
        subset = [record for record in records if record["house"] == house]
        if len(subset) != len(v1.SEEDS) * v1.SOURCE_UPDATES:
            raise ValueError(f"CTT_CBPE_STAGE1_HOUSE_COUNT_FAIL:{house}:{len(subset)}")
        for key in STAGE1_ARRAY_KEYS:
            arrays[f"{house}_{key}"] = np.stack(
                [np.asarray(record[key]) for record in subset]
            )
        for local_index, record in enumerate(subset):
            run_key = f"{house}_seed{int(record['seed'])}"
            current_hashes = dict(record["historical_run_input_hashes"])
            if run_key in run_hashes and run_hashes[run_key] != current_hashes:
                raise ValueError(f"CTT_CBPE_STAGE1_RUN_HASH_DRIFT:{run_key}")
            run_hashes[run_key] = current_hashes
            metadata.append({
                "house": house,
                "local_index": local_index,
                "seed": int(record["seed"]),
                "update_id": int(record["update_id"]),
                "update_time_s": float(record["update_time_s"]),
                "visible_stops": [int(value) for value in record["visible_stops"]],
                "visible_blocks": int(record["visible_blocks"]),
                "observed_hit_stops": int(record["observed_hit_stops"]),
                "observed_block_counts": [
                    int(value) for value in record["observed_block_counts"]
                ],
                "block_order_permutation": [
                    int(value) for value in record["block_order_permutation"]
                ],
                "historical_measured_tape_exact_train_member_matches": int(
                    record["historical_measured_tape_exact_train_member_matches"]
                ),
                "timing": record["timing"],
                "historical_run_input_hashes": current_hashes,
                "online_batch_score_max_abs": float(
                    record["online_batch_score_max_abs"]
                ),
                "online_batch_joint_posterior_max_abs": float(
                    record["online_batch_joint_posterior_max_abs"]
                ),
            })
    npz_path = output / "CBPE_METHOD_POSTERIORS.npz"
    np.savez_compressed(npz_path, **arrays)
    semantic = pretruth_digest(records, q, q_counts)
    if len(run_hashes) != len(v1.HOUSES) * len(v1.SEEDS):
        raise ValueError(f"CTT_CBPE_STAGE1_RUN_HASH_COUNT_FAIL:{len(run_hashes)}")
    manifest = {
        "contract": STAGE1_CONTRACT,
        "status": STAGE1_STATUS,
        "parent_contract": CONTRACT,
        "records": len(records),
        "verified_training_shards": int(verified_shards),
        "pretruth_semantic_sha256": semantic,
        "historical_run_input_hashes": run_hashes,
        "artifact_sha256": sha256_file(npz_path),
        "preregistration_sha256": sha256_file(preregistration),
        "evaluator_sha256": sha256_file(Path(__file__)),
        "input_freeze_sha256": sha256_file(input_freeze_path),
        "implementation_binding": input_freeze["implementation_binding"],
        "array_keys": list(STAGE1_ARRAY_KEYS),
        "global_q_sha256": canonical_array_sha256(q),
        "global_q_lomo_counts_sha256": canonical_array_sha256(q_counts),
        "global_q": np.asarray(q).tolist(),
        "global_q_lomo_counts": np.asarray(q_counts).tolist(),
        "global_q_training_domain": q_domain,
        "metadata": metadata,
    }
    manifest_path = output / "CBPE_STAGE1_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "STAGE1_SHA256.txt").write_text(
        f"{sha256_file(npz_path)}  CBPE_METHOD_POSTERIORS.npz\n"
        f"{sha256_file(manifest_path)}  CBPE_STAGE1_MANIFEST.json\n",
        encoding="utf-8",
    )
    return manifest


def load_stage1_artifact(
    stage1: Path,
    preregistration: Path,
    expected_manifest_sha256: str,
    historical_root: Path,
    current_binding: dict[str, Any],
    expected_premise_hashes: dict[str, str],
) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray, dict[str, Any]]:
    npz_path = stage1 / "CBPE_METHOD_POSTERIORS.npz"
    manifest_path = stage1 / "CBPE_STAGE1_MANIFEST.json"
    freeze_path = stage1 / "INPUT_FREEZE.json"
    if sha256_file(manifest_path) != expected_manifest_sha256:
        raise SystemExit("CTT_CBPE_STAGE1_EXTERNAL_MANIFEST_HASH_FAIL")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if (
        manifest.get("contract") != STAGE1_CONTRACT
        or manifest.get("status") != STAGE1_STATUS
        or manifest.get("records") != 150
        or manifest.get("artifact_sha256") != sha256_file(npz_path)
        or manifest.get("preregistration_sha256") != sha256_file(preregistration)
        or manifest.get("evaluator_sha256") != sha256_file(Path(__file__))
        or manifest.get("input_freeze_sha256") != sha256_file(freeze_path)
        or manifest.get("implementation_binding") != current_binding
        or freeze.get("implementation_binding") != current_binding
        or freeze.get("preregistration_sha256") != current_binding["preregistration_sha256"]
        or freeze.get("premise_addendum_sha256") != current_binding["premise_addendum_sha256"]
        or freeze.get("stop_support_addendum_sha256") != current_binding["stop_support_addendum_sha256"]
        or freeze.get("inference_addendum_sha256") != current_binding["inference_addendum_sha256"]
        or freeze.get("evaluator_sha256") != current_binding["evaluator_sha256"]
        or tuple(manifest.get("array_keys", ())) != STAGE1_ARRAY_KEYS
        or not freeze.get("cbpe_pretruth_premise_hard_pass_rules")
        or not all(freeze["cbpe_pretruth_premise_hard_pass_rules"].values())
        or "cbpe_pretruth_premise_summary_sha256" not in freeze
        or "cbpe_pretruth_premise_verdict_sha256" not in freeze
        or freeze.get("cbpe_pretruth_premise_summary_sha256")
        != expected_premise_hashes["summary"]
        or freeze.get("cbpe_pretruth_premise_verdict_sha256")
        != expected_premise_hashes["verdict"]
        or freeze.get("cbpe_pretruth_premise_input_freeze_sha256")
        != expected_premise_hashes["input_freeze"]
    ):
        raise SystemExit("CTT_CBPE_STAGE1_CONTRACT_OR_HASH_FAIL")
    frozen_run_hashes = manifest.get("historical_run_input_hashes", {})
    if len(frozen_run_hashes) != len(v1.HOUSES) * len(v1.SEEDS):
        raise SystemExit("CTT_CBPE_STAGE1_RUN_HASH_COUNT_FAIL")
    for house in v1.HOUSES:
        for seed in v1.SEEDS:
            key = f"{house}_seed{seed}"
            runtime = v1.runtime_root(historical_root, house, seed)
            expected = {
                "sensor_trace": sha256_file(runtime / "sensor_trace.csv"),
                "sim_pose_trace": sha256_file(runtime / "sim_pose_trace.csv"),
                "source_update_timing": sha256_file(
                    runtime / "context_bank" / "source_update_timing.csv"
                ),
            }
            if frozen_run_hashes.get(key) != expected:
                raise SystemExit(f"CTT_CBPE_STAGE1_HISTORICAL_RUN_HASH_FAIL:{key}")
    records: list[dict[str, Any]] = []
    with np.load(npz_path, allow_pickle=False) as archive:
        expected_arrays = {"GLOBAL_Q", "GLOBAL_Q_LOMO_COUNTS"} | {
            f"{house}_{key}" for house in v1.HOUSES for key in STAGE1_ARRAY_KEYS
        }
        if set(archive.files) != expected_arrays:
            raise SystemExit("CTT_CBPE_STAGE1_ARRAY_SET_FAIL")
        q = np.asarray(archive["GLOBAL_Q"], dtype=np.float64)
        q_counts = np.asarray(archive["GLOBAL_Q_LOMO_COUNTS"], dtype=np.int64)
        for item in manifest["metadata"]:
            house = item["house"]
            index = int(item["local_index"])
            record: dict[str, Any] = {
                key: value for key, value in item.items() if key != "local_index"
            }
            record["visible_stops"] = np.asarray(record["visible_stops"], dtype=np.int64)
            record["observed_block_counts"] = np.asarray(
                record["observed_block_counts"], dtype=np.int64
            )
            record["block_order_permutation"] = np.asarray(
                record["block_order_permutation"], dtype=np.int64
            )
            for key in STAGE1_ARRAY_KEYS:
                record[key] = np.asarray(archive[f"{house}_{key}"][index], dtype=np.float64)
            records.append(record)
    if (
        q.shape != (BLOCK_STATES, BLOCK_STATES)
        or q_counts.shape != (BLOCK_STATES, BLOCK_STATES)
        or canonical_array_sha256(q) != manifest["global_q_sha256"]
        or canonical_array_sha256(q_counts) != manifest["global_q_lomo_counts_sha256"]
        or np.max(np.abs(q.sum(axis=1) - 1.0)) > TOL
        or pretruth_digest(records, q, q_counts) != manifest["pretruth_semantic_sha256"]
        or max(float(item["online_batch_score_max_abs"]) for item in manifest["metadata"])
        > TOL
        or max(
            float(item["online_batch_joint_posterior_max_abs"])
            for item in manifest["metadata"]
        ) > TOL
        or manifest["global_q_training_domain"].get(
            "source_house_seed_conditioned_tables"
        ) is not False
        or manifest["global_q_training_domain"].get("measured_tape_or_truth_consumed")
        is not False
    ):
        raise SystemExit("CTT_CBPE_STAGE1_SEMANTIC_HASH_FAIL")
    reconstructed_run_hashes: dict[str, dict[str, str]] = {}
    for record in records:
        key = f"{record['house']}_seed{int(record['seed'])}"
        value = dict(record["historical_run_input_hashes"])
        if key in reconstructed_run_hashes and reconstructed_run_hashes[key] != value:
            raise SystemExit(f"CTT_CBPE_STAGE1_METADATA_RUN_HASH_DRIFT:{key}")
        reconstructed_run_hashes[key] = value
    if reconstructed_run_hashes != frozen_run_hashes:
        raise SystemExit("CTT_CBPE_STAGE1_METADATA_RUN_HASH_SET_FAIL")
    return records, q, q_counts, manifest


def implementation_binding(
    preregistration: Path,
    premise_addendum: Path,
    stop_support_addendum: Path,
    inference_addendum: Path,
) -> dict[str, Any]:
    return {
        "preregistration_sha256": sha256_file(preregistration),
        "premise_addendum_sha256": sha256_file(premise_addendum),
        "stop_support_addendum_sha256": sha256_file(stop_support_addendum),
        "inference_addendum_sha256": sha256_file(inference_addendum),
        "evaluator_sha256": sha256_file(Path(__file__)),
        "imported_v1_source_sha256": sha256_file(Path(v1.__file__)),
        "imported_v2_source_sha256": sha256_file(Path(v2.__file__)),
        "imported_causal_gate_source_sha256": sha256_file(Path(causal_gate.__file__)),
        "M1_causal_constants": {
            "DT_S": float(causal_gate.DT_S),
            "TAU_S": float(causal_gate.TAU_S),
            "DELAY_SAMPLES": int(causal_gate.DELAY_SAMPLES),
            "THRESHOLD_PPM": float(causal_gate.THRESHOLD_PPM),
            "STOP_SAMPLES": int(causal_gate.STOP_SAMPLES),
            "HOUSES": list(causal_gate.HOUSES),
            "SEEDS": list(causal_gate.SEEDS),
            "JEFFREYS": float(causal_gate.JEFFREYS),
            "PREDICTIVE_MEMBERS": list(causal_gate.PREDICTIVE_MEMBERS),
            "SOURCE_UPDATES": int(v1.SOURCE_UPDATES),
            "SOURCE_COUNTS": dict(causal_gate.SOURCE_COUNTS),
        },
        "NULL_REPLICATES": int(v1.NULL_REPLICATES),
        "PRIMARY_MODES": list(PRIMARY_MODES),
        "RANDOM_MODES": list(RANDOM_MODES),
        "NULL_MODES": list(NULL_MODES),
    }


def build_update_arms(
    record: dict[str, Any], mapping: dict[str, Any], support: dict[str, Any]
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    native_cell = mapping["native_cell"]
    native_carrier = mapping["native_carrier"]
    labels = mapping["cell_to_source"]
    targets = {
        "identity_reconstruction": native_carrier,
        "conditional_only": np.asarray(record["q0_carrier"], dtype=np.float64),
        "full": np.asarray(record["cbpe_carrier"], dtype=np.float64),
        "global_count": np.asarray(record["global_count_carrier"], dtype=np.float64),
        "block_order_permute": np.asarray(
            record["block_order_permute_carrier"], dtype=np.float64
        ),
        "incoherent_per_block": np.asarray(
            record["incoherent_per_block_carrier"], dtype=np.float64
        ),
    }
    projected = {
        name: v2.hierarchical_project(target, native_cell, labels, label=name)
        for name, target in targets.items()
    }
    cells = {name: item["cell"] for name, item in projected.items()}
    invariant_rows = {
        name: v2.projection_invariants(target, projected[name], native_cell, labels)
        for name, target in targets.items()
    }
    invariant = {
        "identity_reconstruction_max_abs": float(
            np.max(np.abs(cells["identity_reconstruction"] - native_cell))
        ),
        "carrier_marginal_max_abs": max(
            item["carrier_marginal_max_abs"] for item in invariant_rows.values()
        ),
        "within_carrier_conditional_max_abs": max(
            item["within_carrier_conditional_max_abs"] for item in invariant_rows.values()
        ),
        "total_mass_max_abs": max(item["total_mass_abs"] for item in invariant_rows.values()),
        "fail_closed_native_max_abs": max(
            item["fail_closed_native_max_abs"] for item in invariant_rows.values()
        ),
        "cell_row_permutation_max_abs_after_restore": max(
            v2.row_permutation_projection_max_abs(target, native_cell, labels)
            for target in targets.values()
        ),
        "abstained_arms": [name for name, item in projected.items() if item["abstained"]],
    }
    return cells, invariant


def evaluate_source_label_nulls(
    final_internal: list[dict[str, Any]], support_all: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    observed: dict[str, float] = {}
    native_error: dict[str, np.ndarray] = {}
    for mode in NULL_MODES:
        native = np.asarray([row[f"native_{mode}_error_m"] for row in final_internal])
        full = np.asarray([row[f"full_{mode}_error_m"] for row in final_internal])
        if (
            not np.isfinite(native).all() or not np.isfinite(full).all()
            or np.any(native <= 0.0)
        ):
            raise ValueError(f"CTT_CBPE_NULL_ERROR_DOMAIN_FAIL:{mode}")
        native_error[mode] = native
        observed[mode] = float((np.sum(native) - np.sum(full)) / np.sum(native))
    null_values = {
        family: {mode: np.empty(v1.NULL_REPLICATES) for mode in NULL_MODES}
        for family in ("unrestricted", "free_count_stratified")
    }
    rows: list[dict[str, Any]] = []
    for replicate in range(v1.NULL_REPLICATES):
        errors = {
            family: {mode: [] for mode in NULL_MODES} for family in null_values
        }
        for item in final_internal:
            house = item["house"]
            support = support_all[house]
            maps = {
                "unrestricted": v2.uniform_permutation(
                    len(support["carriers"]), f"CBPE-UNRESTRICTED|{house}|{replicate}"
                ),
                "free_count_stratified": v2.uniform_stratified_permutation(
                    support["free_cells"], house, replicate
                ),
            }
            for family, label_map in maps.items():
                target = v1.stable_softmax(
                    np.log(item["q0_carrier"]) + item["cbpe_score"][label_map]
                )
                cell = v2.hierarchical_project(
                    target,
                    item["mapping"]["native_cell"],
                    item["mapping"]["cell_to_source"],
                    label=family + "_null",
                )["cell"]
                for mode in NULL_MODES:
                    errors[family][mode].append(v1.endpoint(
                        item["native_rows"], cell, item["truth_xy"], tie_mode=mode
                    )["error_m"])
        row: dict[str, Any] = {"replicate": replicate}
        for family in null_values:
            for mode in NULL_MODES:
                method = np.asarray(errors[family][mode])
                if not np.isfinite(method).all():
                    raise ValueError(
                        f"CTT_CBPE_NULL_METHOD_ERROR_NONFINITE:{family}:{mode}"
                    )
                value = float(
                    (np.sum(native_error[mode]) - np.sum(method))
                    / np.sum(native_error[mode])
                )
                null_values[family][mode][replicate] = value
                row[f"{family}_{mode}_pooled_relative_improvement"] = value
        rows.append(row)
    summary: dict[str, Any] = {"replicates": v1.NULL_REPLICATES, "families": {}}
    for family, modes in null_values.items():
        pvalues = {
            mode: float(
                (1 + np.count_nonzero(values >= observed[mode]))
                / (v1.NULL_REPLICATES + 1)
            )
            for mode, values in modes.items()
        }
        summary["families"][family] = {
            "empirical_upper_tail_p": pvalues,
            "maximum_primary_empirical_upper_tail_p": max(pvalues.values()),
        }
    return rows, summary


def validated_metrics(
    rows: list[dict[str, Any]], mode: str, channel: str
) -> dict[str, Any]:
    native = np.asarray(
        [row[f"native_{mode}_error_m"] for row in rows], dtype=np.float64
    )
    method = np.asarray(
        [row[f"{channel}_{mode}_error_m"] for row in rows], dtype=np.float64
    )
    if (
        len(native) == 0 or not np.isfinite(native).all()
        or not np.isfinite(method).all() or np.any(native <= 0.0)
    ):
        raise ValueError(f"CTT_CBPE_METRIC_ERROR_DOMAIN_FAIL:{channel}:{mode}")
    return v2._metrics(rows, mode, channel)


def evaluate_stage2(
    records: list[dict[str, Any]],
    historical_root: Path,
    support_all: dict[str, dict[str, Any]],
    frozen_v2_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    final_internal: list[dict[str, Any]] = []
    case_cache: dict[tuple[str, int], tuple[dict[str, Any], str]] = {}
    comparator_hashes: dict[str, str] = {}
    invariant_max = {key: 0.0 for key in PROJECTION_INVARIANT_KEYS}
    invariant_max["native_final_endpoint_parity_max_abs_m"] = 0.0
    abstained = {channel: 0 for channel in CHANNELS}
    exact_matches = 0
    for record in records:
        house, seed, update = record["house"], int(record["seed"]), int(record["update_id"])
        support = support_all[house]
        runtime = v1.runtime_root(historical_root, house, seed)
        native_path = runtime / "context_bank" / f"source_update_{update:04d}" / "source_posterior.csv"
        native_rows = v1.read_csv(native_path)
        comparator_hashes[f"{house}_seed{seed}_update{update}"] = sha256_file(native_path)
        mapping = v1.map_native_cells(native_rows, record["timing"], support)
        cell_fields, invariants = build_update_arms(record, mapping, support)
        for key in PROJECTION_INVARIANT_KEYS:
            invariant_max[key] = max(invariant_max[key], float(invariants[key]))
        for channel in invariants["abstained_arms"]:
            abstained[channel] += 1
        # This is a run-level identity diagnostic repeated in the five Stage-1
        # update records.  Count it exactly once per completed run.
        if update == 1:
            exact_matches += int(
                record["historical_measured_tape_exact_train_member_matches"]
            )

        case_key = (house, seed)
        if case_key not in case_cache:
            case_cache[case_key] = v2._case_result(historical_root, house, seed)
        case, case_sha = case_cache[case_key]
        truth_xy = tuple(float(value) for value in case["truth_eval_only"])
        truth_source, truth_cell = v1.true_support_indices(
            truth_xy, record["timing"], native_rows, mapping, support
        )
        endpoints: dict[str, dict[str, float]] = {}
        for channel, cells in {"native": mapping["native_cell"], **cell_fields}.items():
            for mode in ALL_MODES:
                endpoints[f"{channel}_{mode}"] = v1.endpoint(
                    native_rows, cells, truth_xy, tie_mode=mode
                )
        row: dict[str, Any] = {
            "house": house,
            "seed": seed,
            "source_update_id": update,
            "source_update_time_s": float(record["update_time_s"]),
            "visible_physical_stops": len(record["visible_stops"]),
            "visible_blocks": int(record["visible_blocks"]),
            "observed_hit_stops": int(record["observed_hit_stops"]),
            "observed_block_counts": ";".join(
                str(int(value)) for value in record["observed_block_counts"]
            ),
            "truth_carrier_index": truth_source,
            "truth_carrier_id": support["carriers"][truth_source],
            "native_true_cell_rank": v1.rank_desc(mapping["native_cell"], truth_cell),
            "native_carrier_true_rank": v1.rank_desc(mapping["native_carrier"], truth_source),
            "full_carrier_true_rank": v1.rank_desc(record["cbpe_carrier"], truth_source),
            "zero_mass_abstained_arms": ";".join(invariants["abstained_arms"]),
            **{key: float(value) for key, value in invariants.items() if key != "abstained_arms"},
        }
        for channel in ("native",) + CHANNELS:
            for mode in ALL_MODES:
                endpoint = endpoints[f"{channel}_{mode}"]
                row[f"{channel}_{mode}_error_m"] = endpoint["error_m"]
                row[f"{channel}_{mode}_variance_m2"] = endpoint["variance_m2"]
                row[f"{channel}_{mode}_selected_variance_m2"] = endpoint[
                    "selected_variance_m2"
                ]
        updates.append(row)
        if update == v1.SOURCE_UPDATES:
            parity = abs(
                endpoints["native_ascending"]["error_m"] - float(case["primary_error_m"])
            )
            invariant_max["native_final_endpoint_parity_max_abs_m"] = max(
                invariant_max["native_final_endpoint_parity_max_abs_m"], parity
            )
            final_internal.append({
                **record,
                **row,
                "truth_xy": truth_xy,
                "native_rows": native_rows,
                "mapping": mapping,
                "case_sha256": case_sha,
            })
    if len(updates) != 150 or len(final_internal) != 30:
        raise ValueError(f"CTT_CBPE_STAGE2_RECORD_COUNT_FAIL:{len(updates)}:{len(final_internal)}")
    frozen_native = frozen_v2_summary.get("native_source_posterior_sha256", {})
    frozen_cases = frozen_v2_summary.get("case_result_sha256", {})
    current_cases = {
        f"{house}_seed{seed}": digest
        for (house, seed), (_, digest) in case_cache.items()
    }
    if comparator_hashes != frozen_native:
        raise ValueError("CTT_CBPE_NATIVE_POSTERIOR_HASH_SET_FAIL")
    if current_cases != frozen_cases:
        raise ValueError("CTT_CBPE_CASE_RESULT_HASH_SET_FAIL")
    null_rows, null_summary = evaluate_source_label_nulls(final_internal, support_all)
    final_rows = [
        {
            key: value for key, value in item.items()
            if not isinstance(value, (np.ndarray, list, dict, Path, tuple))
        }
        for item in final_internal
    ]
    diagnostics = {
        "invariant_maxima": invariant_max,
        "abstained_updates_by_arm": abstained,
        "historical_measured_tape_exact_train_member_matches": exact_matches,
        "source_label_null": null_summary,
        "case_result_sha256": current_cases,
        "native_source_posterior_sha256": comparator_hashes,
    }
    return updates, final_rows, null_rows, diagnostics


def aggregate(
    updates: list[dict[str, Any]],
    final_rows: list[dict[str, Any]],
    diagnostics: dict[str, Any],
    prereg: dict[str, Any],
    inference_addendum: dict[str, Any],
) -> dict[str, Any]:
    full = {mode: validated_metrics(final_rows, mode, "full") for mode in ALL_MODES}
    by_house = {
        house: {
            mode: validated_metrics(
                [row for row in final_rows if row["house"] == house], mode, "full"
            )
            for mode in ALL_MODES
        }
        for house in v1.HOUSES
    }
    controls = {
        channel: {
            mode: validated_metrics(final_rows, mode, channel) for mode in ALL_MODES
        }
        for channel in ("conditional_only", "global_count", "block_order_permute", "incoherent_per_block")
    }
    incremental_gate = inference_addendum["stage2_incremental_evidence"][
        "hard_go_rules"
    ]
    incremental_evidence: dict[str, dict[str, Any]] = {}
    for comparator in ("global_count", "block_order_permute", "incoherent_per_block"):
        incremental_evidence[comparator] = {}
        for mode in PRIMARY_MODES:
            delta = np.asarray([
                row[f"full_{mode}_error_m"] - row[f"{comparator}_{mode}_error_m"]
                for row in final_rows
            ], dtype=np.float64)
            wins = int(np.count_nonzero(delta < -TOL))
            losses = int(np.count_nonzero(delta > TOL))
            ties = int(np.count_nonzero(np.abs(delta) <= TOL))
            incremental_evidence[comparator][mode] = {
                "paired_runs": len(delta),
                "paired_delta_definition": "FULL error minus comparator error",
                "mean_paired_delta_m": float(np.mean(delta)),
                "full_total_error_m": float(np.sum([
                    row[f"full_{mode}_error_m"] for row in final_rows
                ])),
                "comparator_total_error_m": float(np.sum([
                    row[f"{comparator}_{mode}_error_m"] for row in final_rows
                ])),
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "one_sided_exact_sign_p": exact_sign_upper_p(wins, losses),
            }
    inv = diagnostics["invariant_maxima"]
    limits = prereg["invariants"]
    gate = prereg["hard_go_rules"]
    random_min_pooled = min(full[mode]["pooled_relative_improvement"] for mode in RANDOM_MODES)
    random_min_improved = min(full[mode]["improved_pairs"] for mode in RANDOM_MODES)
    all_house_mode_min = min(
        by_house[house][mode]["pooled_relative_improvement"]
        for house in v1.HOUSES for mode in ALL_MODES
    )
    projection_ok = (
        inv["identity_reconstruction_max_abs"] <= float(limits["identity_projection_max_abs"])
        and inv["carrier_marginal_max_abs"] <= float(limits["carrier_marginal_max_abs"])
        and inv["within_carrier_conditional_max_abs"]
        <= float(limits["within_carrier_conditional_max_abs"])
        and inv["total_mass_max_abs"] <= float(limits["total_mass_max_abs"])
        and inv["fail_closed_native_max_abs"] <= TOL
        and inv["cell_row_permutation_max_abs_after_restore"] <= TOL
        and inv["native_final_endpoint_parity_max_abs_m"]
        <= float(limits["native_final_endpoint_parity_max_abs_m"])
    )
    rules = {
        "valid_updates_exactly": len(updates) == int(gate["valid_updates_exactly"]),
        "valid_final_pairs_exactly": len(final_rows) == int(gate["valid_final_pairs_exactly"]),
        "all_projection_invariants": projection_ok,
        "pooled_each_primary": min(
            full[mode]["pooled_relative_improvement"] for mode in PRIMARY_MODES
        ) >= float(gate["pooled_relative_improvement_each_primary_mode_at_least"]),
        "fixed_random_minimum_pooled": random_min_pooled
        >= float(gate["fixed_random_minimum_pooled_relative_improvement_at_least"]),
        "improved_pairs_each_primary": min(
            full[mode]["improved_pairs"] for mode in PRIMARY_MODES
        ) >= int(gate["improved_pairs_each_primary_mode_at_least"]),
        "fixed_random_minimum_improved_pairs": random_min_improved
        >= int(gate["fixed_random_minimum_improved_pairs_at_least"]),
        "each_house_each_tie_mode": all_house_mode_min
        >= float(gate["each_house_each_tie_mode_pooled_relative_improvement_at_least"]),
        "median_pair_each_primary": min(
            full[mode]["median_pair_relative_improvement"] for mode in PRIMARY_MODES
        ) >= float(gate["median_pair_relative_improvement_each_primary_mode_at_least"]),
        "catastrophes_every_tie_mode": max(
            full[mode]["catastrophic_regressions"] for mode in ALL_MODES
        ) <= int(gate["catastrophic_regressions_every_tie_mode_at_most"]),
        "new_false_confident_collapses": max(
            full[mode]["new_false_confident_collapses"] for mode in PRIMARY_MODES
        ) <= int(gate["new_false_confident_collapses_every_primary_mode_at_most"]),
        "unrestricted_source_label_p": diagnostics["source_label_null"]["families"]
        ["unrestricted"]["maximum_primary_empirical_upper_tail_p"]
        <= float(gate["unrestricted_source_label_empirical_p_at_most"]),
        "stratified_source_label_p": diagnostics["source_label_null"]["families"]
        ["free_count_stratified"]["maximum_primary_empirical_upper_tail_p"]
        <= float(gate["free_count_stratified_source_label_empirical_p_at_most"]),
        "full_strictly_better_total_error_than_global_count_each_primary": all(
            full[mode]["method_total_error_m"]
            < controls["global_count"][mode]["method_total_error_m"] - TOL
            for mode in PRIMARY_MODES
        ),
        "full_strictly_better_total_error_than_block_order_permute_each_primary": all(
            full[mode]["method_total_error_m"]
            < controls["block_order_permute"][mode]["method_total_error_m"] - TOL
            for mode in PRIMARY_MODES
        ),
        "full_strictly_better_total_error_than_incoherent_per_block_each_primary": all(
            full[mode]["method_total_error_m"]
            < controls["incoherent_per_block"][mode]["method_total_error_m"] - TOL
            for mode in PRIMARY_MODES
        ),
        "incremental_paired_runs_exactly": all(
            incremental_evidence[comparator][mode]["paired_runs"]
            == int(incremental_gate["paired_runs_exactly"])
            for comparator in incremental_evidence for mode in PRIMARY_MODES
        ),
        "full_vs_each_comparator_each_primary_exact_sign_p": all(
            incremental_evidence[comparator][mode]["one_sided_exact_sign_p"]
            <= float(incremental_gate[
                "full_vs_each_comparator_each_primary_mode_exact_sign_p_at_most"
            ])
            for comparator in incremental_evidence for mode in PRIMARY_MODES
        ),
        "no_exact_train_member_matches": diagnostics[
            "historical_measured_tape_exact_train_member_matches"
        ] == int(gate["historical_measured_tape_exact_train_member_matches"]),
    }
    verdict = PASS if all(rules.values()) else NO_GO
    return {
        "verdict": verdict,
        "hard_pass_rules": rules,
        "overall": full,
        "by_house": by_house,
        "controls": controls,
        "incremental_evidence": incremental_evidence,
        "fixed_random_tie_worst_case": {
            "minimum_pooled_relative_improvement": random_min_pooled,
            "minimum_improved_pairs": random_min_improved,
            "minimum_house_pooled_relative_improvement_all_modes": all_house_mode_min,
        },
        **diagnostics,
    }


def selftest() -> None:
    rng = np.random.default_rng(20260831)
    tensors = {
        house: [
            rng.integers(0, BLOCK_STATES, size=(4, len(v1.PREDICTIVE_MEMBERS), v1.SOURCE_UPDATES))
            for _ in v1.SEEDS
        ]
        for house in v1.HOUSES
    }
    q, counts, domain = fit_global_lomo_q(tensors)
    assert np.max(np.abs(q.sum(axis=1) - 1.0)) <= TOL
    assert int(np.sum(counts)) == 3 * 10 * 4 * 5 * 8 * 7
    assert domain["source_house_seed_conditioned_tables"] is False
    for heldout in v1.PREDICTIVE_MEMBERS:
        q_minus, counts_minus, excluded = fit_global_lomo_q(
            tensors, excluded_member=heldout
        )
        assert excluded["excluded_member"] == heldout
        assert int(np.sum(counts_minus)) == 3 * 10 * 4 * 5 * 7 * 6
        assert np.max(np.abs(q_minus.sum(axis=1) - 1.0)) <= TOL

    events = rng.integers(0, 2, size=(4, 8, 17), dtype=np.int8).astype(bool)
    blocks = [np.asarray([0, 2, 4]), np.asarray([5, 6, 8]), np.asarray([9, 10, 11]),
              np.asarray([12, 13, 14]), np.asarray([1, 3, 7])]
    counts_from_events = block_counts(events, blocks)
    permuted_events = events.copy()
    for block in blocks:
        permuted_events[:, :, block] = events[:, :, block[::-1]]
    assert np.array_equal(counts_from_events, block_counts(permuted_events, blocks))

    candidate = tensors["H01"][0]
    observed = candidate[0, 0]
    ordered = coherent_cbpe_score(candidate, observed, q, 5)
    online = np.zeros(candidate.shape[:2])
    for block in range(5):
        online += np.log(q)[candidate[:, :, block], observed[block]]
        assert np.max(np.abs(
            _logmeanexp(online, axis=1)
            - coherent_cbpe_score(candidate, observed, q, block + 1)
        )) <= TOL
    order = np.asarray([4, 3, 2, 1, 0])
    assert np.isfinite(coherent_cbpe_score(
        candidate, observed, q, 5, observed_block_order=order
    )).all()
    incoherent = incoherent_per_block_score(candidate, observed, q, 5)
    assert ordered.shape == incoherent.shape == (4,)

    # A block-label permutation preserves the multiset of counts but changes
    # an ordered likelihood when the sequence carries information.
    q_crafted = np.full((BLOCK_STATES, BLOCK_STATES), 0.01, dtype=np.float64)
    np.fill_diagonal(q_crafted, 0.97)
    ordered_counts = np.tile(
        np.asarray([0, 1, 2, 3, 0], dtype=np.int64), (1, 8, 1)
    )
    ordered_observation = np.asarray([0, 1, 2, 3, 0], dtype=np.int64)
    perm = np.asarray([4, 3, 2, 1, 0], dtype=np.int64)
    block_score = coherent_cbpe_score(
        ordered_counts, ordered_observation, q_crafted, 5
    )
    permuted_block_score = coherent_cbpe_score(
        ordered_counts, ordered_observation, q_crafted, 5,
        observed_block_order=perm,
    )
    assert sorted(ordered_observation.tolist()) == sorted(
        ordered_observation[perm].tolist()
    )
    assert np.max(np.abs(block_score - permuted_block_score)) > 1.0

    # Deliberate identity switching: no single member explains the alternating
    # tape, while an incoherent per-block mixture can switch members.  The
    # latter must therefore score higher; this guards the marginalization axes.
    switching = np.empty((1, 8, 5), dtype=np.int64)
    switching[:, :4, :] = 0
    switching[:, 4:, :] = 3
    switching_observation = np.asarray([0, 3, 0, 3, 0], dtype=np.int64)
    coherent_switch = coherent_cbpe_score(
        switching, switching_observation, q_crafted, 5
    )[0]
    incoherent_switch = incoherent_per_block_score(
        switching, switching_observation, q_crafted, 5
    )[0]
    assert incoherent_switch > coherent_switch + 1.0

    # Pooled Q must be invariant to enumeration of sources, Houses and routes.
    transformed: dict[str, list[np.ndarray]] = {}
    cycled = {"H01": "H02", "H02": "H03", "H03": "H01"}
    for house in v1.HOUSES:
        transformed[house] = [
            value[::-1].copy() for value in reversed(tensors[cycled[house]])
        ]
    q_transformed, counts_transformed, _ = fit_global_lomo_q(transformed)
    assert np.array_equal(counts, counts_transformed)
    assert np.max(np.abs(q - q_transformed)) <= TOL

    assert exact_sign_upper_p(0, 0) == 1.0
    assert exact_sign_upper_p(5, 0) < exact_sign_upper_p(4, 1)

    invariants = premise_invariance_audit(tensors)
    assert invariants["within_block_permutation_max_abs"] == 0.0
    assert invariants["candidate_permutation_max_abs"] <= TOL
    assert invariants["member_permutation_max_abs"] <= TOL

    docs_root = Path(__file__).resolve().parents[3] / "docs"
    premise_rules = json.loads((
        docs_root / "CTT_CBPE_TWO_MODULE_V3_PRETRUTH_PREMISE_ADDENDUM_20260831.json"
    ).read_text(encoding="utf-8"))
    inference_rules = json.loads((
        docs_root
        / "CTT_CBPE_TWO_MODULE_V3_INFERENCE_AND_INCREMENTAL_EVIDENCE_ADDENDUM_20260831.json"
    ).read_text(encoding="utf-8"))
    fold_rows, route_rows, premise_source_rows, premise_null_rows, _ = (
        evaluate_pretruth_premise(tensors, premise_rules, inference_rules)
    )
    assert len(fold_rows) == 240
    assert len(route_rows) == 30
    assert all(row["heldout_member_folds"] == 8 for row in route_rows)
    assert len(premise_source_rows) == 240 * 4
    assert len(premise_null_rows) == v1.NULL_REPLICATES

    labels = np.asarray([0, 0, 1, 1])
    native = np.asarray([0.1, 0.2, 0.3, 0.4])
    target = np.asarray([0.6, 0.4])
    projected = v2.hierarchical_project(target, native, labels, label="cbpe_selftest")
    assert np.max(np.abs(v2.carrier_marginal(projected["cell"], labels, 2) - target)) <= TOL

    # Aggregate-level temporal incremental-evidence Gate: all 30 paired runs
    # winning must pass; a FULL/control tie must fail both strict total error
    # and the paired exact sign test.
    synthetic_final: list[dict[str, Any]] = []
    for house in v1.HOUSES:
        for seed in v1.SEEDS:
            row: dict[str, Any] = {"house": house, "seed": int(seed)}
            for mode in ALL_MODES:
                row[f"native_{mode}_error_m"] = 10.0
                row[f"native_{mode}_variance_m2"] = 4.0
                for channel in (
                    "full", "conditional_only", "global_count",
                    "block_order_permute", "incoherent_per_block",
                ):
                    row[f"{channel}_{mode}_error_m"] = 5.0 if channel == "full" else 6.0
                    row[f"{channel}_{mode}_variance_m2"] = 4.0
            synthetic_final.append(row)
    synthetic_prereg = {
        "invariants": {
            "identity_projection_max_abs": TOL,
            "carrier_marginal_max_abs": TOL,
            "within_carrier_conditional_max_abs": TOL,
            "total_mass_max_abs": TOL,
            "native_final_endpoint_parity_max_abs_m": TOL,
        },
        "hard_go_rules": {
            "valid_updates_exactly": 150,
            "valid_final_pairs_exactly": 30,
            "pooled_relative_improvement_each_primary_mode_at_least": 0.1,
            "fixed_random_minimum_pooled_relative_improvement_at_least": 0.1,
            "improved_pairs_each_primary_mode_at_least": 20,
            "fixed_random_minimum_improved_pairs_at_least": 20,
            "each_house_each_tie_mode_pooled_relative_improvement_at_least": -0.05,
            "median_pair_relative_improvement_each_primary_mode_at_least": 0.0,
            "catastrophic_regressions_every_tie_mode_at_most": 0,
            "new_false_confident_collapses_every_primary_mode_at_most": 0,
            "unrestricted_source_label_empirical_p_at_most": 0.01,
            "free_count_stratified_source_label_empirical_p_at_most": 0.01,
            "historical_measured_tape_exact_train_member_matches": 0,
        },
    }
    synthetic_inference = {
        "stage2_incremental_evidence": {"hard_go_rules": {
            "paired_runs_exactly": 30,
            "full_vs_each_comparator_each_primary_mode_exact_sign_p_at_most": 0.05,
        }}
    }
    synthetic_diagnostics = {
        "invariant_maxima": {
            "identity_reconstruction_max_abs": 0.0,
            "carrier_marginal_max_abs": 0.0,
            "within_carrier_conditional_max_abs": 0.0,
            "total_mass_max_abs": 0.0,
            "fail_closed_native_max_abs": 0.0,
            "cell_row_permutation_max_abs_after_restore": 0.0,
            "native_final_endpoint_parity_max_abs_m": 0.0,
        },
        "source_label_null": {"families": {
            "unrestricted": {"maximum_primary_empirical_upper_tail_p": 0.0},
            "free_count_stratified": {"maximum_primary_empirical_upper_tail_p": 0.0},
        }},
        "historical_measured_tape_exact_train_member_matches": 0,
    }
    aggregate_pass = aggregate(
        [{} for _ in range(150)], synthetic_final, synthetic_diagnostics,
        synthetic_prereg, synthetic_inference,
    )
    assert aggregate_pass["verdict"] == PASS
    assert aggregate_pass["incremental_evidence"]["global_count"]["ascending"][
        "one_sided_exact_sign_p"
    ] <= 0.05
    strict_rule = {
        "global_count": "full_strictly_better_total_error_than_global_count_each_primary",
        "block_order_permute": (
            "full_strictly_better_total_error_than_block_order_permute_each_primary"
        ),
        "incoherent_per_block": (
            "full_strictly_better_total_error_than_incoherent_per_block_each_primary"
        ),
    }
    for comparator in strict_rule:
        tied_final = [dict(row) for row in synthetic_final]
        for row in tied_final:
            for mode in PRIMARY_MODES:
                row[f"{comparator}_{mode}_error_m"] = row[f"full_{mode}_error_m"]
        aggregate_fail = aggregate(
            [{} for _ in range(150)], tied_final, synthetic_diagnostics,
            synthetic_prereg, synthetic_inference,
        )
        assert aggregate_fail["verdict"] == NO_GO
        assert not aggregate_fail["hard_pass_rules"][strict_rule[comparator]]
        assert aggregate_fail["incremental_evidence"][comparator]["ascending"][
            "one_sided_exact_sign_p"
        ] == 1.0
        assert not aggregate_fail["hard_pass_rules"][
            "full_vs_each_comparator_each_primary_exact_sign_p"
        ]

    for key, bad_value in (
        ("native_ascending_error_m", 0.0),
        ("native_ascending_error_m", float("nan")),
        ("full_ascending_error_m", float("inf")),
    ):
        bad_row = dict(synthetic_final[0])
        bad_row[key] = bad_value
        try:
            validated_metrics([bad_row], "ascending", "full")
        except ValueError as error:
            assert "CTT_CBPE_METRIC_ERROR_DOMAIN_FAIL" in str(error)
        else:
            raise AssertionError(f"metric domain guard accepted {key}={bad_value}")
    bad_null = [dict(row) for row in synthetic_final]
    bad_null[0][f"native_{NULL_MODES[0]}_error_m"] = 0.0
    try:
        evaluate_source_label_nulls(bad_null, {})
    except ValueError as error:
        assert "CTT_CBPE_NULL_ERROR_DOMAIN_FAIL" in str(error)
    else:
        raise AssertionError("source-label null accepted a zero native pair")

    synthetic: list[dict[str, Any]] = []
    synthetic_run_hashes: dict[tuple[str, int], dict[str, str]] = {}
    for house in v1.HOUSES:
        for seed in v1.SEEDS:
            for update in range(1, v1.SOURCE_UPDATES + 1):
                record: dict[str, Any] = {
                    "house": house,
                    "seed": seed,
                    "update_id": update,
                    "update_time_s": float(update),
                    "visible_stops": np.arange(update * 3),
                    "visible_blocks": update,
                    "observed_hit_stops": update,
                    "observed_block_counts": np.arange(update) % 4,
                    "block_order_permutation": np.arange(update),
                    "historical_measured_tape_exact_train_member_matches": 0,
                    "timing": {"grid_width": "1"},
                    "online_batch_score_max_abs": 0.0,
                    "online_batch_joint_posterior_max_abs": 0.0,
                }
                for key in STAGE1_ARRAY_KEYS:
                    record[key] = np.full(4, 0.25)
                synthetic.append(record)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for stop_count in (17, 18):
            support_root = root / f"support_{stop_count}"
            runtime = v1.runtime_root(support_root, "H01", 0)
            (runtime / "context_bank").mkdir(parents=True)
            pose_path = runtime / "sim_pose_trace.csv"
            sample_count = stop_count * causal_gate.STOP_SAMPLES
            pose_time = np.arange(sample_count, dtype=np.float64) * causal_gate.DT_S
            pose_path.write_text(
                "t_sim_s\n" + "".join(f"{value:.9f}\n" for value in pose_time),
                encoding="utf-8",
            )
            stops = [
                np.arange(
                    index * causal_gate.STOP_SAMPLES,
                    (index + 1) * causal_gate.STOP_SAMPLES,
                    dtype=np.int64,
                )
                for index in range(stop_count)
            ]
            update_times = [pose_time[int(stops[index][-1])] for index in (2, 5, 8, 11, 14)]
            (runtime / "context_bank" / "source_update_timing.csv").write_text(
                "sim_time\n" + "".join(f"{value:.9f}\n" for value in update_times),
                encoding="utf-8",
            )
            authorized = authorized_stop_support(
                support_root, "H01", 0,
                {"path": pose_path, "length": sample_count, "stops": stops},
            )
            assert [len(value) for value in authorized["prefixes"]] == [3, 6, 9, 12, 15]
            assert [len(value) for value in authorized["blocks"]] == [3, 3, 3, 3, 3]
            assert len(authorized["authorized_union"]) == 15
            assert len(authorized["excluded"]) == stop_count - 15

        historical = root / "historical"
        for house in v1.HOUSES:
            for seed in v1.SEEDS:
                runtime = v1.runtime_root(historical, house, seed)
                (runtime / "context_bank").mkdir(parents=True)
                paths = {
                    "sensor_trace": runtime / "sensor_trace.csv",
                    "sim_pose_trace": runtime / "sim_pose_trace.csv",
                    "source_update_timing": runtime / "context_bank" / "source_update_timing.csv",
                }
                for label, path in paths.items():
                    path.write_text(f"label\n{house}-{seed}-{label}\n", encoding="utf-8")
                synthetic_run_hashes[(house, seed)] = {
                    label: sha256_file(path) for label, path in paths.items()
                }
        for record in synthetic:
            record["historical_run_input_hashes"] = synthetic_run_hashes[
                (record["house"], int(record["seed"]))
            ]
        prereg = root / "prereg.json"
        freeze = root / "INPUT_FREEZE.json"
        prereg.write_text("{}\n", encoding="utf-8")
        synthetic_binding = {
            "preregistration_sha256": sha256_file(prereg),
            "premise_addendum_sha256": "premise",
            "stop_support_addendum_sha256": "stop",
            "inference_addendum_sha256": "inference",
            "evaluator_sha256": sha256_file(Path(__file__)),
            "imported_v1_source_sha256": sha256_file(Path(v1.__file__)),
            "imported_v2_source_sha256": sha256_file(Path(v2.__file__)),
            "imported_causal_gate_source_sha256": sha256_file(
                Path(causal_gate.__file__)
            ),
            "M1_causal_constants": {
                "DT_S": float(causal_gate.DT_S),
                "TAU_S": float(causal_gate.TAU_S),
                "DELAY_SAMPLES": int(causal_gate.DELAY_SAMPLES),
                "THRESHOLD_PPM": float(causal_gate.THRESHOLD_PPM),
                "STOP_SAMPLES": int(causal_gate.STOP_SAMPLES),
                "HOUSES": list(causal_gate.HOUSES),
                "SEEDS": list(causal_gate.SEEDS),
                "JEFFREYS": float(causal_gate.JEFFREYS),
                "PREDICTIVE_MEMBERS": list(causal_gate.PREDICTIVE_MEMBERS),
                "SOURCE_UPDATES": int(v1.SOURCE_UPDATES),
                "SOURCE_COUNTS": dict(causal_gate.SOURCE_COUNTS),
            },
            "NULL_REPLICATES": int(v1.NULL_REPLICATES),
            "PRIMARY_MODES": list(PRIMARY_MODES),
            "RANDOM_MODES": list(RANDOM_MODES),
            "NULL_MODES": list(NULL_MODES),
        }
        freeze.write_text(json.dumps({
            "cbpe_pretruth_premise_hard_pass_rules": {"synthetic": True},
            "cbpe_pretruth_premise_summary_sha256": "synthetic",
            "cbpe_pretruth_premise_verdict_sha256": "synthetic",
            "cbpe_pretruth_premise_input_freeze_sha256": "synthetic",
            "preregistration_sha256": synthetic_binding["preregistration_sha256"],
            "premise_addendum_sha256": synthetic_binding["premise_addendum_sha256"],
            "stop_support_addendum_sha256": synthetic_binding["stop_support_addendum_sha256"],
            "inference_addendum_sha256": synthetic_binding["inference_addendum_sha256"],
            "evaluator_sha256": synthetic_binding["evaluator_sha256"],
            "implementation_binding": synthetic_binding,
        }) + "\n", encoding="utf-8")
        manifest = write_stage1_artifact(
            root, synthetic, q, counts, domain, prereg, freeze, 4936
        )
        loaded, loaded_q, loaded_counts, loaded_manifest = load_stage1_artifact(
            root, prereg, sha256_file(root / "CBPE_STAGE1_MANIFEST.json"),
            historical, synthetic_binding,
            {"summary": "synthetic", "verdict": "synthetic", "input_freeze": "synthetic"},
        )
        assert len(loaded) == 150
        assert np.array_equal(loaded_counts, counts)
        assert np.max(np.abs(loaded_q - q)) <= TOL
        assert manifest["pretruth_semantic_sha256"] == loaded_manifest[
            "pretruth_semantic_sha256"
        ]
        mismatch_bindings = []
        config_mismatch = json.loads(json.dumps(synthetic_binding))
        config_mismatch["NULL_REPLICATES"] += 1
        mismatch_bindings.append(config_mismatch)
        causal_mismatch = json.loads(json.dumps(synthetic_binding))
        causal_mismatch["M1_causal_constants"]["DT_S"] += 0.1
        mismatch_bindings.append(causal_mismatch)
        for mismatched in mismatch_bindings:
            try:
                load_stage1_artifact(
                    root, prereg, sha256_file(root / "CBPE_STAGE1_MANIFEST.json"),
                    historical, mismatched,
                    {"summary": "synthetic", "verdict": "synthetic", "input_freeze": "synthetic"},
                )
            except SystemExit as error:
                assert "CTT_CBPE_STAGE1_CONTRACT_OR_HASH_FAIL" in str(error)
            else:
                raise AssertionError(
                    "Stage-1 implementation/M1 binding mismatch did not fail closed"
                )
    print("CTT_CBPE_TWO_MODULE_V3_SELFTEST=PASS")


def verify_contract_documents(
    preregistration: Path,
    premise_addendum_path: Path,
    stop_addendum_path: Path,
    inference_addendum_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    prereg = json.loads(preregistration.read_text(encoding="utf-8"))
    premise_addendum = json.loads(premise_addendum_path.read_text(encoding="utf-8"))
    stop_addendum = json.loads(stop_addendum_path.read_text(encoding="utf-8"))
    inference_addendum = json.loads(
        inference_addendum_path.read_text(encoding="utf-8")
    )
    prereg_sha = sha256_file(preregistration)
    premise_sha = sha256_file(premise_addendum_path)
    stop_sha = sha256_file(stop_addendum_path)
    if (
        prereg.get("contract") != CONTRACT
        or prereg.get("status") != PREREG_STATUS
        or premise_addendum.get("contract") != PREMISE_CONTRACT
        or premise_addendum.get("status") != PREMISE_STATUS
        or premise_addendum.get("parent_preregistration_sha256") != prereg_sha
        or stop_addendum.get("contract") != "CTT_CBPE_TWO_MODULE_V3_STOP_SUPPORT_ADDENDUM"
        or stop_addendum.get("status") != PREMISE_STATUS
        or stop_addendum.get("parent_preregistration_sha256") != prereg_sha
        or stop_addendum.get("premise_addendum_sha256") != premise_sha
        or inference_addendum.get("contract") != INFERENCE_CONTRACT
        or inference_addendum.get("status") != INFERENCE_STATUS
        or inference_addendum.get("parent_preregistration_sha256") != prereg_sha
        or inference_addendum.get("premise_addendum_sha256") != premise_sha
        or inference_addendum.get("stop_support_addendum_sha256") != stop_sha
    ):
        raise SystemExit("CTT_CBPE_CONTRACT_DOCUMENT_CHAIN_FAIL")
    return prereg, premise_addendum, stop_addendum, inference_addendum


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--stage", choices=("premise", "1", "2"))
    parser.add_argument("--bank-root", type=Path)
    parser.add_argument("--historical-root", type=Path)
    parser.add_argument("--source-support", type=Path)
    parser.add_argument("--causal-premise-verdict", type=Path)
    parser.add_argument("--causal-premise-summary", type=Path)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--premise-addendum", type=Path)
    parser.add_argument("--stop-support-addendum", type=Path)
    parser.add_argument("--inference-addendum", type=Path)
    parser.add_argument("--cbpe-premise-root", type=Path)
    parser.add_argument("--cbpe-premise-summary-sha256")
    parser.add_argument("--cbpe-premise-verdict-sha256")
    parser.add_argument("--cbpe-premise-input-freeze-sha256")
    parser.add_argument("--stage1-root", type=Path)
    parser.add_argument("--stage1-manifest-sha256")
    parser.add_argument("--frozen-v2-summary", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    common = (
        args.stage, args.historical_root, args.source_support, args.preregistration,
        args.premise_addendum, args.stop_support_addendum, args.inference_addendum,
        args.output,
    )
    if any(value is None for value in common):
        raise SystemExit("CTT_CBPE_REQUIRED_ARGUMENT_MISSING")
    if args.output.exists():
        raise SystemExit(f"CTT_CBPE_REFUSE_OVERWRITE:{args.output}")
    prereg, premise_addendum, stop_addendum, inference_addendum = verify_contract_documents(
        args.preregistration, args.premise_addendum, args.stop_support_addendum,
        args.inference_addendum,
    )
    current_binding = implementation_binding(
        args.preregistration, args.premise_addendum, args.stop_support_addendum,
        args.inference_addendum,
    )
    if sha256_file(args.source_support) != prereg["frozen_inputs"][
        "region_support_manifest_sha256"
    ]:
        raise SystemExit("CTT_CBPE_SOURCE_SUPPORT_HASH_FAIL")

    if args.stage in ("premise", "1"):
        if any(value is None for value in (
            args.bank_root, args.causal_premise_verdict, args.causal_premise_summary
        )):
            raise SystemExit("CTT_CBPE_PREDICTIVE_STAGE_ARGUMENT_FAIL")
        _, manifest, schedules, freeze = validate_predictive_inputs(
            args.bank_root,
            args.historical_root,
            args.source_support,
            args.causal_premise_verdict,
            args.causal_premise_summary,
            prereg,
        )
        support_all = v1.load_support(args.source_support)
        tensors, _, prefit_shards = materialize_predictive_counts(
            args.bank_root, manifest, schedules, support_all
        )
        q, q_counts, q_domain = fit_global_lomo_q(tensors)
        freeze.update({
            "preregistration_sha256": sha256_file(args.preregistration),
            "premise_addendum_sha256": sha256_file(args.premise_addendum),
            "stop_support_addendum_sha256": sha256_file(args.stop_support_addendum),
            "inference_addendum_sha256": sha256_file(args.inference_addendum),
            "evaluator_sha256": sha256_file(Path(__file__)),
            "predictive_prefit_verified_shards": prefit_shards,
            "global_q_sha256": canonical_array_sha256(q),
            "global_q_lomo_counts_sha256": canonical_array_sha256(q_counts),
            "global_q_training_domain": q_domain,
            "implementation_binding": current_binding,
        })
        args.output.mkdir(parents=True)
        freeze_path = args.output / "INPUT_FREEZE.json"
        freeze_path.write_text(
            json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if args.stage == "premise":
            cluster_rows, route_rows, source_rows, null_rows, summary = evaluate_pretruth_premise(
                tensors, premise_addendum, inference_addendum
            )
            summary["input_hashes"] = {
                "preregistration": sha256_file(args.preregistration),
                "premise_addendum": sha256_file(args.premise_addendum),
                "stop_support_addendum": sha256_file(args.stop_support_addendum),
                "inference_addendum": sha256_file(args.inference_addendum),
                "evaluator": sha256_file(Path(__file__)),
                "input_freeze": sha256_file(freeze_path),
            }
            write_csv(args.output / "PREMISE_CLUSTERS.csv", cluster_rows)
            write_csv(args.output / "PREMISE_ROUTE_CLUSTERS.csv", route_rows)
            write_csv(args.output / "PREMISE_SOURCE_RANKS.csv", source_rows)
            write_csv(args.output / "SOURCE_LABEL_NULLS.csv", null_rows)
            summary_path = args.output / "PREMISE_SUMMARY.json"
            verdict_path = args.output / "PREMISE_VERDICT.txt"
            summary_path.write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            verdict_path.write_text(summary["verdict"] + "\n", encoding="utf-8")
            (args.output / "SHA256SUMS.txt").write_text(
                f"{sha256_file(summary_path)}  PREMISE_SUMMARY.json\n"
                f"{sha256_file(verdict_path)}  PREMISE_VERDICT.txt\n"
                f"{sha256_file(args.output / 'PREMISE_CLUSTERS.csv')}  PREMISE_CLUSTERS.csv\n"
                f"{sha256_file(args.output / 'PREMISE_ROUTE_CLUSTERS.csv')}  PREMISE_ROUTE_CLUSTERS.csv\n"
                f"{sha256_file(args.output / 'PREMISE_SOURCE_RANKS.csv')}  PREMISE_SOURCE_RANKS.csv\n"
                f"{sha256_file(args.output / 'SOURCE_LABEL_NULLS.csv')}  SOURCE_LABEL_NULLS.csv\n",
                encoding="utf-8",
            )
            print(json.dumps(summary, indent=2), flush=True)
            return 0

        if any(value is None for value in (
            args.cbpe_premise_root,
            args.cbpe_premise_summary_sha256,
            args.cbpe_premise_verdict_sha256,
            args.cbpe_premise_input_freeze_sha256,
        )):
            raise SystemExit("CTT_CBPE_STAGE1_PREMISE_ARGUMENT_FAIL")
        premise_summary_path = args.cbpe_premise_root / "PREMISE_SUMMARY.json"
        premise_verdict_path = args.cbpe_premise_root / "PREMISE_VERDICT.txt"
        premise_freeze_path = args.cbpe_premise_root / "INPUT_FREEZE.json"
        premise_summary = json.loads(premise_summary_path.read_text(encoding="utf-8"))
        current_q_minus = {
            str(heldout): canonical_array_sha256(*fit_global_lomo_q(
                tensors, excluded_member=heldout
            )[:2])
            for heldout in v1.PREDICTIVE_MEMBERS
        }
        if (
            sha256_file(premise_summary_path) != args.cbpe_premise_summary_sha256
            or sha256_file(premise_verdict_path) != args.cbpe_premise_verdict_sha256
            or premise_verdict_path.read_text(encoding="utf-8").strip() != PREMISE_PASS
            or premise_summary.get("verdict") != PREMISE_PASS
            or not all(premise_summary.get("hard_pass_rules", {}).values())
            or sha256_file(premise_freeze_path)
            != args.cbpe_premise_input_freeze_sha256
            or premise_summary.get("input_hashes", {}).get("input_freeze")
            != args.cbpe_premise_input_freeze_sha256
            or sha256_file(freeze_path) != args.cbpe_premise_input_freeze_sha256
            or premise_summary.get("input_hashes", {}).get("evaluator")
            != current_binding["evaluator_sha256"]
            or premise_summary.get("input_hashes", {}).get("preregistration")
            != current_binding["preregistration_sha256"]
            or premise_summary.get("input_hashes", {}).get("premise_addendum")
            != current_binding["premise_addendum_sha256"]
            or premise_summary.get("input_hashes", {}).get("stop_support_addendum")
            != current_binding["stop_support_addendum_sha256"]
            or premise_summary.get("input_hashes", {}).get("inference_addendum")
            != current_binding["inference_addendum_sha256"]
            or premise_summary.get("Q_minus_h_sha256") != current_q_minus
        ):
            raise SystemExit("CTT_CBPE_STAGE1_PREMISE_PASS_HASH_FAIL")
        freeze["cbpe_pretruth_premise_summary_sha256"] = sha256_file(premise_summary_path)
        freeze["cbpe_pretruth_premise_verdict_sha256"] = sha256_file(premise_verdict_path)
        freeze["cbpe_pretruth_premise_input_freeze_sha256"] = sha256_file(
            premise_freeze_path
        )
        freeze["cbpe_pretruth_premise_hard_pass_rules"] = premise_summary[
            "hard_pass_rules"
        ]
        freeze_path.write_text(
            json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        # Q and its training domain were frozen before this point.  Only now
        # may the measured tape be opened and Stage-1 posteriors constructed.
        records, q2, counts2, domain2, verified_shards = evaluate_stage1(
            args.bank_root,
            args.historical_root,
            manifest,
            schedules,
            support_all,
            q,
            q_counts,
            q_domain,
        )
        if np.max(np.abs(q2 - q)) > TOL or not np.array_equal(counts2, q_counts):
            raise ValueError("CTT_CBPE_STAGE1_Q_DRIFT_FAIL")
        stage1 = write_stage1_artifact(
            args.output,
            records,
            q2,
            counts2,
            domain2,
            args.preregistration,
            freeze_path,
            verified_shards,
        )
        print(json.dumps({
            "stage": 1,
            "status": stage1["status"],
            "records": stage1["records"],
            "artifact_sha256": stage1["artifact_sha256"],
            "manifest_sha256": sha256_file(args.output / "CBPE_STAGE1_MANIFEST.json"),
            "pretruth_semantic_sha256": stage1["pretruth_semantic_sha256"],
        }, indent=2), flush=True)
        return 0

    if any(value is None for value in (
        args.stage1_root,
        args.stage1_manifest_sha256,
        args.frozen_v2_summary,
        args.cbpe_premise_summary_sha256,
        args.cbpe_premise_verdict_sha256,
        args.cbpe_premise_input_freeze_sha256,
    )) or args.bank_root is not None:
        raise SystemExit("CTT_CBPE_STAGE2_ARGUMENT_FAIL")
    if sha256_file(args.frozen_v2_summary) != prereg[
        "preserved_negative_dependencies"
    ]["v2_summary_sha256"]:
        raise SystemExit("CTT_CBPE_FROZEN_V2_SUMMARY_HASH_FAIL")
    frozen_v2_summary = json.loads(args.frozen_v2_summary.read_text(encoding="utf-8"))
    records, q, q_counts, stage1 = load_stage1_artifact(
        args.stage1_root, args.preregistration, args.stage1_manifest_sha256,
        args.historical_root, current_binding,
        {
            "summary": args.cbpe_premise_summary_sha256,
            "verdict": args.cbpe_premise_verdict_sha256,
            "input_freeze": args.cbpe_premise_input_freeze_sha256,
        },
    )
    support_all = v1.load_support(args.source_support)
    args.output.mkdir(parents=True)
    try:
        updates, final_rows, null_rows, diagnostics = evaluate_stage2(
            records, args.historical_root, support_all, frozen_v2_summary
        )
        result = aggregate(
            updates, final_rows, diagnostics, prereg, inference_addendum
        )
    except Exception as error:
        (args.output / "VERDICT.txt").write_text(INVALID + "\n", encoding="utf-8")
        (args.output / "FIRST_ERROR.txt").write_text(
            f"{type(error).__name__}: {error}\n", encoding="utf-8"
        )
        raise
    report = {
        "contract": CONTRACT,
        "fixed_trajectory_development_only": True,
        "closed_loop_effectiveness_established": False,
        "gaden_runs": 0,
        "neural_training": False,
        "scientific_modules": prereg["scientific_modules"],
        "CBPE_formula": prereg["CBPE_formula"],
        "global_q": q.tolist(),
        "global_q_lomo_counts": q_counts.tolist(),
        **result,
        "input_hashes": {
            "preregistration": sha256_file(args.preregistration),
            "premise_addendum": sha256_file(args.premise_addendum),
            "stop_support_addendum": sha256_file(args.stop_support_addendum),
            "inference_addendum": sha256_file(args.inference_addendum),
            "evaluator": sha256_file(Path(__file__)),
            "stage1_artifact": stage1["artifact_sha256"],
            "stage1_manifest": sha256_file(args.stage1_root / "CBPE_STAGE1_MANIFEST.json"),
            "source_support": sha256_file(args.source_support),
            "frozen_v2_summary": sha256_file(args.frozen_v2_summary),
        },
    }
    write_csv(args.output / "UPDATES.csv", updates)
    write_csv(args.output / "FINAL_PAIRS.csv", final_rows)
    write_csv(args.output / "SOURCE_LABEL_NULLS.csv", null_rows)
    summary_path = args.output / "SUMMARY.json"
    verdict_path = args.output / "VERDICT.txt"
    summary_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    verdict_path.write_text(result["verdict"] + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": result["verdict"],
        "overall": {mode: result["overall"][mode] for mode in PRIMARY_MODES},
        "hard_pass_rules": result["hard_pass_rules"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
