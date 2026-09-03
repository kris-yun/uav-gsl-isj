#!/usr/bin/env python3
"""Finalize TSDC pre-generation evidence before any formal fresh outcome."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

CONTRACT = "CTPI_M2_TSDC_PREGEN_AUDIT_V0"
EXPECTED_SELECTION_SHA256 = "0d4e6162863ca2a07bf93ef74f178b1d4ad5d058ab787345d291362fd8e9f431"
EXPECTED_PLACEMENT_SHA256 = "2dfe8bf70cc5dd191db8659cfc66ed9934927b69d0b6798b9a6b5062e1dd959f"
EXPECTED_FROZEN_MODULE_SHA256 = "854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path, contract: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("contract") != contract or not value.get("pass"):
        raise RuntimeError(f"TSDC_PREGEN_INPUT:{path}:{value.get('contract')}:{value.get('pass')}")
    return value


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--selection", type=Path, required=True)
    p.add_argument("--world-manifest", type=Path, required=True)
    p.add_argument("--runtime-report", type=Path, required=True)
    p.add_argument("--used-asset-registry", type=Path, required=True)
    p.add_argument("--frozen-module", type=Path, required=True)
    p.add_argument("--materializer-code", type=Path, required=True)
    p.add_argument("--smoke-a", type=Path, required=True)
    p.add_argument("--smoke-b", type=Path, required=True)
    p.add_argument("--implementation-commit", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    selection = load(args.selection, "CTPI_M2_TSDC_FRESH_SOURCE_SELECTION_V0")
    worlds = load(args.world_manifest, "CTPI_M2_TSDC_FRESH_WORLD_MANIFEST_V0")
    runtime = load(args.runtime_report, "CTPI_M2_GENERATOR_RUNTIME_IDENTITY_V1")
    smoke_a = load(args.smoke_a, "CTPI_M2_TSDC_ONE_WORLD_MATERIALIZER_V0")
    smoke_b = load(args.smoke_b, "CTPI_M2_TSDC_ONE_WORLD_MATERIALIZER_V0")
    registry = json.loads(args.used_asset_registry.read_text(encoding="utf-8"))
    if registry.get("contract") != "CTPI_M2_TSDC_USED_ASSET_REGISTRY_V0":
        raise RuntimeError("TSDC_PREGEN_REGISTRY")

    smoke_id = worlds["disposable_smoke_world"]["world_id"]
    smoke_checks = {
        "same_disposable_identity": smoke_a["world_id"] == smoke_b["world_id"] == smoke_id,
        "same_payload_sha256": smoke_a["payload_sha256"] == smoke_b["payload_sha256"],
        "one_native_invocation_each": smoke_a["native_invocation_count"] == 1 and smoke_b["native_invocation_count"] == 1,
        "sample_counts": smoke_a["physical_samples"] == smoke_b["physical_samples"] == 1500 and smoke_a["forward_sensor_samples"] == smoke_b["forward_sensor_samples"] == 1502,
        "event_counts": smoke_a["completed_stop_events"] == smoke_b["completed_stop_events"] == 15,
        "m1_visible_cadence": smoke_a["visible_stop_counts"] == smoke_b["visible_stop_counts"] == [3,6,9,12,15],
        "bank_unchanged": bool(smoke_a["bank_unchanged"] and smoke_b["bank_unchanged"]),
        "source_metadata_sealed": smoke_a["source_metadata_visibility"] == smoke_b["source_metadata_visibility"] == "SEALED_FROM_LOCALIZATION_AND_PLANNER",
        "tsdc_adapter": bool(smoke_a.get("tsdc_adapter") and smoke_b.get("tsdc_adapter")),
    }
    formal = worlds["formal_worlds"]
    phase_checks = {
        "selection_exact_sha": sha256_file(args.selection) == EXPECTED_SELECTION_SHA256,
        "selection_pass": bool(selection["pass"]),
        "placement_exact_sha": worlds["placement_manifest_sha256"] == EXPECTED_PLACEMENT_SHA256,
        "world_manifest_pass": bool(worlds["pass"]),
        "world_count_30": len(formal) == 30,
        "ten_per_house": all(sum(w["house"] == h for w in formal) == 10 for h in ("H01","H02","H03")),
        "new_rng_disjoint": bool(worlds["checks"]["all_numeric_seeds_disjoint_from_registry"]),
        "reserved_placements_resolved": bool(worlds["checks"]["all_reserved_placements_resolved"]),
        "runtime_identity": bool(runtime["pass"]),
        "frozen_module_exact_sha": sha256_file(args.frozen_module) == EXPECTED_FROZEN_MODULE_SHA256,
        "implementation_commit": bool(re.fullmatch(r"[0-9a-f]{40}", args.implementation_commit)),
        "smoke_deterministic": all(smoke_checks.values()),
    }
    passed = all(phase_checks.values())
    report = {
        "contract": CONTRACT,
        "implementation_commit": args.implementation_commit,
        "inputs": {
            "selection_sha256": sha256_file(args.selection),
            "world_manifest_sha256": sha256_file(args.world_manifest),
            "runtime_report_sha256": sha256_file(args.runtime_report),
            "used_asset_registry_sha256": sha256_file(args.used_asset_registry),
            "frozen_module_sha256": sha256_file(args.frozen_module),
            "materializer_code_sha256": sha256_file(args.materializer_code),
            "smoke_a_sha256": sha256_file(args.smoke_a),
            "smoke_b_sha256": sha256_file(args.smoke_b),
        },
        "formal_world_count": len(formal),
        "historical_unresolved_numeric_identity": registry.get("historical_unknown_numeric_identity_preserved"),
        "smoke_payload_sha256": smoke_a["payload_sha256"],
        "smoke_checks": smoke_checks,
        "phase_checks": phase_checks,
        "formal_generation_authorized": passed,
        "m3_cpp_ros_closed_loop_authorized": False,
        "pass": passed,
        "CTPI_M2_TSDC_PREGEN": "PASS" if passed else "FAIL",
        "verdict": "CTPI_M2_TSDC_PREGEN=PASS" if passed else "CTPI_M2_TSDC_PREGEN=FAIL",
    }
    data = canonical_bytes(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(f"{digest}  {args.output.name}\n", encoding="ascii")
    print(report["verdict"])
    print(f"CTPI_M2_TSDC_PREGEN_AUDIT_SHA256={digest}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
