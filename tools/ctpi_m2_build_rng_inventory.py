#!/usr/bin/env python3
"""Scan authoritative CTPI/PF-DEI assets into a canonical RNG inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT = "CTPI_M2_LEGACY_RNG_INVENTORY_V1"
PLACEMENT_CONTRACT = "PF_DEI_V3_REGION_PLACEMENT_V1"
HOUSES = ("H01", "H02", "H03")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build(args: argparse.Namespace) -> dict[str, Any]:
    placement_hash = sha256_file(args.placement_manifest)
    placement = json.loads(args.placement_manifest.read_text(encoding="utf-8"))
    if placement.get("contract") != PLACEMENT_CONTRACT:
        raise RuntimeError("CTPI_RNG_PLACEMENT_CONTRACT")
    rows = placement.get("rows")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("CTPI_RNG_PLACEMENT_ROWS")

    by_split: dict[str, set[int]] = {"train": set(), "reserved": set()}
    for row in rows:
        split = str(row.get("split"))
        if split not in by_split:
            raise RuntimeError(f"CTPI_RNG_UNKNOWN_SPLIT:{split}")
        by_split[split].add(int(row["transport_seed"]))

    scanned: list[dict[str, Any]] = [{
        "role": "V3_PLACEMENT_SOURCE_CONTRACT",
        "path": str(args.placement_manifest),
        "sha256": placement_hash,
    }]
    bank_records: list[dict[str, Any]] = []
    historical_unknown: list[dict[str, Any]] = []
    for house in HOUSES:
        path = args.bank_root / house / "bank_summary.json"
        digest = sha256_file(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        keys = sorted(int(v) for v in data.get("prediction_transport_keys", []))
        if keys != sorted(by_split["train"]):
            raise RuntimeError(f"CTPI_RNG_BANK_TRAIN_KEYS:{house}:{keys}")
        if data.get("placement_manifest_sha256") != placement_hash:
            raise RuntimeError(f"CTPI_RNG_BANK_PLACEMENT_HASH:{house}")
        scanned.append({"role": f"FROZEN_PREDICTIVE_BANK_{house}",
                        "path": str(path), "sha256": digest})
        bank_records.append({
            "house": house,
            "rng_domain": data.get("prediction_rng_domain"),
            "numeric_seeds": keys,
            "bank_summary_sha256": digest,
        })
        historical_unknown.append({
            "house": house,
            "rng_domain": data.get("observation_rng_domain"),
            "numeric_seed": "UNKNOWN",
            "world_sha256": data.get("observation_realization_sha256"),
            "source_asset_sha256": digest,
            "numeric_disjointness_claim_permitted": False,
        })

    for role, path in (
        ("V3_FINAL_BANK_SUMMARY", args.final_bank_summary),
        ("OLD_ROUTE_STAGE1_MANIFEST", args.stage1_manifest),
        ("GADEN_RNG_HOOK_SOURCE", args.rng_hook_source),
        ("GADEN_MATHUTILS_SOURCE", args.mathutils_source),
    ):
        scanned.append({"role": role, "path": str(path), "sha256": sha256_file(path)})

    final_summary = json.loads(args.final_bank_summary.read_text(encoding="utf-8"))
    if final_summary.get("placement_manifest_sha256") != placement_hash:
        raise RuntimeError("CTPI_RNG_FINAL_BANK_PLACEMENT_HASH")
    math_text = args.mathutils_source.read_text(encoding="utf-8")
    hook_text = args.rng_hook_source.read_text(encoding="utf-8")
    if "static thread_local std::mt19937 engine" not in math_text:
        raise RuntimeError("CTPI_RNG_DEFAULT_ENGINE_SOURCE")
    if "gaden_initialize_random_engines" not in hook_text:
        raise RuntimeError("CTPI_RNG_HOOK_SOURCE")

    known = sorted(by_split["train"] | by_split["reserved"] | {5489})
    checks = {
        "placement_contract": True,
        "three_bank_summaries_scanned": len(bank_records) == 3,
        "bank_train_keys_match_asset_rows": True,
        "train_reserved_numeric_disjoint": not bool(by_split["train"] & by_split["reserved"]),
        "historical_unknown_preserved_as_unknown": all(
            row["numeric_seed"] == "UNKNOWN" and
            not row["numeric_disjointness_claim_permitted"]
            for row in historical_unknown
        ),
        "fallback_default_seed_source_verified": True,
    }
    result = {
        "contract": CONTRACT,
        "scanner_mode": "ASSET_DERIVED_EXPLICIT_RNG_FIELDS_ONLY",
        "scanned_assets": scanned,
        "predictive_members": bank_records,
        "prospective_reserved_members": {
            "rng_domain": f"{PLACEMENT_CONTRACT}/reserved",
            "numeric_seeds": sorted(by_split["reserved"]),
            "source_asset_sha256": placement_hash,
        },
        "historical_observation_worlds": historical_unknown,
        "fallback_default_generator": {
            "rng_domain": "GADEN_STD_MT19937_NO_EXPLICIT_HOOK",
            "numeric_seed": 5489,
            "mathutils_source_sha256": sha256_file(args.mathutils_source),
        },
        "all_resolved_numeric_seeds": known,
        "unresolved_numeric_identity_count": len(historical_unknown),
        "unresolved_numeric_disjointness": "UNKNOWN",
        "checks": checks,
        "pass": all(checks.values()),
    }
    result["verdict"] = (
        "CTPI_M2_LEGACY_RNG_INVENTORY=PASS" if result["pass"]
        else "CTPI_M2_LEGACY_RNG_INVENTORY=FAIL"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--bank-root", type=Path, required=True)
    parser.add_argument("--final-bank-summary", type=Path, required=True)
    parser.add_argument("--stage1-manifest", type=Path, required=True)
    parser.add_argument("--rng-hook-source", type=Path, required=True)
    parser.add_argument("--mathutils-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args)
    data = canonical_bytes(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(
        f"{digest}  {args.output.name}\n", encoding="ascii"
    )
    print(result["verdict"])
    print(f"CTPI_M2_LEGACY_RNG_INVENTORY_SHA256={digest}")
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
