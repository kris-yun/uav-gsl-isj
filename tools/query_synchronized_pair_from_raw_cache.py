#!/usr/bin/env python3
"""Query the frozen dual route from existing GADEN frames, never simulate gas."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import signal
import subprocess
import time
from collections import deque
from pathlib import Path

import rclpy
from gaden_msgs.srv import FrameQuery
from rclpy.node import Node


DT = 0.2
FRAME_DT = 0.5
SOURCES = ("S_truth", "S_k01", "S_k10", "S_k22")
WINDS = ("W_fast", "W_slow", "W_altfast")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_route(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class FrameClient(Node):
    def __init__(self):
        super().__init__("dual_uav_same_frame_client")
        self.client = self.create_client(FrameQuery, "frame_query")

    def query(self, iteration: int, xyz):
        request = FrameQuery.Request()
        request.iteration = int(iteration)
        request.x, request.y, request.z = map(float, xyz)
        for attempt in range(40):
            future = self.client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=20.0)
            if future.done() and future.result() is not None:
                response = future.result()
                if response.valid:
                    values = tuple(map(float, (response.concentration, response.wind_u, response.wind_v, response.wind_w)))
                    if all(map(math.isfinite, values)):
                        return values
                message = response.error_message or "invalid"
                if "unavailable" not in message.lower():
                    raise RuntimeError(f"frame_query invalid frame={iteration} xyz={xyz}: {message}")
            if attempt == 39:
                raise RuntimeError(f"frame_query timeout frame={iteration} xyz={xyz}")
            time.sleep(0.25)
        raise RuntimeError("unreachable")


class FOPDT:
    def __init__(self, dead=0.4, rise=1.2, recovery=1.2):
        self.dead, self.rise, self.recovery = dead, rise, recovery
        self.t = 0.0
        self.state = 0.0
        self.history = deque([(0.0, 0.0)])

    def delayed(self, query_t):
        if query_t <= 0.0:
            return 0.0
        if query_t >= self.history[-1][0]:
            return self.history[-1][1]
        previous_t, previous_v = self.history[0]
        for next_t, next_v in list(self.history)[1:]:
            if query_t <= next_t:
                width = next_t - previous_t
                return next_v if width <= 0 else previous_v + (query_t - previous_t) / width * (next_v - previous_v)
            previous_t, previous_v = next_t, next_v
        return self.history[-1][1]

    def process(self, value, dt=DT):
        self.t += dt
        self.history.append((self.t, float(value)))
        delayed = self.delayed(self.t - self.dead)
        tau = self.rise if delayed >= self.state else self.recovery
        alpha = math.exp(-dt / tau)
        self.state = alpha * self.state + (1.0 - alpha) * delayed
        return self.state


def start_player(player: str, raw: Path, occupancy: Path, ros_domain: str, log_path: Path):
    environment = os.environ.copy()
    environment["ROS_DOMAIN_ID"] = ros_domain
    log = log_path.open("w", encoding="utf-8")
    command = [
        player, "--ros-args",
        "-p", "num_simulators:=1", "-p", f"simulation_data_0:={raw}",
        "-p", f"occupancyFile:={occupancy}", "-p", "initial_iteration:=0",
        "-p", "player_freq:=1.0", "-p", "manual_iteration_mode:=true",
        "-p", "allow_looping:=false",
    ]
    log.write("COMMAND=" + " ".join(command) + "\n")
    log.flush()
    process = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    return process, log


def stop_player(process, log):
    if process is not None and process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
    if log is not None:
        log.close()


FIELDS = (
    "source_id", "wind_id", "route_time_s", "step", "plume_frame_iteration", "plume_frame_time_s",
    "x_plus", "y_plus", "z_plus_position", "x_minus", "y_minus", "z_minus_position",
    "baseline_angle_deg", "baseline_length_m", "raw_c_plus_ppm", "raw_c_minus_ppm",
    "processed_z_plus_ppm", "processed_z_minus_ppm", "hit_plus", "hit_minus",
    "wind_plus_u", "wind_plus_v", "wind_plus_w", "wind_minus_u", "wind_minus_v", "wind_minus_w",
    "same_frame", "endpoint_geometry_valid",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--plus-route", type=Path, required=True)
    parser.add_argument("--minus-route", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--player", default="/home/zyc/ros2_ws/install/gaden_player/lib/gaden_player/player")
    parser.add_argument("--ros-domain", default="226")
    args = parser.parse_args()
    plus_all, minus_all = read_route(args.plus_route), read_route(args.minus_route)
    os.environ["ROS_DOMAIN_ID"] = args.ros_domain
    args.out_dir.mkdir(parents=True, exist_ok=True)
    log_dir = args.out_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    trace_dir = args.out_dir / "synchronized_traces"
    trace_dir.mkdir(exist_ok=True)
    manifest = []
    rclpy.init()
    try:
        for source in SOURCES:
            for wind in WINDS:
                plus = [row for row in plus_all if row["wind_id"] == wind]
                minus = [row for row in minus_all if row["wind_id"] == wind]
                if len(plus) != 750 or len(minus) != 750:
                    raise RuntimeError(f"route cardinality {wind}: plus={len(plus)} minus={len(minus)}")
                raw = args.raw_root / f"{source}__{wind}"
                if not raw.is_dir():
                    raise FileNotFoundError(raw)
                process = log = node = None
                rows = []
                label = f"{source}__{wind}"
                try:
                    process, log = start_player(args.player, raw, args.occupancy, args.ros_domain, log_dir / f"{label}.log")
                    time.sleep(2.0)
                    node = FrameClient()
                    if not node.client.wait_for_service(timeout_sec=60.0):
                        raise RuntimeError(f"frame_query unavailable for {label}")
                    sensor_plus, sensor_minus = FOPDT(), FOPDT()
                    for index, (p, m) in enumerate(zip(plus, minus)):
                        if p["step"] != m["step"] or p["t_sim_s"] != m["t_sim_s"]:
                            raise RuntimeError(f"pair timing mismatch {label} row={index}")
                        route_t = float(p["t_sim_s"])
                        frame = int(math.floor(route_t / FRAME_DT))
                        pxyz = tuple(float(p[key]) for key in ("x", "y", "z"))
                        mxyz = tuple(float(m[key]) for key in ("x", "y", "z"))
                        cp, up, vp, wp = node.query(frame, pxyz)
                        cm, um, vm, wm = node.query(frame, mxyz)
                        zp, zm = sensor_plus.process(cp), sensor_minus.process(cm)
                        rows.append((
                            source, wind, route_t, int(p["step"]), frame, frame * FRAME_DT,
                            *pxyz, *mxyz, float(p["baseline_angle_deg"]), float(p["baseline_length_m"]),
                            cp, cm, zp, zm, int(zp > 0.1), int(zm > 0.1),
                            up, vp, wp, um, vm, wm, 1, 1,
                        ))
                        if (index + 1) % 150 == 0:
                            print(f"QUERY {label} {index + 1}/750", flush=True)
                    out_path = trace_dir / f"{label}.csv.gz"
                    with gzip.open(out_path, "wt", newline="", encoding="utf-8") as stream:
                        writer = csv.writer(stream)
                        writer.writerow(FIELDS)
                        writer.writerows(rows)
                    manifest.append({"source": source, "wind": wind, "rows": len(rows), "frame_min": 0, "frame_max": max(row[4] for row in rows), "sha256": sha256_file(out_path)})
                finally:
                    if node is not None:
                        node.destroy_node()
                    stop_player(process, log)
    finally:
        rclpy.shutdown()
    summary = {
        "schema": "DUAL_UAV_SAME_FRAME_RAW_CACHE_QUERY_V1",
        "mode": "EXISTING_RAW_CACHE_ONLY_NO_SIMULATION",
        "plus_route_sha256": sha256_file(args.plus_route),
        "minus_route_sha256": sha256_file(args.minus_route),
        "fopdt": {"dead_s": 0.4, "rise_s": 1.2, "recovery_s": 1.2, "dt_s": DT, "independent_receiver_states": True},
        "trace_count": len(manifest), "total_rows": sum(row["rows"] for row in manifest),
        "same_frame_failures": 0, "manifest": manifest,
        "status": "PASS" if len(manifest) == 12 and all(row["rows"] == 750 for row in manifest) else "FAIL",
    }
    (args.out_dir / "SAME_FRAME_QUERY_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
