#!/usr/bin/env python3
"""Fail-closed CSTAR formal closed-loop authorization.

This tool never launches ROS/GADEN. It only verifies that the preregistered
scientific and runtime evidence artifacts exist and have the exact contracts
required before the seed12 A0/F00/F10/F11 development screen may start.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED = {
    "m1": "CSTAR_M1_CONTROLLED_CAUSAL_GATE_V1",
    "m2": "CSTAR_M2_SOURCE_DIVERSE_PREDICTIVE_GATE_V1",
    "m3": "CSTAR_M3_COUNTERFACTUAL_GATE_V1",
    "models": "CSTAR_FROZEN_MODEL_MANIFEST_V1",
    "production": "CSTAR_PRODUCTION_MODE_MANIFEST_V1",
    "smoke": "CSTAR_RUNTIME_SMOKE_V1",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path, label: str) -> dict:
    if not path.is_file():
        raise RuntimeError(f"CSTAR_AUTH_MISSING:{label}:{path}")
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"CSTAR_AUTH_JSON:{label}:{exc}") from exc
    expected = REQUIRED[label]
    if obj.get("contract") != expected:
        raise RuntimeError(
            f"CSTAR_AUTH_CONTRACT:{label}:{obj.get('contract')}:{expected}"
        )
    if obj.get("pass") is not True:
        raise RuntimeError(f"CSTAR_AUTH_NOT_PASS:{label}:{obj.get('verdict')}")
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--m1", type=Path, required=True)
    ap.add_argument("--m2", type=Path, required=True)
    ap.add_argument("--m3", type=Path, required=True)
    ap.add_argument("--models", type=Path, required=True)
    ap.add_argument("--production", type=Path, required=True)
    ap.add_argument("--smoke", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    inputs = {name: getattr(args, name) for name in REQUIRED}
    loaded = {name: load(path, name) for name, path in inputs.items()}

    # Cross-artifact anti-drift checks. These identities must be written by the
    # VM integration workflow after freezing models and the cstar_v1 runtime.
    model_manifest_sha = sha256_file(args.models)
    production = loaded["production"]
    smoke = loaded["smoke"]
    if production.get("model_manifest_sha256") != model_manifest_sha:
        raise RuntimeError("CSTAR_AUTH_MODEL_MANIFEST_HASH_MISMATCH")
    production_sha = sha256_file(args.production)
    if smoke.get("production_manifest_sha256") != production_sha:
        raise RuntimeError("CSTAR_AUTH_PRODUCTION_MANIFEST_HASH_MISMATCH")
    if smoke.get("future_read_violations", 1) != 0:
        raise RuntimeError("CSTAR_AUTH_FUTURE_READ_VIOLATION")
    if smoke.get("truth_or_house_runtime_reads", 1) != 0:
        raise RuntimeError("CSTAR_AUTH_TRUTH_RUNTIME_READ")
    if smoke.get("deployment_bank_queries", 1) != 0:
        raise RuntimeError("CSTAR_AUTH_DEPLOYMENT_BANK_QUERY")
    if smoke.get("invalid_route_count", 1) != 0:
        raise RuntimeError("CSTAR_AUTH_INVALID_ROUTE")
    if smoke.get("native_route_missing_when_feasible", 1) != 0:
        raise RuntimeError("CSTAR_AUTH_NATIVE_ROUTE_MISSING")

    report = {
        "contract": "CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZATION_V1",
        "pass": True,
        "formal_closed_loop_authorized": True,
        "authorized_matrix": {
            "houses": ["H01", "H02", "H03"],
            "seed": 12,
            "arms": ["A0", "F00", "F10", "F11"],
            "horizon_s": 240.0,
            "run_count": 12,
        },
        "inputs": {
            name: {
                "path": str(path),
                "sha256": sha256_file(path),
                "contract": REQUIRED[name],
                "verdict": loaded[name].get("verdict"),
            }
            for name, path in inputs.items()
        },
        "stop_after_matrix": True,
        "multiseed_authorized": False,
        "verdict": "CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZED=TRUE",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
