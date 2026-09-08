"""Analytic falsification tests for CORE-M1's nuisance cancellation.

This is a formula test, not a closed-loop efficacy claim.  Under the frozen
structural model logit P(Y=1 | do(A), S=s) = b + tau_s(A), candidate-centred
log-odds must remove every candidate-common shift b exactly.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def expit(value: float) -> float:
    if value >= 0.0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def logit(probability: float) -> float:
    return math.log(probability) - math.log1p(-probability)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    nuisance_shifts = (-4.0, -1.5, 0.0, 2.0, 4.0)
    source_effects = (-1.5, -0.2, 0.3, 1.4)
    expected = [value - sum(source_effects) / len(source_effects) for value in source_effects]
    centered_rows = []
    legacy_rows = []
    for nuisance in nuisance_shifts:
        probabilities = [expit(nuisance + effect) for effect in source_effects]
        logits = [logit(value) for value in probabilities]
        centered = [value - sum(logits) / len(logits) for value in logits]
        probability_context = sum(probabilities) / len(probabilities)
        legacy = [value - logit(probability_context) for value in logits]
        centered_rows.append(centered)
        legacy_rows.append(legacy)

    max_centered_error = max(
        abs(actual - target)
        for row in centered_rows
        for actual, target in zip(row, expected)
    )
    max_legacy_drift = max(
        abs(legacy_rows[i][j] - legacy_rows[0][j])
        for i in range(1, len(legacy_rows))
        for j in range(len(source_effects))
    )
    permuted = list(reversed(source_effects))
    permuted_logits = [logit(expit(2.0 + effect)) for effect in permuted]
    permuted_residual = [
        value - sum(permuted_logits) / len(permuted_logits) for value in permuted_logits
    ]
    expected_permuted = list(reversed(expected))
    max_permutation_error = max(
        abs(actual - target)
        for actual, target in zip(permuted_residual, expected_permuted)
    )
    null_logits = [logit(expit(3.0)) for _ in source_effects]
    max_null_residual = max(
        abs(value - sum(null_logits) / len(null_logits)) for value in null_logits
    )

    gate = {
        "contract": "CSTAR_CORE_M1_ANALYTIC_INVARIANCE_V1",
        "structural_model": "logit P(Y=1 | do(A), S=s) = b_i + tau_s(A)",
        "operator": "logit(p_s) - mean_j(logit(p_j))",
        "max_centered_nuisance_error": max_centered_error,
        "max_candidate_permutation_error": max_permutation_error,
        "max_null_source_residual": max_null_residual,
        "legacy_logit_of_mean_max_nuisance_drift": max_legacy_drift,
        "pass": (
            max_centered_error < 1.0e-12
            and max_permutation_error < 1.0e-12
            and max_null_residual < 1.0e-12
            and max_legacy_drift > 1.0e-3
        ),
        "limits": [
            "proves only the stated algebraic invariance",
            "does not establish that the real PMFS nuisance is exactly additive on log-odds",
            "does not establish predictive or closed-loop utility",
        ],
    }
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=False)
        args.output.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(gate, indent=2))
    if not gate["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
