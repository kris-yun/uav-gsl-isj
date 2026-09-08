"""Toy gate for event-time sequential assimilation versus retrospective rewrite."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def expit(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def bernoulli_log_likelihood(outcome: int, probability: float) -> float:
    return math.log(probability if outcome else 1.0 - probability)


def normalized(log_weights: list[float]) -> list[float]:
    offset = max(log_weights)
    values = [math.exp(value - offset) for value in log_weights]
    total = sum(values)
    return [value / total for value in values]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    # Candidate-relative effects switch with the transport regime.  Each event
    # must retain the regime under which its sensing action was executed.
    effects_by_window = [(-1.2, 0.4, 0.8), (0.7, -1.0, 0.3)]
    outcomes_by_window = [(0, 1), (1, 0)]
    nuisance_by_window = (-2.0, 2.5)
    log_weights = [0.0, 0.0, 0.0]
    for effects, outcomes, nuisance in zip(
        effects_by_window, outcomes_by_window, nuisance_by_window
    ):
        centered = [value - sum(effects) / len(effects) for value in effects]
        for candidate, effect in enumerate(centered):
            for outcome in outcomes:
                log_weights[candidate] += bernoulli_log_likelihood(outcome, expit(effect))
    sequential = normalized(log_weights)

    # The invalid retrospective implementation scores both old and new outcomes
    # using only the latest transport effects.
    latest = effects_by_window[-1]
    latest_centered = [value - sum(latest) / len(latest) for value in latest]
    rewritten = normalized(
        [
            sum(
                bernoulli_log_likelihood(outcome, expit(effect))
                for outcomes in outcomes_by_window
                for outcome in outcomes
            )
            for effect in latest_centered
        ]
    )
    # Common nuisance never enters the centred effects; perturb it strongly and
    # require the sequential answer to remain unchanged.
    nuisance_perturbed = (-20.0, 20.0)
    invariant_log_weights = [0.0, 0.0, 0.0]
    for effects, outcomes, _ in zip(
        effects_by_window, outcomes_by_window, nuisance_perturbed
    ):
        logits = [effects[candidate] for candidate in range(len(effects))]
        centered = [value - sum(logits) / len(logits) for value in logits]
        for candidate, effect in enumerate(centered):
            for outcome in outcomes:
                invariant_log_weights[candidate] += bernoulli_log_likelihood(
                    outcome, expit(effect)
                )
    invariant = normalized(invariant_log_weights)
    invariance_error = max(abs(a - b) for a, b in zip(sequential, invariant))
    rewrite_distance = sum(abs(a - b) for a, b in zip(sequential, rewritten))
    gate = {
        "contract": "CSTAR_CORE_M1_SEQUENTIAL_EVENT_TIME_V1",
        "sequential_posterior": sequential,
        "retrospectively_rewritten_posterior": rewritten,
        "common_nuisance_invariance_error": invariance_error,
        "retrospective_rewrite_l1_distance": rewrite_distance,
        "pass": invariance_error < 1.0e-12 and rewrite_distance > 0.1,
        "limits": [
            "toy structural check only",
            "does not establish real PMFS transport-window adequacy",
            "does not establish closed-loop utility",
        ],
    }
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(gate, indent=2))
    if not gate["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
