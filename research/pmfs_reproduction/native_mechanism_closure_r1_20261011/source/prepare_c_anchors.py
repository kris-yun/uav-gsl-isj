from common_n import *
m2=load(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/frozen_contract.json');b=load(BASE/'outputs/PMFS_RK2B_CONTINUOUS_20261010_CORE/experiment_registry.json')
banks=[]
for j in m2['jobs']:
 if j['role']=='reference':banks.append(dict(candidate=j['candidate_id'],replicate=j['realization'],source_xyz=j['source_xyz'],seeds=j['seeds'],original_bank='/home/zyc/pmfs_m2_process_observation_20261010/realizations/'+j['candidate_id']+'_'+str(j['realization'])))
for j in b['jobs']:
 if j['role']=='reference':banks.append(dict(candidate=j['job_id'].split('_')[0],replicate=j['replicate'],source_xyz=j['source_xyz'],seeds=[j['gaussian_seed'],j['uniform_seed']],original_bank=b['remote_data_path']+'/realizations/'+j['job_id']))
assert len(banks)==10
anchors=[dict(j,id='OFF_'+j['candidate']+'_'+str(j['replicate']),D=1,V=1) for j in banks if j['candidate'] in ['C7','K2'] and j['replicate']==0]
jobs=[dict(j,id=f'{j["candidate"]}_{j["replicate"]}_D{d}V{v}',D=d,V=v) for j in banks for d,v in [(0,0),(0,1),(1,0)]]
plan=dict(entry_unix=load(WORK/'ENTRY_TIME.json')['start_unix'],data=DATA,anchors=anchors,jobs=jobs,library_directory='/dev/shm/nmc_C',intervention_library_SHA256=load(CORE/'C_BUILD.json')['library_SHA256'],native_library_tail='/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_common/lib:/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:/opt/ros/humble/lib',parameters_template='/home/zyc/pmfs_b4_native_validation_20261009/B4_generation_RESOLVED.yaml',generator='/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator',
 D0='Additional navXY constraint; native3D wall slide retained; no CFD re-solve; artificial support',V0='All vertical displacement cancelled after all three native Gaussian calls; cache-consumption rule fixed; not buoyancy-only',
 RNG_note='Same initial engine/cache states, not stable per-particle common noise after paths diverge',start_only_OFF_anchors=True)
dump(CORE/'FACTORIAL_CONTRACT.json',plan)
code=r'''import subprocess,os
env=os.environ.copy();env['NMC_CAMPAIGN_MODE']='ANCHORS'
p=subprocess.Popen(['python3',str(t/'factorial_worker.py')],env=env,stdout=(t/'factorial_OFF.stdout').open('w'),stderr=(t/'factorial_OFF.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'authorized_gas_OFF_calls':2,'factorial_not_started':True}))
'''
r=json.loads(upload({'FACTORIAL_CONTRACT.json':(CORE/'FACTORIAL_CONTRACT.json').read_bytes(),'factorial_worker.py':(WORK/'factorial_worker.py').read_bytes()},code,'start_two_FULL_OFF_engine_anchors',45));dump(CORE/'FULL_OFF_ANCHORS_STARTED.json',r);print(json.dumps(r))
