#!/usr/bin/env python3
"""Freeze source-blind A/B/C scores and map hashes before truth evaluation."""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--replay-binary", type=Path, required=True)
    args = ap.parse_args()
    run = args.run
    target = run / "r1_scores_frozen_manifest.json"
    if target.exists():
        raise RuntimeError("scores already frozen; refusing overwrite")
    inputs = ["measurement_events.csv", "measured_map_at_update.csv",
              "frozen_candidate_geometry.csv", "wind_source_update.csv",
              "gmrf_wind_at_update.csv"]
    document = {
        "contract": "NATIVE_PMFS_R1_THREE_ARM_FROZEN_SCORES_V1",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "truth_inputs_read": False,
        "replay_binary_sha256": sha(args.replay_binary),
        "source_blind_inputs": {name: sha(run / name) for name in inputs},
        "arms": {},
    }
    reference_ids = None
    for arm in "ABC":
        folder = run / f"R1_arm_{arm}"
        repeat = run / f"R1_arm_{arm}_repeat"
        for path in (folder, repeat):
            if not (path / "candidate_scores.csv").is_file() or not (path / "source_blind_replay_audit.txt").is_file():
                raise RuntimeError(f"incomplete replay: {path}")
        rows = list(csv.DictReader((folder / "candidate_scores.csv").open(newline="")))
        repeated_rows = list(csv.DictReader((repeat / "candidate_scores.csv").open(newline="")))
        if not rows or rows != repeated_rows:
            raise RuntimeError(f"non-deterministic scores for arm {arm}")
        ids = [row["candidate_id"] for row in rows]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"duplicate candidate ID in arm {arm}")
        if reference_ids is None:
            reference_ids = ids
        elif ids != reference_ids:
            raise RuntimeError("candidate geometry/order differs across arms")
        maps = {}
        for row in rows:
            if row["arm"] != arm:
                raise RuntimeError("arm label mismatch")
            relative = Path(row["map_file"])
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError("unsafe map path")
            first = folder / relative
            second = repeat / relative
            if first.stat().st_size != second.stat().st_size or sha(first) != sha(second):
                raise RuntimeError(f"non-deterministic candidate map: {arm} {row['candidate_id']}")
            maps[row["candidate_id"]] = sha(first)
        first_scores = sha(folder / "candidate_scores.csv")
        second_scores = sha(repeat / "candidate_scores.csv")
        if first_scores != second_scores:
            raise RuntimeError(f"non-deterministic CSV bytes for arm {arm}")
        document["arms"][arm] = {
            "candidate_count": len(rows),
            "scores_sha256": first_scores,
            "repeated_scores_sha256": second_scores,
            "candidate_map_sha256": maps,
            "replay_audit_sha256": sha(folder / "source_blind_replay_audit.txt"),
            "deterministic_repeat_pass": True,
        }
    document["candidate_ids"] = reference_ids
    target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"R1_SCORES_FROZEN candidates={len(reference_ids)} manifest={target}")


if __name__ == "__main__":
    main()
