"""Official PMFS launch - with GMRF wind estimation."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
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

        # VGR UAV simulator
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

        # GMRF Wind Estimation (required by PMFS)
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

        # GSL Server with PMFS
        Node(
            package="gsl_server",
            executable="gsl_actionserver_node",
            name="gsl_server",
            output="screen",
            parameters=[{
                "use_sim_time": False,
                "maxSearchTime": 300.0,
                "distanceThreshold": -1.0,
                "ground_truth_x": LaunchConfiguration("source_x"),
                "ground_truth_y": LaunchConfiguration("source_y"),
                "resultsFile": LaunchConfiguration("server_results_file"),
                "navigationPathFile": LaunchConfiguration("server_path_file"),
                # From MAPIRlab main_simbot_launch.py
                "scale": 25,
                "convergence_thr": 1.5,
                "minExplorationIterations": 3,  # MEG: force at least 3 iterations
                "minInformationGain": 0.01,  # MEG: min info gain to continue
                "useWCC": True,  # WCC: Jeffrey divergence convergence
                "wccThreshold": 0.001,  # WCC: divergence threshold
                "useWRSD": True,  # WRSD: sub-cell source refinement
                # CBOL: Causal-Bearing Observation Layer
                "use_observation_enhancer": True,
                "cbol_sensor_delay": 1.0,
                "cbol_confidence_threshold": 0.3,
                "cbol_condition_threshold": 10.0,
                "cbol_min_samples": 3,
                "cbol_ridge_lambda": 0.1,
                "cbol_window_radius": 5.0,

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

        # Benchmark runner (delayed start)
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
