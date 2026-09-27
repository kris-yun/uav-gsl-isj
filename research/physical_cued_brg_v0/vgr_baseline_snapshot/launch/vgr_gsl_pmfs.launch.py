"""Canonical SAISC-PF/VGR launch file for auditable reruns.

This file intentionally disables GT-proximity source declaration by setting
`distanceThreshold=-1.0`. Ground-truth source coordinates are still passed to
GSL only so result loggers can compute offline evaluation metrics. Algorithms
must not call GT in their online decision/declaration logic.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _int(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=int)


def _bool(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=bool)

def _float(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=float)


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('vgr_data_path', default_value=''),
        DeclareLaunchArgument('config_id', default_value='2,4-1_fast'),
        DeclareLaunchArgument('algorithm', default_value='SensorAwareSurgeCastPF'),
        DeclareLaunchArgument('method', default_value='M7_full_saisc_pf'),
        DeclareLaunchArgument('method_family', default_value='proposed_ablation'),
        DeclareLaunchArgument('ablation_id', default_value='M7'),
        DeclareLaunchArgument('run_id', default_value='UNSET_RUN_ID'),
        DeclareLaunchArgument('run_dir', default_value='/tmp/gsl_runs/UNSET_RUN_ID'),
        DeclareLaunchArgument('output_dir', default_value='/tmp/gsl_runs'),
        DeclareLaunchArgument('git_commit', default_value='UNKNOWN'),
        DeclareLaunchArgument('parameter_manifest_sha256', default_value='UNKNOWN'),
        DeclareLaunchArgument('scenario_manifest_sha256', default_value='UNKNOWN'),
        DeclareLaunchArgument('code_manifest_sha256', default_value='UNKNOWN'),

        DeclareLaunchArgument('environment_id', default_value='VGR_House01'),
        DeclareLaunchArgument('scenario_id', default_value='house01_default'),
        DeclareLaunchArgument('dataset', default_value='VGR_House01'),
        DeclareLaunchArgument('source_config', default_value='official_gaden_source'),
        DeclareLaunchArgument('wind_config', default_value='official_gaden_wind'),
        DeclareLaunchArgument('sensor_config', default_value='dynamic_pid_tau1p2_4p0_noise'),
        DeclareLaunchArgument('start_config', default_value='start_default'),

        DeclareLaunchArgument('source_x', default_value='-0.40'),
        DeclareLaunchArgument('source_y', default_value='-2.90'),
        DeclareLaunchArgument('source_z', default_value='-0.30'),
        DeclareLaunchArgument('start_x', default_value='-5.0'),
        DeclareLaunchArgument('start_y', default_value='-5.0'),
        DeclareLaunchArgument('seed', default_value='0'),
        DeclareLaunchArgument('flight_height', default_value='1.0'),
        DeclareLaunchArgument('timeout_sec', default_value='300.0'),
        DeclareLaunchArgument('path_budget_m', default_value='-1.0'),

        DeclareLaunchArgument('use_sdbe', default_value='1'),
        DeclareLaunchArgument('use_kb_tme', default_value='0'),
        DeclareLaunchArgument('use_av_rise', default_value='0'),
        DeclareLaunchArgument('use_entropy_only_active', default_value='0'),
        DeclareLaunchArgument('use_iasc', default_value='1'),
        DeclareLaunchArgument('use_sepf', default_value='1'),
        DeclareLaunchArgument('use_sage', default_value='0'),
        DeclareLaunchArgument('use_sapa_hpa', default_value='0'),
        DeclareLaunchArgument('use_sapa_sig', default_value='0'),
        DeclareLaunchArgument('use_beacon', default_value='0'),
        DeclareLaunchArgument('use_beacon_tr', default_value='0'),
        DeclareLaunchArgument('use_pcrd', default_value='0'),
        DeclareLaunchArgument('use_hmm', default_value='0'),
        DeclareLaunchArgument('temperature_tau', default_value='1.0'),
        DeclareLaunchArgument('tau_adaptive', default_value='0'),
        DeclareLaunchArgument('tau_ess_target_ratio', default_value='0.5'),
        DeclareLaunchArgument('tau_alpha', default_value='0.3'),
        DeclareLaunchArgument('use_tpp', default_value='0'),
        DeclareLaunchArgument('infoTaxis', default_value='false'),
        DeclareLaunchArgument('use_infotaxis', default_value='false'),
        DeclareLaunchArgument('use_pgn', default_value='0'),
        DeclareLaunchArgument('use_evidence_splat_beacon', default_value='0'),
        DeclareLaunchArgument('sensor_model_mode', default_value='dynamic'),
        DeclareLaunchArgument('gaden_iteration_mode', default_value='seeded_time_replay'),
        DeclareLaunchArgument('repo_root', default_value='/home/zyc/gsl_ws/src/GasSourceLocalization'),
        DeclareLaunchArgument('scenario_id', default_value='house01_default'),
        DeclareLaunchArgument('source_config', default_value='official_gaden_source'),
        DeclareLaunchArgument('wind_config', default_value='official_gaden_wind'),
        DeclareLaunchArgument('sensor_config', default_value='dynamic_pid_tau1p2_4p0_noise'),
        DeclareLaunchArgument('start_config', default_value='start_A'),
        DeclareLaunchArgument('parameter_manifest_json', default_value=''),
        DeclareLaunchArgument('scenario_manifest_json', default_value=''),


        Node(
            package='vgr_bridge',
            executable='vgr_sim_node',
            name='vgr_uav_sim',
            output='screen',
            parameters=[{
                'vgr_data_path': LaunchConfiguration('vgr_data_path'),
                'config_id': LaunchConfiguration('config_id'),
                'environment_id': LaunchConfiguration('environment_id'),
                'scenario_id': LaunchConfiguration('scenario_id'),
                'flight_height': _float('flight_height'),
                'start_x': _float('start_x'),
                'start_y': _float('start_y'),
                'seed': _int('seed'),
                'sensor_model_mode': LaunchConfiguration('sensor_model_mode'),
                'gaden_iteration_mode': LaunchConfiguration('gaden_iteration_mode'),
                'sensor_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'sensor_trace.csv']),
                'wind_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'wind_trace.csv']),
                'pose_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'sim_pose_trace.csv']),
            }],
        ),

        # Wind Value Server (direct CSV wind data for PMFS, bypasses DDS service issues)
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

        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='gsl_server',
                    executable='gsl_actionserver_node',
                    name='gsl_server',
                    output='screen',
                    parameters=[{
                'scale': 25,
                'use_infotaxis': _bool('use_infotaxis'),
                'infoTaxis': _bool('infoTaxis'),
                'use_gui': False,
                'maxSearchTime': _float('timeout_sec'),
                'distanceThreshold': -1.0,
                'useWindGroundTruth': True, 'anemometer_frame': 'base_link',
                'wind_csv_dir': PathJoinSubstitution([LaunchConfiguration('vgr_data_path'), 'wind_simulations']),
                'wind_config_id': LaunchConfiguration('config_id'),
                'ground_truth_x': _float('source_x'),
                'ground_truth_y': _float('source_y'),
                'ground_truth_z': _float('source_z'),
                'random_seed': _int('seed'),
                'saisc.use_sdbe': _int('use_sdbe'),
                'saisc.use_kb_tme': _int('use_kb_tme'),
                'saisc.use_av_rise': _int('use_av_rise'),
                'saisc.use_entropy_only_active': _int('use_entropy_only_active'),
                'saisc.use_sapa_hpa': _int('use_sapa_hpa'),
                'saisc.use_sapa_sig': _int('use_sapa_sig'),
                'saisc.use_sage': _int('use_sage'),
                'saisc.use_beacon': _int('use_beacon'),
                'saisc.use_beacon_tr': _int('use_beacon_tr'),
                'saisc.use_evidence_splat_beacon': _int('use_evidence_splat_beacon'),
                'saisc.use_iasc': _int('use_iasc'),
                'saisc.use_sepf': _int('use_sepf'),
                'saisc.use_pcrd': _int('use_pcrd'),
                'saisc.use_pgn': _int('use_pgn'),
                'saisc.use_tpp': _int('use_tpp'),
                'saisc.use_hmm': _int('use_hmm'),
                'saisc.sepf.temperature_tau': _float('temperature_tau'),
                'saisc.sepf.tau_adaptive': _int('tau_adaptive'),
                'saisc.sepf.tau_ess_target_ratio': _float('tau_ess_target_ratio'),
                'saisc.sepf.tau_alpha': _float('tau_alpha'),
                'saisc.audit_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'saisc_pf_audit.csv']),
                'resultsFile': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'official_gsl_results.csv']),
                'pf_estimate_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'pf_estimate.csv']),
                'navigationPathFile': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'official_navigation_path.csv']),
                    }],
                ),
            ],
        ),


        # GMRF Wind Estimation Node (required for PMFS)
        Node(
            package='gmrf_wind_mapping',
            executable='gmrf_wind_mapping_node',
            name='gmrf',
            output='screen',
            parameters=[{
                'frame_id': 'map',
                'sensor_topic': '/Anemometer/WindSensor_reading',
                'map_yaml_file': PathJoinSubstitution([LaunchConfiguration('vgr_data_path'), 'occupancy.yaml']),
                'map_topic': 'map',
                'exec_freq': 10.0,
                'cell_size': 0.3,
                'verbose': False,
                'visualize_gmrf': False,
                'GMRF_lambdaPrior_reg': 0.5,
                'GMRF_lambdaPrior_mass_conservation': 10.0,
                'GMRF_lambdaPrior_obstacles': 1.0,
                'GMRF_lambdaObs': 1.0,
                'GMRF_lambdaObsLoss': 0.0,
            }],
        ),

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
                        'git_commit': LaunchConfiguration('git_commit'),
                        'parameter_manifest_sha256': LaunchConfiguration('parameter_manifest_sha256'),
                        'scenario_manifest_sha256': LaunchConfiguration('scenario_manifest_sha256'),
                        'code_manifest_sha256': LaunchConfiguration('code_manifest_sha256'),
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
                        'source_z': _float('source_z'),
                        'seed': _int('seed'),
                        'flight_height': _float('flight_height'),
                        'timeout_sec': _float('timeout_sec'),
                        'time_budget_s': _float('timeout_sec'),
                        'path_budget_m': _float('path_budget_m'),
                        'use_sdbe': _int('use_sdbe'),
                        'use_iasc': _int('use_iasc'),
                        'use_sepf': _int('use_sepf'),
                        'use_sage': _int('use_sage'),
                        'use_beacon': _int('use_beacon'),
                        'repo_root': LaunchConfiguration('repo_root'),
                        'scenario_id': LaunchConfiguration('scenario_id'),
                        'source_config': LaunchConfiguration('source_config'),
                        'wind_config': LaunchConfiguration('wind_config'),
                        'sensor_config': LaunchConfiguration('sensor_config'),
                        'start_config': LaunchConfiguration('start_config'),
                        'parameter_manifest_json': LaunchConfiguration('parameter_manifest_json'),
                        'scenario_manifest_json': LaunchConfiguration('scenario_manifest_json'),
                        'saisc_audit_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'saisc_pf_audit.csv']),
                        'sensor_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'sensor_trace.csv']),
                        'wind_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'wind_trace.csv']),
                        'pose_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'sim_pose_trace.csv']),
                        'official_pf_result_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'pf_estimate.csv']),
                    }],
                ),
            ],
        ),


    ])
