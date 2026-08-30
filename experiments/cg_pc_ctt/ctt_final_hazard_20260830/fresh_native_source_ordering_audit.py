#!/usr/bin/env python3
"""Post-NO-GO, model-free source-ordering audit on fresh airflow contexts."""

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

CONTEXTS = (10, 11, 12, 13)
PREDICTIVE_MEMBERS = tuple(range(6))
OBSERVATION_MEMBERS = (6, 7)
ROUTE_STREAM = 4
SOURCE_COUNT = 210
STOP_COUNT = 10
TIME_TAG = "CTT-H01-FRESH-NATIVE-TIME-PERMUTE-V1"


def load_carriers(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    carriers = [{"index": int(row["carrier_index"]), "id": row["carrier_id"]} for row in rows]
    carriers.sort(key=lambda row: row["index"])
    if len(carriers) != SOURCE_COUNT or [row["index"] for row in carriers] != list(range(SOURCE_COUNT)):
        raise ValueError("FRESH_NATIVE_CARRIER_CONTRACT_FAIL")
    return carriers


def load_stops(path: Path) -> list[np.ndarray]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    result = []
    for stop_id in sorted({int(row["stop_id"]) for row in rows}):
        idx = np.asarray([
            i for i, row in enumerate(rows)
            if int(row["stop_id"]) == stop_id and int(row["is_moving"]) == 0
        ], dtype=np.int64)
        if len(idx) >= STOP_SAMPLES:
            result.append(idx[:STOP_SAMPLES])
    if len(result) != STOP_COUNT:
        raise ValueError(f"FRESH_NATIVE_STOP_CONTRACT_FAIL:{[len(x) for x in result]}")
    return result


def labels_tapes(path: Path, stops: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    streams = read_physical(path)
    if len(streams) != 5:
        raise ValueError(f"FRESH_NATIVE_STREAM_COUNT_FAIL:{path}")
    measured = sensor_forward(streams[ROUTE_STREAM])
    tapes = np.stack([measured[idx] > FIRST_PASSAGE_THRESHOLD_PPM for idx in stops])
    labels = np.asarray([int(np.argmax(x)) if bool(x.any()) else STOP_SAMPLES for x in tapes], dtype=np.int16)
    return labels, tapes


def time_permute(tapes: np.ndarray, context: int, member: int, truth: int) -> np.ndarray:
    labels = []
    for stop, tape in enumerate(tapes):
        keyed = []
        for i in range(STOP_SAMPLES):
            tag = f"{TIME_TAG}|{context}|{member}|{truth}|{stop}|{i}"
            keyed.append((hashlib.sha256(tag.encode()).digest(), i))
        order = np.asarray([i for _, i in sorted(keyed)], dtype=np.int64)
        shuffled = tape[order]
        if int(shuffled.sum()) != int(tape.sum()):
            raise AssertionError("FRESH_NATIVE_TIME_PERMUTE_COUNT_CHANGED")
        labels.append(int(np.argmax(shuffled)) if bool(shuffled.any()) else STOP_SAMPLES)
    return np.asarray(labels, dtype=np.int16)


def cdf(labels: np.ndarray) -> np.ndarray:
    timeline = np.arange(STOP_SAMPLES, dtype=np.int16)
    return (labels[..., None] <= timeline).mean(axis=0, dtype=np.float64)


def full_distance(predictive_cdf: np.ndarray, observed: np.ndarray) -> np.ndarray:
    timeline = np.arange(STOP_SAMPLES, dtype=np.int16)
    target = observed[:, None] <= timeline[None, :]
    return ((predictive_cdf - target[None, :, :]) ** 2).sum(axis=(1, 2), dtype=np.float64)


def survival_distance(labels: np.ndarray, observed: np.ndarray) -> np.ndarray:
    prob = (labels < STOP_SAMPLES).mean(axis=0, dtype=np.float64)
    target = observed < STOP_SAMPLES
    return ((prob - target[None, :]) ** 2).sum(axis=1, dtype=np.float64)


def midrank(distance: np.ndarray, truth: int) -> float:
    target = distance[truth]
    return float(1 + np.count_nonzero(distance < target) + 0.5 * (np.count_nonzero(distance == target) - 1))


def sign_test(left: np.ndarray, right: np.ndarray) -> dict:
    wins = int(np.count_nonzero(left < right))
    losses = int(np.count_nonzero(left > right))
    ties = int(np.count_nonzero(left == right))
    count = wins + losses
    p = sum(math.comb(count, k) for k in range(wins, count + 1)) / (2 ** count) if count else 1.0
    return {"wins": wins, "losses": losses, "ties": ties, "one_sided_exact_p": float(p)}


def summary(rows: list[dict], key: str) -> dict:
    ranks = np.asarray([row[key] for row in rows], dtype=np.float64)
    return {
        "cases": len(rows),
        "mean_normalized_rank": float(((ranks - 1) / 209).mean()),
        "median_rank": float(np.median(ranks)),
        "top5": float(np.mean(ranks <= 5)),
        "top10": float(np.mean(ranks <= 10)),
    }


def compare(rows: list[dict], other_key: str) -> dict:
    full = np.asarray([row["rank_full"] for row in rows], dtype=np.float64)
    other = np.asarray([row[other_key] for row in rows], dtype=np.float64)
    per_context = {}
    nonreverse = True
    for context in CONTEXTS:
        mask = np.asarray([row["context"] == context for row in rows])
        delta = float((full[mask] - other[mask]).mean() / 209)
        per_context[str(context)] = {"mean_normalized_rank_delta": delta, "nonreverse": delta <= 0}
        nonreverse &= delta <= 0
    full_mean = float(((full - 1) / 209).mean())
    other_mean = float(((other - 1) / 209).mean())
    test = sign_test(full, other)
    return {
        "full_mean_normalized_rank": full_mean,
        "comparator_mean_normalized_rank": other_mean,
        "delta": full_mean - other_mean,
        "sign_test": test,
        "per_context": per_context,
        "pass": bool(full_mean < other_mean and test["one_sided_exact_p"] <= 0.01 and nonreverse),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"FRESH_NATIVE_REFUSE_OVERWRITE:{args.output}")
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    if prereg.get("contract") != "CTT_H01_FRESH_NATIVE_SOURCE_ORDERING_DIAGNOSTIC_V1":
        raise SystemExit("FRESH_NATIVE_PREREGISTRATION_FAIL")
    bank = json.loads((args.bank / "bank_summary.json").read_text(encoding="utf-8"))
    if bank.get("verdict") != "CTT_H01_FRESH_BANK_MATERIALIZATION_PASS" or bank.get("file_count") != 6720:
        raise SystemExit("FRESH_NATIVE_BANK_CONTRACT_FAIL")
    carriers = load_carriers(args.support)
    stops = load_stops(args.schedule)
    args.output.mkdir(parents=True)
    labels = np.empty((4, 8, SOURCE_COUNT, STOP_COUNT), dtype=np.int16)
    tapes = np.empty((4, 2, SOURCE_COUNT, STOP_COUNT, STOP_SAMPLES), dtype=np.bool_)
    for ci, context in enumerate(CONTEXTS):
        for member in range(8):
            for source, carrier in enumerate(carriers):
                path = args.bank / f"context_{context:02d}" / f"member_{member:02d}" / f"{carrier['id']}.bin"
                member_labels, member_tapes = labels_tapes(path, stops)
                labels[ci, member, source] = member_labels
                if member in OBSERVATION_MEMBERS:
                    tapes[ci, member - 6, source] = member_tapes
        print(f"FRESH_NATIVE_LOAD_CONTEXT={context} PASS", flush=True)
    rows = []
    for ci, context in enumerate(CONTEXTS):
        predictive = labels[ci, :6]
        predictive_cdf = cdf(predictive)
        for oi, member in enumerate(OBSERVATION_MEMBERS):
            for truth, carrier in enumerate(carriers):
                observed = labels[ci, member, truth]
                shuffled = time_permute(tapes[ci, oi, truth], context, member, truth)
                full = full_distance(predictive_cdf, observed)
                survival = survival_distance(predictive, observed)
                permuted = full_distance(predictive_cdf, shuffled)
                rows.append({
                    "context": context,
                    "observation_member": member,
                    "truth_source": truth,
                    "truth_id": carrier["id"],
                    "rank_full": midrank(full, truth),
                    "rank_survival": midrank(survival, truth),
                    "rank_time_permute": midrank(permuted, truth),
                    "distance_true_full": float(full[truth]),
                    "distance_true_survival": float(survival[truth]),
                    "distance_true_time_permute": float(permuted[truth]),
                })
        print(f"FRESH_NATIVE_SCORE_CONTEXT={context} PASS", flush=True)
    with (args.output / "CASES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summaries = {key: summary(rows, key) for key in ("rank_full", "rank_survival", "rank_time_permute")}
    vs_survival = compare(rows, "rank_survival")
    vs_time = compare(rows, "rank_time_permute")
    verdict = "FRESH_NATIVE_SOURCE_ORDERING_PASS" if vs_survival["pass"] and vs_time["pass"] else "FRESH_NATIVE_SOURCE_ORDERING_NO_GO"
    report = {
        "contract": prereg["contract"],
        "diagnostic_only": True,
        "closed_loop_authorized": False,
        "case_count": len(rows),
        "summary": summaries,
        "full_vs_survival": vs_survival,
        "full_vs_time_permute": vs_time,
        "verdict": verdict,
        "input_hashes": {
            "preregistration": sha256_file(args.preregistration),
            "bank_summary": sha256_file(args.bank / "bank_summary.json"),
            "bank_manifest": sha256_file(args.bank / "FILE_SHA256.tsv"),
            "support": sha256_file(args.support),
            "schedule": sha256_file(args.schedule),
        },
    }
    (args.output / "SUMMARY.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "VERDICT.txt").write_text(verdict + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
