"""Paired CORE-M1 evaluator with an explicit full-horizon posterior hold."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


TRUTH = {"H01": (-0.4, -2.9), "H02": (0.0, -1.0), "H03": (-0.45, 1.9)}
HORIZON_S = 240.0


def evaluate(path: Path, truth: tuple[float, float]) -> dict[str, float | int | str]:
    status_path = path / "run_status.json"
    trace_path = path / "source_estimate_trace.csv"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status.get("status") != "time_budget_timeout":
        raise ValueError(f"TERMINAL:{path}:{status}")

    with trace_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    values = [
        (
            float(row["sim_time"]),
            math.hypot(
                float(row["estimate_x"]) - truth[0],
                float(row["estimate_y"]) - truth[1],
            ),
        )
        for row in rows
        if 0.0 <= float(row["sim_time"]) <= HORIZON_S
    ]
    if not values:
        raise ValueError(f"EMPTY_TRACE:{path}")
    if any(right[0] <= left[0] for left, right in zip(values, values[1:])):
        raise ValueError(f"NON_MONOTONE_TRACE:{path}")

    # The source posterior is a state, not an instantaneous measurement.  It
    # remains the active estimate while the vehicle navigates and after the
    # final source update.  The terminal status certifies that this state was
    # carried to the frozen horizon.  Endpoint holds make AUC cover exactly
    # [0, 240] for both arms without inventing an unlogged posterior update.
    auc = values[0][0] * values[0][1]
    auc += sum(
        (right[0] - left[0]) * left[1]
        for left, right in zip(values, values[1:])
    )
    auc += (HORIZON_S - values[-1][0]) * values[-1][1]
    return {
        "final_error_m": values[-1][1],
        "distance_auc_0_240_m_s": auc,
        "first_estimate_time_s": values[0][0],
        "last_estimate_time_s": values[-1][0],
        "initial_hold_s": values[0][0],
        "terminal_hold_s": HORIZON_S - values[-1][0],
        "trace_rows_to_240": len(values),
        "status_sha256": hashlib.sha256(status_path.read_bytes()).hexdigest(),
        "trace_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--houses", nargs="+", choices=tuple(TRUTH), required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--m1-arm", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    pairs = []
    for house in args.houses:
        for seed in args.seeds:
            baseline = evaluate(args.run_root / f"{house}_seed{seed}_A0", TRUTH[house])
            core = evaluate(
                args.run_root / f"{house}_seed{seed}_{args.m1_arm}", TRUTH[house]
            )
            pairs.append(
                {
                    "house": house,
                    "seed": seed,
                    "A0": baseline,
                    args.m1_arm: core,
                    "final_improvement_m": baseline["final_error_m"]
                    - core["final_error_m"],
                    "auc_improvement_m_s": baseline["distance_auc_0_240_m_s"]
                    - core["distance_auc_0_240_m_s"],
                }
            )

    final = [pair["final_improvement_m"] for pair in pairs]
    auc = [pair["auc_improvement_m_s"] for pair in pairs]
    both = [
        pair["final_improvement_m"] > 0.0 and pair["auc_improvement_m_s"] > 0.0
        for pair in pairs
    ]
    gate = {
        "paired_worlds": len(pairs),
        "final_improved_worlds": sum(value > 0.0 for value in final),
        "auc_improved_worlds": sum(value > 0.0 for value in auc),
        "both_improved_worlds": sum(both),
        "all_pairs_improved": all(
            pair["final_improvement_m"] > 0.0
            and pair["auc_improvement_m_s"] > 0.0
            for pair in pairs
        ),
        "mean_final_improvement_m": sum(final) / len(final),
        "mean_auc_improvement_m_s": sum(auc) / len(auc),
        "pass": (
            sum(both) * 2 >= len(both)
            and sum(final) > 0.0
            and sum(auc) > 0.0
        ),
    }
    report = {
        "contract": "CSTAR_CORE_M1_PAIRED_CLOSED_LOOP_HORIZON_V3",
        "horizon_s": HORIZON_S,
        "posterior_between_updates": "zero_order_hold",
        "houses": args.houses,
        "seeds": args.seeds,
        "m1_arm": args.m1_arm,
        "pairs": pairs,
        "gate": gate,
        "verdict": "PASS" if gate["pass"] else "NO_GO",
        "limits": [
            "terminal status must independently certify the 240 s time budget",
            "endpoint holding does not invent an unlogged posterior update",
            "algorithm seeds under fixed sensor seed12 are not independent plume realizations",
            "closed-loop utility does not by itself prove structural identification assumptions",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": gate, "verdict": report["verdict"]}, indent=2))


if __name__ == "__main__":
    main()
