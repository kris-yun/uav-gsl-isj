#!/usr/bin/env python3
import unittest
import numpy as np

import screen


class CSLScreenTests(unittest.TestCase):
    def synthetic(self):
        rng = np.random.default_rng(7)
        n_source = 5
        dim = 8
        # Source prototypes plus a high-variance within-source nuisance axis.
        proto = np.zeros((n_source, dim))
        for s in range(n_source):
            proto[s, s % 4] = 0.35 + 0.08 * s
            proto[s, 4 + (s % 4)] = 0.20
        nuisance = np.array([0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.8, -0.8])
        train = np.empty((screen.TRAIN_WORLDS, n_source, dim))
        for w in range(screen.TRAIN_WORLDS):
            z = rng.normal(scale=0.30)
            train[w] = proto + z * nuisance + rng.normal(
                scale=0.01, size=(n_source, dim))
        held = np.empty((screen.HELDOUT_WORLDS, n_source, dim))
        for w in range(screen.HELDOUT_WORLDS):
            z = rng.normal(scale=0.35)
            held[w] = proto + z * nuisance + rng.normal(
                scale=0.01, size=(n_source, dim))
        weight = np.array([1, 2, 1, 3, 2], dtype=float)
        weight /= weight.sum()
        xy = np.stack([np.arange(n_source), np.zeros(n_source)], axis=1)
        return train, held, weight, xy

    def test_fit_uses_training_shape_only(self):
        train, held, weight, xy = self.synthetic()
        model = screen.fit_within_source_whitening(train, weight)
        self.assertEqual(model["prototype"].shape, (train.shape[1], train.shape[2]))
        self.assertEqual(model["whitener"].shape, (train.shape[2], train.shape[2]))
        self.assertGreater(model["eigen_floor"], 0.0)
        metric = screen.evaluate(model, held, weight, xy)
        self.assertEqual(
            metric["sample_count"],
            screen.HELDOUT_WORLDS * train.shape[1])
        self.assertTrue(0.0 <= metric["unique_top1_weighted"] <= 1.0)
        self.assertTrue(0.0 <= metric["top5_weighted"] <= 1.0)
        self.assertTrue(np.isfinite(metric["mean_xy_error_m_weighted"]))

    def test_measure_weight_is_normalized_in_evaluation(self):
        train, held, weight, xy = self.synthetic()
        model = screen.fit_raw(train, weight)
        metric = screen.evaluate(model, held, weight, xy)
        # top-5 is guaranteed with exactly five source classes; verifies the
        # source-measure/world weights sum to one rather than leaf count.
        self.assertAlmostEqual(metric["top5_weighted"], 1.0, places=12)

    def test_shuffle_control_refits_destroyed_groups(self):
        train, held, weight, xy = self.synthetic()
        out = screen.shuffled_positive_control(
            train, held, weight, xy, runs=4, seed=20260922)
        self.assertEqual(out["runs"], 4)
        self.assertEqual(out["seed"], 20260922)
        for key in ("unique_top1_weighted", "top5_weighted",
                    "mean_xy_error_m_weighted"):
            self.assertIn("mean", out[key])
            self.assertTrue(np.isfinite(out[key]["mean"]))


if __name__ == "__main__":
    unittest.main()
