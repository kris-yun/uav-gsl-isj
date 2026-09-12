#!/usr/bin/env python3
"""Evaluator-only diagnosis after the frozen H03 quadrature NO-GO.

This does not select an online model or tune a score. It checks two fixed
questions: whether the logged H03 response supports its source-containing
region, and whether the simplest d log(1+c) transfer rescues the old H01
same-provider two-source counterexample.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

H03_TRUTH = (-0.45, 1.90)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def clip(value: float) -> float:
    return min(1.0 - 1e-4, max(1e-4, value))


def logit(value: float) -> float:
    value = clip(value)
    return math.log(value) - math.log1p(-value)


def component_parts(rows: list[dict]) -> dict:
    previous = 0.0
    hit_ll = miss_ll = 0.0
    hits = zero_hits = clipped_hits = 0
    for row in sorted(rows, key=lambda item: int(item["event_index"])):
        prior = 0.5 * math.erfc(
            (math.log1p(float(row["threshold"])) - math.log1p(previous)) / math.sqrt(2.0)
        )
        eta = logit(prior) + logit(float(row["legacy_hit_probability"])) - logit(float(row["context_value"]))
        probability = clip(1.0 / (1.0 + math.exp(-eta)))
        if int(row["observed_hit"]):
            hits += 1
            raw = float(row["legacy_hit_probability"])
            zero_hits += raw == 0.0
            clipped_hits += raw <= 1e-4
            hit_ll += math.log(probability)
        else:
            miss_ll += math.log1p(-probability)
        previous = float(row["concentration"])
    return {"positive_events": hits, "positive_raw_probability_zero": zero_hits,
            "positive_raw_probability_at_or_below_clip": clipped_hits,
            "hit_log_likelihood": hit_ll, "miss_log_likelihood": miss_ll,
            "total_log_likelihood": hit_ll + miss_ll}


def h03_support(context: Path) -> dict:
    timing_path = context / "source_update_timing.csv"
    score_path = context / "source_point_component_scores.csv"
    event_path = context / "contrastive_source_point_event_attribution.csv"
    timing = {int(row["source_update_id"]): row for row in csv_rows(timing_path)}
    scores: dict[tuple[int, str], dict[int, dict]] = defaultdict(dict)
    for row in csv_rows(score_path):
        scores[(int(row["source_update_id"]), row["candidate_id"])][int(row["source_point_index"])] = row
    events: dict[tuple[int, str, int], list[dict]] = defaultdict(list)
    for row in csv_rows(event_path):
        events[(int(row["source_update_id"]), row["candidate_id"], int(row["source_point_index"]))].append(row)
    updates = []
    for update, meta in sorted(timing.items()):
        size, ox, oy = (float(meta[key]) for key in ("cell_size", "origin_x", "origin_y"))
        truth_i = math.floor((H03_TRUTH[0] - ox) / size)
        truth_j = math.floor((H03_TRUTH[1] - oy) / size)
        candidates = []
        for (candidate_update, candidate), points in scores.items():
            if candidate_update != update:
                continue
            row = points[0]
            i, j, w, h = (int(row[key]) for key in ("origin_i", "origin_j", "size_i", "size_j"))
            contains = i <= truth_i < i + w and j <= truth_j < j + h
            candidates.append((candidate, float(row["region_mixture_likelihood"]), contains))
        true_candidates = [item for item in candidates if item[2]]
        if len(true_candidates) != 1:
            raise ValueError(f"SOURCE_CONTAINING_PARTITION_NOT_UNIQUE:update={update}:{true_candidates}")
        true_candidate = true_candidates[0]
        false_candidate = max((item for item in candidates if not item[2]), key=lambda item: item[1])
        arms = {}
        for label, candidate in (("source_containing", true_candidate[0]), ("strongest_false", false_candidate[0])):
            point_rows = scores[(update, candidate)]
            arms[label] = {
                "candidate_id": candidate,
                "region_mixture_likelihood": float(point_rows[0]["region_mixture_likelihood"]),
                "points": [
                    {"source_point_index": point, "source_xy": [float(point_rows[point]["source_x"]),
                                                                 float(point_rows[point]["source_y"])],
                     **component_parts(events[(update, candidate, point)])}
                    for point in range(4)
                ],
            }
        ratio = math.log(arms["source_containing"]["region_mixture_likelihood"]) - math.log(
            arms["strongest_false"]["region_mixture_likelihood"])
        updates.append({"source_update_id": update, "event_prefix": len(events[(update, true_candidate[0], 0)]),
                        "truth_grid_ij": [truth_i, truth_j], **arms,
                        "source_minus_false_log_mixture_margin": ratio})
    return {
        "role": "evaluator-only diagnosis; source truth never enters online PMFS",
        "selection": "unique current partition leaf containing the H03 truth cell versus highest region-mixture false leaf",
        "updates": updates,
        "inputs": [{"path": str(path), "sha256": sha(path)} for path in (timing_path, score_path, event_path)],
    }


def first_difference(values: list[float]) -> list[float]:
    transformed = [math.log1p(value) for value in values]
    return [0.0] + [b - a for a, b in zip(transformed, transformed[1:])]


def mse(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("TRACE_LENGTH_MISMATCH")
    return math.fsum((a - b) ** 2 for a, b in zip(left, right)) / len(left)


def h01_derivative(repo: Path) -> dict:
    predictions = {}
    observations = {}
    inputs = []
    for source in ("SA", "SB"):
        prediction_path = repo / f"evidence/cstar_m1_estimated_transport_h01_screen_240s_{source}_trace_v3_20260910.json"
        observed_path = repo / f"evidence/cstar_current_runtime_assets240_20260907/realizations/H01_{source}_fast/measured_history.jsonl"
        raw = json.loads(prediction_path.read_text(encoding="utf-8"))
        candidate = raw["candidates"][0]
        if candidate["candidate"] != source or candidate["status"] != "PREFIX_COMPLETE":
            raise ValueError("UNEXPECTED_PREDICTION_IDENTITY")
        predictions[source] = first_difference([float(value) for value in candidate["sensor_ppm"]])
        observations[source] = first_difference([
            float(json.loads(line)["gas_ppm"]) for line in observed_path.read_text(encoding="utf-8").splitlines()
        ])
        inputs.extend(({"path": str(prediction_path.relative_to(repo)), "sha256": sha(prediction_path)},
                       {"path": str(observed_path.relative_to(repo)), "sha256": sha(observed_path)}))
    cases = []
    for actual, observed in observations.items():
        losses = {candidate: mse(observed, predicted) for candidate, predicted in predictions.items()}
        winner = min(losses, key=losses.get)
        cases.append({"actual": actual, "delta_log1p_mse": losses, "winner": winner, "correct": winner == actual})
    return {
        "transform": "parameter-free first difference of log1p(ppm), including initial zero difference",
        "motivation": "minimal data-processing check inspired by the task-relevant d log(c)/dt signal in Mattingly et al.; not their fitted adaptive kernel",
        "score": "full-prefix mean squared error; fixed before reading winners; not a calibrated likelihood",
        "cases": cases, "correct_count": sum(case["correct"] for case in cases), "case_count": len(cases),
        "inputs": inputs,
        "claim_boundary": "Failure rejects this simplest deterministic transfer only; it does not prove all temporal representations lack information.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--h03-context", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "contract": "M1R_POST_NOGO_INFORMATION_DIAGNOSIS_V1_20260913",
        "status": "DIAGNOSTIC_ONLY_NOT_A_REPAIR",
        "parameter_search": False,
        "h03_quadrature_response_support": h03_support(args.h03_context),
        "h01_minimal_derivative_transfer": h01_derivative(args.repo),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"],
                      "h01_derivative_correct": result["h01_minimal_derivative_transfer"]["correct_count"],
                      "h03_updates": len(result["h03_quadrature_response_support"]["updates"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
