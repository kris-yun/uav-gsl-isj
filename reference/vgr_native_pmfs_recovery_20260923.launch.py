"""VGR adapter for the isolated official PMFS recovery binary.

No PFDI/TNQC/TADM/P2 parameter or GMRF node is launched in this Native arm.
The algorithm binary and /wind_value server are validated by the shell runner.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration as LC
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


DEFAULTS = {
    # VGR adapter and fixed evaluation contract.
    "vgr_data_path": "", "config_id": "2,4-1_fast", "house": "House01",
    "environment_id": "VGR_House01", "scenario_id": "H01_cfg_2_4_1_fast",
    "source_x": "-0.40", "source_y": "-2.90", "source_z": "-0.30",
    "start_x": "-3.17", "start_y": "-1.75", "flight_height": "0.3",
    "seed": "0", "run_id": "UNSET", "run_dir": "/tmp/native_pmfs_unset",
    "repo_root": "/home/zyc/native_pmfs_recovery_v1/checkout",
    "timeout_sec": "300.0", "realtime_factor": "1.0", "sim_stop_at_s": "-1.0",
    "gas_backend": "raw_house1_snapshot", "raw_query_executable": "/bin/false",
    # Official PMFS example effective values, except VGR map scale and stop rule.
    "scale": "3", "useWindGroundTruth": "true", "convergence_thr": "-1.0",
    "stepsSourceUpdate": "3", "maxRegionSize": "5",
    "sourceDiscriminationPower": "0.3", "refineFraction": "0.1",
    "deltaTime": "0.1", "noiseSTDev": "0.5", "iterationsToRecord": "200",
    "maxWarmupIterations": "500", "minWarmupIterations": "200",
    "blurSigmaX": "1.5", "blurSigmaY": "1.5",
    "hitPriorProbability": "0.3", "maxUpdatesPerStop": "5",
    "kernelSigma": "1.5", "kernelStretchConstant": "1.5",
    "confidenceMeasurementWeight": "1.0", "confidenceSigmaSpatial": "1.0",
    "localEstimationWindowSize": "2", "openMoveSetExpasion": "5",
    "explorationProbability": "0.05", "initialExplorationMoves": "2",
    "distanceWeight": "0.15", "markers_height": "0.2",
    # Frozen VGR measurement protocol.
    "measurement_settle_samples": "0", "measurement_block_samples": "10",
    "measurement_deduplicate_sim_timestamps": "true",
}


def _typed(key, kind):
    return ParameterValue(LC(key), value_type=kind)


def _file(name):
    return PathJoinSubstitution([LC("run_dir"), name])


def generate_launch_description():
    args = [DeclareLaunchArgument(k, default_value=v) for k, v in DEFAULTS.items()]
    sim = Node(
        package="vgr_bridge", executable="vgr_sim_node", name="vgr_uav_sim", output="screen",
        parameters=[{
            "vgr_data_path": LC("vgr_data_path"), "config_id": LC("config_id"),
            "environment_id": LC("environment_id"), "scenario_id": LC("scenario_id"),
            "flight_height": _typed("flight_height", float),
            "start_x": _typed("start_x", float), "start_y": _typed("start_y", float),
            "seed": _typed("seed", int), "sensor_model_mode": "dynamic",
            "gaden_iteration_mode": "seeded_time_replay",
            "realtime_factor": _typed("realtime_factor", float),
            "sim_stop_at_s": _typed("sim_stop_at_s", float),
            "nav_command_quantum_s": 2.0,
            "gas_backend": LC("gas_backend"), "raw_query_executable": LC("raw_query_executable"),
            "sensor_trace_file": _file("sensor_trace.csv"),
            "wind_trace_file": _file("wind_trace.csv"),
            "pose_trace_file": _file("sim_pose_trace.csv"),
        }],
    )
    pmfs = Node(
        package="gsl_server", executable="gsl_actionserver_node", name="gsl_server", output="screen",
        parameters=[{
            "scale": _typed("scale", int), "seed": _typed("seed", int),
            "use_gui": False, "maxSearchTime": _typed("timeout_sec", float),
            "distanceThreshold": -1.0, "useWindGroundTruth": _typed("useWindGroundTruth", bool),
            "anemometer_frame": "map",
            "ground_truth_x": _typed("source_x", float),
            "ground_truth_y": _typed("source_y", float),
            "ground_truth_z": _typed("source_z", float),
            "convergence_thr": _typed("convergence_thr", float),
            "stepsSourceUpdate": _typed("stepsSourceUpdate", int),
            "maxRegionSize": _typed("maxRegionSize", int),
            "sourceDiscriminationPower": _typed("sourceDiscriminationPower", float),
            "refineFraction": _typed("refineFraction", float),
            "deltaTime": _typed("deltaTime", float),
            "noiseSTDev": _typed("noiseSTDev", float),
            "iterationsToRecord": _typed("iterationsToRecord", int),
            "maxWarmupIterations": _typed("maxWarmupIterations", int),
            "minWarmupIterations": _typed("minWarmupIterations", int),
            "blurSigmaX": _typed("blurSigmaX", float),
            "blurSigmaY": _typed("blurSigmaY", float),
            "hitPriorProbability": _typed("hitPriorProbability", float),
            "maxUpdatesPerStop": _typed("maxUpdatesPerStop", int),
            "kernelSigma": _typed("kernelSigma", float),
            "kernelStretchConstant": _typed("kernelStretchConstant", float),
            "confidenceMeasurementWeight": _typed("confidenceMeasurementWeight", float),
            "confidenceSigmaSpatial": _typed("confidenceSigmaSpatial", float),
            "localEstimationWindowSize": _typed("localEstimationWindowSize", int),
            "openMoveSetExpasion": _typed("openMoveSetExpasion", int),
            "explorationProbability": _typed("explorationProbability", float),
            "initialExplorationMoves": _typed("initialExplorationMoves", int),
            "distanceWeight": _typed("distanceWeight", float),
            "markers_height": _typed("markers_height", float),
            "measurement_settle_samples": _typed("measurement_settle_samples", int),
            "measurement_block_samples": _typed("measurement_block_samples", int),
            "measurement_deduplicate_sim_timestamps": _typed("measurement_deduplicate_sim_timestamps", bool),
            "resultsFile": _file("official_gsl_results.csv"),
            "navigationPathFile": _file("official_navigation_path.csv"),
        }],
    )
    benchmark = Node(
        package="vgr_bridge", executable="gsl_benchmark_runner", name="gsl_benchmark_runner",
        output="screen", parameters=[{
            "algorithm": "PMFS", "method": "B4_PMFS_official",
            "run_id": LC("run_id"), "run_dir": LC("run_dir"),
            "output_dir": LC("run_dir"),
            "repo_root": LC("repo_root"),
            "environment_id": LC("environment_id"), "scenario_id": LC("scenario_id"),
            "dataset": LC("house"), "config_id": LC("config_id"),
            "source_config": "official_gaden_source", "wind_config": "vgr_ground_truth_service",
            "sensor_config": "fopdt_tau1p2_dead0p4_noise0",
            "start_config": "frozen_native_start",
            "source_x": _typed("source_x", float), "source_y": _typed("source_y", float),
            "seed": _typed("seed", int), "flight_height_m": _typed("flight_height", float),
            "time_budget_s": _typed("timeout_sec", float), "path_budget_m": -1.0,
            "sensor_trace_file": _file("sensor_trace.csv"),
            "wind_trace_file": _file("wind_trace.csv"),
            "pose_trace_file": _file("sim_pose_trace.csv"),
        }],
    )
    args += [sim, TimerAction(period=5.0, actions=[pmfs, benchmark])]
    args.append(TimerAction(period=8.0, actions=[ExecuteProcess(
        cmd=["ros2", "service", "call", "/start_simulation", "std_srvs/srv/Trigger", "{}"],
        output="screen")]))
    return LaunchDescription(args)
