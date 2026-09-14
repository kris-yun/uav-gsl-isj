#!/usr/bin/env python3
"""Finalize the support-extension audit and write its immutable hash list."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
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
    gate["TRACE_INTEGRITY"] = "PASS"
    gate["trace_integrity_audit_sha256"] = sha256(audit_path)
    gate["endpoint_query_summary_sha256"] = sha256(args.out_dir / "ENDPOINT_QUERY_SUMMARY.json")
    gate["scoring_policy_sha256"] = sha256(args.out_dir / "SCORING_POLICY_FREEZE.json")
    gate["finalization_status"] = "PASS"
    gate_path.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    required = [
        args.out_dir / name for name in (
            "MECHANISM_POLICY_FREEZE.json", "MECHANISM_POLICY_FREEZE_RERUN.json", "SCORING_POLICY_FREEZE.json",
            "TRACE_INTEGRITY_AUDIT.json", "ENDPOINT_QUERY_SUMMARY.json",
            "SUPPORT_EXTENSION_SCORE.json", "FINAL_GATE.json",
        )
    ]
    required += [args.out_dir / "candidates/CANDIDATE_MANIFEST.json"]
    required += [args.result_note, args.repo / "tools/build_support_extension_routes.py", args.repo / "tools/query_support_extension_design_routes.py", args.repo / "tools/audit_support_extension_traces.py", args.repo / "tools/score_support_extension.py"]
    required += sorted((args.out_dir / "candidates").glob("AO_*/*.csv"), key=lambda path: str(path).lower())
    required += sorted((args.out_dir / "endpoint_design_traces").glob("*.csv.gz"), key=lambda path: str(path).lower())
    required = sorted({path.resolve() for path in required}, key=lambda path: str(path).lower())
    lines = [f"{sha256(path)}  {path.relative_to(args.repo.resolve()).as_posix()}" for path in required]
    (args.out_dir / "FINAL_SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"trace_integrity": gate["TRACE_INTEGRITY"], "hash_entries": len(lines), "final_verdict": gate["FINAL_VERDICT"]}))


if __name__ == "__main__":
    main()
