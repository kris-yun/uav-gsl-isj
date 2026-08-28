#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    args = parser.parse_args()
    left = json.loads((args.first / "trajectory_manifest.json").read_text())
    right = json.loads((args.second / "trajectory_manifest.json").read_text())
    left_key = {(r["house"], r["split"], r["seed"]): r for r in left["trajectories"]}
    right_key = {(r["house"], r["split"], r["seed"]): r for r in right["trajectories"]}
    if left_key.keys() != right_key.keys():
        raise SystemExit("PF_DEI_V3_TRAJECTORY_KEY_MISMATCH")
    for key in left_key:
        if left_key[key]["sha256"] != right_key[key]["sha256"]:
            raise SystemExit(f"PF_DEI_V3_TRAJECTORY_NONDETERMINISTIC:{key}")

    max_step = 0.0
    total = 0
    for row in left["trajectories"]:
        path = Path(row["path"])
        with path.open(newline="") as source:
            samples = list(csv.DictReader(source))
        required = {
            "t_sim_s", "step", "x", "y", "z", "yaw", "is_moving", "seed",
            "stop_id", "stop_start", "block_boundary",
        }
        if not samples or set(samples[0]) != required:
            raise SystemExit(f"PF_DEI_V3_TRAJECTORY_SCHEMA_FAIL:{path}")
        if any(field in samples[0] for field in ("gas", "source", "truth", "error", "posterior")):
            raise SystemExit(f"PF_DEI_V3_TRAJECTORY_FORBIDDEN_FIELD:{path}")
        for index, sample in enumerate(samples, start=1):
            if int(sample["step"]) != index or abs(float(sample["t_sim_s"]) - 0.2 * index) > 1e-8:
                raise SystemExit(f"PF_DEI_V3_TRAJECTORY_TIME_FAIL:{path}:{index}")
            if index > 1:
                prior = samples[index - 2]
                distance = math.hypot(float(sample["x"]) - float(prior["x"]), float(sample["y"]) - float(prior["y"]))
                max_step = max(max_step, distance)
                # CSV coordinates are frozen to 1e-6 m, so a diagonal of two
                # independent rounding residuals can exceed 0.1 by <2e-6 m.
                if distance > 0.100002:
                    raise SystemExit(f"PF_DEI_V3_TRAJECTORY_KINEMATIC_FAIL:{path}:{index}:{distance}")
        total += len(samples)

    print(
        "PF_DEI_V3_MAPONLY_TRAJECTORY_AUDIT=PASS "
        f"trajectories={len(left_key)} samples={total} max_step_m={max_step:.9f} "
        f"unique_cells_min={min(r['unique_free_cells_visited'] for r in left['trajectories'])} "
        f"unique_cells_max={max(r['unique_free_cells_visited'] for r in left['trajectories'])} "
        f"stops_min={min(r['stop_count'] for r in left['trajectories'])} "
        f"stops_max={max(r['stop_count'] for r in left['trajectories'])}"
    )
    print(json.dumps(left["houses"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
