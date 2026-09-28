"""Checks that the two frozen policies differ only after valid local evidence."""

import unittest

from local_action_policy import LocalActionPolicy, StopEvent


A = (0.0, 0.0)
B = (0.9, 0.0)
C = (-0.9, 0.0)
NATIVE = (3.0, 0.0)
FREE = [A, B, C, (0.0, 0.9), (0.0, -0.9)]


def path_length(goal):
    return 0.9 if goal in FREE else None


def event(cycle, time_s, xy, hit, value=None, samples=10):
    return StopEvent(cycle, time_s, xy, 0.2 if hit else 0.0 if value is None else value,
                     hit, samples)


class LocalPolicyTests(unittest.TestCase):
    def test_hit_miss_rehit_control_and_verified_split(self):
        for arm in ("last_hit", "verified_local"):
            p = LocalActionPolicy(arm)
            self.assertEqual(p.decide(NATIVE, 5, event(1, 5, A, False), FREE, path_length).goal_xy, NATIVE)
            self.assertEqual(p.decide(NATIVE, 10, event(2, 10, A, True), FREE, path_length).goal_xy, B)
            self.assertEqual(p.decide(NATIVE, 15, event(3, 15, B, False), FREE, path_length).goal_xy, A)
            result = p.decide(NATIVE, 20, event(4, 20, A, True), FREE, path_length)
            self.assertEqual(result.goal_xy, C if arm == "verified_local" else NATIVE)
            self.assertEqual(result.validated_boundary, arm == "verified_local")
            self.assertAlmostEqual(result.d_ab_ppm, -0.2)
            if arm == "verified_local":
                self.assertEqual(p.decide(NATIVE, 25, event(5, 25, C, False), FREE, path_length).goal_xy, NATIVE)
            self.assertTrue(p.trigger_consumed)
            self.assertEqual(p.decide(NATIVE, 30, event(6, 30, A, True), FREE, path_length).goal_xy, NATIVE)

    def test_revisit_miss_revokes_and_never_retriggers(self):
        p = LocalActionPolicy("verified_local")
        p.decide(NATIVE, 10, event(1, 10, A, True), FREE, path_length)
        p.decide(NATIVE, 15, event(2, 15, B, False), FREE, path_length)
        d = p.decide(NATIVE, 20, event(3, 20, A, False), FREE, path_length)
        self.assertEqual(d.goal_xy, NATIVE)
        self.assertIn("revisit_miss", p.revocations)
        self.assertEqual(p.decide(NATIVE, 25, event(4, 25, A, True), FREE, path_length).goal_xy, NATIVE)

    def test_last_hit_new_hit_does_not_return_to_old_anchor(self):
        control = LocalActionPolicy("last_hit")
        verified = LocalActionPolicy("verified_local")
        for p in (control, verified):
            p.decide(NATIVE, 10, event(1, 10, A, True), FREE, path_length)
        self.assertEqual(control.decide(NATIVE, 15, event(2, 15, B, True), FREE, path_length).goal_xy, NATIVE)
        self.assertEqual(verified.decide(NATIVE, 15, event(2, 15, B, True), FREE, path_length).goal_xy, A)
        self.assertEqual(verified.decide(NATIVE, 20, event(3, 20, A, True), FREE, path_length).goal_xy, NATIVE)

    def test_frozen_time_and_normal_ten_sample_guards(self):
        p = LocalActionPolicy("verified_local")
        self.assertEqual(p.decide(NATIVE, 181, event(1, 181, A, True), FREE, path_length).goal_xy, NATIVE)
        self.assertFalse(p.trigger_consumed)
        self.assertEqual(p.decide(NATIVE, 190, event(2, 190, A, True, samples=9), FREE, path_length).goal_xy, NATIVE)
        self.assertFalse(p.trigger_consumed)
        self.assertEqual(p.decide(NATIVE, 190, event(3, 190, A, True), FREE, path_length).goal_xy, NATIVE)

    def test_unreachable_departure_keeps_native_goal(self):
        p = LocalActionPolicy("verified_local")
        d = p.decide(NATIVE, 10, event(1, 10, A, True), [A], path_length)
        self.assertEqual(d.goal_xy, NATIVE)
        self.assertIn("no_reachable_local_departure", p.revocations)
        self.assertTrue(p.trigger_consumed)

    def test_duplicate_callback_is_idempotent(self):
        p = LocalActionPolicy("verified_local")
        first = p.decide(NATIVE, 10, event(1, 10, A, True), FREE, path_length)
        second = p.decide(NATIVE, 10.2, event(1, 10, A, True), FREE, path_length)
        self.assertEqual(first, second)
        self.assertEqual(p.phase, "to_b")

    def test_anchor_expiry_revokes(self):
        p = LocalActionPolicy("verified_local")
        p.decide(NATIVE, 10, event(1, 10, A, True), FREE, path_length)
        d = p.decide(NATIVE, 90, event(2, 90, B, False), FREE, path_length)
        self.assertEqual(d.goal_xy, NATIVE)
        self.assertIn("anchor_memory_expired", p.revocations)

    def test_mirror_requires_reachable_opposite_cell(self):
        p = LocalActionPolicy("verified_local")
        only_ab = [A, B]
        p.decide(NATIVE, 10, event(1, 10, A, True), only_ab, path_length)
        p.decide(NATIVE, 15, event(2, 15, B, False), only_ab, path_length)
        d = p.decide(NATIVE, 20, event(3, 20, A, True), only_ab, path_length)
        self.assertEqual(d.goal_xy, NATIVE)
        self.assertIn("mirror_goal_unreachable", p.revocations)


if __name__ == "__main__":
    unittest.main()
