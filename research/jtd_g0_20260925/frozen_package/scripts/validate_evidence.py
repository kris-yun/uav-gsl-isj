#!/usr/bin/env python3
"""Minimal evidence validator for JTD-G0.
This checks file presence and basic machine-summary consistency.
It does NOT recompute the scientific result.
"""
from pathlib import Path
import json, sys, hashlib

if len(sys.argv) != 2:
    print("usage: validate_evidence.py <evidence/jtd_g0_20260925>")
    sys.exit(2)

root = Path(sys.argv[1])
required = [
    "audit/R0_INPUT_AUDIT.json",
    "audit/R0_INPUT_AUDIT.md",
    "config/frozen_config.yaml",
    "config/folds.json",
    "config/shuffle_seeds.json",
    "metrics/target_metrics_full.csv",
    "metrics/target_metrics_null_long.csv",
    "metrics/null_replicate_summary.csv",
    "metrics/fold_summary.csv",
    "metrics/source_summary.csv",
    "metrics/leave_one_source_out.csv",
    "metrics/confusion_full.csv",
    "metrics/confusion_null_median.csv",
    "metrics/control_models_summary.csv",
    "JTD_G0_MACHINE_SUMMARY.json",
    "JTD_G0_DECISION_20260925.md",
]
missing = [p for p in required if not (root/p).exists()]
if missing:
    print("MISSING:")
    print("\n".join(missing))
    sys.exit(1)

summary = json.loads((root/"JTD_G0_MACHINE_SUMMARY.json").read_text())
allowed = {
    "JTD_G0_GO_TEMPORAL_DEPENDENCE_SIGNAL",
    "JTD_G0_HOLD_WEAK_OR_UNSTABLE_SIGNAL",
    "JTD_G0_STOP_NO_INCREMENTAL_TEMPORAL_SIGNAL",
    "JTD_G0_STOP_INPUT_CONTRACT_INVALID",
}
if summary.get("decision") not in allowed:
    raise SystemExit(f"invalid decision: {summary.get('decision')}")
if summary.get("n_sources") not in (18, None):
    raise SystemExit("n_sources mismatch")
if summary.get("n_realizations_per_source") not in (16, None):
    raise SystemExit("n_realizations_per_source mismatch")

for k in ["no_closed_loop","no_dense_expansion","no_new_plume_generation"]:
    if summary.get(k) is not True:
        raise SystemExit(f"{k} must be true")

print("JTD-G0 evidence structure: PASS")
print("decision:", summary["decision"])
