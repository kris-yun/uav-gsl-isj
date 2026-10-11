from common_r2 import *
import shutil
assert load(CORE/'NATIVE_SHORT_CONNECTION.json')['status'].startswith('PASS')
plan=dict(entry_unix=load(WORK/'ENTRY_TIME.json')['start_unix'],data=DATA,mode='COARSE',source_count=32,reference_count=2,generator_same_world=True,full1000s=True,parameters_changed=['source_xyz_only_from_catalog','output_and_RAM_readonly_environment_paths_only'],readout_prefixes=[20,35,50],score_head_temperature=1,scientific_fail_continue=True,technical_repair_limit_per_type=2,gas_calls_already=1)
dump(CORE/'REFERENCE_EXECUTION_CONTRACT.json',plan)
files={'REFERENCE_EXECUTION_CONTRACT.json':(CORE/'REFERENCE_EXECUTION_CONTRACT.json').read_bytes(),'reference_worker.py':(WORK/'reference_worker.py').read_bytes()}
code=r'''import subprocess
p=subprocess.Popen(['python3',str(t/'reference_worker.py')],stdout=(t/'references.stdout').open('w'),stderr=(t/'references.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'mode':'COARSE','sources':32,'new_reference_calls':64,'new_observations_not_started':True,'all_domain_covered':447}))
'''
r=json.loads(upload(files,code,'start64_registered_coarse_world_references',45));dump(CORE/'REFERENCES_STARTED.json',r);print(json.dumps(r))
