#!/usr/bin/env python3
"""Run PDSW on the six already-frozen TNQC R2 fixed-trajectory archives.

This runner does not launch ROS/GADEN and does not regenerate a trajectory.
It requires each case to already contain the authoritative TNQC V7 replay
artifact, from which evaluator-only truth coordinates are read.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

CASES = [
    ("House01", 0), ("House01", 1),
    ("House02", 0), ("House02", 1),
    ("House03", 0), ("House03", 1),
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--cpp-endpoint-evaluator", type=Path, required=True)
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    replay = here / "pdsw_vgr_fixed_trajectory_replay.py"
    aggregate = here / "aggregate_pdsw_vgr_offline_gate.py"

    for house, seed in CASES:
        d = args.run_root / f"{house}_seed{seed}_off_off"
        frozen = d / "tnqc_fixed_trajectory_evaluation.json"
        p = load(frozen)
        if p.get("contract") != (
                "TNQC_VGR_FIXED_TRAJECTORY_300S_REPLAY_V7_LINKED_NATIVE_ENDPOINT"):
            raise SystemExit(
                f"{d}: expected frozen TNQC V7 linked-native replay artifact")
        truth = p.get("truth")
        if not (isinstance(truth, list) and len(truth) >= 2):
            raise SystemExit(f"{d}: missing evaluator truth coordinates")

        cmd = [
            args.python, str(replay),
            "--run-dir", str(d),
            "--truth-x", str(truth[0]),
            "--truth-y", str(truth[1]),
            "--cpp-endpoint-evaluator", str(args.cpp_endpoint_evaluator),
        ]
        print("+", " ".join(cmd), flush=True)
        subprocess.run(cmd, check=True)

    cmd = [
        args.python, str(aggregate),
        "--run-root", str(args.run_root),
    ]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
