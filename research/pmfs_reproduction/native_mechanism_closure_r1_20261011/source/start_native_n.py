from common_n import *
import shutil
assert load(CORE/'N0_WIND_PLANE_QUALIFICATION.json')['status']=='PASS'
tasks=[]
for label in ['E3','B4']:
 folder=REMOTE+'/inputs/'+label
 tasks.append(dict(id=label+'_saved_map_scores',mode='score',input=folder,payload=folder+'/score_jobs.csv'))
 tasks.append(dict(id=label+'_short_forward_OFF',mode='anchor_forward',input=folder,payload=folder+'/anchor_job.csv'))
for j in load(CORE/'DERIVED_NATIVE_TASKS.json'):
 tasks.append(dict(id='N0_'+j['oid'],mode='history',input=REMOTE+'/inputs/DERIVED',payload=j['event_file']))
dump(CORE/'NATIVE_EXECUTION_TASKS.json',tasks)
files={'native_worker.py':(WORK/'native_worker.py').read_bytes(),'NATIVE_EXECUTION_TASKS.json':(CORE/'NATIVE_EXECUTION_TASKS.json').read_bytes()}
code=r'''
import subprocess,os,time
p=subprocess.Popen(['python3',str(t/'native_worker.py')],stdout=(t/'native_worker.stdout').open('w'),stderr=(t/'native_worker.stderr').open('w'),start_new_session=True)
(t/'NATIVE_WORKER_STARTED.json').write_text(json.dumps(dict(pid=p.pid,started=time.time(),tasks=16,new_gas=0,navigation=0)))
print(json.dumps(dict(pid=p.pid,started=True,tasks=16)))
'''
r=json.loads(upload(files,code,'START_NATIVE_ANCHORS_AND12_REPLAYS',45));dump(CORE/'NATIVE_WORKER_STARTED.json',r);print(json.dumps(r))
for n in ['native_worker.py','start_native_n.py','prepare_native_inputs.py','common_n.py']:
 shutil.copyfile(WORK/n,CORE/'source'/n)
