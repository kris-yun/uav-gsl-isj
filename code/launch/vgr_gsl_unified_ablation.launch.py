"""Unified ablation launch file - all modules as toggles, identical base params.

Usage: ros2 launch vgr_bridge vgr_gsl_unified_ablation.launch.py pwc_enabled:=true mac_enabled:=true sdr_enabled:=true

Module toggles (all default OFF for baseline):
  pwc_enabled: Plume Wind Correction
  mac_enabled: Plume Spatial Dispersion Estimator (renamed from MAC)
  sdr_enabled: Richardson-Lucy Deconvolution Refinement
  tdc_enabled: Temporal Deconvolution Correction
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # Data & scenario args
        DeclareLaunchArgument("vgr_data_path", default_value=""),
        DeclareLaunchArgument("config_id", default_value="2,4-1_fast"),
        DeclareLaunchArgument("algorithm", default_value="PMFS"),
        DeclareLaunchArgument("output_csv", default_value="/tmp/gsl_result.csv"),
        DeclareLaunchArgument("server_results_file", default_value=""),
        DeclareLaunchArgument("server_path_file", default_value=""),
        DeclareLaunchArgument("source_x", default_value="-0.40"),
        DeclareLaunchArgument("source_y", default_value="-2.90"),
        DeclareLaunchArgument("source_z", default_value="-0.30"),
        DeclareLaunchArgument("start_x", default_value="-5.0"),
        DeclareLaunchArgument("start_y", default_value="-5.0"),
        DeclareLaunchArgument("seed", default_value="0"),
        DeclareLaunchArgument("budget_fraction", default_value="1.0"),
        DeclareLaunchArgument("flight_height", default_value="1.0"),
        DeclareLaunchArgument("dataset", default_value="VGR_House01"),
        DeclareLaunchArgument("frontierWeight", default_value="0.0"),
        DeclareLaunchArgument("edeWeight", default_value="0.0"),

        # Module toggles (all OFF by default = baseline)
        DeclareLaunchArgument("pwc_enabled", default_value="false"),
        DeclareLaunchArgument("mac_enabled", default_value="false"),
        DeclareLaunchArgument("sdr_enabled", default_value="false"),
        DeclareLaunchArgument("tdc_enabled", default_value="false"),

        # Module params (fixed across all conditions)
        DeclareLaunchArgument("pwc_beta", default_value="0.5"),
        DeclareLaunchArgument("pwc_max_correction", default_value="5.0"),
        DeclareLaunchArgument("pwc_min_wind", default_value="0.01"),
        DeclareLaunchArgument("mac_flight_height", default_value="1.0"),
        DeclareLaunchArgument("mac_source_height", default_value="0.0"),
        DeclareLaunchArgument("mac_stability_class", default_value="3"),
        DeclareLaunchArgument("mac_max_distance_weight", default_value="6.0"),
        DeclareLaunchArgument("mac_distance_sigma", default_value="2.0"),

        Node(
            package="vgr_bridge",
            executable="vgr_sim_node",
            name="vgr_uav_sim",
            output="screen",
            parameters=[{
                "vgr_data_path": LaunchConfiguration("vgr_data_path"),
                "config_id": LaunchConfiguration("config_id"),
                "flight_height": LaunchConfiguration("flight_height"),
                "start_x": LaunchConfiguration("start_x"),
                "start_y": LaunchConfiguration("start_y"),
                "use_sim_time": False,
            }],
        ),

        Node(
            package="gmrf_wind_mapping",
            executable="gmrf_wind_mapping_node",
            name="gmrf",
            output="screen",
            parameters=[{
                "frame_id": "map",
                "sensor_topic": "/Anemometer/WindSensor_reading",
                "map_topic": "map",
                "map_yaml_file": "",
                "exec_freq": 10.0,
                "cell_size": 0.3,
                "verbose": False,
                "visualize_gmrf": False,
                "observation_var_wind_speed": 0.00025,
                "observation_var_wind_direction": 0.00025,
                "GMRF_lambdaPrior_advection": 10.0,
                "GMRF_lambdaPrior_mass_conservation": 10.0,
                "GMRF_lambdaPrior_diffusion": 1.0,
                "GMRF_lambdaPrior_vorticity": 1.0,
                "GMRF_lambdaPrior_obstacles": 1.0,
            }],
        ),

        Node(
            package="gsl_server",
            executable="gsl_actionserver_node",
            name="gsl_server",
            output="screen",
            parameters=[{
                # === IDENTICAL base params for ALL conditions ===
                "use_sim_time": False,
                "maxSearchTime": 300.0,
                "distanceThreshold": 0.5,
                "ground_truth_x": LaunchConfiguration("source_x"),
                "ground_truth_y": LaunchConfiguration("source_y"),
                "resultsFile": LaunchConfiguration("server_results_file"),
                "navigationPathFile": LaunchConfiguration("server_path_file"),
                "use_wranf_supervisor": False,

                # Module toggles
                "pwc_enabled": LaunchConfiguration("pwc_enabled"),
                "mac_enabled": LaunchConfiguration("mac_enabled"),
                "sdr_enabled": LaunchConfiguration("sdr_enabled"),
                "tdc_enabled": LaunchConfiguration("tdc_enabled"),
                "adc_enabled": False,
                "set_enabled": False,
                "frg_enabled": False,
                "use_observation_enhancer": False,
                "dbf_enabled": False,
                "spc_enabled": False,
                "fssp_enabled": False,

                # PWC params (fixed)
                "pwc_beta": LaunchConfiguration("pwc_beta"),
                "pwc_max_correction": LaunchConfiguration("pwc_max_correction"),
                "pwc_min_wind": LaunchConfiguration("pwc_min_wind"),
                "pwc_use_adaptive": True,
                "pwc_plume_scale_factor": 1.0,
                "pwc_log_file": "/tmp/pwc_log.csv",

                # PSDE params (fixed)
                "mac_flight_height": LaunchConfiguration("mac_flight_height"),
                "mac_source_height": LaunchConfiguration("mac_source_height"),
                "mac_stability_class": LaunchConfiguration("mac_stability_class"),
                "mac_max_distance_weight": LaunchConfiguration("mac_max_distance_weight"),
                "mac_distance_sigma": LaunchConfiguration("mac_distance_sigma"),

                # TDC params (fixed)
                "tdc_iterations": 5,
                "tdc_tau": 15.0,
                "tdc_damping": 0.8,
                "tdc_sharpen_strength": 0.5,

                # === Core PMFS params (MAPIRlab defaults, IDENTICAL) ===
                "scale": 25,
                "convergence_thr": 1.5,
                "minExplorationIterations": 3,
                "minInformationGain": 0.01,
                "useWCC": True,
                "wccThreshold": 0.001,
                "useWRSD": True,
                "sourceDiscriminationPower": 0.3,
                "refineFraction": 0.1,
                "stepsSourceUpdate": 3,
                "maxRegionSize": 5,
                "deltaTime": 0.1,
                "noiseSTDev": 0.5,
                "iterationsToRecord": 200,
                "maxWarmupIterations": 500,
                "minWarmupIterations": 0,
                "blurSigmaX": 1.5,
                "blurSigmaY": 1.5,
                "hitPriorProbability": 0.3,
                "maxUpdatesPerStop": 5,
                "kernelSigma": 1.5,
                "kernelStretchConstant": 1.5,
                "confidenceMeasurementWeight": 1.0,
                "confidenceSigmaSpatial": 1.0,
                "localEstimationWindowSize": 2,
                "openMoveSetExpasion": 5,
                "explorationProbability": 0.05,
                "initialExplorationMoves": 2,
                "distanceWeight": 0.15,
                "frontierWeight": LaunchConfiguration("frontierWeight"),
                "edeWeight": LaunchConfiguration("edeWeight"),
                "useWindGroundTruth": False,
                "markers_height": 0.2,
            }],
        ),

        TimerAction(
            period=10.0,
            actions=[
                Node(
                    package="vgr_bridge",
                    executable="gsl_benchmark_runner",
                    name="gsl_benchmark_runner",
                    output="screen",
                    parameters=[{
                        "algorithm": LaunchConfiguration("algorithm"),
                        "output_csv": LaunchConfiguration("output_csv"),
                        "source_x": LaunchConfiguration("source_x"),
                        "source_y": LaunchConfiguration("source_y"),
                        "source_z": LaunchConfiguration("source_z"),
                        "seed": LaunchConfiguration("seed"),
                        "budget_fraction": LaunchConfiguration("budget_fraction"),
                        "config_id": LaunchConfiguration("config_id"),
                        "dataset": LaunchConfiguration("dataset"),
                        "server_results_file": LaunchConfiguration("server_results_file"),
                        "use_sim_time": False,
                    }],
                ),
            ],
        ),
    ])
