"""Real DDS/ROS probe for the M2 callback bridge.

This is an isolated transport/wiring test only. It publishes synthetic topic
messages, uses the real message types and stamps, and never starts a House or
controller. A route is explicitly armed between frames to verify the online
prediction-before-observation contract.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bridge", type=Path, required=True)
    ap.add_argument("--prior", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    args = ap.parse_args()
    if not os.environ.get("ROS_DOMAIN_ID") or os.environ.get("ROS_LOCALHOST_ONLY") != "1":
        raise RuntimeError("isolated ROS domain and localhost-only are required")
    if args.result.exists():
        raise FileExistsError(args.result)
    import sys
    sys.path.insert(0, str(args.bridge.parent))
    sys.path.insert(0, str(args.prior.parent.parent))
    from cstar_m2_ros_bridge import CstarM2RosBridge
    from m2_cpo.physical_prior import PhysicalCPOProvider, PhysicalPriorConfig
    import rclpy
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from olfaction_msgs.msg import GasSensor, Anemometer

    cfg = PhysicalPriorConfig(nx=8, ny=2, dx=1.0, diffusion=.05,
                              free=tuple(True for _ in range(16)))
    bridge = CstarM2RosBridge(PhysicalCPOProvider(cfg))
    rclpy.init()
    node = rclpy.create_node("cstar_m2_ros_bridge_probe")
    prefix = "/cstar_m2_bridge_probe"
    pose_pub = node.create_publisher(PoseWithCovarianceStamped, prefix + "/pose", 10)
    gas_pub = node.create_publisher(GasSensor, prefix + "/gas", 10)
    wind_pub = node.create_publisher(Anemometer, prefix + "/wind", 10)
    received = []

    def stamp(msg, index):
        msg.header.stamp.sec = 0
        msg.header.stamp.nanosec = index * 200_000_000
        msg.header.frame_id = "map"

    def pose_cb(msg):
        if msg.header.frame_id != "map":
            raise RuntimeError("POSE_FRAME")
        stamp_ns = msg.header.stamp.nanosec
        received.append(bridge.push_normalized("pose", stamp_ns,
                       (msg.pose.pose.position.x, msg.pose.pose.position.y)))

    def gas_cb(msg):
        if msg.raw_units != GasSensor.UNITS_PPM:
            raise RuntimeError("GAS_UNITS")
        stamp_ns = msg.header.stamp.nanosec
        received.append(bridge.push_normalized("gas", stamp_ns, (msg.raw,)))

    def wind_cb(msg):
        stamp_ns = msg.header.stamp.nanosec
        uv = (msg.wind_speed * math.cos(msg.wind_direction),
              msg.wind_speed * math.sin(msg.wind_direction))
        received.append(bridge.push_normalized("wind", stamp_ns, uv))

    node.create_subscription(PoseWithCovarianceStamped, prefix + "/pose", pose_cb, 10)
    node.create_subscription(GasSensor, prefix + "/gas", gas_cb, 10)
    node.create_subscription(Anemometer, prefix + "/wind", wind_cb, 10)
    deadline = time.monotonic() + 20.0

    def publish(index):
        p, g, w = PoseWithCovarianceStamped(), GasSensor(), Anemometer()
        for msg in (p, g, w): stamp(msg, index)
        p.pose.pose.position.x = float(index)
        p.pose.pose.position.y = 0.0
        g.raw_units, g.raw = GasSensor.UNITS_PPM, float(index) * .1
        w.wind_speed, w.wind_direction = 1.0, 0.0
        # Deliberately scrambled publisher order.
        wind_pub.publish(w); gas_pub.publish(g); pose_pub.publish(p)

    try:
        while min(pose_pub.get_subscription_count(), gas_pub.get_subscription_count(),
                  wind_pub.get_subscription_count()) == 0:
            if time.monotonic() > deadline: raise RuntimeError("DISCOVERY")
            rclpy.spin_once(node, timeout_sec=.05)
        publish(0)
        while not bridge.ready:
            if time.monotonic() > deadline: raise RuntimeError("BOOTSTRAP")
            rclpy.spin_once(node, timeout_sec=.05)
        bridge.arm_route((0.0, 0.0), ((1.0, 0.0), (2.0, 0.0)))
        publish(1)
        while bridge.stats.observations < 1:
            if time.monotonic() > deadline: raise RuntimeError("FRAME1")
            rclpy.spin_once(node, timeout_sec=.05)
        bridge.arm_route((0.0, 0.0), ((1.0, 0.0), (2.0, 0.0)))
        publish(2)
        while bridge.stats.observations < 2:
            if time.monotonic() > deadline: raise RuntimeError("FRAME2")
            rclpy.spin_once(node, timeout_sec=.05)
        bridge.finish(400_000_000)
        result = {"status": "ROS_M2_BRIDGE_WIRING_PASS_NOT_CLOSED_LOOP",
                  "joined_frames": bridge.stats.joined_frames,
                  "predictions": bridge.stats.predictions,
                  "observations": bridge.stats.observations,
                  "scope": "real DDS callbacks plus physical-prior provider; no House/controller"}
        args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
