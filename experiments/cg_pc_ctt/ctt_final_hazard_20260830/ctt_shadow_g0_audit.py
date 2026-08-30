#!/usr/bin/env python3
"""Frozen G0 audit of the H01 CTRE fixed-trajectory shadow.

No GADEN, model training, ROS, method tuning, or new scientific likelihood is
performed. The script tests whether the historical formal-error signal survives
prior-only, label/pairing destruction, cell-row tie perturbation, or an
incorrect online recurrence.
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

from ctre_h01_historical_source_update_shadow import (
    ROOT,
    SENSOR_DELAY,
    STOP_SAMPLES,
    carrier_id_for_cell,
    completed_stops,
    ctre_scores,
    formal_location_error,
    load_support,
    posterior,
    read_csv_member,
    sensor_forward,
    sha256_file,
    unique_member,
)


def exact_rank(values: np.ndarray, truth: int) -> tuple[int, int, float]:
    target = float(values[truth])
    greater = int(np.count_nonzero(values > target))
    tied = int(np.count_nonzero(values == target))
    return 1 + greater, tied, 1.0 + greater + 0.5 * (tied - 1)


def carrier_to_cells_frozen(
    carrier_mass: np.ndarray,
    rows: list[dict],
    source_index: dict[str, int],
    free_cells: np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    """Project with the frozen within-carrier q0 distribution.

    The historical geometry prior is verified to be proportional to free-cell
    count, so its within-carrier q0 is uniform. This is frozen once and does not
    depend on CTRE outcome.
    """
    cell_mass = np.empty(len(rows), dtype=np.float64)
    seen = np.zeros(len(source_index), dtype=np.int64)
    for row_index, row in enumerate(rows):
        source = source_index[carrier_id_for_cell(int(row["cell_index"]), width, height)]
        cell_mass[row_index] = carrier_mass[source] / free_cells[source]
        seen[source] += 1
    if not np.array_equal(seen, free_cells):
        raise ValueError("CTT_G0_FREE_CELL_COUNT_MISMATCH")
    total = float(np.sum(cell_mass))
    if not np.isfinite(total) or total <= 0:
        raise ValueError("CTT_G0_CELL_MASS")
    return cell_mass / total


def tie_aware_formal_error(
    rows: list[dict],
    probability: np.ndarray,
    truth_xy: tuple[float, float],
) -> float:
    count = int(math.ceil(len(rows) * 0.05 - 1e-15))
    boundary = float(np.sort(probability)[::-1][count - 1])
    above = probability > boundary
    tied = probability == boundary
    remaining = count - int(np.count_nonzero(above))
    tie_count = int(np.count_nonzero(tied))
    if tie_count <= 0 or not (0 <= remaining <= tie_count):
        raise ValueError("CTT_G0_TIE_BOUNDARY")
    inclusion = above.astype(np.float64)
    inclusion[tied] = remaining / tie_count
    weight = probability * inclusion
    x = np.asarray([float(row["x"]) for row in rows], dtype=np.float64)
    y = np.asarray([float(row["y"]) for row in rows], dtype=np.float64)
    denom = float(np.sum(weight))
    if denom <= 0:
        raise ValueError("CTT_G0_TIE_ZERO_WEIGHT")
    estimate_x = float(np.sum(x * weight) / denom)
    estimate_y = float(np.sum(y * weight) / denom)
    return float(math.hypot(estimate_x - truth_xy[0], estimate_y - truth_xy[1]))


def row_order_error_range(
    rows: list[dict],
    probability: np.ndarray,
    truth_xy: tuple[float, float],
    seeds: list[int],
) -> tuple[float, float, float]:
    values = [formal_location_error(rows, probability, truth_xy)]
    for seed in seeds:
        permutation = np.random.default_rng(seed).permutation(len(rows))
        permuted_rows = [rows[int(index)] for index in permutation]
        values.append(formal_location_error(
            permuted_rows, probability[permutation], truth_xy))
    return float(min(values)), float(max(values)), float(max(values) - min(values))


def mass_within(
    rows: list[dict],
    probability: np.ndarray,
    truth_xy: tuple[float, float],
    radius_m: float,
) -> float:
    x = np.asarray([float(row["x"]) for row in rows], dtype=np.float64)
    y = np.asarray([float(row["y"]) for row in rows], dtype=np.float64)
    mask = np.hypot(x - truth_xy[0], y - truth_xy[1]) <= radius_m + 1e-12
    return float(np.sum(probability[mask]))


def nearest_truth_cell(
    rows: list[dict],
    probability: np.ndarray,
    truth_xy: tuple[float, float],
) -> tuple[int, float, float]:
    x = np.asarray([float(row["x"]) for row in rows], dtype=np.float64)
    y = np.asarray([float(row["y"]) for row in rows], dtype=np.float64)
    distance = np.hypot(x - truth_xy[0], y - truth_xy[1])
    index = int(np.argmin(distance))
    rank, _, _ = exact_rank(probability, index)
    return rank, float(probability[index]), float(distance[index])


def stable_joint_posterior(log_weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    shifted = log_weights - float(np.max(log_weights))
    weights = np.exp(shifted)
    weights /= np.sum(weights)
    return weights, np.sum(weights, axis=1)


def pooled_improvement(reference: np.ndarray, candidate: np.ndarray) -> float:
    return float((np.sum(reference) - np.sum(candidate)) / np.sum(reference))


def selftest() -> None:
    rows = [
        {"x": str(index), "y": "0", "cell_index": str(index)}
        for index in range(20)
    ]
    probability = np.full(20, 0.05, dtype=np.float64)
    stable = formal_location_error(rows, probability, (0.0, 0.0))
    tied = tie_aware_formal_error(rows, probability, (0.0, 0.0))
    if stable == tied:
        raise AssertionError("tie diagnostic failed to distinguish stable boundary")

    prior = np.asarray([0.4, 0.6])
    per_stop = np.asarray([
        [[math.log(0.75), math.log(0.25)], [math.log(0.25), math.log(0.75)]],
        [[math.log(0.25), math.log(0.25)], [math.log(0.75), math.log(0.75)]],
    ])
    online = np.repeat(np.log(prior)[:, None] - math.log(2.0), 2, axis=1)
    for stop in range(2):
        online += per_stop[:, :, stop]
    _, q_online = stable_joint_posterior(online)
    batch = np.log(prior)[:, None] - math.log(2.0) + np.sum(per_stop, axis=2)
    _, q_batch = stable_joint_posterior(batch)
    if float(np.max(np.abs(q_online - q_batch))) > 1e-15:
        raise AssertionError("online batch selftest")
    print("CTT_SHADOW_G0_SELFTEST=PASS")


def run(args: argparse.Namespace) -> int:
    if args.output.exists():
        raise SystemExit(f"CTT_G0_REFUSE_OVERWRITE:{args.output}")
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    if prereg.get("contract") != "CTT_SHADOW_METRIC_PRIOR_TIE_RECURRENCE_G0_V1":
        raise SystemExit("CTT_G0_PREREG_CONTRACT")
    expected = prereg["input_sha256"]
    for label, path in (
        ("archive", args.archive),
        ("support", args.support),
        ("mapping", args.mapping),
    ):
        actual = sha256_file(path)
        if actual != expected[label]:
            raise SystemExit(f"CTT_G0_HASH:{label}:{actual}")

    support_ids, free_cells = load_support(args.support)
    source_label_permutation = np.random.default_rng(
        int(prereg["frozen_controls"]["source_label_permutation_seed"])
    ).permutation(len(support_ids))
    row_seeds = [int(value) for value in
                 prereg["frozen_controls"]["cell_row_permutation_seeds"]]
    output_rows: list[dict] = []
    final_rows: list[dict] = []
    max_online_batch = 0.0
    max_joint_online_batch = 0.0

    with tarfile.open(args.archive, "r:gz") as tf:
        for seed in prereg["scope"]["seeds"]:
            bank_path = args.bank_dir / f"H01_seed{seed}_candidate_physical.npz"
            actual_bank_hash = sha256_file(bank_path)
            if actual_bank_hash != expected["bank_views"][str(seed)]:
                raise SystemExit(f"CTT_G0_BANK_HASH:{seed}:{actual_bank_hash}")
            with np.load(bank_path, allow_pickle=False) as bank:
                physical = np.asarray(bank["candidate_physical_ppm"], dtype=np.float64)
                source_ids = np.asarray(bank["source_id"]).astype(str)
                prior = np.asarray(bank["geometry_prior"], dtype=np.float64)
                bank_time = np.asarray(bank["sample_time_s"], dtype=np.float64)
            if physical.shape[:2] != (210, 8) or list(source_ids) != support_ids:
                raise ValueError(f"CTT_G0_BANK_SHAPE_OR_ORDER:{seed}")
            prior /= np.sum(prior)
            expected_geometry_prior = free_cells.astype(np.float64) / np.sum(free_cells)
            geometry_prior_max_abs = float(np.max(np.abs(prior - expected_geometry_prior)))
            if geometry_prior_max_abs > 1e-12:
                raise ValueError(f"CTT_G0_Q0_WITHIN_CARRIER_UNRESOLVED:{seed}:{geometry_prior_max_abs}")

            source_index = {source_id: index for index, source_id in enumerate(source_ids)}
            truth_index = source_index["quadtree_22_16_2_2"]
            prefix = f"{ROOT}/seed{seed}/off/runtime/"
            sensor = read_csv_member(tf, unique_member(tf, prefix, "/sensor_trace.csv"))
            pose = read_csv_member(tf, unique_member(tf, prefix, "/sim_pose_trace.csv"))
            timing = read_csv_member(
                tf, unique_member(tf, prefix, "/context_bank/source_update_timing.csv"))
            sensor_time = np.asarray([float(row["t_sim_s"]) for row in sensor])
            pose_time = np.asarray([float(row["t_sim_s"]) for row in pose])
            if len(sensor) != len(pose) or np.max(np.abs(sensor_time - pose_time)) > 1e-9:
                raise ValueError(f"CTT_G0_SENSOR_POSE:{seed}")
            aligned_time = sensor_time[SENSOR_DELAY:]
            measured = np.asarray(
                [float(row["measured_gas_ppm"]) for row in sensor], dtype=np.float64
            )[SENSOR_DELAY:]
            aligned_pose = pose[SENSOR_DELAY:]
            if physical.shape[2] != len(aligned_time):
                raise ValueError(f"CTT_G0_BANK_LENGTH:{seed}")
            if np.max(np.abs(bank_time - sensor_time[:-SENSOR_DELAY])) > 1e-9:
                raise ValueError(f"CTT_G0_BANK_TIME:{seed}")
            stops = completed_stops(aligned_pose, aligned_time)
            candidate_measured = sensor_forward(physical)
            observed_detection = np.asarray(
                [np.any(measured[index] > 0.1) for index in stops], dtype=np.bool_)
            candidate_detection = np.asarray([
                np.any(candidate_measured[:, :, index] > 0.1, axis=2)
                for index in stops
            ], dtype=np.bool_).transpose(1, 2, 0)

            case_member = f"{ROOT}/seed{seed}/off/case_result.json"
            case_file = tf.extractfile(case_member)
            if case_file is None:
                raise ValueError(f"CTT_G0_CASE:{seed}")
            case = json.loads(case_file.read().decode("utf-8"))
            truth_xy = tuple(float(value) for value in case["truth_eval_only"])
            online_log_weights = np.repeat(
                np.log(prior)[:, None] - math.log(8.0), 8, axis=1)
            consumed = 0

            for update in timing:
                update_id = int(update["source_update_id"])
                update_time = float(update["sim_time"])
                visible = [
                    index for index, stop in enumerate(stops)
                    if aligned_time[stop[-1]] <= update_time + 1e-12
                ]
                if len(visible) != 3 * update_id:
                    raise ValueError(
                        f"CTT_G0_VISIBLE_STOP_CONTRACT:{seed}:{update_id}:{len(visible)}")
                new_visible = visible[consumed:]
                if len(new_visible) != 3:
                    raise ValueError(f"CTT_G0_DELTA_STOP_CONTRACT:{seed}:{update_id}")
                probability = (
                    0.5 + candidate_detection[:, :, new_visible].astype(np.float64)
                ) / 2.0
                new_y = observed_detection[new_visible].astype(np.float64)
                online_log_weights += (
                    new_y[None, None, :] * np.log(probability)
                    + (1.0 - new_y[None, None, :]) * np.log1p(-probability)
                ).sum(axis=2)
                online_joint, online_carrier = stable_joint_posterior(online_log_weights)
                consumed = len(visible)

                coherent, stopwise = ctre_scores(
                    candidate_detection[:, :, visible], observed_detection[visible])
                ctt_carrier = posterior(prior, coherent)
                batch_probability = (
                    0.5 + candidate_detection[:, :, visible].astype(np.float64)
                ) / 2.0
                batch_y = observed_detection[visible].astype(np.float64)
                batch_log_weights = np.log(prior)[:, None] - math.log(8.0) + (
                    batch_y[None, None, :] * np.log(batch_probability)
                    + (1.0 - batch_y[None, None, :]) * np.log1p(-batch_probability)
                ).sum(axis=2)
                batch_joint, batch_carrier = stable_joint_posterior(batch_log_weights)
                online_batch = float(np.max(np.abs(online_carrier - batch_carrier)))
                joint_online_batch = float(np.max(np.abs(online_joint - batch_joint)))
                posterior_identity = float(np.max(np.abs(ctt_carrier - batch_carrier)))
                max_online_batch = max(max_online_batch, online_batch, posterior_identity)
                max_joint_online_batch = max(max_joint_online_batch, joint_online_batch)

                label_score = coherent[source_label_permutation]
                label_carrier = posterior(prior, label_score)
                pairing_rng = np.random.default_rng(
                    int(prereg["frozen_controls"]["observation_pairing_permutation_seed"])
                    + 101 * int(seed) + 1009 * update_id)
                pairing_permutation = pairing_rng.permutation(len(visible))
                pairing_score, _ = ctre_scores(
                    candidate_detection[:, :, visible],
                    observed_detection[np.asarray(visible)[pairing_permutation]])
                pairing_carrier = posterior(prior, pairing_score)

                update_suffix = (
                    f"/context_bank/source_update_{update_id:04d}/source_posterior.csv")
                native_cells = read_csv_member(
                    tf, unique_member(tf, prefix, update_suffix))
                width = int(update["grid_width"])
                height = int(update["grid_height"])
                native_cell_mass = np.asarray(
                    [float(row["source_probability"]) for row in native_cells],
                    dtype=np.float64)
                native_cell_mass /= np.sum(native_cell_mass)
                q0_cells = carrier_to_cells_frozen(
                    prior, native_cells, source_index, free_cells, width, height)
                ctt_cells = carrier_to_cells_frozen(
                    ctt_carrier, native_cells, source_index, free_cells, width, height)
                label_cells = carrier_to_cells_frozen(
                    label_carrier, native_cells, source_index, free_cells, width, height)
                pairing_cells = carrier_to_cells_frozen(
                    pairing_carrier, native_cells, source_index, free_cells, width, height)

                stable_error = formal_location_error(native_cells, ctt_cells, truth_xy)
                tie_error = tie_aware_formal_error(native_cells, ctt_cells, truth_xy)
                row_min, row_max, row_range = row_order_error_range(
                    native_cells, ctt_cells, truth_xy, row_seeds)
                raw_rank, raw_ties, raw_midrank = exact_rank(coherent, truth_index)
                posterior_rank, posterior_ties, posterior_midrank = exact_rank(
                    ctt_carrier, truth_index)
                truth_cell_rank, truth_cell_mass, truth_cell_distance = nearest_truth_cell(
                    native_cells, ctt_cells, truth_xy)
                row = {
                    "seed": seed,
                    "source_update_id": update_id,
                    "visible_stops": len(visible),
                    "observed_hit_stops": int(np.sum(observed_detection[visible])),
                    "native_formal_error_m": formal_location_error(
                        native_cells, native_cell_mass, truth_xy),
                    "q0_formal_error_m": formal_location_error(
                        native_cells, q0_cells, truth_xy),
                    "ctt_formal_error_m": stable_error,
                    "source_permuted_formal_error_m": formal_location_error(
                        native_cells, label_cells, truth_xy),
                    "pairing_permuted_formal_error_m": formal_location_error(
                        native_cells, pairing_cells, truth_xy),
                    "ctt_tie_aware_formal_error_m": tie_error,
                    "ctt_tie_aware_abs_difference_m": abs(tie_error - stable_error),
                    "ctt_row_order_min_error_m": row_min,
                    "ctt_row_order_max_error_m": row_max,
                    "ctt_row_order_range_m": row_range,
                    "online_batch_max_abs": online_batch,
                    "joint_online_batch_max_abs": joint_online_batch,
                    "posterior_identity_max_abs": posterior_identity,
                    "raw_true_carrier_rank": raw_rank,
                    "raw_true_carrier_ties": raw_ties,
                    "raw_true_carrier_midrank": raw_midrank,
                    "posterior_true_carrier_rank": posterior_rank,
                    "posterior_true_carrier_ties": posterior_ties,
                    "posterior_true_carrier_midrank": posterior_midrank,
                    "posterior_true_carrier_mass": float(ctt_carrier[truth_index]),
                    "raw_true_score": float(coherent[truth_index]),
                    "raw_true_vs_best_rival_margin": float(
                        coherent[truth_index] - np.max(np.delete(coherent, truth_index))),
                    "nearest_truth_cell_rank": truth_cell_rank,
                    "nearest_truth_cell_mass": truth_cell_mass,
                    "nearest_truth_cell_distance_m": truth_cell_distance,
                    "posterior_mass_within_0p5m": mass_within(
                        native_cells, ctt_cells, truth_xy, 0.5),
                    "posterior_mass_within_1m": mass_within(
                        native_cells, ctt_cells, truth_xy, 1.0),
                    "posterior_mass_within_2m": mass_within(
                        native_cells, ctt_cells, truth_xy, 2.0),
                    "geometry_prior_max_abs": geometry_prior_max_abs,
                }
                output_rows.append(row)
                if update_id == 5:
                    archive_error = float(case["primary_error_m"])
                    if abs(row["native_formal_error_m"] - archive_error) > 1e-10:
                        raise ValueError(f"CTT_G0_NATIVE_PARITY:{seed}")
                    final_rows.append(row)

    pmfs = np.asarray([row["native_formal_error_m"] for row in final_rows])
    q0 = np.asarray([row["q0_formal_error_m"] for row in final_rows])
    ctt = np.asarray([row["ctt_formal_error_m"] for row in final_rows])
    label = np.asarray([
        row["source_permuted_formal_error_m"] for row in final_rows])
    pairing = np.asarray([
        row["pairing_permuted_formal_error_m"] for row in final_rows])
    rules = prereg["pass_rule"]
    summary = {
        "valid_final_pairs": len(final_rows),
        "pmfs_mean_error_m": float(np.mean(pmfs)),
        "q0_mean_error_m": float(np.mean(q0)),
        "ctt_mean_error_m": float(np.mean(ctt)),
        "source_permuted_mean_error_m": float(np.mean(label)),
        "pairing_permuted_mean_error_m": float(np.mean(pairing)),
        "ctt_vs_pmfs_pooled_improvement": pooled_improvement(pmfs, ctt),
        "q0_vs_pmfs_pooled_improvement": pooled_improvement(pmfs, q0),
        "source_permuted_vs_pmfs_pooled_improvement": pooled_improvement(pmfs, label),
        "pairing_permuted_vs_pmfs_pooled_improvement": pooled_improvement(pmfs, pairing),
        "ctt_vs_q0_pooled_improvement": pooled_improvement(q0, ctt),
        "ctt_vs_source_permuted_pooled_improvement": pooled_improvement(label, ctt),
        "ctt_vs_pairing_permuted_pooled_improvement": pooled_improvement(pairing, ctt),
        "ctt_better_than_q0_pairs": int(np.sum(ctt < q0 - 1e-12)),
        "ctt_better_than_source_permuted_pairs": int(np.sum(ctt < label - 1e-12)),
        "ctt_better_than_pairing_permuted_pairs": int(np.sum(ctt < pairing - 1e-12)),
        "maximum_row_order_error_range_m": float(max(
            row["ctt_row_order_range_m"] for row in output_rows)),
        "maximum_tie_aware_error_difference_m": float(max(
            row["ctt_tie_aware_abs_difference_m"] for row in output_rows)),
        "maximum_online_batch_abs": max_online_batch,
        "maximum_joint_online_batch_abs": max_joint_online_batch,
    }
    checks = {
        "online_batch": summary["maximum_online_batch_abs"]
        <= float(rules["online_batch_max_abs_tolerance"]),
        "row_order_invariance": summary["maximum_row_order_error_range_m"]
        <= float(rules["cell_row_formal_error_range_tolerance_m"]),
        "tie_aware_invariance": summary["maximum_tie_aware_error_difference_m"]
        <= float(rules["tie_aware_formal_error_difference_tolerance_m"]),
        "q0_does_not_meet_target": summary["q0_vs_pmfs_pooled_improvement"]
        <= float(rules["maximum_q0_vs_pmfs_pooled_improvement"]),
        "source_permuted_does_not_meet_target":
        summary["source_permuted_vs_pmfs_pooled_improvement"]
        <= float(rules["maximum_source_permuted_vs_pmfs_pooled_improvement"]),
        "ctt_beats_q0_pairs": summary["ctt_better_than_q0_pairs"]
        >= int(rules["minimum_ctt_better_than_q0_pairs"]),
        "ctt_beats_source_permuted_pairs":
        summary["ctt_better_than_source_permuted_pairs"]
        >= int(rules["minimum_ctt_better_than_source_permuted_pairs"]),
        "ctt_beats_pairing_permuted_pairs":
        summary["ctt_better_than_pairing_permuted_pairs"]
        >= int(rules["minimum_ctt_better_than_pairing_permuted_pairs"]),
        "ctt_beats_q0_pooled": summary["ctt_vs_q0_pooled_improvement"]
        > float(rules["minimum_ctt_vs_q0_pooled_improvement"]),
        "ctt_beats_source_permuted_pooled":
        summary["ctt_vs_source_permuted_pooled_improvement"]
        > float(rules["minimum_ctt_vs_source_permuted_pooled_improvement"]),
        "ctt_beats_pairing_permuted_pooled":
        summary["ctt_vs_pairing_permuted_pooled_improvement"]
        > float(rules["minimum_ctt_vs_pairing_permuted_pooled_improvement"]),
    }
    passed = len(final_rows) == 10 and all(checks.values())
    verdict = prereg["terminal_states"]["pass" if passed else "fail"]
    report = {
        "contract": prereg["contract"],
        "summary": summary,
        "checks": checks,
        "failed_checks": [name for name, value in checks.items() if not value],
        "verdict": verdict,
        "input_hashes": {
            "archive": sha256_file(args.archive),
            "support": sha256_file(args.support),
            "mapping": sha256_file(args.mapping),
            "preregistration": sha256_file(args.preregistration),
        },
        "scope": prereg["scope"],
    }
    args.output.mkdir(parents=True)
    with (args.output / "CASES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    (args.output / "SUMMARY.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "VERDICT.txt").write_text(verdict + "\n", encoding="utf-8")
    print(json.dumps({
        "summary": summary,
        "failed_checks": report["failed_checks"],
        "verdict": verdict,
    }, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--bank-dir", type=Path)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    required = ("archive", "bank_dir", "support", "mapping", "preregistration", "output")
    missing = [name for name in required if getattr(args, name) is None]
    if missing:
        parser.error("missing required arguments: " + ", ".join(missing))
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
