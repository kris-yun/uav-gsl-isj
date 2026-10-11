from common_n import *
assert load(CORE/'COLD_FIRST_ANCHOR.json')['status'].startswith('PASS')
src=(WORK/'native_worker.py').read_text().replace("(t/'NATIVE_EXECUTION_TASKS.json')","(t/'COLD_NATIVE_TASKS.json')").replace("t/'native_results'","Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/native_cold_results')").replace("str(t/'native_entry')","'/dev/shm/nmc_cold/native_cold_entry'").replace("(t/'NATIVE_EXECUTION_LEDGER.json')","(t/'COLD_NATIVE_LEDGER.json')").replace("(t/'NATIVE_PROGRESS.json')","(t/'COLD_NATIVE_PROGRESS.json')")
src=src.replace("ledger=dict(status='RUNNING',records=[],native_2D_forward_calls=0,offline_wall_s=0,scientific_start_unix=time.time(),gas_calls=0)","""prior=json.loads((t/'NATIVE_EXECUTION_LEDGER.json').read_text())
initial_count=prior['native_2D_forward_calls']+18
initial_wall=prior['offline_wall_s']+30
fresh=t/'NATIVE_FRESH_EXECUTION_LEDGER.json'
if fresh.exists():
 old=json.loads(fresh.read_text());initial_count+=old['native_2D_forward_calls']-old['prior_forward_calls'];initial_wall+=old['offline_wall_s']-old['prior_offline_wall_s']
ledger=dict(status='RUNNING',records=[],native_2D_forward_calls=initial_count,offline_wall_s=initial_wall,prior_calls=initial_count,prior_wall_s=initial_wall,scientific_start_unix=time.time(),gas_calls=0)
root=Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011')
# Existing physical banks are immutable; reserve1GiB for remaining original-world banks and packaging.
base_storage=sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())+315529864+1073741824
assert base_storage<6442450944,'Conservative space reservation failed'
""")
src=src.replace("size=sum(q.stat().st_size for q in t.rglob('*') if q.is_file())", "size=base_storage+sum(q.stat().st_size for q in (root/'native_cold_results').rglob('*') if q.is_file())")
tasks=[dict(id='N0_'+r['oid'],mode='history',input=DATA+'/cold_inputs/DERIVED',payload=r['event_file']) for r in load(CORE/'DERIVED_NATIVE_TASKS.json')]
dump(CORE/'COLD_NATIVE_EXECUTION_TASKS.json',tasks)
code='''from pathlib import Path
import subprocess,os,signal,json,time
t=Path(REMOTE)
# Replace only the waiting, unexecuted old fresh-native queue. No gas process is touched.
fresh=t/'NATIVE_FRESH_EXECUTION_LEDGER.json'
queue=QUEUE
if not fresh.exists():
 try:os.killpg(queue,signal.SIGTERM)
 except ProcessLookupError:pass
 disposition='old unexecuted queue stopped; all physical runs unchanged'
else:disposition='old warm-native branch already running; preserve it as excluded initialization shadow'
p=subprocess.Popen(['python3',str(t/'cold_native_worker.py')],stdout=(t/'cold_native.stdout').open('w'),stderr=(t/'cold_native.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'primary_native_histories':12,'old_queue_disposition':disposition,'same_seed_and_inputs':True}))
'''.replace('REMOTE',repr(REMOTE)).replace('QUEUE',repr(load(CORE/'FRESH_NATIVE_REPLAY_STARTED.json')['pid']))
r=json.loads(upload({'COLD_NATIVE_TASKS.json':(CORE/'COLD_NATIVE_EXECUTION_TASKS.json').read_bytes(),'cold_native_worker.py':src.encode()},code,'start_verified_cold_primary_replays',45));dump(CORE/'COLD_NATIVE_STARTED.json',r);(CORE/'source/cold_native_worker.py').write_text(src,encoding='utf-8');print(json.dumps(r))
