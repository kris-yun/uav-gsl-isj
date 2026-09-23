#!/usr/bin/env python3
"""Read source truth only after all A/B/C replay scores are frozen."""

import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    args = ap.parse_args()
    run = args.run
    freeze_path = run / "r1_scores_frozen_manifest.json"
    if not freeze_path.is_file():
        raise RuntimeError("truth evaluation forbidden before A/B/C score freeze")
    frozen = json.loads(freeze_path.read_text())
    if frozen["contract"] != "NATIVE_PMFS_R1_THREE_ARM_FROZEN_SCORES_V1" or frozen["truth_inputs_read"]:
        raise RuntimeError("invalid source-blind freeze contract")
    if set(frozen["arms"]) != set("ABC"):
        raise RuntimeError("three arms not frozen")
    scores = {}
    for arm in "ABC":
        path = run / f"R1_arm_{arm}" / "candidate_scores.csv"
        if sha(path) != frozen["arms"][arm]["scores_sha256"]:
            raise RuntimeError("score file changed after freeze")
        rows = list(csv.DictReader(path.open(newline="")))
        if [row["candidate_id"] for row in rows] != frozen["candidate_ids"]:
            raise RuntimeError("candidate IDs changed after freeze")
        if len(rows) != frozen["arms"][arm]["candidate_count"]:
            raise RuntimeError("candidate count changed after freeze")
        scores[arm] = rows
    # The source coordinates appear only in this manifest. No score-generating
    # process reads it, and the read occurs strictly after the freeze checks.
    runtime = json.loads((run / "runtime_manifest.json").read_text())
    source_x = Decimal(runtime["launch_args"]["source_x"])
    source_y = Decimal(runtime["launch_args"]["source_y"])
    with (run / "measured_map_at_update.csv").open(newline="") as fh:
        grid = next(csv.DictReader(fh))
    origin_x = Decimal(grid["origin_x"])
    origin_y = Decimal(grid["origin_y"])
    cell_size = Decimal(grid["cell_size"])
    source_i = int((source_x - origin_x) / cell_size)
    source_j = int((source_y - origin_y) / cell_size)
    report = {"contract": "NATIVE_PMFS_R1_THREE_ARM_TRUTH_EVALUATION_V1",
              "freeze_manifest_sha256": sha(freeze_path),
              "source_x": str(source_x), "source_y": str(source_y),
              "source_grid_i": source_i, "source_grid_j": source_j,
              "arms": {}}
    lines = ["# R1 House01 seed0 three-arm candidate-forward replay", "",
             f"Scores and maps were frozen before truth was opened (`{sha(freeze_path)}`).",
             f"The comparison uses one observation snapshot and its {len(scores['A'])} exported Native candidate regions.",
             "", "| Arm | Candidate count | Truth candidate | Rank | Truth score | Top-5 IDs | Wind min / median / max | Score SHA256 |",
             "|---|---:|---|---:|---:|---|---|---|"]
    for arm in "ABC":
        rows = scores[arm]
        containing = [row for row in rows if int(row["origin_i"]) <= source_i < int(row["origin_i"]) + int(row["size_i"])
                      and int(row["origin_j"]) <= source_j < int(row["origin_j"]) + int(row["size_j"])]
        if len(containing) != 1:
            raise RuntimeError(f"truth must fall in exactly one candidate in arm {arm}: {len(containing)}")
        ranked = sorted(rows, key=lambda row: (-Decimal(row["source_score"]), row["candidate_id"]))
        truth = containing[0]
        rank = next(i + 1 for i, row in enumerate(ranked) if row["candidate_id"] == truth["candidate_id"])
        top = ranked[:5]
        centroid_x = sum(Decimal(row["center_x"]) for row in top) / Decimal(len(top))
        centroid_y = sum(Decimal(row["center_y"]) for row in top) / Decimal(len(top))
        audit = dict(line.split("=", 1) for line in
                     (run / f"R1_arm_{arm}" / "source_blind_replay_audit.txt").read_text().splitlines())
        report["arms"][arm] = {
            "candidate_count": len(rows), "truth_candidate_id": truth["candidate_id"],
            "truth_candidate_rank": rank, "truth_candidate_score": truth["source_score"],
            "top5": [{"id": row["candidate_id"], "center_x": row["center_x"],
                      "center_y": row["center_y"], "score": row["source_score"]} for row in top],
            "top5_unweighted_centroid": {"x": str(centroid_x), "y": str(centroid_y)},
            "endpoint": None, "wind_magnitude": {key: audit[f"wind_{key}"] for key in ("min", "median", "max")},
            "score_sha256": frozen["arms"][arm]["scores_sha256"],
            "deterministic_repeat_pass": frozen["arms"][arm]["deterministic_repeat_pass"],
        }
        ids = ", ".join(row["candidate_id"] for row in top)
        wind = " / ".join(audit[f"wind_{key}"] for key in ("min", "median", "max"))
        lines.append(f"| {arm} | {len(rows)} | {truth['candidate_id']} | {rank} | {truth['source_score']} | {ids} | {wind} | `{frozen['arms'][arm]['scores_sha256']}` |")
    r2_source = bool(frozen.get("r2_replay_binary_sha256"))
    arm_note = ("Arms A/B link the frozen R2 PMFS source and event-keyed candidate RNG; A uses GMRF observer wind and B uses ground-truth wind. Arm C links the official humble PMFS source with ground-truth wind."
                if r2_source else
                "Arm A: GMRF observer wind with frozen R2 PMFS parameters. Arm B: ground-truth wind with frozen R2 PMFS parameters. Arm C: ground-truth wind with official humble PMFS forward and hit-map parameters.")
    lines += ["", arm_note,
              "", "Top-5 centroid is secondary. The smoke capture has no 300 s endpoint. Candidate map hashes and repeat checks are in `r1_scores_frozen_manifest.json`.",
              "", "Truth-source candidate rank is the primary scientific comparison. No arm was selected or retuned after truth evaluation."]
    (run / "R1_three_arm_truth_evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    (run / "R1_three_arm_report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({arm: report["arms"][arm]["truth_candidate_rank"] for arm in "ABC"}, indent=2))


if __name__ == "__main__":
    main()
