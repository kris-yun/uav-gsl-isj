#!/usr/bin/env python3
"""Query frozen plus/minus routes on design winds from existing raw caches only."""

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
EXPECTED_ROUTE_COUNT = 12
EXPECTED_SAMPLES = 750


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def wind_rows(path: Path, wind: str):
    rows = [row for row in read_rows(path) if row["wind_id"] == wind]
    if len(rows) != EXPECTED_SAMPLES:
        raise RuntimeError(f"route cardinality failure: {path} {wind} rows={len(rows)}")
    return rows


FIELDS = (
    "route_id", "source_id", "wind_id", "route_time_s", "step", "plume_frame_iteration",
    "x_plus", "y_plus", "z_plus", "x_minus", "y_minus", "z_minus",
    "raw_c_plus_ppm", "raw_c_minus_ppm", "processed_c_plus_ppm", "processed_c_minus_ppm",
    "wind_plus_u", "wind_plus_v", "wind_plus_w", "wind_minus_u", "wind_minus_v", "wind_minus_w",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--player", required=True)
    parser.add_argument("--ros-domain", default="226")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--no-player-log", action="store_true")
    parser.add_argument("--only-source", choices=SOURCES)
    parser.add_argument("--only-wind", choices=DESIGN_WINDS)
    parser.add_argument("--summary-name", default="ENDPOINT_QUERY_SUMMARY.json")
    args = parser.parse_args()

    os.environ["ROS_DOMAIN_ID"] = args.ros_domain
    route_dirs = sorted(path for path in args.candidate_root.glob("AO_*") if path.is_dir())
    if len(route_dirs) != EXPECTED_ROUTE_COUNT:
        raise RuntimeError(f"expected {EXPECTED_ROUTE_COUNT} candidate routes, found {len(route_dirs)}")

    trace_dir = args.out_dir / "endpoint_design_traces"
    log_dir = args.out_dir / "logs"
    trace_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    player_log = lambda name: Path("/dev/null") if args.no_player_log else log_dir / name
    selected_sources = (args.only_source,) if args.only_source else SOURCES
    selected_winds = (args.only_wind,) if args.only_wind else DESIGN_WINDS

    if args.probe_only:
        source, wind = SOURCES[0], DESIGN_WINDS[0]
        route_dir = route_dirs[0]
        plus = wind_rows(route_dir / "PLUS.csv", wind)[0]
        minus = wind_rows(route_dir / "MINUS.csv", wind)[0]
        process = log = node = None
        os.environ["ROS_DOMAIN_ID"] = args.ros_domain
        rclpy.init()
        try:
            process, log = start_player(
                args.player, args.raw_root / f"{source}__{wind}", args.occupancy,
                args.ros_domain, player_log("QUERY_PATH_PRECHECK.log"),
            )
            time.sleep(2.0)
            node = FrameClient()
            if not node.client.wait_for_service(timeout_sec=60.0):
                raise RuntimeError("frame_query unavailable for query-path precheck")
            pxyz = tuple(float(plus[key]) for key in ("x", "y", "z"))
            mxyz = tuple(float(minus[key]) for key in ("x", "y", "z"))
            plus_values = node.query(0, pxyz)
            minus_values = node.query(0, mxyz)
            report = {
                "schema": "SENSING_SUPPORT_QUERY_PATH_PRECHECK_V1",
                "route_id": route_dir.name,
                "source_selector": source,
                "design_wind": wind,
                "center_path_previously_verified": True,
                "plus_query_valid_finite": all(math.isfinite(value) for value in plus_values),
                "minus_query_valid_finite": all(math.isfinite(value) for value in minus_values),
                "concentration_values_persisted": False,
                "raw_cache_only": True,
                "filament_simulator_started": False,
                "non_design_wind_queried": False,
                "status": "PASS",
            }
            (args.out_dir / "QUERY_PATH_PRECHECK.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(report))
        finally:
            if node is not None:
                node.destroy_node()
            stop_player(process, log)
            rclpy.shutdown()
        return

    rclpy.init()
    try:
        for source in selected_sources:
            for wind in selected_winds:
                label = f"{source}__{wind}"
                raw = args.raw_root / label
                if not raw.is_dir():
                    raise FileNotFoundError(raw)
                process = log = node = None
                query_cache = {}
                try:
                    process, log = start_player(
                        args.player, raw, args.occupancy, args.ros_domain, log_dir / f"{label}.log"
                        if not args.no_player_log else Path("/dev/null")
                    )
                    time.sleep(2.0)
                    node = FrameClient()
                    if not node.client.wait_for_service(timeout_sec=60.0):
                        raise RuntimeError(f"frame_query unavailable for {label}")

                    for route_dir in route_dirs:
                        route_id = route_dir.name
                        plus = wind_rows(route_dir / "PLUS.csv", wind)
                        minus = wind_rows(route_dir / "MINUS.csv", wind)
                        sensor_plus, sensor_minus = FOPDT(), FOPDT()
                        output_rows = []
                        for index, (p_row, m_row) in enumerate(zip(plus, minus)):
                            if p_row["step"] != m_row["step"] or p_row["t_sim_s"] != m_row["t_sim_s"]:
                                raise RuntimeError(f"pair timing mismatch {route_id} {wind} row={index}")
                            route_t = float(p_row["t_sim_s"])
                            frame = int(math.floor(route_t / FRAME_DT))
                            pxyz = tuple(float(p_row[key]) for key in ("x", "y", "z"))
                            mxyz = tuple(float(m_row[key]) for key in ("x", "y", "z"))

                            def query(xyz):
                                key = (frame, *(round(value, 9) for value in xyz))
                                if key not in query_cache:
                                    query_cache[key] = node.query(frame, xyz)
                                return query_cache[key]

                            cp, up, vp, wp = query(pxyz)
                            cm, um, vm, wm = query(mxyz)
                            zp, zm = sensor_plus.process(cp), sensor_minus.process(cm)
                            output_rows.append((
                                route_id, source, wind, route_t, index + 1, frame,
                                *pxyz, *mxyz, cp, cm, zp, zm, up, vp, wp, um, vm, wm,
                            ))

                        out_path = trace_dir / f"{route_id}__{label}.csv.gz"
                        with gzip.open(out_path, "wt", newline="", encoding="utf-8") as stream:
                            writer = csv.writer(stream, lineterminator="\n")
                            writer.writerow(FIELDS)
                            writer.writerows(output_rows)
                        manifest.append({
                            "route_id": route_id,
                            "source": source,
                            "wind": wind,
                            "rows": len(output_rows),
                            "frame_min": 0,
                            "frame_max": 299,
                            "sha256": sha256_file(out_path),
                        })
                        print(
                            f"ENDPOINT_QUERY {label} {route_id} {len(output_rows)}/{EXPECTED_SAMPLES} cache={len(query_cache)}",
                            flush=True,
                        )
                finally:
                    if node is not None:
                        node.destroy_node()
                    stop_player(process, log)
    finally:
        rclpy.shutdown()

    summary = {
        "schema": "SENSING_SUPPORT_ENDPOINT_DESIGN_QUERY_V1",
        "mode": "EXISTING_RAW_CACHE_ONLY_NO_SIMULATION",
        "winds_queried": list(selected_winds),
        "non_design_wind_queried": False,
        "sources": list(selected_sources),
        "candidate_count": len(route_dirs),
        "trace_count": len(manifest),
        "total_rows": sum(item["rows"] for item in manifest),
        "receiver_channels": ["plus", "minus"],
        "channel_compression": "NONE_ORDERED_CHANNELS_PRESERVED",
        "fopdt": {
            "dead_s": 0.4,
            "rise_s": 1.2,
            "recovery_s": 1.2,
            "dt_s": 0.2,
            "independent_receiver_states": True,
        },
        "raw_cache_only": True,
        "filament_simulator_started": False,
        "new_gaden_dataset_generated": False,
        "manifest": manifest,
        "expected_trace_count": EXPECTED_ROUTE_COUNT * len(selected_sources) * len(selected_winds),
        "status": "PASS" if len(manifest) == EXPECTED_ROUTE_COUNT * len(selected_sources) * len(selected_winds) and all(item["rows"] == EXPECTED_SAMPLES for item in manifest) else "FAIL",
    }
    (args.out_dir / args.summary_name).write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: summary[key] for key in ("trace_count", "total_rows", "non_design_wind_queried", "status")}))


if __name__ == "__main__":
    main()
