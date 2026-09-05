#!/usr/bin/env python3
"""Verify activation and causal traces for A0/F00/F01 seed-12 runs."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ARMS = ("A0", "F00", "F01")


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"CTPI_G2_M12_TRACE_MISSING:{path}")
    with path.open(newline="", encoding="utf-8") as handle:
        result = list(csv.DictReader(handle))
    if not result:
        raise RuntimeError(f"CTPI_G2_M12_TRACE_EMPTY:{path}")
    return result


def goals(nav: list[dict[str, str]]) -> list[tuple[float, float]]:
    return [
        (round(float(row["goal_x"]), 6), round(float(row["goal_y"]), 6))
        for row in nav if row.get("event") == "SENT"
    ]


def movement(pose: list[dict[str, str]]) -> float:
    points = []
    for row in pose:
        try:
            points.append((float(row.get("x", row.get("pose_x", "nan"))),
                           float(row.get("y", row.get("pose_y", "nan")))))
        except ValueError:
            continue
    if len(points) < 2:
        return 0.0
    return max(math.hypot(x - points[0][0], y - points[0][1]) for x, y in points)


def estimate_signature(trace: list[dict[str, str]]) -> list[tuple[float, float, float]]:
    result = []
    for row in trace:
        try:
            result.append((round(float(row["sim_time"]), 6),
                           round(float(row["estimate_x"]), 6),
                           round(float(row["estimate_y"]), 6)))
        except (KeyError, ValueError):
            continue
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--house", choices=("H01", "H02", "H03"), required=True)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    checks: dict[str, bool] = {}
    signatures = {}
    sequences = {}
    for arm in ARMS:
        root = args.run_root / f"{args.house}_seed{args.seed}_{arm}"
        manifest = json.loads((root / "formal_runtime_manifest.json").read_text())
        nav = rows(root / "navigation_trace.csv")
        sensor = rows(root / "sensor_trace.csv")
        pose = rows(root / "sim_pose_trace.csv")
        estimate = rows(root / "source_estimate_trace.csv")
        prefix = f"{arm}_"
        checks[prefix + "terminal_guard"] = json.loads(
            (root / "CTPI_FASTTRACK_CASE_TERMINAL.json").read_text()
        ).get("pass") is True
        checks[prefix + "manifest_arm"] = manifest.get("arm") == arm
        checks[prefix + "seed_12"] = manifest.get("seed") == args.seed == 12
        checks[prefix + "motion_feedback"] = movement(pose) > 0.05
        checks[prefix + "sensor_stream"] = len(sensor) >= 2
        checks[prefix + "navigation_sent"] = bool(goals(nav))
        checks[prefix + "estimate_trace"] = len(estimate_signature(estimate)) >= 2
        sequences[arm] = goals(nav)
        signatures[arm] = estimate_signature(estimate)
        if arm != "A0":
            checks[prefix + "cpir_updates"] = bool(rows(root / "ctpi_audit/cpir_update_audit.csv"))

    f00_manifest = json.loads((args.run_root / f"{args.house}_seed12_F00/formal_runtime_manifest.json").read_text())
    f01_root = args.run_root / f"{args.house}_seed12_F01"
    f01_manifest = json.loads((f01_root / "formal_runtime_manifest.json").read_text())
    checks["F00_is_M1_only"] = f00_manifest.get("pfdi_mode") == "ctpi_f00"
    checks["F01_is_M1_M2_only"] = (
        f01_manifest.get("pfdi_mode") == "ctpi_f01"
        and f01_manifest.get("method") == "CTPI_G2_M1_M2"
        and f01_manifest.get("method_family") == "ctpi_two_module"
    )
    m3_audit = f01_root / "ctpi_audit/ctpi_m3_action_audit.csv"
    checks["F01_M3_inactive"] = not m3_audit.exists() or m3_audit.stat().st_size == 0
    checks["M1_changes_closed_loop"] = (
        sequences["F00"] != sequences["A0"] or signatures["F00"] != signatures["A0"]
    )
    checks["M2_changes_closed_loop"] = (
        sequences["F01"] != sequences["F00"] or signatures["F01"] != signatures["F00"]
    )

    passed = all(checks.values())
    report = {
        "contract": "CTPI_G2_M1_M2_SEED12_CAUSAL_CHECK_V1",
        "house": args.house,
        "seed": args.seed,
        "checks": checks,
        "pass": passed,
        "verdict": "CTPI_G2_M12_CAUSAL_CHAIN=PASS" if passed else "CTPI_G2_M12_CAUSAL_CHAIN=FAIL",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["verdict"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
