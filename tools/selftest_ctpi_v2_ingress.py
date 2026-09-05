"""CPU-only message ordering tests. No source, House or simulation inputs."""
import importlib.util
import itertools
from pathlib import Path
import sys
import unittest

source = Path(__file__).resolve().parents[1] / "closed_loop/ctpi/ctpi_v2_ingress.py"
spec = importlib.util.spec_from_file_location("ctpi_v2_ingress", source)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Ingress = module.StampedIngress
DT = 200_000_000


def values(kind, index):
    return {"pose": (index, -index), "gas": (float(index),), "wind": (.1 * index, .2)}[kind]


def frame(stream, index):
    rows = []
    for kind in ("pose", "gas", "wind"):
        rows += stream.push(kind, index * DT, values(kind, index))
    return rows


class TestIngress(unittest.TestCase):
    def test_all_callback_permutations(self):
        for order in itertools.permutations(("pose", "gas", "wind")):
            stream = Ingress()
            rows = []
            for i in range(1201):
                for kind in order:
                    rows += stream.push(kind, i * DT, values(kind, i))
            stream.finish(240_000_000_000)
            self.assertEqual(len(rows), 1201)
            self.assertEqual(rows[-1].pose_xy, (1200., -1200.))
            self.assertEqual(rows[-1].gas_ppm, 1200.)

    def test_cross_topic_skew_no_latest_pose_mix(self):
        stream = Ingress()
        frame(stream, 0)
        stream.push("pose", DT, (1, 1))
        stream.push("pose", 2 * DT, (2, 2))
        stream.push("wind", DT, (.1, 0))
        row = stream.push("gas", DT, (3,))[0]
        self.assertEqual(row.pose_xy, (1, 1))
        self.assertEqual(row.wind_uv, (.1, 0))
        with self.assertRaisesRegex(ValueError, "INCOMPLETE"):
            stream.finish(DT)

    def test_bootstrap_repetition(self):
        stream = Ingress()
        self.assertFalse(stream.ready)
        frame(stream, 0)
        for kind in stream.kinds:
            self.assertEqual(stream.push(kind, 0, values(kind, 0)), [])
        self.assertTrue(stream.ready)
        stream.finish(0)

    def test_missing_first_sample_fail_closed(self):
        stream = Ingress()
        with self.assertRaisesRegex(ValueError, "GAP"):
            stream.push("gas", DT, (0,))
        with self.assertRaisesRegex(ValueError, "ALREADY_FAILED"):
            stream.push("gas", 0, (0,))

    def test_duplicate_gap_wrong_initial_invalid_values(self):
        cases = [("gas", 0, (1,)), ("pose", 1, (0, 0)),
                 ("gas", 0, (float("nan"),)), ("wind", 0, (0,)),
                 ("gas", 0, (-1,)), ("pose", False, (0, 0))]
        for args in cases:
            with self.assertRaises(ValueError):
                Ingress().push(*args)
        for stamp in (DT, 3 * DT):
            stream = Ingress()
            frame(stream, 0)
            frame(stream, 1)
            with self.assertRaisesRegex(ValueError, "GAP_OR_DUPLICATE|CONFLICTING"):
                stream.push("gas", stamp, (2,))

    def test_positive_clock_pause_does_not_add_evidence(self):
        stream = Ingress()
        frame(stream, 0)
        frame(stream, 1)
        for _ in range(15):
            for kind in stream.kinds:
                self.assertEqual(stream.push(kind, DT, values(kind, 1)), [])
        self.assertEqual(stream.identical_repeats, 45)
        self.assertEqual(len(frame(stream, 2)), 1)
        stream.finish(2 * DT)
        with self.assertRaisesRegex(ValueError, "GAP"):
            stream.push("gas", DT, (1,))

    def test_changed_zero_and_unreceived_tail(self):
        stream = Ingress()
        frame(stream, 0)
        with self.assertRaisesRegex(ValueError, "CONFLICTING"):
            stream.push("pose", 0, (1, 0))
        stream = Ingress()
        frame(stream, 0)
        with self.assertRaisesRegex(ValueError, "INCOMPLETE"):
            stream.finish(DT)

    def test_pending_limit_is_not_silent_eviction(self):
        stream = Ingress(max_pending=1)
        stream.push("pose", 0, (0, 0))
        with self.assertRaisesRegex(ValueError, "PENDING_LIMIT"):
            stream.push("pose", DT, (1, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
