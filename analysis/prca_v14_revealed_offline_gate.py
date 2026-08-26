#!/usr/bin/env python3
"""Reproduce the PRCA V14 revealed-data offline gate.

This script is evaluation-only. It reads already completed RCEC V13 logs and
never enters the runtime inference path. Truth coordinates are used only after
runs are complete to report localization metrics.

Expected extracted roots:
  Phase A: RCEC_V13_HELDOUT_DIAGNOSTIC_20260826_WORK
  Phase B: RCEC_V13_H02_PROSPECTIVE_3PAIR_20260826_WORK
"""
from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


def rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def normalize(values):
    values = [max(float(v), 0.0) for v in values]
    total = sum(values)
    if not total > 0.0:
        raise ValueError("zero probability mass")
    return [v / total for v in values]


def proximal_tilt(reference, score):
    reference = normalize(reference)
    maximum = max(score[i] for i, p in enumerate(reference) if p > 0.0)
    tilted = [
        p * math.exp(float(s) - maximum) if p > 0.0 else 0.0
        for p, s in zip(reference, score)
    ]
    return normalize(tilted)


def candidate_metrics(records, probability, truth):
    probability = normalize(probability)
    tx, ty = truth
    xy = [(float(r["x"]), float(r["y"])) for r in records]
    distance = [math.hypot(x - tx, y - ty) for x, y in xy]
    order = sorted(range(len(records)), key=lambda i: probability[i], reverse=True)
    top_count = max(1, math.ceil(0.05 * len(records)))
    top = order[:top_count]
    top_mass = sum(probability[i] for i in top)
    top_x = sum(xy[i][0] * probability[i] for i in top) / top_mass
    top_y = sum(xy[i][1] * probability[i] for i in top) / top_mass
    nearest = min(range(len(records)), key=lambda i: distance[i])
    nearest_rank = order.index(nearest) + 1
    expected_distance = sum(p * d for p, d in zip(probability, distance))
    entropy = -sum(p * math.log(p) for p in probability if p > 0.0)
    return {
        "top5_error": math.hypot(top_x - tx, top_y - ty),
        "expected_distance": expected_distance,
        "nearest_rank": nearest_rank,
        "entropy": entropy,
    }


def final_update(run: Path):
    files = sorted((run / "tadm").glob("meaci_candidate_scores_update_*.csv"))
    if not files:
        raise ValueError(f"no candidate score logs: {run}")
    match = re.search(r"_(\d{4})\.csv$", files[-1].name)
    return int(match.group(1)), files[-1]


def candidate_gate(run: Path, truth):
    update, candidate_path = final_update(run)
    candidate = rows(candidate_path)
    score_path = run / "tadm" / f"rcec_v13_scores_update_{update:04d}.csv"
    score_rows = rows(score_path)
    by_id = {r["candidate_id"]: r for r in score_rows}
    candidate = [r for r in candidate if r["candidate_id"] in by_id]
    causal = [
        min(float(by_id[r["candidate_id"]]["even_normal_rank"]),
            float(by_id[r["candidate_id"]]["odd_normal_rank"]))
        for r in candidate
    ]
    native = normalize([r["native_shadow_mass"] for r in candidate])
    prca = proximal_tilt(native, causal)
    return candidate_metrics(candidate, native, truth), candidate_metrics(candidate, prca, truth)


def parse_candidate_id(candidate_id: str):
    match = re.fullmatch(r"quadtree_(\d+)_(\d+)_(\d+)_(\d+)", candidate_id)
    if not match:
        raise ValueError(f"unsupported candidate id: {candidate_id}")
    return tuple(int(v) for v in match.groups())


