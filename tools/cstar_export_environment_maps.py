"""Freeze geometry-only navigation slices and exhaustive truth-blind candidates.

No gas payload, source labels, banks or outcome-dependent filtering is read.
Flight height and hover endpoints are the unchanged R4 seed12 input settings.
Candidate support is every free fine-grid cell centre (not a learned-model result).
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import cv2
import yaml


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(exist_ok=False, parents=True)
    result = {}
    for house, name, endpoint in [("H01", "House01", (-3.17, -1.75)),
                                   ("H02", "House02", (-0.5, -2.5)),
                                   ("H03", "House03", (2.0, 0.0))]:
        occ = args.scenario_root / name / "OccupancyGrid3D.csv"
        meta, values = {}, []
        for line in occ.read_text().splitlines():
            line = line.strip()
            if not line or line == ";":
                continue
            if line.startswith("#"):
                parts = line.split()
                meta[parts[0].split("(")[0]] = parts[1:]
            else:
                values.extend(map(int, line.split()))
        nx, ny, nz = map(int, meta["#num_cells"])
        origin = list(map(float, meta["#env_min"]))
        size = float(meta["#cell_size"][0])
        assert len(values) == nx*ny*nz and set(values) <= {0, 1, 2}
        zi = int((0.3-origin[2])/size)
        assert 0 <= zi < nz  # never silently clip the navigation height
        layer = np.asarray(values, dtype=np.uint8).reshape(nz, nx, ny)[zi] != 0
        image = np.flipud(np.where(layer.T, 0, 255).astype(np.uint8))
        d = args.out / house
        d.mkdir()
        pgm, ym = d / "navigation_slice.pgm", d / "navigation_slice.yaml"
        assert cv2.imwrite(str(pgm), image)
        ym.write_text(yaml.safe_dump({"image": pgm.name, "resolution": size,
            "origin": origin[:2]+[0], "negate": 0, "occupied_thresh": 0.9, "free_thresh": 0.1}))
        assert np.array_equal(np.flipud(cv2.imread(str(pgm), 0)).T == 0, layer)
        probes = []
        for kind in ("candidate", "route"):
            csvpath = d / f"{kind}.csv"
            with csvpath.open("x", newline="") as f:
                w = csv.writer(f)
                w.writerow(["x", "y"])
                if kind == "candidate":
                    for ix in range(nx):
                        for iy in range(ny):
                            if not layer[ix, iy]:
                                w.writerow([origin[0]+(ix+0.5)*size, origin[1]+(iy+0.5)*size])
                else:
                    w.writerow(endpoint)
            probes.append({"kind": kind, "path": str(csvpath), "sha256": sha(csvpath)})
        result[house] = {"geometry_identity": f"{house}:occupancy-{sha(occ)}:z0.3:full-slice",
            "occupancy_path": str(occ), "occupancy_sha256": sha(occ), "z_index": zi,
            "map_yaml_path": str(ym), "map_yaml_sha256": sha(ym),
            "map_image_path": str(pgm), "map_image_sha256": sha(pgm),
            "navigation_height_m": 0.3, "resolution_m": size, "origin_xy_m": origin[:2],
            "expected_width_px": nx, "expected_height_px": ny, "free_cell_count": int((~layer).sum()),
            "free_space_probe_csvs": probes,
            "candidate_scope": "all-free-cell centres, geometry-only frozen support for future controlled producer",
            "route_scope": "predeclared stationary R4 start endpoint + 1.6s dwell; no navigation performance claim",
            "exporter_sha256": sha(Path(__file__))}
    (args.out / "geometry_manifest.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
