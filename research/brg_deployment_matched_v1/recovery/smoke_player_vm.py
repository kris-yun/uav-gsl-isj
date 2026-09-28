"""Query start/middle/end of one archived OPEN native GADEN realization."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import signal
import subprocess

import rclpy
from gaden_msgs.srv import FrameQuery


ROOT = Path("/home/zyc/brg_v1_recovery_smoke_20260928")
RUN = ROOT / "House01_1,3-2,4_fast_pmfs_13_18_seed123404979"
OCC = Path("/mnt/hgfs/workspace/GADEN_files/scenarios/House01/OccupancyGrid3D.csv")


def main() -> None:
    meta = json.loads((RUN / "RUN_METADATA.json").read_text())
    if meta["raw_frames"] != 566 or not (RUN / "realization" / "iteration_565").is_file():
        raise RuntimeError("native realization incomplete")
    if int(os.getenv("ROS_DOMAIN_ID", "0")) not in range(220, 230):
        raise RuntimeError("isolated ROS_DOMAIN_ID 220..229 required")
    log = (ROOT / "player_smoke.log").open("w")
    args = ["ros2", "run", "gaden_player", "player", "--ros-args",
            "-p", "num_simulators:=1", "-p", f"simulation_data_0:={RUN / 'realization'}",
            "-p", f"occupancyFile:={OCC}", "-p", "initial_iteration:=0",
            "-p", "manual_iteration_mode:=true", "-p", "allow_looping:=false"]
    player = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT,
                              start_new_session=True)
    client_node = None
    try:
        rclpy.init()
        client_node = rclpy.create_node("brg_v1_archived_frame_smoke")
        client = client_node.create_client(FrameQuery, "frame_query")
        if not client.wait_for_service(timeout_sec=25.0):
            raise RuntimeError("GADEN /frame_query did not start")
        source_x, source_y, source_z = meta["source_xyz"]
        records = []
        for frame in (0, 1, 300, 565):
            request = FrameQuery.Request()
            request.iteration = frame
            request.x, request.y, request.z = source_x, source_y, source_z
            future = client.call_async(request)
            rclpy.spin_until_future_complete(client_node, future, timeout_sec=10.0)
            response = future.result() if future.done() else None
            if response is None or not response.valid:
                reason = response.error_message if response else "timeout"
                raise RuntimeError(f"frame {frame} query invalid: {reason}")
            if not all(map(math.isfinite, (response.concentration, response.wind_u,
                                            response.wind_v, response.wind_w))):
                raise RuntimeError(f"frame {frame} query nonfinite")
            records.append({"frame": frame, "valid": True, "finite_gas_and_wind": True})
        result = {"status": "ARCHIVED_NATIVE_ROS_QUERY_PASS", "run_id": meta["run_id"],
                  "frames_checked": records, "mode": "manual_iteration_mode"}
        (ROOT / "PLAYER_SMOKE_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
    finally:
        if client_node is not None:
            client_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        os.killpg(player.pid, signal.SIGTERM)
        try:
            player.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(player.pid, signal.SIGKILL)
            player.wait()
        log.close()


if __name__ == "__main__":
    main()