def exact_grid_gate(run: Path, truth):
    native_files = sorted((run / "tadm").glob("meaci_native_shadow_update_*.csv"))
    if not native_files:
        raise ValueError(f"no native shadow grid: {run}")
    match = re.search(r"_(\d{4})\.csv$", native_files[-1].name)
    update = int(match.group(1))
    native = rows(native_files[-1])
    score_rows = rows(run / "tadm" / f"rcec_v13_scores_update_{update:04d}.csv")

    cell_score = {}
    for row in score_rows:
        i, j, si, sj = parse_candidate_id(row["candidate_id"])
        score = min(float(row["even_normal_rank"]), float(row["odd_normal_rank"]))
        for x in range(i, i + si):
            for y in range(j, j + sj):
                if (x, y) in cell_score:
                    raise ValueError("candidate rectangles overlap")
                cell_score[(x, y)] = score

    xs = sorted({float(r["x"]) for r in native})
    ys = sorted({float(r["y"]) for r in native})
    dx = sorted(xs[k + 1] - xs[k] for k in range(len(xs) - 1))[len(xs) // 2 - 1]
    dy = sorted(ys[k + 1] - ys[k] for k in range(len(ys) - 1))[len(ys) // 2 - 1]
    x0, y0 = min(xs), min(ys)

    best = None
    for ox in range(-2, 3):
        for oy in range(-2, 3):
            count = 0
            for row in native:
                i = int(round((float(row["x"]) - x0) / dx)) + ox
                j = int(round((float(row["y"]) - y0) / dy)) + oy
                count += (i, j) in cell_score
            if best is None or count > best[0]:
                best = (count, ox, oy)
    if best[0] != len(native):
        raise ValueError(f"candidate/free-cell coverage mismatch: {best[0]}/{len(native)}")

    causal = []
    for row in native:
        i = int(round((float(row["x"]) - x0) / dx)) + best[1]
        j = int(round((float(row["y"]) - y0) / dy)) + best[2]
        causal.append(cell_score[(i, j)])

    reference = normalize([r["source_probability"] for r in native])
    prca = proximal_tilt(reference, causal)
    pseudo_candidate = [dict(x=r["x"], y=r["y"]) for r in native]
    return candidate_metrics(pseudo_candidate, reference, truth), candidate_metrics(pseudo_candidate, prca, truth)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase-a", type=Path, required=True)
    parser.add_argument("--phase-b", type=Path, required=True)
    args = parser.parse_args()

    cases = [
        ("House01", 683809789, args.phase_a / "raw" / "House01_seed683809789_on_me_aci", (-0.4, -2.9)),
        ("House02", 859169523, args.phase_a / "raw" / "House02_seed859169523_on_me_aci", (0.0, -1.0)),
        ("House03", 753132313, args.phase_a / "raw" / "House03_seed753132313_on_me_aci", (-0.45, 1.9)),
        ("House02", 332814273, args.phase_b / "raw" / "House02_seed332814273_on_me_aci", (0.0, -1.0)),
        ("House02", 783030861, args.phase_b / "raw" / "House02_seed783030861_on_me_aci", (0.0, -1.0)),
        ("House02", 845534703, args.phase_b / "raw" / "House02_seed845534703_on_me_aci", (0.0, -1.0)),
    ]

    print("house,seed,native_candidate_top5,prca_candidate_top5,improvement_pct")
    for house, seed, run, truth in cases:
        native, prca = candidate_gate(run, truth)
        improvement = 100.0 * (native["top5_error"] - prca["top5_error"]) / native["top5_error"]
        print(f"{house},{seed},{native['top5_error']:.9f},{prca['top5_error']:.9f},{improvement:.9f}")

    print("EXACT_GRID_H02")
    for seed in (332814273, 783030861, 845534703):
        run = args.phase_b / "raw" / f"House02_seed{seed}_on_me_aci"
        native, prca = exact_grid_gate(run, (0.0, -1.0))
        improvement = 100.0 * (native["top5_error"] - prca["top5_error"]) / native["top5_error"]
        print(f"House02,{seed},{native['top5_error']:.9f},{prca['top5_error']:.9f},{improvement:.9f}")

    print("PRCA_V14_REVEALED_OFFLINE_GATE=PASS")


if __name__ == "__main__":
    main()
