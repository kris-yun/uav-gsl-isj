#!/usr/bin/env python3
"""Source-blind first-passage / TPT necessary-phenomenon screen.

Scores are constructed without source truth. Truth is optional and is used only
for post-hoc evaluation of frozen candidate scores.
"""
import argparse
import csv
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path

HIT_THRESHOLD = 0.1
INTERNAL_STEPS = 200
MIN_UNIQUE_HIT_CELLS = 3
NULL_REPEATS = 200
NULL_SEED = 20260923


def midranks(values, reverse=False):
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=reverse)
    ranks = [0.0] * len(values)
    pos = 0
    while pos < len(order):
        end = pos + 1
        v = values[order[pos]]
        while end < len(order) and values[order[end]] == v:
            end += 1
        r = ((pos + 1) + end) / 2.0
        for k in range(pos, end):
            ranks[order[k]] = r
        pos = end
    return ranks


def pearson(a, b):
    if len(a) != len(b) or len(a) < 2:
        return float("nan")
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    va = sum(x * x for x in da)
    vb = sum(x * x for x in db)
    if va <= 0 or vb <= 0:
        return 0.0
    return sum(x * y for x, y in zip(da, db)) / math.sqrt(va * vb)


def spearman(a, b):
    return pearson(midranks(a), midranks(b))


def parse_timing(run_dir):
    path = run_dir / "context_bank" / "source_update_timing.csv"
    rows = list(csv.DictReader(path.open(newline="")))
    if len(rows) != 1 or rows[0]["source_update_id"] != "1":
        raise RuntimeError("expected exactly source_update_id=1")
    return rows[0]


def parse_observed_blocks(run_dir, cutoff_epoch):
    log = run_dir / "launch.log"
    position = None
    blocks = []
    epoch_re = re.compile(r"\[([0-9]+\.[0-9]+)\]")
    start_re = re.compile(r"Start=\(([-+0-9.eE]+),([-+0-9.eE]+)\)")
    goal_re = re.compile(r"Sending goal \(([-+0-9.eE]+),\s*([-+0-9.eE]+)\)")
    gas_re = re.compile(r"avg_gas=([-+0-9.eE]+);")
    for line in log.read_text(errors="replace").splitlines():
        em = epoch_re.search(line)
        if em and float(em.group(1)) > cutoff_epoch:
            break
        sm = start_re.search(line)
        if sm:
            position = (float(sm.group(1)), float(sm.group(2)))
        gm = goal_re.search(line)
        if gm:
            position = (float(gm.group(1)), float(gm.group(2)))
        cm = gas_re.search(line)
        if cm:
            if position is None:
                raise RuntimeError("gas block appears before a known robot position")
            blocks.append((position[0], position[1], float(cm.group(1))))
    if not blocks:
        raise RuntimeError("no causal StopAndMeasure blocks found before source update")
    return blocks


def parse_grid(run_dir):
    path = run_dir / "context_bank" / "source_update_0001" / "measured_hit_probability.csv"
    rows = list(csv.DictReader(path.open(newline="")))
    free = []
    by_cell = {}
    for row in rows:
        if row["occupancy"] != "Free":
            continue
        cell = int(row["cell_index"])
        item = (cell, float(row["x"]), float(row["y"]))
        free.append(item)
        by_cell[cell] = item[1:]
    if not free:
        raise RuntimeError("no free grid cells")
    return free, by_cell


def map_blocks_to_cells(blocks, free_cells, cell_size):
    mapped = []
    max_error = 0.0
    for x, y, gas in blocks:
        cell, cx, cy = min(
            free_cells,
            key=lambda z: (z[1] - x) ** 2 + (z[2] - y) ** 2,
        )
        err = math.hypot(cx - x, cy - y)
        max_error = max(max_error, err)
        mapped.append((cell, gas, err))
    if max_error > cell_size * 0.51:
        raise RuntimeError(f"measurement-to-grid mapping error too large: {max_error}")
    return mapped, max_error


def parse_candidates(run_dir):
    path = run_dir / "context_bank" / "source_update_0001" / "candidate_manifest.csv"
    rows = list(csv.DictReader(path.open(newline="")))
    out = {}
    for row in rows:
        cid = row["candidate_id"]
        if cid in out:
            raise RuntimeError("duplicate candidate_id")
        out[cid] = {
            "x": int(row["origin_i"]),
            "y": int(row["origin_j"]),
            "w": int(row["size_i"]),
            "h": int(row["size_j"]),
            "source_x": float(row["native_source_x"]),
            "source_y": float(row["native_source_y"]),
            "native_score": float(row["native_score"]),
        }
    return out


