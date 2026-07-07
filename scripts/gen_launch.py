#!/usr/bin/env python3
# Fix the EDPA launch file
content = "from launch import LaunchDescription\n"
content += "from launch.actions import DeclareLaunchArgument, TimerAction\n"
content += "from launch.substitutions import LaunchConfiguration\n"
content += "from launch_ros.actions import Node\n"
content += "from launch_ros.parameter_descriptions import ParameterValue\n\n"
content += "def _int(name):\n    return ParameterValue(LaunchConfiguration(name), value_type=int)\n"
content += "def _bool(name):\n    return ParameterValue(LaunchConfiguration(name), value_type=bool)\n"
content += "def _float(name):\n    return ParameterValue(LaunchConfiguration(name), value_type=float)\n\n"
content += "def generate_launch_description():\n"
content += "    return LaunchDescription([\n"
content += '        DeclareLaunchArgument("vgr_data_path", default_value="/home/zyc/enva_vgr"),\n'
content += '        DeclareLaunchArgument("config_id", default_value="A1_fast"),\n'
content += '        DeclareLaunchArgument("algorithm", default_value="OPGSL"),\n'
content += '        DeclareLaunchArgument("method", default_value="M7_full_saisc_pf"),\n'
content += '        DeclareLaunchArgument("source_x", default_value="5.00"),\n'
content += '        DeclareLaunchArgument("source_y", default_value="6.20"),\n'
content += '        DeclareLaunchArgument("source_z", default_value="0.50"),\n'
content += '        DeclareLaunchArgument("start_x", default_value="-0.9"),\n'
content += '        DeclareLaunchArgument("start_y", default_value="0.15"),\n'
content += '        DeclareLaunchArgument("seed", default_value="0"),\n'
content += '        DeclareLaunchArgument("timeout_sec", default_value="300.0"),\n'
content += '        DeclareLaunchArgument("resultsFile", default_value="/tmp/edpa_results.csv"),\n'
content += '        Node(package="vgr_bridge", executable="vgr_sim_node", name="vgr_uav_sim", output="screen",\n'
content += "            parameters=[{\n"
content += '                "vgr_data_path": LaunchConfiguration("vgr_data_path"),\n'
content += '                "config_id": LaunchConfiguration("config_id"),\n'
content += '                "flight_height": 0.3,\n'
content += '                "start_x": _float("start_x"),\n'
content += '                "start_y": _float("start_y"),\n'
content += '                "seed": _int("seed"),\n'
content += "            }]),\n"
content += '        Node(package="gsl_server", executable="gsl_actionserver_node", name="gsl_server", output="screen",\n'
content += "            parameters=[{\n"
content += '                "use_sim_time": False,\n'
content += '                "maxSearchTime": _float("timeout_sec"),\n'
content += '                "distanceThreshold": -1.0,\n'
content += '                "resultsFile": LaunchConfiguration("resultsFile"),\n'
content += '                "ground_truth_x": _float("source_x"),\n'
content += '                "ground_truth_y": _float("source_y"),\n'
content += '                "opgsl.seed": _int("seed"),\n'
content += '                "opgsl.modules.edpa": True,\n'
content += '                "opgsl.edpa.detection_threshold": 0.01,\n'
content += '                "opgsl.edpa.lambda0": 1.0,\n'
content += '                "opgsl.edpa.ell": 2.0,\n'
content += '                "opgsl.edpa.alphaw": 0.5,\n'
content += '                "opgsl.edpa.stop_epsilon": 1.5,\n'
content += '                "opgsl.edpa.stop_delta": 0.10,\n'
content += '                "opgsl.edpa.stop_eta": 5.0,\n'
content += '                "opgsl.modules.sbd": False,\n'
content += '                "opgsl.modules.ddm": False,\n'
content += '                "opgsl.modules.cp": False,\n'
content += '                "opgsl.modules.wraig": False,\n'
content += '                "opgsl.modules.upwind_tracking": False,\n'
content += '                "opgsl.modules.levy": True,\n'
content += '                "opgsl.modules.bout": True,\n'
content += '                "opgsl.modules.adaptive_step": True,\n'
content += '                "opgsl.sdnbv.enabled": True,\n'
content += '                "opgsl.convergence.min_time": 30.0,\n'
content += "            }]),\n"
content += '        TimerAction(period=5.0, actions=[\n'
content += '            Node(package="vgr_bridge", executable="gsl_benchmark_runner", name="benchmark", output="screen",\n'
content += "                parameters=[{\n"
content += '                    "algorithm": LaunchConfiguration("algorithm"),\n'
content += '                    "method": LaunchConfiguration("method"),\n'
content += '                    "source_x": _float("source_x"),\n'
content += '                    "source_y": _float("source_y"),\n'
content += '                    "seed": _int("seed"),\n'
content += '                    "time_budget_s": _float("timeout_sec"),\n'
content += '                    "repo_root": "/home/zyc/gsl_ws/src/GasSourceLocalization",\n'
content += '                    "output_csv": LaunchConfiguration("resultsFile"),\n'
content += "                }]),\n"
content += "        ]),\n"
content += "    ])\n"

path = r"D:\ZYC\A-gas\src\vgr_edpa_launch.py"
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Written: " + path)
