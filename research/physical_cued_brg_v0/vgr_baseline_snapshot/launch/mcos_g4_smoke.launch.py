"""Truth-isolated, fixed-altitude G4 smoke launch for MCOS infrastructure.

This launch is not a paper benchmark.  It verifies synchronized continuous
measurements and an auditable sensor model before the C++ MCOS estimator is
enabled.  Source coordinates are passed only to the separate evaluator node.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _int(name):
    return ParameterValue(LaunchConfiguration(name), value_type=int)


def _float(name):
    return ParameterValue(LaunchConfiguration(name), value_type=float)


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "vgr_data_path", default_value="/home/zyc/vgr_data_scenarios/House01"
        ),
        DeclareLaunchArgument("config_id", default_value="2,4-1_fast"),
        DeclareLaunchArgument("algorithm", default_value="OPGSL"),
        DeclareLaunchArgument("method", default_value="G4_trace_smoke_only"),
        DeclareLaunchArgument("source_x", default_value="-0.40"),
        DeclareLaunchArgument("source_y", default_value="-2.90"),
        DeclareLaunchArgument("start_x", default_value="0.30"),
        DeclareLaunchArgument("start_y", default_value="-1.20"),
        DeclareLaunchArgument("flight_height", default_value="0.30"),
        DeclareLaunchArgument("seed", default_value="0"),
        DeclareLaunchArgument("timeout_sec", default_value="60.0"),
        DeclareLaunchArgument("sim_dt_s", default_value="0.2"),
        DeclareLaunchArgument("realtime_factor", default_value="4.0"),
        DeclareLaunchArgument("open_loop_profile", default_value=""),
        DeclareLaunchArgument("motion_duration_s", default_value="12.0"),
        DeclareLaunchArgument("motion_heading_rad", default_value="0.0"),
        DeclareLaunchArgument("sensor_model_mode", default_value="fopdt"),
        DeclareLaunchArgument("sensor_tau_rise_s", default_value="1.2"),
        DeclareLaunchArgument("sensor_tau_recovery_s", default_value="1.2"),
        DeclareLaunchArgument("sensor_dead_time_s", default_value="0.4"),
        DeclareLaunchArgument("sensor_noise_std_ppm", default_value="0.0"),
        DeclareLaunchArgument(
            "measurement_trace_file",
            default_value="/tmp/mcos_g4/measurement_trace.csv",
        ),
        DeclareLaunchArgument(
            "sensor_manifest_file",
            default_value="/tmp/mcos_g4/sensor_manifest.json",
        ),
        DeclareLaunchArgument(
            "estimator_observation_audit_file",
            default_value="/tmp/mcos_g4/estimator_observations.csv",
        ),
        DeclareLaunchArgument(
            "results_file", default_value="/tmp/mcos_g4/evaluator_results.csv"
        ),
        Node(
            package="vgr_bridge",
            executable="vgr_sim_node",
            name="vgr_uav_sim",
            output="screen",
            parameters=[{
                # The simulator uses a wall timer only as a playback driver and
                # publishes the authoritative deterministic /clock itself.
                "use_sim_time": False,
                "vgr_data_path": LaunchConfiguration("vgr_data_path"),
                "config_id": LaunchConfiguration("config_id"),
                "flight_height": _float("flight_height"),
                "start_x": _float("start_x"),
                "start_y": _float("start_y"),
                "seed": _int("seed"),
                "sim_dt_s": _float("sim_dt_s"),
                "realtime_factor": _float("realtime_factor"),
                "allow_vertical_motion": False,
                "open_loop_profile": LaunchConfiguration("open_loop_profile"),
                "motion_duration_s": _float("motion_duration_s"),
                "motion_heading_rad": _float("motion_heading_rad"),
                "sensor_model_mode": LaunchConfiguration("sensor_model_mode"),
                "sensor_tau_rise_s": _float("sensor_tau_rise_s"),
                "sensor_tau_recovery_s": _float("sensor_tau_recovery_s"),
                "sensor_dead_time_s": _float("sensor_dead_time_s"),
                "sensor_noise_std_ppm": _float("sensor_noise_std_ppm"),
                "measurement_trace_file": LaunchConfiguration(
                    "measurement_trace_file"
                ),
                "sensor_manifest_file": LaunchConfiguration(
                    "sensor_manifest_file"
                ),
            }],
        ),
        Node(
            package="gsl_server",
            executable="gsl_actionserver_node",
            name="gsl_server",
            output="screen",
            parameters=[{
                "use_sim_time": True,
                "maxSearchTime": _float("timeout_sec"),
                "distanceThreshold": -1.0,
                "resultsFile": LaunchConfiguration("results_file"),
                "opgsl.seed": _int("seed"),
                "opgsl.mcos.observation_audit_file": LaunchConfiguration(
                    "estimator_observation_audit_file"
                ),
                "opgsl.modules.sbd": False,
                "opgsl.modules.ddm": False,
                "opgsl.modules.cp": False,
                "opgsl.modules.wraig": False,
                "opgsl.altitude.gp": False,
                "opgsl.event_driven.enabled": False,
                "useWindGroundTruth": False,
            }],
        ),
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package="vgr_bridge",
                    executable="gsl_benchmark_runner",
                    name="offline_evaluator",
                    output="screen",
                    parameters=[{
                        "use_sim_time": True,
                        "algorithm": LaunchConfiguration("algorithm"),
                        "method": LaunchConfiguration("method"),
                        # Truth is confined to this evaluator process.
                        "source_x": _float("source_x"),
                        "source_y": _float("source_y"),
                        "seed": _int("seed"),
                        "time_budget_s": _float("timeout_sec"),
                        "repo_root": "/home/zyc/gsl_ws/src/GasSourceLocalization",
                        "output_csv": LaunchConfiguration("results_file"),
                    }],
                )
            ],
        ),
    ])
