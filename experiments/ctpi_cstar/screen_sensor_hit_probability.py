"""Evaluate the frozen physical/FOPDT prior on the actual hit event.

The upstream truth-conditioned report contains only evaluator-side source
coordinates and frozen route forecasts.  This script does not refit them.  It
maps every predictive log-concentration law to P(gas_ppm > threshold) and
compares proper scores with the same source-free context and persistence laws.
It is a premise screen, not a localization or closed-loop claim.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def normal_tail(threshold: float, mean: float, scale: float) -> float:
    if not (math.isfinite(mean) and math.isfinite(scale) and scale > 0):
        raise ValueError("CSTAR_HIT_LAW_NONFINITE_NORMAL")
    return 0.5 * math.erfc((threshold - mean) / (scale * math.sqrt(2.0)))


def scores(probabilities: list[float], outcomes: list[int]) -> tuple[float, float]:
    if len(probabilities) != len(outcomes) or not outcomes:
        raise ValueError("CSTAR_HIT_LAW_LENGTH")
    nll = 0.0
    brier = 0.0
    for probability, outcome in zip(probabilities, outcomes):
        p = min(1.0 - 1.0e-12, max(1.0e-12, probability))
        nll -= math.log(p if outcome else 1.0 - p)
        brier += (p - outcome) ** 2
    return nll / len(outcomes), brier / len(outcomes)


def logit(probability: float) -> float:
    p = min(1.0 - 1.0e-9, max(1.0e-9, probability))
    return math.log(p) - math.log1p(-p)


def expit(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def ratio_correct(points: list[tuple[float, float, float, int]], weight: float) -> tuple[float, float]:
    probabilities = [
        expit(logit(persistence) + weight * (logit(source) - logit(context)))
        for source, context, persistence, _ in points
    ]
    return scores(probabilities, [outcome for _, _, _, outcome in points])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold-ppm", type=float, default=0.1)
    args = parser.parse_args()
    if not args.threshold_ppm > 0:
        raise ValueError("CSTAR_HIT_LAW_THRESHOLD")

    report = json.loads(args.input.read_text(encoding="utf-8"))
    threshold = math.log1p(args.threshold_ppm)
    rows = []
    point_rows: dict[str, list[tuple[float, float, float, int]]] = {
        "H01": [], "H02": [], "H03": []
    }
    for case in report["cases"]:
        observed = [float(value) for value in case["observed_logppm"]]
        outcomes = [int(value > threshold) for value in observed]
        components = case["source_components"]
        source_probability = []
        for index in range(len(observed)):
            source_probability.append(sum(
                normal_tail(threshold, float(component["mean"][index]),
                            float(component["scale"][index]))
                for component in components
            ) / len(components))
        context_probability = [
            normal_tail(threshold, float(mean), float(scale))
            for mean, scale in zip(case["context_mean"], case["context_scale"])
        ]
        persistence_mean = math.log1p(float(case["latest_observed_ppm"]))
        persistence_probability = [normal_tail(threshold, persistence_mean, 1.0)] * len(outcomes)
        point_rows[case["house"]].extend(zip(
            source_probability, context_probability, persistence_probability, outcomes
        ))
        source_nll, source_brier = scores(source_probability, outcomes)
        context_nll, context_brier = scores(context_probability, outcomes)
        persistence_nll, persistence_brier = scores(persistence_probability, outcomes)
        rows.append({
            "house": case["house"],
            "decision_id": case["decision_id"],
            "samples": len(outcomes),
            "positive_fraction": sum(outcomes) / len(outcomes),
            "source_nll": source_nll,
            "context_nll": context_nll,
            "persistence_nll": persistence_nll,
            "source_brier": source_brier,
            "context_brier": context_brier,
            "persistence_brier": persistence_brier,
        })

    houses = []
    for house in ("H01", "H02", "H03"):
        selected = [row for row in rows if row["house"] == house]
        if not selected:
            raise ValueError(f"CSTAR_HIT_LAW_MISSING_{house}")
        summary = {"house": house, "cases": len(selected)}
        for key in ("source_nll", "context_nll", "persistence_nll",
                    "source_brier", "context_brier", "persistence_brier",
                    "positive_fraction"):
            summary[key] = sum(row[key] for row in selected) / len(selected)
        summary["source_beats_persistence_nll"] = summary["source_nll"] < summary["persistence_nll"]
        summary["source_beats_persistence_brier"] = summary["source_brier"] < summary["persistence_brier"]
        summary["source_beats_context_nll"] = summary["source_nll"] < summary["context_nll"]
        summary["source_beats_context_brier"] = summary["source_brier"] < summary["context_brier"]
        houses.append(summary)

    required = (
        "source_beats_persistence_nll", "source_beats_persistence_brier",
        "source_beats_context_nll", "source_beats_context_brier",
    )
    gate = {key: sum(bool(house[key]) for house in houses) for key in required}
    gate["pass"] = all(gate[key] >= 2 for key in required)

    # Semiparametric source evidence: persistence owns the shared local
    # dynamics, while the physics model contributes only its source-vs-context
    # log likelihood ratio.  The non-negative scalar is fitted on two Houses
    # and evaluated on the third; zero is the exact persistence baseline.
    loho = []
    weight_grid = [index / 100.0 for index in range(201)]
    for heldout in ("H01", "H02", "H03"):
        training = [point for house, points in point_rows.items() if house != heldout for point in points]
        selected_weight = min(weight_grid, key=lambda weight: (ratio_correct(training, weight)[0], weight))
        test_points = point_rows[heldout]
        corrected_nll, corrected_brier = ratio_correct(test_points, selected_weight)
        persistence_nll, persistence_brier = ratio_correct(test_points, 0.0)
        loho.append({
            "heldout_house": heldout,
            "training_houses": [house for house in ("H01", "H02", "H03") if house != heldout],
            "selected_ratio_weight": selected_weight,
            "corrected_nll": corrected_nll,
            "persistence_nll": persistence_nll,
            "nll_improvement": persistence_nll - corrected_nll,
            "corrected_brier": corrected_brier,
            "persistence_brier": persistence_brier,
            "brier_improvement": persistence_brier - corrected_brier,
            "nll_pass": corrected_nll < persistence_nll,
            "brier_pass": corrected_brier < persistence_brier,
        })
    loho_gate = {
        "nll_improved_houses": sum(row["nll_pass"] for row in loho),
        "brier_improved_houses": sum(row["brier_pass"] for row in loho),
    }
    loho_gate["pass"] = loho_gate["nll_improved_houses"] >= 2 and loho_gate["brier_improved_houses"] >= 2
    fixed_ratio = []
    for heldout in ("H01", "H02", "H03"):
        corrected_nll, corrected_brier = ratio_correct(point_rows[heldout], 1.0)
        persistence_nll, persistence_brier = ratio_correct(point_rows[heldout], 0.0)
        fixed_ratio.append({
            "house": heldout,
            "ratio_weight": 1.0,
            "nll_improvement": persistence_nll - corrected_nll,
            "brier_improvement": persistence_brier - corrected_brier,
            "nll_pass": corrected_nll < persistence_nll,
            "brier_pass": corrected_brier < persistence_brier,
        })
    fixed_ratio_gate = {
        "nll_improved_houses": sum(row["nll_pass"] for row in fixed_ratio),
        "brier_improved_houses": sum(row["brier_pass"] for row in fixed_ratio),
    }
    fixed_ratio_gate["pass"] = (fixed_ratio_gate["nll_improved_houses"] >= 2 and
                                fixed_ratio_gate["brier_improved_houses"] >= 2)
    result = {
        "contract": "CSTAR_SENSOR_HIT_PROBABILITY_SCREEN_V1",
        "threshold_ppm": args.threshold_ppm,
        "input_contract": report.get("contract"),
        "input_sha256": __import__("hashlib").sha256(args.input.read_bytes()).hexdigest(),
        "houses": houses,
        "gate": gate,
        "loho_source_context_ratio": loho,
        "loho_ratio_gate": loho_gate,
        "fixed_unit_source_context_ratio": fixed_ratio,
        "fixed_unit_ratio_gate": fixed_ratio_gate,
        "verdict": "FIXED_UNIT_RATIO_GATE_PASS" if fixed_ratio_gate["pass"] else "FIXED_UNIT_RATIO_GATE_NO_GO",
        "limits": [
            "truth source is evaluator-only",
            "route samples are scored individually, not as StopAndMeasure block averages",
            "same frozen forecasts and scales as the physical-prior diagnostic",
            "no posterior, controller, or closed-loop efficacy claim",
        ],
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"houses": houses, "gate": gate, "loho": loho,
                      "loho_gate": loho_gate, "fixed_ratio": fixed_ratio,
                      "fixed_ratio_gate": fixed_ratio_gate,
                      "verdict": result["verdict"]}, indent=2))


if __name__ == "__main__":
    main()
