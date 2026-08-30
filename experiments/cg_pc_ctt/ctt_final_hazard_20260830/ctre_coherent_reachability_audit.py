#!/usr/bin/env python3
"""Development-only comparison of coherent versus stopwise transport mixtures."""

from __future__ import annotations

import argparse
import csv
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


def load_carriers(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    carriers = [{"index": int(row["carrier_index"]), "id": row["carrier_id"]} for row in rows]
    carriers.sort(key=lambda row: row["index"])
    if len(carriers) != SOURCE_COUNT or [row["index"] for row in carriers] != list(range(SOURCE_COUNT)):
        raise ValueError("CTRE_CARRIER_CONTRACT_FAIL")
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
        raise ValueError(f"CTRE_STOP_CONTRACT_FAIL:{[len(x) for x in result]}")
    return result


def detection(path: Path, stops: list[np.ndarray]) -> np.ndarray:
    streams = read_physical(path)
    if len(streams) != 5:
        raise ValueError(f"CTRE_STREAM_COUNT_FAIL:{path}")
    measured = sensor_forward(streams[ROUTE_STREAM])
    return np.asarray([
        bool(np.any(measured[idx] > FIRST_PASSAGE_THRESHOLD_PPM))
        for idx in stops
    ], dtype=np.bool_)


def log_mean_exp(values: np.ndarray, axis: int) -> np.ndarray:
    maximum = np.max(values, axis=axis, keepdims=True)
    return np.squeeze(maximum, axis=axis) + np.log(np.mean(np.exp(values - maximum), axis=axis))


def scores(predictive: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # predictive [member, source, stop]. A one-realization Jeffreys posterior
    # predictive maps miss/hit to 0.25/0.75 without a fitted parameter.
    p = (0.5 + predictive.astype(np.float64)) / 2.0
    y = observed.astype(np.float64)
    per_member = (y[None, None, :] * np.log(p) + (1.0 - y[None, None, :]) * np.log1p(-p)).sum(axis=2)
    coherent = log_mean_exp(per_member, axis=0)
    pbar = p.mean(axis=0)
    stopwise = (y[None, :] * np.log(pbar) + (1.0 - y[None, :]) * np.log1p(-pbar)).sum(axis=1)
    return coherent, stopwise


def midrank_desc(value: np.ndarray, truth: int) -> float:
    target = value[truth]
    return float(1 + np.count_nonzero(value > target) + 0.5 * (np.count_nonzero(value == target) - 1))


def sign_test(left: np.ndarray, right: np.ndarray) -> dict:
    wins = int(np.count_nonzero(left < right))
    losses = int(np.count_nonzero(left > right))
    ties = int(np.count_nonzero(left == right))
    count = wins + losses
    p = sum(math.comb(count, k) for k in range(wins, count + 1)) / (2 ** count) if count else 1.0
    return {"wins": wins, "losses": losses, "ties": ties, "one_sided_exact_p": float(p)}


def rank_summary(rows: list[dict], key: str) -> dict:
    rank = np.asarray([row[key] for row in rows], dtype=np.float64)
    return {
        "cases": len(rows),
        "mean_normalized_rank": float(((rank - 1.0) / 209.0).mean()),
        "median_rank": float(np.median(rank)),
        "top5": float(np.mean(rank <= 5)),
        "top10": float(np.mean(rank <= 10)),
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
        raise SystemExit(f"CTRE_REFUSE_OVERWRITE:{args.output}")
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    if prereg.get("contract") != "CTRE_COHERENT_REACHABILITY_DIAGNOSTIC_V1":
        raise SystemExit("CTRE_PREREGISTRATION_FAIL")
    bank_summary = json.loads((args.bank / "bank_summary.json").read_text(encoding="utf-8"))
    if bank_summary.get("verdict") != "CTT_H01_FRESH_BANK_MATERIALIZATION_PASS" or bank_summary.get("file_count") != 6720:
        raise SystemExit("CTRE_BANK_CONTRACT_FAIL")
    carriers = load_carriers(args.support)
    stops = load_stops(args.schedule)
    detected = np.empty((4, 8, SOURCE_COUNT, STOP_COUNT), dtype=np.bool_)
    for ci, context in enumerate(CONTEXTS):
        for member in range(8):
            for source, carrier in enumerate(carriers):
                path = args.bank / f"context_{context:02d}" / f"member_{member:02d}" / f"{carrier['id']}.bin"
                detected[ci, member, source] = detection(path, stops)
        print(f"CTRE_LOAD_CONTEXT={context} PASS", flush=True)
    rows = []
    for ci, context in enumerate(CONTEXTS):
        predictive = detected[ci, :6]
        for member in OBSERVATION_MEMBERS:
            for truth, carrier in enumerate(carriers):
                coherent, stopwise = scores(predictive, detected[ci, member, truth])
                rows.append({
                    "context": context,
                    "observation_member": member,
                    "truth_source": truth,
                    "truth_id": carrier["id"],
                    "rank_coherent": midrank_desc(coherent, truth),
                    "rank_stopwise": midrank_desc(stopwise, truth),
                    "score_true_coherent": float(coherent[truth]),
                    "score_true_stopwise": float(stopwise[truth]),
                })
        print(f"CTRE_SCORE_CONTEXT={context} PASS", flush=True)
    coherent_rank = np.asarray([row["rank_coherent"] for row in rows], dtype=np.float64)
    stopwise_rank = np.asarray([row["rank_stopwise"] for row in rows], dtype=np.float64)
    per_context = {}
    nonreverse = True
    for context in CONTEXTS:
        mask = np.asarray([row["context"] == context for row in rows])
        delta = float((coherent_rank[mask] - stopwise_rank[mask]).mean() / 209.0)
        per_context[str(context)] = {"mean_normalized_rank_delta": delta, "nonreverse": delta <= 0.0}
        nonreverse &= delta <= 0.0
    test = sign_test(coherent_rank, stopwise_rank)
    coherent_summary = rank_summary(rows, "rank_coherent")
    stopwise_summary = rank_summary(rows, "rank_stopwise")
    passed = bool(
        coherent_summary["mean_normalized_rank"] < stopwise_summary["mean_normalized_rank"]
        and test["one_sided_exact_p"] <= 0.01
        and nonreverse
    )
    verdict = "CTRE_COHERENT_REACHABILITY_DIAGNOSTIC_PASS" if passed else "CTRE_COHERENT_REACHABILITY_DIAGNOSTIC_NO_GO"
    args.output.mkdir(parents=True)
    with (args.output / "CASES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "contract": prereg["contract"],
        "diagnostic_only": True,
        "closed_loop_authorized": False,
        "coherent": coherent_summary,
        "stopwise": stopwise_summary,
        "coherent_vs_stopwise": {
            "delta": coherent_summary["mean_normalized_rank"] - stopwise_summary["mean_normalized_rank"],
            "sign_test": test,
            "per_context": per_context,
            "pass": passed,
        },
        "input_hashes": {
            "preregistration": sha256_file(args.preregistration),
            "bank_summary": sha256_file(args.bank / "bank_summary.json"),
            "bank_manifest": sha256_file(args.bank / "FILE_SHA256.tsv"),
            "support": sha256_file(args.support),
            "schedule": sha256_file(args.schedule),
        },
        "verdict": verdict,
    }
    (args.output / "SUMMARY.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "VERDICT.txt").write_text(verdict + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
