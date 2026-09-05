import unittest
from ctpi_r4_stationary_wind_audit import summarize, replay_resets


def fixture(xs, us, moving=None, steps=None):
    winds, poses = [], []
    for i, (x, u) in enumerate(zip(xs, us)):
        step = steps[i] if steps else i + 1
        common = dict(step=str(step), t_sim_s=str(step / 5), x=str(x), y="0", z="0")
        winds.append(dict(common, wind_u=str(u), wind_v="0", wind_w="0"))
        poses.append(dict(common, is_moving=str(moving[i] if moving else 0)))
    return winds, poses


class TestAudit(unittest.TestCase):
    def test_static(self):
        result = summarize(*fixture([0]*3, [1]*3))
        self.assertEqual(result["stationary_changed_pairs_at_csv_precision"], 0)
        self.assertEqual(result["stationary_adjacent_pairs"], 2)

    def test_temporal_change(self):
        result = summarize(*fixture([0]*3, [1, 2, 1]))
        self.assertEqual(result["stationary_changed_pairs_at_csv_precision"], 2)
        self.assertEqual(result["stationary_max_component_range_m_s"], 1)

    def test_spatial_change_excluded(self):
        result = summarize(*fixture([0, 1, 2], [1, 2, 3]))
        self.assertEqual(result["stationary_adjacent_pairs"], 0)

    def test_moving_flag_excluded(self):
        result = summarize(*fixture([0]*3, [1, 2, 3], [0, 1, 0]))
        self.assertEqual(result["stationary_adjacent_pairs"], 0)

    def test_gap_excluded(self):
        result = summarize(*fixture([0]*2, [1, 2], steps=[1, 3]))
        self.assertEqual(result["stationary_adjacent_pairs"], 0)

    def test_missing_and_mismatched_rejected(self):
        w, p = fixture([0]*2, [1, 2])
        with self.assertRaises(ValueError):
            summarize(w, p[:1])
        p[0]["x"] = "4"
        with self.assertRaises(ValueError):
            summarize(w, p)

    def test_replay_reversal(self):
        w, _ = fixture([0]*3, [1]*3)
        for r, iteration in zip(w, [8, 9, 0]):
            r["iteration"] = str(iteration)
        resets = replay_resets(w)
        self.assertEqual(len(resets), 1)
        self.assertEqual(resets[0]["time_s"], .6)
        self.assertEqual(resets[0]["previous_iteration"], 9)
        self.assertEqual(resets[0]["iteration"], 0)


if __name__ == "__main__":
    unittest.main()
