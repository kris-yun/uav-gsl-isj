"""OPGSL Scientific V3.1 fixed-height ROS/VGR/GADEN launch."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def _float(name):
    return ParameterValue(LaunchConfiguration(name), value_type=float)


def _int(name):
    return ParameterValue(LaunchConfiguration(name), value_type=int)


def _bool(name):
    return ParameterValue(LaunchConfiguration(name), value_type=bool)


def generate_launch_description():
    default_params = PathJoinSubstitution([
        FindPackageShare("vgr_bridge"), "params", "OPGSL_SCIENTIFIC_V31.yaml"
    ])
    return LaunchDescription([
        DeclareLaunchArgument("vgr_data_path", default_value=""),
        DeclareLaunchArgument("config_id", default_value="2,4-1_fast"),
        DeclareLaunchArgument("run_id", default_value="opgsl_scientific_v31_smoke"),
        DeclareLaunchArgument("run_dir", default_value="/tmp/opgsl_scientific_v31_smoke"),
        DeclareLaunchArgument("start_x", default_value="0.30"),
        DeclareLaunchArgument("start_y", default_value="-1.20"),
        DeclareLaunchArgument("seed", default_value="0"),
        DeclareLaunchArgument("flight_height", default_value="0.30"),
        DeclareLaunchArgument("timeout_sec", default_value="60.0"),
        DeclareLaunchArgument("calibration_file", default_value=""),
        DeclareLaunchArgument("params_file", default_value=default_params),
        DeclareLaunchArgument("enable_vertical", default_value="false"),
        DeclareLaunchArgument("evidence_mode", default_value="proper_joint"),
        DeclareLaunchArgument("use_skill_verifier", default_value="true"),
        DeclareLaunchArgument("radius_only_stop", default_value="false"),
        Node(
            package="vgr_bridge", executable="vgr_sim_node", name="vgr_uav_sim",
            output="screen", parameters=[{
                "vgr_data_path": LaunchConfiguration("vgr_data_path"),
                "config_id": LaunchConfiguration("config_id"),
                "flight_height": _float("flight_height"),
                "start_x": _float("start_x"), "start_y": _float("start_y"),
                "seed": _int("seed"), "allow_vertical_motion": False,
                "sensor_model_mode": "fopdt",
                "gaden_iteration_mode": "seeded_time_replay",
                "sensor_trace_file": PathJoinSubstitution([LaunchConfiguration("run_dir"), "raw_trace.csv"]),
                "wind_trace_file": PathJoinSubstitution([LaunchConfiguration("run_dir"), "wind_trace.csv"]),
                "pose_trace_file": PathJoinSubstitution([LaunchConfiguration("run_dir"), "trajectory.csv"]),
                "measurement_trace_file": PathJoinSubstitution([LaunchConfiguration("run_dir"), "measurement_trace.csv"]),
                "sensor_manifest_file": PathJoinSubstitution([LaunchConfiguration("run_dir"), "sensor_manifest.json"]),
            }]
        ),
        Node(
            package="vgr_bridge", executable="wind_value_server", name="wind_value_server",
            output="screen", parameters=[{
                "vgr_data_path": LaunchConfiguration("vgr_data_path"),
                "config_id": LaunchConfiguration("config_id"),
            }]
        ),
        Node(
            package="gmrf_wind_mapping", executable="gmrf_wind_mapping_node", name="gmrf",
            output="screen", parameters=[{
                "frame_id": "map", "sensor_topic": "/Anemometer/WindSensor_reading",
                "map_topic": "map", "map_yaml_file": "", "exec_freq": 10.0,
                "cell_size": 0.3, "verbose": False, "visualize_gmrf": False,
            }]
        ),
        TimerAction(period=5.0, actions=[Node(
            package="gsl_server", executable="gsl_actionserver_node", name="gsl_server",
            output="screen", parameters=[LaunchConfiguration("params_file"), {
                "method": "OPGSL_SCIENTIFIC_V31",
                "maxSearchTime": _float("timeout_sec"),
                "distanceThreshold": -1.0,
                "useWindGroundTruth": False,
                "run_uuid": LaunchConfiguration("run_id"),
                "resultsFile": PathJoinSubstitution([LaunchConfiguration("run_dir"), "opgsl_v31_result.csv"]),
                "navigationPathFile": PathJoinSubstitution([LaunchConfiguration("run_dir"), "navigation_path.csv"]),
                "source_estimate_trace_file": PathJoinSubstitution([LaunchConfiguration("run_dir"), "source_estimate_trace.csv"]),
                "opgsl.v3.calibration_file": LaunchConfiguration("calibration_file"),
                "opgsl.v3.seed": _int("seed"),
                "opgsl.v3.actions.enable_vertical": _bool("enable_vertical"),
                "opgsl.v3.ablation.evidence_mode": LaunchConfiguration("evidence_mode"),
                "opgsl.v3.ablation.use_skill_verifier": _bool("use_skill_verifier"),
                "opgsl.v3.ablation.radius_only_stop": _bool("radius_only_stop"),
                "opgsl.v3.trace.evidence": PathJoinSubstitution([LaunchConfiguration("run_dir"), "evidence_trace.csv"]),
                "opgsl.v3.trace.planner": PathJoinSubstitution([LaunchConfiguration("run_dir"), "planner_trace.csv"]),
                "opgsl.v3.trace.stop": PathJoinSubstitution([LaunchConfiguration("run_dir"), "stop_trace.csv"]),
                "opgsl.v3.trace.parameter_snapshot": PathJoinSubstitution([LaunchConfiguration("run_dir"), "resolved_parameters.yaml"]),
            }]
        )]),
        TimerAction(period=15.0, actions=[Node(
            package="vgr_bridge", executable="gsl_pilot_runner", name="gsl_pilot_runner",
            output="screen", parameters=[{
                "algorithm": "OPGSL_SCIENTIFIC_V31",
                "run_id": LaunchConfiguration("run_id"),
                "run_dir": LaunchConfiguration("run_dir"),
            }]
        )]),
    ])
