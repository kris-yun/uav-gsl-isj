#!/usr/bin/env python3
"""Truth-blind V3 carrier-region to native GADEN 3-D support audit.

This is an engineering/provenance tool only.  It reconstructs the exact
2-D free-cell partition used by persistent PMFS carriers and maps each native
cell centre to the authoritative GADEN voxel column.  It never reads source
truth or gas values and never treats the carrier centroid as a source point.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_pmfs(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    req = {"grid_i", "grid_j", "x", "y", "occupancy"}
    if not rows or not req.issubset(rows[0]):
        raise ValueError(f"{path}: missing PMFS geometry columns")
    cells = {(int(r["grid_i"]), int(r["grid_j"])): r for r in rows}
    if len(cells) != len(rows):
        raise ValueError(f"{path}: duplicate grid cell")
    return cells


def read_gaden(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 5:
        raise ValueError(f"{path}: short occupancy file")
    env_min = tuple(float(x) for x in lines[0].split()[1:])
    dims = tuple(int(x) for x in lines[2].split()[1:])
    cell = float(lines[3].split()[1])
    vals = []
    for line in lines[4:]:
        if line.strip() == ";" or not line.strip():
            continue
        vals.extend(int(x) for x in line.split())
    expected = dims[0] * dims[1] * dims[2]
    if len(vals) != expected:
        raise ValueError(f"{path}: occupancy count {len(vals)} != {expected}")
    # Native Environment::WriteToFile order is z, x, y.
    occ = [[[0] * dims[1] for _ in range(dims[0])] for _ in range(dims[2])]
    k = 0
    for z in range(dims[2]):
        for x in range(dims[0]):
            for y in range(dims[1]):
                occ[z][x][y] = vals[k]
                k += 1
    return env_min, dims, cell, occ


def gaden_index(coord: float, env_min: float, cell: float, n: int) -> int:
    # Source-proven map transform: a PMFS 0.3 m cell centre is aligned to a
    # GADEN voxel centre; reject rather than silently nearest-neighbouring.
    u = (coord - (env_min + 0.5 * cell)) / cell
    idx = int(round(u))
    # PMFS exports centres as float32; retain the exact lattice identity while
    # allowing the observed <=4e-6 coordinate serialization error.
    if abs(u - idx) > 1e-4 or idx < 0 or idx >= n:
        raise ValueError(f"coordinate {coord} is not an exact GADEN centre (u={u})")
    return idx


def carriers(cells):
    width = max(i for i, _ in cells) + 1
    height = max(j for _, j in cells) + 1
    out = []
    for ox in range(0, width, 2):
        for oy in range(0, height, 2):
            sx, sy = min(2, width - ox), min(2, height - oy)
            free = [
                (i, j, cells[(i, j)])
                for i in range(ox, ox + sx)
                for j in range(oy, oy + sy)
                if cells[(i, j)]["occupancy"] == "Free"
            ]
            if free:
                out.append((len(out), f"quadtree_{ox}_{oy}_{sx}_{sy}",
                            (ox, oy, sx, sy), free))
    if sum(len(x[3]) for x in out) != sum(r["occupancy"] == "Free" for r in cells.values()):
        raise ValueError("carrier partition does not cover PMFS free cells exactly once")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pmfs", nargs=3, metavar=("H01", "H02", "H03"), type=Path, required=True)
    ap.add_argument("--gaden", nargs=3, metavar=("H01", "H02", "H03"), type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    houses = ("H01", "H02", "H03")
    a.out.mkdir(parents=True, exist_ok=True)
    all_rows = []
    summary = {"contract": "PF_DEI_V3_REGION_3D_SUPPORT_AUDIT", "truth_used": False,
               "centroid_used_for_placement": False, "houses": {}, "inputs": {}}
    for house, pmfs, gpath in zip(houses, a.pmfs, a.gaden):
        cells = read_pmfs(pmfs)
        env_min, dims, cell, occ = read_gaden(gpath)
        summary["inputs"][house] = {"pmfs": str(pmfs), "pmfs_sha256": sha256(pmfs),
                                     "gaden": str(gpath), "gaden_sha256": sha256(gpath),
                                     "gaden_env_min": env_min, "gaden_dims": dims,
                                     "gaden_cell_size": cell}
        cs = carriers(cells)
        free_total = sum(len(c[3]) for c in cs)
        legal_carriers = 0
        legal_cells = 0
        centroid_invalid = 0
        for idx, cid, rect, free in cs:
            legal_for_carrier = []
            for i, j, r in free:
                x, y = float(r["x"]), float(r["y"])
                gx = gaden_index(x, env_min[0], cell, dims[0])
                gy = gaden_index(y, env_min[1], cell, dims[1])
                zs = [env_min[2] + (z + 0.5) * cell for z in range(dims[2]) if occ[z][gx][gy] == 0]
                if zs:
                    legal_cells += 1
                    legal_for_carrier.append((i, j, x, y, gx, gy, zs))
                all_rows.append({"house": house, "carrier_index": idx, "carrier_id": cid,
                                 "origin_i": rect[0], "origin_j": rect[1], "size_i": rect[2], "size_j": rect[3],
                                 "pmfs_grid_i": i, "pmfs_grid_j": j, "pmfs_x": f"{x:.17g}", "pmfs_y": f"{y:.17g}",
                                 "gaden_x_index": gx, "gaden_y_index": gy, "legal_height_count": len(zs),
                                 "legal_heights_m": ";".join(f"{z:.17g}" for z in zs), "placement_weight": ""})
            if legal_for_carrier:
                legal_carriers += 1
            # The representative is metadata only; calculate its validity as a
            # diagnostic and never use it to create support.
            cx = sum(float(r["x"]) for _, _, r in free) / len(free)
            cy = sum(float(r["y"]) for _, _, r in free) / len(free)
            try:
                cgx = gaden_index(cx, env_min[0], cell, dims[0]); cgy = gaden_index(cy, env_min[1], cell, dims[1])
                if not any(occ[z][cgx][cgy] == 0 for z in range(dims[2])):
                    centroid_invalid += 1
            except ValueError:
                centroid_invalid += 1
        summary["houses"][house] = {"carrier_count": len(cs), "free_cell_count": free_total,
            "legal_carrier_count": legal_carriers, "empty_region_count": len(cs)-legal_carriers,
            "legal_free_cell_count": legal_cells, "centroid_invalid_diagnostic_count": centroid_invalid}
    out_csv = a.out / "source_region_3d_support_manifest.csv"
    fields = list(all_rows[0])
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(all_rows)
    summary["support_manifest"] = str(out_csv)
    summary["support_manifest_sha256"] = sha256(out_csv)
    (a.out / "region_support_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if any(v["empty_region_count"] for v in summary["houses"].values()):
        print("PF_DEI_REGION_3D_SUPPORT_NO_GO")
        return 2
    print("PF_DEI_REGION_3D_SUPPORT=PASS")


if __name__ == "__main__":
    main()
