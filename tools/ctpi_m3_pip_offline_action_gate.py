#!/usr/bin/env python3
"""Truth-blind offline action gate for frozen CTPI M3 PIP V0.

The gate uses only already-spent historical routes to construct a feasible
candidate-action library. At source updates 1..4, the candidates are the
unvisited future stops of that same route. No source truth, localization error,
future observation, or planner outcome is read. Passing this gate proves only
that PIP produces a non-degenerate, M2-sensitive action policy; it does not prove
a localization improvement and does not authorize formal closed-loop.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from cpir_three_module_shadow import HOUSES, BankHouse, load_case, read_csv
from ctpi_m3_pip_frozen_v0 import decide

CONTRACT = "CTPI_M3_PIP_OFFLINE_ACTION_GATE_V0"
SOURCE_UPDATES = 5
ANALYZED_UPDATES = 4
PAIR_TOL = 1e-12


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def decision_sensor_state(case: Any, visible_count: int) -> float:
    rows = read_csv(case.runtime / "sensor_trace.csv")
    if visible_count <= 0 or visible_count > len(case.stops):
        raise RuntimeError("PIP_DECISION_VISIBLE_COUNT")
    end_index = int(case.stops[visible_count - 1][-1])
    value = float(rows[end_index]["measured_gas_ppm"])
    if value < 0.0 or not np.isfinite(value):
        raise RuntimeError("PIP_DECISION_SENSOR_STATE")
    return value


def strict_gain_fraction(rows: list[dict[str, Any]], key: str) -> float:
    return float(np.mean([float(r[key]) > PAIR_TOL for r in rows])) if rows else 0.0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage1-root", type=Path, required=True)
    p.add_argument("--bank-root", type=Path, required=True)
    p.add_argument("--historical-root", type=Path, required=True)
    p.add_argument("--support", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()

    support_rows = read_csv(args.support)
    contexts: list[dict[str, Any]] = []
    for house in HOUSES:
        bank = BankHouse.load(house, args.bank_root, support_rows)
        cases = [load_case(args.historical_root, house, seed, bank, strict_full_coverage=False)
                 for seed in range(10)]
        stage_path = args.stage1_root / f"{house}_FACTORIAL.npz"
        with np.load(stage_path, allow_pickle=False) as z:
            carrier_ids = np.asarray(z["carrier_ids"]).astype(str)
            q_raw = np.asarray(z["q_raw"], dtype=np.float64)
            f00 = np.asarray(z["f00"], dtype=np.float64)
        if list(carrier_ids) != bank.carriers:
            raise RuntimeError(f"PIP_CARRIER_ORDER:{house}")
        if q_raw.shape != (10, len(carrier_ids), 15):
            raise RuntimeError(f"PIP_QRAW_SHAPE:{house}:{q_raw.shape}")
        if f00.shape != (10 * SOURCE_UPDATES, len(carrier_ids)):
            raise RuntimeError(f"PIP_F00_SHAPE:{house}:{f00.shape}")

        for case_index, case in enumerate(cases):
            for update_index in range(ANALYZED_UPDATES):
                visible = np.asarray(case.visible[update_index], dtype=np.int64)
                visible_count = len(visible)
                if visible_count not in (3, 6, 9, 12):
                    raise RuntimeError(f"PIP_VISIBLE:{house}:{case.seed}:{visible_count}")
                candidate_stops = np.arange(visible_count, 15, dtype=np.int64)
                if len(candidate_stops) < 3:
                    raise RuntimeError("PIP_CANDIDATE_COUNT")
                posterior = np.asarray(f00[case_index * SOURCE_UPDATES + update_index], dtype=np.float64)
                if np.any(posterior < 0.0) or not np.isfinite(posterior).all():
                    raise RuntimeError("PIP_M1_POSTERIOR")
                posterior = posterior / float(np.sum(posterior))
                if abs(float(np.sum(posterior)) - 1.0) > PAIR_TOL:
                    raise RuntimeError("PIP_M1_POSTERIOR_MASS")
                probability = np.asarray(q_raw[case_index, :, candidate_stops], dtype=np.float64).T
                m = decision_sensor_state(case, visible_count)
                result = decide(posterior, probability, m, candidate_stops.tolist())
                raw_top = float(np.max(result.raw_scores))
                tsdc_top = float(np.max(result.tsdc_scores))
                raw_next = float(result.raw_scores[0])
                tsdc_next = float(result.tsdc_scores[0])
                raw_ties = int(np.sum(result.raw_scores >= raw_top - 1e-15))
                tsdc_ties = int(np.sum(result.tsdc_scores >= tsdc_top - 1e-15))
                contexts.append({
                    "house": house,
                    "seed": int(case.seed),
                    "update_id": update_index + 1,
                    "visible_stop_count": visible_count,
                    "candidate_count": int(len(candidate_stops)),
                    "decision_sensor_state_ppm": m,
                    "historical_next_stop": int(result.historical_next_id),
                    "raw_selected_stop": int(result.raw_selected_id),
                    "tsdc_selected_stop": int(result.tsdc_selected_id),
                    "raw_top_information_nats": raw_top,
                    "tsdc_top_information_nats": tsdc_top,
                    "raw_next_information_nats": raw_next,
                    "tsdc_next_information_nats": tsdc_next,
                    "raw_gain_over_next_nats": raw_top - raw_next,
                    "tsdc_gain_over_next_nats": tsdc_top - tsdc_next,
                    "raw_top_tie_count": raw_ties,
                    "tsdc_top_tie_count": tsdc_ties,
                    "tsdc_changes_historical_next": int(result.tsdc_selected_id != result.historical_next_id),
                    "tsdc_differs_from_raw_information_policy": int(result.tsdc_selected_id != result.raw_selected_id),
                })

    if len(contexts) != 120:
        raise RuntimeError(f"PIP_CONTEXT_COUNT:{len(contexts)}")

    per_house: dict[str, Any] = {}
    for house in HOUSES:
        rows = [r for r in contexts if r["house"] == house]
        per_house[house] = {
            "contexts": len(rows),
            "tsdc_strict_gain_vs_next_fraction": strict_gain_fraction(rows, "tsdc_gain_over_next_nats"),
            "tsdc_action_change_from_next_fraction": float(np.mean([r["tsdc_changes_historical_next"] for r in rows])),
            "tsdc_vs_raw_action_difference_fraction": float(np.mean([r["tsdc_differs_from_raw_information_policy"] for r in rows])),
            "tsdc_unique_top_fraction": float(np.mean([r["tsdc_top_tie_count"] == 1 for r in rows])),
            "median_tsdc_gain_over_next_nats": float(np.median([r["tsdc_gain_over_next_nats"] for r in rows])),
        }

    pooled = {
        "contexts": len(contexts),
        "tsdc_strict_gain_vs_next_fraction": strict_gain_fraction(contexts, "tsdc_gain_over_next_nats"),
        "tsdc_action_change_from_next_fraction": float(np.mean([r["tsdc_changes_historical_next"] for r in contexts])),
        "tsdc_vs_raw_action_difference_fraction": float(np.mean([r["tsdc_differs_from_raw_information_policy"] for r in contexts])),
        "tsdc_unique_top_fraction": float(np.mean([r["tsdc_top_tie_count"] == 1 for r in contexts])),
        "median_tsdc_gain_over_next_nats": float(np.median([r["tsdc_gain_over_next_nats"] for r in contexts])),
    }

    gate = {
        "context_count_120": len(contexts) == 120,
        "all_candidate_sets_at_least_3": all(int(r["candidate_count"]) >= 3 for r in contexts),
        "all_information_finite_nonnegative": all(
            np.isfinite(float(r[k])) and float(r[k]) >= -PAIR_TOL
            for r in contexts
            for k in ("raw_top_information_nats", "tsdc_top_information_nats", "raw_next_information_nats", "tsdc_next_information_nats")
        ),
        "each_house_majority_strict_gain_over_next": all(
            per_house[h]["tsdc_strict_gain_vs_next_fraction"] >= 0.50 for h in HOUSES
        ),
        "each_house_positive_median_gain": all(
            per_house[h]["median_tsdc_gain_over_next_nats"] > PAIR_TOL for h in HOUSES
        ),
        "pooled_unique_top_fraction_ge_0_75": pooled["tsdc_unique_top_fraction"] >= 0.75,
        "m2_changes_m3_policy_in_each_house": all(
            per_house[h]["tsdc_vs_raw_action_difference_fraction"] > 0.0 for h in HOUSES
        ),
        "pooled_m2_policy_difference_ge_0_10": pooled["tsdc_vs_raw_action_difference_fraction"] >= 0.10,
    }
    passed = all(gate.values())
    report = {
        "contract": CONTRACT,
        "status": "TRUTH_BLIND_OFFLINE_ACTION_LIBRARY",
        "scientific_boundary": "structural action-policy gate only; no localization claim",
        "candidate_action_contract": "at updates 1..4, all unvisited future stops of the same already-feasible 15-stop historical route, ordered chronologically; exact ties keep chronological/native order",
        "m1_posterior": "frozen F00/CREL carrier posterior",
        "m2_predictor": "frozen TSDC V0",
        "truth_read": false,
        "future_observation_read": false,
        "localization_error_read": false,
        "planner_reward_read": false,
        "gaden_runs": 0,
        "contexts": len(contexts),
        "pooled": pooled,
        "per_house": per_house,
        "gate": gate,
        "pass": passed,
        "authorization": {
            "m3_runtime_development": passed,
            "cpp_ros_closed_loop": false,
            "formal_localization_claim": false
        },
        "verdict": "CTPI_M3_PIP_OFFLINE_ACTION_GATE=PASS" if passed else "CTPI_M3_PIP_OFFLINE_ACTION_GATE=NO_GO"
    }

    args.output_dir.mkdir(parents=True, exist_ok=False)
    with (args.output_dir / "M3_PIP_CONTEXTS.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(contexts[0].keys()))
        writer.writeheader(); writer.writerows(contexts)
    (args.output_dir / "M3_PIP_OFFLINE_ACTION_GATE.json").write_bytes(canonical_bytes(report))
    (args.output_dir / ("PASS" if passed else "NO_GO")).write_text(report["verdict"] + "\n", encoding="ascii")
    print(report["verdict"])
    print(json.dumps({"pooled": pooled, "per_house": per_house}, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
