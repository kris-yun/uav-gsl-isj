"""Canonical SAISC-PF/VGR launch file for auditable reruns.

This file intentionally disables GT-proximity source declaration by setting
`distanceThreshold=-1.0`. Ground-truth source coordinates are still passed to
GSL only so result loggers can compute offline evaluation metrics. Algorithms
must not call GT in their online decision/declaration logic.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _int(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=int)


def _bool(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=bool)

def _float(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=float)


def _validate_cpir_launch(context):
    """Fail closed before starting ROS nodes when the frozen tape drifts."""
    value = lambda name: LaunchConfiguration(name).perform(context)
    mode = value('pfdi_mode')
    allowed = {'off', 'cpir_m1', 'cpir_a1', 'cpir_a2', 'cpir_a3'}
    if mode not in allowed:
        raise RuntimeError(f'CPIR_MODE_NOT_EXPLICIT:{mode}')
    if value('algorithm') != 'PMFS':
        raise RuntimeError('CPIR_ALGORITHM_MUST_BE_PMFS')
    expected_ablation = {
        'off': 'A0', 'cpir_a1': 'A1', 'cpir_a2': 'A2', 'cpir_a3': 'A3',
        'cpir_m1': 'CPIR_BASE_LEGACY',
    }[mode]
    if value('ablation_id') != expected_ablation:
        raise RuntimeError(
            f'CPIR_ABLATION_MODE_MISMATCH:{value("ablation_id")}:{mode}'
        )
    if abs(float(value('flight_height')) - 0.3) > 1.0e-12:
        raise RuntimeError('CPIR_FLIGHT_HEIGHT_MUST_BE_0P3')
    updates = int(value('maxUpdatesPerStop'))
    block = int(value('measurement_block_samples'))
    if int(value('measurement_settle_samples')) != 0 or updates * block != 80:
        raise RuntimeError('CPIR_STOP_MUST_BE_EXACTLY_80_SAMPLES_WITH_ZERO_SETTLE')
    if abs(float(value('deltaTime')) - 0.2) > 1.0e-12:
        raise RuntimeError('CPIR_DELTA_TIME_MUST_BE_0P2')
    if mode != 'off':
        if not value('cpir_lookup_root') or not value('cpir_audit_directory'):
            raise RuntimeError('CPIR_LOOKUP_AND_AUDIT_PATHS_REQUIRED')
    return []


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('vgr_data_path', default_value=''),
        DeclareLaunchArgument('config_id', default_value='2,4-1_fast'),
        DeclareLaunchArgument('algorithm', default_value='PMFS'),
        DeclareLaunchArgument('method', default_value='CPIR_THREE_MODULE_NESTED'),
        DeclareLaunchArgument('method_family', default_value='cpir_nested'),
        DeclareLaunchArgument('ablation_id', default_value='UNSET'),
        DeclareLaunchArgument('run_id', default_value='UNSET_RUN_ID'),
        DeclareLaunchArgument('run_uuid', default_value='unknown'),
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
        DeclareLaunchArgument('flight_height', default_value='0.3'),
        DeclareLaunchArgument('timeout_sec', default_value='300.0'),
        DeclareLaunchArgument('path_budget_m', default_value='-1.0'),

        # Frozen House1 PMFS runtime contract.  These are explicit launch
        # arguments so the Main-V8 fallback values cannot silently replace
        # the archived experiment contract.
        DeclareLaunchArgument('scale', default_value='3'),
        DeclareLaunchArgument('useWindGroundTruth', default_value='false'),
        DeclareLaunchArgument('convergence_thr', default_value='-1.0'),
        DeclareLaunchArgument('sourceDiscriminationPower', default_value='1.0'),
        DeclareLaunchArgument('refineFraction', default_value='0.25'),
        DeclareLaunchArgument('stepsSourceUpdate', default_value='10'),
        DeclareLaunchArgument('maxRegionSize', default_value='5'),
        DeclareLaunchArgument('deltaTime', default_value='0.2'),
        DeclareLaunchArgument('noiseSTDev', default_value='0.5'),
        DeclareLaunchArgument('iterationsToRecord', default_value='200'),
        DeclareLaunchArgument('maxWarmupIterations', default_value='500'),
        DeclareLaunchArgument('minWarmupIterations', default_value='200'),
        DeclareLaunchArgument('blurSigmaX', default_value='0.0'),
        DeclareLaunchArgument('blurSigmaY', default_value='0.0'),
        DeclareLaunchArgument('hitPriorProbability', default_value='0.1'),
        DeclareLaunchArgument('maxUpdatesPerStop', default_value='8'),
        DeclareLaunchArgument('kernelSigma', default_value='0.5'),
        DeclareLaunchArgument('kernelStretchConstant', default_value='1.5'),
        DeclareLaunchArgument('confidenceMeasurementWeight', default_value='0.5'),
        DeclareLaunchArgument('confidenceSigmaSpatial', default_value='0.5'),
        DeclareLaunchArgument('localEstimationWindowSize', default_value='2'),
        DeclareLaunchArgument('openMoveSetExpasion', default_value='5'),
        DeclareLaunchArgument('explorationProbability', default_value='0.05'),
        DeclareLaunchArgument('initialExplorationMoves', default_value='2'),
        DeclareLaunchArgument('distanceWeight', default_value='0.15'),
        DeclareLaunchArgument('markers_height', default_value='0.2'),
        DeclareLaunchArgument('measurement_settle_samples', default_value='0'),
        DeclareLaunchArgument('measurement_block_samples', default_value='10'),
        # VGR can repeat readiness messages while /clock is paused.  The
        # deterministic closed-loop contract accepts at most one gas/wind
        # observation per simulation timestamp.
        DeclareLaunchArgument('measurement_deduplicate_sim_timestamps', default_value='false'),
        DeclareLaunchArgument('hover_forward_export_enabled', default_value='false'),
        DeclareLaunchArgument('hover_forward_export_directory', default_value=''),
        DeclareLaunchArgument('hover_forward_export_every_measurement', default_value='false'),
        DeclareLaunchArgument('hover_forward_export_complete_grid', default_value='false'),
        DeclareLaunchArgument('hover_forward_export_continuous_exposure', default_value='false'),
        DeclareLaunchArgument('hover_forward_pmfs_parameters_hash', default_value='UNSET'),
        DeclareLaunchArgument('hover_forward_map_hash', default_value='UNSET'),
        DeclareLaunchArgument('hover_forward_wind_hash', default_value='UNSET'),
        DeclareLaunchArgument('hover_forward_code_hash', default_value='UNSET'),
        DeclareLaunchArgument('p2_shadow_enabled', default_value='false'),
        DeclareLaunchArgument('p2_shadow_directory', default_value=''),
        DeclareLaunchArgument('p2_global_seed', default_value='0'),
        DeclareLaunchArgument('p2_shadow_replicas', default_value='0'),
        DeclareLaunchArgument('p2_transport_substream', default_value='5788047269812129363'),
        DeclareLaunchArgument('tadm_enabled', default_value='false'),
        # Every CPIR/A0 run must select its arm explicitly.
        DeclareLaunchArgument('pfdi_mode', default_value='UNSET'),
        # CPIR is an isolated source-channel replacement.  These paths are
        # explicit launch arguments so the node cannot silently use a stale
        # lookup or audit directory.
        DeclareLaunchArgument('cpir_lookup_root', default_value=''),
        DeclareLaunchArgument('cpir_audit_directory', default_value=''),
        DeclareLaunchArgument('tadm_directory', default_value=''),
        DeclareLaunchArgument('tadm_prior_set', default_value='0'),
        DeclareLaunchArgument('tadm_global_seed', default_value='0'),
        DeclareLaunchArgument('tadm_replicas', default_value='4'),
        DeclareLaunchArgument('tadm_transport_substream', default_value='6077111455669390931'),
        DeclareLaunchArgument('gmrf_update_on_new_observation_only', default_value='false'),
        DeclareLaunchArgument('context_bank_export_enabled', default_value='false'),
        DeclareLaunchArgument('context_bank_export_directory', default_value=''),

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
        # Keep the simulator replay below the callback/service saturation
        # point.  At 4x, the wall-clock PMFS loop can batch different numbers
        # of deterministic simulation ticks across repeated runs.
        DeclareLaunchArgument('realtime_factor', default_value='1.0'),
        DeclareLaunchArgument('sim_stop_at_s', default_value='-1.0'),
        DeclareLaunchArgument('nav_command_quantum_s', default_value='2.0'),
        DeclareLaunchArgument('gas_backend', default_value='raw_house1_snapshot'),
        DeclareLaunchArgument('raw_query_executable', default_value='/dev/shm/house1_raw_query'),
        DeclareLaunchArgument('raw_env_root', default_value=''),
        DeclareLaunchArgument('raw_gas_results', default_value=''),
        DeclareLaunchArgument('repo_root', default_value='/home/zyc/gsl_ws/src/GasSourceLocalization'),
        DeclareLaunchArgument('parameter_manifest_json', default_value=''),
        DeclareLaunchArgument('scenario_manifest_json', default_value=''),


        OpaqueFunction(function=_validate_cpir_launch),

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
                'realtime_factor': _float('realtime_factor'),
                'sim_stop_at_s': _float('sim_stop_at_s'),
                'nav_command_quantum_s': _float('nav_command_quantum_s'),
                'gas_backend': LaunchConfiguration('gas_backend'),
                'raw_query_executable': LaunchConfiguration('raw_query_executable'),
                'raw_env_root': LaunchConfiguration('raw_env_root'),
                'raw_gas_results': LaunchConfiguration('raw_gas_results'),
                'sensor_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'sensor_trace.csv']),
                'wind_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'wind_trace.csv']),
                'pose_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'sim_pose_trace.csv']),
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
                'scale': _int('scale'),
                'use_infotaxis': _bool('use_infotaxis'),
                'infoTaxis': _bool('infoTaxis'),
                'use_gui': False,
                'maxSearchTime': _float('timeout_sec'),
                'distanceThreshold': -1.0,
                'useWindGroundTruth': _bool('useWindGroundTruth'), 'anemometer_frame': 'map',
                'ground_truth_x': _float('source_x'),
                'ground_truth_y': _float('source_y'),
                'ground_truth_z': _float('source_z'),
                'random_seed': _int('seed'),
                'run_uuid': LaunchConfiguration('run_uuid'),
                'convergence_thr': _float('convergence_thr'),
                'sourceDiscriminationPower': _float('sourceDiscriminationPower'),
                'refineFraction': _float('refineFraction'),
                'stepsSourceUpdate': _int('stepsSourceUpdate'),
                'maxRegionSize': _int('maxRegionSize'),
                'deltaTime': _float('deltaTime'),
                'noiseSTDev': _float('noiseSTDev'),
                'iterationsToRecord': _int('iterationsToRecord'),
                'maxWarmupIterations': _int('maxWarmupIterations'),
                'minWarmupIterations': _int('minWarmupIterations'),
                'blurSigmaX': _float('blurSigmaX'),
                'blurSigmaY': _float('blurSigmaY'),
                'hitPriorProbability': _float('hitPriorProbability'),
                'maxUpdatesPerStop': _int('maxUpdatesPerStop'),
                'kernelSigma': _float('kernelSigma'),
                'kernelStretchConstant': _float('kernelStretchConstant'),
                'confidenceMeasurementWeight': _float('confidenceMeasurementWeight'),
                'confidenceSigmaSpatial': _float('confidenceSigmaSpatial'),
                'localEstimationWindowSize': _int('localEstimationWindowSize'),
                'openMoveSetExpasion': _int('openMoveSetExpasion'),
                'explorationProbability': _float('explorationProbability'),
                'initialExplorationMoves': _int('initialExplorationMoves'),
                'distanceWeight': _float('distanceWeight'),
                'markers_height': _float('markers_height'),
                'measurement_settle_samples': _int('measurement_settle_samples'),
                'measurement_block_samples': _int('measurement_block_samples'),
                'measurement_deduplicate_sim_timestamps': _bool('measurement_deduplicate_sim_timestamps'),
                'hover_forward_export_enabled': _bool('hover_forward_export_enabled'),
                'hover_forward_export_directory': LaunchConfiguration('hover_forward_export_directory'),
                'hover_forward_export_every_measurement': _bool('hover_forward_export_every_measurement'),
                'hover_forward_export_complete_grid': _bool('hover_forward_export_complete_grid'),
                'hover_forward_export_continuous_exposure': _bool('hover_forward_export_continuous_exposure'),
                'hover_forward_pmfs_parameters_hash': LaunchConfiguration('hover_forward_pmfs_parameters_hash'),
                'hover_forward_map_hash': LaunchConfiguration('hover_forward_map_hash'),
                'hover_forward_wind_hash': LaunchConfiguration('hover_forward_wind_hash'),
                'hover_forward_code_hash': LaunchConfiguration('hover_forward_code_hash'),
                'p2_shadow_enabled': _bool('p2_shadow_enabled'),
                'p2_shadow_directory': LaunchConfiguration('p2_shadow_directory'),
                'p2_global_seed': _int('p2_global_seed'),
                'p2_shadow_replicas': _int('p2_shadow_replicas'),
                'p2_transport_substream': _int('p2_transport_substream'),
                'tadm_enabled': _bool('tadm_enabled'),
                # Force a string: YAML parses the literal ``off`` as boolean
                # unless the launch parameter type is explicit.
                'pfdi_mode': ParameterValue(LaunchConfiguration('pfdi_mode'), value_type=str),
                'cpir_lookup_root': LaunchConfiguration('cpir_lookup_root'),
                'cpir_audit_directory': LaunchConfiguration('cpir_audit_directory'),
                'tadm_directory': LaunchConfiguration('tadm_directory'),
                'tadm_prior_set': _int('tadm_prior_set'),
                'tadm_global_seed': _int('tadm_global_seed'),
                'tadm_replicas': _int('tadm_replicas'),
                'tadm_transport_substream': _int('tadm_transport_substream'),
                'context_bank_export_enabled': _bool('context_bank_export_enabled'),
                'context_bank_export_directory': LaunchConfiguration('context_bank_export_directory'),
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
                'update_on_new_observation_only': _bool('gmrf_update_on_new_observation_only'),
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

        # The VGR bridge starts paused by contract.  Start the deterministic
        # clock after all three consumers (sim, GMRF, GSL) are discoverable.
        TimerAction(
            period=8.0,
            actions=[
                ExecuteProcess(
                    cmd=['ros2', 'service', 'call', '/start_simulation',
                         'std_srvs/srv/Trigger', '{}'],
                    output='screen',
                ),
            ],
        ),


    ])
