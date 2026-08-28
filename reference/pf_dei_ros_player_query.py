#!/usr/bin/env python3
"""Query the native ROS GADEN player at a frozen synthetic schedule."""

from __future__ import annotations

import csv
import sys

import rclpy
from gaden_msgs.srv import FrameQuery


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: pf_dei_ros_player_query.py SCHEDULE_CSV OUTPUT_CSV")
    schedule_path, output_path = sys.argv[1:]
    with open(schedule_path, newline="", encoding="utf-8") as handle:
        schedule = list(csv.DictReader(handle))

    rclpy.init()
    node = rclpy.create_node("pf_dei_frame_query_client")
    client = node.create_client(FrameQuery, "/pfdei/frame_query")
    if not client.wait_for_service(timeout_sec=30.0):
        raise RuntimeError("PF_DEI_FRAME_QUERY_SERVICE_TIMEOUT")

    rows: list[dict[str, object]] = []
    try:
        for item in schedule:
            request = FrameQuery.Request()
            request.iteration = int(item["iteration"])
            request.x = float(item["x"])
            request.y = float(item["y"])
            request.z = float(item["z"])
            future = client.call_async(request)
            rclpy.spin_until_future_complete(node, future, timeout_sec=10.0)
            response = future.result()
            if response is None:
                raise RuntimeError(f"PF_DEI_FRAME_QUERY_NO_RESPONSE={item['sample_id']}")
            if not response.valid:
                raise RuntimeError(
                    f"PF_DEI_FRAME_QUERY_INVALID={item['sample_id']}:{response.error_message}"
                )
            rows.append(
                {
                    **item,
                    "concentration_ppm": format(response.concentration, ".17g"),
                    "wind_u": format(response.wind_u, ".17g"),
                    "wind_v": format(response.wind_v, ".17g"),
                    "wind_w": format(response.wind_w, ".17g"),
                }
            )
    finally:
        node.destroy_node()
        rclpy.shutdown()

    fieldnames = [
        "sample_id", "sample_time_s", "iteration", "x", "y", "z", "concentration_ppm",
        "wind_u", "wind_v", "wind_w",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"PF_DEI_ROS_PLAYER_QUERY_PASS samples={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
