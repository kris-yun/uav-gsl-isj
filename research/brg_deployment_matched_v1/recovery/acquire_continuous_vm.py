"""Regenerate a frozen OPEN run, retaining every native filament frame."""
from pathlib import Path
import sys,os,json,hashlib,subprocess,shutil,time,re,csv
ROOT=Path(__file__).resolve().parent
LOCK_PATH=ROOT/'FROZEN_RUN_MANIFEST.json'
LOCK_SHA='891a01d580ebc8ddbfa20b4ec2e3e0462cbe54b49232d65c1a36d4982ff4b2fe'
BINARY=Path('/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator')
SCENARIOS=Path('/mnt/hgfs/workspace/GADEN_files/scenarios')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def load():
    if sha(LOCK_PATH)!=LOCK_SHA:raise RuntimeError('frozen manifest changed')
    lock=json.loads(LOCK_PATH.read_text())
    if len(lock['runs'])!=72 or lock['max_new_gaden_executions']!=72:raise RuntimeError('budget drift')
    if sha(BINARY)!=lock['binary_sha256']:raise RuntimeError('historical GADEN binary drift')
    return lock
def preflight(lock,run):
    occ=SCENARIOS/run['house']/'OccupancyGrid3D.csv'
    if sha(occ)!=run['occupancy_sha256']:raise RuntimeError('occupancy drift')
    wind=Path(run['wind_path'])
    if not wind.is_dir() or len(run['wind_iteration_hashes'])!=11:raise RuntimeError('wind path/size drift')
    for name,expected in run['wind_iteration_hashes'].items():
        if sha(wind/name)!=expected:raise RuntimeError(f'wind drift {name}')
    if float(run['xyz'][2])!=.2 or run['house'] not in ('House01','House02'):raise RuntimeError('source/house contract drift')
    free=shutil.disk_usage(lock['scratch_root']).free if Path(lock['scratch_root']).exists() else shutil.disk_usage('/home/zyc').free
    if free<250_000_000:raise RuntimeError('scratch free space <250MB before run')
    return occ,wind,free
def run_one(lock,n):
    run=lock['runs'][n-1]
    if run['ordinal']!=n or not re.fullmatch(r'[A-Za-z0-9_,.\-]+',run['run_id']):raise RuntimeError('run identity invalid')
    occ,wind,free=preflight(lock,run)
    root=Path(lock['scratch_root']);root.mkdir(exist_ok=True)
    out=root/run['run_id']
    if out.exists():raise RuntimeError('refuse to overwrite existing run; inspect before resume')
    out.mkdir();real=out/'realization';real.mkdir()
    (real/'OccupancyGrid3D.csv').symlink_to(occ)
    sx,sy,sz=run['xyz'];c=lock['simulation_parameters']
    opts={'verbose':'false','wait_preprocessing':'false','sim_time':c['sim_time'],'time_step':c['time_step'],'num_filaments_sec':c['num_filaments_sec'],'variable_rate':c['variable_rate'],'filament_stop_steps':c['filament_stop_steps'],'ppm_filament_center':c['ppm_filament_center'],'filament_initial_std':c['filament_initial_std'],'filament_growth_gamma':c['filament_growth_gamma'],'filament_noise_std':c['filament_noise_std'],'gas_type':c['gas_type'],'temperature':c['temperature'],'pressure':c['pressure'],'concentration_unit_choice':c['concentration_unit_choice'],'occupancy3D_data':str(occ),'fixed_frame':'map','wind_data':str(wind),'wind_time_step':c['wind_time_step'],'allow_looping':c['allow_looping'],'loop_from_step':c['loop_from_step'],'loop_to_step':c['loop_to_step'],'source_position_x':repr(sx),'source_position_y':repr(sy),'source_position_z':repr(sz),'save_results':c['save_results'],'results_time_step':c['results_time_step'],'results_min_time':c['results_min_time'],'writeConcentrations':c['writeConcentrations'],'results_location':str(real)}
    cmd=[str(BINARY),'--ros-args']+[v for k,value in opts.items() for v in ('-p',f'{k}:={value}')]
    env=dict(os.environ,GADEN_RNG_SEED=str(run['historical_seed']))
    t0=time.monotonic()
    with (out/'generation.log').open('w') as log:process=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    elapsed=time.monotonic()-t0
    files=sorted((p for p in real.iterdir() if re.fullmatch(r'iteration_\d+',p.name)),key=lambda p:int(p.name.split('_')[1]))
    ids=[int(p.name.split('_')[1]) for p in files]
    log_text=(out/'generation.log').read_text(errors='replace')
    if process.returncode!=0 or 'Filament simulator finished correctly!' not in log_text or not files or ids!=list(range(len(files))):raise RuntimeError(f'GADEN run incomplete: {out}; inspect without deleting')
    with (out/'RAW_SHA256.tsv').open('w',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['file','bytes','sha256'])
        for p in files:w.writerow([p.name,p.stat().st_size,sha(p)])
    generated_bytes=sum(p.stat().st_size for p in files)
    m={'ordinal':n,'run_id':run['run_id'],'house':run['house'],'wind':run['wind'],'source_id':run['source_id'],'source_xyz':run['xyz'],'historical_seed':run['historical_seed'],'historical_original_cube_sha256':run['original_cube_sha256'],'split':run['split'],'binary_sha256':lock['binary_sha256'],'occupancy_sha256':run['occupancy_sha256'],'wind_iteration_hashes':run['wind_iteration_hashes'],'simulation_parameters':c,'requested_duration_s':float(c['sim_time']),'writer_interval_config_s':float(c['results_time_step']),'raw_frames':len(files),'frame_id_first':ids[0],'frame_id_last':ids[-1],'frame_bytes':generated_bytes,'raw_inventory_sha256':sha(out/'RAW_SHA256.tsv'),'generation_log_sha256':sha(out/'generation.log'),'wall_seconds':elapsed,'scratch_free_before_bytes':free,'scratch_free_after_bytes':shutil.disk_usage(root).free,'actual_frame_time_map_status':'UNRESOLVED_UNTIL_PLAYER_WRITER_AUDIT','new_gaden_execution':True,'new_independent_plume':False}
    (out/'RUN_METADATA.json').write_text(json.dumps(m,indent=2)+'\n')
    print(json.dumps({'status':'RAW_NATIVE_FRAMES_PRESERVED','ordinal':n,'run_id':run['run_id'],'frames':len(files),'bytes':generated_bytes,'wall_seconds':elapsed,'scratch_free_after_bytes':m['scratch_free_after_bytes'],'run_dir':str(out)},indent=2),flush=True)
def main():
    lock=load()
    if len(sys.argv)==3 and sys.argv[1]=='preflight':
        n=int(sys.argv[2]);run=lock['runs'][n-1]
        occ,wind,free=preflight(lock,run)
        print(json.dumps({'status':'PREFLIGHT_PASS','ordinal':n,'run_id':run['run_id'],'occupancy':str(occ),'wind':str(wind),'scratch_free_bytes':free,'manifest_sha256':LOCK_SHA},indent=2))
    elif len(sys.argv)==3 and sys.argv[1]=='run-one':run_one(lock,int(sys.argv[2]))
    else:raise SystemExit('usage: acquire_continuous_vm.py {preflight|run-one} ordinal')
if __name__=='__main__':main()
