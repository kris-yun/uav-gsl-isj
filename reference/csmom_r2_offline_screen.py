#!/usr/bin/env python3
"""Correlation-scale Median-of-Means screen for the frozen TNQC V5 R2 archive.

This is an offline falsification/reproduction tool. It changes only candidate
cell-evidence aggregation. It preserves the exported candidate support, final
quadtree partition, PMFS cell likelihood, softmax posterior construction, and
native 300 s top-5% ExpectedValue endpoint.

Block width is NOT endpoint-tuned:
    B = ceil(2 * kernel_sigma / cell_size)
The frozen R2 runtime has kernel_sigma=0.5 m and cell_size=0.3 m, so B=4.
To remove arbitrary block-origin dependence, all B^2 spatial offsets are
computed and their candidate-level MoM risks are aggregated by the median.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import statistics
from pathlib import Path

CASES = [f"House{h:02d}_seed{s}_off_off" for h in (1, 2, 3) for s in (0, 1)]


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def final_update_id(bank: Path) -> int:
    return max(
        (float(row["sim_time"]), int(row["source_update_id"]))
        for row in read_rows(bank / "source_update_timing.csv")
        if float(row["sim_time"]) <= 300.0 + 1e-9
    )[1]


def source_truth(case_root: Path):
    for path in (case_root / "resolved_runtime").glob("launch_params_*"):
        text = path.read_text(errors="ignore")
        xm = re.search(r"^\s*source_x:\s*([-+0-9.eE]+)", text, re.M)
        ym = re.search(r"^\s*source_y:\s*([-+0-9.eE]+)", text, re.M)
        if xm and ym:
            return float(xm.group(1)), float(ym.group(1))
    raise RuntimeError(f"source truth not found in {case_root}")


def parse_scalar(case_root: Path, key: str) -> float:
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*([-+0-9.eE]+)", re.M)
    for path in (case_root / "resolved_runtime").glob("launch_params_*"):
        match = pattern.search(path.read_text(errors="ignore"))
        if match:
            return float(match.group(1))
    raise RuntimeError(f"runtime parameter {key} not found in {case_root}")


def normalize_logweights(scores):
    maximum = max(scores.values())
    denominator = sum(math.exp(value - maximum) for value in scores.values())
    return {
        key: math.exp(value - maximum) / denominator
        for key, value in scores.items()
    }


def endpoint_metrics(posterior, cells, tx, ty):
    ranked = sorted(
        [(idx, cells[idx][2], cells[idx][3], probability)
         for idx, probability in posterior.items()],
        key=lambda row: (-row[3], row[0]),
    )
    n_top = max(1, math.ceil(0.05 * len(ranked)))
    top = ranked[:n_top]
    mass = sum(row[3] for row in top)
    ex = sum(row[1] * row[3] for row in top) / mass
    ey = sum(row[2] * row[3] for row in top) / mass

    mx = sum(row[1] * row[3] for row in ranked)
    my = sum(row[2] * row[3] for row in ranked)
    variance = sum(
        row[3] * ((row[1] - mx) ** 2 + (row[2] - my) ** 2)
        for row in ranked
    )
    return {
        "top5_error_m": math.hypot(ex - tx, ey - ty),
        "variance_m2": variance,
        "max_cell_probability": max(row[3] for row in ranked),
    }


def load_case(native_root: Path, case: str):
    case_root = native_root / case
    bank = case_root / "context_bank"
    update = bank / f"source_update_{final_update_id(bank):04d}"
    tx, ty = source_truth(case_root)

    cells = {
        int(row["cell_index"]): (
            int(row["grid_i"]),
            int(row["grid_j"]),
            float(row["x"]),
            float(row["y"]),
        )
        for row in read_rows(update / "measured_hit_probability.csv")
        if row["occupancy"] == "Free"
    }
    candidates = {
        row["candidate_id"]: {
            "origin_i": int(row["origin_i"]),
            "origin_j": int(row["origin_j"]),
            "size_i": int(row["size_i"]),
            "size_j": int(row["size_j"]),
        }
        for row in read_rows(update / "candidate_manifest.csv")
    }
    alignment = {}
    for row in read_rows(update / "candidate_support_alignment.csv"):
        cell = int(row["cell_index"])
        if cell not in cells:
            continue
        alignment.setdefault(row["candidate_id"], {})[cell] = (
            float(row["measured_probability"]),
            float(row["measured_confidence"]),
            float(row["simulated_hit_probability"]),
        )

    partition = {}
    for idx, (gi, gj, _, _) in cells.items():
        partition[idx] = min(
            (candidate["size_i"] * candidate["size_j"], cid)
            for cid, candidate in candidates.items()
            if candidate["origin_i"] <= gi < candidate["origin_i"] + candidate["size_i"]
            and candidate["origin_j"] <= gj < candidate["origin_j"] + candidate["size_j"]
        )[1]

    return {
        "case": case,
        "cells": cells,
        "candidates": candidates,
        "alignment": alignment,
        "partition": partition,
        "truth": (tx, ty),
        "cell_size_m": parse_scalar(case_root, "cell_size"),
        "kernel_sigma_m": parse_scalar(case_root, "kernelSigma"),
        "confidence_sigma_spatial_m": parse_scalar(
            case_root, "confidenceSigmaSpatial"
        ),
    }


def cell_loss(value):
    measured, confidence, simulated = value
    likelihood = 1.0 - confidence * abs(measured - simulated)
    if not (likelihood > 0.0):
        raise RuntimeError(f"nonpositive frozen likelihood: {likelihood}")
    return -math.log(likelihood)


def evaluate(data, scorer):
    candidate_scores = {
        cid: scorer(cid, data["alignment"][cid], data["cells"])
        for cid in data["candidates"]
    }
    cell_scores = {
        idx: candidate_scores[cid]
        for idx, cid in data["partition"].items()
    }
    posterior = normalize_logweights(cell_scores)
    tx, ty = data["truth"]
    return endpoint_metrics(posterior, data["cells"], tx, ty)


def native_score(_cid, alignment, _cells):
    return -sum(cell_loss(value) for value in alignment.values())


def correlation_scale_block_width(data):
    return math.ceil(
        2.0 * data["kernel_sigma_m"] / data["cell_size_m"]
    )


def csmom_score(block_width: int):
    def scorer(_cid, alignment, cells):
        offset_risks = []
        for offset_i in range(block_width):
            for offset_j in range(block_width):
                blocks = {}
                for idx, value in alignment.items():
                    gi, gj, _, _ = cells[idx]
                    key = (
                        (gi - offset_i) // block_width,
                        (gj - offset_j) // block_width,
                    )
                    blocks.setdefault(key, []).append(cell_loss(value))
                means = [
                    sum(values) / len(values)
                    for values in blocks.values()
                ]
                offset_risks.append(statistics.median(means))
        robust_risk = statistics.median(offset_risks)
        return -robust_risk * len(alignment)

    return scorer


def random_block_score(cells, block_area: int, seed: int):
    ids = sorted(cells)
    rng = random.Random(seed)
    rng.shuffle(ids)
    assignment = {
        idx: position // block_area
        for position, idx in enumerate(ids)
    }

    def scorer(_cid, alignment, _cells):
        groups = {}
        for idx, value in alignment.items():
            groups.setdefault(assignment[idx], []).append(cell_loss(value))
        means = [
            sum(values) / len(values)
            for values in groups.values()
        ]
        return -statistics.median(means) * len(alignment)

    return scorer


def aggregate(rows):
    errors = [row["top5_error_m"] for row in rows]
    return {
        "mean_top5_error_m": statistics.mean(errors),
        "false_confident_collapse_count": sum(
            row["variance_m2"] < 1.0 and row["top5_error_m"] > 2.0
            for row in rows
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--release-root",
        type=Path,
        required=True,
        help="tnqc_r2_six_offline_20260921_authoritative directory",
    )
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--random-seeds", type=int, default=30)
    args = parser.parse_args()

    native_root = args.release_root / "native"
    data = {
        case: load_case(native_root, case)
        for case in CASES
    }

    widths = {
        case: correlation_scale_block_width(case_data)
        for case, case_data in data.items()
    }
    if set(widths.values()) != {4}:
        raise RuntimeError(
            f"expected frozen 4-cell correlation block, got {widths}"
        )
    block_width = 4

    native_rows = []
    robust_rows = []
    for case in CASES:
        native = evaluate(data[case], native_score)
        robust = evaluate(data[case], csmom_score(block_width))
        native_rows.append({"case": case, **native})
        robust_rows.append({"case": case, **robust})

    native_summary = aggregate(native_rows)
    robust_summary = aggregate(robust_rows)
    native_mean = native_summary["mean_top5_error_m"]
    robust_mean = robust_summary["mean_top5_error_m"]

    random_means = []
    random_collapses = []
    for seed in range(args.random_seeds):
        seed_rows = []
        for case_index, case in enumerate(CASES):
            scorer = random_block_score(
                data[case]["cells"],
                block_width * block_width,
                1000003 * seed + case_index,
            )
            seed_rows.append(evaluate(data[case], scorer))
        summary = aggregate(seed_rows)
        random_means.append(summary["mean_top5_error_m"])
        random_collapses.append(
            summary["false_confident_collapse_count"]
        )

    payload = {
        "contract": "CSMOM_R2_OFFLINE_SCREEN_V1",
        "endpoint": "native 300 s ExpectedValue(sourceProbability,0.05)",
        "block_rule": "ceil(2*kernelSigma/cell_size)",
        "block_width_cells": block_width,
        "block_width_m": (
            block_width * data[CASES[0]]["cell_size_m"]
        ),
        "frozen_runtime_parameters": {
            case: {
                "cell_size_m": case_data["cell_size_m"],
                "kernel_sigma_m": case_data["kernel_sigma_m"],
                "confidence_sigma_spatial_m":
                    case_data["confidence_sigma_spatial_m"],
            }
            for case, case_data in data.items()
        },
        "native": {
            "cases": native_rows,
            **native_summary,
        },
        "csmom": {
            "cases": robust_rows,
            **robust_summary,
            "pooled_improvement_percent":
                100.0 * (native_mean - robust_mean) / native_mean,
            "nonworse_cases": sum(
                robust_rows[i]["top5_error_m"]
                <= native_rows[i]["top5_error_m"] + 1e-12
                for i in range(len(CASES))
            ),
        },
        "random_block_control": {
            "seeds": args.random_seeds,
            "mean_endpoint_m": statistics.mean(random_means),
            "median_endpoint_m": statistics.median(random_means),
            "best_endpoint_m": min(random_means),
            "worst_endpoint_m": max(random_means),
            "mean_improvement_percent":
                100.0 * (
                    native_mean - statistics.mean(random_means)
                ) / native_mean,
            "collapse_count_distribution": {
                str(value): random_collapses.count(value)
                for value in sorted(set(random_collapses))
            },
        },
        "decision":
            "STAGE_2_POSITIVE_MAIN_INNOVATION_CANDIDATE_NOT_CLOSED_LOOP_READY",
        "known_failure":
            "House01_seed0_off_off worsens under CS-MoM",
    }

    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.write_text(
            text + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
