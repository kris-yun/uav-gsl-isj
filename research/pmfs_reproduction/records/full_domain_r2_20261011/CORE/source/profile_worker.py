from pathlib import Path
import json,os,csv,time,subprocess,shutil,hashlib,bisect,signal
import numpy as np,yaml
import raw_decode as raw
T=Path(__file__).resolve().parent;P=json.loads((T/'PROFILE_PREREGISTRATION.json').read_text());D=Path('/mnt/hgfs/workspace/PMFS_FULL_DOMAIN_R2_DATA_20261011');ram=Path('/dev/shm/pmfs_r2')
def rows(p):return list(csv.DictReader(Path(p).open()))
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2))
def wc(p,rs):
 with Path(p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',ROS_DOMAIN_ID='229',LD_LIBRARY_PATH='/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_common/lib:/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:/opt/ros/humble/lib')
L=dict(status='RUNNING',records=[],new_gas_calls=0);dump(D/'PROFILE_LEDGER.json',L)
def run(cmd,log,e):
 start=time.monotonic();p=subprocess.Popen(cmd,env=e,stdout=Path(log).open('w'),stderr=subprocess.STDOUT,start_new_session=True);peak=0;last=0
 while p.poll() is None:
  rss=0
  for f in Path('/proc').glob('[0-9]*/status'):
   try:
    if os.getpgid(int(f.parent.name))==p.pid:rss+=next(int(x.split()[1])*1024 for x in f.read_text().splitlines() if x.startswith('VmRSS:'))
   except (OSError,StopIteration):pass
  peak=max(peak,rss)
  if rss>1610612736 or time.monotonic()-start>240 or time.time()-P['entry_unix']>1200:
   os.killpg(p.pid,signal.SIGINT);p.wait(timeout=10);raise RuntimeError('PROFILE_RESOURCE_OR_20MIN_CAP')
  if time.monotonic()-last>30:print(json.dumps({'stage':'PROFILE','seconds':time.monotonic()-start,'RSS':rss}),flush=True);last=time.monotonic()
  time.sleep(.1)
 assert p.returncode==0,(cmd,Path(log).read_text()[-1500:]);return dict(wall_s=time.monotonic()-start,peak_RSS=peak)
try:
 for bank in P['old_profile_banks']:
  src=Path(bank['bank']);dest=D/('PROFILE_'+bank['id']);dest.mkdir();times=rows(src/'PHYSICAL_FRAME_TIME.csv');tt=[float(r['physical_snapshot_time_s']) for r in times];qs=[];sel=set();copy_start=time.monotonic();stage=ram/bank['id'];stage.mkdir()
  for name,events in P['plans'].items():
   for b,e in enumerate(events):
    n=bisect.bisect_right(tt,float(e['physical_target_s']))-1;frame=int(times[n]['frame']);sel.add(frame)
    for ci in P['grid_indexes']:qs.append(dict(query_id=f'{name}_g{b}_{ci}',frame=frame,x=float(np.float32(-7.55))+(ci%34+.5)*.25,y=float(np.float32(-7.88))+(ci//34+.5)*.25,z=-.2))
    qs.append(dict(query_id=f'{name}_r{b}',frame=frame,x=e['x'],y=e['y'],z=e['z']))
  for frame in sel:shutil.copy2(src/'bank'/f'iteration_{frame}',stage/f'iteration_{frame}')
  shutil.copytree(src/'bank/wind',stage/'wind');wc(stage/'QUERIES.csv',qs);transfer=time.monotonic()-copy_start
  timing=run([P['query'],P['environment'],str(stage),str(stage/'QUERIES.csv'),str(stage/'QUERY_OUTPUT.csv')],dest/'query.log',env)
  shutil.copy2(stage/'QUERIES.csv',dest/'QUERIES.csv');shutil.copy2(stage/'QUERY_OUTPUT.csv',dest/'QUERY_OUTPUT.csv');q=rows(dest/'QUERY_OUTPUT.csv');assert len(q)==44800
  actual={r['query_id']:r for r in q};maximum=0.;start=time.monotonic()
  for name in P['plans']:
   old=Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/readout')/(name+'_'+bank['id'].split('_reference')[0]+'_0')/'QUERY_OUTPUT.csv'
   for r in rows(old):
    a=actual[name+'_'+r['query_id']]
    for k in ['ppm_float32','physical_free','wind_x','wind_y','wind_z']:maximum=max(maximum,abs(float(r[k])-float(a[k])))
  assert maximum==0
  record=dict(bank,transfer_ram_s=transfer,two_plan_query=timing,query_rows=len(q),used_frames=len(sel),numerical_max_abs=maximum,verification_s=time.monotonic()-start)
  L['records'].append(record);dump(D/'PROFILE_LEDGER.json',L)
 # One same-seed full bank in RAM: I/O-only numerical anchor, not new scientific realization.
 old=Path(P['old_profile_banks'][0]['bank']);target=ram/'RAM_IO_ANCHOR';target.mkdir();pars=yaml.safe_load((old/'PARAMETERS.yaml').read_text())['/**']['ros__parameters'];pars.update(results_location=str(target/'bank'),r6_time_trace_path=str(target/'PHYSICAL_FRAME_TIME.csv'))
 (target/'PARAMETERS.yaml').write_text(yaml.safe_dump({'/**':{'ros__parameters':pars}},sort_keys=False));reg=json.loads(Path('/mnt/hgfs/workspace/PMFS_RK2B_DATA_20261010/FROZEN_PHYSICS_SOURCE_REGISTRY.json').read_text()) if False else None
 oldq=json.loads((old/'QUALIFICATION.json').read_text());job=oldq.get('job',oldq)
 # Seeds are supplied by signed profile plan, never inferred from outcomes.
 e=env.copy();e.update(LD_LIBRARY_PATH=str(Path(P['world_library']).parent)+':'+env['LD_LIBRARY_PATH'],M2_GAUSSIAN_SEED=str(P['IO_anchor_seeds'][0]),M2_UNIFORM_SEED=str(P['IO_anchor_seeds'][1]),M2_RNG_TRACE=str(target/'RNG'))
 L['new_gas_calls']+=1;dump(D/'PROFILE_LEDGER.json',L)
 generation=run(['bash','-c','source /opt/ros/humble/setup.bash; exec "$@"','bash','/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator','--ros-args','--params-file',str(target/'PARAMETERS.yaml')],target/'generation.log',e)
 oldframes=rows(old/'ALL_FRAME_SHA256_AND_TIME.csv');assert len(oldframes)==1803
 for r in oldframes:assert sh(target/'bank'/('iteration_'+r['frame']))==r['SHA256']
 for p in old.glob('RNG.*'):assert sh(p)==sh(target/p.name)
 assert sh(old/'PHYSICAL_FRAME_TIME.csv')==sh(target/'PHYSICAL_FRAME_TIME.csv')
 dest=D/'PROFILE_RAM_IO_ANCHOR';dest.mkdir()
 for p in target.iterdir():
  if p.is_file():shutil.copy2(p,dest/p.name)
 L.update(status='PASS_OLD_BANK_PROFILES_AND_FULL_RAM_IO_ANCHOR',RAM_full_generation=generation,all1803_frame_SHA_equal=True,RNG_time_equal=True,physics_changed=False)
except Exception as ex:L.update(status='TECHNICAL_PROFILE_STOP',error=repr(ex))
finally:dump(D/'PROFILE_LEDGER.json',L);print(json.dumps({'status':L['status'],'records':len(L['records']),'error':L.get('error')}),flush=True)
