"""Targeted behavior/causality tests; synthetic scales are not UAV calibration."""

import unittest
import numpy as np

from gsl_discrimination.m2_boundary import (
    BoundaryEvent, BoundaryMemoryConfig, CausalBoundaryMemory,
    FormationGeometry, LocalWind, ReturnTube, rank_by_maxmin,
    score_paired_formations,
)


def memory_config(**overrides):
    values = dict(mode="entry_only", entry_decay=0.7, entry_gain=0.4,
                  min_pre_s=0.4, min_post_s=0.4, direction_window_s=0.8,
                  max_observation_gap_s=0.25, max_memory_age_s=5.0,
                  min_speed=0.01, max_speed=2.0, timing_validated=True,
                  direction_noise_variance=0.001)
    values.update(overrides)
    return BoundaryMemoryConfig(**values)


def eastward_entry(config=None, offset=(0, 0)):
    memory = CausalBoundaryMemory(config or memory_config())
    for index in range(6):
        time = index * 0.2
        event = BoundaryEvent("entry", 0.6, 0.6, 0.4) if index == 5 else None
        memory.update(timestamp_s=time, position_xy=np.asarray(offset) + [time, 0], heading_rad=0, event=event)
    return memory


def geometry(**overrides):
    values = dict(lower_xy=[-10, -10], upper_xy=[10, 10], min_separation=0.1,
                  max_separation=2.0, linearization_radius=1.0)
    values.update(overrides)
    return FormationGeometry(**values)


def score(means, gradients, **overrides):
    means = np.asarray(means, dtype=float)
    n, ns = means.shape
    values = dict(center_xy=np.zeros((n, 2)), source_means=means,
                  source_gradients=np.asarray(gradients, dtype=float),
                  joint_covariance=np.broadcast_to(np.eye(2), (n, ns, 2, 2)),
                  costs=np.ones(n), separations=[1.0], orientations_rad=[0.0, np.pi / 2],
                  geometry=geometry(), contrast_threshold=1e-10)
    values.update(overrides)
    return score_paired_formations(**values)


