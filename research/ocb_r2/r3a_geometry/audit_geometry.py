#!/usr/bin/env python3
"""R3A read-only geometry census. Never imports plume or score data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt


EXPECTED = {
    "House01": "846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb",
    "House02": "9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_occ(path: Path) -> tuple[dict, np.ndarray]:
    header: dict[str, list[float]] = {}
    values: list[int] = []
    for line in path.read_text().splitlines():
        if line.startswith("#"):
            key, *v = line[1:].split()
            header[key] = [float(x) for x in v]
        elif line.strip() and line.strip() != ";":
            values.extend(int(x) for x in line.split())
    nx, ny, nz = (int(x) for x in header["num_cells"])
    return header, np.asarray(values, dtype=np.int8).reshape(nz, nx, ny)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--h01-occ", type=Path, required=True)
    p.add_argument("--h02-occ", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    runlist = a.repo / "evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv"
    exposure = a.repo / "evidence/e2c_r1/PRIOR_SOURCE_EXPOSURE_UNION.tsv"
    with runlist.open(newline="") as f:
        runrows = list(csv.DictReader(f, delimiter="\t"))
    with exposure.open(newline="") as f:
        banned = {(r["house"], r["source_id"]) for r in csv.DictReader(f, delimiter="\t")}
    out: dict = {"inputs": {"s2_runlist_sha256": sha(runlist), "exposure_union_sha256": sha(exposure)}, "houses": {}}
    eligible_rows: list[dict] = []
    for house, occpath, env_idx in (("House01", a.h01_occ, 0), ("House02", a.h02_occ, 1)):
        assert sha(occpath) == EXPECTED[house], f"occupancy hash mismatch: {house}"
        header, occ = read_occ(occpath)
        clearance3d = distance_transform_edt(occ == 0) * header["cell_size(m)"][0]
        meta_path = a.repo / f"evidence/marked_encounter_pmfs_d0/inputs/env_{env_idx}/meta.json"
        mask_path = meta_path.with_name("occupancy.u8")
        meta = json.loads(meta_path.read_text())
        nx, ny = meta["width"], meta["height"]
        nav = np.frombuffer(mask_path.read_bytes(), dtype=np.uint8).reshape(ny, nx).T == 1
        origin = header["env_min(m)"]
        cell = header["cell_size(m)"][0]
        assert abs(cell - 0.1) < 1e-8
        assert abs(meta["origin_x"] - origin[0]) < 1e-5
        assert abs(meta["origin_y"] - origin[1]) < 1e-5
        original = {}
        for r in runrows:
            if r["house"] == house:
                original[r["source_id"]] = (float(r["source_x"]), float(r["source_y"]), float(r["source_z"]))
        assert len(original) == 2
        house_result = {"occupancy_sha256": sha(occpath), "nav_mask_sha256": sha(mask_path),
                        "nav_free_cells": int(nav.sum()), "original_sources": original, "layers": {}}
        for anchor_name, (ax, ay, az) in sorted(original.items()):
            iz = math.floor((az - origin[2]) / cell)
            assert 0 <= iz < occ.shape[0]
            valid = np.zeros_like(nav)
            for i, j in np.argwhere(nav):
                x = origin[0] + (int(i) + .5) * .3
                y = origin[1] + (int(j) + .5) * .3
                fi = math.floor((x - origin[0]) / cell)
                fj = math.floor((y - origin[1]) / cell)
                if 0 <= fi < occ.shape[1] and 0 <= fj < occ.shape[2] and occ[iz, fi, fj] == 0:
                    valid[i, j] = True
            clearance = distance_transform_edt(np.pad(valid, 1, constant_values=False))[1:-1, 1:-1] * .3
            entries = []
            for i, j in np.argwhere(valid):
                i, j = int(i), int(j)
                sid = f"pmfs_{i}_{j}"
                x = origin[0] + (i + .5) * .3
                y = origin[1] + (j + .5) * .3
                fi = math.floor((x - origin[0]) / cell)
                fj = math.floor((y - origin[1]) / cell)
                dist = math.hypot(x - ax, y - ay)
                other_dist = min(math.hypot(x - ox, y - oy) for name, (ox, oy, _) in original.items() if name != anchor_name)
                banned_here = (house, sid) in banned or min(math.hypot(x - ox, y - oy) for ox, oy, _ in original.values()) < .15
                entries.append((i, j, sid, x, y, az, dist, other_dist, float(clearance[i, j]), banned_here))
                eligible_rows.append({"house": house, "anchor": anchor_name, "source_id": sid, "i": i, "j": j,
                                      "x_m": f"{x:.8f}", "y_m": f"{y:.8f}", "z_m": f"{az:.8f}",
                                      "anchor_distance_m": f"{dist:.6f}", "other_old_distance_m": f"{other_dist:.6f}",
                                      "2d_clearance_m": f"{clearance[i, j]:.6f}",
                                      "3d_clearance_m": f"{clearance3d[iz, fi, fj]:.6f}",
                                      "exposed": int(banned_here)})
            allowed = [e for e in entries if not e[-1]]
            shell = {}
            for lo, hi in ((.0, .6), (.6, .9), (.9, 1.2), (1.2, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 100.0)):
                shell[f"{lo:.1f}-{hi:.1f}"] = sum(lo <= e[6] < hi and e[8] >= .6 for e in allowed)
            house_result["layers"][anchor_name] = {"source_z": az, "fine_z_index": iz,
                "valid_source_cells": len(entries), "unexposed_source_cells": len(allowed),
                "unexposed_clearance_ge_0p6_shell_counts": shell}
        out["houses"][house] = house_result
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "R3A_GEOMETRY_CENSUS.json").write_bytes((json.dumps(out, indent=2, sort_keys=True) + "\n").encode())
    with (a.out / "R3A_ELIGIBLE_CELLS.tsv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(eligible_rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(eligible_rows)
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
