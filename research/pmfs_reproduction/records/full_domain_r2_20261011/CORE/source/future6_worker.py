"""Serial new references, actual native processes, immutable physical parameters.
Full1000s generated in own RAM; allframe time/hash index and all used frames kept.
"""
from pathlib import Path
import json,time,os,csv,bisect,hashlib,subprocess,shutil,signal,math,gc
import numpy as np,yaml
import raw_decode as raw
T=Path(__file__).resolve().parent;P=json.loads((T/'REFERENCE_EXECUTION_CONTRACT.json').read_text());C=json.loads((T/'COMMON_TASK_CONTRACT.json').read_text());J=json.loads((T/'FUTURE_OBSERVATION_JOBS.json').read_text());D=Path(P['data']);RAM=Path('/dev/shm/pmfs_r2');ENV=RAM/'environment'
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',ROS_DOMAIN_ID='229',LD_LIBRARY_PATH='/home/zyc/pmfs_m2_process_observation_20261010:/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_common/lib:/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:/opt/ros/humble/lib')
env_native=env.copy();env_native['LD_LIBRARY_PATH']=json.loads(Path('/home/zyc/ros2_ws/pmfs_native_mechanism_closure_r1_20261011/ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH']
BINARY=RAM/'native_build/native_batch_entry';QUERY=Path('/home/zyc/pmfs_m2_process_observation_20261010/query_native');GEN=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator')
BASE=yaml.safe_load(Path('/mnt/hgfs/workspace/PMFS_RK2B_DATA_20261010/realizations/B000_reference0/PARAMETERS.yaml').read_text())['/**']['ros__parameters']
GRID=list(csv.DictReader((T/'inputs/R0/input.csv').open()));FREE=np.array([r['occupancy']=='1' for r in GRID]);IDX=np.flatnonzero(FREE);OCC=raw.occupancy(ENV/'OccupancyGrid3D.csv')
L=dict(status='RUNNING',records=[],gas_calls=65,reference_calls=0,observation_calls=0,technical_retries=0,started_unix=time.time(),new_CFD=0,new_nav=0);lastbeat=lastcheck=0
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open()))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2))
def wc(p,r):
 with Path(p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(r[0]),lineterminator='\n');w.writeheader();w.writerows(r)
def save():dump(D/'FUTURE_OBSERVATION_LEDGER.json',L)
def resource(task,rss=0):
 global lastcheck,lastbeat
 now=time.monotonic()
 if now-lastbeat>=30:print(json.dumps(dict(task=task,done=len(L['records']),total=len(J),gas_calls=L['gas_calls'],RSS=rss,elapsed_s=time.time()-P['entry_unix'])),flush=True);lastbeat=now
 if now-lastcheck>=60:
  lastcheck=now;size=sum(p.stat().st_size for p in D.rglob('*') if p.is_file());rootfree=shutil.disk_usage(T).free
  with (D/'RESOURCE_CHECKS.jsonl').open('a') as f:f.write(json.dumps(dict(task=task,RSS=rss,bytes=size,root_free=rootfree,RAM_free=shutil.disk_usage(RAM).free,elapsed=time.time()-P['entry_unix']))+'\n')
  assert rootfree>=4294967296 and shutil.disk_usage(D).free>=4294967296,'FREE4GIB_CAP';assert size<=8589934592,'NEW8GIB_CAP'
 assert time.time()-P['entry_unix']<14400,'TOTAL4H_CAP'
 assert time.time()-L['started_unix']<9000,'PHYSICS_AND_QUERY150MIN_CAP'
 assert rss<1610612736,'RSS1.5GIB_CAP'
def stop(p):
 for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGKILL]:
  try:os.killpg(p.pid,sig);p.wait(timeout=3);return
  except subprocess.TimeoutExpired:pass
  except ProcessLookupError:return
