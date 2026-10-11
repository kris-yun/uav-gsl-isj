from common_n import *
src=(CORE/'source/cold_native_worker_storage_fix.py').read_text()
src=src.replace("(t/'COLD_NATIVE_TASKS.json')","(t/'COLD_FRESH_TASKS.json')").replace("(t/'COLD_NATIVE_LEDGER.json')","(t/'COLD_FRESH_LEDGER.json')").replace("(t/'COLD_NATIVE_PROGRESS.json')","(t/'COLD_FRESH_PROGRESS.json')")
start=src.index("prior=json.loads((t/'NATIVE_EXECUTION_LEDGER.json').read_text())")
end=src.index("root=Path('/mnt/hgfs",start)
src=src[:start]+"""prior=json.loads((t/'COLD_NATIVE_LEDGER.json').read_text());assert prior['status'].startswith('PASS')
ledger=dict(status='RUNNING',records=[],native_2D_forward_calls=prior['native_2D_forward_calls'],offline_wall_s=prior['offline_wall_s'],prior_calls=prior['native_2D_forward_calls'],prior_wall_s=prior['offline_wall_s'],scientific_start_unix=time.time(),gas_calls=0)
"""+src[end:]
coordinator=(CORE/'source/coordinate_fresh_native.py').read_text()
coordinator=coordinator.replace("dest=t/'events'/(job['oid']+'.csv');assert not dest.exists()", "dest=t/'events'/(job['oid']+'.csv');assert not dest.exists()")
coordinator=coordinator.replace("str(t/'inputs/DERIVED')","str(data/'cold_inputs/DERIVED')").replace("(t/'NATIVE_FRESH_EXECUTION_TASKS.json')","(t/'COLD_FRESH_TASKS.json')")
coordinator=coordinator.replace("subprocess.run(['python3',str(t/'native_fresh_worker.py')],check=True)","""while not (t/'COLD_NATIVE_LEDGER.json').exists() or json.loads((t/'COLD_NATIVE_LEDGER.json').read_text())['status']=='RUNNING':
 assert time.time()-p['entry_unix']<9000;time.sleep(2)
assert json.loads((t/'COLD_NATIVE_LEDGER.json').read_text())['status'].startswith('PASS')
subprocess.run(['python3',str(t/'cold_fresh_worker.py')],check=True)""")
code=r'''import subprocess
p=subprocess.Popen(['python3',str(t/'coordinate_qualified_fresh_cold.py')],stdout=(t/'qualified_fresh_cold.stdout').open('w'),stderr=(t/'qualified_fresh_cold.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'fresh_histories':6,'qualified_cold_initializer':True,'waits_for_physical_PASS_and_first12_complete':True}))
'''
r=json.loads(upload({'cold_fresh_worker.py':src.encode(),'coordinate_qualified_fresh_cold.py':coordinator.encode()},code,'queue_qualified_cold_fresh6_after_primary12',45));dump(CORE/'QUALIFIED_FRESH_COLD_STARTED.json',r)
(CORE/'source/cold_fresh_worker.py').write_text(src,encoding='utf-8');(CORE/'source/coordinate_qualified_fresh_cold.py').write_text(coordinator,encoding='utf-8');print(json.dumps(r))
