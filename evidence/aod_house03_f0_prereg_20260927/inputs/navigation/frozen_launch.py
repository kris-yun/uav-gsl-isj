"""Development launch for the RMFE activation/paired protocol.

This launch is not itself evidence of a closed-loop performance gain.  The
runner must bind it to a fresh run directory, a run UUID, code/bank hashes and
an auditable paired-condition manifest.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition
from launch_ros.parameter_descriptions import ParameterValue


def _float(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=float)


def _bool(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=bool)


def _int(name: str):
    return ParameterValue(LaunchConfiguration(name), value_type=int)


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
        # Optional deterministic measurement contract.  The experiment scripts
        # pass the same fixed block to both arms to remove wall-clock jitter.
        DeclareLaunchArgument('measurement_settle_samples', default_value='-1'),
        DeclareLaunchArgument('measurement_block_samples', default_value='-1'),
        DeclareLaunchArgument('measurement_deduplicate_sim_timestamps', default_value='false'),
        # The VGR bridge deliberately refuses a legacy concentration fallback.
        # Supply the exact GADEN playback realization used by both arms.
        DeclareLaunchArgument('gaden_realization_path', default_value=''),
        DeclareLaunchArgument('gaden_initial_iteration', default_value='1196'),
        # FOPDT evidence operator. Defaults reproduce the current VGR sensor;
        # the PMFS branch stays OFF until the isolated parity gate passes.
        DeclareLaunchArgument('dynamic_evidence_enabled', default_value='false'),
        DeclareLaunchArgument('dynamic_route_evidence_enabled', default_value='false'),
        DeclareLaunchArgument('sensor_tau_rise_s', default_value='1.2'),
        DeclareLaunchArgument('sensor_tau_recovery_s', default_value='1.2'),
        DeclareLaunchArgument('sensor_dead_time_s', default_value='0.4'),
        DeclareLaunchArgument('sensor_gain', default_value='1.0'),
        DeclareLaunchArgument('sensor_baseline_ppm', default_value='0.0'),
        DeclareLaunchArgument('sensor_drift_rate_ppm_s', default_value='0.0'),
        DeclareLaunchArgument('sensor_noise_std_ppm', default_value='0.0'),
        DeclareLaunchArgument('sim_dt_s', default_value='0.2'),
        # PMFS source-update cadence is an explicit common-condition
        # parameter.  The default preserves the historical baseline; paired
        # causal runs may freeze a faster cadence so that a live evidence
        # stream is actually consumed more than once, without changing it
        # between OFF and ON.
        DeclareLaunchArgument('pmfs_steps_source_update', default_value='10'),
        DeclareLaunchArgument('pmfs_initial_exploration_moves', default_value='2'),
        DeclareLaunchArgument('pmfs_max_updates_per_stop', default_value='3'),
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
        # TCEE C1: a frozen route is used only to export candidate-conditioned
        # sequential responses.  No posterior or eligibility-graph update is
        # connected at this stage.
        DeclareLaunchArgument('tcee_route_export_enabled', default_value='false'),
        DeclareLaunchArgument('tcee_route_file', default_value=''),
        DeclareLaunchArgument('tcee_route_output_directory', default_value=''),

        # ---- RMFE opt-in switches (added for closed-loop pilot) ----
        DeclareLaunchArgument('rmfe_enabled', default_value='false'),
        DeclareLaunchArgument('rmfe_epsilon', default_value='1e-12'),
        DeclareLaunchArgument('rmfe_max_factor_age_s', default_value='32.0'),
        DeclareLaunchArgument('rmfe_model_weight', default_value='1.0'),
        DeclareLaunchArgument('rmfe_baseline_samples', default_value='0'),
        DeclareLaunchArgument('rmfe_bank_sha256', default_value=''),
        DeclareLaunchArgument('rmfe_score_semantics',
                              default_value='PROFILE_COHERENCE_CUMULATIVE_V1'),
        DeclareLaunchArgument('rmfe_factor_file', default_value=''),
        DeclareLaunchArgument('rmfe_block_trace_file', default_value=''),
        DeclareLaunchArgument('geometry_export_dir', default_value=''),
        DeclareLaunchArgument('rmfe_house', default_value='H01'),
        DeclareLaunchArgument('rmfe_bank_dir', default_value=''),
        DeclareLaunchArgument('rmfe_evidence_enabled', default_value='false'),
        DeclareLaunchArgument('rmfe_evidence_script',
                              default_value='/home/zyc/rmfe_pmfs_closedloop_v1/rmfe_evidence_node.py'),
        DeclareLaunchArgument('rmfe_causal_fixed_amplitude', default_value='false'),
        DeclareLaunchArgument('rmfe_causal_sigma', default_value='1.0'),
        DeclareLaunchArgument('rmfe_causal_amplitude_mean', default_value='1.0'),
        DeclareLaunchArgument('rmfe_causal_amplitude_std', default_value='0.0'),
        DeclareLaunchArgument('rmfe_causal_temporal_rho', default_value='0.8464817249'),
        DeclareLaunchArgument('rmfe_causal_log_floor', default_value='-3.0'),
        DeclareLaunchArgument('rmfe_causal_log_cap', default_value='3.0'),
        DeclareLaunchArgument('rmfe_causal_sensor_lag_ensemble', default_value='false'),
        DeclareLaunchArgument('rmfe_causal_lag_scales', default_value='0.8,1.0,1.2'),
        DeclareLaunchArgument('rmfe_support_aware', default_value='false'),
        DeclareLaunchArgument('rmfe_support_radius_m', default_value=''),

        # GADEN's official replay service: VGR requests /frame_query at each
        # simulator tick, so both PMFS arms see the identical realization.
        Node(
            package='gaden_player',
            executable='player',
            name='gaden_player',
            output='screen',
            parameters=[{
                'num_simulators': 1,
                'simulation_data_0': LaunchConfiguration('gaden_realization_path'),
                'occupancyFile': PathJoinSubstitution([LaunchConfiguration('vgr_data_path'), 'OccupancyGrid3D.csv']),
                'initial_iteration': _int('gaden_initial_iteration'),
                'player_freq': 1.0,
                'manual_iteration_mode': True,
            }],
        ),

        # VGR UAV Simulator.  Wait for gaden_player to load and advertise
        # /frame_query before constructing the bridge client.
        TimerAction(
            period=5.0,
            actions=[Node(
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
                'gas_backend': 'gaden_player',
                'gaden_iteration_mode': 'seeded_time_replay',
                'realtime_factor': 1.0,
                'sensor_tau_rise_s': _float('sensor_tau_rise_s'),
                'sensor_tau_recovery_s': _float('sensor_tau_recovery_s'),
                'sensor_dead_time_s': _float('sensor_dead_time_s'),
                'sensor_gain': _float('sensor_gain'),
                'sensor_baseline_ppm': _float('sensor_baseline_ppm'),
                'sensor_drift_rate_ppm_s': _float('sensor_drift_rate_ppm_s'),
                'sensor_noise_std_ppm': _float('sensor_noise_std_ppm'),
                'sim_dt_s': _float('sim_dt_s'),
                'sensor_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'vgr_sensor_trace.csv']),
                'measurement_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'vgr_measurement_trace.csv']),
                'continuous_measurement_samples_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'vgr_continuous_samples.csv']),
                'sensor_manifest_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'vgr_sensor_manifest.json']),
            }],
        )],
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
                        # Search time is VGR /clock simulation time.  Leaving
                        # this false spends budget during pre-start setup.
                        'use_sim_time': True,
                        'maxSearchTime': _float('timeout_sec'),
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
                        # Handshake contract: the runner starts the simulator
                        # only after PMFS has subscribed and initialized.
                        'evidence_ready_file': PathJoinSubstitution([
                            LaunchConfiguration('run_dir'),
                            'pmfs_evidence_ready.marker',
                        ]),
                        'method': LaunchConfiguration('algorithm'),
                        # Frozen B0-R geometry/PMFS contract.  A coarse scale
                        # of 25 removes every usable cell in H01; scale 3 is
                        # the validated native baseline resolution.
                        'scale': 3,
                        'useWindGroundTruth': False,
                        'anemometer_frame': 'base_link',
                        # A localization evaluation must consume the declared
                        # simulation-time budget.  A negative variance gate
                        # cannot fire, so neither arm can report an empty-map
                        # "success" before the 60 s budget has elapsed.
                        'convergence_thr': -1.0,
                        'sourceDiscriminationPower': 1.0,
                        'refineFraction': 0.25,
                        'stepsSourceUpdate': _int('pmfs_steps_source_update'),
                        'maxRegionSize': 5,
                        'deltaTime': 0.2,
                        'noiseSTDev': 0.5,
                        'iterationsToRecord': 200,
                        'maxWarmupIterations': 500,
                        'minWarmupIterations': 200,
                        'blurSigmaX': 0.0,
                        'blurSigmaY': 0.0,
                        'hitPriorProbability': 0.1,
                        'maxUpdatesPerStop': _int('pmfs_max_updates_per_stop'),
                        'kernelSigma': 0.5,
                        'kernelStretchConstant': 1.5,
                        'confidenceMeasurementWeight': 0.5,
                        'confidenceSigmaSpatial': 0.5,
                        'localEstimationWindowSize': 2,
                        'openMoveSetExpasion': 5,
                        'explorationProbability': 0.05,
                        'initialExplorationMoves': _int('pmfs_initial_exploration_moves'),
                        'distanceWeight': 0.15,
                        'markers_height': 0.2,
                        'th_gas_present': 0.1,
                        'th_wind_present': 0.1,
                        'stop_and_measure_time': 2.0,
                        'measurement_settle_samples': _int('measurement_settle_samples'),
                        'measurement_block_samples': _int('measurement_block_samples'),
                        'measurement_deduplicate_sim_timestamps': _bool('measurement_deduplicate_sim_timestamps'),
                        'diagnostic_continue': True,
                        'dynamic_evidence_enabled': _bool('dynamic_evidence_enabled'),
                        'dynamic_route_evidence_enabled': _bool('dynamic_route_evidence_enabled'),
                        'dynamic_sensor_tau_rise_s': _float('sensor_tau_rise_s'),
                        'dynamic_sensor_tau_recovery_s': _float('sensor_tau_recovery_s'),
                        'dynamic_sensor_dead_time_s': _float('sensor_dead_time_s'),
                        'dynamic_sensor_gain': _float('sensor_gain'),
                        'dynamic_sensor_baseline_ppm': _float('sensor_baseline_ppm'),
                        'dynamic_sensor_drift_rate_ppm_s': _float('sensor_drift_rate_ppm_s'),
                        'dynamic_evidence_trace_file': PathJoinSubstitution([LaunchConfiguration('run_dir'), 'dynamic_evidence_trace.csv']),
                        'hover_forward_export_enabled': LaunchConfiguration('hover_forward_export_enabled'),
                        'hover_forward_export_complete_grid': LaunchConfiguration('hover_forward_export_complete_grid'),
                        'hover_forward_export_every_measurement': LaunchConfiguration('hover_forward_export_every_measurement'),
                        'hover_forward_export_continuous_exposure': LaunchConfiguration('hover_forward_export_continuous_exposure'),
                        'hover_forward_export_directory': LaunchConfiguration('hover_forward_export_directory'),
                        'hover_forward_pmfs_parameters_hash': LaunchConfiguration('hover_forward_pmfs_parameters_hash'),
                        'hover_forward_map_hash': LaunchConfiguration('hover_forward_map_hash'),
                        'hover_forward_wind_hash': LaunchConfiguration('hover_forward_wind_hash'),
                        'hover_forward_code_hash': LaunchConfiguration('hover_forward_code_hash'),
                        'tcee_route_export_enabled': _bool('tcee_route_export_enabled'),
                        'tcee_route_file': LaunchConfiguration('tcee_route_file'),
                        'tcee_route_output_directory': LaunchConfiguration('tcee_route_output_directory'),
                        'tcee_sensor_tau_rise_s': _float('sensor_tau_rise_s'),
                        'tcee_sensor_tau_recovery_s': _float('sensor_tau_recovery_s'),
                        'tcee_sensor_dead_time_s': _float('sensor_dead_time_s'),
                        'tcee_sensor_gain': _float('sensor_gain'),
                        'tcee_sensor_baseline': _float('sensor_baseline_ppm'),
                        # ---- RMFE ----
                        'rmfe_enabled': _bool('rmfe_enabled'),
                        'rmfe_epsilon': _float('rmfe_epsilon'),
                        'rmfe_max_factor_age_s': _float('rmfe_max_factor_age_s'),
                        'rmfe_model_weight': _float('rmfe_model_weight'),
                        'rmfe_bank_sha256': LaunchConfiguration('rmfe_bank_sha256'),
                        'rmfe_score_semantics': LaunchConfiguration('rmfe_score_semantics'),
                        'rmfe_factor_file': LaunchConfiguration('rmfe_factor_file'),
                        'rmfe_block_trace_file': LaunchConfiguration('rmfe_block_trace_file'),
                        'geometry_export_dir': LaunchConfiguration('geometry_export_dir'),
                    }],
                ),
            ],
        ),

        # Submit the goal while VGR remains paused, then start /clock only
        # after PMFS writes its explicit readiness marker.  This removes the
        # launch-order race without changing flight or sensing budget.
        TimerAction(
            period=15.0,
            actions=[
                ExecuteProcess(
                    cmd=['python3', '/home/zyc/tcee_route_sets_v1/fopdt_active_runner.py'],
                    output='screen',
                    additional_env={
                        'FOPDT_ALGORITHM': LaunchConfiguration('algorithm'),
                        'FOPDT_RUN_ID': LaunchConfiguration('run_id'),
                        'FOPDT_RUN_DIR': LaunchConfiguration('run_dir'),
                        'FOPDT_TIMEOUT_SEC': LaunchConfiguration('timeout_sec'),
                        'FOPDT_READY_FILE': PathJoinSubstitution([
                            LaunchConfiguration('run_dir'),
                            'pmfs_evidence_ready.marker',
                        ]),
                    },
                ),
            ],
        ),

        # ---- RMFE evidence adapter (concurrent, opt-in) ----
        TimerAction(
            period=20.0,
            condition=IfCondition(LaunchConfiguration('rmfe_evidence_enabled')),
            actions=[
                ExecuteProcess(
                    cmd=['python3', LaunchConfiguration('rmfe_evidence_script'),
                         '--house', LaunchConfiguration('rmfe_house'),
                         '--run_uuid', LaunchConfiguration('run_id'),
                         '--run_dir', LaunchConfiguration('run_dir'),
                         '--bank_dir', LaunchConfiguration('rmfe_bank_dir'),
                         '--factor_file', LaunchConfiguration('rmfe_factor_file'),
                         '--geometry_export_dir', LaunchConfiguration('geometry_export_dir'),
                         '--block_samples', '80',
                         '--baseline_samples', LaunchConfiguration('rmfe_baseline_samples'),
                         '--epsilon', LaunchConfiguration('rmfe_epsilon'),
                         '--max_sim_s', LaunchConfiguration('timeout_sec')],
                    additional_env={
                        'RMFE_CAUSAL_FIXED_AMPLITUDE': LaunchConfiguration('rmfe_causal_fixed_amplitude'),
                        'RMFE_CAUSAL_SIGMA': LaunchConfiguration('rmfe_causal_sigma'),
                        'RMFE_CAUSAL_AMPLITUDE_MEAN': LaunchConfiguration('rmfe_causal_amplitude_mean'),
                        'RMFE_CAUSAL_AMPLITUDE_STD': LaunchConfiguration('rmfe_causal_amplitude_std'),
                        'RMFE_CAUSAL_TEMPORAL_RHO': LaunchConfiguration('rmfe_causal_temporal_rho'),
                        'RMFE_CAUSAL_LOG_FLOOR': LaunchConfiguration('rmfe_causal_log_floor'),
                        'RMFE_CAUSAL_LOG_CAP': LaunchConfiguration('rmfe_causal_log_cap'),
                        'RMFE_CAUSAL_SENSOR_LAG_ENSEMBLE': LaunchConfiguration('rmfe_causal_sensor_lag_ensemble'),
                        'RMFE_CAUSAL_LAG_SCALES': LaunchConfiguration('rmfe_causal_lag_scales'),
                        'RMFE_SUPPORT_AWARE': LaunchConfiguration('rmfe_support_aware'),
                        'RMFE_SUPPORT_RADIUS_M': LaunchConfiguration('rmfe_support_radius_m'),
                    },
                    output='screen',
                ),
            ],
        ),
    ])
