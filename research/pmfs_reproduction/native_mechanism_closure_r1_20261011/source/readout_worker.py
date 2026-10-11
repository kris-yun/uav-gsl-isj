"""Existing-bank native query, native blur, and native map transform. No gas generation."""
from pathlib import Path
import os,json,csv,time,bisect,subprocess,hashlib,shutil,signal
import numpy as np
T=Path(__file__).resolve().parent;DATA=Path(json.loads((T/'CAMPAIGN_CONTRACT.json').read_text())['remote_data_path']) if False else Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011')
P=json.loads((T/'READOUT_CONTRACT.json').read_text());D=DATA/'readout';D.mkdir(exist_ok=False)
import raw_decode as raw
def rows(p):return list(csv.DictReader(Path(p).open()))
def wc(p,rs):
 with Path(p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',ROS_DOMAIN_ID='229',LD_LIBRARY_PATH=json.loads((T/'ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH'])
envq=env.copy();envq['LD_LIBRARY_PATH']='/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_common/lib:/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:/opt/ros/humble/lib'
assert sh(P['query_executable'])==P['query_SHA256']
input=rows(T/'inputs/DERIVED/input.csv');free=np.array([r['occupancy']=='1' for r in input]);indexes=np.flatnonzero(free)
ledger={'status':'RUNNING','records':[],'new_gas_calls':0,'new_native_candidate_forwards':0};begun=time.time();last=0
def save():(D/'READOUT_LEDGER.json').write_text(json.dumps(ledger,indent=2))
def run(cmd,folder,label,qe=False):
 global last
 start=time.time()
 with (folder/(label+'.log')).open('w') as f:
  p=subprocess.Popen(cmd,env=envq if qe else env,stdout=f,stderr=f,start_new_session=True)
  while p.poll() is None:
   if time.time()-start>180:os.killpg(p.pid,signal.SIGINT);p.wait(timeout=10);raise RuntimeError('PER_OPERATOR_180S')
   if time.time()-P['entry_unix']>9000:os.killpg(p.pid,signal.SIGINT);p.wait(timeout=10);raise RuntimeError('TOTAL150MIN')
   if time.time()-last>30:print(json.dumps({'stage':'READOUT_NATIVE','done':len(ledger['records']),'task':label,'elapsed_s':time.time()-begun}),flush=True);last=time.time()
   time.sleep(.1)
 assert p.returncode==0,(cmd,(folder/(label+'.log')).read_text()[-1500:])
 return time.time()-start
try:
 for schedule in P['schedules']:
  common=rows(T/schedule['events']);lineage=[]
  for bank in P['banks']:
   folder=D/(schedule['id']+'_'+bank['id']);folder.mkdir()
   src=Path(bank['path']);times=rows(src/'PHYSICAL_FRAME_TIME.csv');tt=[float(r['physical_snapshot_time_s']) for r in times]
   qs=[];selected=[]
   for b,e in enumerate(common):
    i=bisect.bisect_right(tt,float(e['physical_target_s']))-1;assert i>=0 and i+1<len(tt)
    frame=int(times[i]['frame']);selected.append(frame)
    for ci in indexes:
     x=float(np.float32(-7.55))+ (int(ci)%34+.5)*.25;y=float(np.float32(-7.88))+(int(ci)//34+.5)*.25
     qs.append(dict(query_id=f'g{b}_{ci}',frame=frame,x=x,y=y,z=-.2))
    qs.append(dict(query_id=f'r{b}',frame=frame,x=e['x'],y=e['y'],z=e['z']))
   wc(folder/'QUERIES.csv',qs)
   wall=run([P['query_executable'],P['environment'],str(src/'bank'),str(folder/'QUERIES.csv'),str(folder/'QUERY_OUTPUT.csv')],folder,'native_query',True)
   q=rows(folder/'QUERY_OUTPUT.csv');assert len(q)==50*448
   original_hash=[];center=np.zeros((50,len(input)),np.float32);pid=np.zeros_like(center);receiver=[]
   qm={r['query_id']:r for r in q};outside=nonfree=total=0
   for b,(frame,e) in enumerate(zip(selected,common)):
    snap=src/'bank'/f'iteration_{frame}';desc=raw.snapshot(snap);assert desc['wind_index']==10
    original_hash.append(dict(block=b,frame=frame,physical_actual_s=tt[bisect.bisect_right(tt,float(e['physical_target_s']))-1],SHA256=sh(snap)))
    fil=desc['filaments'];ij=np.floor((fil[:,:2]-np.array([np.float32(-7.55),np.float32(-7.88)]))/np.float32(.25)).astype(int)
    bounds=(ij[:,0]>=0)&(ij[:,0]<34)&(ij[:,1]>=0)&(ij[:,1]<45);ind=ij[bounds,0]+ij[bounds,1]*34
    center[b,np.unique(ind)]=1;outside+=int((~bounds).sum());nonfree+=int((~free[ind]).sum());total+=len(fil)
    for ci in indexes:pid[b,ci]=float(qm[f'g{b}_{ci}']['ppm_float32'])>np.float32(.1)
    r=qm[f'r{b}'];event=dict(e);event['event_hit']=int(float(r['ppm_float32'])>np.float32(.1));event['concentration_ppm']=r['ppm_float32'];receiver.append(event)
   center[:,~free]=0;pid[:,~free]=0
   np.savez_compressed(folder/'READOUT_FIELDS.npz',O0=center,O1=pid)
   wc(folder/'EVENTS_O1.csv',receiver);wc(folder/'SELECTED_FRAME_LINEAGE.csv',original_hash)
   for name,a in [('O0',center.mean(0)),('O1',pid.mean(0))]:a.astype('<f4').tofile(folder/(name+'.f32'))
   jobs=[dict(id=name,path=str(folder/(name+'.f32'))) for name in ['O0','O1']];wc(folder/'blur_jobs.csv',jobs)
   run([str(T/'native_entry'),'blur_score',str(T/'inputs/DERIVED'),str(folder/'blur_jobs.csv'),str(folder/'native_blur')],folder,'native_blur')
   run([str(T/'native_entry'),'map',str(T/'inputs/DERIVED'),str(folder/'EVENTS_O1.csv'),str(folder/'A1_native_map')],folder,'native_map')
   a=np.array([float(r['probability']) for r in rows(folder/'A1_native_map/final_map.csv')],np.float32);a[~free]=0;a.tofile(folder/'A1.f32')
   rec=dict(id=folder.name,candidate=bank['candidate'],replicate=bank['replicate'],schedule=schedule['id'],source_bank=bank['path'],query_wall_s=wall,
       queries=len(q),query_SHA256=sh(folder/'QUERY_OUTPUT.csv'),particle_snapshot_occurrences=total,nonfree_projected_occurrences=nonfree,outside_occurrences=outside,
       physical_nonfree_grid_queries=sum(r['physical_free']!='1' for r in q),complete=True)
   ledger['records'].append(rec);save();print(json.dumps({'done':len(ledger['records']),'total':len(P['banks'])*2,'id':folder.name}),flush=True)
   assert shutil.disk_usage(T).free>=4294967296 and shutil.disk_usage(DATA).free>=4294967296
 ledger['status']='PASS_ALL_EXISTING_BANK_READOUTS_NATIVE_OPERATORS'
except Exception as e:ledger['status']='STOP_RELATED_READOUT';ledger['error']=repr(e)
finally:ledger['wall_s']=time.time()-begun;save()
raise SystemExit(0 if ledger['status'].startswith('PASS') else 1)