def terminal_ids(candidates):
    ids = list(candidates)
    terminal = set()
    for cid in ids:
        c = candidates[cid]
        child = False
        area = c["w"] * c["h"]
        for oid in ids:
            if oid == cid:
                continue
            o = candidates[oid]
            oarea = o["w"] * o["h"]
            if (
                oarea < area
                and o["x"] >= c["x"]
                and o["y"] >= c["y"]
                and o["x"] + o["w"] <= c["x"] + c["w"]
                and o["y"] + o["h"] <= c["y"] + c["h"]
            ):
                child = True
                break
        if not child:
            terminal.add(cid)
    return terminal


def read_target_occupancy(trace_csv, candidates, target_cells):
    target = set(target_cells)
    counts = {cid: defaultdict(int) for cid in candidates}
    first = {cid: {} for cid in candidates}
    seen_candidates = set()
    with trace_csv.open(newline="") as stream:
        for row in csv.DictReader(stream):
            cid = row["candidate_id"]
            if cid not in candidates:
                raise RuntimeError(f"unknown trace candidate {cid}")
            seen_candidates.add(cid)
            t = int(row["internal_timestep"])
            cell = int(row["cell_index"])
            if not 1 <= t <= INTERNAL_STEPS:
                raise RuntimeError("invalid internal timestep")
            if cell not in target:
                continue
            counts[cid][cell] += 1
            prev = first[cid].get(cell)
            if prev is None or t < prev:
                first[cid][cell] = t
    if seen_candidates != set(candidates):
        missing = sorted(set(candidates) - seen_candidates)
        raise RuntimeError(f"trace missing candidates: {missing[:5]}")
    for cid in candidates:
        for cell, k in counts[cid].items():
            if k > INTERNAL_STEPS:
                raise RuntimeError(f"duplicate same-cell occupancy within step suspected: {cid} {cell} {k}")
    return counts, first


def passage_score(first_by_cell, target_cells):
    if not target_cells:
        return 0.0
    total = 0.0
    for cell in target_cells:
        t = first_by_cell.get(cell)
        if t is not None:
            total += (INTERNAL_STEPS + 1 - t) / INTERNAL_STEPS
    return total / len(target_cells)


def static_score(count_by_cell, target_cells):
    if not target_cells:
        return 0.0
    return sum(count_by_cell.get(cell, 0) / INTERNAL_STEPS for cell in target_cells) / len(target_cells)


def geometry_score(candidate, target_cells, by_cell):
    if not target_cells:
        return 0.0
    sx, sy = candidate["source_x"], candidate["source_y"]
    return -sum(math.hypot(sx - by_cell[c][0], sy - by_cell[c][1]) for c in target_cells) / len(target_cells)


def score_candidates(candidates, counts, first, target_cells, by_cell):
    result = {}
    for cid, candidate in candidates.items():
        result[cid] = {
            "passage_auc": passage_score(first[cid], target_cells),
            "static_occupancy": static_score(counts[cid], target_cells),
            "geometry": geometry_score(candidate, target_cells, by_cell),
            "reach_fraction": sum(1 for c in target_cells if c in first[cid]) / len(target_cells) if target_cells else 0.0,
        }
    return result


def evaluate(scores, candidates, terminals, truth_x, truth_y, field):
    ids = sorted(terminals)
    vals = [scores[cid][field] for cid in ids]
    distances = [
        math.hypot(candidates[cid]["source_x"] - truth_x, candidates[cid]["source_y"] - truth_y)
        for cid in ids
    ]
    truth_index = min(range(len(ids)), key=lambda i: distances[i])
    ranks = midranks(vals, reverse=True)
    rank = ranks[truth_index]
    percentile = 0.0 if len(ids) == 1 else (rank - 1.0) / (len(ids) - 1.0)
    return {
        "truth_nearest_candidate": ids[truth_index],
        "truth_nearest_distance_m": distances[truth_index],
        "rank": rank,
        "candidate_count": len(ids),
        "rank_percentile": percentile,
        "spearman_score_vs_negative_truth_distance": spearman(vals, [-d for d in distances]),
    }


