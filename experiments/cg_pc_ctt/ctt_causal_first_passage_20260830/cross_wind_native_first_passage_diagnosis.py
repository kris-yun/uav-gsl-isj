#!/usr/bin/env python3
"""Frozen model-free cross-wind native first-passage source diagnosis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from ctt_h01_wind_bank_io import (
    FIRST_PASSAGE_THRESHOLD_PPM,
    STOP_SAMPLES,
    read_physical,
    sensor_forward,
    sha256_file,
)


CONTEXTS = (1, 2)
PREDICTIVE_MEMBERS = (0, 1, 2, 3, 4, 5)
OBSERVATION_MEMBERS = (6, 7)
ROUTE_STREAM = 4
ROUTE_SEED = 4005
SOURCE_COUNT = 210
STOP_COUNT = 10
TIME_TAG = "CTT-H01-CROSS-WIND-TIME-PERMUTE-V1"
FROZEN_NEURAL_VERDICT = "CTT_H01_WIND_CONDITIONED_NEURAL_M1_PHYSICAL_NO_GO"


def load_carriers(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    carriers = [{"index": int(row["carrier_index"]), "id": row["carrier_id"]} for row in rows]
    carriers.sort(key=lambda row: row["index"])
    if len(carriers) != SOURCE_COUNT or [row["index"] for row in carriers] != list(range(SOURCE_COUNT)):
        raise ValueError("CROSS_WIND_CARRIER_CONTRACT_FAIL")
    if len({row["id"] for row in carriers}) != SOURCE_COUNT:
        raise ValueError("CROSS_WIND_CARRIER_ALIAS_FAIL")
    return carriers


def load_stop_indices(path: Path) -> list[np.ndarray]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    result = []
    stop_ids = sorted({int(row["stop_id"]) for row in rows})
    for stop_id in stop_ids:
        indices = np.asarray([
            index for index, row in enumerate(rows)
            if int(row["stop_id"]) == stop_id and int(row["is_moving"]) == 0
        ], dtype=np.int64)
        if len(indices) < STOP_SAMPLES:
            continue
        result.append(indices[:STOP_SAMPLES])
    if len(result) != STOP_COUNT or any(len(indices) != STOP_SAMPLES for indices in result):
        raise ValueError(f"CROSS_WIND_STOP_CONTRACT_FAIL:{[len(x) for x in result]}")
    return result


def labels_and_tapes(path: Path, stop_indices: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    streams = read_physical(path)
    if len(streams) != 5:
        raise ValueError(f"CROSS_WIND_ROUTE_STREAM_COUNT_FAIL:{path}")
    measured = sensor_forward(streams[ROUTE_STREAM])
    tapes = np.stack([measured[indices] > FIRST_PASSAGE_THRESHOLD_PPM for indices in stop_indices])
    labels = np.asarray([
        int(np.argmax(tape)) if bool(tape.any()) else STOP_SAMPLES for tape in tapes
    ], dtype=np.int16)
    return labels, tapes


def deterministic_permutation(context: int, member: int, truth: int, stop: int) -> np.ndarray:
    rows = []
    for index in range(STOP_SAMPLES):
        text = f"{TIME_TAG}|{context}|{member}|{truth}|{stop}|{index}"
        rows.append((hashlib.sha256(text.encode("utf-8")).digest(), index))
    return np.asarray([index for _, index in sorted(rows)], dtype=np.int64)


def permuted_labels(tapes: np.ndarray, context: int, member: int, truth: int) -> np.ndarray:
    result = []
    for stop, tape in enumerate(tapes):
        permuted = tape[deterministic_permutation(context, member, truth, stop)]
        if int(permuted.sum()) != int(tape.sum()):
            raise AssertionError("CROSS_WIND_TIME_PERMUTE_COUNT_CHANGED")
        result.append(int(np.argmax(permuted)) if bool(permuted.any()) else STOP_SAMPLES)
    return np.asarray(result, dtype=np.int16)


def predictive_cdf(labels: np.ndarray) -> np.ndarray:
    # labels: [predictive_member, candidate, stop]
    timeline = np.arange(STOP_SAMPLES, dtype=np.int16)
    return (labels[..., None] <= timeline).mean(axis=0, dtype=np.float64)


def full_distances(cdf: np.ndarray, observed: np.ndarray) -> np.ndarray:
    timeline = np.arange(STOP_SAMPLES, dtype=np.int16)
    target = observed[:, None] <= timeline[None, :]
    return ((cdf - target[None, :, :]) ** 2).sum(axis=(1, 2), dtype=np.float64)


def survival_distances(labels: np.ndarray, observed: np.ndarray) -> np.ndarray:
    probability = (labels < STOP_SAMPLES).mean(axis=0, dtype=np.float64)
    target = observed < STOP_SAMPLES
    return ((probability - target[None, :]) ** 2).sum(axis=1, dtype=np.float64)


def exact_midrank(distance: np.ndarray, truth: int) -> float:
    target = distance[truth]
    return float(1 + np.count_nonzero(distance < target) +
                 0.5 * (np.count_nonzero(distance == target) - 1))


def exact_sign_test(left: np.ndarray, right: np.ndarray) -> dict:
    wins = int(np.count_nonzero(left < right))
    losses = int(np.count_nonzero(left > right))
    ties = int(np.count_nonzero(left == right))
    count = wins + losses
    numerator = sum(math.comb(count, value) for value in range(wins, count + 1)) if count else 1
    denominator = 2 ** count if count else 1
    return {"wins": wins, "losses": losses, "ties": ties,
            "one_sided_exact_p": float(numerator / denominator)}


def summarize(rows: list[dict], rank_field: str) -> dict:
    ranks = np.asarray([float(row[rank_field]) for row in rows], dtype=np.float64)
    normalized = (ranks - 1.0) / (SOURCE_COUNT - 1)
    return {
        "cases": len(rows),
        "mean_normalized_rank": float(normalized.mean()),
        "median_rank": float(np.median(ranks)),
        "top5": float(np.mean(ranks <= 5.0)),
        "top10": float(np.mean(ranks <= 10.0)),
    }


def comparison(rows: list[dict], comparator: str) -> dict:
    full = np.asarray([row["rank_full"] for row in rows], dtype=np.float64)
    other = np.asarray([row[f"rank_{comparator}"] for row in rows], dtype=np.float64)
    sign = exact_sign_test(full, other)
    by_context = {}
    nonreverse = True
    for context in CONTEXTS:
        mask = np.asarray([row["context"] == context for row in rows])
        full_mean = float(((full[mask] - 1.0) / 209.0).mean())
        other_mean = float(((other[mask] - 1.0) / 209.0).mean())
        by_context[str(context)] = {
            "full_mean_normalized_rank": full_mean,
            "comparator_mean_normalized_rank": other_mean,
            "full_minus_comparator": full_mean - other_mean,
            "nonreverse": full_mean <= other_mean,
        }
        nonreverse &= full_mean <= other_mean
    full_mean = float(((full - 1.0) / 209.0).mean())
    other_mean = float(((other - 1.0) / 209.0).mean())
    passed = full_mean < other_mean and sign["one_sided_exact_p"] <= 0.01 and nonreverse
    return {
        "full_mean_normalized_rank": full_mean,
        "comparator_mean_normalized_rank": other_mean,
        "full_minus_comparator": full_mean - other_mean,
        "sign_test": sign,
        "by_context": by_context,
        "pass": bool(passed),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--g0-gate", type=Path, required=True)
    parser.add_argument("--frozen-neural-verdict", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--preregistration-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"CROSS_WIND_REFUSE_OVERWRITE:{args.output}")
    if sha256_file(args.preregistration) != args.preregistration_sha256:
        raise SystemExit("CROSS_WIND_PREREGISTRATION_HASH_FAIL")
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    if prereg.get("contract") != "CTT_H01_CROSS_WIND_NATIVE_FIRST_PASSAGE_DIAGNOSIS_V1":
        raise SystemExit("CROSS_WIND_PREREGISTRATION_CONTRACT_FAIL")
    bank_summary = json.loads((args.bank / "bank_summary.json").read_text(encoding="utf-8"))
    if (bank_summary.get("verdict") != "CTT_H01_WIND_BANK_MATERIALIZATION_PASS" or
            not bank_summary.get("scientific_gate_eligible") or bank_summary.get("file_count") != 16800):
        raise SystemExit("CROSS_WIND_BANK_CONTRACT_FAIL")
    g0 = json.loads(args.g0_gate.read_text(encoding="utf-8"))
    if g0.get("verdict") != "CTT_H01_WIND_BANK_G0_PASS" or not all(g0.get("gates", {}).values()):
        raise SystemExit("CROSS_WIND_G0_CONTRACT_FAIL")
    if args.frozen_neural_verdict.read_text(encoding="utf-8").strip() != FROZEN_NEURAL_VERDICT:
        raise SystemExit("CROSS_WIND_FROZEN_NEURAL_VERDICT_CHANGED")

    args.output.mkdir(parents=True)
    carriers = load_carriers(args.support)
    stop_indices = load_stop_indices(args.schedule)
    labels = np.empty((len(CONTEXTS), 8, SOURCE_COUNT, STOP_COUNT), dtype=np.int16)
    held_tapes = np.empty((len(CONTEXTS), len(OBSERVATION_MEMBERS), SOURCE_COUNT,
                           STOP_COUNT, STOP_SAMPLES), dtype=np.bool_)
    for ci, context in enumerate(CONTEXTS):
        for member in range(8):
            for source, carrier in enumerate(carriers):
                path = args.bank / f"context_{context:02d}" / f"member_{member:02d}" / f"{carrier['id']}.bin"
                member_labels, tapes = labels_and_tapes(path, stop_indices)
                labels[ci, member, source] = member_labels
                if member in OBSERVATION_MEMBERS:
                    held_tapes[ci, member - OBSERVATION_MEMBERS[0], source] = tapes
        print(f"CROSS_WIND_LOAD_CONTEXT={context} PASS", flush=True)

    rows = []
    for ci, context in enumerate(CONTEXTS):
        predictive = labels[ci, :6]
        cdf = predictive_cdf(predictive)
        for oi, member in enumerate(OBSERVATION_MEMBERS):
            for truth, carrier in enumerate(carriers):
                observed = labels[ci, member, truth]
                permuted = permuted_labels(held_tapes[ci, oi, truth], context, member, truth)
                full = full_distances(cdf, observed)
                survival = survival_distances(predictive, observed)
                time_permute = full_distances(cdf, permuted)
                best_full = int(np.argmin(full))
                best_survival = int(np.argmin(survival))
                best_time = int(np.argmin(time_permute))
                rank_full = exact_midrank(full, truth)
                rank_survival = exact_midrank(survival, truth)
                rank_time = exact_midrank(time_permute, truth)
                rows.append({
                    "context": context, "observation_transport_key": member,
                    "truth_source_index": truth, "truth_source_id": carrier["id"],
                    "rank_full": rank_full, "normalized_rank_full": (rank_full - 1.0) / 209.0,
                    "rank_survival": rank_survival, "normalized_rank_survival": (rank_survival - 1.0) / 209.0,
                    "rank_time_permute": rank_time, "normalized_rank_time_permute": (rank_time - 1.0) / 209.0,
                    "top5_full": int(rank_full <= 5.0), "top10_full": int(rank_full <= 10.0),
                    "top5_survival": int(rank_survival <= 5.0), "top10_survival": int(rank_survival <= 10.0),
                    "top5_time_permute": int(rank_time <= 5.0), "top10_time_permute": int(rank_time <= 10.0),
                    "distance_true_full": float(full[truth]), "distance_true_survival": float(survival[truth]),
                    "distance_true_time_permute": float(time_permute[truth]),
                    "best_source_full": best_full, "best_source_survival": best_survival,
                    "best_source_time_permute": best_time,
                })
        print(f"CROSS_WIND_SCORE_CONTEXT={context} PASS", flush=True)

    write_csv(args.output / "840_CASES.csv", rows)
    rank_fields = ("full", "survival", "time_permute")
    overall = {name: summarize(rows, f"rank_{name}") for name in rank_fields}
    by_context = {
        str(context): {name: summarize([row for row in rows if row["context"] == context], f"rank_{name}")
                       for name in rank_fields} for context in CONTEXTS
    }
    by_key = {
        str(member): {name: summarize([row for row in rows if row["observation_transport_key"] == member],
                                     f"rank_{name}") for name in rank_fields}
        for member in OBSERVATION_MEMBERS
    }
    full_vs_survival = comparison(rows, "survival")
    full_vs_time = comparison(rows, "time_permute")
    passed_count = int(full_vs_survival["pass"]) + int(full_vs_time["pass"])
    verdict = ("CROSS_WIND_NATIVE_FIRST_PASSAGE_PASS" if passed_count == 2 else
               "CROSS_WIND_FIRST_PASSAGE_PARTIAL" if passed_count == 1 else
               "CROSS_WIND_FIRST_PASSAGE_NO_GO")
    interpretation = {
        "CROSS_WIND_NATIVE_FIRST_PASSAGE_PASS": "NEURAL_REPRESENTATION_FAILURE_SUPPORTED_NEW_UNSEEN_WINDS_REQUIRED",
        "CROSS_WIND_FIRST_PASSAGE_PARTIAL": "NATIVE_MECHANISM_PARTIAL_AMBIGUOUS",
        "CROSS_WIND_FIRST_PASSAGE_NO_GO": "CROSS_WIND_FIRST_PASSAGE_MECHANISM_FAILURE_SUPPORTED_STOP_LINE",
    }[verdict]
    report = {
        "contract": prereg["contract"], "diagnostic_after_test_opening": True,
        "frozen_neural_verdict_unchanged": FROZEN_NEURAL_VERDICT,
        "cases": len(rows), "overall": overall, "by_context": by_context, "by_key": by_key,
        "full_vs_survival": full_vs_survival, "full_vs_time_permute": full_vs_time,
        "random_reference": {"mean_normalized_rank": 0.5, "top5": 5 / 210, "top10": 10 / 210},
        "verdict": verdict, "interpretation": interpretation,
        "closed_loop_authorized": False,
    }
    hashes = {
        "preregistration_sha256": sha256_file(args.preregistration),
        "bank_summary_sha256": sha256_file(args.bank / "bank_summary.json"),
        "bank_file_manifest_sha256": sha256_file(args.bank / "FILE_SHA256.tsv"),
        "support_sha256": sha256_file(args.support), "schedule_sha256": sha256_file(args.schedule),
        "g0_gate_sha256": sha256_file(args.g0_gate),
        "frozen_neural_verdict_sha256": sha256_file(args.frozen_neural_verdict),
    }
    (args.output / "SUMMARY.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (args.output / "INPUT_HASHES.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    (args.output / "VERDICT.txt").write_text(verdict + "\n")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

