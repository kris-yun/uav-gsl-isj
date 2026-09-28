#!/usr/bin/env python3
"""Exercise the deployed VGR callback with ROS messages and the case 009 map."""
import asyncio
import hashlib
import json
import math
import time
from pathlib import Path
from types import MethodType, SimpleNamespace

import numpy as np
import rclpy
from builtin_interfaces.msg import Time
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path as RosPath
from nav2_msgs.action import ComputePathToPose
from rclpy.action import ActionClient, ActionServer
from rclpy.executors import MultiThreadedExecutor
from threading import Thread

from vgr_bridge.vgr_sim_node import VGRUAVSimNode
import vgr_bridge.vgr_sim_node as loaded


class Logger:
    def info(self, value):
        pass

    def warn(self, value):
        pass


class GoalHandle:
    def __init__(self, x, y):
        goal = PoseStamped()
        goal.pose.position.x = float(x)
        goal.pose.position.y = float(y)
        self.request = SimpleNamespace(goal=goal)
        self.did_succeed = False

    def succeed(self):
        self.did_succeed = True


def action_rpc_check(node, destination, blocked):
    rclpy.init()
    server_node = rclpy.create_node('brg_navfix_path_smoke_server')
    client_node = rclpy.create_node('brg_navfix_path_smoke_client')
    executor = MultiThreadedExecutor(num_threads=2)
    async def execute_callback(handle):
        return await VGRUAVSimNode._plan_callback(node, handle)
    action_server = ActionServer(
        server_node, ComputePathToPose, 'compute_path_to_pose',
        execute_callback=execute_callback,
    )
    client = ActionClient(client_node, ComputePathToPose, 'compute_path_to_pose')
    executor.add_node(server_node)
    executor.add_node(client_node)
    worker = Thread(target=executor.spin, daemon=True)
    worker.start()

    def await_future(future):
        deadline = time.monotonic() + 15
        while not future.done() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert future.done(), 'ComputePathToPose action timeout'
        return future.result()

    def query(xy):
        goal = ComputePathToPose.Goal()
        goal.goal.header.frame_id = 'map'
        goal.goal.pose.position.x = float(xy[0])
        goal.goal.pose.position.y = float(xy[1])
        goal.goal.pose.orientation.w = 1.0
        handle = await_future(client.send_goal_async(goal))
        assert handle.accepted
        return await_future(handle.get_result_async()).result.path

    try:
        assert client.wait_for_server(timeout_sec=10)
        good = query(destination)
        bad = query(blocked)
        assert isinstance(good, RosPath) and good.header.frame_id == 'map' and good.poses
        endpoint = good.poses[-1].pose.position
        assert math.hypot(endpoint.x-destination[0], endpoint.y-destination[1]) < 1e-10
        assert isinstance(bad, RosPath) and bad.header.frame_id == 'map' and not bad.poses
        return len(good.poses), [endpoint.x, endpoint.y], len(bad.poses)
    finally:
        executor.shutdown()
        worker.join(timeout=5)
        client.destroy()
        action_server.destroy()
        client_node.destroy_node()
        server_node.destroy_node()
        rclpy.shutdown()


def main():
    freeze = json.loads(Path('/home/zyc/brg_v1_recovery_20260928/PILOT_EVAL_FREEZE.json').read_text())
    case_path = Path('/home/zyc/brg_v1_recovery_20260928') / freeze['cases'][0]['case_file']
    case = json.loads(case_path.read_text())
    node = SimpleNamespace(
        vgr_path=case['scenario_root'], flight_height=0.2,
        environment_id='VGR_House01', nav_reduce_scale=3,
        get_logger=lambda: Logger(), _sim_stamp=lambda: Time(),
    )
    for name in ('_is_position_free', '_bfs_path'):
        setattr(node, name, MethodType(getattr(VGRUAVSimNode, name), node))
    VGRUAVSimNode._load_occupancy(node)
    VGRUAVSimNode._build_coarse_navigation_grid(node)
    node.uav_pos = np.array([*case['start_xy'], 0.2], dtype=float)
    assert node._is_position_free(*node.uav_pos[:2]), 'frozen start is not navigable'
    start = tuple(node.uav_pos[:2])
    destination = None
    for radius in range(1, 10):
        for ix in range(node.nav_nx):
            for iy in range(node.nav_ny):
                if node.nav_occ[ix, iy] != 0:
                    continue
                x = node.nav_env_min[0] + (ix + 0.5) * node.nav_cell_size
                y = node.nav_env_min[1] + (iy + 0.5) * node.nav_cell_size
                if not (radius - 1 < math.hypot(x-start[0], y-start[1]) <= radius):
                    continue
                if node._bfs_path(start, (x, y)):
                    destination = (x, y)
                    break
            if destination is not None:
                break
        if destination is not None:
            break
    assert destination is not None and math.hypot(*destination) > 0.1
    reachable = GoalHandle(*destination)
    good = asyncio.run(VGRUAVSimNode._plan_callback(node, reachable))
    assert reachable.did_succeed and isinstance(good.path, RosPath)
    assert good.path.header.frame_id == 'map' and good.path.poses
    endpoint = good.path.poses[-1].pose.position
    assert math.hypot(endpoint.x-destination[0], endpoint.y-destination[1]) < 1e-10
    blocked = GoalHandle(float(node.env_min[0])-10, float(node.env_min[1])-10)
    bad = asyncio.run(VGRUAVSimNode._plan_callback(node, blocked))
    assert blocked.did_succeed and isinstance(bad.path, RosPath)
    assert bad.path.header.frame_id == 'map' and not bad.path.poses
    rpc_poses, rpc_endpoint, rpc_blocked_poses = action_rpc_check(
        node, destination, (float(node.env_min[0])-10, float(node.env_min[1])-10)
    )
    print(json.dumps({
        'status': 'LIVE_ROS_ACTION_AND_REAL_MAP_PATH_PASS',
        'module_file': loaded.__file__,
        'module_sha256': hashlib.sha256(Path(loaded.__file__).read_bytes()).hexdigest(),
        'occupancy_file': str(Path(case['scenario_root']) / 'OccupancyGrid3D.csv'),
        'start_xy': start, 'reachable_goal_xy': destination,
        'path_poses': len(good.path.poses),
        'last_pose_xy': [endpoint.x, endpoint.y],
        'unreachable_path_poses': len(bad.path.poses),
        'rpc_path_poses': rpc_poses,
        'rpc_last_pose_xy': rpc_endpoint,
        'rpc_unreachable_path_poses': rpc_blocked_poses,
    }, indent=2))


if __name__ == '__main__':
    main()
