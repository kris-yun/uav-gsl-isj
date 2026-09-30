"""Frozen existing Native parameter profile; external executable differs only by logger."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument,ExecuteProcess,TimerAction
from launch.substitutions import LaunchConfiguration as LC
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
DEFAULTS=dict(vgr_data_path='',config_id='',house='',run_id='',run_dir='',source_x='0.',source_y='0.',source_z='0.',
    start_x='0.',start_y='0.',time_map='',binary='/home/zyc/d1a_common_replay_20260930/logger_build/gsl_actionserver_node')
NATIVE=dict(scale=3,seed=0,use_sim_time=True,use_gui=False,maxSearchTime=300.,distanceThreshold=-1.,useWindGroundTruth=True,
    anemometer_frame='map',convergence_thr=.5,stepsSourceUpdate=3,maxRegionSize=5,sourceDiscriminationPower=.3,refineFraction=.1,
    deltaTime=.1,noiseSTDev=.5,iterationsToRecord=200,maxWarmupIterations=500,minWarmupIterations=200,blurSigmaX=1.5,blurSigmaY=1.5,
    hitPriorProbability=.3,maxUpdatesPerStop=5,kernelSigma=1.5,kernelStretchConstant=1.5,confidenceMeasurementWeight=1.,
    confidenceSigmaSpatial=1.,localEstimationWindowSize=2,openMoveSetExpasion=5,explorationProbability=.05,initialExplorationMoves=2,
    distanceWeight=.15,markers_height=.2,measurement_settle_samples=0,measurement_block_samples=10,
    measurement_deduplicate_sim_timestamps=True,brg_enabled=False)
def typed(k,t):return ParameterValue(LC(k),value_type=t)
def file(n):return [LC('run_dir'),'/',n]
def generate_launch_description():
    args=[DeclareLaunchArgument(k,default_value=v) for k,v in DEFAULTS.items()]
    sim=Node(package='vgr_bridge',executable='vgr_sim_node',name='vgr_uav_sim',output='screen',parameters=[dict(
        vgr_data_path=LC('vgr_data_path'),config_id=LC('config_id'),environment_id=LC('house'),scenario_id=LC('run_id'),
        flight_height=.3,start_x=typed('start_x',float),start_y=typed('start_y',float),seed=0,sensor_model_mode='dynamic',
        gaden_iteration_mode='recorded_snapshot_time_replay',recorded_snapshot_time_map=LC('time_map'),
        realtime_factor=1.,sim_stop_at_s=300.,gas_backend='gaden_player',raw_query_executable='/bin/true',
        open_loop_profile='',coverage_goal_file='',nav_command_quantum_s=2.,
        sensor_trace_file=file('sensor_trace.csv'),wind_trace_file=file('wind_trace.csv'),pose_trace_file=file('sim_pose_trace.csv'))])
    cmd=[LC('binary'),'--ros-args','-r','__node:=gsl_server']
    for k,v in NATIVE.items():cmd+=['-p',k+':='+str(v).lower()]
    for k in ['ground_truth_x','ground_truth_y','ground_truth_z']:
        cmd+=['-p',[k+':=',LC('source_'+k[-1])]]
    cmd+=['-p',['run_uuid:=',LC('run_id')],'-p','method:=D1A_NATIVE']
    for k,n in dict(measurement_trace_file='measurement_blocks.csv',continuous_measurement_samples_file='measurement_samples.csv',
        resultsFile='official_gsl_results.csv',navigationPathFile='official_navigation_path.csv',navigation_trace_file='navigation_trace.csv').items():
        cmd+=['-p',[k+':=',*file(n)]]
    native=ExecuteProcess(cmd=cmd,output='screen')
    benchmark=Node(package='vgr_bridge',executable='gsl_benchmark_runner',name='gsl_benchmark_runner',output='screen',parameters=[dict(
        algorithm='PMFS',method='B4_PMFS_official',use_sim_time=True,official_pmfs_belief_file=file('beliefs.jsonl'),
        run_id=LC('run_id'),run_dir=LC('run_dir'),output_dir=LC('run_dir'),repo_root='/home/zyc/native_pmfs_recovery_v1/checkout',
        environment_id=LC('house'),scenario_id=LC('run_id'),dataset=LC('house'),config_id=LC('config_id'),
        source_x=typed('source_x',float),source_y=typed('source_y',float),seed=0,flight_height_m=.3,time_budget_s=300.,path_budget_m=-1.,
        sensor_trace_file=file('sensor_trace.csv'),wind_trace_file=file('wind_trace.csv'),pose_trace_file=file('sim_pose_trace.csv'))])
    return LaunchDescription(args+[sim,TimerAction(period=5.,actions=[native,benchmark])])
