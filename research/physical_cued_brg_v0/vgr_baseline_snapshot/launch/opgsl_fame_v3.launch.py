"""FAME V3 minimal real closed-loop isolation launch.

HAEM/CP-HVQ is intentionally disabled. C0 is launched separately with the
existing OPGSL_SCIM_V1 launch; this launch runs C1 or C2 via opgsl.fame.mode.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, TimerAction
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def _float(name):
    return ParameterValue(LaunchConfiguration(name), value_type=float)


def _int(name):
    return ParameterValue(LaunchConfiguration(name), value_type=int)


def generate_launch_description():
    params = PathJoinSubstitution([FindPackageShare("vgr_bridge"), "params", "OPGSL_FAME_V3.yaml"])
    run_dir = LaunchConfiguration("run_dir")
    return LaunchDescription([
        DeclareLaunchArgument("vgr_data_path", default_value=""),
        DeclareLaunchArgument("config_id", default_value="2,4-1_fast"),
        DeclareLaunchArgument("run_id", default_value="opgsl_fame_v3_c1_smoke"),
        DeclareLaunchArgument("run_dir", default_value="/tmp/opgsl_fame_v3_c1_smoke"),
        DeclareLaunchArgument("start_x", default_value="0.30"),
        DeclareLaunchArgument("start_y", default_value="-1.20"),
        DeclareLaunchArgument("seed", default_value="35"),
        DeclareLaunchArgument("mode", default_value="1"),
        DeclareLaunchArgument("flight_height", default_value="0.30"),
        DeclareLaunchArgument("timeout_sec", default_value="120.0"),
        DeclareLaunchArgument("shutdown_sec", default_value="180.0"),
        DeclareLaunchArgument("params_file", default_value=params),
        Node(package="vgr_bridge", executable="vgr_sim_node", name="vgr_uav_sim", output="screen",
             parameters=[{
                 "vgr_data_path": LaunchConfiguration("vgr_data_path"),
                 "config_id": LaunchConfiguration("config_id"),
                 "flight_height": _float("flight_height"),
                 "start_x": _float("start_x"), "start_y": _float("start_y"),
                 "seed": _int("seed"), "allow_vertical_motion": False,
                 "sensor_model_mode": "fopdt", "gaden_iteration_mode": "seeded_time_replay",
                 "sensor_trace_file": PathJoinSubstitution([run_dir, "raw_trace.csv"]),
                 "wind_trace_file": PathJoinSubstitution([run_dir, "wind_trace.csv"]),
                 "pose_trace_file": PathJoinSubstitution([run_dir, "trajectory.csv"]),
                 "measurement_trace_file": PathJoinSubstitution([run_dir, "measurement_trace.csv"]),
                 "sensor_manifest_file": PathJoinSubstitution([run_dir, "sensor_manifest.json"]),
             }]),
        Node(package="vgr_bridge", executable="wind_value_server", name="wind_value_server", output="screen",
             parameters=[{"vgr_data_path": LaunchConfiguration("vgr_data_path"), "config_id": LaunchConfiguration("config_id")}]),
        Node(package="gmrf_wind_mapping", executable="gmrf_wind_mapping_node", name="gmrf", output="screen",
             parameters=[{"frame_id": "map", "sensor_topic": "/Anemometer/WindSensor_reading", "map_topic": "map",
                          "map_yaml_file": "", "exec_freq": 10.0, "cell_size": 0.3,
                          "verbose": False, "visualize_gmrf": False}]),
        TimerAction(period=5.0, actions=[Node(
            package="gsl_server", executable="gsl_actionserver_node", name="gsl_server", output="screen",
            parameters=[LaunchConfiguration("params_file"), {
                "method": "OPGSL_FAME_V3", "maxSearchTime": _float("timeout_sec"),
                "distanceThreshold": -1.0, "useWindGroundTruth": False,
                "run_uuid": LaunchConfiguration("run_id"),
                "resultsFile": PathJoinSubstitution([run_dir, "opgsl_fame_v3_result.csv"]),
                "navigationPathFile": PathJoinSubstitution([run_dir, "navigation_path.csv"]),
                "source_estimate_trace_file": PathJoinSubstitution([run_dir, "source_estimate_trace.csv"]),
                "fame_evidence_trace_file": PathJoinSubstitution([run_dir, "evidence_trace.csv"]),
                "joint_posterior_trace_file": PathJoinSubstitution([run_dir, "joint_posterior_trace.csv"]),
                "fame_memory_trace_file": PathJoinSubstitution([run_dir, "fame_memory_trace.csv"]),
                "fame_action_risk_trace_file": PathJoinSubstitution([run_dir, "fame_action_risk_trace.csv"]),
                "fame_parameter_snapshot_file": PathJoinSubstitution([run_dir, "resolved_parameters.yaml"]),
                "opgsl.fame.mode": _int("mode"), "opgsl.fame.seed": _int("seed"),
                "enable_haem_retrieval": False,
            }])]),
        Node(package="vgr_bridge", executable="gsl_pilot_runner", name="gsl_pilot_runner", output="screen",
             parameters=[{"algorithm": "OPGSL_FAME_V3", "run_id": LaunchConfiguration("run_id"), "run_dir": run_dir,
                          "timeout_sec": _float("timeout_sec")}]),
        TimerAction(period=LaunchConfiguration("shutdown_sec"), actions=[EmitEvent(event=Shutdown(reason="normal_budget_end"))]),
    ])
