#!/usr/bin/env python3
"""Independent reconstruction of E1 FPS and voxel validity from geometry."""

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

BASE = Path("/home/zyc")
SCENARIOS = Path("/mnt/hgfs/workspace/GADEN_files/scenarios")
EXPORT = BASE / "rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4"
IDS = {"House01": "H01_air_seed0", "House02": "H02_seed0", "House03": "H03_seed0"}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def table(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def read_occ(path):
    lines = path.read_text().splitlines()
    header = {}
    payload = []
    for line in lines:
        if line.startswith("#"):
            key, *values = line[1:].split()
            header[key] = [float(v) for v in values]
        elif line.strip() != ";":
            payload.extend(int(v) for v in line.split())
    nx, ny, nz = [int(v) for v in header["num_cells"]]
    assert len(payload) == nx * ny * nz
    return header, np.asarray(payload, dtype=np.int8).reshape(nz, nx, ny)


def choose_fps(candidates, count):
    # (grid_i, grid_j, integer_x, integer_y). No implementation imported from
    # the constructor; all integer distances are recomputed here.
    n = len(candidates)
    sx = sum(c[2] for c in candidates)
    sy = sum(c[3] for c in candidates)
    first = min(range(n), key=lambda k: ((candidates[k][2] * n - sx) ** 2 +
                                         (candidates[k][3] * n - sy) ** 2,
                                         candidates[k][0], candidates[k][1]))
    selected = [first]
    while len(selected) < count:
        def key(k):
            near = min((candidates[k][2] - candidates[q][2]) ** 2 +
                       (candidates[k][3] - candidates[q][3]) ** 2 for q in selected)
            return (-near, candidates[k][0], candidates[k][1])
        selected.append(min((k for k in range(n) if k not in selected), key=key))
    return [candidates[k][:2] for k in selected]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--e0-inventory", type=Path, required=True)
    args = parser.parse_args()
    probes = table(args.out / "E1_HOUSE_PROBE_CONTRACTS.tsv")
    sources = table(args.out / "E1_HOUSE_SOURCE_PANELS.tsv")
    assert len(probes) == 90 and len(sources) == 18
    counts = {}
    for house in IDS:
        header, occ = read_occ(SCENARIOS / house / "OccupancyGrid3D.csv")
        xmin, ymin, zmin = header["env_min(m)"]
        cell = header["cell_size(m)"][0]
        nav_root = EXPORT / IDS[house] / "off/geometry_export"
        meta = json.loads((nav_root / "pruned_meta.json").read_text())
        nav = np.fromfile(nav_root / "pruned_occupancy.bin", dtype=np.uint8).reshape(meta["height"], meta["width"]).T == 1
        iz = math.floor((.2 - zmin) / cell)
        assert 0 <= iz < occ.shape[0]
        def nav_ok(x, y):
            i = math.floor((x - meta["origin_x"]) / meta["resolution"])
            j = math.floor((y - meta["origin_y"]) / meta["resolution"])
            return 0 <= i < nav.shape[0] and 0 <= j < nav.shape[1] and nav[i, j]
        candidate_probes = []
        for i in range((occ.shape[1] + 1) // 2):
            for j in range((occ.shape[2] + 1) // 2):
                x0, x1 = 2 * i, min(2 * i + 2, occ.shape[1])
                y0, y1 = 2 * j, min(2 * j + 2, occ.shape[2])
                if np.any(occ[iz, x0:x1, y0:y1] != 0):
                    continue
                if all(nav_ok(xmin + (ix + .5) * cell, ymin + (iy + .5) * cell)
                       for ix in range(x0, x1) for iy in range(y0, y1)):
                    candidate_probes.append((i, j, x0 + x1, y0 + y1))
        expected_probes = choose_fps(candidate_probes, 30)
        observed_probes = [(int(r["pool_i"]), int(r["pool_j"])) for r in probes if r["house"] == house]
        assert observed_probes == expected_probes, (house, observed_probes, expected_probes)
        for row in (r for r in probes if r["house"] == house):
            x0, x1 = int(row["native_x0"]), int(row["native_x1_exclusive"])
            y0, y1 = int(row["native_y0"]), int(row["native_y1_exclusive"])
            assert np.all(occ[iz, x0:x1, y0:y1] == 0)
            assert math.isclose(float(row["center_x_m"]), xmin + (x0 + x1) * cell / 2, abs_tol=1e-9)
            assert math.isclose(float(row["center_y_m"]), ymin + (y0 + y1) * cell / 2, abs_tol=1e-9)

        candidate_sources = []
        for i in range(nav.shape[0]):
            for j in range(nav.shape[1]):
                if not nav[i, j]:
                    continue
                x, y = xmin + (i + .5) * .3, ymin + (j + .5) * .3
                fi, fj = math.floor((x - xmin) / cell), math.floor((y - ymin) / cell)
                if 0 <= fi < occ.shape[1] and 0 <= fj < occ.shape[2] and occ[iz, fi, fj] == 0:
                    candidate_sources.append((i, j, fi, fj))
        valid = {(i, j): (fi, fj) for i, j, fi, fj in candidate_sources}
        blocked = {(i, j) for i in range(-1, nav.shape[0] + 1)
                   for j in range(-1, nav.shape[1] + 1) if (i, j) not in valid}
        chosen = []
        used = set()
        sx = sum(i for i, _, _, _ in candidate_sources)
        sy = sum(j for _, j, _, _ in candidate_sources)
        n = len(candidate_sources)
        for pair in range(1, 4):
            def rank(c):
                i, j = c[:2]
                if pair == 1:
                    return ((i*n-sx)**2+(j*n-sy)**2, i, j)
                return (-min((i-a)**2+(j-b)**2 for a, b in chosen), i, j)
            for c in sorted(candidate_sources, key=rank):
                anchor = c[:2]
                if anchor in used:
                    continue
                possible = []
                for offset_rank, (di, dj) in enumerate(((1, 0), (0, 1), (-1, 0), (0, -1))):
                    partner = (anchor[0] + di, anchor[1] + dj)
                    if partner in valid and partner not in used:
                        clearance2 = min((partner[0]-bi)**2+(partner[1]-bj)**2 for bi,bj in blocked)
                        possible.append((-clearance2, offset_rank, partner))
                if possible:
                    _, _, partner = min(possible)
                    chosen.append(anchor)
                    used.update((anchor, partner))
                    expected_pair = (anchor, partner)
                    break
            else:
                raise AssertionError(f"no pair {pair}: {house}")
            observed_pair = [(int(r["pmfs_i"]), int(r["pmfs_j"])) for r in sources
                             if r["house"] == house and int(r["pair_id"]) == pair]
            assert observed_pair == list(expected_pair), (house, pair, observed_pair, expected_pair)
            for row in (r for r in sources if r["house"] == house and int(r["pair_id"]) == pair):
                i, j = int(row["pmfs_i"]), int(row["pmfs_j"])
                assert math.isclose(float(row["z_m"]), .2, abs_tol=1e-12)
                fi, fj = valid[(i, j)]
                assert occ[iz, fi, fj] == 0
                assert math.isclose(float(row["x_m"]), xmin + (i + .5) * .3, abs_tol=1e-9)
                assert math.isclose(float(row["y_m"]), ymin + (j + .5) * .3, abs_tol=1e-9)
        counts[house] = {"candidate_probes": len(candidate_probes),
                         "candidate_sources_at_z0p20": len(candidate_sources),
                         "verified_probes": 30, "verified_sources": 6}

    # Independent asset join: the frozen 6-source H02 panel has zero retained
    # cubes across all three proposed winds. Gate1A compact vectors cannot be
    # sampled at the new probe positions.
    inventory = table(args.e0_inventory)
    h02_source_xyz = {(round(float(r["x_m"]),4), round(float(r["y_m"]),4), round(float(r["z_m"]),4))
                      for r in sources if r["house"] == "House02"}
    reuse = [r for r in inventory if r["house"] == "House02" and r["form"] == "cube_10x83x119"
             and r["wind"] in ("3,5-1_fast", "3,5-1_slow", "4,5-3_slow")
             and (round(float(r["x_m"]),4), round(float(r["y_m"]),4), round(float(r["z_m"]),4)) in h02_source_xyz]
    assert len(reuse) == 0, reuse[:3]
    result = json.loads((args.out / "E1_RESULT.json").read_text())
    assert result["provisional_new_run_count"] == 168
    assert result["new_plume_runs"] == 0
    for line in (args.out / "SHA256SUMS.txt").read_text().splitlines():
        expected, filename = line.split("  ", 1)
        assert sha(args.out / filename) == expected, filename
    report = {"verdict": "E1_GEOMETRY_INDEPENDENT_CHECK_PASS",
              "house_counts": counts, "H02_matching_existing_cube_rows": 0,
              "provisional_new_runs_recomputed": 168,
              "sha_manifest_verified": True, "new_plume_runs": 0}
    (args.out / "E1_INDEPENDENT_CHECK.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
