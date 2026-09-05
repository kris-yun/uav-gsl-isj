import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("preflight", Path(__file__).resolve().parents[1] / "closed_loop/ctpi/ctpi_v2_replay_preflight.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
audit_replay = module.audit_replay


class TestReplay(unittest.TestCase):
    def test_spent_seed12_wrap(self):
        r = audit_replay(1999, 12, .2, 240)
        self.assertEqual(r["first_observed_iteration"], 1050)
        self.assertEqual(r["wraps"], [dict(step=949, time_s=189.8, previous_iteration=1997, iteration=0)])
        self.assertFalse(r["continuous_transport_qualified"])

    def test_no_wrap_not_physics_pass(self):
        r = audit_replay(1999, 12, .2, 1)
        self.assertEqual(r["status"], "NO_INDEX_WRAP_ONLY")
        self.assertFalse(r["continuous_transport_qualified"])

    def test_boundary_included(self):
        self.assertEqual(len(audit_replay(1999, 12, .2, 189.8)["wraps"]), 1)
        self.assertEqual(len(audit_replay(1999, 12, .2, 189.6)["wraps"]), 0)

    def test_invalid_inputs(self):
        for args in [(1, 12, .2, 240), (1999, 12, 0, 240), (1999, 12, .2, .3), (1999, 12, .2, float("nan"))]:
            with self.assertRaises(ValueError):
                audit_replay(*args)


if __name__ == "__main__":
    unittest.main()
