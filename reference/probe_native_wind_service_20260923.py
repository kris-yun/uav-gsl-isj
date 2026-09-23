#!/usr/bin/env python3
"""Source-blind /wind_value shape and finite-response preflight."""

import argparse
import json
import math
import time

import rclpy
from gaden_msgs.srv import WindPosition


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", type=float, required=True, help="predeclared robot start x")
    ap.add_argument("--y", type=float, required=True, help="predeclared robot start y")
    ap.add_argument("--z", type=float, default=0.3)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    points = [(args.x, args.y), (args.x + 0.3, args.y),
              (args.x, args.y + 0.3), (args.x - 0.3, args.y),
              (args.x, args.y - 0.3)]
    rclpy.init()
    node = rclpy.create_node("native_recovery_wind_preflight")
    client = node.create_client(WindPosition, "/wind_value")
    if not client.wait_for_service(timeout_sec=15.0):
        raise RuntimeError("/wind_value unavailable")
    request = WindPosition.Request()
    request.x = [x for x, _ in points]
    request.y = [y for _, y in points]
    request.z = [args.z] * len(points)
    future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future, timeout_sec=15.0)
    response = future.result()
    if response is None or any(len(getattr(response, component)) != len(points) for component in ("u", "v", "w")):
        raise RuntimeError("/wind_value returned no response or wrong vector lengths")
    rows = []
    for i, (x, y) in enumerate(points):
        u, v, w = response.u[i], response.v[i], response.w[i]
        if not all(math.isfinite(t) for t in (u, v, w)):
            raise RuntimeError("/wind_value returned nonfinite wind")
        rows.append({"x": x, "y": y, "z": args.z, "u": u, "v": v, "w": w,
                     "magnitude_xy": math.hypot(u, v)})
    if not any(row["magnitude_xy"] > 1e-8 for row in rows):
        raise RuntimeError("all source-blind wind probes are zero; possible empty VGR wind data")
    with open(args.output, "w", encoding="utf-8") as stream:
        json.dump({"service": "/wind_value", "type": "gaden_msgs/srv/WindPosition",
                   "probe_basis": "robot start and four fixed 0.3 m offsets; no source truth",
                   "wall_time_unix": time.time(), "rows": rows}, stream, indent=2)
        stream.write("\n")
    node.destroy_node()
    rclpy.shutdown()
    print("NATIVE_RECOVERY_WIND_SERVICE_PROBE_PASS")


if __name__ == "__main__":
    main()
