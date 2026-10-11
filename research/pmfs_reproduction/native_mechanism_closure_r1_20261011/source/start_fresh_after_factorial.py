from common_n import *
import ast
p=load(CORE/'FRESH_CONFIRMATION_PREREGISTRATION.json');b=load(BASE/'outputs/PMFS_RK2B_CONTINUOUS_20261010_CORE/experiment_registry.json')
reg=dict(remote_data_path=DATA+'/fresh',host_data_path='D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/fresh',jobs=[dict(j,job_id=j['id'],role='fresh_confirmation',candidate_id=j['candidate'],gaussian_seed=j['seeds'][0],uniform_seed=j['seeds'][1]) for j in p['jobs']],hard_limits=dict(generation_s=1800,response_s=600,total_scientific_s=7200),new_disk_cap_bytes=6442450944,receiver_plan=b['receiver_plan'],all_receiver_xyz=b['all_receiver_xyz'])
pref=dict(chosen_mode='FRESH6_ORIGINAL_NATIVE_PHYSICS',RNG_initial_and_cache_SHA256=load(CORE/'FRESH_RNG_PRECOMMIT.json'))
src=(BASE/'work/pmfs_rk2b_continuous_20261010/generate_b.py').read_text()
src=src.replace("(ROOT/'experiment_registry.json')","(ROOT/'FRESH_REGISTRY.json')").replace("(ROOT/'PREFLIGHT.json')","(ROOT/'FRESH_PREFLIGHT.json')")
src=src.replace("assert not (DATA/'CAMPAIGN_STARTED.json').exists()", """# Original-world branch waits for any current intervention generation to finish.
while True:
    status=json.loads((DATA.parent/'factorial/GAS_LEDGER.json').read_text())['status']
    if status.startswith('PASS_THIRTY') or status.startswith('STOP'):break
    assert time.time()-FRESH_ENTRY<9000,'TOTAL_TASK_CAP_WHILE_WAITING'
    time.sleep(2)
assert not (DATA/'CAMPAIGN_STARTED.json').exists()""")
src=src.replace("OLD=Path('/home/zyc/pmfs_m2_process_observation_20261010')", "OLD=Path('/home/zyc/pmfs_m2_process_observation_20261010');FRESH_ENTRY="+repr(p['entry_unix'])+"\nDATA.mkdir(exist_ok=False)")
src=src.replace("disk=sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file())", "disk=sum(p.stat().st_size for p in DATA.parent.rglob('*') if p.is_file())+315529864")
src=src.replace("if time.monotonic()-begun>LIMIT['total_scientific_s']:", "if time.monotonic()-begun>LIMIT['total_scientific_s'] or time.time()-FRESH_ENTRY>9000:")
src=src.replace("print(json.dumps(LED,indent=2))", "print(json.dumps({'status':LED['status'],'records':len(LED['records']),'error':LED.get('error')}))")
dump(CORE/'FRESH_REGISTRY.json',reg);dump(CORE/'FRESH_PREFLIGHT.json',pref)
files={'FRESH_REGISTRY.json':(CORE/'FRESH_REGISTRY.json').read_bytes(),'FRESH_PREFLIGHT.json':(CORE/'FRESH_PREFLIGHT.json').read_bytes(),'fresh_worker.py':src.encode(),
 'verify_raw_receiver_queries.py':(BASE/'work/pmfs_rk2b_continuous_20261010/verify_raw_receiver_queries.py').read_bytes(),'cache_native.py':(BASE/'work/pmfs_rk2b_continuous_20261010/cache_native.py').read_bytes()}
code=r'''import subprocess
p=subprocess.Popen(['python3',str(t/'fresh_worker.py')],stdout=(t/'fresh6.stdout').open('w'),stderr=(t/'fresh6.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'fresh_physics':6,'waits_for_active_factorial':True,'world_unmodified':True}))
'''
r=json.loads(upload(files,code,'fresh6_original_physics_waiting_serial',45));dump(CORE/'FRESH6_WORKER_STARTED.json',r)
(CORE/'source/fresh_worker.py').write_text(src,encoding='utf-8');print(json.dumps(r))