def null_first_passage_scores(candidates, counts, target_cells, by_cell, rng):
    scores = {}
    for cid, candidate in candidates.items():
        synthetic_first = {}
        for cell in target_cells:
            k = counts[cid].get(cell, 0)
            if k:
                synthetic_first[cell] = min(rng.sample(range(1, INTERNAL_STEPS + 1), k))
        scores[cid] = {
            "passage_auc": passage_score(synthetic_first, target_cells),
            "static_occupancy": static_score(counts[cid], target_cells),
            "geometry": geometry_score(candidate, target_cells, by_cell),
            "reach_fraction": sum(1 for c in target_cells if c in synthetic_first) / len(target_cells),
        }
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--trace-csv", type=Path, required=True)
    ap.add_argument("--candidate-csv-out", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--truth-x", type=float)
    ap.add_argument("--truth-y", type=float)
    args = ap.parse_args()
    if (args.truth_x is None) != (args.truth_y is None):
        raise SystemExit("truth-x and truth-y must be supplied together")

    timing = parse_timing(args.run_dir)
    cell_size = float(timing["cell_size"])
    blocks = parse_observed_blocks(args.run_dir, float(timing["wall_start_epoch"]))
    free_cells, by_cell = parse_grid(args.run_dir)
    mapped, max_map_error = map_blocks_to_cells(blocks, free_cells, cell_size)
    hit_cells = sorted({cell for cell, gas, _ in mapped if gas > HIT_THRESHOLD})
    miss_cells = sorted({cell for cell, gas, _ in mapped if gas <= HIT_THRESHOLD})
    candidates = parse_candidates(args.run_dir)
    terminals = terminal_ids(candidates)
    counts, first = read_target_occupancy(args.trace_csv, candidates, hit_cells)
    scores = score_candidates(candidates, counts, first, hit_cells, by_cell)

    args.candidate_csv_out.parent.mkdir(parents=True, exist_ok=True)
    with args.candidate_csv_out.open("w", newline="") as stream:
        fields = [
            "candidate_id", "terminal_leaf", "source_x", "source_y", "native_score",
            "passage_auc", "static_occupancy", "geometry", "reach_fraction",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for cid in sorted(candidates):
            c, s = candidates[cid], scores[cid]
            writer.writerow({
                "candidate_id": cid,
                "terminal_leaf": int(cid in terminals),
                "source_x": c["source_x"],
                "source_y": c["source_y"],
                "native_score": c["native_score"],
                **s,
            })

    result = {
        "contract": "TPT_FIRST_PASSAGE_NECESSARY_PHENOMENON_V1",
        "source_blind_score_construction": True,
        "hit_threshold_ppm": HIT_THRESHOLD,
        "internal_steps": INTERNAL_STEPS,
        "internal_dt_s": 0.2,
        "measurement_block_count": len(mapped),
        "hit_block_count": sum(gas > HIT_THRESHOLD for _, gas, _ in mapped),
        "unique_hit_cell_count": len(hit_cells),
        "unique_miss_cell_count": len(miss_cells),
        "hit_cells": hit_cells,
        "max_measurement_to_grid_error_m": max_map_error,
        "candidate_count": len(candidates),
        "terminal_candidate_count": len(terminals),
        "eligible_positive_reactive_target": len(hit_cells) >= MIN_UNIQUE_HIT_CELLS,
        "primary_score": "mean discrete first-arrival coverage AUC over unique causal hit cells",
        "static_control": "mean 200-step occupancy frequency over the same hit cells",
        "geometry_control": "negative mean source-point distance to the same hit-cell centers",
        "null": "within candidate/cell timestamp randomization preserving exact 200-step occupancy count",
    }

    if args.truth_x is not None:
        evals = {
            field: evaluate(scores, candidates, terminals, args.truth_x, args.truth_y, field)
            for field in ("passage_auc", "static_occupancy", "geometry")
        }
        result["truth_used_for_score"] = False
        result["evaluation"] = evals
        if len(hit_cells) >= MIN_UNIQUE_HIT_CELLS:
            rng = random.Random(NULL_SEED)
            null_rank_pct = []
            null_rho = []
            for _ in range(NULL_REPEATS):
                ns = null_first_passage_scores(candidates, counts, hit_cells, by_cell, rng)
                ev = evaluate(ns, candidates, terminals, args.truth_x, args.truth_y, "passage_auc")
                null_rank_pct.append(ev["rank_percentile"])
                null_rho.append(ev["spearman_score_vs_negative_truth_distance"])
            real = evals["passage_auc"]
            p_rank = sum(x <= real["rank_percentile"] for x in null_rank_pct) / NULL_REPEATS
            p_rho = sum(x >= real["spearman_score_vs_negative_truth_distance"] for x in null_rho) / NULL_REPEATS
            temporal_better_static = (
                real["rank_percentile"] < evals["static_occupancy"]["rank_percentile"]
                and real["spearman_score_vs_negative_truth_distance"] > evals["static_occupancy"]["spearman_score_vs_negative_truth_distance"]
            )
            temporal_better_geometry = (
                real["rank_percentile"] < evals["geometry"]["rank_percentile"]
                and real["spearman_score_vs_negative_truth_distance"] > evals["geometry"]["spearman_score_vs_negative_truth_distance"]
            )
            result["time_order_null"] = {
                "repeats": NULL_REPEATS,
                "seed": NULL_SEED,
                "fraction_null_rank_as_good_or_better": p_rank,
                "fraction_null_rho_as_good_or_better": p_rho,
            }
            result["single_run_mechanism_pass"] = bool(
                temporal_better_static
                and temporal_better_geometry
                and p_rank <= 0.05
                and p_rho <= 0.05
            )
        else:
            result["single_run_mechanism_pass"] = False
            result["ineligible_reason"] = "fewer than three unique causal hit cells"

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
