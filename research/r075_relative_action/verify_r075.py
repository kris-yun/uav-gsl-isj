"""Cross-check frozen D1/CD baselines and centered/all-pair identity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "research/cd_d0_action_sensory"))
from score_cd_d0 import profile  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--r075", type=Path, required=True)
    args = p.parse_args()
    r075 = json.loads(args.r075.read_text(encoding="utf-8"))
    cd = json.loads((REPO / "evidence/cd_d0_action_sensory/CD_D0_RESULT.json").read_text(encoding="utf-8"))
    old = {(v["case_id"], v["prefix"]): v for v in cd["update_results"]}
    checked = 0
    for row in r075["update_results"]:
        previous = old[(row["case_id"], row["event_prefix"])]
        assert row["source_id"] == previous["source_id"]
        assert row["candidate_count"] == previous.get("candidate_count", row["candidate_count"])
        for arm in ("u", "rawu"):
            for new, prior in (("ABS", "absolute_b2"), ("REAL_ADJ", "real")):
                assert row[arm][new]["truth_rank"] == previous[arm][prior + "_rank"]
                assert row[arm][new]["unique_top1"] == previous[arm][prior + "_top1"]
                assert np.isclose(row[arm][new]["best_wrong_margin"],
                                  previous[arm][prior + "_margin"], rtol=1e-9, atol=1e-8)
                checked += 1
    assert len(r075["update_results"]) == len(cd["update_results"])
    assert checked == 4 * r075["update_count"]
    # For any gain g, all-pair residual differences equal n times centered
    # residual energy. Profile both sides independently and compare optima.
    rng = np.random.default_rng(2026092805)
    y = rng.normal(size=11)
    candidates = rng.normal(size=(23, 11))
    yc = y - y.mean()
    mc = candidates - candidates.mean(axis=1, keepdims=True)
    centered = profile(mc, yc)
    i, j = np.triu_indices(len(y), 1)
    pair = profile(candidates[:, j] - candidates[:, i], y[j] - y[i])
    assert np.allclose(pair, len(y) * centered, rtol=1e-12, atol=1e-10)
    # Joint stop permutation preserves every absolute and centered candidate
    # score because the observation and its template move as one pair.
    pi = rng.permutation(len(y))
    assert np.allclose(profile(candidates[:, pi], y[pi]), profile(candidates, y),
                       rtol=1e-12, atol=1e-10)
    assert np.allclose(profile(mc[:, pi], yc[pi]), centered, rtol=1e-12, atol=1e-10)
    print(json.dumps({"D1_CD_absolute_and_adj_parity": checked,
                      "all_pair_centered_profile_identity": "PASS",
                      "joint_stop_permutation_invariance": "PASS"}))


if __name__ == "__main__":
    main()
