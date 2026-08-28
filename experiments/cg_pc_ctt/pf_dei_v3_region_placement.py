#!/usr/bin/env python3
"""Frozen PF-DEI V3 hierarchical region-placement selector.

The carrier remains the inference target.  This module only selects deterministic
native-GADEN nuisance placements from the geometry-only conditional distribution:
uniform over legal horizontal PMFS cells, then uniform over legal voxel heights
inside the selected horizontal cell.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

TRAIN_QUANTILES = tuple(i / 16.0 for i in (1, 3, 5, 7, 9, 11, 13, 15))
TRAIN_SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
RESERVED_QUANTILES = tuple(i / 16.0 for i in (2, 6, 10, 14))
RESERVED_SEEDS = (907, 1009, 1103, 1201)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_support(path: Path) -> dict[tuple[str, str], list[dict]]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            heights = tuple(sorted(float(x) for x in row["legal_heights_m"].split(";") if x))
            if not heights:
                raise ValueError(f"empty legal height support: {row['house']} {row['carrier_id']}")
            grouped[(row["house"], row["carrier_id"])].append({
                "grid_i": int(row["pmfs_grid_i"]),
                "grid_j": int(row["pmfs_grid_j"]),
                "x": float(row["pmfs_x"]),
                "y": float(row["pmfs_y"]),
                "heights": heights,
            })
    for cells in grouped.values():
        cells.sort(key=lambda c: (c["grid_i"], c["grid_j"]))
    return dict(grouped)


def select_placement(cells: list[dict], quantile: float) -> dict:
    if not cells or not (0.0 < quantile < 1.0):
        raise ValueError("cells must be non-empty and quantile must be in (0,1)")
    n = len(cells)
    # Horizontal mass is exactly 1/n.  The residual quantile then indexes the
    # uniform height distribution of that cell.  This avoids voxel-count bias.
    scaled = quantile * n
    cell_index = min(int(scaled), n - 1)
    within = scaled - cell_index
    heights = cells[cell_index]["heights"]
    height_index = min(int(within * len(heights)), len(heights) - 1)
    cell = cells[cell_index]
    return {
        "pmfs_grid_i": cell["grid_i"],
        "pmfs_grid_j": cell["grid_j"],
        "x": cell["x"], "y": cell["y"], "z": heights[height_index],
        "horizontal_index": cell_index,
        "horizontal_count": n,
        "height_index": height_index,
        "height_count": len(heights),
    }


def build_manifest(support_path: Path) -> dict:
    support = read_support(support_path)
    rows = []
    for (house, carrier_id), cells in sorted(support.items()):
        for split, quantiles, seeds in (
            ("train", TRAIN_QUANTILES, TRAIN_SEEDS),
            ("reserved", RESERVED_QUANTILES, RESERVED_SEEDS),
        ):
            for member_id, (u, seed) in enumerate(zip(quantiles, seeds)):
                rows.append({
                    "house": house, "carrier_id": carrier_id, "split": split,
                    "member_id": member_id, "placement_quantile": u,
                    "transport_seed": seed, **select_placement(cells, u),
                })
    return {
        "contract": "PF_DEI_V3_REGION_PLACEMENT_V1",
        "source_support_sha256": sha256_file(support_path),
        "carrier_count": len(support),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("support", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = build_manifest(args.support)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PF_DEI_V3_REGION_PLACEMENT=PASS carriers={payload['carrier_count']} rows={len(payload['rows'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
