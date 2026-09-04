#!/usr/bin/env python3
"""Deterministic correctness tests for CTPI-G2 proper H2 EID."""
from __future__ import annotations

import numpy as np

from ctpi_g2_m3_nonmyopic import (
    entropy,
    horizon2_eid,
    marginalize_uniform_free_placements,
    myopic_eid,
    posterior_branches,
    predicted_concentration_exploit_scores,
)


def selftest() -> None:
    prior = np.asarray([0.5, 0.5], dtype=np.float64)
    likelihood = np.asarray([
        [0.5, 0.5],
        [0.05, 0.95],
    ])
    score = myopic_eid(prior, likelihood)
    assert score[1] > score[0] + 1.0e-12

    branches = posterior_branches(prior, likelihood)
    np.testing.assert_allclose(branches.probability[:, 0], [0.5, 0.5], atol=1e-15)
    np.testing.assert_allclose(branches.posterior[:, 0], np.tile(prior, (2, 1)), atol=1e-15)
    assert entropy(branches.posterior[0, 1]) < entropy(prior)
    assert entropy(branches.posterior[1, 1]) < entropy(prior)
    assert not np.allclose(branches.posterior[0, 1], branches.posterior[1, 1])

    # Exact zero-probability branches stay finite and normalized.
    deterministic = np.asarray([[0.0, 0.0], [1.0, 1.0]])
    det_branches = posterior_branches(prior, deterministic)
    assert np.isfinite(det_branches.posterior).all()
    np.testing.assert_allclose(det_branches.posterior.sum(axis=2), 1.0, atol=1e-15)

    # Constructed three-source case: y=0 and y=1 after action 0 prefer
    # different second actions.  This would fail for an expected-observation
    # shortcut because that shortcut creates only one synthetic posterior.
    tri_prior = np.asarray([0.34, 0.33, 0.33])
    tri_likelihood = np.asarray([
        [0.05, 0.50, 0.95],
        [0.05, 0.95, 0.50],
        [0.50, 0.05, 0.95],
        [0.95, 0.50, 0.05],
    ])
    h2 = horizon2_eid(tri_prior, tri_likelihood, allow_repeat=False)
    assert h2.branch_best_action[0, 0] != h2.branch_best_action[1, 0]
    assert np.all(h2.value >= h2.immediate - 1.0e-12)
    np.testing.assert_allclose(h2.branch_probability.sum(axis=0), 1.0, atol=1e-15)

    # Horizon degeneration: no feasible second action yields exact myopic EID.
    none = np.zeros((len(tri_likelihood), len(tri_likelihood)), dtype=bool)
    degenerate = horizon2_eid(tri_prior, tri_likelihood, second_feasible=none)
    np.testing.assert_allclose(degenerate.value, degenerate.immediate, atol=1e-15)

    # Region-valued source state: obstacle placement 1 is excluded, then free
    # placements receive fixed equal weights within each carrier.
    placement_probability = np.asarray([
        [0.1, 0.2],  # u0, free, carrier 0
        [0.9, 0.9],  # u1, obstacle, carrier 0
        [0.5, 0.7],  # u2, free, carrier 0
        [0.8, 0.4],  # u3, free, carrier 1
    ])
    marginalized, weights = marginalize_uniform_free_placements(
        placement_probability,
        carrier_placements=[[0, 1, 2], [3]],
        free_placement=np.asarray([True, False, True, True]),
    )
    np.testing.assert_allclose(weights[0], [0.5, 0.0, 0.5, 0.0], atol=1e-15)
    np.testing.assert_allclose(weights[1], [0.0, 0.0, 0.0, 1.0], atol=1e-15)
    np.testing.assert_allclose(marginalized, [[0.3, 0.8], [0.45, 0.4]], atol=1e-15)

    # Audit/freeze of the old benchmark's exploit definition.
    concentration = np.asarray([[1.0, 0.0, 0.1], [0.0, 2.0, 0.1]])
    exploit = predicted_concentration_exploit_scores([0.75, 0.25], concentration)
    np.testing.assert_allclose(exploit, [0.75, 0.5, 0.1], atol=1e-15)
    assert int(np.argmax(exploit)) == 0

    print("CTPI_G2_M3_PROPER_H2_SELFTEST=PASS")
    print("CTPI_G2_M3_BRANCH_POSTERIORS_DIFFER=PASS")
    print("CTPI_G2_M3_BRANCH_ACTIONS_DIFFER=PASS")
    print("CTPI_G2_M3_CARRIER_MARGINALIZATION=PASS")


if __name__ == "__main__":
    selftest()
