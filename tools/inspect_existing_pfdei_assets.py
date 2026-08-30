#!/usr/bin/env python3
"""Read-only inventory of existing PF-DEI banks relevant to CTT placement U."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def placement_key(row: dict) -> tuple[str, str, str]:
    """Return the exact serialized 3-D placement used by the frozen manifest."""

    return tuple(format(float(row[name]), ".17g") for name in ("x", "y", "z"))


def duplicate_factorization_audit(rows: list[dict]) -> dict:
    """Measure whether the frozen diagonal member library can isolate U from K."""

    by_carrier: dict[str, list[dict]] = {}
    for row in rows:
        by_carrier.setdefault(row["carrier_id"], []).append(row)

    carrier_rows = []
    for carrier_id, carrier_members in sorted(by_carrier.items()):
        u_to_k: dict[tuple[str, str, str], set[str]] = {}
        k_to_u: dict[str, set[tuple[str, str, str]]] = {}
        pairs: set[tuple[tuple[str, str, str], str]] = set()
        for row in carrier_members:
            u_key = placement_key(row)
            k_key = str(row["transport_seed"])
            u_to_k.setdefault(u_key, set()).add(k_key)
            k_to_u.setdefault(k_key, set()).add(u_key)
            pairs.add((u_key, k_key))

        max_k_per_u = max(map(len, u_to_k.values()), default=0)
        max_u_per_k = max(map(len, k_to_u.values()), default=0)
        full_cross_pairs = len(u_to_k) * len(k_to_u)
        carrier_rows.append(
            {
                "carrier_id": carrier_id,
                "rows": len(carrier_members),
                "unique_u": len(u_to_k),
                "unique_k": len(k_to_u),
                "observed_u_k_pairs": len(pairs),
                "full_cross_pairs": full_cross_pairs,
                "pair_coverage": (
                    len(pairs) / full_cross_pairs if full_cross_pairs else 0.0
                ),
                "max_distinct_k_at_same_u": max_k_per_u,
                "max_distinct_u_at_same_k": max_u_per_k,
            }
        )

    def count_at_least(field: str, threshold: int) -> int:
        return sum(row[field] >= threshold for row in carrier_rows)

    return {
        "carriers": len(carrier_rows),
        "rows": len(rows),
        "carriers_with_same_u_at_least_2_k": count_at_least(
            "max_distinct_k_at_same_u", 2
        ),
        "carriers_with_same_u_at_least_3_k": count_at_least(
            "max_distinct_k_at_same_u", 3
        ),
        "carriers_with_same_u_at_least_4_k": count_at_least(
            "max_distinct_k_at_same_u", 4
        ),
        "carriers_with_same_k_at_least_2_u": count_at_least(
            "max_distinct_u_at_same_k", 2
        ),
        "fully_crossed_carriers": sum(
            row["observed_u_k_pairs"] == row["full_cross_pairs"]
            and row["unique_u"] > 1
            and row["unique_k"] > 1
            for row in carrier_rows
        ),
        "maximum_pair_coverage": max(
            (row["pair_coverage"] for row in carrier_rows), default=0.0
        ),
        "maximum_k_at_same_u": max(
            (row["max_distinct_k_at_same_u"] for row in carrier_rows), default=0
        ),
        "maximum_u_at_same_k": max(
            (row["max_distinct_u_at_same_k"] for row in carrier_rows), default=0
        ),
        "eligible_same_u_carriers": [
            row for row in carrier_rows if row["max_distinct_k_at_same_u"] >= 2
        ],
    }


def describe_npz(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as archive:
        return {
            key: {"shape": list(archive[key].shape), "dtype": str(archive[key].dtype)}
            for key in archive.files
        }


def main() -> int:
    paths = {
        "historical_view": Path(
            "/home/zyc/H01_HISTORICAL_10SEED_EXISTING_BANK_REPLAY_20260829/"
            "bank_views/H01_seed0_candidate_physical.npz"
        ),
        "final_summary": Path(
            "/home/zyc/PF_DEI_V3_FINAL_SIM_BANK_20260828_R1/bank_summary.json"
        ),
        "historical_summary": Path(
            "/home/zyc/PF_DEI_V3_HISTORICAL_BANK_20260828_R1/bank_summary.json"
        ),
        "placement_manifest": Path(
            "/home/zyc/PF_DEI_V3_STREAM_BUILD/src/"
            "frozen_region_placement_manifest.json"
        ),
    }
    placement = json.loads(paths["placement_manifest"].read_text())
    h01_rows = [row for row in placement["rows"] if row["house"] == "H01"]
    by_carrier: dict[str, list[dict]] = {}
    for row in h01_rows:
        by_carrier.setdefault(row["carrier_id"], []).append(row)
    example_id = next(
        carrier_id for carrier_id, rows in by_carrier.items()
        if max(int(row["horizontal_count"]) for row in rows) >= 4
    )
    report = {
        "placement_summary": {
            "contract": placement["contract"],
            "h01_rows": len(h01_rows),
            "h01_carriers": len(by_carrier),
            "horizontal_count_histogram": {
                str(count): sum(
                    1 for rows in by_carrier.values()
                    if int(rows[0]["horizontal_count"]) == count
                )
                for count in sorted({
                    int(rows[0]["horizontal_count"])
                    for rows in by_carrier.values()
                })
            },
            "example_carrier": example_id,
            "example_rows": sorted(
                by_carrier[example_id], key=lambda row: (
                    row["split"], int(row["member_id"]))
            ),
        },
        "historical_view": describe_npz(paths["historical_view"]),
        "final_summary": json.loads(paths["final_summary"].read_text()),
        "historical_summary": json.loads(paths["historical_summary"].read_text()),
        "u_k_factorization": {
            "train": duplicate_factorization_audit(
                [row for row in h01_rows if row["split"] == "train"]
            ),
            "reserved": duplicate_factorization_audit(
                [row for row in h01_rows if row["split"] == "reserved"]
            ),
            "all": duplicate_factorization_audit(h01_rows),
        },
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
