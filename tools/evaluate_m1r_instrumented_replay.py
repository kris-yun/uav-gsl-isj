#!/usr/bin/env python3
"""Evaluate passive M0/M1/M2 scores from V4.1 attribution exports."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

TRUTH = {"H01": (-0.4, -2.9), "H02": (0.0, -1.0), "H03": (-0.45, 1.9)}
EPS = 1.0e-4


def clip(value: float) -> float:
    return min(1.0 - EPS, max(EPS, value))


def logit(value: float) -> float:
    value = clip(value)
    return math.log(value) - math.log1p(-value)


def expit(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def score_candidate(rows: list[dict]) -> dict:
    previous = 0.0
    arms = {name: {"nll": 0.0, "brier": 0.0, "log_likelihood": 0.0} for name in ("M0", "M1", "M2")}
    increments = []
    for row in sorted(rows, key=lambda item: int(item["event_index"])):
        threshold_log = math.log1p(float(row["threshold"]))
        persistence = 0.5 * math.erfc((threshold_log - math.log1p(previous)) / math.sqrt(2.0))
        p_sim = clip(float(row["legacy_hit_probability"]))
        p_context = clip(float(row["context_value"]))
        probabilities = {
            "M0": clip(persistence),
            "M1": clip(expit(logit(persistence) + logit(p_sim))),
            "M2": clip(expit(logit(persistence) + logit(p_sim) - logit(p_context))),
        }
        outcome = int(row["observed_hit"])
        event_scores = {}
        for arm, probability in probabilities.items():
            ll = math.log(probability if outcome else 1.0 - probability)
            arms[arm]["log_likelihood"] += ll
            arms[arm]["nll"] -= ll
            arms[arm]["brier"] += (probability - outcome) ** 2
            event_scores[arm] = ll
        increments.append(
            {
                "event_index": int(row["event_index"]),
                "sim_time_s": float(row["sim_time_s"]),
                "observed_hit": outcome,
                "persistence": probabilities["M0"],
                "p_sim": p_sim,
                "p_context": p_context,
                "m2_minus_m1_log_score": event_scores["M2"] - event_scores["M1"],
            }
        )
        previous = float(row["concentration"])
    count = len(rows)
    for values in arms.values():
        values["mean_nll"] = values["nll"] / count
        values["mean_brier"] = values["brier"] / count
    return {"event_count": count, "arms": arms, "increments": increments}


def evaluate_house(run_root: Path, house: str) -> dict:
    run_dir = run_root / f"{house}_seed12_M1R"
    attribution = run_dir / "context_bank/contrastive_event_attribution.csv"
    if not attribution.is_file():
        raise FileNotFoundError(attribution)
    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    coordinates = {}
    with attribution.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if int(row["member_index"]) != 0:
                continue
            key = (int(row["source_update_id"]), row["candidate_id"])
            grouped[key].append(row)
            coordinates[key] = (float(row["candidate_x"]), float(row["candidate_y"]))
    updates = {}
    truth = TRUTH[house]
    for update_id in sorted({key[0] for key in grouped}):
        keys = [key for key in grouped if key[0] == update_id]
        scored = {key[1]: score_candidate(grouped[key]) for key in keys}
        true_key = min(keys, key=lambda key: math.hypot(coordinates[key][0] - truth[0], coordinates[key][1] - truth[1]))
        true_id = true_key[1]
        true_xy = coordinates[true_key]
        arm_summaries = {}
        for arm in ("M0", "M1", "M2"):
            ordered = sorted(
                ((cid, values["arms"][arm]["log_likelihood"]) for cid, values in scored.items()),
                key=lambda item: (-item[1], item[0]),
            )
            true_score = scored[true_id]["arms"][arm]["log_likelihood"]
            rank = next(index for index, item in enumerate(ordered, 1) if item[0] == true_id)
            false = next((item for item in ordered if item[0] != true_id), None)
            arm_summaries[arm] = {
                **scored[true_id]["arms"][arm],
                "true_source_rank": rank,
                "candidate_count": len(ordered),
                "top_false_candidate": false[0] if false else None,
                "true_minus_top_false_log_margin": true_score - false[1] if false else None,
            }
        increments = scored[true_id]["increments"]
        split = max(1, len(increments) // 2)
        updates[str(update_id)] = {
            "true_candidate_id": true_id,
            "true_candidate_xy": list(true_xy),
            "true_candidate_distance_to_source_m": math.hypot(true_xy[0] - truth[0], true_xy[1] - truth[1]),
            "arms": arm_summaries,
            "contrast_true_log_score": {
                "total_m2_minus_m1": sum(row["m2_minus_m1_log_score"] for row in increments),
                "early_half": sum(row["m2_minus_m1_log_score"] for row in increments[:split]),
                "late_half": sum(row["m2_minus_m1_log_score"] for row in increments[split:]),
                "wrong_sign_event_count": sum(row["m2_minus_m1_log_score"] < 0 for row in increments),
                "event_count": len(increments),
            },
            "true_candidate_event_components": increments,
        }
    return {"house": house, "updates": updates}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "contract": "M1R_NEW_INSTRUMENTED_DEVELOPMENT_REPLICATION_V41",
        "evidence_label": "NEW_INSTRUMENTED_DEVELOPMENT_REPLICATION",
        "historical_exact_replay": False,
        "houses": {house: evaluate_house(args.run_root, house) for house in TRUTH},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
