"""Independent finite-model checks for fixed-source U / transport K mixing.

No ROS, simulator, House data, source labels, or protected bank is read.
This checks the mathematical contract, not native runtime efficacy.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
import json
import math


def conditional_likelihood(probabilities, hits):
    return math.prod(p if y else 1.0 - p for p, y in zip(probabilities, hits))


def context_for(candidates):
    source_count = len(candidates)
    points = len(candidates[0])
    members = len(candidates[0][0])
    events = len(candidates[0][0][0])
    if points != 4 or any(len(c) != points for c in candidates):
        raise ValueError("SOURCE_SUPPORT_COUNT")
    if any(len(p) != members or any(len(k) != events for k in p)
           for c in candidates for p in c):
        raise ValueError("INDEPENDENT_U_K_DIMENSION")
    return [[sum(sum(c[u][k][e] for u in range(points)) / points for c in candidates) / source_count
             for e in range(events)] for k in range(members)]


def score(candidate, context, hits, concentration, threshold):
    def clip(p):
        return min(1 - 1e-4, max(1e-4, p))

    def logit(p):
        p = clip(p)
        return math.log(p) - math.log1p(-p)

    point_scores = []
    for point in candidate:
        member_scores = []
        for k, probabilities in enumerate(point):
            previous = 0.0
            factors = []
            for e, probability in enumerate(probabilities):
                persistence = 0.5 * math.erfc((math.log1p(threshold) - math.log1p(previous)) / math.sqrt(2))
                eta = logit(persistence) + logit(probability) - logit(context[k][e])
                corrected = clip(1 / (1 + math.exp(-eta)))
                factors.append(corrected if hits[e] else 1 - corrected)
                previous = concentration[e]
            member_scores.append(math.prod(factors))
        point_scores.append(sum(member_scores) / len(member_scores))
    return sum(point_scores) / len(point_scores), point_scores


def main():
    # Two observations disagree about which fixed source is plausible.
    # Refreshing the unknown source between observations spuriously raises
    # evidence from .09 to .25.
    points = [[.9, .1], [.1, .9], [.9, .1], [.1, .9]]
    fixed_source = sum(conditional_likelihood(p, [1, 1]) for p in points) / 4
    pooled_first = conditional_likelihood([sum(p[e] for p in points) / 4 for e in range(2)], [1, 1])
    assert math.isclose(fixed_source, .09) and math.isclose(pooled_first, .25)

    candidates = [
        [[[.85, .10, .65], [.65, .25, .40]],
         [[.10, .85, .25], [.20, .70, .50]],
         [[.60, .20, .85], [.50, .40, .65]],
         [[.25, .60, .10], [.35, .55, .20]]],
        [[[.30, .65, .70], [.40, .50, .45]],
         [[.75, .25, .30], [.60, .20, .35]],
         [[.20, .45, .55], [.10, .60, .75]],
         [[.45, .75, .15], [.55, .80, .20]]],
    ]
    hits, measured, threshold = [1, 0, 1], [.4, .03, .7], .1
    context = context_for(candidates)
    scores = [score(c, context, hits, measured, threshold)[0] for c in candidates]
    # Reordering U independently in each region must not alter the shared
    # context or scores. A flattened U-by-K context can violate this.
    permuted = [list(reversed(candidates[0])), [candidates[1][i] for i in (2, 0, 3, 1)]]
    permuted_context = context_for(permuted)
    permuted_scores = [score(c, permuted_context, hits, measured, threshold)[0] for c in permuted]
    assert max(abs(a - b) for row_a, row_b in zip(context, permuted_context)
               for a, b in zip(row_a, row_b)) < 1e-15
    assert max(abs(a - b) for a, b in zip(scores, permuted_scores)) < 1e-15

    identical = [[candidate[0]] * 4 for candidate in candidates]
    identical_context = context_for(identical)
    for candidate in identical:
        mixture, components = score(candidate, identical_context, hits, measured, threshold)
        assert max(components) - min(components) == 0 and mixture == components[0]

    invalid = [[point[:] for point in candidate] for candidate in candidates]
    invalid[0][0] = invalid[0][0][:1]
    try:
        context_for(invalid)
    except ValueError as error:
        assert str(error) == "INDEPENDENT_U_K_DIMENSION"
    else:
        raise AssertionError("mismatched K was accepted")

    with localcontext() as decimal_context:
        decimal_context.prec = 60
        # A mathematical long-prefix reference. The native long-double
        # implementation must fail explicitly if its own range is exceeded.
        tiny_components = [Decimal("0.0001") ** 400] * 4
        tiny_mixture = sum(tiny_components) / 4
        assert tiny_mixture == Decimal("1e-1600")

    print(json.dumps({
        "contract": "M1R_FIXED_SOURCE_QUADRATURE_MATH_V1",
        "status": "MATHEMATICAL_CONTRACT_PASS",
        "source_points": 4, "weights": [.25] * 4,
        "quadrature_fractions": [[.25, .25], [.25, .75], [.75, .25], [.75, .75]],
        "correct_fixed_source_mixture": fixed_source,
        "incorrect_eventwise_source_refresh": pooled_first,
        "independent_region_U_permutation_error": max(abs(a - b) for a, b in zip(scores, permuted_scores)),
        "component_idempotence": True, "dimension_rejection": True,
        "exact_tiny_mixture_decimal_reference": str(tiny_mixture),
        "limits": ["finite four-point approximation, not exact regional integration",
                   "not a C++ build or runtime result", "not source identification or closed-loop utility",
                   "shared random streams are not per-filament noise matching after different exits"],
    }, indent=2))


if __name__ == "__main__":
    main()
