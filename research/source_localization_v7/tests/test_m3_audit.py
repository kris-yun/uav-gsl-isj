"""Analytic and finite-enumeration checks, run with standard unittest.

These are finite-channel checks. They are not physical plume calibration or
evidence that any particular simulator-fitted probability table is correct.
"""
from itertools import product
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from gsl_discrimination.channel import FiniteChannel, JointPosterior
from gsl_discrimination.m3_audit import (
    AuditLedger, CoveragePlanner, ImpossibleObservationError,
    cost_aware_allocation, pairwise_kl,
)


def make_channel(probabilities, costs=None):
    p = np.asarray(probabilities, dtype=float)
    a, s, _, _ = p.shape
    return FiniteChannel(
        p, np.ones(a) if costs is None else np.asarray(costs),
        np.column_stack((np.arange(s), np.zeros(s))),
        [f"a{k}" for k in range(a)], [f"s{k}" for k in range(s)],
    )


def binary_channel(probability_one, costs=None):
    p = np.asarray(probability_one, dtype=float)
    return make_channel(np.stack((1 - p, p), axis=-1), costs)


class CostAllocationTests(unittest.TestCase):
    def test_resource_fractions_are_not_sampling_frequencies(self):
        # To balance evidence: lambda_0=9*lambda_1. Cost=1.8, evidence=.9.
        d = np.array([[1.0, 0.0], [0.0, 9.0]])
        costs = np.array([1.0, 9.0])
        result = cost_aware_allocation(d, costs)
        assert_allclose(result.probabilities, [0.9, 0.1], atol=1e-10)
        assert_allclose(result.resource_fractions, [0.5, 0.5], atol=1e-10)
        self.assertAlmostEqual(result.value, 0.5)
        self.assertAlmostEqual(costs @ result.observations_per_cost, 1.0)
        naive = min(np.array([0.5, 0.5]) @ d) / (np.array([0.5, 0.5]) @ costs)
        self.assertAlmostEqual(naive, 0.1)

    def test_two_source_lp_collapses_to_best_divergence_per_cost(self):
        result = cost_aware_allocation(np.array([[1.0], [4.0], [3.0]]), np.array([1.0, 5.0, 2.0]))
        assert_allclose(result.probabilities, [0.0, 0.0, 1.0])
        self.assertAlmostEqual(result.value, 1.5)

    def test_weak_positive_differences_survive_solver_scaling(self):
        result = cost_aware_allocation(np.array([[1e-10, 0.0], [0.0, 9e-10]]), np.array([1.0, 9.0]))
        assert_allclose(result.probabilities, [0.9, 0.1], atol=1e-10)
        self.assertAlmostEqual(result.value / 1e-10, 0.5)


