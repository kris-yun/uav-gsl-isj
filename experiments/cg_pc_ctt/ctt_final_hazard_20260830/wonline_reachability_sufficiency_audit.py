#!/usr/bin/env python3
"""No-training diagnostic of online-wind support for source reachability."""

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
    read_wind,
    sensor_forward,
    sha256_file,
)

DEV = tuple(range(10))
FRESH = (10, 11, 12, 13)
PREDICTIVE = tuple(range(6))
OBSERVATION = (6, 7)
SOURCE_COUNT = 210
STOP_COUNT = 10
ROUTE_STREAM = 4


def carriers(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    rows.sort(key=lambda row: int(row["carrier_index"]))
    if len(rows) != SOURCE_COUNT or [int(row["carrier_index"]) for row in rows] != list(range(SOURCE_COUNT)):
        raise ValueError("WONLINE_CARRIER_CONTRACT_FAIL")
    return [row["carrier_id"] for row in rows]


def stop_indices(path: Path) -> list[np.ndarray]:
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
        raise ValueError("WONLINE_STOP_CONTRACT_FAIL")
    return result


def context_path(dev_bank: Path, fresh_bank: Path, context: int) -> Path:
    return (dev_bank if context in DEV else fresh_bank) / f"context_{context:02d}"


def load_winds(dev_bank: Path, fresh_bank: Path) -> dict[int, np.ndarray]:
    result = {}
    for context in DEV + FRESH:
        streams = read_wind(context_path(dev_bank, fresh_bank, context) / "exact_wind_routes.bin")
        if len(streams) != 5:
            raise ValueError(f"WONLINE_WIND_STREAM_FAIL:{context}")
        result[context] = streams[ROUTE_STREAM][:, :2].astype(np.float64)
    return result


def nearest_by_stop(winds: dict[int, np.ndarray], stops: list[np.ndarray], target: int,
                    donors: tuple[int, ...]) -> tuple[list[int], list[float]]:
    selected, distances = [], []
    for idx in stops:
        end = int(idx[-1]) + 1
        target_prefix = winds[target][:end]
        rows = []
        for donor in donors:
            delta = target_prefix - winds[donor][:end]
            rows.append((float(np.sqrt(np.mean(delta * delta))), donor))
        distance, donor = min(rows)
        selected.append(donor); distances.append(distance)
    return selected, distances


def load_events(dev_bank: Path, fresh_bank: Path, ids: list[str], stops: list[np.ndarray]) -> np.ndarray:
    # [context 0..13, member 0..7, source, stop] true iff the stop ever crosses threshold.
    events = np.empty((14, 8, SOURCE_COUNT, STOP_COUNT), dtype=np.bool_)
    for context in DEV + FRESH:
        root = context_path(dev_bank, fresh_bank, context)
        for member in range(8):
            for source, carrier_id in enumerate(ids):
                streams = read_physical(root / f"member_{member:02d}" / f"{carrier_id}.bin")
                measured = sensor_forward(streams[ROUTE_STREAM])
                events[context, member, source] = [bool(np.any(measured[idx] > FIRST_PASSAGE_THRESHOLD_PPM)) for idx in stops]
        print(f"WONLINE_LOAD_CONTEXT={context} PASS", flush=True)
    return events


def rank(distance: np.ndarray, truth: int) -> float:
    target = distance[truth]
    return float(1 + np.count_nonzero(distance < target) + 0.5 * (np.count_nonzero(distance == target) - 1))


def sign_test(left: np.ndarray, right: np.ndarray) -> dict:
    wins = int(np.count_nonzero(left < right)); losses = int(np.count_nonzero(left > right))
    ties = int(np.count_nonzero(left == right)); n = wins + losses
    p = sum(math.comb(n, k) for k in range(wins, n + 1)) / (2 ** n) if n else 1.0
    return {"wins": wins, "losses": losses, "ties": ties, "one_sided_exact_p": float(p)}


def summarize(rows: list[dict], key: str) -> dict:
    values = np.asarray([row[key] for row in rows], dtype=np.float64)
    return {
        "mean_normalized_rank": float(((values - 1) / 209).mean()),
        "median_rank": float(np.median(values)),
        "top5": float(np.mean(values <= 5)),
        "top10": float(np.mean(values <= 10)),
    }


def compare(rows: list[dict], left_key: str, right_key: str) -> dict:
    left = np.asarray([row[left_key] for row in rows], dtype=np.float64)
    right = np.asarray([row[right_key] for row in rows], dtype=np.float64)
    per_context = {}
    nonreverse = True
    for context in FRESH:
        mask = np.asarray([row["context"] == context for row in rows])
        delta = float((left[mask] - right[mask]).mean() / 209)
        per_context[str(context)] = {"mean_normalized_rank_delta": delta, "nonreverse": delta <= 0}
        nonreverse &= delta <= 0
    left_mean = float(((left - 1) / 209).mean()); right_mean = float(((right - 1) / 209).mean())
    test = sign_test(left, right)
    return {
        "left_mean_normalized_rank": left_mean,
        "right_mean_normalized_rank": right_mean,
        "delta": left_mean - right_mean,
        "sign_test": test,
        "per_context": per_context,
        "pass": bool(left_mean < right_mean and test["one_sided_exact_p"] <= 0.01 and nonreverse),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development-bank", type=Path, required=True)
    parser.add_argument("--fresh-bank", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"WONLINE_REFUSE_OVERWRITE:{args.output}")
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    if prereg.get("contract") != "CTT_H01_WONLINE_REACHABILITY_SUFFICIENCY_DIAGNOSTIC_V1":
        raise SystemExit("WONLINE_PREREGISTRATION_FAIL")
    dev_summary = json.loads((args.development_bank / "bank_summary.json").read_text(encoding="utf-8"))
    fresh_summary = json.loads((args.fresh_bank / "bank_summary.json").read_text(encoding="utf-8"))
    if dev_summary.get("verdict") != "CTT_H01_WIND_BANK_MATERIALIZATION_PASS" or dev_summary.get("file_count") != 16800:
        raise SystemExit("WONLINE_DEVELOPMENT_BANK_FAIL")
    if fresh_summary.get("verdict") != "CTT_H01_FRESH_BANK_MATERIALIZATION_PASS" or fresh_summary.get("file_count") != 6720:
        raise SystemExit("WONLINE_FRESH_BANK_FAIL")
    ids = carriers(args.support); stops = stop_indices(args.schedule)
    winds = load_winds(args.development_bank, args.fresh_bank)
    donor_map = {}
    for context in FRESH:
        dev_donor, dev_distance = nearest_by_stop(winds, stops, context, DEV)
        fresh_donor, fresh_distance = nearest_by_stop(winds, stops, context, tuple(x for x in FRESH if x != context))
        donor_map[str(context)] = {
            "development_nearest_by_stop": dev_donor,
            "development_rmse_by_stop": dev_distance,
            "fresh_loco_nearest_by_stop": fresh_donor,
            "fresh_loco_rmse_by_stop": fresh_distance,
        }
    events = load_events(args.development_bank, args.fresh_bank, ids, stops)
    static = events[np.asarray(DEV), :6].mean(axis=(0, 1), dtype=np.float64)  # [source,stop]
    rows = []
    for context in FRESH:
        dev_donors = donor_map[str(context)]["development_nearest_by_stop"]
        fresh_donors = donor_map[str(context)]["fresh_loco_nearest_by_stop"]
        p_oracle = events[context, :6].mean(axis=0, dtype=np.float64)
        p_dev = np.stack([events[dev_donors[stop], :6, :, stop].mean(axis=0) for stop in range(STOP_COUNT)], axis=1)
        p_fresh = np.stack([events[fresh_donors[stop], :6, :, stop].mean(axis=0) for stop in range(STOP_COUNT)], axis=1)
        for member in OBSERVATION:
            for truth in range(SOURCE_COUNT):
                observed = events[context, member, truth].astype(np.float64)
                distances = {
                    "oracle": ((p_oracle - observed[None, :]) ** 2).sum(axis=1),
                    "development_nearest": ((p_dev - observed[None, :]) ** 2).sum(axis=1),
                    "fresh_loco_nearest": ((p_fresh - observed[None, :]) ** 2).sum(axis=1),
                    "static": ((static - observed[None, :]) ** 2).sum(axis=1),
                }
                rows.append({
                    "context": context,
                    "observation_member": member,
                    "truth_source": truth,
                    "rank_oracle": rank(distances["oracle"], truth),
                    "rank_development_nearest": rank(distances["development_nearest"], truth),
                    "rank_fresh_loco_nearest": rank(distances["fresh_loco_nearest"], truth),
                    "rank_static": rank(distances["static"], truth),
                    "brier_true_oracle": float(distances["oracle"][truth] / STOP_COUNT),
                    "brier_true_development_nearest": float(distances["development_nearest"][truth] / STOP_COUNT),
                    "brier_true_fresh_loco_nearest": float(distances["fresh_loco_nearest"][truth] / STOP_COUNT),
                    "brier_true_static": float(distances["static"][truth] / STOP_COUNT),
                })
        print(f"WONLINE_SCORE_CONTEXT={context} PASS", flush=True)
    args.output.mkdir(parents=True)
    with (args.output / "CASES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    rank_keys = ("rank_oracle", "rank_development_nearest", "rank_fresh_loco_nearest", "rank_static")
    development_comparison = compare(rows, "rank_development_nearest", "rank_static")
    fresh_comparison = compare(rows, "rank_fresh_loco_nearest", "rank_static")
    if development_comparison["pass"]:
        verdict = "WONLINE_CURRENT_SUPPORT_USEFUL"
    elif fresh_comparison["pass"]:
        verdict = "WONLINE_DIVERSE_SUPPORT_SIGNAL"
    else:
        verdict = "WONLINE_NO_DEMONSTRATED_SUFFICIENCY"
    report = {
        "contract": prereg["contract"],
        "diagnostic_only": True,
        "closed_loop_authorized": False,
        "cases": len(rows),
        "donor_map": donor_map,
        "summary": {key: summarize(rows, key) for key in rank_keys},
        "development_nearest_vs_static": development_comparison,
        "fresh_loco_nearest_vs_static": fresh_comparison,
        "verdict": verdict,
        "input_hashes": {
            "preregistration": sha256_file(args.preregistration),
            "development_summary": sha256_file(args.development_bank / "bank_summary.json"),
            "fresh_summary": sha256_file(args.fresh_bank / "bank_summary.json"),
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
