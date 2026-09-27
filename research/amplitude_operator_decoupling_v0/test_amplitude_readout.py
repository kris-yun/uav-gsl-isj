import tempfile, unittest
from pathlib import Path
import numpy as np
from amplitude_readout import (Arm, DEFAULT_ARM, ObservationOperator, AmplitudeTemplates,
                               rectangular_weights, load_saved_mean_maps, ranking)


class Regression(unittest.TestCase):
    def setUp(self):
        self.meta = dict(width=2, height=2, resolution=1., origin_x=0., origin_y=0.)
        self.w = rectangular_weights(self.meta, [[1., 1.]], [[2., 2.]])

    def test_explicit_kind_and_default(self):
        self.assertEqual(DEFAULT_ARM, Arm.RAWU_FOOTPRINT)
        self.assertEqual(Arm('u_nearest').map_kind, 'u')
        with self.assertRaises(ValueError): Arm('p_footprint')
        with self.assertRaises(ValueError): load_saved_mean_maps(Path('.'), 0, 'p', 4)

    def test_raw_no_blur_and_occurrence_isolation(self):
        p = np.array([.1, .2, .3, .4], np.float32)
        before = p.tobytes()
        maps = dict(rawu=np.array([[0., 0., 0., 4.]]), u=np.ones((1, 4)))
        ops = dict(nearest=ObservationOperator('nearest', [[0., 0., 0., 1.]]),
                   footprint=ObservationOperator('footprint', self.w))
        for arm in Arm:
            bank = AmplitudeTemplates.prepare(maps, ops, arm)
            self.assertEqual(p.tobytes(), before)
            self.assertFalse(bank.values.flags.writeable)
            self.assertFalse(bank.fields.flags.writeable)
        self.assertEqual(AmplitudeTemplates.prepare(maps, ops, Arm.RAWU_NEAREST).fields[0, 0], 4.)
        self.assertEqual(AmplitudeTemplates.prepare(maps, ops, Arm.RAWU_FOOTPRINT).fields[0, 0], 1.)

    def test_operator_is_copy_readonly(self):
        op = ObservationOperator('footprint', self.w)
        self.w[:] = 0
        np.testing.assert_array_equal(op.weights, [[.25]*4])
        with self.assertRaises(ValueError): op.weights[0, 0] = 0

    def test_deterministic_projection(self):
        other = rectangular_weights(self.meta, [[1., 1.]], [[2., 2.]])
        self.assertEqual(other.tobytes(), self.w.tobytes())
        np.testing.assert_array_equal(self.w, [[.25]*4])

    def test_outside_not_renormalized_and_rejected(self):
        w = rectangular_weights(self.meta, [[0., 1.]], [[2., 2.]])
        self.assertEqual(w.sum(), .5)
        with self.assertRaisesRegex(ValueError, 'outside'): ObservationOperator('footprint', w)

    def test_no_wall_rescaling(self):
        # A wall-valued zero cell stays in the area denominator.
        op = ObservationOperator('footprint', self.w)
        np.testing.assert_array_equal(op.project([[0., 4., 4., 4.]]), [[3.]])

    def test_bad_geometry_and_fields(self):
        with self.assertRaises(ValueError): rectangular_weights(self.meta, [[np.nan, 1.]], [[1., 1.]])
        with self.assertRaises(ValueError): rectangular_weights(self.meta, [[1., 1.]], [[-1., 1.]])
        with self.assertRaises(ValueError): ObservationOperator('footprint', [[np.nan]*4])
        with self.assertRaises(ValueError): ObservationOperator('footprint', self.w).project([[-1., 0., 0., 0.]])

    def test_exact_archived_b2_and_ties(self):
        f = np.tile(np.array([[1., 2.], [2., 1.], [1., 2.]])[:, None, :], (1, 10, 1))
        bank = AmplitudeTemplates(Arm.U_NEAREST, f[:, 0, :], f)
        y = np.tile(np.array([2., 4.], np.float32), (10, 1))
        norm = (f*f).sum(axis=(1, 2))
        gain = np.maximum(0, (f*y[None]).sum(axis=(1, 2))/norm)
        expected = ((y[None]-gain[:, None, None]*f)**2).sum(axis=(1, 2))
        actual, g = bank.score(y)
        self.assertEqual(expected.tobytes(), actual.tobytes())
        self.assertEqual(gain.tobytes(), g.tobytes())
        self.assertEqual(ranking(actual, 0), (1, False))

    def test_incomplete_saved_bank_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                load_saved_mean_maps(Path(tmp), 0, 'rawu', 4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
