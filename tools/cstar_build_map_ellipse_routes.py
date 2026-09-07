"""Build source-blind, map-derived fixed routes for the current-runtime screen.

The route is an ellipse fitted only to the free-cell candidate-domain bounds;
source coordinates are never read.  Each sample is projected to the nearest
free candidate cell, producing a 0.2 s, 300-frame history route.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--frames", type=int, default=301)
    args = ap.parse_args()
    if args.frames < 2:
        raise SystemExit("frames")
    summaries = {}
    for house in ("H01", "H02", "H03"):
        src = args.maps / house / "candidate.csv"
        with src.open(encoding="utf-8", newline="") as f:
            pts = [(float(r["x"]), float(r["y"])) for r in csv.DictReader(f)]
        xs, ys = zip(*pts)
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        rx, ry = 0.95 * (max(xs) - min(xs)) / 2, 0.95 * (max(ys) - min(ys)) / 2
        route = []
        for i in range(args.frames):
            theta = 2 * math.pi * i / (args.frames - 1)
            tx, ty = cx + rx * math.cos(theta), cy + ry * math.sin(theta)
            x, y = min(pts, key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2)
            route.append((round(i * 0.2, 9), x, y, 0.3))
        out = args.out / house
        out.mkdir(parents=True, exist_ok=True)
        path = out / "history_route.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(("t_sim_s", "x", "y", "z"))
            w.writerows(route)
        ds = [math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(route, route[1:])]
        summaries[house] = {
            "frames": len(route), "t_end_s": route[-1][0],
            "bounds": [min(xs), max(xs), min(ys), max(ys)],
            "center": [cx, cy], "radii": [rx, ry],
            "max_step_m": max(ds), "path_length_m": sum(ds),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    (args.out / "ROUTE_RULE.json").write_text(json.dumps({
        "contract": "CSTAR_SOURCE_BLIND_MAP_ELLIPSE_ROUTE_V1",
        "source_coordinates_read": False,
        "candidate_domain_only": True,
        "sample_period_s": 0.2,
        "houses": summaries,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summaries, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
