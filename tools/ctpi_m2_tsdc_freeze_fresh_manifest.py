#!/usr/bin/env python3
"""Freeze the 30-world TSDC fresh-confirm manifest without reading outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT = "CTPI_M2_TSDC_FRESH_WORLD_MANIFEST_V0"
DOMAIN_PREFIX = "CTPI_M2_TSDC_FRESH_CONFIRM_OBSERVATION_V0"
HOUSES = ("H01", "H02", "H03")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def derive_seed(domain: str, occupied: set[int]) -> tuple[int, str, int]:
    retry = 0
    while True:
        preimage = f"{domain}|retry={retry}"
        seed = int.from_bytes(hashlib.sha256(preimage.encode("utf-8")).digest()[:4], "big")
        if seed != 0 and seed not in occupied:
            occupied.add(seed)
            return seed, preimage, retry
        retry += 1


def build(selection_path: Path, placement_path: Path, registry_path: Path) -> dict[str, Any]:
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    placement = json.loads(placement_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if selection.get("contract") != "CTPI_M2_TSDC_FRESH_SOURCE_SELECTION_V0" or not selection.get("pass"):
        raise RuntimeError("TSDC_FRESH_SELECTION_CONTRACT")
    if placement.get("contract") != "PF_DEI_V3_REGION_PLACEMENT_V1":
        raise RuntimeError("TSDC_PLACEMENT_CONTRACT")
    if registry.get("contract") != "CTPI_M2_TSDC_USED_ASSET_REGISTRY_V0":
        raise RuntimeError("TSDC_USED_ASSET_REGISTRY")

    reserved: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in placement["rows"]:
        if row.get("split") != "reserved":
            continue
        key = (str(row["house"]), str(row["carrier_id"]), int(row["member_id"]))
        if key in reserved:
            raise RuntimeError(f"TSDC_DUP_RESERVED:{key}")
        reserved[key] = row

    occupied = set(int(value) for value in registry["reserved_numeric_seeds"])
    used_carriers = {
        house: set(str(value) for value in registry["used_carriers_by_house"][house])
        for house in HOUSES
    }
    worlds: list[dict[str, Any]] = []
    for house in HOUSES:
        records = selection["houses"][house]["worlds"]
        if len(records) != 10:
            raise RuntimeError(f"TSDC_FRESH_COUNT:{house}")
        for item in records:
            carrier = str(item["controlled_carrier_id"])
            member = int(item["reserved_placement_member"])
            route = int(item["route_index"])
            if carrier in used_carriers[house]:
                raise RuntimeError(f"TSDC_FRESH_REUSES_CARRIER:{house}:{carrier}")
            row = reserved.get((house, carrier, member))
            if row is None:
                raise RuntimeError(f"TSDC_RESERVED_MISSING:{house}:{carrier}:{member}")
            domain = f"{DOMAIN_PREFIX}/{house}/{carrier}/route{route:02d}/U{member}"
            seed, preimage, retry = derive_seed(domain, occupied)
            worlds.append(
                {
                    "world_id": f"TSDC_FRESH_{house}_{int(item['ordinal']):02d}",
                    "set": "TSDC_FRESH_CONFIRM",
                    "house": house,
                    "ordinal": int(item["ordinal"]),
                    "controlled_carrier_id": carrier,
                    "route_index": route,
                    "reserved_placement_member": member,
                    "reserved_placement_quantile": float(row["placement_quantile"]),
                    "reserved_horizontal_index": int(row["horizontal_index"]),
                    "reserved_height_index": int(row["height_index"]),
                    "source_xyz_m": [float(row["x"]), float(row["y"]), float(row["z"])],
                    "source_xyz_semantics": "EXACT_PF_DEI_V3_RESERVED_PLACEMENT_NOT_QUADTREE_CENTER",
                    "placement_row_transport_seed_provenance_only": int(row["transport_seed"]),
                    "observation_rng_domain": domain,
                    "observation_transport_seed_uint32": seed,
                    "seed_derivation_preimage": preimage,
                    "seed_derivation_retry": retry,
                    "expected_k_levels": selection["houses"][house]["expected_k_levels"],
                }
            )

    numeric = [int(row["observation_transport_seed_uint32"]) for row in worlds]
    checks = {
        "world_count_30": len(worlds) == 30,
        "ten_per_house": all(sum(row["house"] == h for row in worlds) == 10 for h in HOUSES),
        "all_carriers_fresh": all(
            row["controlled_carrier_id"] not in used_carriers[row["house"]] for row in worlds
        ),
        "all_numeric_seeds_unique": len(set(numeric)) == 30,
        "all_numeric_seeds_disjoint_from_registry": not bool(
            set(numeric) & set(registry["reserved_numeric_seeds"])
        ),
        "all_reserved_placements_resolved": len(worlds) == 30,
        "domain_prefix_new": all(
            row["observation_rng_domain"].startswith(DOMAIN_PREFIX + "/") for row in worlds
        ),
    }
    result = {
        "contract": CONTRACT,
        "selection_sha256": sha256_file(selection_path),
        "placement_manifest_sha256": sha256_file(placement_path),
        "used_asset_registry_sha256": sha256_file(registry_path),
        "domain_prefix": DOMAIN_PREFIX,
        "predictive_bank_generation": False,
        "formal_worlds": worlds,
        "checks": checks,
        "pass": all(checks.values()),
    }
    result["verdict"] = (
        "CTPI_M2_TSDC_FRESH_WORLD_FREEZE=PASS"
        if result["pass"]
        else "CTPI_M2_TSDC_FRESH_WORLD_FREEZE=FAIL"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--used-asset-registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.selection, args.placement_manifest, args.used_asset_registry)
    data = canonical_bytes(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(
        f"{digest}  {args.output.name}\n", encoding="ascii"
    )
    print(result["verdict"])
    print(f"CTPI_M2_TSDC_FRESH_WORLD_MANIFEST_SHA256={digest}")
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
