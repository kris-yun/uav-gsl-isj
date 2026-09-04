#!/usr/bin/env python3
"""Measure instantaneous GADEN peak offsets in frozen CPIR world files.

The diagnostic reads the real GADEN-generated stream banks, never a peak-field
summary.  It is diagnostic-only and is not an M3 pass criterion.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import struct
from pathlib import Path
from typing import Any

import numpy as np


MAGIC = b"PFV3STR1"
SOURCE_XY = {
    "H01": (-0.40, -2.90),
    "H02": (0.00, -1.00),
    "H03": (-0.45, 1.90),
}
CARRIER_RE = re.compile(r"^quadtree_(\d+)_(\d+)_(\d+)_(\d+)$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_cells(path: Path) -> list[dict[str, float | int]]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    cells = [{
        "stream": int(row["stream_ordinal"]),
        "native": int(row["native_cell_index"]),
        "x": float(row["x"]),
        "y": float(row["y"]),
    } for row in rows]
    if [int(row["stream"]) for row in cells] != list(range(len(cells))):
        raise ValueError("CTPI_PEAK_CELL_STREAM_ORDER")
    return cells


def carrier_rect(carrier_id: str) -> tuple[int, int, int, int]:
    match = CARRIER_RE.fullmatch(carrier_id)
    if match is None:
        raise ValueError(f"CTPI_PEAK_CARRIER_ID:{carrier_id}")
    return tuple(int(value) for value in match.groups())  # type: ignore[return-value]


def choose_true_carrier(rows: list[dict[str, Any]], house: str) -> str:
    source_x, source_y = SOURCE_XY[house]
    by_carrier: dict[str, list[tuple[float, float]]] = {}
    for row in rows:
        if row.get("house") == house and row.get("split") == "train":
            by_carrier.setdefault(str(row["carrier_id"]), []).append((float(row["x"]), float(row["y"])))
    if not by_carrier:
        raise ValueError(f"CTPI_PEAK_NO_PLACEMENTS:{house}")
    return min(by_carrier, key=lambda carrier: (
        np.mean([(x - source_x) ** 2 + (y - source_y) ** 2 for x, y in by_carrier[carrier]]),
        carrier,
    ))


def load_world(path: Path, cell_count: int) -> np.memmap:
    with path.open("rb") as source:
        magic = source.read(8)
        count_raw = source.read(4)
        if magic != MAGIC or len(count_raw) != 4:
            raise ValueError(f"CTPI_PEAK_WORLD_HEADER:{path}")
        count = struct.unpack("<I", count_raw)[0]
        lengths = np.fromfile(source, dtype="<u4", count=count)
    if count != cell_count or lengths.size != cell_count or not np.all(lengths == lengths[0]):
        raise ValueError(f"CTPI_PEAK_WORLD_RECTANGLE:{path}")
    time_count = int(lengths[0])
    expected = 12 + 4 * cell_count + 4 * cell_count * time_count
    if path.stat().st_size != expected:
        raise ValueError(f"CTPI_PEAK_WORLD_SIZE:{path}")
    return np.memmap(path, dtype="<f4", mode="r", offset=12 + 4 * cell_count,
                     shape=(cell_count, time_count), order="C")


def summarize_house(bank_root: Path, placement_rows: list[dict[str, Any]], house: str,
                    fixed_radius_m: float, time_bins: int) -> dict[str, Any]:
    root = bank_root / house
    summary = json.loads((root / "bank_summary.json").read_text(encoding="utf-8"))
    cells = load_cells(root / "cell_manifest.csv")
    x = np.asarray([row["x"] for row in cells], dtype=np.float64)
    y = np.asarray([row["y"] for row in cells], dtype=np.float64)
    native = np.asarray([row["native"] for row in cells], dtype=np.int64)
    dx_values = np.diff(np.unique(np.round(x, 9)))
    dy_values = np.diff(np.unique(np.round(y, 9)))
    spacing = np.concatenate([dx_values[dx_values > 1e-8], dy_values[dy_values > 1e-8]])
    cell_size = float(np.min(spacing))
    carrier = choose_true_carrier(placement_rows, house)
    oi, oj, sx, sy = carrier_rect(carrier)
    house_carriers = [str(row["carrier_id"]) for row in placement_rows
                      if row.get("house") == house and row.get("split") == "train"]
    nx = max(carrier_rect(value)[0] + carrier_rect(value)[2] for value in house_carriers)

    member_results: list[dict[str, Any]] = []
    all_distance: list[np.ndarray] = []
    all_inside: list[np.ndarray] = []
    time_bin_rows: list[dict[str, Any]] = []
    used_hashes: dict[str, str] = {}
    for member in range(int(summary["member_count"])):
        candidates = [row for row in placement_rows
                      if row.get("house") == house and row.get("split") == "train"
                      and str(row["carrier_id"]) == carrier and int(row["member_id"]) == member]
        if len(candidates) != 1:
            raise ValueError(f"CTPI_PEAK_PLACEMENT_ROW:{house}:{carrier}:{member}")
        placement = candidates[0]
        world_path = root / "worlds" / f"member_{member:02d}" / f"{carrier}.bin"
        world = load_world(world_path, len(cells))
        peak_stream = np.asarray(np.argmax(world, axis=0), dtype=np.int64)
        peak_value = np.asarray(world[peak_stream, np.arange(world.shape[1])], dtype=np.float64)
        source_x, source_y = float(placement["x"]), float(placement["y"])
        distance = np.hypot(x[peak_stream] - source_x, y[peak_stream] - source_y)
        peak_native = native[peak_stream]
        peak_i = peak_native % nx
        peak_j = peak_native // nx
        inside = (peak_i >= oi) & (peak_i < oi + sx) & (peak_j >= oj) & (peak_j < oj + sy)
        all_distance.append(distance)
        all_inside.append(inside)
        used_hashes[world_path.relative_to(bank_root).as_posix()] = sha256_file(world_path)
        member_results.append({
            "member_id": member,
            "transport_seed": int(placement["transport_seed"]),
            "source_xyz": [source_x, source_y, float(placement["z"])],
            "snapshot_count": int(world.shape[1]),
            "fraction_peak_inside_true_carrier": float(np.mean(inside)),
            "fraction_peak_within_1_cell": float(np.mean(distance <= cell_size + 1e-12)),
            "fraction_peak_within_2_cells": float(np.mean(distance <= 2.0 * cell_size + 1e-12)),
            "fraction_peak_within_fixed_radius": float(np.mean(distance <= fixed_radius_m + 1e-12)),
            "distance_mean_m": float(np.mean(distance)),
            "distance_median_m": float(np.median(distance)),
            "distance_p90_m": float(np.quantile(distance, 0.9)),
            "peak_ppm_mean": float(np.mean(peak_value)),
            "peak_ppm_max": float(np.max(peak_value)),
        })
        edges = np.linspace(0, world.shape[1], time_bins + 1, dtype=int)
        for time_bin, (start, end) in enumerate(zip(edges[:-1], edges[1:])):
            time_bin_rows.append({
                "member_id": member,
                "transport_seed": int(placement["transport_seed"]),
                "time_bin": time_bin,
                "start_index": int(start),
                "end_index_exclusive": int(end),
                "distance_mean_m": float(np.mean(distance[start:end])),
                "fraction_inside": float(np.mean(inside[start:end])),
            })

    distance = np.concatenate(all_distance)
    inside = np.concatenate(all_inside)
    return {
        "house": house,
        "true_source_xy_scenario": list(SOURCE_XY[house]),
        "selected_true_carrier": carrier,
        "cell_size_m": cell_size,
        "fixed_radius_m": fixed_radius_m,
        "snapshot_count": int(distance.size),
        "fraction_peak_inside_true_carrier": float(np.mean(inside)),
        "fraction_peak_within_1_cell": float(np.mean(distance <= cell_size + 1e-12)),
        "fraction_peak_within_2_cells": float(np.mean(distance <= 2.0 * cell_size + 1e-12)),
        "fraction_peak_within_fixed_radius": float(np.mean(distance <= fixed_radius_m + 1e-12)),
        "distance_mean_m": float(np.mean(distance)),
        "distance_median_m": float(np.median(distance)),
        "distance_p90_m": float(np.quantile(distance, 0.9)),
        "signed_along_wind_offset": None,
        "signed_along_wind_status": "NOT_COMPUTED_NO_SNAPSHOT_ALIGNED_WIND_LEDGER",
        "members": member_results,
        "time_bins": time_bin_rows,
        "input_sha256": used_hashes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank-root", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--houses", nargs="+", choices=sorted(SOURCE_XY), default=sorted(SOURCE_XY))
    parser.add_argument("--fixed-radius-m", type=float, default=1.0)
    parser.add_argument("--time-bins", type=int, default=5)
    args = parser.parse_args()
    if args.fixed_radius_m <= 0.0 or args.time_bins < 1:
        parser.error("positive radius and time-bins required")
    placement = json.loads(args.placement_manifest.read_text(encoding="utf-8"))
    if placement.get("contract") != "PF_DEI_V3_REGION_PLACEMENT_V1":
        raise SystemExit("CTPI_PEAK_PLACEMENT_CONTRACT")
    report = {
        "contract": "CTPI_GADEN_INSTANTANEOUS_PEAK_OFFSET_DIAGNOSTIC_V1",
        "status": "DIAGNOSTIC_ONLY_NOT_M3_GATE",
        "placement_manifest_sha256": sha256_file(args.placement_manifest),
        "houses": [summarize_house(args.bank_root, placement["rows"], house,
                                    args.fixed_radius_m, args.time_bins)
                   for house in args.houses],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CTPI_GADEN_PEAK_DIAGNOSTIC=PASS:{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
