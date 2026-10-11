from common_n import *
worker=(WORK/'native_worker.py').read_text().replace("(t/'NATIVE_EXECUTION_TASKS.json')","(t/'NATIVE_FRESH_EXECUTION_TASKS.json')").replace("(t/'NATIVE_EXECUTION_LEDGER.json')","(t/'NATIVE_FRESH_EXECUTION_LEDGER.json')").replace("(t/'NATIVE_PROGRESS.json')","(t/'NATIVE_FRESH_PROGRESS.json')")
worker=worker.replace("ledger=dict(status='RUNNING',records=[],native_2D_forward_calls=0,offline_wall_s=0,scientific_start_unix=time.time(),gas_calls=0)","""prior=json.loads((t/'NATIVE_EXECUTION_LEDGER.json').read_text())
ledger=dict(status='RUNNING',records=[],native_2D_forward_calls=prior['native_2D_forward_calls']+12,offline_wall_s=prior['offline_wall_s'],prior_forward_calls=prior['native_2D_forward_calls']+12,prior_offline_wall_s=prior['offline_wall_s'],scientific_start_unix=time.time(),gas_calls=0)""")
worker=worker.replace("size=sum(q.stat().st_size for q in t.rglob('*') if q.is_file())", "size=sum(q.stat().st_size for q in Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011').rglob('*') if q.is_file())+315529864")
coordinator='''from pathlib import Path
import json,time,csv,subprocess,math,numpy as np,hashlib
t=Path(__file__).resolve().parent;data=Path(DATA);p=json.loads((t/'FRESH_CONFIRMATION_PREREGISTRATION.json').read_text());reg=json.loads((t/'FRESH_REGISTRY.json').read_text())
while not (data/'fresh/GENERATION_LEDGER.json').exists() or json.loads((data/'fresh/GENERATION_LEDGER.json').read_text())['status']=='RUNNING':
 assert time.time()-p['entry_unix']<9000,'TOTAL_TIME_CAP_WAITING_FRESH_DATA';time.sleep(2)
assert json.loads((data/'fresh/GENERATION_LEDGER.json').read_text())['status'].startswith('PASS'),'FRESH_INPUT_NOT_QUALIFIED'
tasks=[];before=[]
for job in p['jobs']:
 source=data/'fresh/realizations'/job['id'];queries={r['query_id']:r for r in csv.DictReader((source/'QUERY_OUTPUT.csv').open())};dest=t/'events'/(job['oid']+'.csv');assert not dest.exists()
 events=[]
 for b,e in enumerate(reg['receiver_plan']):
  q=queries[f'b{b}_p{e["pose_id"]}'];u,v=float(q['wind_x']),float(q['wind_y']);ppm=np.float32(float(q['ppm_float32']))
  events.append(dict(block_id=b,stop_id=e['pose_id'],physical_target_s=e['physical_s'],x=e['xyz'][0],y=e['xyz'][1],z=e['xyz'][2],wind_speed=math.hypot(u,v),wind_direction_to=math.atan2(v,u),concentration_ppm=float(ppm),event_hit=int(ppm>np.float32(.1))))
 with dest.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(events[0]),lineterminator='\\n');w.writeheader();w.writerows(events)
 before.append({'oid':job['oid'],'event_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_labels_in_consumer_payload':False})
 tasks.append(dict(id='FRESH_N0_'+job['oid'],mode='history',input=str(t/'inputs/DERIVED'),payload=str(dest)))
(t/'NATIVE_FRESH_EXECUTION_TASKS.json').write_text(json.dumps(tasks,indent=2));(data/'FRESH_NATIVE_INPUT_FREEZE.json').write_text(json.dumps(before,indent=2))
subprocess.run(['python3',str(t/'native_fresh_worker.py')],check=True)
'''.replace('DATA',repr(DATA))
code=r'''import subprocess
p=subprocess.Popen(['python3',str(t/'coordinate_fresh_native.py')],stdout=(t/'fresh_native.stdout').open('w'),stderr=(t/'fresh_native.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'fresh_native_histories':6,'starts_only_qualified_fresh_inputs':True}))
'''
r=json.loads(upload({'native_fresh_worker.py':worker.encode(),'coordinate_fresh_native.py':coordinator.encode()},code,'queue_fresh_native_six_qualified_replays',45));dump(CORE/'FRESH_NATIVE_REPLAY_STARTED.json',r);print(json.dumps(r))
(CORE/'source/native_fresh_worker.py').write_text(worker,encoding='utf-8');(CORE/'source/coordinate_fresh_native.py').write_text(coordinator,encoding='utf-8')
