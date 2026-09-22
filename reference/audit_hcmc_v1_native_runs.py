#!/usr/bin/env python3
"""Audit the frozen six Native PMFS runs before HCMC posterior generation."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


CASES = (
    "H01_R2026092201", "H01_R2026092202",
    "H02_R2026092211", "H02_R2026092212",
    "H03_R2026092221", "H03_R2026092222",
)
TRACES = ("sensor_trace.csv", "sim_pose_trace.csv", "wind_trace.csv")


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def trace_audit(path: Path) -> dict:
    if not path.is_file():
        return {"pass": False, "reason": "missing"}
    rows = read_csv(path)
    result = {"row_count": len(rows), "pass": len(rows) == 1500}
    if not rows:
        return result
    keys = set(rows[0])
    step_key = next((key for key in ("step", "sample_index", "iteration") if key in keys), None)
    if step_key:
        values = [int(float(row[step_key])) for row in rows]
        result["step_key"] = step_key
        result["step_contiguous"] = all(b - a == 1 for a, b in zip(values, values[1:]))
        result["pass"] &= result["step_contiguous"]
    time_key = next((key for key in ("t_sim_s", "sim_time", "timestamp", "time", "stamp") if key in keys), None)
    if time_key:
        values = [float(row[time_key]) for row in rows]
        result["time_key"] = time_key
        result["first_time"] = values[0]
        result["last_time"] = values[-1]
        result["time_strictly_increasing"] = all(b > a for a, b in zip(values, values[1:]))
        result["pass"] &= result["time_strictly_increasing"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    frozen = {entry["case_id"]: entry for entry in freeze["realizations"]}
    reports = []
    all_pass = True
    for case_id in CASES:
        case_dir = args.run_root / case_id
        runtime_path = case_dir / "runtime_manifest.json"
        status_path = case_dir / "run_status.json"
        runtime = json.loads(runtime_path.read_text()) if runtime_path.is_file() else {}
        status = json.loads(status_path.read_text()) if status_path.is_file() else {}
        trace_reports = {name: trace_audit(case_dir / name) for name in TRACES}
        update_dirs = sorted(
            path
            for path in (case_dir / "context_bank").glob("source_update_*")
            if path.is_dir()
        )
        last_update = update_dirs[-1] if update_dirs else None
        bank = {
            "source_update_count": len(update_dirs),
            "last_update": str(last_update) if last_update else None,
            "candidate_manifest_present": bool(last_update and (last_update / "candidate_manifest.csv").is_file()),
            "candidate_support_alignment_present": bool(last_update and (last_update / "candidate_support_alignment.csv").is_file()),
        }
        log = (case_dir / "launch.log").read_text(errors="replace") if (case_dir / "launch.log").is_file() else ""
        matches = list(re.finditer(r"RESULT IS:.*?Error=([0-9.eE+-]+)", log))
        frozen_case = frozen[case_id]
        checks = {
            "terminal_status_present": status.get("status") == "time_budget_timeout",
            "all_traces_pass": all(item["pass"] for item in trace_reports.values()),
            "final_bank_complete": bank["candidate_manifest_present"] and bank["candidate_support_alignment_present"],
            "algorithm_sha_matches_freeze": runtime.get("algorithm_sha256") == frozen_case["pmfs_binary_sha256"],
            "launch_sha_matches_freeze": runtime.get("launch_sha256") == frozen_case["launch_sha256"],
            "realization_manifest_sha_matches_freeze": runtime.get("realization_manifest_sha256") == frozen_case["generation_manifest_sha256"],
            "logged_native_endpoint_present": bool(matches),
        }
        case_pass = all(checks.values())
        all_pass &= case_pass
        reports.append({
            "case_id": case_id,
            "pass": case_pass,
            "checks": checks,
            "traces": trace_reports,
            "context_bank": bank,
            "logged_native_error_m": float(matches[-1].group(1)) if matches else None,
            "runtime_manifest": runtime,
            "run_status": status,
        })
    output = {"contract": "HCMC_V1_NATIVE_RUN_INTEGRITY_V1", "all_pass": all_pass, "cases": reports}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    raise SystemExit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
