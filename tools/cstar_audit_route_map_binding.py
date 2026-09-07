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


def read_pgm(path: Path):
    raw = path.read_bytes()
    if not raw.startswith(b"P5"):
        raise ValueError("CSTAR_MAP_BINDING_PGM")
    parts, i = [], 2
    while len(parts) < 3:
        while i < len(raw) and raw[i] in b" \t\r\n": i += 1
        if raw[i:i + 1] == b"#":
            i = raw.find(b"\n", i) + 1
            continue
        j = i
        while j < len(raw) and raw[j] not in b" \t\r\n": j += 1
        parts.append(int(raw[i:j])); i = j
    width, height, maximum = parts
    pixels = raw[i:i + width * height]
    if maximum != 255 or len(pixels) != width * height:
        raise ValueError("CSTAR_MAP_BINDING_PGM_SIZE")
    free = [False] * (width * height)
    for row in range(height):
        for x in range(width):
            y = height - 1 - row
            free[x + y * width] = pixels[row * width + x] > 0
    return width, height, tuple(free)


def map_info(path: Path):
    lines = (path / "navigation_slice.yaml").read_text(encoding="utf-8").splitlines()
    oi = next(i for i, line in enumerate(lines) if line.startswith("origin:"))
    ox = float(lines[oi + 1].split("-", 1)[1])
    oy = float(lines[oi + 2].split("-", 1)[1])
    resolution = float(next(line.split(":", 1)[1] for line in lines if line.startswith("resolution:")))
    width, height, free = read_pgm(path / "navigation_slice.pgm")
    return width, height, free, ox, oy, resolution


def cell(x, y, info):
    width, height, free, ox, oy, resolution = info
    ix, iy = round((float(x) - ox) / resolution), round((float(y) - oy) / resolution)
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
            for row in (json.loads(line) for line in
                        (args.assets / ep["history_trace_path"]).read_text(encoding="utf-8").splitlines() if line.strip()):
                points.append((*row["pose_xy"], f"history:{ep['episode_id']}:{row['t_sim_s']}"))
        for case in manifest["m2_route_cases"]:
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
    report = {"contract": "CSTAR_ROUTE_MAP_BINDING_AUDIT_V1", "pass": passed,
              "verdict": "CSTAR_ROUTE_MAP_BINDING_PASS" if passed else "CSTAR_ROUTE_MAP_BINDING_NO_GO",
              "houses": houses,
              "policy": "no snapping, translation, or House-specific repair is allowed after route freeze"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
