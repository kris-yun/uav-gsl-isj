from common_r2 import *
import csv,numpy as np,math,shutil
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
grid=rows(R1/'native_inputs/inputs/DERIVED/input.csv');indexes=np.array([int(r['cell_index']) for r in grid if r['occupancy']=='1']);plans={k:rows(CORE/'registered_covariates'/n) for k,n in [('B4','B4_plan.csv'),('PUBLIC_B','D00.csv')]}
profile=[]
for c in ['B000','B001','B002']:
 folder=Path('D:/ZYC/A-gas/workspace/PMFS_RK2B_DATA_20261010/realizations')/(c+'_reference0');d=load(folder/'QUALIFICATION.json')
 profile.append(dict(id=c+'_reference0',bank='/mnt/hgfs/workspace/PMFS_RK2B_DATA_20261010/realizations/'+c+'_reference0',historical_generation_wall_s=d['generation']['wall_s'],historical_receiver_readout_wall_s=d['native_response']['wall_s'],historical_generation_RSS=d['generation']['sampled_process_group_peak_RSS_bytes']))
fresh=load(Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/fresh/GENERATION_LEDGER.json'))
registry=load(BASE/'outputs/PMFS_RK2B_CONTINUOUS_20261010_CORE/experiment_registry.json');anchor=next(j for j in registry['jobs'] if j['job_id']=='B000_reference0')
plan=dict(entry_unix=load(WORK/'ENTRY_TIME.json')['start_unix'],old_profile_banks=profile,registered_selection='first three source IDs sorted bytewise from existing D1V1 reference0 banks',plans=plans,grid_indexes=indexes.tolist(),world_library='/home/zyc/pmfs_m2_process_observation_20261010/libgaden.so',world_library_SHA256=load(CORE/'ENTRY_VM_PREFLIGHT.json')['world_library_SHA256'],query='/home/zyc/pmfs_m2_process_observation_20261010/query_native',environment='/home/zyc/pmfs_b4_native_validation_20261009/derived_B4',slow_recent_generation_wall_s=max(r['generation']['wall_s'] for r in fresh['records']),slow_recent_query_wall_s=max(r['native_response']['wall_s'] for r in fresh['records']),new_physical_anchor_source='B000_reference0',anchor_full_1000s=True,prefix_truncation=False,numerical_target='native_query ppm_float32/physicalfree/all wind values and all1803 raw generation frames',physics_parameters_changed=False)
dump(CORE/'PROFILE_PREREGISTRATION.json',plan)
plan['IO_anchor_seeds']=[anchor['gaussian_seed'],anchor['uniform_seed']];dump(CORE/'PROFILE_PREREGISTRATION.json',plan)
src=(WORK/'profile_worker.py').read_bytes();code=r'''import subprocess
ram=Path('/dev/shm/pmfs_r2');assert not ram.exists();ram.mkdir()
p=subprocess.Popen(['python3',str(t/'profile_worker.py')],stdout=(t/'profile.stdout').open('w'),stderr=(t/'profile.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'old_banks':3,'new_same_contract_IO_anchor_calls':1}))
'''
files={'PROFILE_PREREGISTRATION.json':(CORE/'PROFILE_PREREGISTRATION.json').read_bytes(),'profile_worker.py':src,'raw_decode.py':(R1/'source/portable/raw_decode.py').read_bytes()}
r=json.loads(upload(files,code,'start_three_old_bank_cost_profiles_and_RAM_anchor',45));dump(CORE/'PROFILE_STARTED.json',r);print(json.dumps(r))
