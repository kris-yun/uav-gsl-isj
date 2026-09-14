#!/usr/bin/env python3
"""Query S1-center responses for the frozen route set on design winds only."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import os
import time
from pathlib import Path

import rclpy

from query_synchronized_pair_from_raw_cache import FOPDT, FrameClient, sha256_file, start_player, stop_player


SOURCES = ("S_truth", "S_k01", "S_k10", "S_k22")
DESIGN_WINDS = ("W_fast", "W_slow")
FRAME_DT = 0.5


def read_route(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


FIELDS = (
    "route_id", "source_id", "wind_id", "route_time_s", "step", "plume_frame_iteration",
    "x", "y", "z", "raw_gas_concentration_ppm", "processed_sensor_output_ppm",
    "wind_u", "wind_v", "wind_w", "gas_hit",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--player", required=True)
    parser.add_argument("--ros-domain", default="226")
    args = parser.parse_args()
    os.environ["ROS_DOMAIN_ID"] = args.ros_domain
    route_paths = sorted(args.candidate_root.glob("AO_*/CENTER.csv"))
    if len(route_paths) != 12:
        raise RuntimeError(f"expected 12 frozen candidate routes, found {len(route_paths)}")
    routes = {path.parent.name: read_route(path) for path in route_paths}
    if any(len(rows) != 750 for rows in routes.values()):
        raise RuntimeError("candidate route cardinality failure")
    trace_dir = args.out_dir / "design_traces"
    log_dir = args.out_dir / "logs"
    trace_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    rclpy.init()
    try:
        for source in SOURCES:
            for wind in DESIGN_WINDS:
                label = f"{source}__{wind}"
                raw = args.raw_root / label
                process = log = node = None
                cache = {}
                try:
                    process, log = start_player(args.player, raw, args.occupancy, args.ros_domain, log_dir / f"{label}.log")
                    time.sleep(2.0)
                    node = FrameClient()
                    if not node.client.wait_for_service(timeout_sec=60.0):
                        raise RuntimeError(f"frame_query unavailable for {label}")
                    for route_id, route in routes.items():
                        sensor, rows = FOPDT(), []
                        for index, sample in enumerate(route):
                            route_t = float(sample["t_sim_s"])
                            frame = int(math.floor(route_t / FRAME_DT))
                            xyz = tuple(float(sample[key]) for key in ("x", "y", "z"))
                            key = (frame, *(round(value, 9) for value in xyz))
                            if key not in cache:
                                cache[key] = node.query(frame, xyz)
                            concentration, wind_u, wind_v, wind_w = cache[key]
                            processed = sensor.process(concentration)
                            rows.append((route_id, source, wind, route_t, index + 1, frame, *xyz, concentration, processed, wind_u, wind_v, wind_w, int(processed > 0.1)))
                        out_path = trace_dir / f"{route_id}__{label}.csv.gz"
                        with gzip.open(out_path, "wt", newline="", encoding="utf-8") as stream:
                            writer = csv.writer(stream, lineterminator="\n")
                            writer.writerow(FIELDS)
                            writer.writerows(rows)
                        manifest.append({"route_id": route_id, "source": source, "wind": wind, "rows": len(rows), "frame_min": 0, "frame_max": 299, "sha256": sha256_file(out_path)})
                        print(f"DESIGN_QUERY {label} {route_id} 750/750 cache={len(cache)}", flush=True)
                finally:
                    if node is not None:
                        node.destroy_node()
                    stop_player(process, log)
    finally:
        rclpy.shutdown()
    summary = {
        "schema": "OBSERVABILITY_FIRST_DESIGN_QUERY_V1",
        "winds_queried": list(DESIGN_WINDS), "forbidden_wind_queried": False,
        "sources": list(SOURCES), "candidate_count": len(routes), "trace_count": len(manifest),
        "total_rows": sum(item["rows"] for item in manifest),
        "raw_cache_only": True, "new_gaden": False,
        "fopdt": {"dead_s": 0.4, "rise_s": 1.2, "recovery_s": 1.2, "dt_s": 0.2},
        "manifest": manifest,
        "status": "PASS" if len(manifest) == 96 and all(item["rows"] == 750 for item in manifest) else "FAIL",
    }
    (args.out_dir / "DESIGN_QUERY_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("trace_count", "total_rows", "forbidden_wind_queried", "status")}))


if __name__ == "__main__":
    main()
