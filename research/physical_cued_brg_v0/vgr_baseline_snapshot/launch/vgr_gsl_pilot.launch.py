"""Failure Pilot V1 smoke/baseline launch file.

Runs one method (PMFS, GrGSL, or SurgeCast) with full trace output.
Disables ground-truth proximity stopping (distanceThreshold=-1.0).
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _float(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=float)


def generate_launch_description():
    return LaunchDescription([
        # Scenario
        DeclareLaunchArgument('vgr_data_path', default_value=''),
        DeclareLaunchArgument('config_id', default_value='2,4-1_fast'),
        DeclareLaunchArgument('algorithm', default_value='PMFS'),
        DeclareLaunchArgument('run_id', default_value='smoke_test'),
        DeclareLaunchArgument('run_dir', default_value='/tmp/failure_pilot_v1/smoke'),

        # Source truth (for offline eval only)
        DeclareLaunchArgument('source_x', default_value='-0.40'),
        DeclareLaunchArgument('source_y', default_value='-2.90'),
        DeclareLaunchArgument('source_z', default_value='-0.30'),
        DeclareLaunchArgument('start_x', default_value='-3.17'),
        DeclareLaunchArgument('start_y', default_value='-1.75'),
        DeclareLaunchArgument('seed', default_value='0'),
        DeclareLaunchArgument('flight_height', default_value='0.3'),
        DeclareLaunchArgument('timeout_sec', default_value='300.0'),
        # Optional read-only PMFS forward export. Defaults preserve classical PMFS.
        DeclareLaunchArgument('hover_forward_export_enabled', default_value='false'),
        DeclareLaunchArgument('hover_forward_export_complete_grid', default_value='false'),
        DeclareLaunchArgument('hover_forward_export_every_measurement', default_value='false'),
        DeclareLaunchArgument('hover_forward_export_continuous_exposure', default_value='false'),
        DeclareLaunchArgument('hover_forward_export_directory', default_value=''),
        DeclareLaunchArgument('hover_forward_pmfs_parameters_hash', default_value='UNSET'),
        DeclareLaunchArgument('hover_forward_map_hash', default_value='UNSET'),
        DeclareLaunchArgument('hover_forward_wind_hash', default_value='UNSET'),
        DeclareLaunchArgument('hover_forward_code_hash', default_value='UNSET'),

        # VGR UAV Simulator
        Node(
            package='vgr_bridge',
            executable='vgr_sim_node',
            name='vgr_uav_sim',
            output='screen',
            parameters=[{
                'vgr_data_path': LaunchConfiguration('vgr_data_path'),
                'config_id': LaunchConfiguration('config_id'),
                'flight_height': LaunchConfiguration('flight_height'),
                'start_x': LaunchConfiguration('start_x'),
                'start_y': LaunchConfiguration('start_y'),
                'seed': LaunchConfiguration('seed'),
            }],
        ),

        # Wind Value Server (for PMFS GADEN path)
        Node(
            package='vgr_bridge',
            executable='wind_value_server',
            name='wind_value_server',
            output='screen',
            parameters=[{
                'vgr_data_path': LaunchConfiguration('vgr_data_path'),
                'config_id': LaunchConfiguration('config_id'),
            }],
        ),

        # GMRF Wind Estimation
        Node(
            package='gmrf_wind_mapping',
            executable='gmrf_wind_mapping_node',
            name='gmrf',
            output='screen',
            parameters=[{
                'frame_id': 'map',
                'sensor_topic': '/Anemometer/WindSensor_reading',
                'map_topic': 'map',
                'map_yaml_file': '',
                'exec_freq': 10.0,
                'cell_size': 0.3,
                'verbose': False,
                'visualize_gmrf': False,
            }],
        ),

        # GSL Server (delayed for service discovery)
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='gsl_server',
                    executable='gsl_actionserver_node',
                    name='gsl_server',
                    output='screen',
                    parameters=[{
                        'maxSearchTime': LaunchConfiguration('timeout_sec'),
                        'distanceThreshold': -1.0,
                        'ground_truth_x': LaunchConfiguration('source_x'),
                        'ground_truth_y': LaunchConfiguration('source_y'),
                        'resultsFile': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'official_gsl_results.csv']),
                        'navigationPathFile': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'navigation_path.csv']),
                        'measurement_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'algorithm_measurement_trace.csv']),
                        'continuous_measurement_samples_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'continuous_measurement_samples.csv']),
                        'navigation_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'navigation_episode_trace.csv']),
                        'source_estimate_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'source_estimate_trace.csv']),
                        'wait_diag_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'wait_for_gas_diag.csv']),
                        'run_uuid': LaunchConfiguration('run_id'),
                        'method': LaunchConfiguration('algorithm'),
                        'scale': 25,
                        'useWindGroundTruth': True,
                        'anemometer_frame': 'base_link',
                        'convergence_thr': 1.5,
                        'sourceDiscriminationPower': 0.3,
                        'refineFraction': 0.1,
                        'stepsSourceUpdate': 3,
                        'maxRegionSize': 5,
                        'deltaTime': 0.1,
                        'noiseSTDev': 0.5,
                        'iterationsToRecord': 200,
                        'maxWarmupIterations': 500,
                        'minWarmupIterations': 0,
                        'blurSigmaX': 1.5,
                        'blurSigmaY': 1.5,
                        'hitPriorProbability': 0.3,
                        'maxUpdatesPerStop': 5,
                        'kernelSigma': 1.5,
                        'kernelStretchConstant': 1.5,
                        'confidenceMeasurementWeight': 1.0,
                        'confidenceSigmaSpatial': 1.0,
                        'localEstimationWindowSize': 2,
                        'openMoveSetExpasion': 5,
                        'explorationProbability': 0.05,
                        'initialExplorationMoves': 2,
                        'distanceWeight': 0.15,
                        'markers_height': 0.2,
                        'th_gas_present': 0.1,
                        'th_wind_present': 0.1,
                        'stop_and_measure_time': 2.0,
                        'diagnostic_continue': True,
                        'hover_forward_export_enabled': LaunchConfiguration('hover_forward_export_enabled'),
                        'hover_forward_export_complete_grid': LaunchConfiguration('hover_forward_export_complete_grid'),
                        'hover_forward_export_every_measurement': LaunchConfiguration('hover_forward_export_every_measurement'),
                        'hover_forward_export_continuous_exposure': LaunchConfiguration('hover_forward_export_continuous_exposure'),
                        'hover_forward_export_directory': LaunchConfiguration('hover_forward_export_directory'),
                        'hover_forward_pmfs_parameters_hash': LaunchConfiguration('hover_forward_pmfs_parameters_hash'),
                        'hover_forward_map_hash': LaunchConfiguration('hover_forward_map_hash'),
                        'hover_forward_wind_hash': LaunchConfiguration('hover_forward_wind_hash'),
                        'hover_forward_code_hash': LaunchConfiguration('hover_forward_code_hash'),
                    }],
                ),
            ],
        ),

        # Pilot Runner (delayed start)
        TimerAction(
            period=15.0,
            actions=[
                Node(
                    package='vgr_bridge',
                    executable='gsl_pilot_runner',
                    name='gsl_pilot_runner',
                    output='screen',
                    parameters=[{
                        'algorithm': LaunchConfiguration('algorithm'),
                        'run_id': LaunchConfiguration('run_id'),
                        'run_dir': LaunchConfiguration('run_dir'),
                        'timeout_sec': _float('timeout_sec'),
                        'source_x': LaunchConfiguration('source_x'),
                        'source_y': LaunchConfiguration('source_y'),
                        'source_z': LaunchConfiguration('source_z'),
                        'seed': LaunchConfiguration('seed'),
                    }],
                ),
            ],
        ),
    ])