class CoveragePlannerTests(unittest.TestCase):
    def setUp(self):
        # s0 and s1 cannot be separated; s2 is distinguishable at action 1.
        self.channel = binary_channel([
            [[0.5], [0.5], [0.5]],
            [[0.1], [0.1], [0.9]],
            [[0.4], [0.4], [0.6]],
        ], [1.0, 2.0, 4.0])

    def test_zero_pair_does_not_cause_eig_fallback_or_drop_low_prior_source(self):
        posterior = np.array([1 - 1e-15, 5e-16, 5e-16])
        plan = CoveragePlanner(epsilon=0.3).plan(self.channel, self.channel.marginal(), posterior, 0)
        self.assertEqual(plan.info["reason"], "zero_maxmin_challenge")
        self.assertEqual(plan.info["challenger"], 2)
        self.assertEqual(plan.info["legal_sources"], [0, 1, 2])
        self.assertEqual(plan.info["lp_opponents"], [1, 2])
        self.assertIn([0, 1], plan.info["zero_pairs"])
        self.assertAlmostEqual(plan.info["lp_value_per_cost"], 0.0)
        assert_allclose(plan.probabilities, [0.1, 0.8, 0.1])
        self.assertAlmostEqual(plan.info["expected_total_cost_per_step"], plan.probabilities @ self.channel.costs)
        self.assertAlmostEqual(plan.info["coverage_expected_cost_per_step"], 0.7)
        self.assertTrue(plan.info["no_automatic_stopping"])

    def test_explicit_unidentifiable_challenger_returns_coverage(self):
        nu = np.array([0.2, 0.3, 0.5])
        plan = CoveragePlanner(coverage=nu).plan(
            self.channel, self.channel.marginal(), [1.0, 0.0, 0.0], 2, challenger=1,
        )
        assert_allclose(plan.probabilities, nu)
        self.assertEqual(plan.info["reason"], "indistinguishable_pair_coverage")
        self.assertEqual(plan.info["challenger"], 1)

    def test_tube_only_restricts_lp_and_challenge_can_escape(self):
        plan = CoveragePlanner(epsilon=0.3).plan(
            self.channel, self.channel.marginal(), [1.0, 0.0, 0.0], 0,
            exploit_mask=np.array([True, False, False]),
        )
        self.assertEqual(plan.info["reason"], "tube_escape_challenge")
        self.assertTrue(plan.info["escaped_exploit_mask"])
        assert_allclose(plan.probabilities, [0.1, 0.8, 0.1])
        self.assertTrue(np.all(plan.probabilities >= 0.1 - 1e-15))

    def test_positive_lp_respects_tube_but_coverage_stays_global(self):
        channel = binary_channel([[[0.1], [0.9]], [[0.2], [0.8]], [[0.3], [0.7]]])
        plan = CoveragePlanner(epsilon=0.3).plan(
            channel, channel.marginal(), [0.999999999, 0.000000001], 0,
            exploit_mask=np.array([False, True, False]),
        )
        self.assertEqual(plan.info["reason"], "full_cost_maxmin")
        assert_allclose(plan.probabilities, [0.1, 0.8, 0.1])
        self.assertFalse(plan.info["escaped_exploit_mask"])

    def test_support_singular_channels_are_reported_without_silent_smoothing(self):
        channel = binary_channel([[[0.0], [1.0]], [[0.5], [0.5]]], [2.0, 1.0])
        kl = pairwise_kl(channel.marginal())
        self.assertTrue(np.isinf(kl[0, 0, 1]))
        plan = CoveragePlanner(epsilon=0.2).plan(channel, channel.marginal(), [0.99, 0.01], 0)
        self.assertEqual(plan.info["reason"], "support_singular_challenge")
        assert_allclose(plan.probabilities, [0.9, 0.1])

    def test_coverage_floor_is_independent_of_extreme_prior_and_returns_actions(self):
        planner = CoveragePlanner(epsilon=1.0, coverage=[0.2, 0.3, 0.5], rng=np.random.default_rng(72))
        plan = planner.plan(self.channel, self.channel.marginal(), [0.0, 0.0, 1.0], 0)
        assert_allclose(plan.probabilities, [0.2, 0.3, 0.5])
        self.assertIn(plan.action, range(3))
        self.assertTrue(plan.info["coverage_draw"])


