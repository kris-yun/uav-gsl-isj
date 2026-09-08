"""Algebra and causal-boundary regressions; not House performance evidence."""
from pathlib import Path
import math
import sys
import unittest
from types import SimpleNamespace as NS

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.ctpi_cstar.m1_picr.sequential_joint import SequentialJointEvidence
from experiments.ctpi_cstar.m2_cpo.physical_prior import PhysicalCPOProvider, PhysicalPriorConfig
from closed_loop.ctpi.cstar_joint_source_online import JointSourceSession


class Tests(unittest.TestCase):
    def test_joint_matches_batch_and_does_not_reset_nuisance(self):
        state = SequentialJointEvidence([1, 1], [1, 1])
        means = [np.array([[0., 4.], [2., 2.]]), np.array([[4., 0.], [2., 2.]])]
        joint_score = np.zeros((2, 2))
        resetting_score = np.zeros(2)
        for i, mu in enumerate(means, 1):
            state.predict(i * 200_000_000, mu, np.ones((2, 2)))
            state.observe(i * 200_000_000, 0.)
            ll = -.5 * (math.log(2 * math.pi) + mu ** 2)
            joint_score += ll
            resetting_score += np.log(np.exp(ll).mean(axis=1))
        expected = np.exp(joint_score - joint_score.max()).sum(axis=1)
        expected /= expected.sum()
        np.testing.assert_allclose(state.source_posterior, expected)
        self.assertGreater(state.source_posterior[1], .98)
        self.assertGreater(resetting_score[0], resetting_score[1])

    def test_duplicates_and_bad_prediction_are_rejected(self):
        s = SequentialJointEvidence([1, 1], [1])
        with self.assertRaises(ValueError): s.observe(200_000_000, 0.)
        with self.assertRaises(ValueError): s.predict(200_000_000, [[0], [1]], [[0], [1]])
        s.predict(200_000_000, [[0], [1]], [[1], [1]])
        with self.assertRaises(ValueError): s.observe(200_000_000, float('nan'))
        np.testing.assert_allclose(s.source_posterior, [.5, .5])
        s.observe(200_000_000, 0.)
        with self.assertRaises(ValueError): s.observe(200_000_000, 0.)
        with self.assertRaises(ValueError): s.predict(600_000_000, [[0], [1]], [[1], [1]])
        self.assertEqual(s.observation_count, 1)

    def test_missing_is_neutral_but_zero_is_evidence(self):
        s = SequentialJointEvidence([1, 1], [1])
        s.predict(200_000_000, [[0], [3]], [[1], [1]])
        s.observe(200_000_000, valid=False)
        np.testing.assert_allclose(s.source_posterior, [.5, .5])
        s.predict(400_000_000, [[0], [3]], [[1], [1]])
        s.observe(400_000_000, 0.)
        self.assertGreater(s.source_posterior[0], .98)

    def test_prediction_arrays_are_copied(self):
        s = SequentialJointEvidence([1, 1], [1])
        mu = np.array([[0.], [3.]])
        s.predict(200_000_000, mu, np.ones((2, 1)))
        mu[:] = 0
        self.assertGreater(s.observe(200_000_000, 0.)[0], .98)

    def test_real_provider_next_wind_not_used_and_geometry_guard(self):
        cfg = PhysicalPriorConfig(nx=4, ny=3, dx=1., diffusion=.05,
              free=(True,) * 12, transport_backend='numpy')
        bootstrap = NS(stamp_ns=0, gas_ppm=0., pose_xy=(1.5, 1.5), wind_uv=(1., 0.))
        sessions = [JointSourceSession(PhysicalCPOProvider(cfg), [(0.5, 1.5), (2.5, 1.5)], bootstrap)
                    for _ in range(2)]
        for s in sessions: s.predict_next((1.5, 1.5))
        posterior = []
        for s, wind in zip(sessions, [(1., 0.), (-10., 0.)]):
            posterior.append(s.observe(NS(stamp_ns=200_000_000, gas_ppm=.1,
                                   pose_xy=(1.5, 1.5), wind_uv=wind)))
        np.testing.assert_array_equal(*posterior)
        for s in sessions: s.predict_next((1.5, 1.5))
        with self.assertRaises(ValueError):
            sessions[0].observe(NS(stamp_ns=400_000_000, gas_ppm=.1,
                                   pose_xy=(2.5, 1.5), wind_uv=(1., 0.)))
        self.assertEqual(len(sessions[0].prefix), 2)

    def test_ar_state_survives_boundaries(self):
        s = SequentialJointEvidence([1], [1], rho=.5)
        for i in range(1, 3):
            s.predict(i * 200_000_000, [[0]], [[1]])
            s.observe(i * 200_000_000, math.e - 1)
        self.assertAlmostEqual(s.log_evidence, -math.log(2 * math.pi) - .5 * (1 + .25))

    def test_input_frame_is_snapshotted(self):
        cfg = PhysicalPriorConfig(nx=3, ny=2, dx=1., diffusion=.05, free=(True,) * 6)
        bootstrap = NS(stamp_ns=0, gas_ppm=0., pose_xy=[1.5, .5], wind_uv=[1., 0.])
        session = JointSourceSession(PhysicalCPOProvider(cfg), [(0.5, .5)], bootstrap)
        bootstrap.wind_uv[0] = -100.
        self.assertEqual(session.prefix[0].wind_uv, (1., 0.))
        session.predict_next((1.5, .5))
        frame = NS(stamp_ns=200_000_000, gas_ppm=.1, pose_xy=[1.5, .5], wind_uv=[1., 0.])
        session.observe(frame)
        frame.gas_ppm = 100.
        self.assertEqual(session.prefix[-1].gas_ppm, .1)


if __name__ == '__main__':
    unittest.main()
