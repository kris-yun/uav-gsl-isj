from __future__ import annotations

import math

from cstar_reference import (
    CPORouteLaw,
    bhattacharyya_coefficient,
    first_passage_to_encounter_cdf,
    hazards_to_first_passage,
    prospective_resolution_scores,
    route_committor,
    select_route,
)


def close(a, b, tol=1e-12):
    assert abs(a - b) <= tol, (a, b)


def main():
    # Exact first-passage factorization.
    law = hazards_to_first_passage([0.2, 0.5, 1.0])
    expected = [0.2, 0.4, 0.4, 0.0]
    for a, b in zip(law, expected):
        close(a, b)
    cdf = first_passage_to_encounter_cdf(law)
    for a, b in zip(cdf, [0.2, 0.6, 1.0]):
        close(a, b)
    close(route_committor(law), 1.0)

    # Identical laws are maximally confusable; disjoint laws are separable.
    close(bhattacharyya_coefficient([1, 0], [1, 0]), 1.0)
    close(bhattacharyya_coefficient([1, 0], [0, 1]), 0.0)

    # Route 0: identical source predictions => resolution 0.
    # Route 1: perfectly disjoint source predictions => resolution 1.
    route_laws = [
        [[0.5, 0.5], [1.0, 0.0]],
        [[0.5, 0.5], [0.0, 1.0]],
    ]
    scores = prospective_resolution_scores([0.5, 0.5], route_laws)
    close(scores[0].resolution, 0.0)
    close(scores[1].resolution, 1.0)
    chosen = select_route([0.5, 0.5], route_laws, [0.1, 10.0])
    assert chosen.route_index == 1  # information wins; distance is tie-break only

    # With tied information, shorter route wins deterministically.
    tied = [
        [[0.5, 0.5], [0.5, 0.5]],
        [[0.5, 0.5], [0.5, 0.5]],
    ]
    assert select_route([0.5, 0.5], tied, [4.0, 2.0]).route_index == 1

    # Degenerate posterior means there is no remaining hypothesis pair.
    degenerate = prospective_resolution_scores([1.0, 0.0], route_laws)
    assert all(
        item.resolution == 0.0 and item.pair_weight_sum == 0.0
        for item in degenerate
    )

    # M2 contract consistency: route committor = 1 - no-hit probability.
    cpo = CPORouteLaw.from_hazards(
        [0.1, 0.25, 0.4],
        [math.log1p(0.1), math.log1p(0.2), math.log1p(0.3)],
        [0.2, 0.2, 0.2],
    )
    close(cpo.route_committor, 1.0 - cpo.first_hit_prob[-1])
    assert all(
        cpo.encounter_cdf[i] <= cpo.encounter_cdf[i + 1]
        for i in range(len(cpo.encounter_cdf) - 1)
    )

    # Input failures are loud, not silently renormalized from negative values.
    try:
        hazards_to_first_passage([0.2, -0.1])
        raise AssertionError("negative hazard accepted")
    except ValueError:
        pass

    print("CSTAR_REFERENCE_SELFTEST PASS")


if __name__ == "__main__":
    main()
