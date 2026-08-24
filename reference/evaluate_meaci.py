#!/usr/bin/env python3
"""External truth evaluator; never imported or called by the online method."""
import argparse
import csv
import json
import math
from pathlib import Path


def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def posterior_metrics(path, tx, ty):
    rr = rows(path)
    xyz = [(float(r["x"]), float(r["y"]), float(r["source_probability"])) for r in rr]
    total = sum(max(p, 0.0) for _, _, p in xyz)
    if not xyz or not total > 0:
        raise ValueError(f"invalid posterior {path}")
    xyz = [(x, y, max(p, 0.0) / total) for x, y, p in xyz]
    mx = sum(x * p for x, _, p in xyz); my = sum(y * p for _, y, p in xyz)
    mapx, mapy, _ = max(xyz, key=lambda z: z[2])
    # Exact counterpart of PMFS Utils::ExpectedValue(grid, 0.05): sort all
    # free cells by probability, retain ceil(5% * N), and renormalize their
    # probability-weighted coordinates.
    top_count = max(1, math.ceil(0.05 * len(xyz)))
    top = sorted(xyz, key=lambda z: z[2], reverse=True)[:top_count]
    top_mass = sum(p for _, _, p in top)
    topx = sum(x * p for x, _, p in top) / top_mass
    topy = sum(y * p for _, y, p in top) / top_mass
    variance = sum(p * ((x - mx) ** 2 + (y - my) ** 2) for x, y, p in xyz)
    return {"map_x": mapx, "map_y": mapy, "mean_x": mx, "mean_y": my,
            "pmfs_top5_x": topx, "pmfs_top5_y": topy,
            "pmfs_top5_error_m": math.hypot(topx - tx, topy - ty),
            "pmfs_top5_cell_count": top_count,
            "map_error_m": math.hypot(mapx - tx, mapy - ty),
            "mean_error_m": math.hypot(mx - tx, my - ty), "variance_m2": variance}


def rank_metrics(path, tx, ty):
    rr = rows(path)
    nearest = min(range(len(rr)), key=lambda i: math.hypot(float(rr[i]["x"]) - tx, float(rr[i]["y"]) - ty))
    def rank(column):
        values = [float(r[column]) for r in rr]
        order = sorted(range(len(rr)), key=lambda i: (-values[i], rr[i]["candidate_id"]))
        return order.index(nearest) + 1
    native, meaci = rank("native_shadow_mass"), rank("posterior_mass")
    return {"candidate_count": len(rr), "nearest_truth_candidate_id": rr[nearest]["candidate_id"],
            "native_rank": native, "meaci_rank": meaci,
            "native_rank_fraction": native / len(rr), "meaci_rank_fraction": meaci / len(rr)}


def relative_improvement(base, new):
    return (base - new) / max(abs(base), 1e-12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--truth-x", type=float, required=True)
    ap.add_argument("--truth-y", type=float, required=True)
    ap.add_argument("--update-tag", help="evaluate one frozen update instead of the latest")
    ap.add_argument("--house", default="GENERIC", help="label only; never used by scoring")
    args = ap.parse_args()
    td = args.run_dir / "tadm"
    score_paths = sorted(td.glob("meaci_candidate_scores_update_*.csv"))
    if not score_paths:
        raise SystemExit("no ME-ACI update artifacts")
    tag = args.update_tag or score_paths[-1].stem.rsplit("_", 1)[-1]
    selected_score = td / f"meaci_candidate_scores_update_{tag}.csv"
    if not selected_score.exists():
        raise SystemExit(f"missing requested update tag {tag}")
    native = posterior_metrics(td / f"meaci_native_shadow_update_{tag}.csv", args.truth_x, args.truth_y)
    meaci = posterior_metrics(td / f"meaci_source_posterior_update_{tag}.csv", args.truth_x, args.truth_y)
    ranks = rank_metrics(selected_score, args.truth_x, args.truth_y)
    map_gain = relative_improvement(native["map_error_m"], meaci["map_error_m"])
    mean_gain = relative_improvement(native["mean_error_m"], meaci["mean_error_m"])
    paper_gain = relative_improvement(native["pmfs_top5_error_m"], meaci["pmfs_top5_error_m"])
    rank_pass = ranks["meaci_rank_fraction"] <= 0.25 and ranks["meaci_rank"] < ranks["native_rank"]
    accuracy_pass = paper_gain >= 0.10
    collapse_pass = not (meaci["variance_m2"] < 1.0 and meaci["pmfs_top5_error_m"] > 2.0)
    development_pass = accuracy_pass and collapse_pass
    strict_rank_augmented_pass = rank_pass and development_pass
    payload = {"contract": "MEACI_EXTERNAL_TRUTH_EVALUATOR_V2", "update_tag": tag,
               "truth": [args.truth_x, args.truth_y], "native": native, "meaci": meaci,
               "ranks": ranks, "map_improvement_fraction": map_gain,
               "mean_improvement_fraction": mean_gain,
               "pmfs_paper_metric_improvement_fraction": paper_gain,
               "criteria": {"rank_pass": rank_pass, "accuracy_pass": accuracy_pass,
                            "primary_metric": "PMFS_ExpectedValue_top_5_percent",
                            "no_false_confident_collapse": collapse_pass},
               "development_gate_pass": development_pass,
               "strict_rank_augmented_pass": strict_rank_augmented_pass,
               "verdict": f"MEACI_{args.house}_DEVELOPMENT_GATE_{'PASS' if development_pass else 'FAIL'}"}
    out = args.run_dir / "meaci_evaluation.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
