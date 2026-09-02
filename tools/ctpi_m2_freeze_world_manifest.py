#!/usr/bin/env python3
"""Resolve selected carriers to reserved V3 placements and fresh RNG worlds."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT = "CTPI_M2_SOURCE_INTERVENTION_WORLD_MANIFEST_V1"
DOMAIN_PREFIX = "CTPI_M2_SOURCE_INTERVENTION_OBSERVATION_V1"
HOUSES = ("H01", "H02", "H03")
SETS = ("M2_CAL", "M2_CONFIRM")


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


def build(args: argparse.Namespace) -> dict[str, Any]:
    selection_hash = sha256_file(args.selection)
    placement_hash = sha256_file(args.placement_manifest)
    inventory_hash = sha256_file(args.rng_inventory)
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    placement = json.loads(args.placement_manifest.read_text(encoding="utf-8"))
    inventory = json.loads(args.rng_inventory.read_text(encoding="utf-8"))
    if selection.get("contract") != "CTPI_M2_SOURCE_SELECTION_V3" or not selection.get("pass"):
        raise RuntimeError("CTPI_WORLD_SELECTION_CONTRACT")
    if placement.get("contract") != "PF_DEI_V3_REGION_PLACEMENT_V1":
        raise RuntimeError("CTPI_WORLD_PLACEMENT_CONTRACT")
    if inventory.get("contract") != "CTPI_M2_LEGACY_RNG_INVENTORY_V1" or not inventory.get("pass"):
        raise RuntimeError("CTPI_WORLD_RNG_INVENTORY")

    reserved: dict[tuple[str, str, int], dict[str, Any]] = {}
    carriers_by_house: dict[str, set[str]] = {h: set() for h in HOUSES}
    for row in placement["rows"]:
        if row["split"] != "reserved":
            continue
        key = (str(row["house"]), str(row["carrier_id"]), int(row["member_id"]))
        if key in reserved:
            raise RuntimeError(f"CTPI_WORLD_DUPLICATE_RESERVED:{key}")
        reserved[key] = row
        carriers_by_house[key[0]].add(key[1])

    occupied = set(int(v) for v in inventory["all_resolved_numeric_seeds"])
    worlds: list[dict[str, Any]] = []
    selected_carriers: dict[str, set[str]] = {h: set() for h in HOUSES}
    for house in HOUSES:
        for set_name in SETS:
            records = selection["houses"][house]["sets"][set_name]["worlds"]
            if len(records) != 10:
                raise RuntimeError(f"CTPI_WORLD_SELECTION_COUNT:{house}:{set_name}")
            for item in records:
                carrier = str(item["controlled_carrier_id"])
                member = int(item["reserved_placement_member"])
                row = reserved.get((house, carrier, member))
                if row is None:
                    raise RuntimeError(f"CTPI_WORLD_RESERVED_PLACEMENT_MISSING:{house}:{carrier}:{member}")
                route = int(item["route_index"])
                domain = f"{DOMAIN_PREFIX}/{set_name}/{house}/{carrier}/route{route:02d}/U{member}"
                seed, preimage, retry = derive_seed(domain, occupied)
                selected_carriers[house].add(carrier)
                worlds.append({
                    "world_id": f"{set_name}_{house}_{int(item['ordinal']):02d}",
                    "set": set_name, "house": house, "ordinal": int(item["ordinal"]),
                    "controlled_carrier_id": carrier,
                    "carrier_region_descriptor": {
                        "center_x": float(item["region_descriptor_center_x"]),
                        "center_y": float(item["region_descriptor_center_y"]),
                        "semantics": "REGION_DESCRIPTOR_ONLY_NOT_GENERATOR_XY",
                    },
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
                    "expected_k_levels": selection["houses"][house]["sets"][set_name]["expected_k_levels"],
                })

    # Disposable smoke is a carrier outside both formal source sets.
    smoke_carrier = sorted(carriers_by_house["H01"] - selected_carriers["H01"])[0]
    smoke_member = 0
    smoke_row = reserved[("H01", smoke_carrier, smoke_member)]
    smoke_domain = f"{DOMAIN_PREFIX}/SMOKE/H01/{smoke_carrier}/route00/U{smoke_member}"
    smoke_seed, smoke_preimage, smoke_retry = derive_seed(smoke_domain, occupied)
    smoke = {
        "world_id": "SMOKE_H01_DISPOSABLE_00", "set": "SMOKE", "house": "H01",
        "ordinal": 0, "controlled_carrier_id": smoke_carrier, "route_index": 0,
        "reserved_placement_member": smoke_member,
        "reserved_placement_quantile": float(smoke_row["placement_quantile"]),
        "reserved_horizontal_index": int(smoke_row["horizontal_index"]),
        "reserved_height_index": int(smoke_row["height_index"]),
        "source_xyz_m": [float(smoke_row["x"]), float(smoke_row["y"]), float(smoke_row["z"])],
        "source_xyz_semantics": "EXACT_PF_DEI_V3_RESERVED_PLACEMENT_NOT_QUADTREE_CENTER",
        "placement_row_transport_seed_provenance_only": int(smoke_row["transport_seed"]),
        "observation_rng_domain": smoke_domain,
        "observation_transport_seed_uint32": smoke_seed,
        "seed_derivation_preimage": smoke_preimage,
        "seed_derivation_retry": smoke_retry,
        "formal_dataset_exclusion": ["M2_CAL", "M2_CONFIRM"],
    }
    numeric = [int(row["observation_transport_seed_uint32"]) for row in worlds] + [smoke_seed]
    checks = {
        "formal_world_count_60": len(worlds) == 60,
        "cal_world_count_30": sum(row["set"] == "M2_CAL" for row in worlds) == 30,
        "confirm_world_count_30": sum(row["set"] == "M2_CONFIRM" for row in worlds) == 30,
        "all_numeric_seeds_unique": len(set(numeric)) == len(numeric),
        "all_numeric_seeds_disjoint_from_resolved_inventory": not bool(
            set(numeric) & set(inventory["all_resolved_numeric_seeds"])
        ),
        "all_reserved_placements_resolved": len(worlds) == 60,
        "smoke_excluded_from_formal_sets": smoke["controlled_carrier_id"] not in selected_carriers["H01"],
        "historical_unknown_numeric_disjointness_preserved":
            inventory["unresolved_numeric_disjointness"] == "UNKNOWN",
    }
    result = {
        "contract": CONTRACT,
        "selection_path": str(args.selection), "selection_sha256": selection_hash,
        "selector_code_path": str(args.selector_code),
        "selector_code_sha256": sha256_file(args.selector_code),
        "placement_manifest_path": str(args.placement_manifest),
        "placement_manifest_sha256": placement_hash,
        "rng_inventory_path": str(args.rng_inventory), "rng_inventory_sha256": inventory_hash,
        "formal_worlds": worlds, "disposable_smoke_world": smoke,
        "numeric_disjointness_from_unknown_historical_worlds": "UNKNOWN",
        "domain_disjointness_from_historical_worlds": True,
        "checks": checks, "pass": all(checks.values()),
    }
    result["verdict"] = (
        "CTPI_M2_SOURCE_INTERVENTION_WORLD_FREEZE=PASS" if result["pass"]
        else "CTPI_M2_SOURCE_INTERVENTION_WORLD_FREEZE=FAIL"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--selector-code", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--rng-inventory", type=Path, required=True)
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
    print(f"CTPI_M2_WORLD_MANIFEST_SHA256={digest}")
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
