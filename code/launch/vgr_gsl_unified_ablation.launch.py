"""Unified UAV-GSL ablation launch file after audit fixes.

All method modules are disabled by default. A clean baseline must keep:
  pwc_enabled=false, psde_online_enabled=false, psde_final_enabled=false,
  sdr_enabled=false, bwe_enabled=false, pgpt_enabled=false, hce_enabled=false.

Legacy mac_enabled is kept only for compatibility. Prefer the split flags:
  psde_online_enabled: affects sourceProbability and therefore the online path.
  psde_final_enabled: affects only final post-processing estimate.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def arg(name, default):
    return DeclareLaunchArgument(name, default_value=str(default))


def generate_launch_description():
    return LaunchDescription([
        # Data & scenario args
        arg("vgr_data_path", ""),
        arg("config_id", "2,4-1_fast"),
        arg("algorithm", "PMFS"),
        arg("output_csv", "/tmp/gsl_result.csv"),
        arg("server_results_file", ""),
        arg("server_path_file", ""),
        arg("source_x", "-0.40"),
        arg("source_y", "-2.90"),
        arg("source_z", "-0.30"),
        arg("start_x", "-5.0"),
        arg("start_y", "-5.0"),
        arg("seed", "0"),
        arg("budget_fraction", "1.0"),
        arg("flight_height", "1.0"),
        arg("dataset", "VGR_House01"),
        arg("method_id", "baseline"),
        arg("frontierWeight", "0.0"),
        arg("edeWeight", "0.0"),

        # Strict method toggles: all OFF by default = clean baseline.
        arg("pwc_enabled", "false"),
        arg("mac_enabled", "false"),                  # legacy alias; avoid using in new experiments
        arg("psde_online_enabled", "false"),
        arg("psde_final_enabled", "false"),
        arg("sdr_enabled", "false"),
        arg("tdc_enabled", "false"),
        arg("bwe_enabled", "false"),
        arg("pgpt_enabled", "false"),
        arg("hce_enabled", "false"),

        # BAPR params
        arg("bapr_enabled", "false"),
        arg("bapr_wall_penalty", "2.0"),
        arg("bapr_wall_distance", "2.0"),
        arg("bapr_sigmoid_steepness", "3.0"),
        arg("bapr_dtf_radius", "10"),

        # HSPB params
        arg("hspb_enabled", "false"),
        arg("hspb_min_hits", "3"),
        arg("hspb_distance_scale", "1.0"),
        arg("hspb_angular_spread", "0.35"),
        arg("hspb_kernel_radius", "3"),
        arg("gt_debug_logging", "false"),
        arg("verbose_debug", "false"),

        # Shared convention. true means wind vector is flow-to; upwind correction uses -wind.
        arg("wind_vector_is_flow_to", "true"),

        # PWC params
        arg("pwc_beta", "0.5"),
        arg("pwc_max_correction", "5.0"),
        arg("pwc_min_wind", "0.01"),
        arg("pwc_use_adaptive", "true"),
        arg("pwc_plume_scale_factor", "1.0"),
        arg("pwc_log_file", ""),

        # PSDE params; legacy names retained to minimize code churn.
        arg("mac_flight_height", "1.0"),
        arg("mac_source_height", "0.0"),
        arg("mac_stability_class", "3"),
        arg("mac_min_distance", "0.5"),
        arg("mac_max_distance_weight", "6.0"),
        arg("mac_distance_sigma", "2.0"),
        arg("mac_sigma_z_max", "3.0"),
        arg("mac_min_hits", "5"),
        arg("mac_online_update_stride", "3"),
        arg("mac_online_boost_weight", "0.01"),

        # SDR params
        arg("sdr_rl_iterations", "10"),
        arg("sdr_psf_size", "7"),
        arg("sdr_blob_radius", "4.5"),
        arg("sdr_min_hits", "5"),
        arg("sdr_min_peak_mass_ratio", "0.0"),

        # HCE/BWE params
        arg("hce_min_concentration", "0.001"),
        arg("bwe_alpha", "0.15"),
        arg("bwe_alpha_fast", "0.40"),
        arg("bwe_min_speed", "0.01"),

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
                # Identical base params for every condition.
                "use_sim_time": False,
                "maxSearchTime": 300.0,
                "distanceThreshold": 0.5,
                "ground_truth_x": LaunchConfiguration("source_x"),
                "ground_truth_y": LaunchConfiguration("source_y"),
                "resultsFile": LaunchConfiguration("server_results_file"),
                "navigationPathFile": LaunchConfiguration("server_path_file"),
                "use_wranf_supervisor": False,
                "method_id": LaunchConfiguration("method_id"),

                # Method toggles
                "pwc_enabled": LaunchConfiguration("pwc_enabled"),
                "mac_enabled": LaunchConfiguration("mac_enabled"),
                "psde_online_enabled": LaunchConfiguration("psde_online_enabled"),
                "psde_final_enabled": LaunchConfiguration("psde_final_enabled"),
                "sdr_enabled": LaunchConfiguration("sdr_enabled"),
                "tdc_enabled": LaunchConfiguration("tdc_enabled"),
                "bwe_enabled": LaunchConfiguration("bwe_enabled"),
                "pgpt_enabled": LaunchConfiguration("pgpt_enabled"),
                "hce_enabled": LaunchConfiguration("hce_enabled"),
                "bapr_enabled": LaunchConfiguration("bapr_enabled"),
                "bapr_wall_penalty": LaunchConfiguration("bapr_wall_penalty"),
                "bapr_wall_distance": LaunchConfiguration("bapr_wall_distance"),
                "bapr_sigmoid_steepness": LaunchConfiguration("bapr_sigmoid_steepness"),
                "bapr_dtf_radius": LaunchConfiguration("bapr_dtf_radius"),
                "hspb_enabled": LaunchConfiguration("hspb_enabled"),
                "hspb_min_hits": LaunchConfiguration("hspb_min_hits"),
                "hspb_distance_scale": LaunchConfiguration("hspb_distance_scale"),
                "hspb_angular_spread": LaunchConfiguration("hspb_angular_spread"),
                "hspb_kernel_radius": LaunchConfiguration("hspb_kernel_radius"),
                "gt_debug_logging": LaunchConfiguration("gt_debug_logging"),
                "verbose_debug": LaunchConfiguration("verbose_debug"),
                "wind_vector_is_flow_to": LaunchConfiguration("wind_vector_is_flow_to"),

                # Explicitly disable unrelated modules.
                "adc_enabled": False,
                "set_enabled": False,
                "frg_enabled": False,
                "use_observation_enhancer": False,
                "dbf_enabled": False,
                "spc_enabled": False,
                "fssp_enabled": False,

                # PWC params
                "pwc_beta": LaunchConfiguration("pwc_beta"),
                "pwc_max_correction": LaunchConfiguration("pwc_max_correction"),
                "pwc_min_wind": LaunchConfiguration("pwc_min_wind"),
                "pwc_use_adaptive": LaunchConfiguration("pwc_use_adaptive"),
                "pwc_plume_scale_factor": LaunchConfiguration("pwc_plume_scale_factor"),
                "pwc_log_file": LaunchConfiguration("pwc_log_file"),

                # PSDE params
                "mac_flight_height": LaunchConfiguration("mac_flight_height"),
                "mac_source_height": LaunchConfiguration("mac_source_height"),
                "mac_stability_class": LaunchConfiguration("mac_stability_class"),
                "mac_min_distance": LaunchConfiguration("mac_min_distance"),
                "mac_max_distance_weight": LaunchConfiguration("mac_max_distance_weight"),
                "mac_distance_sigma": LaunchConfiguration("mac_distance_sigma"),
                "mac_sigma_z_max": LaunchConfiguration("mac_sigma_z_max"),
                "mac_min_hits": LaunchConfiguration("mac_min_hits"),
                "mac_online_update_stride": LaunchConfiguration("mac_online_update_stride"),
                "mac_online_boost_weight": LaunchConfiguration("mac_online_boost_weight"),

                # SDR params
                "sdr_rl_iterations": LaunchConfiguration("sdr_rl_iterations"),
                "sdr_psf_size": LaunchConfiguration("sdr_psf_size"),
                "sdr_blob_radius": LaunchConfiguration("sdr_blob_radius"),
                "sdr_min_hits": LaunchConfiguration("sdr_min_hits"),
                "sdr_min_peak_mass_ratio": LaunchConfiguration("sdr_min_peak_mass_ratio"),

                # HCE/BWE params
                "hce_min_concentration": LaunchConfiguration("hce_min_concentration"),
                "bwe_alpha": LaunchConfiguration("bwe_alpha"),
                "bwe_alpha_fast": LaunchConfiguration("bwe_alpha_fast"),
                "bwe_min_speed": LaunchConfiguration("bwe_min_speed"),

                # Core PMFS params. These must remain identical across conditions.
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
