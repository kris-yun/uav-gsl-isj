"""Launch file with OPGSL altitude parameter forwarding for ablation experiments."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def _int(name):
    return ParameterValue(LaunchConfiguration(name), value_type=int)
def _bool(name):
    return ParameterValue(LaunchConfiguration(name), value_type=bool)
def _float(name):
    return ParameterValue(LaunchConfiguration(name), value_type=float)

def generate_launch_description():
    return LaunchDescription([
        # Core args
        DeclareLaunchArgument('vgr_data_path', default_value=''),
        DeclareLaunchArgument('config_id', default_value='2,4-1_fast'),
        DeclareLaunchArgument('algorithm', default_value='OPGSL'),
        DeclareLaunchArgument('method', default_value='M0_sc_pf_hard_base'),
        DeclareLaunchArgument('source_x', default_value='-0.40'),
        DeclareLaunchArgument('source_y', default_value='-2.90'),
        DeclareLaunchArgument('source_z', default_value='-0.30'),
        DeclareLaunchArgument('start_x', default_value='-0.9'),
        DeclareLaunchArgument('start_y', default_value='0.15'),
        DeclareLaunchArgument('seed', default_value='0'),
        DeclareLaunchArgument('flight_height', default_value='0.3'),
        DeclareLaunchArgument('timeout_sec', default_value='300.0'),
        DeclareLaunchArgument('resultsFile', default_value='/tmp/gsl_result.csv'),
        DeclareLaunchArgument('run_dir', default_value='/tmp/gsl_runs/UNSET'),
        DeclareLaunchArgument('method_family', default_value='proposed_ablation'),
        DeclareLaunchArgument('ablation_id', default_value='M0'),
        DeclareLaunchArgument('run_id', default_value='UNSET_RUN_ID'),
        DeclareLaunchArgument('output_dir', default_value='/tmp/gsl_runs'),
        DeclareLaunchArgument('environment_id', default_value='VGR_House01'),
        DeclareLaunchArgument('scenario_id', default_value='house01_default'),
        DeclareLaunchArgument('dataset', default_value='VGR_House01'),
        DeclareLaunchArgument('source_config', default_value='official_gaden_source'),
        DeclareLaunchArgument('wind_config', default_value='official_gaden_wind'),
        DeclareLaunchArgument('sensor_config', default_value='dynamic_pid_tau1p2_4p0_noise'),
        DeclareLaunchArgument('start_config', default_value='start_default'),
        DeclareLaunchArgument('path_budget_m', default_value='-1.0'),
        DeclareLaunchArgument('repo_root', default_value='/home/zyc/gsl_ws/src/GasSourceLocalization'),

        # OPGSL altitude toggles (KEY ADDITION)
        DeclareLaunchArgument('opgsl_alt_esc', default_value='true'),
        DeclareLaunchArgument('opgsl_alt_levy', default_value='true'),
        DeclareLaunchArgument('opgsl_alt_layer_scan', default_value='true'),
        DeclareLaunchArgument('opgsl_alt_decay', default_value='true'),

        # VGR sim node
        Node(package='vgr_bridge', executable='vgr_sim_node', name='vgr_uav_sim', output='screen',
            parameters=[{
                'vgr_data_path': LaunchConfiguration('vgr_data_path'),
                'config_id': LaunchConfiguration('config_id'),
                'flight_height': _float('flight_height'),
                'start_x': _float('start_x'),
                'start_y': _float('start_y'),
                'seed': _int('seed'),
            }]),

        # GSL server with OPGSL altitude params forwarded
        Node(package='gsl_server', executable='gsl_actionserver_node', name='gsl_server', output='screen',
            parameters=[{
                'use_sim_time': False,
                'maxSearchTime': _float('timeout_sec'),
                'distanceThreshold': -1.0,
                'resultsFile': LaunchConfiguration('resultsFile'),
                'ground_truth_x': _float('source_x'),
                'ground_truth_y': _float('source_y'),
                'navigationPathFile': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'nav_path.csv']),
                # OPGSL altitude toggles (FORWARDED TO ALGORITHM)
                'opgsl.altitude.esc': _bool('opgsl_alt_esc'),
                'opgsl.altitude.levy': _bool('opgsl_alt_levy'),
                'opgsl.altitude.layer_scan': _bool('opgsl_alt_layer_scan'),
                'opgsl.altitude.decay': _bool('opgsl_alt_decay'),
            }]),

        # Benchmark runner
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='vgr_bridge',
                    executable='gsl_benchmark_runner',
                    name='gsl_benchmark_runner',
                    output='screen',
                    parameters=[{
                        'algorithm': LaunchConfiguration('algorithm'),
                        'method': LaunchConfiguration('method'),
                        'method_family': LaunchConfiguration('method_family'),
                        'ablation_id': LaunchConfiguration('ablation_id'),
                        'run_id': LaunchConfiguration('run_id'),
                        'run_dir': LaunchConfiguration('run_dir'),
                        'output_dir': LaunchConfiguration('output_dir'),
                        'environment_id': LaunchConfiguration('environment_id'),
                        'scenario_id': LaunchConfiguration('scenario_id'),
                        'dataset': LaunchConfiguration('dataset'),
                        'config_id': LaunchConfiguration('config_id'),
                        'source_config': LaunchConfiguration('source_config'),
                        'wind_config': LaunchConfiguration('wind_config'),
                        'sensor_config': LaunchConfiguration('sensor_config'),
                        'start_config': LaunchConfiguration('start_config'),
                        'source_x': _float('source_x'),
                        'source_y': _float('source_y'),
                        'seed': _int('seed'),
                        'flight_height_m': _float('flight_height'),
                        'time_budget_s': _float('timeout_sec'),
                        'path_budget_m': _float('path_budget_m'),
                        'repo_root': LaunchConfiguration('repo_root'),
                        'sensor_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'sensor_trace.csv']),
                        'wind_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'wind_trace.csv']),
                        'pose_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'sim_pose_trace.csv']),
                        'saisc_audit_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'saisc_pf_audit.csv']),
                    }],
                ),
            ],
        ),
    ])
