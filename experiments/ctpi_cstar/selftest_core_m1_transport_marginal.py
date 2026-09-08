"""Analytic checks for M1E transport-nuisance marginalization."""

import json
import math


observations = [1, 0, 1, 1]
member_probabilities = [
    [0.80, 0.25, 0.65, 0.75],
    [0.55, 0.40, 0.60, 0.50],
    [0.70, 0.30, 0.45, 0.65],
]


def likelihood(probabilities):
    value = 1.0
    for outcome, probability in zip(observations, probabilities):
        value *= probability if outcome else 1.0 - probability
    return value


member_likelihoods = [likelihood(row) for row in member_probabilities]
marginal = sum(member_likelihoods) / len(member_likelihoods)
permuted = sum(reversed(member_likelihoods)) / len(member_likelihoods)
duplicated_identical = sum([member_likelihoods[0]] * 3) / 3

report = {
    "contract": "CSTAR_CORE_M1_TRANSPORT_MARGINAL_V1",
    "member_likelihoods": member_likelihoods,
    "marginal_likelihood": marginal,
    "member_permutation_error": abs(marginal - permuted),
    "identical_member_idempotence_error": abs(duplicated_identical - member_likelihoods[0]),
    "single_member_log_likelihood_range": max(map(math.log, member_likelihoods))
    - min(map(math.log, member_likelihoods)),
    "pass": abs(marginal - permuted) < 1.0e-15
    and abs(duplicated_identical - member_likelihoods[0]) < 1.0e-15
    and min(member_likelihoods) <= marginal <= max(member_likelihoods),
    "limits": [
        "finite toy marginalization only",
        "three replicas approximate rather than exactly integrate transport nuisance",
        "does not establish closed-loop utility",
    ],
}

print(json.dumps(report, indent=2))
if not report["pass"]:
    raise SystemExit(1)
