#!/usr/bin/env python3
"""Validate explicit CTPI V0.4 posterior->action->environment causal-chain logs.

This is an engineering/evidence checker, not a scientific module.  It does not
infer causality from correlation.  Instead it requires the runtime to log the
exact posterior hash handed to the planner, the command acknowledgement, fresh
observation identity/time, and pre/post poses for each decision step.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

REQUIRED = {
    "step",
    "method",
    "runtime_contract",
    "trajectory_source",
    "observation_id",
    "observation_sim_time",
    "posterior_before_sha256",
    "posterior_after_sha256",
    "planner_posterior_sha256",
    "action_id",
    "command_ack",
    "pose_before_x",
    "pose_before_y",
    "pose_after_x",
    "pose_after_y",
}


def truthy(v: str) -> bool:
    return v.strip().lower() in {"1", "true", "yes", "pass", "ok"}


def finite(v: str) -> float:
    x = float(v)
    if not math.isfinite(x):
        raise ValueError(v)
    return x


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--json-out", default="")
    ap.add_argument("--min-motion-m", type=float, default=1e-3)
    args = ap.parse_args()

    path = Path(args.trace).expanduser().resolve()
    result = {
        "contract": "CTPI_V04_TRUE_CLOSED_LOOP_CAUSAL_CHAIN_V1",
        "trace": str(path),
        "checks": {},
        "failures": [],
    }
    if not path.is_file():
        result["failures"].append("TRACE_MISSING")
        rows = []
        fields = set()
    else:
        result["trace_sha256"] = file_sha256(path)
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields = set(reader.fieldnames or [])
            rows = list(reader)

    missing = sorted(REQUIRED - fields)
    result["checks"]["schema_complete"] = not missing
    if missing:
        result["failures"].append("MISSING_COLUMNS:" + ",".join(missing))

    result["checks"]["nonempty"] = bool(rows)
    if not rows:
        result["failures"].append("NO_DECISION_ROWS")

    if rows and not missing:
        steps = []
        obs_ids = []
        obs_times = []
        moved = 0
        posterior_changed = 0
        planner_matches = 0
        acked = 0
        no_replay = 0
        method_ok = 0
        contract_ok = 0
        action_ids = []

        for i, r in enumerate(rows):
            try:
                step = int(r["step"])
                obs_id = int(r["observation_id"])
                obs_time = finite(r["observation_sim_time"])
                x0, y0 = finite(r["pose_before_x"]), finite(r["pose_before_y"])
                x1, y1 = finite(r["pose_after_x"]), finite(r["pose_after_y"])
            except Exception as exc:
                result["failures"].append(f"ROW_{i}_PARSE:{exc}")
                continue
            steps.append(step)
            obs_ids.append(obs_id)
            obs_times.append(obs_time)
            action_ids.append(r["action_id"].strip())
            if math.hypot(x1 - x0, y1 - y0) > args.min_motion_m:
                moved += 1
            if r["posterior_before_sha256"].strip() != r["posterior_after_sha256"].strip():
                posterior_changed += 1
            if r["planner_posterior_sha256"].strip() == r["posterior_after_sha256"].strip() and r["planner_posterior_sha256"].strip():
                planner_matches += 1
            if truthy(r["command_ack"]):
                acked += 1
            if r["trajectory_source"].strip().lower() not in {"replay", "fixed", "historical", "tape"}:
                no_replay += 1
            if r["method"].strip().lower() == "ctpi_v04":
                method_ok += 1
            if r["runtime_contract"].strip() == "CTPI_V04_RUNTIME_CONTRACT_V1":
                contract_ok += 1

        n = len(rows)
        strict_steps = len(steps) == n and all(b > a for a, b in zip(steps, steps[1:]))
        strict_obs = len(obs_ids) == n and all(b > a for a, b in zip(obs_ids, obs_ids[1:]))
        strict_time = len(obs_times) == n and all(b > a for a, b in zip(obs_times, obs_times[1:]))
        unique_actions = len(action_ids) == n and all(action_ids) and len(set(action_ids)) == n

        result["checks"].update({
            "METHOD_IDENTITY": method_ok == n,
            "RUNTIME_CONTRACT": contract_ok == n,
            "FRESH_OBSERVATION": strict_obs and strict_time,
            "POSTERIOR_UPDATE": posterior_changed > 0,
            "POSTERIOR_TO_ACTION": planner_matches == n,
            "COMMAND_ACK": acked == n,
            "MOTION_FEEDBACK": moved > 0,
            "ACTION_IDENTITY_FRESH": unique_actions,
            "NO_FIXED_TRAJECTORY_REPLAY": no_replay == n,
            "STEP_ORDER": strict_steps,
        })
        result["counts"] = {
            "rows": n,
            "posterior_changed_rows": posterior_changed,
            "planner_posterior_match_rows": planner_matches,
            "command_ack_rows": acked,
            "motion_rows": moved,
        }

        for name, ok in result["checks"].items():
            if name in {"schema_complete", "nonempty"}:
                continue
            if not ok:
                result["failures"].append(name)

    passed = (
        bool(rows)
        and not missing
        and not result["failures"]
        and all(result["checks"].values())
    )
    result["verdict"] = (
        "TRUE_CLOSED_LOOP_CAUSAL_CHAIN=PASS"
        if passed
        else "TRUE_CLOSED_LOOP_CAUSAL_CHAIN=FAIL"
    )

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        out = Path(args.json_out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    return 0 if passed else 43


if __name__ == "__main__":
    raise SystemExit(main())
