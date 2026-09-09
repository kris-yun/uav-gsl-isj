#!/usr/bin/env python3
"""Evaluate the frozen causal-M1 likelihood on exact GADEN candidate traces.

Each target source/wind history is scored against both source candidates using
only the *opposite* wind member.  Thus neither an identical trajectory nor the
target wind's candidate-forward input can enter its score.  This is an
offline, two-candidate factorial premise gate; it is not full-map localization
or a closed-loop result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from m1_causal.counterfactual_likelihood import FopdtConfig, decide_with_observability, fopdt_response, score_candidates

HOUSES = ("H01", "H02", "H03")
SOURCES = ("SA", "SB")
WINDS = ("fast", "slow")


def read_jsonl(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"M1_EXACT_EMPTY:{path}")
    if [int(row["step"]) for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError(f"M1_EXACT_NONCONTIGUOUS:{path}")
    return rows


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rms(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)) / len(left))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True,
                        help="frozen controller-visible measured histories")
    parser.add_argument("--candidate-forward", type=Path, required=True,
                        help="isolated GADEN do(source) input traces")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sensor = FopdtConfig(tau_s=1.2, dead_time_s=.4)
    rows: list[dict] = []
    house_summary: dict[str, dict] = {}
    for house in HOUSES:
        observed: dict[tuple[str, str], list[dict]] = {}
        exposure: dict[tuple[str, str], tuple[float, ...]] = {}
        response: dict[tuple[str, str], tuple[float, ...]] = {}
        for source in SOURCES:
            for wind in WINDS:
                key = (source, wind)
                observed[key] = read_jsonl(args.assets / "realizations" / f"{house}_{source}_{wind}" / "measured_history.jsonl")
                forward_path = args.candidate_forward / f"{house}_{source}_{wind}" / "candidate_forward_input.jsonl"
                forward_rows = read_jsonl(forward_path)
                if [row["stamp_ns"] for row in observed[key]] != [row["stamp_ns"] for row in forward_rows]:
                    raise ValueError(f"M1_EXACT_STAMP_MISMATCH:{house}:{source}:{wind}")
                exposure[key] = tuple(float(row["candidate_forward_input_ppm"]) for row in forward_rows)
                response[key] = fopdt_response(
                    tuple(float(row["t_sim_s"]) for row in forward_rows), exposure[key], sensor)
        # Fixed before target scoring: candidate-bank-only cross-transport
        # discrepancy.  It is not a fitted target outcome scale.
        crosswind_rms = [rms(response[(source, "fast")], response[(source, "slow")]) for source in SOURCES]
        observation_sigma = max(1.0e-9, sorted(crosswind_rms)[len(crosswind_rms) // 2])
        for true_source in SOURCES:
            for target_wind in WINDS:
                other_wind = "slow" if target_wind == "fast" else "fast"
                target = observed[(true_source, target_wind)]
                stamps = tuple(float(row["t_sim_s"]) for row in target)
                measured = tuple(float(row["gas_ppm"]) for row in target)
                scores = score_candidates(
                    timestamps_s=stamps, observed_sensor=measured,
                    candidate_member_exposure={source: (exposure[(source, other_wind)],) for source in SOURCES},
                    sensor=sensor, observation_sigma=observation_sigma,
                )
                decision = decide_with_observability(scores, sensor_discrepancy_bound=observation_sigma)
                rows.append({
                    "house": house,
                    "target_wind": target_wind,
                    "counterfactual_wind": other_wind,
                    "true_source_evaluator_only": true_source,
                    "true_source_rank": [score.candidate_id for score in scores].index(true_source) + 1,
                    "observation_sigma_from_candidate_bank": observation_sigma,
                    "candidate_scores": [{
                        "candidate_id": score.candidate_id,
                        "marginal_log_likelihood": score.marginal_log_likelihood,
                    } for score in scores],
                    "decision": decision.decision,
                    "likelihood_contrast": decision.lower_contrast_bound,
                    "discrepancy_bound": decision.discrepancy_bound,
                    "same_source_same_wind_prediction_forbidden": True,
                    "target_history_sha256": digest(args.assets / "realizations" / f"{house}_{true_source}_{target_wind}" / "measured_history.jsonl"),
                    "candidate_forward_sha256": {
                        source: digest(args.candidate_forward / f"{house}_{source}_{other_wind}" / "candidate_forward_input.jsonl")
                        for source in SOURCES
                    },
                })
        subset = [row for row in rows if row["house"] == house]
        house_summary[house] = {
            "cases": len(subset),
            "rank1_cases": sum(row["true_source_rank"] == 1 for row in subset),
            "commit_cases": sum(row["decision"] == "COMMIT" for row in subset),
        }
    for item in house_summary.values():
        item["pass"] = item["rank1_cases"] == item["cases"] and item["commit_cases"] == item["cases"]
    report = {
        "contract": "CSTAR_M1_EXACT_COUNTERFACTUAL_TRANSFER_V1",
        "sensor": {"tau_s": 1.2, "dead_time_s": .4, "implementation": "m1_causal.counterfactual_likelihood"},
        "target_rule": "target source/wind never scored with its same-source same-wind candidate-forward trace",
        "sigma_rule": "per-House median same-candidate fast/slow FOPDT RMS, computed before target scoring",
        "by_house": house_summary,
        "rows": rows,
        "verdict": "M1_EXACT_COUNTERFACTUAL_CROSS_TRANSPORT_PREMISE_PASS" if all(item["pass"] for item in house_summary.values())
        else "M1_EXACT_COUNTERFACTUAL_CROSS_TRANSPORT_PREMISE_NO_GO",
        "limits": [
            "only two candidate source positions per House",
            "candidate-forward traces are evaluator/development assets, not yet an online full-map provider",
            "does not establish closed-loop utility or cross-dataset localization gain",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])


if __name__ == "__main__":
    main()