class BoundaryMemoryTests(unittest.TestCase):
    def test_nature_gain_update_is_not_silently_normalized(self):
        memory = eastward_entry()
        np.testing.assert_allclose(memory.snapshot().entry_vector, [0.4, 0])
        for index in range(6, 11):
            time = index * 0.2
            event = BoundaryEvent("entry", 1.6, 0.6, 0.4) if index == 10 else None
            memory.update(timestamp_s=time, position_xy=[time, 0], heading_rad=0, event=event)
        np.testing.assert_allclose(memory.snapshot().entry_vector, [0.7 * 0.4 + 0.4, 0])
        self.assertEqual(memory.snapshot().entry_count, 2)
        np.testing.assert_allclose(memory.snapshot().exit_vector, [0, 0])

    def test_return_tube_is_relative_to_current_position(self):
        first_memory = eastward_entry(offset=(9, 5))
        second_memory = eastward_entry(offset=(19, -2))
        kwargs = dict(timestamp_s=1.0, length=3, base_radius=0.1,
                      position_covariance=np.zeros((2, 2)), drift_variance_rate=0,
                      sensor_delay_uncertainty_s=0)
        first = first_memory.make_return_tube(current_position_xy=[10, 5], **kwargs)
        second = second_memory.make_return_tube(current_position_xy=[20, -2], **kwargs)
        self.assertTrue(first.contains([11, 5]))
        self.assertTrue(second.contains([21, -2]))
        self.assertFalse(second.contains([11, 5]))
        np.testing.assert_allclose(first.direction_xy, second.direction_xy)

    def test_memory_is_source_independent_and_not_mutated_by_planning(self):
        memory = eastward_entry()
        before = memory.snapshot()
        tube = memory.make_return_tube(timestamp_s=1.0, current_position_xy=[1, 0],
                                       length=4, base_radius=0.2,
                                       position_covariance=np.zeros((2, 2)),
                                       drift_variance_rate=0, sensor_delay_uncertainty_s=0)
        for gradients in ([[[1, 0], [1, 2]]], [[[8, -4], [-3, 7]]]):
            score([[0, 0]], gradients, center_xy=[[1, 0]], return_tube=tube)
        after = memory.snapshot()
        np.testing.assert_array_equal(before.entry_vector, after.entry_vector)
        np.testing.assert_array_equal(before.entry_covariance, after.entry_covariance)
        self.assertEqual(before.entry_count, after.entry_count)
        self.assertFalse(hasattr(memory, "posterior"))

    def test_real_clock_and_max_gap_are_hard_gates(self):
        memory = eastward_entry()
        for time in (1.0, 0.9, 51.0):
            with self.assertRaises(ValueError):
                memory.update(timestamp_s=time, position_xy=[time, 0], heading_rad=0)
        self.assertEqual(memory.snapshot().last_observation_s, 1.0)
        with self.assertRaises(ValueError):
            memory_config(timing_validated=False)

    def test_future_and_unconfirmed_events_rejected_without_mutation(self):
        memory = eastward_entry()
        events = [BoundaryEvent("entry", 1.3, 1, 0.4),
                  BoundaryEvent("entry", 1.1, 1, 0.4),
                  BoundaryEvent("entry", 1.1, 1, 0.05)]
        for event in events:
            with self.assertRaises(ValueError):
                memory.update(timestamp_s=1.2, position_xy=[1.2, 0], heading_rad=0, event=event)
        self.assertEqual(memory.snapshot().entry_count, 1)
        self.assertEqual(memory.snapshot().last_observation_s, 1.0)

    def test_stationary_plume_fluctuation_does_not_create_motion_memory(self):
        memory = CausalBoundaryMemory(memory_config())
        for index in range(5):
            memory.update(timestamp_s=index * 0.2, position_xy=[0, 0], heading_rad=0)
        with self.assertRaises(ValueError):
            memory.update(timestamp_s=1.0, position_xy=[0, 0], heading_rad=0,
                          event=BoundaryEvent("entry", 0.6, 0.6, 0.4))
        self.assertEqual(memory.snapshot().entry_count, 0)

    def test_no_wind_mode_and_wind_mode_have_different_requirements(self):
        CausalBoundaryMemory(memory_config()).update(timestamp_s=0, position_xy=[0, 0], heading_rad=0)
        cfg = memory_config(mode="wind_gated", exit_decay=0.9, exit_gain=0.3,
                            initial_upwind_gain=1.0, max_wind_age_s=0.1)
        memory = CausalBoundaryMemory(cfg)
        with self.assertRaises(ValueError):
            memory.update(timestamp_s=0, position_xy=[0, 0], heading_rad=0)
        for wind in (LocalWind([1, 0], 1.0), LocalWind([1, 0], -0.2), LocalWind([0, 0], 0)):
            with self.assertRaises(ValueError):
                memory.update(timestamp_s=0, position_xy=[0, 0], heading_rad=0, local_wind=wind)
        self.assertIsNone(memory.snapshot().last_observation_s)

    def test_air_velocity_sign_and_exit_upwind_gate(self):
        cfg = memory_config(mode="wind_gated", exit_decay=0.9, exit_gain=0.3,
                            initial_upwind_gain=1.0)
        memory = CausalBoundaryMemory(cfg)
        for index in range(6):
            time = index * 0.2
            wind = LocalWind([1, 0], time) if index in (0, 5) else None
            event = BoundaryEvent("exit", 0.6, 0.6, 0.4) if index == 5 else None
            result = memory.update(timestamp_s=time, position_xy=[time, 0], heading_rad=0,
                                   event=event, local_wind=wind)
        # Downwind east movement must not reinforce the west/upwind exit prior.
        np.testing.assert_allclose(memory.snapshot().exit_vector, [-1, 0])
        self.assertEqual(memory.snapshot().exit_count, 0)
        self.assertEqual(result.reason, "exit_rejected_by_upwind_gate")

    def test_latency_uncertainty_widens_tube_but_not_direction(self):
        memory = eastward_entry()
        kwargs = dict(timestamp_s=1.0, current_position_xy=[1, 0], length=3, base_radius=0.1,
                      position_covariance=np.zeros((2, 2)), drift_variance_rate=0)
        narrow = memory.make_return_tube(sensor_delay_uncertainty_s=0, **kwargs)
        wide = memory.make_return_tube(sensor_delay_uncertainty_s=0.2, **kwargs)
        self.assertGreater(wide.radius(0), narrow.radius(0))
        np.testing.assert_allclose(wide.direction_xy, narrow.direction_xy)

    def test_unobserved_or_stale_direction_cannot_make_tube(self):
        memory = eastward_entry()
        with self.assertRaises(ValueError):
            memory.make_return_tube(timestamp_s=7.0, current_position_xy=[0, 0], length=3,
                                    base_radius=0.1, position_covariance=np.eye(2),
                                    drift_variance_rate=0, sensor_delay_uncertainty_s=0)

    def test_current_tube_origin_cannot_teleport(self):
        memory = eastward_entry()
        with self.assertRaises(ValueError):
            memory.make_return_tube(timestamp_s=1.0, current_position_xy=[100, 0], length=3,
                                    base_radius=0.1, position_covariance=np.eye(2),
                                    drift_variance_rate=0, sensor_delay_uncertainty_s=0)

    def test_delayed_confirmation_does_not_reset_physical_memory_age(self):
        memory = CausalBoundaryMemory(memory_config())
        for index in range(8):
            time = index * 0.2
            event = BoundaryEvent("entry", 0.6, 0.6, 0.4) if index == 7 else None
            memory.update(timestamp_s=time, position_xy=[time, 0], heading_rad=0, event=event)
        self.assertAlmostEqual(memory.snapshot().last_entry_sample_s, 1.0)
        self.assertAlmostEqual(memory.snapshot().last_entry_confirmation_s, 1.4)
        memory.reset()
        self.assertEqual(memory.snapshot().entry_count, 0)
        self.assertIsNone(memory.snapshot().last_entry_sample_s)


