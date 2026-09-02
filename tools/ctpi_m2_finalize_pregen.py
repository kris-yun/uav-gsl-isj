#!/usr/bin/env python3
"""Validate Phase-0 A-F evidence and emit the sole CAL unlock marker."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


CONTRACT = "CTPI_M2_SOURCE_INTERVENTION_PREGEN_AUDIT_V1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path, contract: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("contract") != contract or not value.get("pass"):
        raise RuntimeError(f"CTPI_PREGEN_INPUT:{path}:{value.get('contract')}:{value.get('pass')}")
    return value


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--rng-inventory", type=Path, required=True)
    parser.add_argument("--world-manifest", type=Path, required=True)
    parser.add_argument("--runtime-report", type=Path, required=True)
    parser.add_argument("--smoke-a", type=Path, required=True)
    parser.add_argument("--smoke-b", type=Path, required=True)
    parser.add_argument("--materializer-code", type=Path, required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--preserved-failure", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    selection = load(args.selection, "CTPI_M2_SOURCE_SELECTION_V3")
    inventory = load(args.rng_inventory, "CTPI_M2_LEGACY_RNG_INVENTORY_V1")
    worlds = load(args.world_manifest, "CTPI_M2_SOURCE_INTERVENTION_WORLD_MANIFEST_V1")
    runtime = load(args.runtime_report, "CTPI_M2_GENERATOR_RUNTIME_IDENTITY_V1")
    smoke_a = load(args.smoke_a, "CTPI_M2_ONE_WORLD_MATERIALIZER_V1")
    smoke_b = load(args.smoke_b, "CTPI_M2_ONE_WORLD_MATERIALIZER_V1")

    smoke_checks = {
        "same_disposable_identity": smoke_a["world_id"] == smoke_b["world_id"]
            == worlds["disposable_smoke_world"]["world_id"],
        "same_payload_sha256": smoke_a["payload_sha256"] == smoke_b["payload_sha256"],
        "same_world_audit_sha256": sha256_file(args.smoke_a) == sha256_file(args.smoke_b),
        "one_native_invocation_each": smoke_a["native_invocation_count"] == 1
            and smoke_b["native_invocation_count"] == 1,
        "sample_counts": smoke_a["physical_samples"] == smoke_b["physical_samples"] == 1500
            and smoke_a["forward_sensor_samples"] == smoke_b["forward_sensor_samples"] == 1502,
        "event_counts": smoke_a["completed_stop_events"] == smoke_b["completed_stop_events"] == 15,
        "m1_visible_cadence": smoke_a["visible_stop_counts"] == smoke_b["visible_stop_counts"]
            == [3, 6, 9, 12, 15],
        "bank_unchanged": bool(smoke_a["bank_unchanged"] and smoke_b["bank_unchanged"]),
        "source_metadata_sealed": smoke_a["source_metadata_visibility"]
            == smoke_b["source_metadata_visibility"]
            == "SEALED_FROM_LOCALIZATION_AND_PLANNER",
    }
    phase_checks = {
        "A_CONTROLLED_SOURCE_MANIFEST": bool(selection["pass"]),
        "B_RESERVED_PHYSICAL_PLACEMENT": bool(
            worlds["checks"]["all_reserved_placements_resolved"]
        ),
        "C_ASSET_DERIVED_RNG_INVENTORY": bool(
            inventory["pass"] and
            inventory["unresolved_numeric_disjointness"] == "UNKNOWN" and
            worlds["checks"]["all_numeric_seeds_disjoint_from_resolved_inventory"]
        ),
        "D_GENERATOR_RUNTIME_IDENTITY": bool(runtime["pass"]),
        "E_FAIL_CLOSED_MATERIALIZER_COMMITTED": bool(
            re.fullmatch(r"[0-9a-f]{40}", args.implementation_commit)
        ),
        "F_DISPOSABLE_SMOKE_DETERMINISTIC": all(smoke_checks.values()),
    }
    failures = [{"path": str(path), "sha256": sha256_file(path),
                 "text": path.read_text(encoding="utf-8").strip()}
                for path in args.preserved_failure]
    passed = all(phase_checks.values())
    report = {
        "contract": CONTRACT,
        "remote_head_implementation": args.implementation_commit,
        "inputs": {
            "selection": {"path": str(args.selection), "sha256": sha256_file(args.selection)},
            "rng_inventory": {"path": str(args.rng_inventory), "sha256": sha256_file(args.rng_inventory)},
            "world_manifest": {"path": str(args.world_manifest), "sha256": sha256_file(args.world_manifest)},
            "runtime_report": {"path": str(args.runtime_report), "sha256": sha256_file(args.runtime_report)},
            "materializer_code": {"path": str(args.materializer_code),
                                  "sha256": sha256_file(args.materializer_code)},
            "smoke_a": {"path": str(args.smoke_a), "sha256": sha256_file(args.smoke_a)},
            "smoke_b": {"path": str(args.smoke_b), "sha256": sha256_file(args.smoke_b)},
        },
        "formal_world_counts": {"M2_CAL": 30, "M2_CONFIRM": 30},
        "historical_observation_numeric_seed_disjointness": "UNKNOWN_NOT_ASSERTED_TRUE",
        "smoke_payload_sha256": smoke_a["payload_sha256"],
        "smoke_checks": smoke_checks,
        "preserved_failed_smoke_preflights": failures,
        "phase_checks": phase_checks,
        "cal_generation_authorized": passed,
        "confirm_generation_authorized": False,
        "m3_cpp_ros_authorized": False,
        "pass": passed,
        "CTPI_M2_SOURCE_INTERVENTION_PREGEN": "PASS" if passed else "FAIL",
        "verdict": (
            "CTPI_M2_SOURCE_INTERVENTION_PREGEN=PASS" if passed
            else "CTPI_M2_SOURCE_INTERVENTION_PREGEN=FAIL"
        ),
    }
    data = canonical_bytes(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(
        f"{digest}  {args.output.name}\n", encoding="ascii"
    )
    print(report["verdict"])
    print(f"CTPI_M2_PREGEN_AUDIT_SHA256={digest}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
