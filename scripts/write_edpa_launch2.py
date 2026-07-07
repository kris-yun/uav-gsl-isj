#!/usr/bin/env python3
"""Write proper EDPA-GSL launch file matching existing format"""
content = '''from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def _int(name):
    return ParameterValue(LaunchConfiguration(name), value_type=int)
def _bool(name):
    return ParameterValue(LaunchConfiguration(name), value_type=bool)
def _float(name):
    return ParameterValue(LaunchConfiguration(name), value_type=float)

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("vgr_data_path", default_value="/home/zyc/enva_vgr"),
        DeclareLaunchArgument("config_id", default_value="1,3-2,4_fast"),
        DeclareLaunchArgument("algorithm", default_value="OPGSL"),
        DeclareLaunchArgument("method", default_value="M7_edpa"),
        DeclareLaunchArgument("source_x", default_value="-0.60"),
        DeclareLaunchArgument("source_y", default_value="1.95"),
        DeclareLaunchArgument("source_z", default_value="0.40"),
        DeclareLaunchArgument("start_x", default_value="-0.9"),
        DeclareLaunchArgument("start_y", default_value="0.15"),
        DeclareLaunchArgument("seed", default_value="0"),
        DeclareLaunchArgument("timeout_sec", default_value="300.0"),
        DeclareLaunchArgument("resultsFile", default_value="/tmp/edpa_results.csv"),
        # EDPA parameters
        DeclareLaunchArgument("edpa_lambda0", default_value="1.0"),
        DeclareLaunchArgument("edpa_ell", default_value="2.0"),
        DeclareLaunchArgument("edpa_alphaw", default_value="0.5"),
        DeclareLaunchArgument("edpa_stop_epsilon", default_value="1.5"),
        DeclareLaunchArgument("edpa_stop_delta", default_value="0.10"),
        DeclareLaunchArgument("edpa_stop_eta", default_value="5.0"),
        DeclareLaunchArgument("detection_threshold", default_value="0.01"),
        Node(package="vgr_bridge", executable="vgr_sim_node", name="vgr_uav_sim", output="screen",
            parameters=[{
                "vgr_data_path": LaunchConfiguration("vgr_data_path"),
                "config_id": LaunchConfiguration("config_id"),
                "flight_height": 0.3,
                "start_x": _float("start_x"),
                "start_y": _float("start_y"),
                "seed": _int("seed"),
            }]),
        Node(package="gsl_server", executable="gsl_actionserver_node", name="gsl_server", output="screen",
            parameters=[{
                "use_sim_time": False,
                "maxSearchTime": _float("timeout_sec"),
                "distanceThreshold": -1.0,
                "resultsFile": LaunchConfiguration("resultsFile"),
                "ground_truth_x": _float("source_x"),
                "ground_truth_y": _float("source_y"),
                "opgsl.seed": _int("seed"),
                # EDPA-GSL mode
                "opgsl.modules.edpa": True,
                "opgsl.edpa.detection_threshold": _float("detection_threshold"),
                "opgsl.edpa.lambda0": _float("edpa_lambda0"),
                "opgsl.edpa.ell": _float("edpa_ell"),
                "opgsl.edpa.alphaw": _float("edpa_alphaw"),
                "opgsl.edpa.stop_epsilon": _float("edpa_stop_epsilon"),
                "opgsl.edpa.stop_delta": _float("edpa_stop_delta"),
                "opgsl.edpa.stop_eta": _float("edpa_stop_eta"),
                # Disable non-EDPA modules
                "opgsl.modules.sbd": False,
                "opgsl.modules.ddm": False,
                "opgsl.modules.cp": False,
                "opgsl.modules.wraig": False,
                "opgsl.modules.upwind_tracking": False,
                "opgsl.modules.levy": True,
                "opgsl.modules.bout": True,
                "opgsl.modules.adaptive_step": True,
                "opgsl.sdnbv.enabled": True,
                "opgsl.convergence.min_time": 30.0,
            }]),
        TimerAction(period=5.0, actions=[
            Node(package="vgr_bridge", executable="gsl_benchmark_runner", name="benchmark", output="screen",
                parameters=[{
                    "algorithm": LaunchConfiguration("algorithm"),
                    "method": LaunchConfiguration("method"),
                    "source_x": _float("source_x"),
                    "source_y": _float("source_y"),
                    "seed": _int("seed"),
                    "time_budget_s": _float("timeout_sec"),
                    "repo_root": "/home/zyc/gsl_ws/src/GasSourceLocalization",
                    "output_csv": LaunchConfiguration("resultsFile"),
                }]),
        ]),
    ])
'''

path = "/home/zyc/gsl_ws/src/vgr_bridge/launch/vgr_edpa.launch.py"
with open(path, "w") as f:
    f.write(content)
print("Written: " + path)
