"""Source-blind receiver/grid queries, floor by physical time; bounded standalone calls."""
from pathlib import Path
import bisect,csv,hashlib,json,os,signal,subprocess,sys,time
import numpy as np
t=Path(__file__).resolve().parent;phase=sys.argv[1]
assert phase in ['smoke','remaining']
contract=json.loads((t/'frozen_contract.json').read_text());jobs=contract['jobs'][:2] if phase=='smoke' else contract['jobs'][2:]
schedule=list(csv.DictReader((t/'FROZEN_RECEPTOR_SCHEDULE.csv').open()))
raw=list(csv.DictReader((t/'FROZEN_INPUT.csv').open()));meta=json.loads((t/'FROZEN_METADATA.json').read_text())
grid=[]
for row in raw:
 if row['occupancy']!='1':continue
 index=int(row['cell_index']);i=index%meta['width'];j=index//meta['width']
 x=float(np.float32(np.float32(meta['origin_x'])+np.float32((i+.5)*.25)))
 y=float(np.float32(np.float32(meta['origin_y'])+np.float32((j+.5)*.25)))
 grid.append((index,x,y))
assert len(grid)==447
core=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws');env=os.environ.copy()
env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=str(core/'install/gaden_common/lib')+':'+str(core/'build/gaden_common/third_party/gaden_core/third_party/libbsc')+':/opt/ros/humble/lib')
assert not (t/(phase+'_QUERY_STARTED.json')).exists();(t/(phase+'_QUERY_STARTED.json')).write_text(json.dumps(dict(phase=phase,start=time.time())))
ledger=dict(phase=phase,status='RUNNING',records=[])
try:
 for job in jobs:
  root=t/'realizations'/(job['candidate_id']+'_'+str(job['realization']))
  assert json.loads((root/'GENERATION_QUALIFICATION.json').read_text())['verdict'].startswith('PASS')
  times=list(csv.DictReader((root/'ALL_FRAME_SHA256_AND_TIME.csv').open()));timestamps=[float(row['physical_snapshot_time_s']) for row in times]
  queries=[];lineage=[]
  for receptor in schedule:
   target=float(receptor['physical_target_s']);frame=bisect.bisect_right(timestamps,target)-1
   assert frame>=0 and frame+1<len(times) and timestamps[frame]<=target<timestamps[frame+1]
   block=receptor['block_id'];branch=receptor['membership_branch'];prefix='b'+block+'_v'+branch
   queries.append(dict(query_id='receiver_'+prefix,frame=frame,x=receptor['sensor_x'],y=receptor['sensor_y'],z=receptor['sensor_z']))
   for index,x,y in grid:
    queries.append(dict(query_id='grid_'+prefix+'_c'+str(index),frame=frame,x=x,y=y,z=receptor['sensor_z']))
   lineage.append(dict(block_id=block,membership_branch=branch,target_physical_s=target,selected_frame=frame,
                       selected_frame_physical_s=timestamps[frame],next_frame_physical_s=timestamps[frame+1],wind_index=times[frame]['wind_index']))
  queries.sort(key=lambda r:r['frame'])
  for name,rows in [('QUERIES.csv',queries),('QUERY_PHYSICAL_LINEAGE.csv',lineage)]:
   assert not (root/name).exists()
   with (root/name).open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  start=time.monotonic();peak=0;reason=None
  cmd=[str(t/'query_native'),'/home/zyc/pmfs_b4_native_validation_20261009/derived_B4',str(root/'bank'),str(root/'QUERIES.csv'),str(root/'QUERY_OUTPUT.csv')]
  with (root/'query.log').open('w') as log:
   p=subprocess.Popen(cmd,env=env,stdout=log,stderr=log,start_new_session=True)
   while p.poll() is None:
    rss=0
    try:
     for line in Path('/proc/'+str(p.pid)+'/status').read_text().splitlines():
      if line.startswith('VmRSS:'):rss=int(line.split()[1])*1024
    except FileNotFoundError:pass
    peak=max(peak,rss)
    if rss>1073741824:reason='QUERY_RSS_CAP'
    if time.monotonic()-start>180:reason='QUERY_WALL_CAP_180S'
    if reason:
     os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=3);break
    time.sleep(.05)
   exitcode=p.wait()
  assert exitcode==0 and reason is None,(exitcode,reason,(root/'query.log').read_text()[-2000:])
  output=list(csv.DictReader((root/'QUERY_OUTPUT.csv').open()));assert len(output)==len(queries)==51*448
  assert all(np.isfinite(float(r['ppm_float32'])) and float(r['ppm_float32'])>=0 for r in output)
  receptor=[r for r in output if r['query_id'].startswith('receiver_')]
  assert len(receptor)==51 and all(r['physical_free']=='1' for r in receptor)
  record=dict(candidate_id=job['candidate_id'],realization=job['realization'],role=job['role'],query_rows=len(output),receiver_rows=51,
              unique_physical_frames=len(set(r['frame'] for r in output)),query_wall_s=time.monotonic()-start,peak_RSS_bytes=peak,exitcode=exitcode,
              output_sha256=hashlib.sha256((root/'QUERY_OUTPUT.csv').read_bytes()).hexdigest(),
              observation_operator='native GADEN SampleConcentration; native float PID sum for one gas; one consumed sample per actual block',
              source_truth_role_read=False)
  (root/'QUERY_QUALIFICATION.json').write_text(json.dumps(record,indent=2));ledger['records'].append(record)
  (t/(phase+'_QUERY_LEDGER.json')).write_text(json.dumps(ledger,indent=2))
 ledger['status']='PASS_NATIVE_SOURCE_CONDITIONED_RECEIVER_AND_GRID_QUERY'
 if phase=='smoke':
  smoke=dict(verdict='PASS_BOTH_NATIVE_PHYSICAL_AND_QUERY_SMOKE',first_two_realizations_included_in_eight=True,
             generation_wall_s=sum(json.loads((t/'realizations'/(j['candidate_id']+'_0')/'GENERATION_QUALIFICATION.json').read_text())['generation_wall_s'] for j in jobs),
             query_wall_s=sum(r['query_wall_s'] for r in ledger['records']),
             bank_bytes=sum(json.loads((t/'realizations'/(j['candidate_id']+'_0')/'GENERATION_QUALIFICATION.json').read_text())['bank_bytes'] for j in jobs),
             outcome_based_selection=False,additional_reference_count_preregistered=6)
  (t/'SMOKE_QUALIFICATION.json').write_text(json.dumps(smoke,indent=2))
except Exception as error:ledger['status']='STOP_QUERY_OR_ALIGNMENT_FAULT_NO_EXTRA_BANK';ledger['error']=repr(error)
(t/(phase+'_QUERY_LEDGER.json')).write_text(json.dumps(ledger,indent=2));print(json.dumps(ledger,indent=2))
