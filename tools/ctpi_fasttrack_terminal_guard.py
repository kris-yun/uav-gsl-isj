#!/usr/bin/env python3
"""Fail-closed terminal guard for one CTPI fast-track closed-loop case.

This guard does not score localization performance. It verifies that a case
which the shell wrapper considers complete has the frozen runtime identity,
a non-failure terminal record, and the trace products required by the later
causal/performance Gates.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

FAIL_TOKENS = ("fail", "error", "exception", "abort", "crash", "invalid")


def csv_rows(path: Path) -> int:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"TRACE_MISSING_OR_EMPTY:{path.name}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2:
        raise RuntimeError(f"TRACE_NO_DATA:{path.name}")
    return len(rows) - 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--arm", choices=("A0", "F00", "F01", "F10", "F11"), required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.run_dir.resolve()

    status_path = root / "run_status.json"
    manifest_path = root / "formal_runtime_manifest.json"
    if not status_path.is_file() or not manifest_path.is_file():
        raise RuntimeError("CTPI_TERMINAL_RECORD_MISSING")
    status = json.loads(status_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    terminal = str(status.get("status", "")).strip()
    if not terminal:
        raise RuntimeError("CTPI_TERMINAL_STATUS_EMPTY")
    if any(token in terminal.lower() for token in FAIL_TOKENS):
        raise RuntimeError(f"CTPI_TERMINAL_STATUS_FAILURE:{terminal}")

    checks = {
        "arm_matches": manifest.get("arm") == args.arm,
        "contract_matches": manifest.get("contract") == "CTPI_FASTTRACK_PAIRED_RUN_V0",
        "timeout_240": abs(float(manifest.get("timeout_sec", -1.0)) - 240.0) <= 1e-12,
        "steps_source_update_3": int(manifest.get("steps_source_update", -1)) == 3,
        "max_warmup_3": int(manifest.get("max_warmup_iterations", -1)) == 3,
        "min_warmup_1": int(manifest.get("min_warmup_iterations", -1)) == 1,
        "terminal_nonfailure": True,
    }
    trace_rows = {}
    for name in ("navigation_trace.csv", "sensor_trace.csv", "sim_pose_trace.csv", "source_estimate_trace.csv"):
        trace_rows[name] = csv_rows(root / name)
    if args.arm in {"F10", "F11"}:
        trace_rows["ctpi_m3_action_audit.csv"] = csv_rows(root / "ctpi_audit" / "ctpi_m3_action_audit.csv")

    checks["required_traces_nonempty"] = all(value >= 1 for value in trace_rows.values())
    passed = all(checks.values())
    report = {
        "contract": "CTPI_FASTTRACK_CASE_TERMINAL_GUARD_V0",
        "arm": args.arm,
        "terminal_status": terminal,
        "checks": checks,
        "trace_rows": trace_rows,
        "pass": passed,
        "verdict": "CTPI_FASTTRACK_CASE_TERMINAL=PASS" if passed else "CTPI_FASTTRACK_CASE_TERMINAL=FAIL",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
