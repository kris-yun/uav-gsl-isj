"""Losslessly select the six fields required by the supplied D0.5 cross audit.

Only reads the frozen goal CSV and result JSON. It never recomputes B2 scores,
changes selected goals, or reads target concentration.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "evidence/hd_plf_v0/action_validity_d05/GOAL_COUNTERFACTUALS.csv"
RESULT = ROOT / "evidence/hd_plf_v0/action_validity_d05/D05_RESULT.json"
OUT = ROOT / "evidence/hd_plf_v0/d05_selector_decoder_cross/archived_goals_normalized.csv"
SOURCE_SHA256 = "66a9a2e3f7244f88ed30d706bbab4a4abf26bf0757e83a460317241befb59c1f"
RESULT_SHA256 = "baa871f020703f2d05e9dc1d71d036511c5d61ef5a00bc88ab31b643781f1e10"
FIELDS = ("environment", "source_index", "target_index", "goal_cell", "decoder", "expected_rank")


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if hash_file(SOURCE) != SOURCE_SHA256 or hash_file(RESULT) != RESULT_SHA256:
        raise ValueError("frozen D0.5 input hash mismatch")
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    ep = {(e["environment"], e["source_index"], e["target_index"]): e
          for e in result["episodes"]}
    if len(ep) != 72:
        raise ValueError("expected all 72 archived episodes")
    rows = []
    counts = defaultdict(int)
    selected = defaultdict(list)
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {"environment", "source_index", "target_index", "goal_cell", "arm",
                    "rank_before_tie_aware", "rank_after_tie_aware", "rank_gain", "selected"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("archived CSV lacks the frozen rank/selection columns")
        for original in reader:
            key = tuple(int(original[name]) for name in ("environment", "source_index", "target_index"))
            arm = original["arm"]
            goal = int(original["goal_cell"])
            if key not in ep or arm not in ("LF-u", "LF-rawu"):
                raise ValueError("unexpected episode or decoder")
            before = float(original["rank_before_tie_aware"])
            after = float(original["rank_after_tie_aware"])
            gain = float(original["rank_gain"])
            if not (1 <= before <= 6 and 1 <= after <= 6 and abs(before - after - gain) < 1e-12):
                raise ValueError("archived tie-aware rank identity failed")
            if original["selected"] not in ("True", "False"):
                raise ValueError("unknown archived selection flag")
            if original["selected"] == "True":
                selected[(key, arm)].append(goal)
            counts[(key, arm)] += 1
            # Preserve the archived decimal string; do not recompute or round rank.
            rows.append({"environment": original["environment"],
                         "source_index": original["source_index"],
                         "target_index": original["target_index"],
                         "goal_cell": original["goal_cell"],
                         "decoder": arm,
                         "expected_rank": original["rank_after_tie_aware"]})
    if len(rows) != 2208 or len(counts) != 144:
        raise ValueError("not all 1104 goals x two decoders are present")
    for key, episode in ep.items():
        for arm in ("LF-u", "LF-rawu"):
            if counts[(key, arm)] != episode["feasible_goals"]:
                raise ValueError(f"action count mismatch at {key}, {arm}")
            if selected[(key, arm)] != [episode[arm]["selected_cell"]]:
                raise ValueError(f"selected goal mismatch at {key}, {arm}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"rows": len(rows), "episodes": len(ep), "goal_sets": len(counts),
                      "normalized_sha256": hash_file(OUT)}, indent=2))


if __name__ == "__main__":
    main()
