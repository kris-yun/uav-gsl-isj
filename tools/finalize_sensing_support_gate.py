#!/usr/bin/env python3
"""Finalize the audited design-wind gate and emit the final hash manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--result-note", type=Path, required=True)
    args = parser.parse_args()
    audit_path = args.out_dir / "TRACE_INTEGRITY_AUDIT.json"
    gate_path = args.out_dir / "FINAL_GATE.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if audit["status"] != "PASS":
        raise RuntimeError("cannot finalize a failed trace audit")
    if gate["HELD_WIND_STATUS"] != "NOT_RUN_NOT_READ":
        raise RuntimeError("held-wind status is not frozen closed")
    gate["TRACE_INTEGRITY"] = audit["status"]
    gate["trace_integrity_audit_sha256"] = sha256_file(audit_path)
    gate["endpoint_query_summary_sha256"] = sha256_file(args.out_dir / "ENDPOINT_QUERY_SUMMARY.json")
    gate["finalization_status"] = "PASS"
    gate_path.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")

    required = [
        args.out_dir / name for name in (
            "MEASUREMENT_POLICY_FREEZE.json", "TRACE_INTEGRITY_AUDIT.json", "C0_REFERENCE_REPRODUCTION.json",
            "C1_CENTER_RAW_ORACLE.json", "C2_D2_PROCESSED_FOPDT.json", "C3_D2_RAW_ORACLE.json",
            "CONFIGURATION_COMPARISON.json", "FINAL_GATE.json", "PRE_RESPONSE_SHA256SUMS", "ENDPOINT_QUERY_SUMMARY.json",
        )
    ]
    required += [args.result_note, args.repo / "tools/query_sensing_support_design_routes.py", args.repo / "tools/audit_sensing_support_upper_bound.py", args.repo / "tools/score_sensing_support_upper_bound.py"]
    required += sorted((args.out_dir / "endpoint_design_traces").glob("*.csv.gz"))
    required += sorted((args.out_dir / "remote_batch_summaries").glob("*.json"))
    required = sorted({path.resolve() for path in required}, key=lambda path: str(path).lower())
    lines = [f"{sha256_file(path)}  {path.relative_to(args.repo.resolve()).as_posix()}" for path in required]
    (args.out_dir / "FINAL_SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"trace_integrity": gate["TRACE_INTEGRITY"], "hash_entries": len(lines), "final_verdict": gate["FINAL_VERDICT"]}))


if __name__ == "__main__":
    main()
