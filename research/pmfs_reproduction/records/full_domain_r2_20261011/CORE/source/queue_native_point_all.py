from common_r2 import *
import csv
catalog=load(CORE/'SOURCE_CATALOG_AND_COVERAGE.json')['catalog'];payload=[]
for c in catalog:payload.append(dict(id=c['source_id'],origin_i=c['representative_cell']%34,origin_j=c['representative_cell']//34,size_i=1,size_j=1,point_x=c['x'],point_y=c['y']))
with (CORE/'N_POINT_ALL_JOBS.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(payload[0]),lineterminator='\n');w.writeheader();w.writerows(payload)
code=r'''import subprocess
p=subprocess.Popen(['python3',str(t/'point_all_worker.py')],stdout=(t/'point_all.stdout').open('w'),stderr=(t/'point_all.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'point_forward_calls':64,'source_mode':'COARSE_ALL32','waits_for_serial_reference_completion':True}))
'''
r=json.loads(upload({'point_all_worker.py':(WORK/'point_all_worker.py').read_bytes(),'N_POINT_ALL_JOBS.csv':(CORE/'N_POINT_ALL_JOBS.csv').read_bytes()},code,'queue_native_point_all_after_world_banks',45));dump(CORE/'POINT_ALL_STARTED.json',r);print(json.dumps(r))
