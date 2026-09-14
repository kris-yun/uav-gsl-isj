#!/usr/bin/env python3
"""Read-only contract audit for a PE-WHRM shadow trajectory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames or [], rows


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def monotonic(rows, key):
    vals = [float(r[key]) for r in rows if r.get(key) not in (None, "")]
    return all(b > a for a, b in zip(vals, vals[1:]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    d = args.run_dir.resolve()
    paths = {
        "sensor": d / "sensor_trace.csv",
        "pose": d / "sim_pose_trace.csv",
        "wind": d / "wind_trace.csv",
        "status": d / "run_status.json",
        "raw_record": next(iter((d / "results" / "raw").glob("*_record.csv")), None),
        "candidate_scores": d / "analysis" / "p2_fixed_path_candidate_scores.csv",
    }
    required = {
        "sensor": {"t_sim_s", "step", "x", "y", "z", "true_gas_ppm", "measured_gas_ppm", "seed"},
        "pose": {"t_sim_s", "step", "x", "y", "z", "yaw", "seed"},
        "wind": {"t_sim_s", "step", "x", "y", "z", "wind_u", "wind_v", "wind_w", "seed"},
        "candidate_scores": {"source_update_id", "candidate_id", "source_x", "source_y"},
    }
    checks = {}
    rows_by_name = {}
    headers_by_name = {}
    for name in ("sensor", "pose", "wind", "candidate_scores"):
        p = paths[name]
        exists = p is not None and p.exists()
        headers, rows = read_csv(p) if exists else ([], [])
        rows_by_name[name] = rows
        headers_by_name[name] = headers
        checks[f"{name}_exists"] = exists
        checks[f"{name}_schema"] = exists and required[name].issubset(set(headers))
        checks[f"{name}_nonempty"] = bool(rows)
        if name in ("sensor", "pose", "wind"):
            checks[f"{name}_time_strictly_increasing"] = bool(rows) and monotonic(rows, "t_sim_s")
    checks["trace_lengths_aligned"] = len(rows_by_name["sensor"]) == len(rows_by_name["pose"]) == len(rows_by_name["wind"])

    status = json.loads(paths["status"].read_text(encoding="utf-8")) if paths["status"] and paths["status"].exists() else {}
    checks["run_status_present"] = bool(status)
    checks["trajectory_completed"] = status.get("status") in {"completed", "success", "localized"}

    raw = {}
    if paths["raw_record"] and paths["raw_record"].exists():
        _, raw_rows = read_csv(paths["raw_record"])
        raw = raw_rows[0] if raw_rows else {}
    checks["source_label_join_available"] = all(raw.get(k) not in (None, "") for k in ("ground_truth_x", "ground_truth_y", "dataset", "seed"))
    checks["context_stratum_available"] = all(raw.get(k) not in (None, "") for k in ("dataset", "config_id", "wind_config", "sensor_config", "seed"))
    checks["candidate_map_trace_available"] = checks["candidate_scores_exists"] and checks["candidate_scores_schema"] and checks["candidate_scores_nonempty"]

    structural_pass = all(checks[k] for k in (
        "sensor_exists", "sensor_schema", "sensor_nonempty", "sensor_time_strictly_increasing",
        "pose_exists", "pose_schema", "pose_nonempty", "pose_time_strictly_increasing",
        "wind_exists", "wind_schema", "wind_nonempty", "wind_time_strictly_increasing",
        "trace_lengths_aligned", "run_status_present", "source_label_join_available",
        "context_stratum_available", "candidate_map_trace_available"))
    readiness = "READY_FOR_SHADOW" if structural_pass and checks["trajectory_completed"] else "CONTRACT_PARTIAL_NO_GO"
    result = {
        "mechanism": "PE-WHRM",
        "run_dir": str(d),
        "status": readiness,
        "structural_contract_pass": structural_pass,
        "trajectory_usable_for_final_claim": False,
        "reason": "The selected artifact has the required joined fields but its run status is not completed; it is contract evidence only, not a localization result.",
        "run_status": status,
        "source_context": {k: raw.get(k) for k in ("run_id", "dataset", "config_id", "source_config", "wind_config", "sensor_config", "seed", "ground_truth_x", "ground_truth_y", "gsl_action_status", "declared_success")},
        "checks": checks,
        "row_counts": {k: len(v) for k, v in rows_by_name.items()},
        "sha256": {k: sha256(p) for k, p in paths.items() if p is not None and p.exists() and p.is_file()},
        "next_gate": "Use only a completed source-labelled development shadow; do not open held-out or closed-loop claims from this timeout artifact.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": readiness, "structural_contract_pass": structural_pass, "trajectory_completed": checks["trajectory_completed"], "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
