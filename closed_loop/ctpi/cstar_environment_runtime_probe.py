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

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ctpi_v2_ingress import StampedIngress
from cstar_local_wind import decode_local_downwind, DIRECTION_CONVENTION, UNITS

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
    args, ros_args = ap.parse_known_args()
    if args.required_aligned_frames < 2:
        ap.error("required-aligned-frames must be >=2")

    map_yaml = args.map_yaml.resolve()
    map_image = args.map_image.resolve()
    if not map_yaml.is_file() or not map_image.is_file():
        raise RuntimeError("CSTAR_ENV_PROBE_MAP_FILE_MISSING")
    if map_yaml_image(map_yaml) != map_image:
        raise RuntimeError(
            f"CSTAR_ENV_PROBE_YAML_IMAGE_MISMATCH:{map_yaml_image(map_yaml)}:{map_image}"
        )

    ingress_code = HERE / "ctpi_v2_ingress.py"
    wind_code = HERE / "cstar_local_wind.py"
    ingress = StampedIngress(cadence_ns=CADENCE_NS)
    aligned = []
    invalid = []

    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from olfaction_msgs.msg import GasSensor, Anemometer

    rclpy.init(args=ros_args)

    class Probe(Node):
        def __init__(self):
            super().__init__(f"cstar_environment_probe_{args.house.lower()}")
            self.subs = [
                self.create_subscription(PoseWithCovarianceStamped, args.pose_topic, self.pose, 100),
                self.create_subscription(GasSensor, args.gas_topic, self.gas, 100),
                self.create_subscription(Anemometer, args.wind_topic, self.wind, 100),
            ]

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
    try:
        while rclpy.ok() and len(aligned) < args.required_aligned_frames:
            rclpy.spin_once(node, timeout_sec=1.0)
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
        for fr in aligned:
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
