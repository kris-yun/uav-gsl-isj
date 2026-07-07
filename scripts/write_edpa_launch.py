#!/usr/bin/env python3
"""Create EDPA-GSL launch file for PMFS scenario A experiments"""
launch = """#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    scenario = os.path.join(
        get_package_share_directory("pmfs_env"), "scenarios", "A", "A1_fast"
    )
    return LaunchDescription([
        Node(
            package="gsl_server",
            executable="gsl_server_node",
            name="gsl_node",
            parameters=[{
                "algorithm": "opgsl",
                "scenario": scenario,
                "opgsl.grid.n_cells": 40,
                "opgsl.grid.resolution": 0.5,
                "opgsl.modules.edpa": True,
                "opgsl.edpa.detection_threshold": 0.01,
                "opgsl.edpa.lambda0": 1.0,
                "opgsl.edpa.ell": 2.0,
                "opgsl.edpa.alphaw": 0.5,
                "opgsl.edpa.stop_epsilon": 1.5,
                "opgsl.edpa.stop_delta": 0.10,
                "opgsl.edpa.stop_eta": 5.0,
                "opgsl.convergence.entropy_threshold": 4.0,
                "opgsl.convergence.min_bouts": 5,
                "opgsl.convergence.stable_steps": 5,
                "opgsl.convergence.min_time": 30.0,
                "opgsl.modules.cp": False,
                "opgsl.modules.ddm": False,
                "opgsl.modules.sbd": False,
                "opgsl.modules.upwind_tracking": False,
            }],
        ),
        Node(
            package="vgr_bridge",
            executable="vgr_sim_node",
            name="vgr_sim",
            parameters=[{
                "scenario": scenario,
                "playback_speed": 0.0,
                "loop": False,
            }],
        ),
    ])
"""

path = "/home/zyc/gsl_ws/src/vgr_bridge/launch/vgr_edpa.launch.py"
with open(path, "w") as f:
    f.write(launch)
print("Written: " + path)
