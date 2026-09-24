#!/usr/bin/env python3
"""Prepare the frozen arbitrary-source and probe bank for Bi-Green Gate 1A.

This script is read-only with respect to frozen evidence. It expands the
House02 PMFS quadtree candidate manifest onto the native 0.30 m PMFS source
support, filters occupied source cells using the frozen 3-D occupancy grid, and
reconstructs the already-frozen M4 probe contract correctly: points_xy are
coordinates on the 2x2 pooled grid, not raw 83x119 grid coordinates.

No plume concentration or source-rank result is read while constructing the
source/probe bank.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

TRUTH = np.array([-4.342730045, 2.899120331, 0.20], dtype=np.float64)
TRUTH_PMFS_IJ = (3, 34)
PMFS_CELL = 0.30
GADEN_CELL_EXPECTED = 0.10
PROBE_POOL = 2


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_occ(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    headers: dict[str, list[float]] = {}
    data_start = 0
    for i, line in enumerate(lines):
        if not line.startswith("#"):
            data_start = i
            break
        toks = line[1:].split()
        if toks:
            headers[toks[0]] = [float(x) for x in toks[1:]]
    nx, ny, nz = map(int, headers["num_cells"])
    values = np.fromiter(
        (int(x) for line in lines[data_start:] if line.strip() != ";"
         for x in line.split()),
        dtype=np.int8,
    )
    expected = nx * ny * nz
    if values.size != expected:
        raise ValueError(f"occupancy values {values.size} != {expected}")
    return headers, values.reshape((nz, nx, ny))


def fine_index(x: float, minimum: float, cell: float) -> int:
    return int(np.floor((x - minimum) / cell))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-manifest", type=Path, required=True)
    ap.add_argument("--occupancy", type=Path, required=True)
    ap.add_argument("--probe-json", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    headers, occ = read_occ(args.occupancy)
    nx, ny, nz = map(int, headers["num_cells"])
    env_min = np.asarray(headers["env_min(m)"], dtype=np.float64)
    cell = float(headers["cell_size(m)"][0])
    if abs(cell - GADEN_CELL_EXPECTED) > 1e-9:
        raise ValueError(f"unexpected GADEN cell size {cell}")

    z_index = fine_index(float(TRUTH[2]), float(env_min[2]), cell)
    if not 0 <= z_index < nz:
        raise ValueError("source z outside occupancy grid")

    with args.candidate_manifest.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 143:
        raise ValueError(f"candidate manifest too small: {len(rows)}")

    base_x = float(env_min[0]) + PMFS_CELL / 2
    base_y = float(env_min[1]) + PMFS_CELL / 2

    support_to_parents: dict[tuple[int, int], list[str]] = {}
    for r in rows:
        oi, oj = int(r["origin_i"]), int(r["origin_j"])
        si, sj = int(r["size_i"]), int(r["size_j"])
        expected_cx = base_x + (oi + (si - 1) / 2) * PMFS_CELL
        expected_cy = base_y + (oj + (sj - 1) / 2) * PMFS_CELL
        if abs(expected_cx - float(r["center_x"])) > 1e-4:
            raise ValueError(f"x-center drift for {r['candidate_id']}")
        if abs(expected_cy - float(r["center_y"])) > 1e-4:
            raise ValueError(f"y-center drift for {r['candidate_id']}")
        for i in range(oi, oi + si):
            for j in range(oj, oj + sj):
                support_to_parents.setdefault((i, j), []).append(r["candidate_id"])

    records = []
    rejected = []
    for (i, j), parents in sorted(support_to_parents.items()):
        x = base_x + i * PMFS_CELL
        y = base_y + j * PMFS_CELL
        ix = fine_index(x, float(env_min[0]), cell)
        iy = fine_index(y, float(env_min[1]), cell)
        if not (0 <= ix < nx and 0 <= iy < ny):
            rejected.append((i, j, "out_of_bounds"))
            continue
        state = int(occ[z_index, ix, iy])
        if state != 0:
            rejected.append((i, j, f"state_{state}"))
            continue
        records.append({
            "source_id": f"pmfs_{i}_{j}",
            "pmfs_i": i,
            "pmfs_j": j,
            "x_m": x,
            "y_m": y,
            "z_m": float(TRUTH[2]),
            "gaden_ix": ix,
            "gaden_iy": iy,
            "gaden_iz": z_index,
            "parent_leaf_count": len(parents),
            "parent_leaf_ids": ";".join(sorted(parents)),
        })

    if len(records) < 143:
        raise ValueError(f"free support too small after occupancy filter: {len(records)}")

    truth = next((r for r in records
                  if (r["pmfs_i"], r["pmfs_j"]) == TRUTH_PMFS_IJ), None)
    if truth is None:
        raise ValueError("exact S2 truth support cell (3,34) is missing")
    if np.linalg.norm(np.array([truth["x_m"], truth["y_m"], truth["z_m"]]) - TRUTH) > 1e-6:
        raise ValueError("truth support coordinate mismatch")

    bank_path = args.out / "source_bank.tsv"
    with bank_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(records[0].keys())
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(records)

    probe = json.loads(args.probe_json.read_text(encoding="utf-8"))
    points = probe.get("points_xy")
    if not isinstance(points, list) or len(points) != 30:
        raise ValueError("expected frozen 30-point pooled probe set")
    if len({tuple(map(int, p)) for p in points}) != 30:
        raise ValueError("pooled probe points are not unique")

    # c05_sparse_rank_diagnostic.py selects points AFTER 2x2 pooling:
    # x_s2_w2[0,4] is the max-pooled occupancy mask and targets are avg-pooled.
    # Therefore every (px,py) denotes a 2x2 native block, not a raw grid cell.
    probe_blocks = []
    pooled_nx = (nx + PROBE_POOL - 1) // PROBE_POOL
    pooled_ny = (ny + PROBE_POOL - 1) // PROBE_POOL
    for px, py in points:
        px, py = int(px), int(py)
        if not (0 <= px < pooled_nx and 0 <= py < pooled_ny):
            raise ValueError(f"pooled probe outside grid: {(px, py)}")
        x0, x1 = px * PROBE_POOL, min((px + 1) * PROBE_POOL, nx)
        y0, y1 = py * PROBE_POOL, min((py + 1) * PROBE_POOL, ny)
        block = occ[z_index, x0:x1, y0:y1]
        if block.size == 0 or np.any(block != 0):
            raise ValueError(f"pooled probe block not all-free: {(px, py)}")
        xs = [float(env_min[0]) + (ix + 0.5) * cell for ix in range(x0, x1)]
        ys = [float(env_min[1]) + (iy + 0.5) * cell for iy in range(y0, y1)]
        probe_blocks.append({
            "pool_x": px,
            "pool_y": py,
            "native_x0": x0,
            "native_x1_exclusive": x1,
            "native_y0": y0,
            "native_y1_exclusive": y1,
            "native_cell_count": int((x1 - x0) * (y1 - y0)),
            "center_x_m": float(np.mean(xs)),
            "center_y_m": float(np.mean(ys)),
            "z_m": float(TRUTH[2]),
        })

    contract = {
        "mode": "BIGREEN_GATE1A_EXACT_FORWARD_ORACLE",
        "candidate_manifest": str(args.candidate_manifest),
        "candidate_manifest_sha256": sha256(args.candidate_manifest),
        "occupancy": str(args.occupancy),
        "occupancy_sha256": sha256(args.occupancy),
        "probe_json": str(args.probe_json),
        "probe_json_sha256": sha256(args.probe_json),
        "manifest_leaf_count": len(rows),
        "deduplicated_support_count_before_occupancy": len(support_to_parents),
        "free_source_count": len(records),
        "rejected_support_count": len(rejected),
        "pmfs_source_cell_m": PMFS_CELL,
        "gaden_cell_m": cell,
        "truth_xyz_m": TRUTH.tolist(),
        "truth_pmfs_ij": list(TRUTH_PMFS_IJ),
        "truth_source_id": truth["source_id"],
        "probe_count": len(probe_blocks),
        "probe_operator": {
            "type": "avg_pool_2x2_then_sample",
            "kernel": 2,
            "stride": 2,
            "ceil_mode": True,
            "source_contract": "c05_sparse_rank_diagnostic.py",
        },
        "probe_points": probe_blocks,
        "target_cells": ["S2_W2_A", "S2_W2_B"],
        "target_seeds": [2026092301, 2026092302],
        "prediction_seeds": [2026092401, 2026092402],
        "iteration_indices": [100, 150, 200, 250, 300, 350, 400, 450, 500, 550],
        "observation_count_per_target": 300,
        "primary_score": "raw_ppm_normalized_sse",
        "gate": {
            "min_free_sources": 143,
            "mean_prediction_truth_rank_max": 3,
            "per_seed_truth_rank_max": 10,
        },
    }
    (args.out / "gate1a_contract.json").write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "leaf_candidates": len(rows),
        "support_before_occupancy": len(support_to_parents),
        "free_sources": len(records),
        "truth_source_id": truth["source_id"],
        "probe_count": len(probe_blocks),
        "probe_coordinate_space": "2x2_pooled_grid",
        "contract": str(args.out / "gate1a_contract.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
