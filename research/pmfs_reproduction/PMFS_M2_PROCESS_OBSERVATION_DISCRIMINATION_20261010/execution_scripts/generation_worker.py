"""Run only the frozen first pair or remaining six, bounded, serial, without navigation."""
from pathlib import Path
import csv,hashlib,json,os,shutil,signal,struct,subprocess,sys,time,zlib
import yaml,numpy as np
t=Path(__file__).resolve().parent;phase=sys.argv[1]
assert phase in ['smoke','remaining']
contract=json.loads((t/'frozen_contract.json').read_text());assert len(contract['jobs'])==8
marker=t/(phase+'_GENERATION_STARTED.json');assert not marker.exists()
if phase=='remaining':assert json.loads((t/'SMOKE_QUALIFICATION.json').read_text())['verdict']=='PASS_BOTH_NATIVE_PHYSICAL_AND_QUERY_SMOKE'
old=Path('/home/zyc/pmfs_b4_native_validation_20261009');core=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws')
exe=core/'install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator'
expected_library=json.loads((t/'RNG_LIBRARY_BUILD_RESULT.json').read_text())['library_SHA256']
assert hashlib.sha256((t/'libgaden.so').read_bytes()).hexdigest()==expected_library
base=yaml.safe_load((old/'B4_generation_RESOLVED.yaml').read_text())['/**']['ros__parameters']
jobs=contract['jobs'][:2] if phase=='smoke' else contract['jobs'][2:]
marker.write_text(json.dumps(dict(phase=phase,job_ids=[j['candidate_id']+'_'+str(j['realization']) for j in jobs],started_wall=time.time())))
prior_wall=sum(json.loads(p.read_text())['generation_wall_s'] for p in (t/'realizations').glob('*/GENERATION_QUALIFICATION.json')) if (t/'realizations').exists() else 0.
ledger=dict(phase=phase,status='RUNNING',records=[],prior_generation_wall_s=prior_wall,new_GADEN_realizations=0)
def save():(t/(phase+'_GENERATION_LEDGER.json')).write_text(json.dumps(ledger,indent=2))
def dirsize():return sum(p.stat().st_size for p in t.rglob('*') if p.is_file())
try:
 for job in jobs:
  root=t/'realizations'/(job['candidate_id']+'_'+str(job['realization']));assert not root.exists();root.mkdir(parents=True)
  parameters=base.copy();parameters.update(source_position_x=job['source_xyz'][0],source_position_y=job['source_xyz'][1],source_position_z=job['source_xyz'][2],
                                          results_location=str(root/'bank'),r6_time_trace_path=str(root/'PHYSICAL_FRAME_TIME.csv'))
  (root/'PARAMETERS.yaml').write_text(yaml.safe_dump({'/**':{'ros__parameters':parameters}},sort_keys=False))
  env=os.environ.copy();env.update(M2_GAUSSIAN_SEED=str(job['seeds'][0]),M2_UNIFORM_SEED=str(job['seeds'][1]),
                                  M2_RNG_TRACE=str(root/'RNG'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',ROS_DOMAIN_ID='88')
  env.pop('GADEN_RNG_SEED',None)
  env['LD_LIBRARY_PATH']=str(t)+':'+str(core/'install/gaden_common/lib')+':'+str(core/'build/gaden_common/third_party/gaden_core/third_party/libbsc')+':/opt/ros/humble/lib'
  # Generator node itself is allowed; no GSL, player, sensor or navigation node is launched.
  command=['bash','-c','source /opt/ros/humble/setup.bash; exec "$@"','bash',str(exe),'--ros-args','--params-file',str(root/'PARAMETERS.yaml')]
  (root/'EXECUTION_INPUT.json').write_text(json.dumps(dict(candidate_id=job['candidate_id'],realization=job['realization'],seed_streams=job['seeds'],
       loaded_library_sha256=expected_library,command=command,ROS_DOMAIN_ID=88),indent=2))
  start=time.monotonic();peak=0;disk_peak=dirsize();reason=None
  ledger['new_GADEN_realizations']+=1;save()
  with (root/'generation.log').open('w') as log:
   p=subprocess.Popen(command,env=env,stdout=log,stderr=log,start_new_session=True)
   while p.poll() is None:
    rss=0
    for entry in Path('/proc').iterdir():
     if not entry.name.isdigit():continue
     try:
      if os.getpgid(int(entry.name))!=p.pid:continue
      for line in (entry/'status').read_text().splitlines():
       if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
     except (ProcessLookupError,PermissionError,FileNotFoundError):pass
    peak=max(peak,rss);size=dirsize();disk_peak=max(disk_peak,size)
    elapsed=time.monotonic()-start
    total=prior_wall+sum(r['generation_wall_s'] for r in ledger['records'])+elapsed
    if rss>1073741824:reason='RSS_OVER_1GIB'
    if total>900:reason='TOTAL_GENERATION_WALL_OVER_900S'
    if size>2147483648:reason='TASK_DISK_OVER_2GIB'
    if shutil.disk_usage(t).free<1073741824:reason='VM_FREE_DISK_BELOW_1GIB'
    if reason:
     for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGKILL]:
      try:os.killpg(p.pid,sig);p.wait(timeout=3);break
      except subprocess.TimeoutExpired:continue
      except ProcessLookupError:break
     break
    time.sleep(.15)
   exit_code=p.wait()
  elapsed=time.monotonic()-start;assert exit_code==0 and reason is None,(exit_code,reason,(root/'generation.log').read_text()[-3000:])
  times=list(csv.DictReader((root/'PHYSICAL_FRAME_TIME.csv').open()))
  frames=sorted((root/'bank').glob('iteration_*'),key=lambda p:int(p.name.split('_')[1]));assert len(times)==len(frames)==1803
  records=[];max_active=0
  for index,(file,row) in enumerate(zip(frames,times)):
   blob=file.read_bytes();assert blob.startswith(b'GADEN_RESULT\0') and blob[13]==1
   data=zlib.decompress(blob[22:]);assert len(data)==struct.unpack_from('<Q',blob,14)[0]
   assert struct.unpack_from('<II',data)==(3,0)
   off=56+struct.unpack_from('<Q',data,48)[0];source=struct.unpack_from('<3f',data,off)
   assert np.allclose(source,job['source_xyz'],rtol=0,atol=1e-6)
   wind_index=struct.unpack_from('<i',data,off+24)[0];assert wind_index==int(row['wind_index_at_save'])
   length=struct.unpack_from('<Q',data,off+28)[0];assert data[off+36:off+36+length]==b'filaments'
   ptr=off+36+length;num=struct.unpack_from('<Q',data,ptr)[0];ptr+=8
   assert len(data)-ptr==num*16 and num==int(row['filaments_after_step'])
   values=np.frombuffer(data,dtype='<f4',offset=ptr).reshape(num,4);assert np.isfinite(values).all() and (values[:,3]>0).all()
   max_active=max(max_active,num)
   records.append(dict(frame=index,physical_snapshot_time_s=float(row['physical_snapshot_time_s']),post_step_time_s=float(row['post_step_time_s']),
                       wind_index=wind_index,filaments=num,bytes=len(blob),SHA256=hashlib.sha256(blob).hexdigest()))
  assert records[0]['physical_snapshot_time_s']==0 and records[-1]['physical_snapshot_time_s']>999
  assert np.all(np.diff([r['physical_snapshot_time_s'] for r in records])>0)
  for wind in (root/'bank/wind').glob('wind_iteration_*'):
   assert wind.read_bytes()==(old/'derived_B4/wind'/wind.name).read_bytes()
  rng_files=list(root.glob('RNG.*'));assert len(rng_files)==6 and all(p.stat().st_size>0 for p in rng_files)
  for stream,seed in enumerate(job['seeds']):
   first=(root/('RNG.stream'+str(stream)+'.initial.txt')).read_text().split()[0]
   assert int(first)==seed,(stream,seed,first)
  with (root/'ALL_FRAME_SHA256_AND_TIME.csv').open('w',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
  result=dict(verdict='PASS_INDEPENDENT_SOURCE_CONDITIONED_SIMULATION_CONTRACT',candidate_id=job['candidate_id'],realization=job['realization'],role=job['role'],
              source_xyz=job['source_xyz'],seeds=job['seeds'],generation_wall_s=elapsed,peak_RSS_bytes=peak,task_peak_disk_bytes=disk_peak,
              bank_bytes=sum(p.stat().st_size for p in (root/'bank').rglob('*') if p.is_file()),frames=len(frames),max_active_filaments=max_active,
              first_physical_time=records[0]['physical_snapshot_time_s'],last_physical_time=records[-1]['physical_snapshot_time_s'],
              wind_indices_at_or_after_267s=sorted({r['wind_index'] for r in records if r['physical_snapshot_time_s']>=267}),
              exit_code=exit_code,resource_stop=reason,random_state_artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in rng_files})
  (root/'GENERATION_QUALIFICATION.json').write_text(json.dumps(result,indent=2));ledger['records'].append(result);save()
 ledger['status']='PASS_ALL_FROZEN_PHASE_GENERATIONS'
except Exception as error:
 ledger['status']='STOP_GENERATION_OR_QUALIFICATION_FAULT_NO_EXTRA_REALIZATION';ledger['error']=repr(error)
finally:save()
print(json.dumps(ledger,indent=2))
