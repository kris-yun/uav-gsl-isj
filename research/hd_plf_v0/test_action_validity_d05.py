"""Small contract checks for the read-only D0.5 evaluator."""

import unittest

import numpy as np

from run_action_validity_d05_vm import archived_strict_rank, b2_sse, margin, spearman, square_reading, tie_rank


class D05EvaluatorTests(unittest.TestCase):
    def test_b2_profiles_only_nonnegative_gain(self):
        templates = np.array([[1., 2.], [2., 1.]])
        np.testing.assert_allclose(b2_sse(templates, np.array([2., 4.])), [0., 7.2])
        np.testing.assert_allclose(b2_sse(templates, np.array([-1., -2.])), [5., 5.])

    def test_archived_rank_and_tie_aware_rank_are_separate(self):
        sse = np.array([0., 0., 2.])
        self.assertEqual(archived_strict_rank(sse, 1), 1)
        self.assertEqual(tie_rank(sse, 1, np.array([1.])), 1.5)
        self.assertEqual(margin(sse, 2), -2.)

    def test_square_sampling_matches_two_by_two_native_pool(self):
        cube = np.arange(16., dtype=np.float32).reshape(1, 4, 4)
        metadata = {"coarse_cell": .1, "min_x": 0., "min_y": 0.}
        self.assertAlmostEqual(square_reading(cube, metadata, (.2, .2), 0),
                               float(cube[0, 1:3, 1:3].mean()))

    def test_spearman_reports_undefined_instead_of_zero(self):
        self.assertIsNone(spearman(np.array([1., 1., 1.]), np.array([2., 3., 4.])))
        self.assertAlmostEqual(spearman(np.array([1., 2., 3.]), np.array([3., 2., 1.])), -1.)


if __name__ == "__main__":
    unittest.main()
