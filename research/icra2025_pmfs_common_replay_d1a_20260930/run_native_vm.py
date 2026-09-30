"""One existing-plume replay, isolated processes and immutable Native parameters."""
import argparse,csv,hashlib,json,os,resource,signal,subprocess,time
from pathlib import Path
ROOT=Path('/home/zyc/d1a_common_replay_20260930')
OVERLAY=Path('/home/zyc/brg_closedloop_20260927/vgr_execution_v2')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--mode',choices=['off','on'],required=True);a=ap.parse_args()
    with (ROOT/'D1A_RUNLIST_64.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
    row=next(x for x in rows if x['run_id']==a.run_id)
    leaf=ROOT/'input'/a.run_id
    assert sha(leaf/'RUN_MANIFEST.json')==row['run_manifest_sha256']
    assert sha(leaf/'OUTPUT_SHA256SUMS.tsv')==row['raw_inventory_sha256']
    with (leaf/'OUTPUT_SHA256SUMS.tsv').open() as f:
        for x in csv.DictReader(f,delimiter='\t'):
            assert sha(leaf/x['name'])==x['sha256'],x['name']
    manifest=json.loads((leaf/'RUN_MANIFEST.json').read_text());scenario=Path(manifest['simulation_parameters']['occupancy3D_data']).parent
    assert sha(scenario/'OccupancyGrid3D.csv')==row['occupancy_sha256']
    run=ROOT/'runs'/a.run_id/a.mode;run.mkdir(parents=True,exist_ok=False)
    view=ROOT/'views'/a.run_id/a.mode;view.mkdir(parents=True,exist_ok=False)
    for n in ['OccupancyGrid3D.csv','wind_simulations']:(view/n).symlink_to(scenario/n,target_is_directory=(scenario/n).is_dir())
    gas=view/'gas_simulations'/row['wind_id'];gas.mkdir(parents=True);(gas/'FilamentSimulation_frozen_ocb').symlink_to(leaf,target_is_directory=True)
    with (leaf/'RECORD_TIMELINE.tsv').open() as f:timeline=list(csv.DictReader(f,delimiter='\t'))
    with (run/'record_time_map.csv').open('w') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['physical_sim_time_s','save_record_id'])
        for t in timeline:w.writerow([t['internal_simulation_time_s'],t['record_index']])
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    env=dict(os.environ,ROS_DOMAIN_ID='226',RMW_IMPLEMENTATION='rmw_fastrtps_cpp',ROS_LOG_DIR=str(run/'ros_log'),
        PYTHONPATH=str(OVERLAY)+':'+os.environ.get('PYTHONPATH',''),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        BRG_BELIEF_AUDIT_JSONL=str(run/'beliefs.jsonl'),D1A_RUN_ID=a.run_id,
        D1A_EVENTS_RAW_JSONL=str(run/'events_raw.jsonl') if a.mode=='on' else '')
    for k,n in {'NATIVE_RECOVERY_WIND_QUERY_CSV':'wind_query.csv','NATIVE_RECOVERY_WIND_UPDATE_CSV':'wind_source_update.csv',
        'NATIVE_RECOVERY_MEASUREMENT_EVENTS_CSV':'measurement_events.csv','NATIVE_RECOVERY_MEASURED_MAP_CSV':'measured_map_at_update.csv',
        'NATIVE_RECOVERY_CANDIDATES_CSV':'frozen_candidate_geometry.csv','NATIVE_RECOVERY_UPDATE_COMPLETE_FILE':'source_update_complete.txt'}.items():env[k]=str(run/n)
    children=[];handles=[];commands=[]
    def start(cmd,log):
        handle=(run/log).open('w');handles.append(handle);commands.append(cmd)
        p=subprocess.Popen(cmd,stdout=handle,stderr=subprocess.STDOUT,env=env,start_new_session=True);children.append(p);return p
    def wait_service(name,typ):
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            q=subprocess.run(['ros2','service','type',name],env=env,capture_output=True,text=True,timeout=15)
            if q.returncode==0 and q.stdout.strip()==typ:return
            if any(p.poll() is not None for p in children):raise RuntimeError('child exited during readiness: '+name)
            time.sleep(.5)
        raise TimeoutError('service readiness '+name)
    status='D1A_INFRASTRUCTURE_HOLD';reason='not_started';wall=time.monotonic()
    try:
        start(['/dev/shm/house2_gaden_install/gaden_player/lib/gaden_player/player','--ros-args','-r','__node:=gaden_player',
            '-p','num_simulators:=1','-p','simulation_data_0:='+str(leaf),'-p','occupancyFile:='+str(scenario/'OccupancyGrid3D.csv'),
            '-p','initial_iteration:=0','-p','player_freq:=1.0','-p','manual_iteration_mode:=true'],'player.log')
        wait_service('/frame_query','gaden_msgs/srv/FrameQuery')
        start(['python3','/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/wind_value_server.py','--ros-args',
            '-p','vgr_data_path:='+str(view),'-p','config_id:='+row['wind_id']],'wind_server.log')
        wait_service('/wind_value','gaden_msgs/srv/WindPosition')
        args=dict(vgr_data_path=str(view),config_id=row['wind_id'],house=row['house'],run_id=a.run_id,run_dir=str(run),
            time_map=str(run/'record_time_map.csv'),source_x=row['source_x'],source_y=row['source_y'],source_z=row['source_z'],
            start_x=row['start_x'],start_y=row['start_y'])
        child=start(['ros2','launch',str(ROOT/'d1a_native.launch.py')]+[k+':='+v for k,v in args.items()],'launch.log')
        provenance=dict(run=row,mode=a.mode,argv=commands,domain=226,nav_seed=0,budget_s=300,
            native_binary_sha256=sha(ROOT/'logger_build/gsl_actionserver_node'),
            vgr_module_sha256=sha(OVERLAY/'vgr_bridge/vgr_sim_node.py'),
            wind_server_sha256=sha('/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/wind_value_server.py'),
            native_wind='unchanged full spatial state0 wind_value service; local measurement wind is current GADEN record',
            target_generator_executions=0,confirmation_read=False,house03_read=False,unet_evaluations=0,
            physical_time_rule='latest saved simulator time <= clock; no record ID interpreted as seconds')
        (run/'provenance.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            p=run/'beliefs.jsonl'
            if p.exists() and p.stat().st_size:
                initial=json.loads(p.read_text().splitlines()[0]);assert initial['time_s']==0 and initial['search_time_s']==0;break
            if child.poll() is not None:raise RuntimeError('launch exited before paused Native initialization')
            if 'Traceback (most recent call last)' in (run/'launch.log').read_text(errors='replace'):
                raise RuntimeError('pre-clock adapter initialization error')
            time.sleep(.2)
        else:raise TimeoutError('Native paused initialization')
        capture=subprocess.run(['python3',str(ROOT/'capture_map_vm.py'),str(run/'map_receipt.json')],env=env,capture_output=True,text=True,timeout=70)
        (run/'map_capture.log').write_text(capture.stdout+capture.stderr)
        if capture.returncode:raise RuntimeError('map receipt failed before clock start')
        wait_service('/start_simulation','std_srvs/srv/Trigger')
        q=subprocess.run(['ros2','service','call','/start_simulation','std_srvs/srv/Trigger','{}'],env=env,capture_output=True,text=True,timeout=30)
        (run/'clock_start.log').write_text(q.stdout+q.stderr)
        if q.returncode or 'success=True' not in q.stdout:raise RuntimeError('clock start failed')
        deadline=time.monotonic()+2400
        while time.monotonic()<deadline:
            if (run/'run_status.json').exists():
                result=json.loads((run/'run_status.json').read_text());reason=result['status'];status='NATIVE_REPLAY_RETURNED';break
            log=(run/'launch.log').read_text(errors='replace')
            if any(s in log for s in ['Traceback (most recent call last)', 'terminate called', 'D1A_READONLY_LOG_WRITE_FAILED', 'Error executing callback']):
                raise RuntimeError('runtime exception; see launch.log')
            if child.poll() is not None:raise RuntimeError('launch exited without Native result')
            time.sleep(.5)
        else:raise TimeoutError('outer wall deadline')
    except Exception as exc:reason=type(exc).__name__+': '+str(exc)
    finally:
        for p in reversed(children):
            if p.poll() is None:
                try:os.killpg(p.pid,signal.SIGINT)
                except ProcessLookupError:pass
        for p in children:
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait()
        for handle in handles:handle.close()
    result=dict(status=status,reason=reason,wall_time_s=time.monotonic()-wall,run_id=a.run_id,logger_mode=a.mode)
    (run/'execution_status.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    if status!='NATIVE_REPLAY_RETURNED':raise SystemExit(2)
if __name__=='__main__':main()
