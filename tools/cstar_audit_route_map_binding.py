"""Fail-closed audit of trajectory/map coordinate identity.

Existing environment preflight checks map and candidate files, but a scientific
M2 route also needs every historical and planned pose to use that same map
frame. This audit is evaluator-only and never changes a route or snaps a point
to a neighboring free cell.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments/ctpi_cstar'))
from common.map_geometry import load_map_info, world_cell


def map_info(path: Path):
    return load_map_info(path)


def cell(x, y, info):
    width, height, free, ox, oy, resolution = info
    ix, iy = world_cell(float(x), float(y), ox, oy, resolution)
    if ix < 0 or iy < 0 or ix >= width or iy >= height:
        return "OUTSIDE_GRID"
    return "FREE" if free[ix + iy * width] else "SOLID"


def check_points(points, info):
    counts = {"FREE": 0, "SOLID": 0, "OUTSIDE_GRID": 0}
    examples = []
    for x, y, label in points:
        status = cell(x, y, info)
        counts[status] += 1
        if status != "FREE" and len(examples) < 8:
            examples.append({"label": label, "x": x, "y": y, "status": status})
    return counts, examples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", type=Path, required=True)
    ap.add_argument("--maps", type=Path, required=True)
    ap.add_argument("--routes", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    houses = {}
    for house in ("H01", "H02", "H03"):
        manifest = json.loads((args.assets / "manifests" / f"{house}.json").read_text(encoding="utf-8"))
        info = map_info(args.maps / house)
        points = []
        for ep in manifest["m1_episodes"]:
            # The frozen LOHO manifests are deliberately complete: each file
            # contains all three Houses, with only the outer-fold role changed.
            # Bind a trajectory to the map named by its own physical House;
            # otherwise a complete manifest would be (incorrectly) replayed
            # against H01/H02/H03 maps in turn and manufacture false failures.
            if ep["house"] != house:
                continue
            for row in (json.loads(line) for line in
                        (args.assets / ep["history_trace_path"]).read_text(encoding="utf-8").splitlines() if line.strip()):
                points.append((*row["pose_xy"], f"history:{ep['episode_id']}:{row['t_sim_s']}"))
        for case in manifest["m2_route_cases"]:
            if case["house"] != house:
                continue
            route_name = Path(case["planned_route_path"]).name
            with (args.routes / house / route_name).open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    points.append((float(row["x"]), float(row["y"]),
                                   f"route:{case['decision_id']}:{row['t_sim_s']}"))
        counts, examples = check_points(points, info)
        houses[house] = {"map": {"width": info[0], "height": info[1],
                                  "origin_xy": [info[3], info[4]], "resolution": info[5]},
                         "point_counts": counts, "bad_examples": examples,
                         "pass": counts["SOLID"] == 0 and counts["OUTSIDE_GRID"] == 0}
    passed = all(item["pass"] for item in houses.values())
    report = {"contract": "CSTAR_ROUTE_MAP_BINDING_AUDIT_V2", "pass": passed,
              "geometry_semantics": "byte-exact PGM; YAML strict free threshold; floor from cell-corner origin",
              "verdict": "CSTAR_ROUTE_MAP_BINDING_PASS" if passed else "CSTAR_ROUTE_MAP_BINDING_NO_GO",
              "houses": houses,
              "policy": "no snapping, translation, or House-specific repair is allowed after route freeze"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
