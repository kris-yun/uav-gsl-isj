import importlib.util
from pathlib import Path
import math
import unittest

spec = importlib.util.spec_from_file_location("wind", Path(__file__).resolve().parents[1] / "closed_loop/ctpi/ctpi_v2_wind_observation.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
encode = module.gmrf_request_values


class TestWind(unittest.TestCase):
    def test_direction_and_position(self):
        for uv in [(1, 0), (0, 1), (-1, 0), (0, -1), (3, -4), (0, 0)]:
            report = encode(200_000_000, (2, -3), uv)
            r = report["request"]
            self.assertEqual((r["x_pos"][0], r["y_pos"][0]), (2, -3))
            recovered = (r["wind_speed"][0] * math.cos(r["wind_direction"][0]),
                         r["wind_speed"][0] * math.sin(r["wind_direction"][0]))
            for a, b in zip(recovered, uv):
                self.assertAlmostEqual(a, b, places=12)
            self.assertEqual(report["delivery_status"], "NOT_SUBMITTED")

    def test_zero_placeholder_rejected(self):
        with self.assertRaises(ValueError):
            encode(0, (0, 0), (0, 0))

    def test_bad_input_rejected(self):
        for args in [(100_000_000, (0, 0), (1, 0)),
                     (200_000_000, (0,), (1, 0)),
                     (200_000_000, (math.nan, 0), (1, 0)),
                     (200_000_000, (0, 0), (math.inf, 0))]:
            with self.assertRaises(ValueError):
                encode(*args)


if __name__ == "__main__":
    unittest.main()
