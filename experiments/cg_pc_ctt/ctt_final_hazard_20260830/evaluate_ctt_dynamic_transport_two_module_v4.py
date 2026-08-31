#!/usr/bin/env python3
"""Final frozen M2 revision: exchangeable dynamic transport filtering.

The scientific contract is frozen in
``CTT_DYNAMIC_TRANSPORT_TWO_MODULE_V4_PREREGISTRATION_20260831.json``.
This program deliberately has three separate stages.  ``premise`` consumes
only simulated predictive counts.  ``stage1`` may consume measured tapes but
not native PMFS or truth and emits a hashable posterior artifact.  ``stage2``
opens native PMFS and truth only after the Stage-1 manifest is externally
anchored.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

import evaluate_ctt_coherent_block_partial_exchange_shadow as v3
import evaluate_ctt_crosshouse_measured_pmfs_shadow as v1
import evaluate_ctt_hierarchical_projection_v2 as v2


CONTRACT = "CTT_DYNAMIC_TRANSPORT_TWO_MODULE_V4"
PREMISE_PASS = "CTT_DYNAMIC_TRANSPORT_M2_PREMISE_PASS"
PREMISE_NO_GO = "CTT_DYNAMIC_TRANSPORT_M2_PREMISE_NO_GO"
PASS = "CTT_DYNAMIC_TRANSPORT_TWO_MODULE_V4_PASS_TO_NINE_PAIRED_CLOSED_LOOP"
NO_GO = "CTT_DYNAMIC_TRANSPORT_TWO_MODULE_V4_NO_GO"
INVALID = "CTT_DYNAMIC_TRANSPORT_TWO_MODULE_V4_INVALID"
MEMBERS = tuple(v1.PREDICTIVE_MEMBERS)
M = len(MEMBERS)
J = v1.SOURCE_UPDATES
TOL = 1.0e-12
CHANNELS = (
    "m1_causal_only",
    "dynamic_full",
    "time_shuffle",
    "iid_transport",
    "fixed_transport",
)
SCORE_KEYS = tuple(name + "_score" for name in CHANNELS)
CARRIER_KEYS = tuple(name + "_carrier" for name in CHANNELS)
ARRAY_KEYS = SCORE_KEYS + ("q0_carrier",) + CARRIER_KEYS


def sha256_file(path: Path) -> str:
    return v1.sha256_file(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"CTT_DYNAMIC_EMPTY_CSV:{path.name}")
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def canonical_array_sha256(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for item in arrays:
        value = np.asarray(item, dtype="<f8", order="C")
        digest.update(np.asarray(value.shape, dtype="<u8").tobytes())
        digest.update(value.tobytes())
    return digest.hexdigest()


def active_members(excluded_member: int | None = None) -> np.ndarray:
    return np.asarray(
        [member for member in MEMBERS if member != excluded_member], dtype=np.int64
    )


def estimate_persistence(
    tensors: dict[str, list[np.ndarray]], *, excluded_member: int | None = None
) -> tuple[float, dict[str, Any]]:
    """Estimate chance-corrected adjacent persistence from simulation only."""
    members = active_members(excluded_member)
    same_success = same_trials = cross_success = cross_trials = 0
    house_rows: dict[str, dict[str, int]] = {}
    for house in v1.HOUSES:
        if house not in tensors or len(tensors[house]) != len(v1.SEEDS):
            raise ValueError(f"CTT_DYNAMIC_RHO_HOUSE_DOMAIN_FAIL:{house}")
        hs = ht = hc = hx = 0
        for route, tensor in enumerate(tensors[house]):
            value = np.asarray(tensor, dtype=np.int64)
            if value.ndim != 3 or value.shape[1:] != (M, J):
                raise ValueError(
                    f"CTT_DYNAMIC_RHO_TENSOR_SHAPE_FAIL:{house}:{route}:{value.shape}"
                )
            for left_block in range(J - 1):
                right_block = left_block + 1
                for left in members:
                    a = value[:, left, left_block]
                    b = value[:, left, right_block]
                    hs += int(np.count_nonzero(a == b))
                    ht += len(a)
                    for right in members:
                        if right == left:
                            continue
                        c = value[:, right, right_block]
                        hc += int(np.count_nonzero(a == c))
                        hx += len(a)
        same_success += hs
        same_trials += ht
        cross_success += hc
        cross_trials += hx
        house_rows[house] = {
            "same_success": hs,
            "same_trials": ht,
            "cross_success": hc,
            "cross_trials": hx,
        }
    if min(same_trials, cross_trials) <= 0:
        raise ValueError("CTT_DYNAMIC_RHO_EMPTY_DOMAIN_FAIL")
    p_same = (same_success + 0.5) / (same_trials + 1.0)
    p_cross = (cross_success + 0.5) / (cross_trials + 1.0)
    if not (math.isfinite(p_same) and math.isfinite(p_cross)) or p_cross >= 1.0:
        raise ValueError("CTT_DYNAMIC_RHO_DENOMINATOR_FAIL")
    raw = (p_same - p_cross) / (1.0 - p_cross)
    rho = float(np.clip(raw, 0.0, 1.0))
    return rho, {
        "excluded_member": excluded_member,
        "active_members": members.tolist(),
        "same_success": same_success,
        "same_trials": same_trials,
        "cross_success": cross_success,
        "cross_trials": cross_trials,
        "p_same_jeffreys": p_same,
        "p_cross_jeffreys": p_cross,
        "rho_unclipped": raw,
        "rho": rho,
        "house_rows": house_rows,
        "measured_tape_native_pmfs_truth_localization_consumed": False,
    }


def transition_matrix(member_count: int, rho: float) -> np.ndarray:
    if member_count < 2 or not math.isfinite(rho) or not 0.0 <= rho <= 1.0:
        raise ValueError("CTT_DYNAMIC_TRANSITION_DOMAIN_FAIL")
    result = np.full(
        (member_count, member_count), (1.0 - rho) / member_count,
        dtype=np.float64,
    )
    result[np.diag_indices(member_count)] += rho
    if np.max(np.abs(result.sum(axis=1) - 1.0)) > TOL or np.any(result < 0.0):
        raise ValueError("CTT_DYNAMIC_TRANSITION_NORMALIZATION_FAIL")
    return result


def nonidentity_block_order(house: str, seed: int, visible: int) -> np.ndarray:
    if visible < 1 or visible > J:
        raise ValueError("CTT_DYNAMIC_TIME_SHUFFLE_PREFIX_FAIL")
    if visible == 1:
        return np.asarray([0], dtype=np.int64)
    token = hashlib.sha256(
        f"CTT-DYNAMIC-TIME-SHUFFLE|{house}|{seed}|{visible}".encode()
    ).digest()
    shift = 1 + int.from_bytes(token[:8], "little") % (visible - 1)
    order = np.roll(np.arange(visible, dtype=np.int64), shift)
    if np.array_equal(order, np.arange(visible)):
        raise ValueError("CTT_DYNAMIC_TIME_SHUFFLE_IDENTITY_FAIL")
    return order


def dynamic_log_score(
    candidate_counts: np.ndarray,
    observed_counts: np.ndarray,
    q: np.ndarray,
    visible: int,
    rho: float,
    *,
    members: np.ndarray | None = None,
    observed_order: np.ndarray | None = None,
) -> np.ndarray:
    """Exact finite-state likelihood, globally rescaled after each block."""
    candidate = np.asarray(candidate_counts, dtype=np.int64)
    observed = np.asarray(observed_counts, dtype=np.int64)
    matrix = np.asarray(q, dtype=np.float64)
    selected = active_members() if members is None else np.asarray(members, dtype=np.int64)
    if candidate.ndim != 3 or candidate.shape[1:] != (M, J):
        raise ValueError("CTT_DYNAMIC_SCORE_CANDIDATE_SHAPE_FAIL")
    if observed.shape != (J,) or not 1 <= visible <= J:
        raise ValueError("CTT_DYNAMIC_SCORE_OBSERVED_SHAPE_FAIL")
    if matrix.shape != (v3.BLOCK_STATES, v3.BLOCK_STATES) or np.any(matrix <= 0.0):
        raise ValueError("CTT_DYNAMIC_SCORE_Q_FAIL")
    order = (
        np.arange(visible, dtype=np.int64)
        if observed_order is None else np.asarray(observed_order, dtype=np.int64)
    )
    if order.shape != (visible,) or sorted(order.tolist()) != list(range(visible)):
        raise ValueError("CTT_DYNAMIC_SCORE_ORDER_FAIL")
    if selected.ndim != 1 or len(selected) < 2 or len(set(selected.tolist())) != len(selected):
        raise ValueError("CTT_DYNAMIC_SCORE_MEMBER_SET_FAIL")
    emission = matrix[
        candidate[:, selected, :visible], observed[order][None, None, :]
    ]
    alpha = emission[:, :, 0] / len(selected)
    log_scale = 0.0
    scale = float(np.max(alpha))
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("CTT_DYNAMIC_FORWARD_SCALE_FAIL")
    alpha /= scale
    log_scale += math.log(scale)
    for block in range(1, visible):
        propagated = rho * alpha + (1.0 - rho) * np.mean(
            alpha, axis=1, keepdims=True
        )
        alpha = emission[:, :, block] * propagated
        scale = float(np.max(alpha))
        if not math.isfinite(scale) or scale <= 0.0:
            raise ValueError("CTT_DYNAMIC_FORWARD_SCALE_FAIL")
        alpha /= scale
        log_scale += math.log(scale)
    likelihood = np.sum(alpha, axis=1)
    if np.any(likelihood <= 0.0) or not np.isfinite(likelihood).all():
        raise ValueError("CTT_DYNAMIC_FORWARD_LIKELIHOOD_FAIL")
    return np.log(likelihood) + log_scale


def m1_count_score_from_counts(
    candidate_counts: np.ndarray,
    observed_counts: np.ndarray,
    visible: int,
    *,
    members: np.ndarray,
) -> np.ndarray:
    """Exact V1 count-only statistic expressed through block counts."""
    candidate = np.asarray(candidate_counts, dtype=np.int64)
    observed = np.asarray(observed_counts, dtype=np.int64)
    n_members = len(members)
    stops = v3.BLOCK_SIZE * visible
    total_hits = np.sum(candidate[:, members, :visible], axis=(1, 2))
    pbar = (total_hits + v1.JEFFREYS * stops) / ((n_members + 2 * v1.JEFFREYS) * stops)
    reached = int(np.sum(observed[:visible]))
    return reached * np.log(pbar) + (stops - reached) * np.log1p(-pbar)


def normalized_diagonal_ranks(score: np.ndarray) -> np.ndarray:
    return v3.normalized_truth_ranks(np.asarray(score, dtype=np.float64))


def score_matrix(
    candidate: np.ndarray,
    heldout: int,
    q_minus: np.ndarray,
    rho_minus: float,
    arm: str,
    house: str,
    route: int,
) -> np.ndarray:
    members = active_members(heldout)
    observations = np.asarray(candidate[:, heldout, :], dtype=np.int64)
    rows = []
    for source, observed in enumerate(observations):
        if arm == "dynamic_full":
            score = dynamic_log_score(candidate, observed, q_minus, J, rho_minus, members=members)
        elif arm == "m1_causal_only":
            score = m1_count_score_from_counts(
                candidate, observed, J, members=members
            )
        elif arm == "time_shuffle":
            score = dynamic_log_score(
                candidate, observed, q_minus, J, rho_minus, members=members,
                observed_order=nonidentity_block_order(house, route, J),
            )
        elif arm == "iid_transport":
            score = dynamic_log_score(candidate, observed, q_minus, J, 0.0, members=members)
        elif arm == "fixed_transport":
            score = dynamic_log_score(candidate, observed, q_minus, J, 1.0, members=members)
        else:
            raise ValueError(f"CTT_DYNAMIC_UNKNOWN_ARM:{arm}")
        rows.append(score)
    return np.stack(rows)


def exact_sign_upper_p(wins: int, losses: int) -> float:
    return v3.exact_sign_upper_p(wins, losses)


def compare_rank_delta(rows: list[dict[str, Any]], comparator: str) -> dict[str, Any]:
    delta = np.asarray(
        [row[f"dynamic_minus_{comparator}"] for row in rows], dtype=np.float64
    )
    wins = int(np.count_nonzero(delta < -TOL))
    losses = int(np.count_nonzero(delta > TOL))
    ties = int(np.count_nonzero(np.abs(delta) <= TOL))
    return {
        "mean_dynamic_minus_comparator": float(np.mean(delta)),
        "median_dynamic_minus_comparator": float(np.median(delta)),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "one_sided_exact_sign_p": exact_sign_upper_p(wins, losses),
    }


def evaluate_premise(
    tensors: dict[str, list[np.ndarray]], prereg: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    fold_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    rank_matrices: list[dict[str, Any]] = []
    fold_parameters: dict[str, Any] = {}
    for heldout in MEMBERS:
        q_minus, q_counts, _ = v3.fit_global_lomo_q(
            tensors, excluded_member=heldout
        )
        rho_minus, rho_detail = estimate_persistence(
            tensors, excluded_member=heldout
        )
        fold_parameters[str(heldout)] = {
            "Q_and_counts_sha256": canonical_array_sha256(q_minus, q_counts),
            "rho": rho_minus,
            "rho_detail": rho_detail,
        }
        for house in v1.HOUSES:
            for route in v1.SEEDS:
                candidate = tensors[house][route]
                matrices = {
                    arm: score_matrix(
                        candidate, heldout, q_minus, rho_minus, arm, house, route
                    )
                    for arm in CHANNELS
                }
                ranks = {
                    arm: normalized_diagonal_ranks(matrix)
                    for arm, matrix in matrices.items()
                }
                rank_matrices.append({"house": house, "dynamic": v3.all_candidate_normalized_ranks(matrices["dynamic_full"])})
                for source in range(candidate.shape[0]):
                    source_rows.append({
                        "house": house,
                        "route_index": route,
                        "heldout_member": heldout,
                        "source_index": source,
                        **{f"{arm}_normalized_true_source_rank": float(ranks[arm][source]) for arm in CHANNELS},
                    })
                means = {arm: float(np.mean(value)) for arm, value in ranks.items()}
                fold_rows.append({
                    "house": house,
                    "route_index": route,
                    "heldout_member": heldout,
                    "sources": candidate.shape[0],
                    "rho_minus_heldout": rho_minus,
                    **{f"{arm}_mean_normalized_true_source_rank": value for arm, value in means.items()},
                    **{f"dynamic_minus_{arm}": means["dynamic_full"] - means[arm] for arm in CHANNELS if arm != "dynamic_full"},
                })
    if len(fold_rows) != 240:
        raise ValueError(f"CTT_DYNAMIC_PREMISE_FOLD_COUNT_FAIL:{len(fold_rows)}")
    route_rows: list[dict[str, Any]] = []
    for house in v1.HOUSES:
        for route in v1.SEEDS:
            subset = [row for row in fold_rows if row["house"] == house and row["route_index"] == route]
            if len(subset) != M:
                raise ValueError("CTT_DYNAMIC_PREMISE_ROUTE_FOLD_FAIL")
            route_rows.append({
                "house": house,
                "route_index": route,
                **{
                    f"dynamic_minus_{arm}": float(np.mean([row[f"dynamic_minus_{arm}"] for row in subset]))
                    for arm in CHANNELS if arm != "dynamic_full"
                },
                **{
                    f"{arm}_mean_normalized_true_source_rank": float(np.mean([row[f"{arm}_mean_normalized_true_source_rank"] for row in subset]))
                    for arm in CHANNELS
                },
            })
    observed_mean = float(np.mean([
        row["dynamic_full_mean_normalized_true_source_rank"] for row in fold_rows
    ]))
    null_rows: list[dict[str, Any]] = []
    for replicate in range(v1.NULL_REPLICATES):
        label_maps = {
            house: v2.uniform_permutation(
                tensors[house][0].shape[0],
                f"CTT-DYNAMIC-PREMISE-SOURCE-NULL|{house}|{replicate}",
            ) for house in v1.HOUSES
        }
        values = []
        for item in rank_matrices:
            rank = item["dynamic"]
            labels = label_maps[item["house"]]
            values.append(float(np.mean(rank[np.arange(len(labels)), labels])))
        null_rows.append({
            "replicate": replicate,
            "mean_normalized_true_source_rank": float(np.mean(values)),
        })
    source_p = float((1 + np.count_nonzero(
        np.asarray([row["mean_normalized_true_source_rank"] for row in null_rows])
        <= observed_mean
    )) / (v1.NULL_REPLICATES + 1))
    comparisons = {
        arm: compare_rank_delta(route_rows, arm)
        for arm in CHANNELS if arm != "dynamic_full"
    }
    house_directions = {
        house: {
            arm: float(np.mean([
                row[f"dynamic_minus_{arm}"] for row in route_rows if row["house"] == house
            ]))
            for arm in CHANNELS if arm != "dynamic_full"
        } for house in v1.HOUSES
    }
    rules = prereg["premise_gate"]["hard_rules"]
    hard = {
        "route_clusters_exactly": len(route_rows) == int(rules["route_clusters_exactly"]),
        "dynamic_source_label_empirical_p": source_p <= float(rules["dynamic_source_label_empirical_p_at_most"]),
        **{
            f"dynamic_vs_{arm}_exact_sign_p": comparisons[arm]["one_sided_exact_sign_p"]
            <= float(rules[f"dynamic_vs_{'M1' if arm == 'm1_causal_only' else arm.replace('_transport','')}_route_exact_sign_p_at_most"])
            for arm in CHANNELS if arm != "dynamic_full"
        },
        "each_house_no_comparator_reversal": all(
            value <= TOL for mapping in house_directions.values() for value in mapping.values()
        ),
    }
    summary = {
        "verdict": PREMISE_PASS if all(hard.values()) else PREMISE_NO_GO,
        "dynamic_mean_normalized_true_source_rank": observed_mean,
        "source_label_empirical_p": source_p,
        "comparisons": comparisons,
        "house_directions": house_directions,
        "hard_pass_rules": hard,
        "fold_parameters": fold_parameters,
        "independent_route_clusters": len(route_rows),
        "diagnostic_member_LOO_folds": len(fold_rows),
    }
    return fold_rows, route_rows, source_rows, null_rows, summary


def semantic_digest(records: list[dict[str, Any]], rho: float, q: np.ndarray) -> str:
    digest = hashlib.sha256(canonical_array_sha256(np.asarray([rho]), q).encode())
    for row in sorted(records, key=lambda x: (x["house"], x["seed"], x["update_id"])):
        digest.update(f"{row['house']}|{row['seed']}|{row['update_id']}".encode())
        digest.update(json.dumps(row["historical_run_input_hashes"], sort_keys=True).encode())
        for key in ARRAY_KEYS:
            digest.update(np.asarray(row[key], dtype="<f8").tobytes())
    return digest.hexdigest()


def evaluate_stage1(
    bank_root: Path,
    historical_root: Path,
    manifest: list[dict[str, str]],
    schedules: dict[str, list[dict[str, Any]]],
    support_all: dict[str, dict[str, Any]],
    tensors: dict[str, list[np.ndarray]],
    train_events: dict[str, list[np.ndarray]],
    q: np.ndarray,
    rho: float,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for house in v1.HOUSES:
        q0 = np.asarray(support_all[house]["q0"], dtype=np.float64)
        for seed in v1.SEEDS:
            observed = v1.load_observed_case(
                historical_root, house, seed, schedules[house][seed]
            )
            observed_counts = v3.observed_block_counts(
                observed["observed_events"], schedules[house][seed]["authorized"]["blocks"]
            )
            candidate = tensors[house][seed]
            events = train_events[house][seed]
            exact_matches = sum(
                int(np.array_equal(events[source, member], observed["observed_events"]))
                for source in range(events.shape[0]) for member in MEMBERS
            )
            for update, (timing, visible) in enumerate(
                zip(observed["timing"], observed["visible"]), start=1
            ):
                expected = schedules[house][seed]["authorized"]["prefixes"][update - 1]
                if not np.array_equal(np.asarray(visible, dtype=np.int64), expected):
                    raise ValueError("CTT_DYNAMIC_VISIBLE_PREFIX_FAIL")
                order = nonidentity_block_order(house, seed, update)
                scores = {
                    "dynamic_full": dynamic_log_score(candidate, observed_counts, q, update, rho),
                    "time_shuffle": dynamic_log_score(candidate, observed_counts, q, update, rho, observed_order=order),
                    "iid_transport": dynamic_log_score(candidate, observed_counts, q, update, 0.0),
                    "fixed_transport": dynamic_log_score(candidate, observed_counts, q, update, 1.0),
                    "m1_causal_only": v1.count_only_score(
                        events, observed["observed_events"], np.asarray(visible)
                    ),
                }
                carriers = {
                    name: v1.stable_softmax(np.log(q0) + score)
                    for name, score in scores.items()
                }
                records.append({
                    "house": house,
                    "seed": int(seed),
                    "update_id": update,
                    "update_time_s": float(timing["sim_time"]),
                    "visible_stops": np.asarray(visible, dtype=np.int64),
                    "visible_blocks": update,
                    "observed_hit_stops": int(np.sum(observed["observed_events"][visible])),
                    "observed_block_counts": observed_counts[:update].copy(),
                    "time_shuffle_order": order,
                    "historical_measured_tape_exact_train_member_matches": exact_matches,
                    "timing": timing,
                    "historical_run_input_hashes": dict(observed["hashes"]),
                    "q0_carrier": q0,
                    **{f"{name}_score": score for name, score in scores.items()},
                    **{f"{name}_carrier": value for name, value in carriers.items()},
                })
    if len(records) != 150:
        raise ValueError(f"CTT_DYNAMIC_STAGE1_COUNT_FAIL:{len(records)}")
    return records


def write_stage1(
    output: Path,
    records: list[dict[str, Any]],
    q: np.ndarray,
    q_counts: np.ndarray,
    rho: float,
    rho_detail: dict[str, Any],
    prereg_path: Path,
    evaluator_path: Path,
    freeze: dict[str, Any],
) -> dict[str, Any]:
    arrays: dict[str, np.ndarray] = {
        "GLOBAL_Q": q,
        "GLOBAL_Q_COUNTS": q_counts,
        "RHO": np.asarray([rho]),
    }
    metadata: list[dict[str, Any]] = []
    for house in v1.HOUSES:
        subset = [row for row in records if row["house"] == house]
        for key in ARRAY_KEYS:
            arrays[f"{house}_{key}"] = np.stack([row[key] for row in subset])
        for local_index, row in enumerate(subset):
            metadata.append({
                "house": house,
                "local_index": local_index,
                "seed": row["seed"],
                "update_id": row["update_id"],
                "update_time_s": row["update_time_s"],
                "visible_stops": row["visible_stops"].tolist(),
                "visible_blocks": row["visible_blocks"],
                "observed_hit_stops": row["observed_hit_stops"],
                "observed_block_counts": row["observed_block_counts"].tolist(),
                "time_shuffle_order": row["time_shuffle_order"].tolist(),
                "historical_measured_tape_exact_train_member_matches": row["historical_measured_tape_exact_train_member_matches"],
                "timing": row["timing"],
                "historical_run_input_hashes": row["historical_run_input_hashes"],
            })
    artifact = output / "DYNAMIC_METHOD_POSTERIORS.npz"
    np.savez_compressed(artifact, **arrays)
    manifest = {
        "contract": CONTRACT + "_STAGE1",
        "status": "ALL_150_DYNAMIC_POSTERIORS_FROZEN_BEFORE_NATIVE_OR_TRUTH_READ",
        "records": len(records),
        "artifact_sha256": sha256_file(artifact),
        "semantic_sha256": semantic_digest(records, rho, q),
        "preregistration_sha256": sha256_file(prereg_path),
        "evaluator_sha256": sha256_file(evaluator_path),
        "input_freeze_sha256": sha256_file(output / "INPUT_FREEZE.json"),
        "Q_sha256": canonical_array_sha256(q, q_counts),
        "rho": rho,
        "rho_detail": rho_detail,
        "array_keys": list(ARRAY_KEYS),
        "metadata": metadata,
        "predictive_input_freeze": freeze,
    }
    path = output / "STAGE1_MANIFEST.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def load_stage1(
    root: Path,
    expected_manifest_sha: str,
    prereg_path: Path,
    evaluator_path: Path,
) -> tuple[list[dict[str, Any]], float, np.ndarray, dict[str, Any]]:
    manifest_path = root / "STAGE1_MANIFEST.json"
    artifact = root / "DYNAMIC_METHOD_POSTERIORS.npz"
    if sha256_file(manifest_path) != expected_manifest_sha:
        raise SystemExit("CTT_DYNAMIC_STAGE1_EXTERNAL_ANCHOR_FAIL")
    manifest = read_json(manifest_path)
    if (
        manifest.get("contract") != CONTRACT + "_STAGE1"
        or manifest.get("records") != 150
        or manifest.get("artifact_sha256") != sha256_file(artifact)
        or manifest.get("preregistration_sha256") != sha256_file(prereg_path)
        or manifest.get("evaluator_sha256") != sha256_file(evaluator_path)
    ):
        raise SystemExit("CTT_DYNAMIC_STAGE1_MANIFEST_FAIL")
    records: list[dict[str, Any]] = []
    with np.load(artifact, allow_pickle=False) as archive:
        expected = {"GLOBAL_Q", "GLOBAL_Q_COUNTS", "RHO"} | {
            f"{house}_{key}" for house in v1.HOUSES for key in ARRAY_KEYS
        }
        if set(archive.files) != expected:
            raise SystemExit("CTT_DYNAMIC_STAGE1_ARRAY_SET_FAIL")
        q = np.asarray(archive["GLOBAL_Q"], dtype=np.float64)
        rho = float(np.asarray(archive["RHO"])[0])
        for item in manifest["metadata"]:
            row = {key: value for key, value in item.items() if key != "local_index"}
            index = int(item["local_index"])
            for key in ARRAY_KEYS:
                row[key] = np.asarray(archive[f"{item['house']}_{key}"][index], dtype=np.float64)
            records.append(row)
    if semantic_digest(records, rho, q) != manifest["semantic_sha256"]:
        raise SystemExit("CTT_DYNAMIC_STAGE1_SEMANTIC_FAIL")
    return records, rho, q, manifest


def project_arms(
    record: dict[str, Any], mapping: dict[str, Any]
) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    native_cell = mapping["native_cell"]
    native_carrier = mapping["native_carrier"]
    labels = mapping["cell_to_source"]
    targets = {
        "identity_reconstruction": native_carrier,
        **{name: np.asarray(record[f"{name}_carrier"]) for name in CHANNELS},
    }
    projected = {
        name: v2.hierarchical_project(target, native_cell, labels, label=name)
        for name, target in targets.items()
    }
    invariants = {
        name: v2.projection_invariants(targets[name], projected[name], native_cell, labels)
        for name in targets
    }
    maxima = {
        "identity_reconstruction_max_abs": float(np.max(np.abs(
            projected["identity_reconstruction"]["cell"] - native_cell
        ))),
        "carrier_marginal_max_abs": max(
            float(item["carrier_marginal_max_abs"]) for item in invariants.values()
        ),
        "within_carrier_conditional_max_abs": max(
            float(item["within_carrier_conditional_max_abs"]) for item in invariants.values()
        ),
        "total_mass_max_abs": max(
            float(item["total_mass_abs"]) for item in invariants.values()
        ),
        "fail_closed_native_max_abs": max(
            float(item["fail_closed_native_max_abs"]) for item in invariants.values()
        ),
        "cell_row_permutation_max_abs_after_restore": max(
            v2.row_permutation_projection_max_abs(target, native_cell, labels)
            for target in targets.values()
        ),
    }
    return {name: projected[name]["cell"] for name in CHANNELS}, maxima


def evaluate_stage2(
    records: list[dict[str, Any]],
    historical_root: Path,
    support_all: dict[str, dict[str, Any]],
    frozen_v2: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    finals: list[dict[str, Any]] = []
    cases: dict[tuple[str, int], tuple[dict[str, Any], str]] = {}
    native_hashes: dict[str, str] = {}
    max_inv = {key: 0.0 for key in v2.PROJECTION_INVARIANT_KEYS}
    max_inv["native_final_endpoint_parity_max_abs_m"] = 0.0
    exact_matches = 0
    for record in records:
        house, seed, update = record["house"], int(record["seed"]), int(record["update_id"])
        support = support_all[house]
        runtime = v1.runtime_root(historical_root, house, seed)
        native_path = runtime / "context_bank" / f"source_update_{update:04d}" / "source_posterior.csv"
        native_rows = v1.read_csv(native_path)
        native_hashes[f"{house}_seed{seed}_update{update}"] = sha256_file(native_path)
        mapping = v1.map_native_cells(native_rows, record["timing"], support)
        cells, inv = project_arms(record, mapping)
        for key, value in inv.items():
            max_inv[key] = max(max_inv[key], value)
        if update == 1:
            exact_matches += int(record["historical_measured_tape_exact_train_member_matches"])
        key = (house, seed)
        if key not in cases:
            cases[key] = v2._case_result(historical_root, house, seed)
        case, case_sha = cases[key]
        truth_xy = tuple(float(value) for value in case["truth_eval_only"])
        truth_source, truth_cell = v1.true_support_indices(
            truth_xy, record["timing"], native_rows, mapping, support
        )
        endpoints: dict[str, dict[str, float]] = {}
        for channel, mass in {"native": mapping["native_cell"], **cells}.items():
            for mode in v2.ALL_MODES:
                endpoints[f"{channel}_{mode}"] = v1.endpoint(
                    native_rows, mass, truth_xy, tie_mode=mode
                )
        row: dict[str, Any] = {
            "house": house,
            "seed": seed,
            "source_update_id": update,
            "source_update_time_s": float(record["update_time_s"]),
            "visible_physical_stops": len(record["visible_stops"]),
            "visible_blocks": int(record["visible_blocks"]),
            "observed_hit_stops": int(record["observed_hit_stops"]),
            "truth_carrier_index": truth_source,
            "truth_carrier_id": support["carriers"][truth_source],
            "native_true_cell_rank": v1.rank_desc(mapping["native_cell"], truth_cell),
            **{key: float(value) for key, value in inv.items()},
        }
        for channel in ("native",) + CHANNELS:
            for mode in v2.ALL_MODES:
                endpoint = endpoints[f"{channel}_{mode}"]
                row[f"{channel}_{mode}_error_m"] = endpoint["error_m"]
                row[f"{channel}_{mode}_variance_m2"] = endpoint["variance_m2"]
                row[f"{channel}_{mode}_selected_variance_m2"] = endpoint["selected_variance_m2"]
        updates.append(row)
        if update == J:
            parity = abs(endpoints["native_ascending"]["error_m"] - float(case["primary_error_m"]))
            max_inv["native_final_endpoint_parity_max_abs_m"] = max(
                max_inv["native_final_endpoint_parity_max_abs_m"], parity
            )
            finals.append(row)
    current_cases = {f"{h}_seed{s}": digest for (h, s), (_, digest) in cases.items()}
    if native_hashes != frozen_v2.get("native_source_posterior_sha256", {}):
        raise ValueError("CTT_DYNAMIC_NATIVE_HASH_SET_FAIL")
    if current_cases != frozen_v2.get("case_result_sha256", {}):
        raise ValueError("CTT_DYNAMIC_CASE_HASH_SET_FAIL")
    if len(updates) != 150 or len(finals) != 30:
        raise ValueError("CTT_DYNAMIC_STAGE2_COUNT_FAIL")
    return updates, finals, {
        "invariant_maxima": max_inv,
        "historical_measured_tape_exact_train_member_matches": exact_matches,
        "native_source_posterior_sha256": native_hashes,
        "case_result_sha256": current_cases,
    }


def metrics(rows: list[dict[str, Any]], mode: str, channel: str) -> dict[str, Any]:
    result = v2._metrics(rows, mode, channel)
    native = np.asarray([row[f"native_{mode}_error_m"] for row in rows])
    method = np.asarray([row[f"{channel}_{mode}_error_m"] for row in rows])
    result.update({
        "native_median_error_m": float(np.median(native)),
        "method_median_error_m": float(np.median(method)),
        "mean_paired_delta_m": float(np.mean(method - native)),
        "median_paired_delta_m": float(np.median(method - native)),
    })
    return result


def paired_comparison(
    rows: list[dict[str, Any]], mode: str, comparator: str
) -> dict[str, Any]:
    delta = np.asarray([
        row[f"dynamic_full_{mode}_error_m"] - row[f"{comparator}_{mode}_error_m"]
        for row in rows
    ])
    wins = int(np.count_nonzero(delta < -TOL))
    losses = int(np.count_nonzero(delta > TOL))
    ties = int(np.count_nonzero(np.abs(delta) <= TOL))
    return {
        "paired_runs": len(delta),
        "dynamic_total_error_m": float(np.sum([
            row[f"dynamic_full_{mode}_error_m"] for row in rows
        ])),
        "comparator_total_error_m": float(np.sum([
            row[f"{comparator}_{mode}_error_m"] for row in rows
        ])),
        "mean_dynamic_minus_comparator_m": float(np.mean(delta)),
        "median_dynamic_minus_comparator_m": float(np.median(delta)),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "one_sided_exact_sign_p": exact_sign_upper_p(wins, losses),
    }


def aggregate(
    updates: list[dict[str, Any]],
    finals: list[dict[str, Any]],
    diagnostics: dict[str, Any],
    prereg: dict[str, Any],
) -> dict[str, Any]:
    overall = {
        channel: {mode: metrics(finals, mode, channel) for mode in v2.ALL_MODES}
        for channel in CHANNELS
    }
    by_house = {
        house: {
            channel: {
                mode: metrics([row for row in finals if row["house"] == house], mode, channel)
                for mode in v2.ALL_MODES
            } for channel in CHANNELS
        } for house in v1.HOUSES
    }
    comparators = tuple(name for name in CHANNELS if name != "dynamic_full")
    paired = {
        comparator: {
            mode: paired_comparison(finals, mode, comparator)
            for mode in v2.PRIMARY_MODES
        } for comparator in comparators
    }
    rules = prereg["measured_fixed_trajectory_gate"]["hard_rules"]
    dyn = overall["dynamic_full"]
    hard = {
        "valid_updates_exactly": len(updates) == int(rules["valid_updates_exactly"]),
        "valid_final_pairs_exactly": len(finals) == int(rules["valid_final_pairs_exactly"]),
        "pooled_improvement_each_primary": min(dyn[mode]["pooled_relative_improvement"] for mode in v2.PRIMARY_MODES)
        >= float(rules["pooled_relative_improvement_vs_PMFS_each_primary_at_least"]),
        "improved_pairs_each_primary": min(dyn[mode]["improved_pairs"] for mode in v2.PRIMARY_MODES)
        >= int(rules["improved_pairs_vs_PMFS_each_primary_at_least"]),
        "each_house_pooled_each_primary": min(
            by_house[house]["dynamic_full"][mode]["pooled_relative_improvement"]
            for house in v1.HOUSES for mode in v2.PRIMARY_MODES
        ) >= float(rules["each_House_pooled_relative_improvement_each_primary_at_least"]),
        "zero_catastrophes_each_primary": max(dyn[mode]["catastrophic_regressions"] for mode in v2.PRIMARY_MODES)
        <= int(rules["catastrophic_regressions_each_primary_at_most"]),
        "zero_new_false_confident_collapses_each_primary": max(dyn[mode]["new_false_confident_collapses"] for mode in v2.PRIMARY_MODES)
        <= int(rules["new_false_confident_collapses_each_primary_at_most"]),
        "dynamic_total_strictly_lower_all_controls_each_primary": all(
            paired[control][mode]["dynamic_total_error_m"]
            < paired[control][mode]["comparator_total_error_m"] - TOL
            for control in comparators for mode in v2.PRIMARY_MODES
        ),
        "dynamic_exact_sign_p_all_controls_each_primary": all(
            paired[control][mode]["one_sided_exact_sign_p"]
            <= float(rules["dynamic_vs_M1_time_shuffle_iid_fixed_one_sided_exact_sign_p_each_primary_at_most"])
            for control in comparators for mode in v2.PRIMARY_MODES
        ),
        "projection_invariants": max(
            diagnostics["invariant_maxima"].get(key, 0.0)
            for key in v2.PROJECTION_INVARIANT_KEYS
        ) <= TOL and diagnostics["invariant_maxima"]["native_final_endpoint_parity_max_abs_m"] <= TOL,
        "no_exact_train_member_matches": diagnostics["historical_measured_tape_exact_train_member_matches"] == 0,
    }
    return {
        "verdict": PASS if all(hard.values()) else NO_GO,
        "hard_pass_rules": hard,
        "overall": overall,
        "by_house": by_house,
        "paired_incremental_evidence": paired,
        **diagnostics,
    }


def selftest() -> None:
    rng = np.random.default_rng(20260831)
    tensors = {
        house: [rng.integers(0, 4, size=(5, M, J)) for _ in v1.SEEDS]
        for house in v1.HOUSES
    }
    rho, detail = estimate_persistence(tensors)
    assert 0.0 <= rho <= 1.0 and detail["measured_tape_native_pmfs_truth_localization_consumed"] is False
    perm = rng.permutation(M)
    permuted = {house: [value[:, perm, :] for value in rows] for house, rows in tensors.items()}
    rho_perm, _ = estimate_persistence(permuted)
    assert abs(rho - rho_perm) <= TOL
    excluded = 3
    rho_excluded, _ = estimate_persistence(tensors, excluded_member=excluded)
    contaminated = {
        house: [value.copy() for value in rows] for house, rows in tensors.items()
    }
    for rows in contaminated.values():
        for value in rows:
            value[:, excluded, :] = rng.integers(0, 4, size=value[:, excluded, :].shape)
    rho_contaminated, _ = estimate_persistence(
        contaminated, excluded_member=excluded
    )
    assert abs(rho_excluded - rho_contaminated) <= TOL
    candidate = rng.integers(0, 4, size=(6, M, J))
    observed = rng.integers(0, 4, size=J)
    q = rng.random((4, 4)) + 0.1
    q /= q.sum(axis=1, keepdims=True)
    iid = dynamic_log_score(candidate, observed, q, J, 0.0)
    fixed = dynamic_log_score(candidate, observed, q, J, 1.0)
    assert np.max(np.abs(iid - v3.incoherent_per_block_score(candidate, observed, q, J))) <= 1e-11
    assert np.max(np.abs(fixed - v3.coherent_cbpe_score(candidate, observed, q, J))) <= 1e-11
    # The block-count expression for M1 is exactly the frozen event-level
    # count-only score; within-block ordering is irrelevant to this control.
    events = np.zeros((candidate.shape[0], M, J * v3.BLOCK_SIZE), dtype=np.bool_)
    for source in range(candidate.shape[0]):
        for member in range(M):
            for block in range(J):
                start = block * v3.BLOCK_SIZE
                events[source, member, start:start + candidate[source, member, block]] = True
    observed_events = np.zeros(J * v3.BLOCK_SIZE, dtype=np.bool_)
    for block in range(J):
        start = block * v3.BLOCK_SIZE
        observed_events[start:start + observed[block]] = True
    count_from_blocks = m1_count_score_from_counts(
        candidate, observed, J, members=active_members()
    )
    count_from_events = v1.count_only_score(
        events, observed_events, np.arange(J * v3.BLOCK_SIZE)
    )
    assert np.max(np.abs(count_from_blocks - count_from_events)) <= 1e-11
    test_rho = 0.37
    forward = dynamic_log_score(candidate[:2], observed, q, J, test_rho)
    A = transition_matrix(M, test_rho)
    brute = []
    for source in range(2):
        total = 0.0
        for states in itertools.product(range(M), repeat=J):
            probability = 1.0 / M
            probability *= q[candidate[source, states[0], 0], observed[0]]
            for block in range(1, J):
                probability *= A[states[block - 1], states[block]]
                probability *= q[candidate[source, states[block], block], observed[block]]
            total += probability
        brute.append(math.log(total))
    assert np.max(np.abs(forward - np.asarray(brute))) <= 1e-11
    for visible in range(2, J + 1):
        order = nonidentity_block_order("House01", 0, visible)
        assert not np.array_equal(order, np.arange(visible))
    # Online prefix recomputation is the exact batch recursion at each prefix.
    prefix = [dynamic_log_score(candidate, observed, q, visible, test_rho) for visible in range(1, J + 1)]
    assert all(np.isfinite(value).all() for value in prefix)
    # A simultaneous member relabeling cannot change the result.
    relabeled = candidate[:, perm, :]
    assert np.max(np.abs(
        dynamic_log_score(candidate, observed, q, J, test_rho)
        - dynamic_log_score(relabeled, observed, q, J, test_rho)
    )) <= 1e-11
    native = np.asarray([0.1, 0.2, 0.3, 0.4])
    mapping = {
        "native_cell": native,
        "native_carrier": np.asarray([0.3, 0.7]),
        "cell_to_source": np.asarray([0, 0, 1, 1]),
    }
    synthetic_record = {
        f"{name}_carrier": np.asarray([0.6, 0.4]) for name in CHANNELS
    }
    cells, invariants = project_arms(synthetic_record, mapping)
    assert set(cells) == set(CHANNELS)
    assert max(invariants.values()) <= TOL
    print("CTT_DYNAMIC_TRANSPORT_TWO_MODULE_V4_SELFTEST=PASS")


def verify_prereg(path: Path) -> dict[str, Any]:
    prereg = read_json(path)
    if (
        prereg.get("contract") != CONTRACT
        or prereg.get("status") != "FROZEN_BEFORE_V4_PREDICTIVE_OR_MEASURED_RESULT_READ"
        or prereg.get("transition_model", {}).get("free_parameters") != 0
    ):
        raise SystemExit("CTT_DYNAMIC_PREREGISTRATION_FAIL")
    dependencies = prereg["frozen_dependencies"]
    current = {
        "v3_evaluator_sha256": sha256_file(Path(v3.__file__)),
        "v1_evaluator_sha256": sha256_file(Path(v1.__file__)),
        "v2_projection_sha256": sha256_file(Path(v2.__file__)),
        "causal_gate_sha256": sha256_file(Path(v3.causal_gate.__file__)),
    }
    if any(dependencies[key] != value for key, value in current.items()):
        raise SystemExit("CTT_DYNAMIC_FROZEN_DEPENDENCY_HASH_FAIL")
    return prereg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--stage", choices=("premise", "1", "2"))
    parser.add_argument("--bank-root", type=Path)
    parser.add_argument("--historical-root", type=Path)
    parser.add_argument("--source-support", type=Path)
    parser.add_argument("--causal-premise-verdict", type=Path)
    parser.add_argument("--causal-premise-summary", type=Path)
    parser.add_argument("--v3-preregistration", type=Path)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--premise-root", type=Path)
    parser.add_argument("--premise-summary-sha256")
    parser.add_argument("--premise-verdict-sha256")
    parser.add_argument("--stage1-root", type=Path)
    parser.add_argument("--stage1-manifest-sha256")
    parser.add_argument("--frozen-v2-summary", type=Path)
    parser.add_argument("--v3-summary", type=Path)
    parser.add_argument("--v3-verdict", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    required = (
        args.stage, args.historical_root, args.source_support,
        args.v3_preregistration, args.preregistration, args.v3_summary,
        args.v3_verdict, args.output,
    )
    if any(value is None for value in required):
        raise SystemExit("CTT_DYNAMIC_REQUIRED_ARGUMENT_MISSING")
    if args.output.exists():
        raise SystemExit(f"CTT_DYNAMIC_REFUSE_OVERWRITE:{args.output}")
    prereg = verify_prereg(args.preregistration)
    if (
        sha256_file(args.v3_summary) != prereg["preserved_results"]["v3_summary_sha256"]
        or sha256_file(args.v3_verdict) != prereg["preserved_results"]["v3_verdict_sha256"]
        or args.v3_verdict.read_text(encoding="utf-8").strip() != v3.NO_GO
    ):
        raise SystemExit("CTT_DYNAMIC_V3_NEGATIVE_EVIDENCE_PRESERVATION_FAIL")
    v3_prereg = read_json(args.v3_preregistration)
    if args.stage in ("premise", "1"):
        if any(value is None for value in (
            args.bank_root, args.causal_premise_verdict, args.causal_premise_summary
        )):
            raise SystemExit("CTT_DYNAMIC_PREDICTIVE_ARGUMENT_FAIL")
        _, manifest, schedules, freeze = v3.validate_predictive_inputs(
            args.bank_root, args.historical_root, args.source_support,
            args.causal_premise_verdict, args.causal_premise_summary, v3_prereg,
        )
        support_all = v1.load_support(args.source_support)
        tensors, train_events, verified_shards = v3.materialize_predictive_counts(
            args.bank_root, manifest, schedules, support_all
        )
        q, q_counts, q_domain = v3.fit_global_lomo_q(tensors)
        rho, rho_detail = estimate_persistence(tensors)
        freeze.update({
            "contract": CONTRACT + "_PREDICTIVE_INPUT_FREEZE",
            "preregistration_sha256": sha256_file(args.preregistration),
            "evaluator_sha256": sha256_file(Path(__file__)),
            "verified_training_shards": verified_shards,
            "Q_sha256": canonical_array_sha256(q, q_counts),
            "Q_domain": q_domain,
            "rho": rho,
            "rho_detail": rho_detail,
            "v3_summary_sha256": sha256_file(args.v3_summary),
            "v3_verdict_sha256": sha256_file(args.v3_verdict),
        })
        args.output.mkdir(parents=True)
        freeze_path = args.output / "INPUT_FREEZE.json"
        freeze_path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.stage == "premise":
            folds, routes, sources, nulls, summary = evaluate_premise(tensors, prereg)
            summary["global_rho"] = rho
            summary["global_rho_detail"] = rho_detail
            summary["input_hashes"] = {
                "preregistration": sha256_file(args.preregistration),
                "evaluator": sha256_file(Path(__file__)),
                "input_freeze": sha256_file(freeze_path),
            }
            write_csv(args.output / "PREMISE_FOLDS.csv", folds)
            write_csv(args.output / "PREMISE_ROUTE_CLUSTERS.csv", routes)
            write_csv(args.output / "PREMISE_SOURCE_RANKS.csv", sources)
            write_csv(args.output / "SOURCE_LABEL_NULLS.csv", nulls)
            (args.output / "PREMISE_SUMMARY.json").write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            (args.output / "PREMISE_VERDICT.txt").write_text(summary["verdict"] + "\n", encoding="utf-8")
            print(json.dumps(summary, indent=2), flush=True)
            return 0
        if any(value is None for value in (
            args.premise_root, args.premise_summary_sha256, args.premise_verdict_sha256
        )):
            raise SystemExit("CTT_DYNAMIC_STAGE1_PREMISE_ARGUMENT_FAIL")
        premise_summary = args.premise_root / "PREMISE_SUMMARY.json"
        premise_verdict = args.premise_root / "PREMISE_VERDICT.txt"
        premise = read_json(premise_summary)
        if (
            sha256_file(premise_summary) != args.premise_summary_sha256
            or sha256_file(premise_verdict) != args.premise_verdict_sha256
            or premise.get("verdict") != PREMISE_PASS
            or not all(premise.get("hard_pass_rules", {}).values())
            or premise.get("input_hashes", {}).get("evaluator") != sha256_file(Path(__file__))
            or abs(float(premise.get("global_rho", -1)) - rho) > TOL
        ):
            raise SystemExit("CTT_DYNAMIC_STAGE1_PREMISE_PASS_HASH_FAIL")
        freeze["premise_summary_sha256"] = sha256_file(premise_summary)
        freeze["premise_verdict_sha256"] = sha256_file(premise_verdict)
        freeze_path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        records = evaluate_stage1(
            args.bank_root, args.historical_root, manifest, schedules,
            support_all, tensors, train_events, q, rho,
        )
        stage1 = write_stage1(
            args.output, records, q, q_counts, rho, rho_detail,
            args.preregistration, Path(__file__), freeze,
        )
        print(json.dumps({
            "stage": 1,
            "records": stage1["records"],
            "rho": rho,
            "artifact_sha256": stage1["artifact_sha256"],
            "manifest_sha256": sha256_file(args.output / "STAGE1_MANIFEST.json"),
        }, indent=2), flush=True)
        return 0
    if any(value is None for value in (
        args.stage1_root, args.stage1_manifest_sha256, args.frozen_v2_summary,
        args.premise_root, args.premise_summary_sha256, args.premise_verdict_sha256,
    )) or args.bank_root is not None:
        raise SystemExit("CTT_DYNAMIC_STAGE2_ARGUMENT_FAIL")
    premise_summary = args.premise_root / "PREMISE_SUMMARY.json"
    premise_verdict = args.premise_root / "PREMISE_VERDICT.txt"
    if (
        sha256_file(premise_summary) != args.premise_summary_sha256
        or sha256_file(premise_verdict) != args.premise_verdict_sha256
        or premise_verdict.read_text(encoding="utf-8").strip() != PREMISE_PASS
    ):
        raise SystemExit("CTT_DYNAMIC_STAGE2_PREMISE_HASH_FAIL")
    records, rho, q, stage1 = load_stage1(
        args.stage1_root, args.stage1_manifest_sha256,
        args.preregistration, Path(__file__),
    )
    if sha256_file(args.frozen_v2_summary) != v3_prereg[
        "preserved_negative_dependencies"
    ]["v2_summary_sha256"]:
        raise SystemExit("CTT_DYNAMIC_FROZEN_V2_SUMMARY_HASH_FAIL")
    frozen_v2 = read_json(args.frozen_v2_summary)
    support_all = v1.load_support(args.source_support)
    args.output.mkdir(parents=True)
    try:
        updates, finals, diagnostics = evaluate_stage2(
            records, args.historical_root, support_all, frozen_v2
        )
        result = aggregate(updates, finals, diagnostics, prereg)
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
        "rho": rho,
        "global_Q": q.tolist(),
        **result,
        "input_hashes": {
            "preregistration": sha256_file(args.preregistration),
            "evaluator": sha256_file(Path(__file__)),
            "premise_summary": sha256_file(premise_summary),
            "premise_verdict": sha256_file(premise_verdict),
            "stage1_manifest": sha256_file(args.stage1_root / "STAGE1_MANIFEST.json"),
            "stage1_artifact": stage1["artifact_sha256"],
            "v3_summary": sha256_file(args.v3_summary),
            "v3_verdict": sha256_file(args.v3_verdict),
        },
    }
    write_csv(args.output / "UPDATES.csv", updates)
    write_csv(args.output / "FINAL_PAIRS.csv", finals)
    (args.output / "SUMMARY.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output / "VERDICT.txt").write_text(result["verdict"] + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": result["verdict"],
        "rho": rho,
        "dynamic_overall": {mode: result["overall"]["dynamic_full"][mode] for mode in v2.PRIMARY_MODES},
        "hard_pass_rules": result["hard_pass_rules"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
