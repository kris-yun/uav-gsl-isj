"""Serial same-GADEN engine interventions; OFF anchors gate factorial."""
from pathlib import Path
import os,json,csv,time,subprocess,signal,shutil,hashlib,zlib,struct
import yaml,numpy as np
import raw_decode as raw
T=Path(__file__).resolve().parent;P=json.loads((T/'FACTORIAL_CONTRACT.json').read_text());DATA=Path(P['data']);mode=os.environ.get('NMC_CAMPAIGN_MODE','ANCHORS')
D=DATA/'factorial';D.mkdir(exist_ok=True)
L={'status':'RUNNING','mode':mode,'records':[],'gas_calls':0,'started_unix':time.time(),'physical_retries':0}
if mode=='FACTORIAL':
 L=json.loads((D/'GAS_LEDGER.json').read_text());assert L['status']=='PASS_TWO_FULL_OFF_ANCHORS';L['mode']=mode;L['status']='RUNNING'
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open()))
def wc(p,r):
 with Path(p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
def save():(D/'GAS_LEDGER.json').write_text(json.dumps(L,indent=2))
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',ROS_DOMAIN_ID='229',LD_LIBRARY_PATH=P['library_directory']+':'+P['native_library_tail'])
assert sh(Path(P['library_directory'])/'libgaden.so')==P['intervention_library_SHA256']
base=yaml.safe_load(Path(P['parameters_template']).read_text())['/**']['ros__parameters'];lastbeat=0;lastcheck=0
try:
 for job in P['anchors'] if mode=='ANCHORS' else P['jobs']:
  folder=D/job['id'];assert not folder.exists();folder.mkdir()
  pars=base.copy();pars.update(source_position_x=job['source_xyz'][0],source_position_y=job['source_xyz'][1],source_position_z=job['source_xyz'][2],results_location=str(folder/'bank'),r6_time_trace_path=str(folder/'PHYSICAL_FRAME_TIME.csv'))
  (folder/'PARAMETERS.yaml').write_text(yaml.safe_dump({'/**':{'ros__parameters':pars}},sort_keys=False))
  e=env.copy();e.update(M2_GAUSSIAN_SEED=str(job['seeds'][0]),M2_UNIFORM_SEED=str(job['seeds'][1]),M2_RNG_TRACE=str(folder/'RNG'),NMC_RESTRICT_NAV=str(job['D']==0 and 1 or 0),NMC_FIX_HEIGHT=str(job['V']==0 and 1 or 0),NMC_STATE_TRACE=str(folder/'STATE_ACCOUNTING.csv'),NMC_NAV_PATH=str(T/'inputs/DERIVED/input.csv'))
  cmd=['bash','-c','source /opt/ros/humble/setup.bash; exec "$@"','bash',P['generator'],'--ros-args','--params-file',str(folder/'PARAMETERS.yaml')]
  start=time.time();peak=0;reason=None;L['gas_calls']+=1;save()
  with (folder/'generation.log').open('w') as f:
   p=subprocess.Popen(cmd,env=e,stdout=f,stderr=f,start_new_session=True)
   while p.poll() is None:
    rss=0
    for item in Path('/proc').glob('[0-9]*/status'):
     try:
      if os.getpgid(int(item.parent.name))==p.pid:rss+=next(int(x.split()[1])*1024 for x in item.read_text().splitlines() if x.startswith('VmRSS:'))
     except (OSError,ProcessLookupError,StopIteration):pass
    peak=max(peak,rss)
    if rss>1610612736:reason='RSS_CAP'
    if time.time()-P['entry_unix']>9000:reason='TOTAL150MIN_CAP'
    if time.time()-start>240:reason='SINGLE_GENERATION240S_ENGINE_PROGRESS_CAP'
    if time.time()-lastcheck>=60:
     lastcheck=time.time();size=sum(q.stat().st_size for q in DATA.rglob('*') if q.is_file())+315529864
     if size>6442450944:reason='NEW_DISK6GIB_CAP'
     if min(shutil.disk_usage(T).free,shutil.disk_usage(DATA).free)<4294967296:reason='FREE4GIB_RESERVE'
     with (D/'RESOURCES.jsonl').open('a') as f:f.write(json.dumps({'task':job['id'],'new_bytes':size,'RSS':rss,'root_free':shutil.disk_usage(T).free,'frames':len(list((folder/'bank').glob('iteration_*')))})+'\n')
    if time.time()-lastbeat>=30:
     lastbeat=time.time();print(json.dumps({'task':job['id'],'gas_calls':L['gas_calls'],'completed':len(L['records']),'generation_s':time.time()-start,'frames':len(list((folder/'bank').glob('iteration_*')))}),flush=True)
    if reason:
     for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGKILL]:
      try:os.killpg(p.pid,sig);p.wait(timeout=3);break
      except subprocess.TimeoutExpired:continue
      except ProcessLookupError:break
     break
    time.sleep(.1)
   code=p.wait()
  rec=dict(job,exitcode=code,resource_stop=reason,wall_s=time.time()-start,peak_RSS_bytes=peak)
  L['records'].append(rec);save();assert code==0 and reason is None,(rec,(folder/'generation.log').read_text()[-2000:])
  frames=sorted((folder/'bank').glob('iteration_*'),key=lambda x:int(x.name.split('_')[-1]));tt=rows(folder/'PHYSICAL_FRAME_TIME.csv');assert len(frames)==len(tt)==1803
  proof=[]
  for fp,row in zip(frames,tt):
   a=raw.snapshot(fp);assert np.allclose(a['source'],job['source_xyz'],atol=1e-6,rtol=0);assert a['gas_type']==13 and a['wind_index']==int(row['wind_index_at_save']);assert len(a['filaments'])==int(row['filaments_after_step'])
   if job['V']==0:assert (a['filaments'][:,2]==np.float32(job['source_xyz'][2])).all()
   proof.append(dict(frame=int(row['frame']),physical_snapshot_time_s=float(row['physical_snapshot_time_s']),wind_index=a['wind_index'],filaments=len(a['filaments']),SHA256=sh(fp),bytes=fp.stat().st_size))
  assert np.diff([r['physical_snapshot_time_s'] for r in proof]).min()>0
  wc(folder/'ALL_FRAME_SHA256_AND_TIME.csv',proof)
  native=Path(job['original_bank'])
  for name in ['RNG.stream0.initial.txt','RNG.stream1.initial.txt','RNG.cache1000.f32','RNG.cache1000.index.txt']:assert sh(folder/name)==sh(native/name),(job['id'],name)
  accounting=rows(folder/'STATE_ACCOUNTING.csv');assert len(accounting)==10001
  alive=0
  for row in accounting:
   alive+=int(row['released'])-int(row['removed']);assert alive==int(row['alive']);assert int(row['gaussian_cache_calls'])%3==0
  rec.update(frames=len(frames),physical_qualification='PASS',native_input_RNG_match=True,accounting_steps=len(accounting),total_released=sum(int(x['released']) for x in accounting),total_removed=sum(int(x['removed']) for x in accounting),nav_blocks=sum(int(x['nav_blocks']) for x in accounting),physical_blocks=sum(int(x['physical_blocks']) for x in accounting),noise_calls=sum(int(x['gaussian_cache_calls']) for x in accounting))
  if mode=='ANCHORS':
   assert all(sh(native/'bank'/fp.name)==r['SHA256'] for fp,r in zip(frames,proof)),'OFF_BANK_BYTES_MISMATCH'
   for name in ['RNG.stream0.final.txt','RNG.stream1.final.txt']:assert sh(folder/name)==sh(native/name)
   assert sh(folder/'PHYSICAL_FRAME_TIME.csv')==sh(native/'PHYSICAL_FRAME_TIME.csv')
   rec['full_OFF_anchor']='PASS_1803_FRAMES_TIME_AND_RNG_IDENTICAL'
  (folder/'QUALIFICATION.json').write_text(json.dumps(rec,indent=2));save()
 L['status']='PASS_TWO_FULL_OFF_ANCHORS' if mode=='ANCHORS' else 'PASS_THIRTY_SAME_ENGINE_COUNTERFACTUAL_BANKS'
except Exception as error:L['status']='STOP_RELATED_PHYSICS';L['error']=repr(error)
finally:save();print(json.dumps({'status':L['status'],'calls':L['gas_calls'],'completed':len(L['records']),'error':L.get('error')}),flush=True)
raise SystemExit(0 if L['status'].startswith('PASS') else 1)
