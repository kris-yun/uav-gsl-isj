from pathlib import Path
import json,time,csv,subprocess,math,numpy as np,hashlib
t=Path(__file__).resolve().parent;data=Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');p=json.loads((t/'FRESH_CONFIRMATION_PREREGISTRATION.json').read_text());reg=json.loads((t/'FRESH_REGISTRY.json').read_text())
while not (data/'fresh/GENERATION_LEDGER.json').exists() or json.loads((data/'fresh/GENERATION_LEDGER.json').read_text())['status']=='RUNNING':
 assert time.time()-p['entry_unix']<9000,'TOTAL_TIME_CAP_WAITING_FRESH_WORLD';time.sleep(2)
assert json.loads((data/'fresh/GENERATION_LEDGER.json').read_text())['status'].startswith('PASS'),'FRESH_INPUT_NOT_QUALIFIED'
tasks=[];before=[]
for job in p['jobs']:
 source=data/'fresh/realizations'/job['id'];queries={r['query_id']:r for r in csv.DictReader((source/'QUERY_OUTPUT.csv').open())};dest=t/'events'/(job['oid']+'.csv');assert not dest.exists()
 events=[]
 for b,e in enumerate(reg['receiver_plan']):
  q=queries[f'b{b}_p{e["pose_id"]}'];u,v=float(q['wind_x']),float(q['wind_y']);ppm=np.float32(float(q['ppm_float32']))
  events.append(dict(block_id=b,stop_id=e['pose_id'],physical_target_s=e['physical_s'],x=e['xyz'][0],y=e['xyz'][1],z=e['xyz'][2],wind_speed=math.hypot(u,v),wind_direction_to=math.atan2(v,u),concentration_ppm=float(ppm),event_hit=int(ppm>np.float32(.1))))
 with dest.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(events[0]),lineterminator='\n');w.writeheader();w.writerows(events)
 before.append({'oid':job['oid'],'event_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_labels_in_consumer_payload':False})
 tasks.append(dict(id='FRESH_N0_'+job['oid'],mode='history',input=str(data/'cold_inputs/DERIVED'),payload=str(dest)))
(t/'COLD_FRESH_TASKS.json').write_text(json.dumps(tasks,indent=2));(data/'FRESH_NATIVE_INPUT_FREEZE.json').write_text(json.dumps(before,indent=2))
while not (t/'COLD_NATIVE_LEDGER.json').exists() or json.loads((t/'COLD_NATIVE_LEDGER.json').read_text())['status']=='RUNNING':
 assert time.time()-p['entry_unix']<9000;time.sleep(2)
assert json.loads((t/'COLD_NATIVE_LEDGER.json').read_text())['status'].startswith('PASS')
subprocess.run(['python3',str(t/'cold_fresh_worker.py')],check=True)
