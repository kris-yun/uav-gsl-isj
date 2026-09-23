#!/usr/bin/env python3
"""Aggregate the frozen six-run TPT first-passage Layer-1 gate."""
import argparse
import json
import statistics
from pathlib import Path

EXPECTED_ELIGIBLE = {
    "H02_R2026092211",
    "H02_R2026092212",
    "H03_R2026092221",
    "H03_R2026092222",
}


def median(xs):
    return statistics.median(xs) if xs else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_root", type=Path)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()

    rows = {}
    for path in sorted(args.result_root.glob("*/tpt_first_passage.json")):
        run = path.parent.name
        rows[run] = json.loads(path.read_text())

    missing = sorted(EXPECTED_ELIGIBLE - set(rows))
    eligible = {run: rows[run] for run in EXPECTED_ELIGIBLE if run in rows and rows[run].get("eligible_positive_reactive_target")}
    passes = {run for run, row in eligible.items() if row.get("single_run_mechanism_pass")}

    passage_pct = [
        row["evaluation"]["passage_auc"]["rank_percentile"] for row in eligible.values()
    ]
    static_pct = [
        row["evaluation"]["static_occupancy"]["rank_percentile"] for row in eligible.values()
    ]
    geometry_pct = [
        row["evaluation"]["geometry"]["rank_percentile"] for row in eligible.values()
    ]

    both_houses = (
        any(run.startswith("H02_") for run in passes)
        and any(run.startswith("H03_") for run in passes)
    )
    gate = bool(
        not missing
        and len(eligible) == 4
        and len(passes) >= 3
        and both_houses
        and median(passage_pct) <= 0.25
        and median(passage_pct) < median(static_pct)
        and median(passage_pct) < median(geometry_pct)
    )

    payload = {
        "contract": "TPT_FIRST_PASSAGE_LAYER1_AGGREGATE_V1",
        "expected_positive_target_runs": sorted(EXPECTED_ELIGIBLE),
        "missing_expected_runs": missing,
        "eligible_runs": sorted(eligible),
        "single_run_passes": sorted(passes),
        "single_run_pass_count": len(passes),
        "both_houses_represented_among_passes": both_houses,
        "median_truth_rank_percentile": {
            "passage_auc": median(passage_pct),
            "static_occupancy": median(static_pct),
            "geometry": median(geometry_pct),
        },
        "promotion_rule": {
            "all_four_H02_H03_runs_present_and_eligible": True,
            "single_run_mechanism_pass_min": 3,
            "passes_must_include_H02_and_H03": True,
            "median_passage_truth_rank_percentile_max": 0.25,
            "median_passage_must_beat_static": True,
            "median_passage_must_beat_geometry": True,
        },
        "decision": "GO_TO_LAYER2_CROSS_REALIZATION_TPT" if gate else "TPT_LAYER1_HOLD",
        "closed_loop_authorized": False,
        "posterior_construction_authorized": False,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(json.dumps(payload, indent=2, allow_nan=False))
    raise SystemExit(0 if gate else 10)


if __name__ == "__main__":
    main()
