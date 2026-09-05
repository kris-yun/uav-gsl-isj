import importlib.util
from fractions import Fraction
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("release", Path(__file__).resolve().parents[1] / "closed_loop/ctpi/ctpi_v2_release_schedule.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class TestRelease(unittest.TestCase):
    def test_fractional_carry_is_not_reset_by_actual_release(self):
        carry = 0
        caps = []
        for _ in range(10):
            cap, carry = release.nominal_step(carry, 7, .1)
            caps.append(cap)
            self.assertEqual(release.release_count(cap, 0), 0)
        self.assertEqual(caps, [0, 1, 1, 0, 1, 1, 0, 1, 1, 1])
        self.assertAlmostEqual(carry, 0)
        self.assertEqual(sum(caps), 7)

    def test_declared_uniform_residue_law_not_uniform_count_law(self):
        p = [Fraction(1, 100)] * 100
        self.assertEqual(release.conditional_count_law(0, p), {0: 1})
        self.assertEqual(release.conditional_count_law(1, p), {0: Fraction(1, 2), 1: Fraction(1, 2)})
        self.assertEqual(release.conditional_count_law(2, p), {0: Fraction(1, 4), 1: Fraction(1, 2), 2: Fraction(1, 4)})

    def test_half_tie_and_explicit_nonuniform_law(self):
        self.assertEqual(release.release_count(1, 50), 1)
        p = [0] * 100
        p[99] = 1
        self.assertEqual(release.conditional_count_law(3, p), {3: 1})

    def test_phase_and_units_are_explicit(self):
        self.assertEqual(release.nominal_step(.4, 7, .1)[0], 1)
        self.assertEqual(release.nominal_step(0, 7, .1)[0], 0)
        self.assertEqual(release.nominal_step(0, 7, .5)[0], 3)
        # A .5 s saved frame must be composed of generator .1 s steps;
        # one large release draw has a different distribution.

    def test_invalid_inputs_fail(self):
        for args in [(1, 7, .1), (-.1, 7, .1), (0, -1, .1), (0, 7, 0), (0, float('nan'), .1), (0, 1e300, 1e300)]:
            with self.assertRaises(ValueError):
                release.nominal_step(*args)
        for args in [(1, 100), (1, -1), (True, 0), (-1, 0)]:
            with self.assertRaises(ValueError):
                release.release_count(*args)
        for law in [[], [0] * 100, [1] * 100]:
            with self.assertRaises(ValueError):
                release.conditional_count_law(1, law)


if __name__ == '__main__':
    unittest.main()
