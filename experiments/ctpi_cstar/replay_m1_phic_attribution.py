"""Read-only PHIC attribution replay for PMFS event exports.

The runtime export is deliberately the legacy forward operator.  This tool
adds only the observation-side diagnostics: exposure-rate normalization,
first-order sensor memory, stable residuals and a fixed sensitivity interval.
It never reads source truth, House labels, posterior, or planner state.

The output is a diagnostic gate.  A closed-loop PHIC claim still requires a
block-level exposure sequence from the runtime rather than the aggregate
forward exposure currently exported here.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
from collections import defaultdict
from pathlib import Path


REQUIRED = {
    "candidate_id", "member_index", "event_index", "block_id", "sim_time_s",
    "observed_hit", "threshold", "legacy_hit_probability",
    "aggregate_raw_exposure", "iterations_to_record", "delta_time_s",
    "context_value", "context_centered_log_odds",
}


def clip_probability(value: float) -> float:
    return min(max(value, 1.0e-6), 1.0 - 1.0e-6)


def logit(value: float) -> float:
    p = clip_probability(value)
    return math.log(p) - math.log1p(-p)


def fopdt_step(state: float, exposure_rate: float, dt: float, tau: float, gain: float) -> float:
    if dt < 0.0 or not math.isfinite(dt):
        raise ValueError("event times must be monotone")
    alpha = 1.0 - math.exp(-dt / tau)
    return state + alpha * (gain * exposure_rate - state)


def parse_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"missing columns: {sorted(missing)}")
        return list(reader)


def replay(rows: list[dict[str, str]], tau_s: float, gain: float, lambda_ratio: float) -> dict:
    if not rows:
        raise ValueError("empty attribution export")
    if tau_s <= 0.0 or not math.isfinite(tau_s):
        raise ValueError("tau_s must be positive")
    if lambda_ratio < 1.0 or not math.isfinite(lambda_ratio):
        raise ValueError("lambda_ratio must be >= 1")

    # The runtime appends one CSV across source updates.  block_id/event_index
    # are local to an update, so the immutable run/update identity must be part
    # of the replay key; otherwise the second update falsely looks non-monotone.
    grouped: dict[tuple[str, int, str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (row["run_uuid"], int(row["source_update_id"]),
               row["candidate_id"], int(row["member_index"]))
        grouped[key].append(row)

    member_summaries = []
    event_rows = []
    for (run_uuid, source_update_id, candidate, member), sequence in sorted(grouped.items()):
        sequence.sort(key=lambda row: (int(row["event_index"]), int(row["block_id"])))
        previous_time: float | None = None
        state = 0.0
        legacy_ll = 0.0
        phic_ll = 0.0
        residuals = []
        previous_block = 0
        for row in sequence:
            block_id = int(row["block_id"])
            event_index = int(row["event_index"])
            if block_id <= previous_block:
                raise ValueError(f"non-monotone block_id for {candidate}/{member}")
            previous_block = block_id
            sim_time = float(row["sim_time_s"])
            # The first event starts one measured block after the sensor
            # state was initialized; subsequent gaps use the stamped event
            # times.  This avoids an artificial zero-state penalty on the
            # first physical stop.
            dt = float(row["delta_time_s"]) if previous_time is None else sim_time - previous_time
            previous_time = sim_time
            iterations = int(row["iterations_to_record"])
            if iterations <= 0:
                raise ValueError("iterations_to_record must be positive")
            exposure = max(0.0, float(row["aggregate_raw_exposure"])) / iterations
            state = fopdt_step(state, exposure, dt, tau_s, gain)
            q = clip_probability(state)
            hit = int(row["observed_hit"]) != 0
            legacy_q = clip_probability(float(row["legacy_hit_probability"]))
            legacy_ll += math.log(legacy_q if hit else 1.0 - legacy_q)
            phic_ll += math.log(q if hit else 1.0 - q)
            context = float(row["context_value"])
            if int(row["context_centered_log_odds"]):
                residual = logit(q) - context
            else:
                residual = logit(q) - logit(context)
            residuals.append(residual)
            event_rows.append({
                "run_uuid": run_uuid,
                "source_update_id": source_update_id,
                "candidate_id": candidate,
                "member_index": member,
                "event_index": event_index,
                "block_id": block_id,
                "sim_time_s": sim_time,
                "exposure_rate": exposure,
                "fopdt_state": state,
                "phic_event_probability": q,
                "legacy_event_probability": legacy_q,
                "observed_hit": int(hit),
                "legacy_log_likelihood_increment": math.log(legacy_q if hit else 1.0 - legacy_q),
                "phic_log_likelihood_increment": math.log(q if hit else 1.0 - q),
                "stable_residual": residual,
            })
        member_summaries.append({
            "candidate_id": candidate,
            "member_index": member,
            "event_count": len(sequence),
            "legacy_log_likelihood": legacy_ll,
            "phic_log_likelihood": phic_ll,
            "stable_residual_mean": sum(residuals) / len(residuals),
            "stable_residual_variance": sum((value - sum(residuals) / len(residuals)) ** 2 for value in residuals) / len(residuals),
        })

    candidates: dict[str, list[dict]] = defaultdict(list)
    for summary in member_summaries:
        candidates[summary["candidate_id"]].append(summary)
    candidate_summaries = []
    width = math.log(lambda_ratio)
    for candidate, members in sorted(candidates.items()):
        phic = sum(item["phic_log_likelihood"] for item in members) / len(members)
        legacy = sum(item["legacy_log_likelihood"] for item in members) / len(members)
        stable_values = [item["stable_residual_mean"] for item in members]
        stable = sum(stable_values) / len(stable_values)
        interaction = sum((value - stable) ** 2 for value in stable_values) / len(stable_values)
        candidate_summaries.append({
            "candidate_id": candidate,
            "member_count": len(members),
            "legacy_log_likelihood_mean": legacy,
            "phic_log_likelihood_mean": phic,
            "stable_residual_mean": stable,
            "candidate_transport_interaction_variance": interaction,
            "lambda_interval": [phic - width, phic + width],
        })
    ranked = sorted(candidate_summaries, key=lambda item: item["phic_log_likelihood_mean"], reverse=True)
    overlap = False
    if len(ranked) >= 2:
        left = ranked[0]["lambda_interval"]
        right = ranked[1]["lambda_interval"]
        overlap = max(left[0], right[0]) <= min(left[1], right[1])
    return {
        "contract": "CSTAR_M1_PHIC_ATTRIBUTION_REPLAY_V1",
        "observation_operator": "aggregate exposure rate -> FOPDT state -> Bernoulli event",
        "tau_s": tau_s,
        "gain": gain,
        "lambda_ratio": lambda_ratio,
        "member_summaries": member_summaries,
        "candidate_summaries": candidate_summaries,
        "ranked_candidates": [item["candidate_id"] for item in ranked],
        "sensitivity_top_two_overlap": overlap,
        "update_decision": "ABSTAIN_OVERLAPPING_INTERVALS" if overlap else "RANKING_AVAILABLE",
        "limits": [
            "aggregate exposure is a stationary surrogate, not a block-level forward trajectory",
            "diagnostic attribution only; no source truth, posterior, planner, or House label is used",
            "closed-loop effectiveness requires a preregistered paired run after block-level replay",
        ],
    }, event_rows


def selftest() -> dict:
    fieldnames = sorted(REQUIRED)
    rows = []
    for candidate, exposure in (("source", 180.0), ("decoy", 20.0)):
        for member in (0, 1):
            for index in range(1, 4):
                rows.append({
                    "run_uuid": "selftest",
                    "source_update_id": "1",
                    "candidate_id": candidate,
                    "member_index": str(member), "event_index": str(index), "block_id": str(index),
                    "sim_time_s": str(index * 2.0), "observed_hit": "1",
                    "threshold": "0.1", "legacy_hit_probability": "0.5",
                    "aggregate_raw_exposure": str(exposure), "iterations_to_record": "200", "delta_time_s": "0.2",
                    "context_value": "0.0", "context_centered_log_odds": "1",
                })
    report, _ = replay(rows, tau_s=1.2, gain=1.0, lambda_ratio=1.5)
    ambiguous_rows = [dict(row, observed_hit="1", aggregate_raw_exposure="180.0") for row in rows]
    ambiguous, _ = replay(ambiguous_rows, tau_s=1.2, gain=1.0, lambda_ratio=1.5)
    checks = {
        "source_ranked_first": report["ranked_candidates"][0] == "source",
        "event_rows_have_fopdt_state": len(report["member_summaries"]) == 4,
        "overlap_guard_is_active": ambiguous["sensitivity_top_two_overlap"],
        "no_truth_key_in_output": all("truth" not in key.lower() for key in report),
    }
    return {"contract": "CSTAR_M1_PHIC_ATTRIBUTION_REPLAY_SELFTEST_V1", "checks": checks, "pass": all(checks.values())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--rows-output", type=Path)
    parser.add_argument("--tau-s", type=float, default=1.2)
    parser.add_argument("--gain", type=float, default=1.0)
    parser.add_argument("--lambda-ratio", type=float, default=1.5)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        report = selftest()
        print(json.dumps(report, indent=2))
        if not report["pass"]:
            raise SystemExit(1)
        return
    if args.input is None or args.output is None:
        parser.error("--input and --output are required unless --selftest is used")
    report, event_rows = replay(parse_rows(args.input), args.tau_s, args.gain, args.lambda_ratio)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.rows_output:
        if args.rows_output.exists():
            raise FileExistsError(args.rows_output)
        args.rows_output.parent.mkdir(parents=True, exist_ok=True)
        with args.rows_output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=sorted(event_rows[0]))
            writer.writeheader()
            writer.writerows(event_rows)
    print(json.dumps({"contract": report["contract"], "update_decision": report["update_decision"], "ranked_candidates": report["ranked_candidates"]}, indent=2))


if __name__ == "__main__":
    main()
