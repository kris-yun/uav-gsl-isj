"""Verify that five-event stop averaging preserves the original absolute B2 rank."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cd", type=Path, required=True)
    p.add_argument("--d1", type=Path, required=True)
    args = p.parse_args()
    cd = json.loads(args.cd.read_text(encoding="utf-8"))
    d1 = json.loads(args.d1.read_text(encoding="utf-8"))
    by_case = {r["case_id"]: r for r in d1["final_trajectory_results"]}
    checked = 0
    for row in cd["final_results"]:
        parent = by_case[row["case_id"]]
        assert row["prefix"] == parent["event_prefix"]
        for arm in ("u", "rawu"):
            assert row[arm]["absolute_b2_rank"] == parent[arm]["truth_rank"]
            assert row[arm]["absolute_b2_top1"] == parent[arm]["unique_top1"]
            # Every stop contributes five observations at the exact same pose.
            assert np.isclose(5 * row[arm]["absolute_b2_margin"],
                              parent[arm]["best_wrong_margin"], rtol=1e-7, atol=1e-6)
            assert len(row[arm]["permutation_ranks"]) == 200
            checked += 1
    assert checked == 2 * cd["trajectory_count"] == 98
    print(json.dumps({"absolute_B2_rank_and_margin_parity": checked, "status": "PASS"}))


if __name__ == "__main__":
    main()