class AuditLedgerTests(unittest.TestCase):
    def test_shared_nuisance_is_max_of_products_not_product_of_maxima(self):
        channel = binary_channel([[[0.1, 0.9], [0.5, 0.5]]])
        ledger = AuditLedger(channel)
        for t, outcome in enumerate([1, 0]):
            ledger.prepare(0)
            ledger.update(0, outcome, f"event-{t}")
        assert_allclose(np.exp(ledger.log_likelihood[0]), [0.09, 0.09])
        self.assertAlmostEqual(np.exp(ledger.log_e_values[0]), 0.25 / 0.09)
        self.assertNotAlmostEqual(np.exp(ledger.log_e_values[0]), 0.25 / 0.81)

    def test_prequential_alternative_equals_fixed_mixture_path_likelihood(self):
        channel = binary_channel([
            [[0.1, 0.3], [0.6, 0.9], [0.2, 0.8]],
            [[0.4, 0.2], [0.9, 0.7], [0.8, 0.3]],
        ])
        ledger = AuditLedger(channel)
        likelihood = np.ones(channel.shape[1:3])
        for t, (action, outcome) in enumerate([(0, 1), (1, 0), (0, 1)]):
            q = ledger.prepare(action)
            assert_allclose(q.sum(1), 1.0)
            ledger.update(action, outcome, t)
            likelihood *= channel.probabilities[action, :, :, outcome]
            for null in range(3):
                expected_q = likelihood[np.arange(3) != null].mean()
                self.assertAlmostEqual(np.exp(ledger.log_alt[null]), expected_q)
                self.assertAlmostEqual(np.exp(ledger.log_e_values[null]), expected_q / likelihood[null].max())

    def test_current_list_can_reenter_but_ever_rejected_list_cannot(self):
        channel = binary_channel([[[0.1], [0.9]]])
        ledger = AuditLedger(channel, alpha=0.2)
        ledger.prepare(0)
        first = ledger.update(0, 1, "first")
        self.assertEqual(first.compatible_now, (1,))
        ledger.prepare(0)
        second = ledger.update(0, 0, "second")
        self.assertEqual(second.compatible_now, (0, 1))
        self.assertEqual(second.not_rejected_since_start, (1,))
        assert_allclose(second.log_e_values, [0.0, 0.0], atol=1e-14)

    def test_fresh_audit_does_not_inherit_wrong_prior_or_update_posterior_twice(self):
        channel = binary_channel([[[0.5], [0.5]], [[0.1], [0.9]]], [1.0, 2.0])
        posterior = JointPosterior(channel, [1 - 1e-9, 1e-9])
        ledger = AuditLedger(channel, alpha=0.05)
        self.assertEqual(ledger.compatible_now, (0, 1))
        assert_allclose(ledger.log_e_values, 0.0)
        plan = CoveragePlanner().plan(channel, posterior.predict(), posterior.source, 0)
        self.assertTrue(np.all(plan.probabilities > 0))
        for t in range(14):
            ledger.prepare(1)
            posterior.update(1, 1, t)
            after_single_raw_update = posterior.source.copy()
            ledger.update(1, 1, t)
            assert_allclose(posterior.source, after_single_raw_update)
        self.assertGreater(posterior.source[1], 0.999)
        self.assertEqual(len(posterior.events), 14)
        self.assertEqual(len(ledger.events), 14)
        self.assertEqual(ledger.snapshot().total_cost, 28.0)

    def test_missing_prepare_duplicate_and_wrong_action_are_atomic(self):
        channel = binary_channel([[[0.1], [0.9]], [[0.3], [0.7]]])
        ledger = AuditLedger(channel)
        with self.assertRaises(RuntimeError):
            ledger.update(0, 1, "one")
        ledger.prepare(0)
        with self.assertRaises(ValueError):
            ledger.update(1, 1, "one")
        self.assertEqual(len(ledger.events), 0)
        ledger.update(0, 1, "one")
        before = ledger.log_likelihood
        ledger.prepare(1)
        with self.assertRaises(ValueError):
            ledger.update(1, 0, "one")
        assert_array_equal(ledger.log_likelihood, before)
        self.assertEqual(ledger.pending_action, 1)
        ledger.update(1, 0, "two")
        self.assertEqual(len(ledger.events), 2)
        assert_array_equal(ledger.action_counts, [1, 1])

    def test_prepared_law_is_frozen_before_the_observation(self):
        channel = binary_channel([[[0.1], [0.9]]])
        ledger = AuditLedger(channel)
        current_table = channel.probabilities.copy()
        ledger.prepare(0, probabilities=current_table, model_version="past-0")
        current_table[0, 0, 0] = [0.99, 0.01]
        ledger.update(0, 1, "one")
        self.assertAlmostEqual(np.exp(ledger.log_likelihood[0, 0]), 0.1)
        self.assertEqual(ledger.events[0]["model_version"], "past-0")

    def test_globally_impossible_outcome_is_model_failure_not_fake_confidence(self):
        # A shared bit flips both sensor bits, so 01 and 10 are impossible.
        joint = np.array([[[[0.9, 0.0, 0.0, 0.1], [0.8, 0.0, 0.0, 0.2]],
                           [[0.1, 0.0, 0.0, 0.9], [0.2, 0.0, 0.0, 0.8]]]])
        channel = make_channel(joint)
        ledger = AuditLedger(channel)
        ledger.prepare(0)
        with self.assertRaises(ImpossibleObservationError):
            ledger.update(0, 1, "impossible")
        self.assertEqual(len(ledger.events), 0)
        assert_allclose(ledger.log_likelihood, 0.0)
        ledger.update(0, 3, "valid")
        self.assertAlmostEqual(np.exp(ledger.log_e_values[0]), 0.85 / 0.2)
        self.assertIn("model-relative", ledger.snapshot().guarantee_scope)

    def test_zero_alternative_path_stays_zero_and_never_creates_zero_over_zero(self):
        # After observing 1, null s0 is impossible and the alternative to s1
        # has zero path mass. Subsequent predictions on that zero-mass branch
        # may be arbitrary normalized laws; cumulative alternative mass is 0.
        channel = binary_channel([[[0.0], [1.0]]])
        ledger = AuditLedger(channel)
        for t in range(3):
            prediction = ledger.prepare(0)
            assert_allclose(prediction.sum(1), 1.0)
            snapshot = ledger.update(0, 1, t)
            self.assertFalse(np.isnan(snapshot.log_e_values).any())
            self.assertTrue(np.isposinf(snapshot.log_e_values[0]))
            self.assertTrue(np.isneginf(snapshot.log_e_values[1]))
            self.assertEqual(snapshot.compatible_now, (1,))
        before = ledger.log_likelihood
        ledger.prepare(0)
        with self.assertRaises(ImpossibleObservationError):
            ledger.update(0, 0, "contradictory-zero-support")
        assert_array_equal(ledger.log_likelihood, before)
        self.assertEqual(len(ledger.events), 3)

    def test_anytime_error_bound_by_exact_finite_enumeration(self):
        # Enumerate every path under each fixed nuisance, with adaptive actions.
        # Checking every prefix verifies the crossing event, not just final e.
        channel = binary_channel([
            [[0.15, 0.35], [0.70, 0.85]],
            [[0.40, 0.20], [0.80, 0.60]],
        ])
        alpha, horizon = 0.2, 7
        crossing_probabilities = []
        for true_source, true_nuisance in product(range(2), repeat=2):
            crossing_probability = 0.0
            total_probability = 0.0
            for outcomes in product(range(2), repeat=horizon):
                ledger = AuditLedger(channel, alpha=alpha)
                path_probability = 1.0
                crossed = False
                history_sum = 0
                for t, outcome in enumerate(outcomes):
                    action = (history_sum + t) % 2
                    ledger.prepare(action)
                    snapshot = ledger.update(action, outcome, t)
                    path_probability *= channel.probabilities[action, true_source, true_nuisance, outcome]
                    crossed |= snapshot.max_log_e_values[true_source] >= np.log(1 / alpha)
                    history_sum += outcome
                total_probability += path_probability
                crossing_probability += path_probability * crossed
            self.assertAlmostEqual(total_probability, 1.0, places=12)
            self.assertLessEqual(crossing_probability, alpha + 1e-12)
            crossing_probabilities.append(crossing_probability)
        self.assertGreater(max(crossing_probabilities), 0.0)  # the check is not vacuous


if __name__ == "__main__":
    unittest.main()
