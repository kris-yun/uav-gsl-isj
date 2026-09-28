#!/usr/bin/env python3
"""Deployment-matched V1 adapter around existing ROS Native/VGR/player.

One process group per subprocess; truth stays in benchmark/evaluator only.
Every algorithm/service failure produces a case result instead of fallback.
"""
import argparse,csv,hashlib,json,math,os,re,resource,signal,socket,subprocess,sys,time
from pathlib import Path
import numpy as np
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csvrows(p):
    if not Path(p).exists():return []
    with open(p) as f:return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arm',required=True,choices=['native_pmfs','aod_filter']);ap.add_argument('--case-file',required=True);ap.add_argument('--budget-s',type=float,required=True);ap.add_argument('--output',required=True);ap.add_argument('--domain',type=int,default=228);ap.add_argument('--software-smoke',action='store_true');ap.add_argument('--training-collection',action='store_true');ap.add_argument('--coverage',action='store_true');ap.add_argument('--checkpoint');ap.add_argument('--realtime-factor',type=float,default=5.0);a=ap.parse_args()
    case=json.loads(Path(a.case_file).read_text());out=Path(a.output);run=out.parent/(out.stem+'_raw')
    assert not out.exists() and not run.exists();run.mkdir(parents=True)
    assert 0<=a.domain<=232
    if not a.software_smoke:assert a.budget_s==300
    if a.coverage and (not a.training_collection or a.arm!='native_pmfs' or case['split'] not in ('train','dev')):
        raise RuntimeError('fixed coverage is only for OPEN Native training/development collection')
    if a.checkpoint or a.training_collection or a.coverage or a.software_smoke:
        raise RuntimeError('AOD comparison accepts no neural checkpoint or training/coverage/smoke mode')
    if a.training_collection and a.arm=='native_pmfs' and a.checkpoint:raise RuntimeError('Native has no checkpoint')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    env=dict(os.environ,ROS_DOMAIN_ID=str(a.domain),RMW_IMPLEMENTATION='rmw_fastrtps_cpp',ROS_LOG_DIR=str(run/'ros_log'),
        PYTHONPATH='/home/zyc/brg_closedloop_20260927/vgr_execution_v2:'+os.environ.get('PYTHONPATH',''),
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',BRG_BELIEF_AUDIT_JSONL=str(run/'beliefs.jsonl'))
    for var,name in {'NATIVE_RECOVERY_WIND_QUERY_CSV':'wind_query.csv','NATIVE_RECOVERY_WIND_UPDATE_CSV':'wind_source_update.csv',
        'NATIVE_RECOVERY_MEASUREMENT_EVENTS_CSV':'measurement_events.csv','NATIVE_RECOVERY_MEASURED_MAP_CSV':'measured_map_at_update.csv',
        'NATIVE_RECOVERY_CANDIDATES_CSV':'frozen_candidate_geometry.csv','NATIVE_RECOVERY_UPDATE_COMPLETE_FILE':'source_update_complete.txt'}.items():env[var]=str(run/name)
    view=Path('/dev/shm/brg_case_views')/(out.stem+'_'+hashlib.sha256(str(out.resolve()).encode()).hexdigest()[:8]);view.mkdir(parents=True,exist_ok=False);scenario=Path(case['scenario_root']);wind=case['wind']
    for n in ['OccupancyGrid3D.csv','wind_simulations']:(view/n).symlink_to(scenario/n,target_is_directory=(scenario/n).is_dir())
    gas=view/'gas_simulations'/wind;gas.mkdir(parents=True)
    (gas/'FilamentSimulation_existing_open_case').symlink_to(Path(case['realization']),target_is_directory=True)
    env_index=int(case['environment_index']);assert env_index in (0,1,2,3)
    bank_path=(ROOT/f'legal_support_v2/env_{env_index}_bank.npz' if env_index<3
               else ROOT/'legal_support_v2/h03_native_legal_bank.npz')
    bank=TemplateBank.load(bank_path)
    assert len(bank.ids)==(596 if env_index==0 else 615 if env_index==3 else 630)
    assert case['candidate_support_id']==bank.fingerprint
    assert case['truth_in_support']==(case['source_id'] in bank.ids)
    port=18000+a.domain;children=[];handles=[];commands=[]
    def start(cmd,log,child_env=None):
        f=(run/log).open('w');handles.append(f);commands.append(cmd)
        p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env if child_env is None else child_env,start_new_session=True);children.append(p);return p
    def wait_service(name,typ,timeout=100):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            p=subprocess.run(['ros2','service','type',name],capture_output=True,text=True,env=env,timeout=15)
            if p.returncode==0 and p.stdout.strip()==typ:return
            if any(c.poll() is not None for c in children):raise RuntimeError('runtime child exited during readiness')
            time.sleep(1)
        raise TimeoutError(name+' readiness timeout')
    start_wall=time.monotonic();status='infrastructure_error';reason='not_started';declared=False
    try:
        player='/dev/shm/house2_gaden_install/gaden_player/lib/gaden_player/player'
        start([player,'--ros-args','-r','__node:=gaden_player','-p','num_simulators:=1','-p','simulation_data_0:='+case['realization'],
            '-p','occupancyFile:='+str(scenario/'OccupancyGrid3D.csv'),'-p','initial_iteration:=0','-p','player_freq:=1.0','-p','manual_iteration_mode:=true'],'gaden_player.log')
        wait_service('/frame_query','gaden_msgs/srv/FrameQuery')
        start(['python3','/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/wind_value_server.py','--ros-args','-r','__node:=wind_value_server',
            '-p','vgr_data_path:='+str(view),'-p','config_id:='+wind],'wind_value_server.log')
        wait_service('/wind_value','gaden_msgs/srv/WindPosition')
        if a.arm!='native_pmfs':
            side=start(['python3','/home/zyc/brg_v1_recovery_20260928/aod_filter/serve_aod_filter_vm.py',
                '--calibration','/home/zyc/brg_v1_recovery_20260928/aod_filter/TRAIN_ONLY_CALIBRATION.json',
                '--bank',str(bank_path),
                '--measurement-blocks',str(run/'measurement_blocks.csv'),
                '--measurement-samples',str(run/'measurement_samples.csv'),
                '--sensor-trace',str(run/'sensor_trace.csv'),
                '--trace',str(run/'aod_filter_trace.jsonl'),'--arrays',str(run/'aod_filter_arrays'),
                '--tcp-port',str(port),'--log',str(run/'sidecar_events.jsonl')],'sidecar.log',
                dict(env,PYTHONPATH='/home/zyc/.local/lib/python3.10/site-packages:'+env['PYTHONPATH']))
            for _ in range(100):
                if side.poll() is not None:raise RuntimeError('sidecar initialization failed')
                try:
                    with socket.create_connection(('127.0.0.1',port),.5) as s:
                        s.sendall(b'HELLO\n');assert s.recv(4096).decode().split()[1]==bank.fingerprint
                    break
                except (OSError,AssertionError):time.sleep(.2)
            else:raise TimeoutError('sidecar readiness')
        launch=Path('/home/zyc/brg_v1_recovery_20260928/v1_collection.launch.py') if a.coverage else ROOT/'integration/brg_existing_native.launch.py'
        # The TCP client's RESET grammar admits only ASCII letters, digits, ._-.
        # Case IDs contain wind-name commas, so use an identity-derived token
        # without changing the scientific case ID, seed, plume, or file names.
        run_token='run_'+hashlib.sha256(out.stem.encode('utf-8')).hexdigest()[:32]
        args={'vgr_data_path':str(view),'config_id':wind,'house':case['house'],'environment_id':'VGR_'+case['house'],'scenario_id':case['case_id'],
            'source_x':str(case['truth_xy'][0]),'source_y':str(case['truth_xy'][1]),'source_z':'.2','start_x':str(case['start_xy'][0]),'start_y':str(case['start_xy'][1]),'flight_height':'.2',
            'seed':'0','run_id':out.stem,'run_dir':str(run),'timeout_sec':str(a.budget_s),'realtime_factor':str(a.realtime_factor),'sim_stop_at_s':str(a.budget_s),
            'gas_backend':'gaden_player','raw_query_executable':'/bin/true','shadow_gmrf':'false','convergence_thr':'0.5',
            'recorded_snapshot_time_map':'/dev/null','gaden_iteration_mode':'physical_time_replay_300s','repo_root':'/home/zyc/native_pmfs_recovery_v1/checkout',
            'brg_enabled':str(a.arm!='native_pmfs').lower(),'brg_port':str(port),'brg_candidates':str(len(bank.ids)),'brg_bank_sha256':bank.fingerprint,
            'brg_run_id':run_token,'brg_sensor_offset_z_m':'0.0','pmfs_belief_file':str(run/'beliefs.jsonl')}
        if a.training_collection:args['convergence_thr']='-1.0'
        if a.coverage:
            args.update(coverage_goal_file='/home/zyc/brg_v1_recovery_20260928/coverage_routes/COVERAGE_STOP_GOALS_FREEZE_V3.json',
                        coverage_environment_index=str(env_index))
        child=start(['ros2','launch',str(launch)]+[k+':='+v for k,v in args.items()],'launch.log')
        (run/'runtime_binding.json').write_text(json.dumps({'argv':commands,'effective_launch_args':args,'bank_id':bank.fingerprint,
            'brg_run_token':run_token,
            'bank_file_sha256':sha(bank_path),'software_smoke':a.software_smoke,
            'source_truth_in_sidecar_inputs':False,'candidate_support_count':len(bank.ids),'replay':'causal actual-writer-time snapshot hold; no cyclic or seed offset',
            'training_collection':a.training_collection,'fixed_source_blind_coverage':a.coverage,
            'realtime_factor':a.realtime_factor},indent=2)+'\n')
        deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            if (run/'beliefs.jsonl').exists() and (run/'beliefs.jsonl').stat().st_size:
                initial=json.loads((run/'beliefs.jsonl').read_text().splitlines()[0])
                assert initial['time_s']==0 and initial['search_time_s']==0,'clock advanced before PMFS readiness'
                break
            if child.poll() is not None:raise RuntimeError('launch exited before initialization')
            time.sleep(.2)
        else:raise TimeoutError('PMFS initialization at paused t=0')
        wait_service('/start_simulation','std_srvs/srv/Trigger')
        started=subprocess.run(['ros2','service','call','/start_simulation','std_srvs/srv/Trigger','{}'],
            capture_output=True,text=True,env=env,timeout=30)
        (run/'clock_start.log').write_text(started.stdout+started.stderr)
        if started.returncode or 'success=True' not in started.stdout:raise RuntimeError('simulation clock start failed')
        deadline=time.monotonic()+a.budget_s*6+600
        while time.monotonic()<deadline:
            log=(run/'launch.log').read_text(errors='replace')
            if 'PMFS_NO_VALID_PLAN' in log:
                status='algorithm_error';reason='no_valid_planner_goal';break
            if any(x in log for x in ['Error executing callback', 'AttributeError:', 'Traceback (most recent call last)']):
                status='service_error';reason='planner_callback_exception';break
            if any(x in log for x in ['terminate called','what():','BRG handshake mismatch','BRG/native grid geometry mismatch']):
                status='service_error' if a.arm!='native_pmfs' else 'algorithm_error';reason='runtime_exception';break
            if (run/'run_status.json').exists():
                record=json.loads((run/'run_status.json').read_text());reason=record['status'];declared=reason=='declared_success'
                status='completed' if declared else ('time_budget' if 'timeout' in reason else 'algorithm_error');break
            if child.poll() is not None:status='algorithm_error';reason='launch_exited_without_result';break
            if a.arm!='native_pmfs' and side.poll() is not None:status='service_error';reason='sidecar_exited';break
            time.sleep(.5)
        else:status='infrastructure_error';reason='outer_wall_deadline'
    except Exception as exc:
        reason=type(exc).__name__+': '+str(exc);(run/'infrastructure_error.txt').write_text(reason+'\n')
    finally:
        for child in reversed(children):
            if child.poll() is None:
                try:os.killpg(child.pid,signal.SIGINT)
                except ProcessLookupError:pass
        for child in children:
            try:child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                child.wait()
        for f in handles:f.close()
    beliefs=[];invalid_belief_rows=0
    if (run/'beliefs.jsonl').exists():
        for line in (run/'beliefs.jsonl').read_text().splitlines():
            try:r=json.loads(line)
            except json.JSONDecodeError:
                invalid_belief_rows+=1;continue
            valid=np.isfinite(r['estimate_xy']).all() and np.isfinite(r['source_map']).all() and np.isfinite(r['variance_map']).all()
            if not valid:invalid_belief_rows+=1
            if 0<=r['search_time_s']<=a.budget_s and valid:beliefs.append(r)
    estimate=beliefs[-1]['estimate_xy'] if beliefs else None
    if beliefs:
        row=beliefs[0];assert (row['width'],row['height'])==(bank.nx,bank.ny)
        support_matches=row['free_cells']==bank.cells.tolist()
        if not a.software_smoke:assert support_matches,'native/legal support mismatch'
    log=(run/'launch.log').read_text(errors='replace') if (run/'launch.log').exists() else ''
    nav_failures=(log.count("Couldn't reach the target")+
                  log.count('Waypoint execution geometry violation')+
                  log.count('PMFS_NO_VALID_PLAN'))
    planning_requests=log.count('PLAN_CB: called with goal=')
    planning_returns=log.count('PLAN_CB: returning ')
    nonempty_planning_returns=sum(int(n)>0 for n in re.findall(r'PLAN_CB: returning (\d+) poses',log))
    issued_goals=log.count('Sending goal (')
    timed_out=status=='time_budget'
    if nav_failures and status in ('completed','time_budget'):status='navigation_failure';reason='navigation_failure_recorded'
    if invalid_belief_rows:status='algorithm_error';reason='invalid_or_nonfinite_belief_record'
    poses=csvrows(run/'sim_pose_trace.csv');poses=[r for r in poses if float(r['t_sim_s'])<=a.budget_s]
    xy=np.array([[float(r['x']),float(r['y'])] for r in poses]);truth=np.array(case['truth_xy'])
    path_length=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()) if len(xy)>1 else 0.
    proximity=[float(r['t_sim_s']) for r,x in zip(poses,xy) if np.linalg.norm(x-truth)<=.5]
    events=csvrows(run/'measurement_events.csv');error=float(np.linalg.norm(np.array(estimate)-truth)) if estimate is not None else None
    geometric=int(status in ('completed','time_budget') and error is not None and error<=.5)
    result={k:case[k] for k in ['case_id','source_id','plume_id','initial_pose_id','observation_contract_id','candidate_support_id','truth_xy','truth_in_support','reporting_stratum']}
    result.update(arm=a.arm,budget_s=a.budget_s,status=status,failure_reason=reason,estimate_xy=estimate,
        geometric_success=geometric,final_source_error_m=error,algorithm_declared_success=int(declared),timeout=int(timed_out),
        wrong_declaration=int(declared and (error is None or error>.5)),declaration_time_s=(beliefs[-1]['search_time_s'] if declared and beliefs else None),
        first_navigation_within_0_5m_time_s=min(proximity) if proximity else None,path_length_m=path_length,
        measurement_count=len(events),hit_count=sum(int(r['hit']) for r in events),navigation_failure_count=nav_failures,invalid_belief_rows=invalid_belief_rows,
        planning_request_count=planning_requests,planning_return_count=planning_returns,
        nonempty_planning_return_count=nonempty_planning_returns,issued_goal_count=issued_goals,
        callback_exception_count=log.count('Error executing callback')+log.count('AttributeError:'),
        wall_time_s=time.monotonic()-start_wall,raw_run_directory=str(run),software_smoke=a.software_smoke,
        fixed_source_blind_coverage=a.coverage)
    result['actual_native_support_count']=len(beliefs[0]['free_cells']) if beliefs else None
    result['common_legal_support_matches']=bool(beliefs and beliefs[0]['free_cells']==bank.cells.tolist())
    if not case['truth_in_support']:
        result.update(exact_cell_rank=None,exact_cell_metric_reason='truth outside Native615 support; no nearest-label substitution',extended_true_label_probability=0.,extended_true_label_nll='positive_infinity')
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
