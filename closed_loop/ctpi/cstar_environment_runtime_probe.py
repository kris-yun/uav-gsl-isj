#!/usr/bin/env python3
"""Short CSTAR environment probe; no source model and no GMRF dependency.

Run this against each House's normal simulator/navigation topics before formal
M1/M2 data work.  It loads the declared navigation-height map, joins stamped
pose/gas/local-wind with the same strict ingress contract, records actual wind
observation positions, and emits CSTAR_RUNTIME_INPUT_LOAD_AUDIT_V1.

This is environment evidence only.  It does not authorize a scientific gate or
a closed-loop performance run.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ctpi_v2_ingress import StampedIngress
from cstar_local_wind import decode_local_downwind, DIRECTION_CONVENTION, UNITS
sys.path.insert(0, str(HERE.parents[1] / "experiments" / "ctpi_cstar"))
from validate_environment_alignment_v2 import parse_map_yaml, read_pgm, p_occ

CADENCE_NS = 200_000_000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def map_yaml_image(yaml_path: Path) -> Path:
    image = None
    for raw in yaml_path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("image:"):
            image = line.split(":", 1)[1].strip().strip("\"'")
            break
    if not image:
        raise RuntimeError(f"CSTAR_ENV_PROBE_MAP_IMAGE_FIELD:{yaml_path}")
    p = Path(image)
    return (p if p.is_absolute() else yaml_path.parent / p).resolve()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--house", required=True, choices=("H01", "H02", "H03"))
    ap.add_argument("--geometry-identity", required=True)
    ap.add_argument("--git-sha", required=True)
    ap.add_argument("--map-yaml", type=Path, required=True)
    ap.add_argument("--map-image", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--wind-position-csv", type=Path, required=True)
    ap.add_argument("--frame-jsonl", type=Path, required=True)
    ap.add_argument("--pose-topic", default="/amcl_pose")
    ap.add_argument("--gas-topic", default="/PID/Sensor_reading")
    ap.add_argument("--wind-topic", default="/Anemometer/WindSensor_reading")
    ap.add_argument("--required-aligned-frames", type=int, default=8)
    ap.add_argument("--wall-timeout-s", type=float, default=40.0)
    ap.add_argument("--start-simulation", action="store_true",
                    help="Release this isolated simulator only after t=0 and map parity")
    args, ros_args = ap.parse_known_args()
    if args.required_aligned_frames < 8 or not 0 < args.wall_timeout_s <= 60:
        ap.error("need >=8 positive frames and 0 < wall timeout <=60 s")
    for output in (args.output, args.wind_position_csv, args.frame_jsonl):
        if output.exists():
            raise FileExistsError(output)

    map_yaml = args.map_yaml.resolve()
    map_image = args.map_image.resolve()
    if not map_yaml.is_file() or not map_image.is_file():
        raise RuntimeError("CSTAR_ENV_PROBE_MAP_FILE_MISSING")
    if map_yaml_image(map_yaml) != map_image:
        raise RuntimeError(
            f"CSTAR_ENV_PROBE_YAML_IMAGE_MISMATCH:{map_yaml_image(map_yaml)}:{map_image}"
        )
    geometry = parse_map_yaml(map_yaml)
    width, height, maxval, pixels = read_pgm(map_image)
    expected_grid = [0 if p_occ(pixels[(height-1-r)*width+c], maxval, geometry["negate"])
                     < geometry["free_thresh"] else 100
                     for r in range(height) for c in range(width)]

    ingress_code = HERE / "ctpi_v2_ingress.py"
    wind_code = HERE / "cstar_local_wind.py"
    ingress = StampedIngress(cadence_ns=CADENCE_NS)
    aligned = []
    invalid = []

    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from olfaction_msgs.msg import GasSensor, Anemometer
    from nav_msgs.msg import OccupancyGrid
    from rclpy.qos import QoSProfile, DurabilityPolicy
    from std_srvs.srv import Trigger

    rclpy.init(args=ros_args)

    class Probe(Node):
        def __init__(self):
            super().__init__(f"cstar_environment_probe_{args.house.lower()}")
            self.subs = [
                self.create_subscription(PoseWithCovarianceStamped, args.pose_topic, self.pose, 100),
                self.create_subscription(GasSensor, args.gas_topic, self.gas, 100),
                self.create_subscription(Anemometer, args.wind_topic, self.wind, 100),
            ]
            self.map_parity = False
            self.start_future = None
            self.start_client = self.create_client(Trigger, "/start_simulation")
            self.subs.append(self.create_subscription(OccupancyGrid, "/map", self.map,
                QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)))

        def map(self, msg):
            origin = msg.info.origin
            if not (msg.header.frame_id == "map" and msg.info.width == width
                    and msg.info.height == height
                    and abs(msg.info.resolution-geometry["resolution"]) < 1e-7
                    and abs(origin.position.x-geometry["origin"][0]) < 1e-7
                    and abs(origin.position.y-geometry["origin"][1]) < 1e-7
                    and abs(origin.orientation.x) < 1e-7 and abs(origin.orientation.y) < 1e-7
                    and abs(origin.orientation.z) < 1e-7 and abs(abs(origin.orientation.w)-1) < 1e-7
                    and list(msg.data) == expected_grid):
                raise RuntimeError("CSTAR_ENV_PROBE_RUNTIME_MAP_MISMATCH")
            self.map_parity = True

        def accept(self, kind, msg, values):
            stamp = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            try:
                frames = ingress.push(kind, stamp, values)
                aligned.extend(frames)
            except Exception as exc:
                invalid.append({"kind": kind, "stamp_ns": stamp, "error": str(exc)})
                raise

        def pose(self, msg):
            if msg.header.frame_id != "map":
                raise ValueError(f"CSTAR_ENV_PROBE_POSE_FRAME:{msg.header.frame_id}")
            self.accept("pose", msg, (msg.pose.pose.position.x, msg.pose.pose.position.y))

        def gas(self, msg):
            if msg.raw_units != GasSensor.UNITS_PPM:
                raise ValueError(f"CSTAR_ENV_PROBE_GAS_UNITS:{msg.raw_units}")
            self.accept("gas", msg, (msg.raw,))

        def wind(self, msg):
            uv = decode_local_downwind(msg.header.frame_id, msg.wind_speed, msg.wind_direction)
            self.accept("wind", msg, uv)

    node = Probe()
    deadline = time.monotonic() + args.wall_timeout_s
    try:
        while rclpy.ok() and (len(aligned) < args.required_aligned_frames+1 or not node.map_parity):
            if time.monotonic() >= deadline:
                raise RuntimeError(f"CSTAR_ENV_PROBE_WALL_TIMEOUT:frames={len(aligned)}:map={node.map_parity}")
            rclpy.spin_once(node, timeout_sec=0.1)
            if (args.start_simulation and ingress.ready and node.map_parity
                    and node.start_future is None and node.start_client.service_is_ready()):
                node.start_future = node.start_client.call_async(Trigger.Request())
            if node.start_future is not None and node.start_future.done():
                if not node.start_future.result().success:
                    raise RuntimeError("CSTAR_ENV_PROBE_START_REJECTED")
    except Exception as exc:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"contract": "CSTAR_RUNTIME_INPUT_LOAD_AUDIT_V1",
            "house": args.house, "pass": False, "error": str(exc),
            "aligned_frame_count": len(aligned), "runtime_map_parity": node.map_parity})+"\n")
        raise
    finally:
        node.destroy_node()
        rclpy.shutdown()

    if invalid:
        raise RuntimeError(f"CSTAR_ENV_PROBE_INVALID_STREAM:{invalid[:3]}")
    if len(aligned) < args.required_aligned_frames:
        raise RuntimeError(
            f"CSTAR_ENV_PROBE_INSUFFICIENT_ALIGNED_FRAMES:{len(aligned)}:{args.required_aligned_frames}"
        )
    if aligned[-1].stamp_ns <= 0:
        raise RuntimeError("CSTAR_ENV_PROBE_NO_POSITIVE_TIME_FRAME")

    args.wind_position_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.wind_position_csv.open("x", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stamp_ns", "x", "y", "wind_u", "wind_v"])
        for fr in aligned[1:]:  # t=0 is bootstrap state, never an observed wind sample
            w.writerow([fr.stamp_ns, fr.pose_xy[0], fr.pose_xy[1], fr.wind_uv[0], fr.wind_uv[1]])

    args.frame_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.frame_jsonl.open("x", encoding="utf-8") as f:
        for fr in aligned:
            f.write(json.dumps({
                "stamp_ns": fr.stamp_ns,
                "pose_xy": list(fr.pose_xy),
                "gas_ppm": fr.gas_ppm,
                "wind_uv": list(fr.wind_uv),
            }, allow_nan=False, sort_keys=True) + "\n")

    audit = {
        "contract": "CSTAR_RUNTIME_INPUT_LOAD_AUDIT_V1",
        "audit_scope": "environment_preflight_shared_loader_no_scientific_model",
        "house": args.house,
        "git_sha": args.git_sha,
        "geometry_identity": args.geometry_identity,
        "map_yaml_path": str(map_yaml),
        "map_yaml_sha256": sha256_file(map_yaml),
        "map_image_path": str(map_image),
        "map_image_sha256": sha256_file(map_image),
        "world_frame": "map",
        "pose_topic": args.pose_topic,
        "gas_topic": args.gas_topic,
        "wind_topic": args.wind_topic,
        "wind_direction_convention": DIRECTION_CONVENTION,
        "wind_vector_units": UNITS,
        "stamp_units": "ns",
        "cadence_ns": CADENCE_NS,
        "candidate_frame": "map",
        "route_frame": "map",
        "source_estimate_frame": "map",
        "ingress_code_sha256": sha256_file(ingress_code),
        "wind_adapter_code_sha256": sha256_file(wind_code),
        "loader_started_before_scientific_model": True,
        "old_native_gmrf_anemometer_subscription_used": False,
        "aligned_frame_count": len(aligned),
        "positive_observation_count": len(aligned)-1,
        "runtime_map_parity": node.map_parity,
        "runtime_map_topic": "/map",
        "runtime_map_data_sha256": hashlib.sha256(bytes(expected_grid)).hexdigest(),
        "runtime_probe_code_sha256": sha256_file(Path(__file__)),
        "first_stamp_ns": aligned[0].stamp_ns,
        "last_stamp_ns": aligned[-1].stamp_ns,
        "wind_position_csv_path": str(args.wind_position_csv.resolve()),
        "wind_position_csv_sha256": sha256_file(args.wind_position_csv),
        "frame_jsonl_path": str(args.frame_jsonl.resolve()),
        "frame_jsonl_sha256": sha256_file(args.frame_jsonl),
        "gmrf_required": False,
        "scientific_model_loaded": False,
        "pass": True,
        "verdict": "CSTAR_RUNTIME_INPUT_LOAD_AUDIT=PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(audit["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
