"""Independent rank/tie/margin recomputation from the frozen all-source scores."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = json.loads((args.output / "D1_RESULT.json").read_text(encoding="utf-8"))
    all_scores = json.loads((args.output / "ALL_CANDIDATE_SCORES.json").read_text(encoding="utf-8"))
    checked = 0
    for row in result["update_results"]:
        for arm in ("u", "rawu"):
            key = f"{row['case_id']}__{row['event_prefix']}__{arm}"
            saved = all_scores[key]
            ids = saved["candidate_ids"]
            assert len(ids) == row["candidate_count"] and len(set(ids)) == len(ids)
            truth = ids.index(row["source_id"])
            score = np.asarray(saved["sse"], dtype=np.float64)
            assert score.shape == (len(ids),) and np.isfinite(score).all()
            rank = int(np.count_nonzero(score < score[truth]) + 1)
            unique = int(rank == 1 and np.count_nonzero(score == score.min()) == 1)
            wrong = np.delete(score, truth)
            assert row[arm]["truth_rank"] == rank
            assert row[arm]["unique_top1"] == unique
            assert row[arm]["top3"] == int(rank <= 3)
            assert np.isclose(row[arm]["best_wrong_margin"], wrong.min() - score[truth], atol=1e-9)
            checked += 1
    assert checked == 2 * result["update_count"]
    assert len(result["final_trajectory_results"]) == result["trajectory_count"]
    print(json.dumps({"independent_rank_recomputations": checked,
                      "trajectory_count": result["trajectory_count"], "status": "PASS"}))


if __name__ == "__main__":
    main()
