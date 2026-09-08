"""Paired A0 versus CORE-M1 closed-loop evaluator."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


TRUTH = {"H01": (-0.4, -2.9), "H02": (0.0, -1.0), "H03": (-0.45, 1.9)}


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
        if float(row["sim_time"]) <= 240.0
    ]
    if not values or values[-1][0] < 235.0:
        raise ValueError(f"HORIZON:{path}:{values[-1] if values else None}")
    auc = sum(
        (right[0] - left[0]) * (left[1] + right[1]) / 2.0
        for left, right in zip(values, values[1:])
    )
    return {
        "final_error_m": values[-1][1],
        "distance_auc_m_s": auc,
        "last_estimate_time_s": values[-1][0],
        "trace_rows_to_240": len(values),
        "status_sha256": hashlib.sha256(status_path.read_bytes()).hexdigest(),
        "trace_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--houses", nargs="+", choices=tuple(TRUTH), required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--m1-arm", default="M1C")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    pairs = []
    for house in args.houses:
        for seed in args.seeds:
            baseline = evaluate(args.run_root / f"{house}_seed{seed}_A0", TRUTH[house])
            core = evaluate(args.run_root / f"{house}_seed{seed}_{args.m1_arm}", TRUTH[house])
            pairs.append(
                {
                    "house": house,
                    "seed": seed,
                    "A0": baseline,
                    args.m1_arm: core,
                    "final_improvement_m": baseline["final_error_m"] - core["final_error_m"],
                    "auc_improvement_m_s": baseline["distance_auc_m_s"] - core["distance_auc_m_s"],
                }
            )

    final = [pair["final_improvement_m"] for pair in pairs]
    auc = [pair["auc_improvement_m_s"] for pair in pairs]
    gate = {
        "paired_worlds": len(pairs),
        "final_improved_worlds": sum(value > 0.0 for value in final),
        "auc_improved_worlds": sum(value > 0.0 for value in auc),
        "both_improved_worlds": sum(
            pair["final_improvement_m"] > 0.0 and pair["auc_improvement_m_s"] > 0.0
            for pair in pairs
        ),
        "all_pairs_improved": all(
            pair["final_improvement_m"] > 0.0 and pair["auc_improvement_m_s"] > 0.0
            for pair in pairs
        ),
        "mean_final_improvement_m": sum(final) / len(final),
        "mean_auc_improvement_m_s": sum(auc) / len(auc),
        "pass": (
            sum(value > 0.0 for value in final) * 2 >= len(final)
            and sum(value > 0.0 for value in auc) * 2 >= len(auc)
            and sum(final) > 0.0
            and sum(auc) > 0.0
        ),
    }
    report = {
        "contract": "CSTAR_CORE_M1_PAIRED_CLOSED_LOOP_V1",
        "houses": args.houses,
        "seeds": args.seeds,
        "m1_arm": args.m1_arm,
        "pairs": pairs,
        "gate": gate,
        "verdict": "PASS" if gate["pass"] else "NO_GO",
        "limits": [
            "a one-world pilot is only an early-stop screen",
            "seed12 is exposed development evidence and must remain labelled as such",
            "closed-loop benefit does not by itself prove the structural identification assumptions",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": gate, "verdict": report["verdict"]}, indent=2))


if __name__ == "__main__":
    main()
