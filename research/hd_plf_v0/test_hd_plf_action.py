import unittest

import numpy as np

from hd_plf_action import GoalCandidate, HDPLFActionSelector
from hd_plf_controller import HDPLFLocalController, StopEvent


NATIVE = (4.0, 4.0)
ANCHOR = (0.0, 0.0)
G1 = GoalCandidate(1, 0.9, 0.0, 1.0)
G2 = GoalCandidate(2, -0.9, 0.0, 1.0)
Q = np.array([0.5, 0.5])


class HDPLFActionTests(unittest.TestCase):
    def select(self, maps, arm="LF-rawu", goals=(G1, G2), q=Q):
        return HDPLFActionSelector(arm, np.array(maps, dtype=float)).choose(
            NATIVE, ANCHOR, [0], q, goals)

    def test_proportional_views_do_not_create_separation(self):
        d = self.select([[1, 2, 3], [2, 4, 6]])
        self.assertEqual(d.history_separation, 0.0)
        for value in d.ranked_goals:
            self.assertAlmostEqual(value.pair_separation, 0.0, places=14)
            self.assertAlmostEqual(value.separation_gain, 0.0, places=14)

    def test_new_position_breaks_gain_proportionality(self):
        d = self.select([[1, 2, 1], [2, 1, 2]])
        self.assertEqual(d.selected.goal.cell_index, 1)
        self.assertGreater(d.selected.separation_gain, 0.0)
        self.assertAlmostEqual(d.ranked_goals[1].pair_separation, 0.0, places=14)

    def test_common_positive_scale_does_not_change_ranking(self):
        maps = np.array([[1, 2, 1], [2, 1, 2]], dtype=float)
        a = self.select(maps)
        b = self.select(maps * 17.25)
        self.assertEqual([x.goal.cell_index for x in a.ranked_goals],
                         [x.goal.cell_index for x in b.ranked_goals])
        np.testing.assert_allclose([x.pair_separation for x in a.ranked_goals],
                                   [x.pair_separation for x in b.ranked_goals], atol=1e-14)

    def test_u_and_rawu_share_rules_but_maps_change_waypoint(self):
        rawu_maps = [[1, 2, 1], [2, 1, 2]]
        u_maps = [[1, 1, 2], [2, 2, 1]]
        raw = self.select(rawu_maps, "LF-rawu")
        blurred = self.select(u_maps, "LF-u")
        self.assertEqual(raw.selected.goal.cell_index, 1)
        self.assertEqual(blurred.selected.goal.cell_index, 2)
        self.assertEqual(raw.selected.goal.path_length_m, blurred.selected.goal.path_length_m)
        self.assertEqual(raw.selected.travel_penalty, blurred.selected.travel_penalty)

    def test_rawu_is_used_in_actual_goal_selection(self):
        maps = [[1, 2, 1], [2, 1, 2]]
        d = self.select(maps, "LF-rawu")
        self.assertEqual(d.goal_xy, (G1.x_m, G1.y_m))
        changed = self.select([[1, 1, 2], [2, 2, 1]], "LF-rawu")
        self.assertEqual(changed.goal_xy, (G2.x_m, G2.y_m))

    def test_native_probability_is_input_only(self):
        q = np.array([0.7, 0.3])
        original = q.copy()
        self.select([[1, 2, 1], [2, 1, 2]], q=q)
        np.testing.assert_array_equal(q, original)

    def test_invalid_support_or_memory_falls_back_to_native(self):
        selector = HDPLFActionSelector("LF-rawu", np.ones((2, 3)))
        bad_q = selector.choose(NATIVE, ANCHOR, [0], [1.0], [G1])
        bad_memory = selector.choose(NATIVE, ANCHOR, [0, 0], Q, [G1])
        self.assertEqual(bad_q.goal_xy, NATIVE)
        self.assertEqual(bad_memory.goal_xy, NATIVE)

    def test_zero_vector_is_conservative(self):
        d = self.select([[0, 0, 0], [1, 2, 1]])
        self.assertAlmostEqual(d.selected.pair_separation, 0.0, places=14)

    def test_fast_pair_formula_matches_explicit_sum(self):
        rng = np.random.default_rng(20260928)
        views = rng.uniform(0.0, 3.0, size=(7, 4))
        views[0] = 0.0
        q = rng.dirichlet(np.ones(7))
        direct = 0.0
        for a in range(7):
            for b in range(a + 1, 7):
                if np.linalg.norm(views[a]) == 0 or np.linalg.norm(views[b]) == 0:
                    continue
                cos = np.dot(views[a], views[b]) / (np.linalg.norm(views[a]) * np.linalg.norm(views[b]))
                direct += q[a] * q[b] * (1 - cos * cos)
        fast = HDPLFActionSelector._pair_separation(views, q)
        self.assertAlmostEqual(fast, direct, places=14)

    def test_controller_routes_rawu_action_into_departure_goal(self):
        rawu_maps = np.array([[1, 2, 1], [2, 1, 2]], dtype=float)
        u_maps = np.array([[1, 1, 2], [2, 2, 1]], dtype=float)
        arms = [HDPLFLocalController("LF-u", u_maps),
                HDPLFLocalController("LF-rawu", rawu_maps)]
        event = StopEvent(1, 10.0, ANCHOR, .2, True, 10)
        free = [ANCHOR, (G1.x_m, G1.y_m), (G2.x_m, G2.y_m)]
        def path_length(goal):
            return 1.0 if goal in free else None
        outcomes = [arm.decide(NATIVE, 10.0, event, free, path_length,
                               native_source_probability=Q,
                               actual_history_cells=[0], reachable_goals=[G1, G2])
                    for arm in arms]
        self.assertEqual(outcomes[0].goal_xy, (G2.x_m, G2.y_m))
        self.assertEqual(outcomes[1].goal_xy, (G1.x_m, G1.y_m))
        self.assertTrue(all(x.phase == "to_b" for x in outcomes))
        self.assertEqual(arms[1].last_action_decision.selected.goal.cell_index, G1.cell_index)
        self.assertEqual(arms[0].last_action_decision.selected.goal.cell_index, G2.cell_index)

    def test_controller_invalid_native_axis_falls_back(self):
        arm = HDPLFLocalController("LF-rawu", [[1, 2, 1], [2, 1, 2]])
        event = StopEvent(1, 10.0, ANCHOR, .2, True, 10)
        decision = arm.decide(NATIVE, 10.0, event, [ANCHOR, (G1.x_m, G1.y_m)],
                              lambda _: 1.0, native_source_probability=[1.0],
                              actual_history_cells=[0], reachable_goals=[G1])
        self.assertEqual(decision.goal_xy, NATIVE)
        self.assertIn("no_reachable_local_departure", arm.revocations)


if __name__ == "__main__":
    unittest.main()