class ResponseContrastTests(unittest.TestCase):
    def test_response_gradient_rotation_rotates_best_baseline(self):
        first = score([[0, 0]], [[[1, 0], [1, 2]]])
        second = score([[0, 0]], [[[0, 1], [-2, 1]]])
        first_best = first.actions[rank_by_maxmin(first)[0]]
        second_best = second.actions[rank_by_maxmin(second)[0]]
        self.assertAlmostEqual(first_best.orientation_rad, np.pi / 2)
        self.assertAlmostEqual(second_best.orientation_rad, 0.0)
        np.testing.assert_array_equal(first_best.center_xy, second_best.center_xy)

    def test_amplitude_only_cannot_separate_equal_means(self):
        result = score([[7, 7]], [[[1, 0], [1, 2]]])
        np.testing.assert_allclose(result.delta_even, 0)
        self.assertGreater(result.pair_contrast[:, 0].max(), 0)
        self.assertGreater(np.abs(result.delta_odd).max(), 0)

    def test_even_amplitude_is_preserved_when_gradients_match(self):
        result = score([[2, 1]], [[[1, 0], [1, 0]]])
        np.testing.assert_allclose(result.delta_odd, 0)
        self.assertTrue(np.all(result.pair_contrast > 0))

    def test_full_joint_covariance_is_used_once(self):
        covariance = np.broadcast_to([[1.0, 0.5], [0.5, 1.0]], (1, 2, 2, 2))
        result = score([[1, 0]], [[[0, 0], [-2, 0]]], joint_covariance=covariance,
                       orientations_rad=[0])
        # delta=(1,1), pooled covariance=[[2,1],[1,2]] -> distance=2/3.
        self.assertAlmostEqual(result.pair_contrast[0, 0], 2 / 3)
        self.assertFalse(result.calibrated_probabilities)

    def test_geometry_limits_and_linearization_radius(self):
        blocked = score([[0, 0]], [[[1, 0], [0, 1]]],
                        geometry=geometry(lower_xy=[-0.2, -0.2], upper_xy=[0.2, 0.2]))
        self.assertEqual(blocked.status, "no_legal_actions")
        self.assertEqual(blocked.rejected_geometry_count, 2)
        too_long = score([[0, 0]], [[[1, 0], [0, 1]]], geometry=geometry(linearization_radius=0.4))
        self.assertEqual(len(too_long.actions), 0)
        predicate = geometry(endpoint_legal=lambda xy: np.array([True, False]))
        self.assertEqual(len(score([[0, 0]], [[[1, 0], [0, 1]]], geometry=predicate).actions), 0)

    def test_no_information_inside_tube_releases_outside_retest(self):
        tube = ReturnTube([0, 0], [1, 0], 3, 0.1, np.zeros((2, 2)), np.zeros((2, 2)))
        result = score([[0, 0], [0, 0]], [[[1, 0], [1, 0]], [[1, 0], [1, 2]]],
                       center_xy=[[1, 0], [1, 3]], return_tube=tube)
        self.assertEqual(result.status, "out_of_tube_retest")
        self.assertTrue(len(result.eligible_indices) > 0)
        self.assertTrue(np.all(~result.in_tube[result.eligible_indices]))
        self.assertTrue(all(result.actions[i].center_index == 1 for i in result.eligible_indices))

    def test_uninformative_tube_requests_new_proposals_not_false_progress(self):
        tube = ReturnTube([0, 0], [1, 0], 3, 0.1, np.zeros((2, 2)), np.zeros((2, 2)))
        result = score([[0, 0]], [[[1, 0], [1, 0]]], center_xy=[[1, 0]], return_tube=tube)
        self.assertEqual(result.status, "need_outside_proposals")
        self.assertEqual(len(result.eligible_indices), 0)
        self.assertEqual(len(rank_by_maxmin(result)), 0)

    def test_all_source_pairs_available_without_cluster_allocation(self):
        result = score([[0, 0, 0]], [[[0, 0], [2, 0], [0, 2]]])
        np.testing.assert_array_equal(result.pair_indices, [[0, 1], [0, 2], [1, 2]])
        self.assertEqual(result.pair_contrast.shape, (2, 3))
        self.assertEqual(result.predicted_even_odd.shape, (2, 3, 2))

    def test_costs_and_covariance_need_valid_explicit_values(self):
        for costs in (0.0, [-1.0], [float("nan")]):
            with self.assertRaises(ValueError):
                score([[0, 0]], [[[1, 0], [0, 1]]], costs=costs)
        with self.assertRaises(ValueError):
            score([[0, 0]], [[[1, 0], [0, 1]]], joint_covariance=np.zeros((1, 2, 2, 2)))
        invalid = np.broadcast_to([[1, 2], [2, 1]], (1, 2, 2, 2))
        with self.assertRaises(ValueError):
            score([[0, 0]], [[[1, 0], [0, 1]]], joint_covariance=invalid)


if __name__ == "__main__":
    unittest.main()
