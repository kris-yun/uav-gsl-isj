"""Isolated DDS wind-interface test on the existing GMRF binary, no House.

Two fresh tiny-map processes: existing map-frame anemometer convention, then
explicit downwind+position service. No sensor/source simulation or bank reads.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from nav_msgs.msg import OccupancyGrid
from olfaction_msgs.msg import Anemometer
from gmrf_msgs.srv import WindEstimation, AddWindObservation

BINARY = Path("/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib/gmrf_wind_mapping/gmrf_wind_mapping_node")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from closed_loop.ctpi.ctpi_v2_wind_observation import gmrf_request_values


def call(node, client, request, timeout=3.0):
    future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
    if not future.done() or future.exception():
        raise RuntimeError("probe service request failed or timed out")
    return future.result()


def run_case(case, directory):
    prefix = "/ctpi_v2_wind_contract/" + case
    node = Node("ctpi_v2_wind_probe_" + case)
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     reliability=ReliabilityPolicy.RELIABLE)
    map_pub = node.create_publisher(OccupancyGrid, prefix + "/map", qos)
    wind_pub = node.create_publisher(Anemometer, prefix + "/wind", 10)
    query = node.create_client(WindEstimation, prefix + "/estimate")
    add = node.create_client(AddWindObservation, prefix + "/add")
    command = [str(BINARY), "--ros-args", "-r", "__node:=gmrf_contract_" + case,
               "-r", "WindEstimation:=" + prefix + "/estimate",
               "-r", "AddWindObservation:=" + prefix + "/add",
               "-p", "map_topic:=" + prefix + "/map", "-p", "sensor_topic:=" + prefix + "/wind",
               "-p", "frame_id:=map", "-p", "cell_size:=1.0", "-p", "exec_freq:=10.0",
               "-p", "verbose:=false", "-p", "visualize_gmrf:=false"]
    log_path = directory / (case + ".log")
    process = None
    try:
        with log_path.open("x", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            grid = OccupancyGrid()
            grid.header.frame_id = "map"
            grid.info.width = grid.info.height = 7
            grid.info.resolution = 1.0
            grid.info.origin.position.x = grid.info.origin.position.y = -3.0
            grid.info.origin.orientation.w = 1.0
            grid.data = [0] * 49
            deadline = time.monotonic() + 15.0
            # Event-driven bounded startup; no simulator time or external process.
            while not (query.service_is_ready() and wind_pub.get_subscription_count()):
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("GMRF probe startup failed: " + str(log_path))
                grid.header.stamp = node.get_clock().now().to_msg()
                map_pub.publish(grid)
                rclpy.spin_once(node, timeout_sec=.05)
            request = WindEstimation.Request()
            request.x = [-1., 0., 1., 2.]
            request.y = [0., 0., 1., 1.]
            # Service existence follows GMRF initialization in this implementation.
            baseline = call(node, query, request)
            if case == "legacy_map_message":
                msg = Anemometer()
                msg.header.frame_id = "map"
                msg.header.stamp = node.get_clock().now().to_msg()
                msg.wind_speed = 1.0
                msg.wind_direction = 0.0
                wind_pub.publish(msg)
            else:
                if not add.wait_for_service(timeout_sec=3.0):
                    raise RuntimeError("explicit observation service unavailable")
                req = AddWindObservation.Request()
                encoded = gmrf_request_values(200_000_000, (1.0, 1.0), (1.0, 0.0))
                for name, values in encoded["request"].items():
                    setattr(req, name, values)
                call(node, add, req)
            # Fixed bounded settling interval for this numerical interface test.
            end = time.monotonic() + 2.0
            while time.monotonic() < end:
                rclpy.spin_once(node, timeout_sec=.05)
            response = call(node, query, request)
            return {"case": case, "requested_downwind_uv": [1., 0.],
                    "intended_sensor_xy": [1., 1.],
                    "query_x": list(request.x), "query_y": list(request.y),
                    "baseline_u": list(baseline.u), "baseline_v": list(baseline.v),
                    "u": list(response.u), "v": list(response.v),
                    "var_u": list(response.var_u), "var_v": list(response.var_v),
                    "command": command, "log": str(log_path)}
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()  # only this script's child
                process.wait(timeout=5.0)
        node.destroy_node()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("ROS_DOMAIN_ID") != "193" or os.environ.get("ROS_LOCALHOST_ONLY") != "1":
        raise RuntimeError("run only in the dedicated localhost-only probe domain 193")
    if args.output.exists():
        raise FileExistsError(args.output)
    directory = Path(tempfile.mkdtemp(prefix="ctpi-v2-gmrf-contract-"))
    rclpy.init()
    try:
        cases = [run_case(case, directory) for case in ("legacy_map_message", "explicit_downwind_service")]
    finally:
        rclpy.shutdown()
    report = {"status": "BINARY_INTERFACE_DIAGNOSTIC_ONLY", "cases": cases,
              "binary_sha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
              "core_library_sha256": hashlib.sha256((BINARY.parents[1]/"libgmrf_wind_core.so").read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "adapter_sha256": hashlib.sha256((Path(__file__).resolve().parents[1]/"closed_loop/ctpi/ctpi_v2_wind_observation.py").read_bytes()).hexdigest(),
              "ros_domain_id": os.environ.get("ROS_DOMAIN_ID"),
              "limitations": ["No immutable R4 binary hash was recovered; current binary behavior is not full historical identity proof.",
                              "Not a wind prediction or uncertainty calibration gate.",
                              "The two paths use different observation variances in the implementation; vector magnitudes are not a controlled utility comparison.",
                              "Map-frame TF implies origin position in the source callback; response magnitudes alone do not prove where an observation was inserted."]}
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({"output": str(args.output), "cases": [{"case": c["case"], "u": c["u"], "v": c["v"]} for c in cases]}))


if __name__ == "__main__":
    main()
