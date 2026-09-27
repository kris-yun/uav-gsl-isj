#!/usr/bin/env python3
"""Adapter around the existing ROS Native launch/player/benchmark, no new plume.

One process group per subprocess; truth stays in benchmark/evaluator only.
Every algorithm/service failure produces a case result instead of fallback.
"""
import argparse,csv,hashlib,json,math,os,resource,signal,socket,subprocess,sys,time
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
    ap=argparse.ArgumentParser();ap.add_argument('--arm',required=True,choices=['native_pmfs','candidate_gru','brg','brg_ungated']);ap.add_argument('--case-file',required=True);ap.add_argument('--budget-s',type=float,required=True);ap.add_argument('--output',required=True);ap.add_argument('--domain',type=int,default=228);ap.add_argument('--software-smoke',action='store_true');a=ap.parse_args()
    case=json.loads(Path(a.case_file).read_text());out=Path(a.output);run=out.parent/(out.stem+'_raw')
    assert not out.exists() and not run.exists();run.mkdir(parents=True)
    assert 0<=a.domain<=232
    if not a.software_smoke:
        assert a.budget_s==300 and (ROOT/'CHECKPOINT_FREEZE.json').exists()
        frozen=json.loads((ROOT/'CHECKPOINT_FREEZE.json').read_text())
        for name,h in frozen['weights_sha256'].items():assert sha(ROOT/f'trained_full/{name}/best.pt')==h
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    env=dict(os.environ,ROS_DOMAIN_ID=str(a.domain),RMW_IMPLEMENTATION='rmw_fastrtps_cpp',ROS_LOG_DIR=str(run/'ros_log'),
        PYTHONPATH='/home/zyc/brg_closedloop_20260927/vgr_execution_v2:'+os.environ.get('PYTHONPATH',''),
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',BRG_BELIEF_AUDIT_JSONL=str(run/'beliefs.jsonl'))
    for var,name in {'NATIVE_RECOVERY_WIND_QUERY_CSV':'wind_query.csv','NATIVE_RECOVERY_WIND_UPDATE_CSV':'wind_source_update.csv',
        'NATIVE_RECOVERY_MEASUREMENT_EVENTS_CSV':'measurement_events.csv','NATIVE_RECOVERY_MEASURED_MAP_CSV':'measured_map_at_update.csv',
        'NATIVE_RECOVERY_CANDIDATES_CSV':'frozen_candidate_geometry.csv','NATIVE_RECOVERY_UPDATE_COMPLETE_FILE':'source_update_complete.txt'}.items():env[var]=str(run/name)
    view=run/'asset_view';view.mkdir();scenario=Path(case['scenario_root']);wind=case['wind']
    for n in ['OccupancyGrid3D.csv','wind_simulations']:(view/n).symlink_to(scenario/n,target_is_directory=(scenario/n).is_dir())
    gas=view/'gas_simulations'/wind;gas.mkdir(parents=True)
    (gas/'FilamentSimulation_existing_open_case').symlink_to(Path(case['realization']),target_is_directory=True)
    bank=TemplateBank.load(ROOT/'example_banks/h03_model_only.npz');assert len(bank.ids)==624
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
            variant={'candidate_gru':'gru','brg':'brg','brg_ungated':'ungated'}[a.arm]
            checkpoint=ROOT/('trained' if a.software_smoke else 'trained_full')/variant/'best.pt'
            side=start(['python3',str(ROOT/'tools/serve.py'),'--checkpoint',str(checkpoint),'--bank',str(ROOT/'example_banks/h03_model_only.npz'),
                '--allow-warmstart','--tcp-port',str(port),'--threads','1','--log',str(run/'sidecar_events.jsonl')],'sidecar.log',
                dict(env,PYTHONPATH='/home/zyc/.local/lib/python3.10/site-packages:'+env['PYTHONPATH']))
            for _ in range(100):
                if side.poll() is not None:raise RuntimeError('sidecar initialization failed')
                try:
                    with socket.create_connection(('127.0.0.1',port),.5) as s:
                        s.sendall(b'HELLO\n');assert s.recv(4096).decode().split()[1]==bank.fingerprint
                    break
                except (OSError,AssertionError):time.sleep(.2)
            else:raise TimeoutError('sidecar readiness')
        launch=ROOT/'integration/brg_existing_native.launch.py'
        args={'vgr_data_path':str(view),'config_id':wind,'house':'House03','environment_id':'VGR_House03','scenario_id':case['case_id'],
            'source_x':str(case['truth_xy'][0]),'source_y':str(case['truth_xy'][1]),'source_z':'.2','start_x':'2.0','start_y':'0.0','flight_height':'.2',
            'seed':'0','run_id':out.stem,'run_dir':str(run),'timeout_sec':str(a.budget_s),'realtime_factor':'1.0','sim_stop_at_s':str(a.budget_s),
            'gas_backend':'gaden_player','raw_query_executable':'/bin/true','shadow_gmrf':'false','convergence_thr':'0.5',
            'recorded_snapshot_time_map':case['time_map'],'repo_root':'/home/zyc/native_pmfs_recovery_v1/checkout',
            'brg_enabled':str(a.arm!='native_pmfs').lower(),'brg_port':str(port),'brg_candidates':'624','brg_bank_sha256':bank.fingerprint,
            'brg_run_id':out.stem,'brg_sensor_offset_z_m':'0.0','pmfs_belief_file':str(run/'beliefs.jsonl')}
        child=start(['ros2','launch',str(launch)]+[k+':='+v for k,v in args.items()],'launch.log')
        (run/'runtime_binding.json').write_text(json.dumps({'argv':commands,'effective_launch_args':args,'bank_id':bank.fingerprint,
            'bank_file_sha256':sha(ROOT/'example_banks/h03_model_only.npz'),'software_smoke':a.software_smoke,
            'source_truth_in_sidecar_inputs':False,'candidate_support_count':624,'replay':'causal actual-writer-time snapshot hold; no cyclic or seed offset'},indent=2)+'\n')
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
        if not a.software_smoke:assert support_matches,'native/full624 support mismatch'
    log=(run/'launch.log').read_text(errors='replace') if (run/'launch.log').exists() else ''
    nav_failures=log.count("Couldn't reach the target")+log.count('Waypoint execution geometry violation')
    timed_out=status=='time_budget'
    if nav_failures and status in ('completed','time_budget'):status='navigation_failure';reason='navigation_failure_recorded'
    if invalid_belief_rows:status='algorithm_error';reason='invalid_or_nonfinite_belief_record'
    poses=csvrows(run/'sim_pose_trace.csv');poses=[r for r in poses if float(r['t_sim_s'])<=a.budget_s]
    xy=np.array([[float(r['x']),float(r['y'])] for r in poses]);truth=np.array(case['truth_xy'])
    path_length=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()) if len(xy)>1 else 0.
    proximity=[float(r['t_sim_s']) for r,x in zip(poses,xy) if np.linalg.norm(x-truth)<=.5]
    events=csvrows(run/'measurement_events.csv');error=float(np.linalg.norm(np.array(estimate)-truth)) if estimate is not None else None
    geometric=int(status in ('completed','time_budget') and error is not None and error<=.5)
    result={k:case[k] for k in ['case_id','source_id','plume_id','initial_pose_id','observation_contract_id','candidate_support_id','truth_xy']}
    result.update(arm=a.arm,budget_s=a.budget_s,status=status,failure_reason=reason,estimate_xy=estimate,
        geometric_success=geometric,final_source_error_m=error,algorithm_declared_success=int(declared),timeout=int(timed_out),
        wrong_declaration=int(declared and (error is None or error>.5)),declaration_time_s=(beliefs[-1]['search_time_s'] if declared and beliefs else None),
        first_navigation_within_0_5m_time_s=min(proximity) if proximity else None,path_length_m=path_length,
        measurement_count=len(events),hit_count=sum(int(r['hit']) for r in events),navigation_failure_count=nav_failures,invalid_belief_rows=invalid_belief_rows,
        wall_time_s=time.monotonic()-start_wall,raw_run_directory=str(run),software_smoke=a.software_smoke)
    result['actual_native_support_count']=len(beliefs[0]['free_cells']) if beliefs else None
    result['full624_support_matches']=bool(beliefs and beliefs[0]['free_cells']==bank.cells.tolist())
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
