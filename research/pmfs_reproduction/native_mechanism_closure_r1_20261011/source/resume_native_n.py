from common_n import *
worker=(WORK/'native_worker.py').read_text()
worker=worker.replace("tasks=json.loads((t/'NATIVE_EXECUTION_TASKS.json').read_text());", "tasks=json.loads((t/'NATIVE_RESUME_TASKS.json').read_text());")
old="ledger=dict(status='RUNNING',records=[],native_2D_forward_calls=0,offline_wall_s=0,scientific_start_unix=time.time(),gas_calls=0)"
new="ledger=json.loads((t/'NATIVE_PRE_RESUME_LEDGER.json').read_text());ledger['status']='RUNNING';ledger['resumed_unix']=time.time()"
assert old in worker;worker=worker.replace(old,new)
worker=worker.replace("size=sum(q.stat().st_size for q in t.rglob('*') if q.is_file())", "size=sum(q.stat().st_size for q in Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011').rglob('*') if q.is_file())+315529864")
setup='''from pathlib import Path
import json,time,subprocess,shutil
t=Path(REMOTE)
old=json.loads((t/'NATIVE_EXECUTION_LEDGER.json').read_text())
assert old['status']=='BUDGET_STOP'
assert old['records'][-1]['id']=='N0_D03' and old['records'][-1]['forward_calls']==0
backup=t/'NATIVE_PRE_RESUME_LEDGER.json';assert not backup.exists();backup.write_text(json.dumps(old,indent=2))
done={x['id'] for x in old['records'] if x['exitcode']==0}
tasks=[x for x in json.loads((t/'NATIVE_EXECUTION_TASKS.json').read_text()) if x['id'] not in done]
failed=t/'native_results'/'N0_D03'
if failed.exists():
 assert not list(failed.rglob('candidates.csv'))
 failed.rename(failed.with_name('N0_D03_RESOURCE_STOP_ZERO_CALLS'))
(t/'NATIVE_RESUME_TASKS.json').write_text(json.dumps(tasks,indent=2))
assert shutil.disk_usage(t).free>=4294967296
p=subprocess.Popen(['python3',str(t/'native_worker_resume.py')],stdout=(t/'native_worker_resume.stdout').open('w'),stderr=(t/'native_worker_resume.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'remaining':len(tasks),'completed_not_repeated':len(done),'previous_forward_calls':old['native_2D_forward_calls']}))
'''.replace('REMOTE',repr(REMOTE))
r=json.loads(upload({'native_worker_resume.py':worker.encode()},setup,'resume_remaining_native',45))
dump(CORE/'NATIVE_WORKER_RESUMED.json',r);print(json.dumps(r))
(CORE/'source'/'native_worker_resume.py').write_text(worker,encoding='utf-8')
