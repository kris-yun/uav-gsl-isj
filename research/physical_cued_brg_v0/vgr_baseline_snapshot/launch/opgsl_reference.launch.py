"""OPGSL reference run launch file.

Runs OPGSL with full module activation logging.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('vgr_data_path', default_value=''),
        DeclareLaunchArgument('config_id', default_value='2,4-1_fast'),
        DeclareLaunchArgument('run_id', default_value='opgsl_ref'),
        DeclareLaunchArgument('run_dir', default_value='/tmp/opgsl_runs/ref'),
        DeclareLaunchArgument('source_x', default_value='-0.40'),
        DeclareLaunchArgument('source_y', default_value='-2.90'),
        DeclareLaunchArgument('source_z', default_value='-0.30'),
        DeclareLaunchArgument('start_x', default_value='-3.17'),
        DeclareLaunchArgument('start_y', default_value='-1.75'),
        DeclareLaunchArgument('seed', default_value='0'),
        DeclareLaunchArgument('flight_height', default_value='0.3'),
        DeclareLaunchArgument('timeout_sec', default_value='300.0'),

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
                        'source_estimate_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'source_estimate_trace.csv']),
                        'wait_diag_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'wait_for_gas_diag.csv']),
                        'run_uuid': LaunchConfiguration('run_id'),
                        'method': 'OPGSL',
                        'useWindGroundTruth': True,
                        'anemometer_frame': 'base_link',
                        'th_gas_present': 0.1,
                        'th_wind_present': 0.1,
                        'stop_and_measure_time': 2.0,
                        'opgsl.trace.module_activation': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'module_activation_trace.csv']),
                        'opgsl.trace.waypoint_candidate': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'waypoint_candidate_trace.csv']),
                        'opgsl.trace.stop_decision': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'stop_decision_trace.csv']),
                        'opgsl.mcos.observation_audit_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'mcos_observation_trace.csv']),
                    }],
                ),
            ],
        ),

        TimerAction(
            period=15.0,
            actions=[
                Node(
                    package='vgr_bridge',
                    executable='gsl_pilot_runner',
                    name='gsl_pilot_runner',
                    output='screen',
                    parameters=[{
                        'algorithm': 'OPGSL',
                        'run_id': LaunchConfiguration('run_id'),
                        'run_dir': LaunchConfiguration('run_dir'),
                    }],
                ),
            ],
        ),
    ])
