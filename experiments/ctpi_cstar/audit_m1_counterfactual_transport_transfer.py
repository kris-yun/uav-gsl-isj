#!/usr/bin/env python3
"""Read-only factorial gate for the causal M1 counterfactual premise.

For a target history from source S under wind W, this deliberately forbids the
same (S, W) trace as a candidate prediction.  Each candidate source is instead
represented by its trace under the opposite wind intervention.  The score asks
whether source identity survives this transport intervention better than the
alternative source does.  It is a small factorial mechanism gate, not an
online PMFS implementation and not a closed-loop efficacy claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


WINDS = ("fast", "slow")
SOURCES = ("SA", "SB")


def load_trace(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise ValueError(f"empty trace: {path}")
    expected = list(range(1, len(rows) + 1))
    if [int(row["step"]) for row in rows] != expected:
        raise ValueError(f"non-contiguous causal trace: {path}")
    if any(float(row["gas_ppm"]) < 0.0 for row in rows):
        raise ValueError(f"negative sensor value: {path}")
    return rows


def score(target: list[dict], prediction: list[dict]) -> float:
    """Fixed log-concentration squared-error contrast; no fitted parameters."""
    if len(target) != len(prediction):
        raise ValueError("counterfactual trace length mismatch")
    total = 0.0
    for actual, predicted in zip(target, prediction):
        if actual["stamp_ns"] != predicted["stamp_ns"]:
            raise ValueError("counterfactual trace timestamps mismatch")
        residual = math.log1p(float(actual["gas_ppm"])) - math.log1p(float(predicted["gas_ppm"]))
        total += residual * residual
    return total / len(target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assets = args.assets.resolve()
    manifest = assets / "MANIFEST.json"
    if not manifest.is_file():
        raise ValueError("missing asset manifest")
    trace_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    rows: list[dict] = []
    for house in ("H01", "H02", "H03"):
        traces = {
            (source, wind): load_trace(assets / "realizations" / f"{house}_{source}_{wind}" / "measured_history.jsonl")
            for source in SOURCES for wind in WINDS
        }
        lengths = {len(trace) for trace in traces.values()}
        if len(lengths) != 1:
            raise ValueError(f"inconsistent trace length in {house}")
        for true_source in SOURCES:
            for target_wind in WINDS:
                target = traces[(true_source, target_wind)]
                counterfactual_wind = "slow" if target_wind == "fast" else "fast"
                candidate_scores = {
                    candidate: score(target, traces[(candidate, counterfactual_wind)])
                    for candidate in SOURCES
                }
                ranked = sorted(candidate_scores, key=lambda candidate: (candidate_scores[candidate], candidate))
                rows.append({
                    "house": house,
                    "target_wind": target_wind,
                    "counterfactual_wind": counterfactual_wind,
                    "true_source_evaluator_only": true_source,
                    "candidate_scores": candidate_scores,
                    "ranked_candidates": ranked,
                    "true_source_rank": ranked.index(true_source) + 1,
                    "true_minus_decoy_score": candidate_scores[true_source] - candidate_scores[
                        "SB" if true_source == "SA" else "SA"
                    ],
                    "same_source_same_wind_prediction_forbidden": True,
                })
    by_house = {}
    for house in ("H01", "H02", "H03"):
        subset = [row for row in rows if row["house"] == house]
        correct = sum(row["true_source_rank"] == 1 for row in subset)
        by_house[house] = {"rank1_cases": correct, "cases": len(subset), "pass": correct == len(subset)}
    report = {
        "contract": "CSTAR_M1_FACTORIAL_COUNTERFACTUAL_TRANSPORT_TRANSFER_V1",
        "asset_manifest_sha256": trace_hash,
        "estimator": "fixed mean squared error of log1p measured FOPDT outputs",
        "counterfactual": "target (source, wind) is scored only against candidate traces under the opposite wind",
        "forbidden": [
            "same source and same wind trace as its own candidate prediction",
            "true source, House identifier, future gas, or source label in candidate score",
            "fitted calibration, threshold selection, or closed-loop interpretation",
        ],
        "rows": rows,
        "by_house": by_house,
        "verdict": "M1_FACTORIAL_CROSS_TRANSPORT_PREMISE_PASS" if all(item["pass"] for item in by_house.values())
        else "M1_FACTORIAL_CROSS_TRANSPORT_PREMISE_NO_GO",
        "limits": [
            "two source candidates per House do not establish full-map source localization",
            "this is an offline physical-response premise gate, not an online forward provider",
            "a pass does not establish cross-House closed-loop utility",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])


if __name__ == "__main__":
    main()
