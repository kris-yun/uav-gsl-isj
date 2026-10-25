"""Bounded native concentration queries of existing E3/E4 archives only.

Run in original Ubuntu. No ROS, no RunningSimulation, no source relocation.
Uses the pre-readout fixed design; saves every success/failure and selected
physical file identities for independent recomputation.
"""
from pathlib import Path
import bisect,csv,hashlib,json,os,shutil,subprocess,time,resource
ROOT=Path('/mnt/hgfs/workspace/METHOD_COMPARISON_O24_1M2_20261024')
OUT=ROOT/'outputs/E3_INFORMATION_SOURCE_20261025'
REPLAY=ROOT/'V12_REVIEW_20261024/pro_handoff/physical_replay_bundle'
ENGINE=REPLAY/'headless_build/headless_saved_query'
MAP=REPLAY/'actual_runtime/OccupancyGrid3D.csv'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csvrows(p):
    with Path(p).open() as f:return list(csv.DictReader(f))
def put(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def table(p,rr):
    with Path(p).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rr[0]);w.writeheader();w.writerows(rr)
def run_query(src,dst,world):
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    a=resource.getrusage(resource.RUSAGE_CHILDREN);started=time.monotonic()
    with src.open() as fi,dst.open('w') as fo,(dst.with_suffix('.stderr')).open('w') as err:
        p=subprocess.run([str(ENGINE),str(MAP),str(world)],stdin=fi,stdout=fo,stderr=err,env=env,timeout=90)
    b=resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt=dict(command=[str(ENGINE),str(MAP),str(world)],returncode=p.returncode,wall_s=time.monotonic()-started,child_CPU_s=b.ru_utime+b.ru_stime-a.ru_utime-a.ru_stime,input_sha256=sha(src),output_sha256=sha(dst))
    put(dst.with_suffix('.receipt.json'),receipt);assert p.returncode==0,receipt
    assert all(int(r['mode'])==1 for r in csvrows(dst)), 'Expected native filament concentration branch'
    return receipt
def main():
    assert not (OUT/'NATIVE_READOUT_RECEIPT.json').exists()
    started=time.monotonic();costs=[];identities=[];native=OUT/'native_query';native.mkdir(exist_ok=True)
    worlds={
        'E3':(Path('/home/zyc/pmfs_e3_native_validation_20261009/one_realization_E3'),OUT/'inputs/E3_R01/PHYSICAL_FRAME_TIME.csv'),
        'E4':(Path('/mnt/hgfs/workspace/NATIVE_PMFS_FULL20_20261014/cases/E4/one_realization'),Path('/mnt/hgfs/workspace/NATIVE_PMFS_FULL20_20261014/cases/E4/PHYSICAL_FRAME_TIME.csv'))}
    assert sha(MAP)=='24cc18fb1b428bd12d53de22e6434560f9fa34d28798d0f19b372ba9f2c8e403'
    for case,(world,timeline) in worlds.items():
        wind=list((world/'wind').iterdir());assert len(wind)==1 and sha(wind[0])=='135690ce4679f43bb02d7d40fe39b338a250f2aa94cf3e71d0f2dbf8bbe4705a'
    # First recheck the existing historical native raw-response regression.
    hist=REPLAY/'historical_readout_qualification';reg=native/'historical_regression.csv'
    costs.append(run_query(hist/'headless_input.csv',reg,worlds['E3'][0]))
    expected=csvrows(hist/'RECORDED_GAS_QUERIES.csv');got=csvrows(reg);assert len(expected)==len(got)==290
    diffs=[abs(float(a['logged_raw_gas_ppm'])-float(b['raw_gas_ppm'])) for a,b in zip(expected,got)]
    assert max(diffs)==0
    schedule=csvrows(OUT/'FIXED_QUERY_SCHEDULE.csv');assert len(schedule)<=360
    for case,(world,timeline) in worlds.items():
        trace=csvrows(timeline);times=[float(t['physical_snapshot_time_s']) for t in trace];requests=[];bindings=[]
        for r in schedule:
            t=float(r['physical_s']);idx=bisect.bisect_right(times,t)-1
            assert 0<=idx<len(times)-1 and t<times[-1]
            frame=int(trace[idx]['frame']);requests.append(dict(query_id=r['query_id'],frame=frame,x=r['x'],y=r['y'],z=r['z']))
            bindings.append(dict(**r,frame=frame,snapshot_physical_s=times[idx],staleness_s=t-times[idx],case=case))
        folder=native/case;folder.mkdir(exist_ok=True);table(folder/'QUERY_INPUT.csv',requests);table(folder/'QUERY_BINDING.csv',bindings)
        costs.append(run_query(folder/'QUERY_INPUT.csv',folder/'QUERY_OUTPUT.csv',world))
        frames=sorted({x['frame'] for x in requests}|({int(r['frame']) for r in expected} if case=='E3' else set()))
        copied=folder/'saved_world';copied.mkdir(exist_ok=True);(copied/'wind').mkdir(exist_ok=True)
        shutil.copy2(next((world/'wind').iterdir()),copied/'wind/wind_iteration_0');shutil.copy2(timeline,folder/'PHYSICAL_FRAME_TIME.csv')
        for frame in frames:
            src=world/f'iteration_{frame}';dst=copied/src.name;shutil.copy2(src,dst);assert sha(src)==sha(dst)
            identities.append(dict(case=case,path=str(src),packaged_path=dst.relative_to(OUT).as_posix(),sha256=sha(src),bytes=src.stat().st_size))
    shutil.copy2(MAP,native/'OccupancyGrid3D.csv');shutil.copy2(ENGINE,native/'headless_saved_query');shutil.copy2(REPLAY/'actual_runtime/libbsc.so',native/'libbsc.so')
    put(OUT/'QUERIED_FRAME_IDENTITIES.json',identities)
    put(OUT/'NATIVE_READOUT_RECEIPT.json',dict(status='PASS_EXISTING_NATIVE_READOUT',engine_sha256=sha(ENGINE),map_sha256=sha(MAP),historical_regression_queries=290,historical_regression_max_abs_error_ppm=max(diffs),new_query_points=len(schedule)*2,per_world_query_points=len(schedule),saved_physical_frames=len(identities),costs=costs,total_wall_s=time.monotonic()-started,new_gas_worlds=0,physical_propagation_calls=0,ROS_runs=0,neural_training=0))
    print('RESULT_RECEIVED',json.dumps(dict(new_queries=len(schedule)*2,frames=len(identities),historical_error=max(diffs))),flush=True)
if __name__=='__main__':main()
