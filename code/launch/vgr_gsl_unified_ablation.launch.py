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
        arg("tdc_adaptive", "true"),
        arg("tdc_tau_min", "1.0"),
        arg("tdc_tau_decay_n0", "15.0"),
        arg("bwe_enabled", "false"),
        arg("pgpt_enabled", "false"),
        arg("hce_enabled", "false"),

        # BAPR params
        arg("asa_enabled", "false"),
        
        
        
        arg("asa_ema_alpha", "0.15"),
        arg("mhc_enabled", "false"),
        arg("mhc_open_radius", "1"),
        arg("mhc_close_radius", "2.0"),
        arg("mti_enabled", "false"),
        arg("mti_alpha", "0.15"),
        arg("mti_threshold_ratio", "0.3"),
        arg("mti_hit_gain", "0.3"),

        # HSPB params
        arg("spw_enabled", "false"),
        arg("spw_gamma", "0.5"),
        arg("spw_min_updates", "3"),
        
        
        arg("gt_debug_logging", "false"),
        arg("verbose_debug", "false"),


        # Review innovation modules (EGS, DIRL, RGC)
        arg("egs_enabled", "false"),
        arg("egs_min_iterations", "5"),
        arg("egs_min_hit_count", "5"),
        arg("egs_min_hit_mass", "0.0"),
        arg("egs_min_hit_bbox_diag_m", "0.75"),
        arg("egs_min_wind_coherence", "0.25"),
        arg("egs_max_entropy_norm", "0.98"),
        arg("egs_min_posterior_peak_ratio", "0.005"),
        arg("egs_reject_no_hit_convergence", "true"),
        arg("dirl_enabled", "false"),
        arg("dirl_min_hits", "5"),
        arg("dirl_min_concentration", "0.0"),
        arg("dirl_rl_iterations", "10"),
        arg("dirl_psf_size", "9"),
        arg("dirl_sigma_upwind_cells", "1.0"),
        arg("dirl_sigma_downwind_cells", "3.0"),
        arg("dirl_sigma_crosswind_cells", "1.5"),
        arg("dirl_hit_splat_radius_cells", "2"),
        arg("dirl_hit_splat_sigma_cells", "1.0"),
        arg("dirl_hit_weight_exponent", "1.0"),
        arg("dirl_pmfs_prior_power", "1.0"),
        arg("dirl_min_wind_speed", "0.01"),
        arg("dirl_min_peak_mass_ratio", "0.005"),
        arg("dirl_max_entropy_norm", "1.0"),
        arg("rgc_enabled", "false"),
        arg("rgc_dirl_min_hits", "5"),
        arg("rgc_dirl_min_wind_coherence", "0.25"),
        arg("rgc_dirl_min_peak_mass_ratio", "0.005"),
        arg("rgc_max_dirl_pmfs_disagreement_m", "6.0"),
        arg("rgc_weak_evidence_max_correction_m", "2.0"),
        arg("rgc_allow_blend", "true"),
        arg("rgc_min_blend_weight", "0.20"),
        arg("rgc_max_blend_weight", "0.85"),
        arg("review_modules_verbose", "true"),

        arg("eae_enabled", "false"),
        arg("eae_base_exploration_prob", "0.05"),
        arg("eae_max_exploration_prob", "0.50"),
        arg("eae_boost_per_miss", "0.03"),
        arg("eae_miss_threshold", "3"),
        arg("eae_extend_search_on_low_evidence", "true"),
        arg("eae_max_extension_factor", "2.0"),
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
                "tdc_adaptive": LaunchConfiguration("tdc_adaptive"),
                "tdc_tau_min": LaunchConfiguration("tdc_tau_min"),
                "tdc_tau_decay_n0": LaunchConfiguration("tdc_tau_decay_n0"),
                "bwe_enabled": LaunchConfiguration("bwe_enabled"),
                "pgpt_enabled": LaunchConfiguration("pgpt_enabled"),
                "hce_enabled": LaunchConfiguration("hce_enabled"),
                "asa_enabled": LaunchConfiguration("asa_enabled"),
                
                
                
                "asa_ema_alpha": LaunchConfiguration("asa_ema_alpha"),
                "mhc_enabled": LaunchConfiguration("mhc_enabled"),
                "mhc_open_radius": LaunchConfiguration("mhc_open_radius"),
                "mhc_close_radius": LaunchConfiguration("mhc_close_radius"),
                "mti_enabled": LaunchConfiguration("mti_enabled"),
                "mti_alpha": LaunchConfiguration("mti_alpha"),
                "mti_threshold_ratio": LaunchConfiguration("mti_threshold_ratio"),
                "mti_hit_gain": LaunchConfiguration("mti_hit_gain"),
                "spw_enabled": LaunchConfiguration("spw_enabled"),
                "spw_gamma": LaunchConfiguration("spw_gamma"),
                "spw_min_updates": LaunchConfiguration("spw_min_updates"),
                
                
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


                # Review innovation modules (EGS, DIRL, RGC)
                "egs_enabled": LaunchConfiguration("egs_enabled"),
                "egs_min_iterations": LaunchConfiguration("egs_min_iterations"),
                "egs_min_hit_count": LaunchConfiguration("egs_min_hit_count"),
                "egs_min_hit_mass": LaunchConfiguration("egs_min_hit_mass"),
                "egs_min_hit_bbox_diag_m": LaunchConfiguration("egs_min_hit_bbox_diag_m"),
                "egs_min_wind_coherence": LaunchConfiguration("egs_min_wind_coherence"),
                "egs_max_entropy_norm": LaunchConfiguration("egs_max_entropy_norm"),
                "egs_min_posterior_peak_ratio": LaunchConfiguration("egs_min_posterior_peak_ratio"),
                "egs_reject_no_hit_convergence": LaunchConfiguration("egs_reject_no_hit_convergence"),
                "dirl_enabled": LaunchConfiguration("dirl_enabled"),
                "dirl_min_hits": LaunchConfiguration("dirl_min_hits"),
                "dirl_min_concentration": LaunchConfiguration("dirl_min_concentration"),
                "dirl_rl_iterations": LaunchConfiguration("dirl_rl_iterations"),
                "dirl_psf_size": LaunchConfiguration("dirl_psf_size"),
                "dirl_sigma_upwind_cells": LaunchConfiguration("dirl_sigma_upwind_cells"),
                "dirl_sigma_downwind_cells": LaunchConfiguration("dirl_sigma_downwind_cells"),
                "dirl_sigma_crosswind_cells": LaunchConfiguration("dirl_sigma_crosswind_cells"),
                "dirl_hit_splat_radius_cells": LaunchConfiguration("dirl_hit_splat_radius_cells"),
                "dirl_hit_splat_sigma_cells": LaunchConfiguration("dirl_hit_splat_sigma_cells"),
                "dirl_hit_weight_exponent": LaunchConfiguration("dirl_hit_weight_exponent"),
                "dirl_pmfs_prior_power": LaunchConfiguration("dirl_pmfs_prior_power"),
                "dirl_min_wind_speed": LaunchConfiguration("dirl_min_wind_speed"),
                "dirl_min_peak_mass_ratio": LaunchConfiguration("dirl_min_peak_mass_ratio"),
                "dirl_max_entropy_norm": LaunchConfiguration("dirl_max_entropy_norm"),
                "rgc_enabled": LaunchConfiguration("rgc_enabled"),
                "rgc_dirl_min_hits": LaunchConfiguration("rgc_dirl_min_hits"),
                "rgc_dirl_min_wind_coherence": LaunchConfiguration("rgc_dirl_min_wind_coherence"),
                "rgc_dirl_min_peak_mass_ratio": LaunchConfiguration("rgc_dirl_min_peak_mass_ratio"),
                "rgc_max_dirl_pmfs_disagreement_m": LaunchConfiguration("rgc_max_dirl_pmfs_disagreement_m"),
                "rgc_weak_evidence_max_correction_m": LaunchConfiguration("rgc_weak_evidence_max_correction_m"),
                "rgc_allow_blend": LaunchConfiguration("rgc_allow_blend"),
                "rgc_min_blend_weight": LaunchConfiguration("rgc_min_blend_weight"),
                "rgc_max_blend_weight": LaunchConfiguration("rgc_max_blend_weight"),
                "review_modules_verbose": LaunchConfiguration("review_modules_verbose"),

                "eae_enabled": LaunchConfiguration("eae_enabled"),
                "eae_base_exploration_prob": LaunchConfiguration("eae_base_exploration_prob"),
                "eae_max_exploration_prob": LaunchConfiguration("eae_max_exploration_prob"),
                "eae_boost_per_miss": LaunchConfiguration("eae_boost_per_miss"),
                "eae_miss_threshold": LaunchConfiguration("eae_miss_threshold"),
                "eae_extend_search_on_low_evidence": LaunchConfiguration("eae_extend_search_on_low_evidence"),
                "eae_max_extension_factor": LaunchConfiguration("eae_max_extension_factor"),
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
