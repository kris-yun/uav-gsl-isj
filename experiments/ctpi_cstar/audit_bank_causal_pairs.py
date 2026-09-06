#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.frozen_bank import load_placement_manifest


def xyz_key(row: dict, ndigits: int = 9):
    return (
        row["house"], row["carrier_id"],
        round(row["x"], ndigits), round(row["y"], ndigits), round(row["z"], ndigits),
    )


def build_report(rows: list[dict]) -> dict:
    exact: dict[tuple, list[dict]] = defaultdict(list)
    region: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if row["split"] != "reserved":
            continue
        exact[xyz_key(row)].append(row)
        region[(row["house"], row["carrier_id"])].append(row)

    legal_groups = []
    for key, group in sorted(exact.items()):
        seeds = sorted({int(row["transport_seed"]) for row in group})
        members = sorted({int(row["member_id"]) for row in group})
        if len(group) >= 2 and len(seeds) >= 2:
            legal_groups.append({
                "house": key[0],
                "carrier_id": key[1],
                "source_xyz_m": [key[2], key[3], key[4]],
                "member_ids": members,
                "transport_seeds": seeds,
                "rows": len(group),
            })

    region_summary = []
    for (house, carrier), group in sorted(region.items()):
        unique_xyz = {
            (round(row["x"], 9), round(row["y"], 9), round(row["z"], 9))
            for row in group
        }
        region_summary.append({
            "house": house,
            "carrier_id": carrier,
            "rows": len(group),
            "member_ids": sorted({int(row["member_id"]) for row in group}),
            "unique_source_xyz": len(unique_xyz),
            "unique_transport_seeds": len({int(row["transport_seed"]) for row in group}),
        })

    return {
        "contract": "CSTAR_BANK_CAUSAL_PAIR_AUDIT_V1",
        "reserved_rows": sum(len(group) for group in region.values()),
        "exact_source_multi_transport_groups": legal_groups,
        "exact_source_groups_count": len(legal_groups),
        "legal_exact_source_transport_pairing_available": bool(legal_groups),
        "region_summary": region_summary,
        "hard_rule": (
            "An M1 exact-source nuisance-intervention pair requires identical source_xyz "
            "and at least two distinct transport_seed values. Same carrier_id with different "
            "source_xyz is a region-level source identity, not an exact-source transport intervention."
        ),
        "fallback_if_unavailable": (
            "Do not relabel different placements as the same exact source. Either train/evaluate a "
            "region-identity representation explicitly, or materialize a bounded offline dataset with "
            "the exact same source_xyz under independently seeded transport realizations."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--placement-manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    report = build_report(load_placement_manifest(args.placement_manifest))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report["legal_exact_source_transport_pairing_available"]:
        print("CSTAR_BANK_EXACT_SOURCE_TRANSPORT_PAIRS=AVAILABLE")
    else:
        print("CSTAR_BANK_EXACT_SOURCE_TRANSPORT_PAIRS=UNAVAILABLE")
    # This is an audit result, not a software failure. Always produce the report;
    # downstream gates decide whether controlled materialization is required.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