def run(cmd,log,e,task):
 st=time.monotonic();peak=0;reason=None
 with Path(log).open('w') as f:
  p=subprocess.Popen(cmd,env=e,stdout=f,stderr=f,start_new_session=True)
  try:
   while p.poll() is None:
    rss=0
    for q in Path('/proc').glob('[0-9]*/status'):
     try:
      if os.getpgid(int(q.parent.name))==p.pid:rss+=next(int(r.split()[1])*1024 for r in q.read_text().splitlines() if r.startswith('VmRSS:'))
     except (OSError,StopIteration):pass
    peak=max(peak,rss);resource(task,rss);assert time.monotonic()-st<240,'OPERATOR240S_CAP';time.sleep(.1)
  except Exception:stop(p);raise
  code=p.wait()
 assert code==0,(task,Path(log).read_text()[-2000:]);return dict(wall_s=time.monotonic()-st,sampled_peak_RSS=peak,exitcode=code)
def remove_owned_stage(stage):
 absolute=stage.resolve();root=RAM.resolve();assert root in absolute.parents and absolute.name.startswith('REF_')
 shutil.rmtree(absolute)
save()
try:
 for job in J:
  dest=D/'observations'/job['id'];dest.mkdir(parents=True);stage=RAM/('REF_'+job['id']);assert not stage.exists();stage.mkdir();start=time.monotonic()
  params=dict(BASE);params.update(occupancy3D_data=str(ENV/'OccupancyGrid3D.csv'),wind_data=str(ENV/'wind'),source_position_x=job['source_xyz'][0],source_position_y=job['source_xyz'][1],source_position_z=job['source_xyz'][2],results_location=str(stage/'bank'),r6_time_trace_path=str(stage/'PHYSICAL_FRAME_TIME.csv'))
  (stage/'PARAMETERS.yaml').write_text(yaml.safe_dump({'/**':{'ros__parameters':params}},sort_keys=False));e=env.copy();e.update(M2_GAUSSIAN_SEED=str(job['seeds'][0]),M2_UNIFORM_SEED=str(job['seeds'][1]),M2_RNG_TRACE=str(stage/'RNG'))
  L['gas_calls']+=1;L['observation_calls']+=1;assert L['gas_calls']<=140;save()
  generation=run(['bash','-c','source /opt/ros/humble/setup.bash; exec "$@"','bash',str(GEN),'--ros-args','--params-file',str(stage/'PARAMETERS.yaml')],stage/'generation.log',e,job['id']+'_generation')
  index_start=time.monotonic();times=rows(stage/'PHYSICAL_FRAME_TIME.csv');tt=[float(r['physical_snapshot_time_s']) for r in times];assert len(times)==1803 and np.diff(tt).min()>0
  manifest=[]
  for r in times:
   fp=stage/'bank'/('iteration_'+r['frame']);a=raw.snapshot(fp);assert np.array_equal(a['source'],np.asarray(job['source_xyz'],np.float32)) and a['gas_type']==13 and a['wind_index']==int(r['wind_index_at_save'])
   assert np.array_equal(a['dimensions'],OCC['dimensions']) and a['cell_size']==OCC['cell_size'];assert raw.cell_state(a['source'],a,OCC)==0
   manifest.append(dict(frame=int(r['frame']),physical_snapshot_time_s=float(r['physical_snapshot_time_s']),post_step_time_s=r['post_step_time_s'],wind_index=a['wind_index'],filaments=len(a['filaments']),SHA256=sh(fp),bytes=fp.stat().st_size))
  wc(dest/'ALL_FRAME_SHA256_AND_TIME.csv',manifest);index_wall=time.monotonic()-index_start;qs=[];selected=[];used=set()
  for plan,events in C['receiver_plans'].items():
   fs=[]
   for b,event in enumerate(events):
    n=bisect.bisect_right(tt,float(event['physical_target_s']))-1;assert n>=0 and n+1<len(tt);frame=int(times[n]['frame']);assert int(times[n]['wind_index_at_save'])==10;fs.append(frame);used.add(frame)
    for ci in IDX:qs.append(dict(query_id=f'{plan}_g{b}_{ci}',frame=frame,x=float(np.float32(-7.55))+(int(ci)%34+.5)*.25,y=float(np.float32(-7.88))+(int(ci)//34+.5)*.25,z=-.2))
    qs.append(dict(query_id=f'{plan}_r{b}',frame=frame,x=event['x'],y=event['y'],z=event['z']))
    if plan=='PUBLIC_B':
     for k,xyz in enumerate(C['auxiliary_receivers']):qs.append(dict(query_id=f'{plan}_a{b}_{k}',frame=frame,x=xyz[0],y=xyz[1],z=xyz[2]))
   selected.append((plan,fs))
  wc(stage/'QUERIES.csv',qs);query=run([str(QUERY),str(ENV),str(stage/'bank'),str(stage/'QUERIES.csv'),str(stage/'QUERY_OUTPUT.csv')],stage/'query.log',env,job['id']+'_query')
  read_start=time.monotonic();qr=rows(stage/'QUERY_OUTPUT.csv');assert len(qr)==45000;byq={r['query_id']:r for r in qr};packed={};events_to_map=[];blurs=[]
  for plan,frames in selected:
   center=np.zeros((50,len(GRID)),np.float32);pid=np.zeros_like(center);receiver=[];values=[];aux=[];cov=C['receiver_plans'][plan];line=[]
   for b,frame in enumerate(frames):
    desc=raw.snapshot(stage/'bank'/f'iteration_{frame}');fil=desc['filaments'];ij=np.floor((fil[:,:2]-np.array([np.float32(-7.55),np.float32(-7.88)]))/.25).astype(int);ok=(ij[:,0]>=0)&(ij[:,0]<34)&(ij[:,1]>=0)&(ij[:,1]<45);centreidx=ij[ok,0]+ij[ok,1]*34;center[b,np.unique(centreidx)]=1
    vv=[]
    for ci in IDX:
     q=byq[f'{plan}_g{b}_{ci}'];pid[b,ci]=np.float32(float(q['ppm_float32']))>np.float32(.1);vv.append([float(q[k]) for k in ['ppm_float32','physical_free','wind_x','wind_y','wind_z']])
    q=byq[f'{plan}_r{b}'];assert q['physical_free']=='1';vv.append([float(q[k]) for k in ['ppm_float32','physical_free','wind_x','wind_y','wind_z']]);values.append(vv)
    ev=dict(cov[b]);ev['concentration_ppm']=float(np.float32(float(q['ppm_float32'])));ev['event_hit']=int(np.float32(ev['concentration_ppm'])>np.float32(.1));receiver.append(ev)
    if plan=='PUBLIC_B':aux.append([[float(byq[f'{plan}_a{b}_{k}'][f]) for f in ['ppm_float32','physical_free','wind_x','wind_y','wind_z']] for k in range(4)])
    line.append(dict(block=b,target_physical_s=cov[b]['physical_target_s'],frame=frame,selected_physical_s=manifest[frame]['physical_snapshot_time_s'],next_frame_physical_s=manifest[frame+1]['physical_snapshot_time_s'],wind_index=10,SHA256=manifest[frame]['SHA256']))
   center[:,~FREE]=0;pid[:,~FREE]=0;packed[plan+'_O0']=center;packed[plan+'_O1']=pid;packed[plan+'_query']=np.asarray(values,dtype='<f4');packed[plan+'_frames']=np.array(frames,np.int32)
   packed[plan+'_receiver_ppm']=np.array([r['concentration_ppm'] for r in receiver],np.float32);packed[plan+'_receiver_events']=np.array([r['event_hit'] for r in receiver],np.uint8)
   if aux:packed[plan+'_auxiliary']=np.array(aux,dtype='<f4')
   wc(dest/(plan+'_RECEIVER_EVENTS.csv'),receiver);wc(dest/(plan+'_FRAME_LINEAGE.csv'),line);wc(stage/(plan+'_map_events.csv'),receiver)
   native_map=run([str(BINARY),'map',str(T/'inputs/R0'),str(stage/(plan+'_map_events.csv')),str(stage/(plan+'_map'))],stage/(plan+'_map.log'),env_native,job['id']+'_'+plan+'_map')
   for count in [20,35,50]:
    r=rows(stage/(plan+'_map')/f'map_blocks_{count}.csv');p=np.array([float(q['probability']) for q in r],np.float32);p[~FREE]=0;packed[f'{plan}_A1_{count}']=p
    for method,array in [('O0',center),('O1',pid)]:
     filename=f'{plan}_{method}_{count}.f32';array[:count].mean(0).astype('<f4').tofile(stage/filename);blurs.append(dict(id=filename[:-4],path=str(stage/filename)))
  wc(stage/'blur_jobs.csv',blurs);blur=run([str(BINARY),'blur_score',str(T/'inputs/R0'),str(stage/'blur_jobs.csv'),str(stage/'blur')],stage/'blur.log',env_native,job['id']+'_native_blur')
  for b in blurs:packed[b['id']+'_blurred']=np.fromfile(stage/'blur'/b['id']/'blurred.f32',dtype='<f4');assert np.isfinite(packed[b['id']+'_blurred']).all()
  np.savez_compressed(dest/'PREDICTIONS.npz',**packed);processing_wall=time.monotonic()-read_start
  used.update([0,manifest[-1]['frame']]);preserve_start=time.monotonic();(dest/'used_frames').mkdir()
  for frame in sorted(used):shutil.copy2(stage/'bank'/f'iteration_{frame}',dest/'used_frames'/f'iteration_{frame}')
  for p in stage.iterdir():
   if p.is_file() and (p.name.startswith('RNG.') or p.name in ['PARAMETERS.yaml','PHYSICAL_FRAME_TIME.csv','PHYSICAL_FRAME_TIME.csv.default_mt19937_state.txt','generation.log','query.log','blur.log']):shutil.copy2(p,dest/p.name)
  wc(dest/'QUERY_NUMERIC_PACKING_INDEX.csv',[dict(rows=len(qr),raw_query_CSV_SHA256=sh(stage/'QUERY_OUTPUT.csv'),all_query_values_packaged=True,storage='PREDICTIONS.npz query and auxiliary tensors',coordinate_source='COMMON_TASK_CONTRACT receptor covariates plus fixed447 grid centres')])
  rec=dict(job,status='PASS_PHYSICAL_REFERENCE_AND_NATIVE_READOUT',generation=generation,query=query,index_wall_s=index_wall,processing_wall_s=processing_wall,preservation_wall_s=time.monotonic()-preserve_start,end_to_end_wall_s=time.monotonic()-start,raw_frames=1803,used_raw_frames=len(used),all_used_wind_index10=True,reference_parameters_unchanged=True,predictions_SHA256=sh(dest/'PREDICTIONS.npz'),rng_initial_SHA256=[sh(dest/f'RNG.stream{k}.initial.txt') for k in [0,1]],max_filaments=max(int(r['filaments']) for r in manifest))
  
  nstart=time.monotonic();cold=Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/cold_inputs/DERIVED');nb=Path('/dev/shm/nmc_cold/native_cold_entry')
  assert sh(nb)=='490114422d661bbbe3ed6173f36b800b4880ac80812a16513124988ae3ba5c06'
  ni=rows(cold/'rng.csv')[0];assert ni['ready']=='0' and ni['phase']=='0' and ni['engine']=='470211272'
  ncost=run([str(nb),'history',str(cold),str(dest/'PUBLIC_B_RECEIVER_EVENTS.csv'),str(dest/'N0')],dest/'N0.log',env_native,job['id']+'_qualified_cold_N0')
  rec['native_N0_cost']=ncost;dump(dest/'QUALIFICATION.json',rec)
  L['records'].append(rec);save();remove_owned_stage(stage);del qr,byq,packed;gc.collect();resource(job['id']+'_complete')
 L['status']='PASS_ALL_SIX_PREREGISTERED_OBSERVATIONS'
except Exception as ex:L.update(status='TECHNICAL_REFERENCE_STOP',error=repr(ex))
finally:save();print(json.dumps({'status':L['status'],'done':len(L['records']),'calls':L['gas_calls'],'error':L.get('error')}),flush=True)
