"""Real DDS/ROS message test, not a House/plume experiment. No truth input.

Launch only inside a dedicated ROS_DOMAIN_ID with ROS_LOCALHOST_ONLY=1. Creates
isolated topic names and one child ingress process, never starts a simulator.
"""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingress", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("ROS_DOMAIN_ID") or os.environ.get("ROS_LOCALHOST_ONLY") != "1":
        raise RuntimeError("isolated ROS domain and localhost-only are required")
    if args.result.exists():
        raise FileExistsError(args.result)
    import rclpy
    from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from olfaction_msgs.msg import GasSensor, Anemometer
    from std_msgs.msg import Bool

    # Keep each probe's artifacts for audit; no recursive deletion.
    run = Path(tempfile.mkdtemp(prefix="ctpi-v2-ingress-"))
    audit = run / "frames.jsonl"
    prefix = "/ctpi_v2_contract_probe"
    rclpy.init()
    node = rclpy.create_node("ctpi_v2_contract_probe")
    pose_pub = node.create_publisher(PoseWithCovarianceStamped, prefix + "/pose", 10)
    gas_pub = node.create_publisher(GasSensor, prefix + "/gas", 10)
    wind_pub = node.create_publisher(Anemometer, prefix + "/wind", 10)
    ready = []
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     reliability=ReliabilityPolicy.RELIABLE)
    ready_sub = node.create_subscription(Bool, "/ctpi_v2_ingress_ready",
                                         lambda msg: ready.append(msg.data), qos)
    command = [sys.executable, str(args.ingress), "--output", str(audit),
               "--pose-topic", prefix + "/pose", "--gas-topic", prefix + "/gas",
               "--wind-topic", prefix + "/wind", "--final-stamp-ns", "600000000"]
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    deadline = time.monotonic() + 20.0  # diagnostic wall timeout, not research gate
    try:
        while min(pose_pub.get_subscription_count(), gas_pub.get_subscription_count(),
                  wind_pub.get_subscription_count()) == 0:
            if time.monotonic() > deadline or child.poll() is not None:
                raise RuntimeError("ingress discovery failed")
            rclpy.spin_once(node, timeout_sec=.05)

        def publish(index):
            pose, gas, wind = PoseWithCovarianceStamped(), GasSensor(), Anemometer()
            for msg in (pose, gas, wind):
                msg.header.stamp.nanosec = index * 200_000_000
                msg.header.frame_id = "map"
            pose.pose.pose.position.x = float(index)
            pose.pose.pose.position.y = -float(index)
            gas.raw_units, gas.raw = GasSensor.UNITS_PPM, float(index)
            wind.wind_speed, wind.wind_direction = .25, 0.0
            # Deliberately different callback arrival order; join must use stamps.
            wind_pub.publish(wind)
            gas_pub.publish(gas)
            pose_pub.publish(pose)

        publish(0)
        while True not in ready:
            if time.monotonic() > deadline or child.poll() is not None:
                raise RuntimeError("zero-frame handshake failed")
            rclpy.spin_once(node, timeout_sec=.05)
        for i in range(1, 4):
            publish(i)
            if i == 1:
                publish(i)  # VGR repeats identical messages during planner pause.
        stdout, _ = child.communicate(timeout=max(.1, deadline - time.monotonic()))
        if child.returncode:
            raise RuntimeError(stdout)
        entries = [json.loads(line) for line in audit.read_text().splitlines()]
        frames = [item for item in entries if item["event"] == "frame"]
        assert len(frames) == 4 and entries[-1]["event"] == "complete", entries
        assert entries[-1]["identical_repeats_ignored"] == 3, entries
        for i, f in enumerate(frames):
            assert f["stamp_ns"] == i * 200_000_000
            assert f["pose_xy"] == [float(i), -float(i)]
            assert f["gas_ppm"] == float(i)
            assert math.isclose(f["wind_uv"][0], .25) and f["wind_uv"][1] == 0
        result = {"status": "ROS_INGRESS_PROBE_PASS_NOT_CLOSED_LOOP",
                  "frames": len(frames), "zero_handshake": True,
                  "positive_stamp_repeats_ignored": 3,
                  "audit_path": str(audit), "ros_domain_id": os.environ["ROS_DOMAIN_ID"],
                  "scope": "DDS transport and aligned ingress only; no predictor/controller/House"}
        with args.result.open("x", encoding="utf-8") as out:
            json.dump(result, out, indent=2)
        print(json.dumps(result))
    finally:
        if child.poll() is None:
            child.terminate()  # only this probe's owned child
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)
        node.destroy_subscription(ready_sub)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
