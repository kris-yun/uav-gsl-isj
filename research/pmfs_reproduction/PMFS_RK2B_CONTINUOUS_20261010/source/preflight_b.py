"""No gas generation: resource, runtime, source geometry and RNG initialization freeze."""
from common_b import *
import shutil,csv,numpy as np,importlib.util
CORE.mkdir(exist_ok=True);RAW.mkdir(exist_ok=True)
assert not any(CORE.iterdir()) and not any(RAW.iterdir()),'Only resume the empty preflight directories'
plan=load(PARENT/'B_DESIGN_ONLY/B_PROSPECTIVE_GEOMETRY_ONLY_PLAN.json')
assert sha(PARENT/'B_DESIGN_ONLY/B_PROSPECTIVE_GEOMETRY_ONLY_PLAN.json')==load(WORK/'pro_handoff/machine_contract.json')['original_B_plan_SHA256']
seeds=load(WORK/'pro_handoff/NEW_SEED_PROPOSAL.json')
assert seeds['original_12_seed_records']==plan['proposed_rng_initial_states']
extra_key=next(k for k in seeds if k not in ('status','base_seed_binding','derivation','original_12_seed_records'))
extra=seeds[extra_key];assert len(extra)==12
records=plan['proposed_rng_initial_states']+extra
for r in records:
    byte_order='little' if r['role'] in ('reference','heldout') else 'big'
    assert int.from_bytes(hashlib.sha256(r['tag'].encode()).digest()[:4],byte_order)==r['proposed_uint32_seed']
    r['gaussian_seed']=r['proposed_uint32_seed']
    r['uniform_tag']=r['tag']+'|native-uniform-stream-v1'
    r['uniform_seed']=int.from_bytes(hashlib.sha256(r['uniform_tag'].encode()).digest()[:4],'big')
    r['job_id']=r['candidate_id'].replace('candidate_B_','B')+'_'+r['role']+str(r['replicate'])
    r['source_xyz']=next(s['xyz_m'] for s in plan['sources'] if s['future_candidate_id']==r['candidate_id'])
assert len({r['gaussian_seed'] for r in records})==24 and len({r['uniform_seed'] for r in records})==24
assert len({r['gaussian_seed'] for r in records}|{r['uniform_seed'] for r in records})==48
# Auxiliary receiver selection uses only the frozen eligibility table and geometry.
with (PARENT/'B_DESIGN_ONLY/B_GEOMETRY_ELIGIBILITY_AUDIT.csv').open(newline='',encoding='utf-8') as f:a=list(csv.DictReader(f))
pts=[];original={(r['grid_i'],r['grid_j']) for r in plan['receivers']}
for r in a:
    i,j=int(r['grid_i']),int(r['grid_j'])
    if r['receiver_base_eligible']!='True' or (i,j) in original or int(r['component'])!=plan['sources'][0]['component']:continue
    x,y=-7.55+(i+.5)*.25,-7.88+(j+.5)*.25
    if min((x-s['xyz_m'][0])**2+(y-s['xyz_m'][1])**2 for s in plan['sources'])<1:continue
    pts.append(dict(grid_i=i,grid_j=j,xyz_m=[x,y,-.2]))
selected=[];existing=[r['xyz_m'] for r in plan['receivers']]
for _ in range(min(4,len(pts))):
    chosen=min(pts,key=lambda p:(-min((p['xyz_m'][0]-q[0])**2+(p['xyz_m'][1]-q[1])**2 for q in existing),p['grid_i'],p['grid_j']))
    selected.append(chosen);existing.append(chosen['xyz_m']);pts.remove(chosen)
registry=dict(parent_commit='5df5771ca916f209d041e3e3ecd548ec65eb8424',original_B_plan=plan,
    new_seed_records=records,auxiliary_receivers=selected,random_binding='Explicit qualified M2_GAUSSIAN_SEED=base uint32 and M2_UNIFORM_SEED=SHA(tag|native-uniform-stream-v1) first4 big-endian. Existing library has no base-seed convention; both native stream states and cache are frozen explicitly.',
    sources=plan['sources'],receiver_plan=[dict(block_id=b,pose_id=r['stop_id'],physical_s=t,xyz=r['xyz_m']) for r in plan['receivers'] for b,t in [(r['stop_id']*5+k,t) for k,t in enumerate(r['physical_query_times_s'])]],
    all_receiver_xyz=[r['xyz_m'] for r in plan['receivers']]+[r['xyz_m'] for r in selected],
    model_rules={k:v for k,v in load(PARENT/'RK2_NEW/contract.json').items() if k in ('ridge_lambda','solver_maxiter','solver_gtol','solver_ftol','KKT_relative_tolerance','split_quantiles','split_loss_tolerance')},
    primary_gate=load(WORK/'pro_handoff/machine_contract.json')['original_B_gate'],hard_limits=load(WORK/'pro_handoff/machine_contract.json')['limits'],
    extra_reference_pairs='original2,extra2,all4 preregistered',heads=['H0','H1'],training_and_test_information='reference-only features/counts/phi; heldout/diagnostic scalar-only infer; truth after prediction freeze',
    auxiliary_scope='14-pose matrix; 4 extras never train main kernels; candidate-side F fallback on extras; no zero-shot claim',
    source_stream_initialization_not_physics_generation=True)
dump(WORK/'registry_preflight.json',registry)
tail='''
import hashlib,subprocess,time,os,shutil,json
data=Path(DATA);assert not data.exists();data.mkdir()
old=Path('/home/zyc/pmfs_m2_process_observation_20261010')
core=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws')
root_free=shutil.disk_usage(t).free;data_free=shutil.disk_usage(data).free
assert root_free>=4294967296+16777216,'VM code filesystem lacks4GiB+16MiB protection'
mode=24 if data_free>=6442450944+4294967296 else 12
assert data_free>=3221225472+4294967296,'Data filesystem lacks12-mode reservation+margin'
assert os.cpu_count()>=1
registry=json.loads((t/'registry_preflight.json').read_text())
jobs=registry['new_seed_records'] if mode==24 else registry['original_B_plan']['proposed_rng_initial_states']
if mode==12:jobs=[j for j in registry['new_seed_records'] if j['role'] in ['reference','heldout']]
jobs=sorted(jobs,key=lambda j:({'reference':0,'extra_reference':1,'diagnostic':2,'heldout':3}[j['role']],j['candidate_id'],j['replicate']))
assets=[old/'libgaden.so',old/'query_native',old/'include/gaden/internal/MathUtils.hpp',core/'install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator',Path('/home/zyc/pmfs_b4_native_validation_20261009/B4_generation_RESOLVED.yaml'),Path('/home/zyc/pmfs_b4_native_validation_20261009/derived_B4/OccupancyGrid3D.csv'),Path('/home/zyc/pmfs_b4_native_validation_20261009/derived_B4/wind/wind_iteration_10')]
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in assets}
assert hashes[str(old/'libgaden.so')]=='ed042a1c317a0350e3e1bd701c3ac1e1ab3df23a9807612fd6e91f9234be76c6'
assert hashes[str(old/'query_native')]=='52e282b03b7e109204c1b22b096ab41ca15e33a7cc24625b1b79feaa0b9789f5'
assert hashes[str(assets[-2])]=='00914f3d7114d45d764ff24be9e832da70d6e2e69528918f2c3c1143fea40295'
assert hashes[str(assets[-1])]=='18b07a284fd3432c77759499b96d2bb5153e945efe0b6644ce0537911697722a'
# Process isolation checked explicitly by final prephysical preflight.
inc=core/'src/gaden_common/third_party/gaden_core'
cmd=['c++','-O2','-std=c++20','-I'+str(old/'include'),'-I'+str(inc/'include'),'-I'+str(inc/'third_party/DDA/third_party/glm'),str(t/'rng_probe.cpp'),'-o',str(t/'rng_probe')]
started=time.monotonic();p=subprocess.run(cmd,capture_output=True,timeout=180);(t/'rng_build.stdout').write_bytes(p.stdout);(t/'rng_build.stderr').write_bytes(p.stderr);assert p.returncode==0,p.stderr.decode()
init={}
for j in jobs:
    d=t/'precommitted_rng'/j['job_id'];d.mkdir(parents=True)
    env=os.environ.copy();env.update(M2_GAUSSIAN_SEED=str(j['gaussian_seed']),M2_UNIFORM_SEED=str(j['uniform_seed']),M2_RNG_TRACE=str(d/'RNG'))
    subprocess.run([str(t/'rng_probe')],env=env,check=True,timeout=10)
    init[j['job_id']]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in d.iterdir() if '.initial.' in p.name or '.cache' in p.name}
    assert len(init[j['job_id']])==4
result=dict(status='PASS_PREPHYSICAL_RESOURCES_RUNTIME_RNG_PROBE',chosen_mode=mode,new_physical_outputs=0,root_free_bytes=root_free,data_free_bytes=data_free,root_new_code_reservation_bytes=16777216,data_path=str(data),runtime_assets_SHA256=hashes,rng_probe_build_wall_s=time.monotonic()-started,rng_probe_source_SHA256=hashlib.sha256((t/'rng_probe.cpp').read_bytes()).hexdigest(),RNG_initial_and_cache_SHA256=init,jobs=jobs)
(t/'PREFLIGHT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
'''.replace('DATA',repr(DATA))
res=load(WORK/'registry_preflight.json')
p=load(PARENT/'RK2_NEW/contract.json')
result=json.loads(upload({'rng_probe.cpp':(WORK/'rng_probe.cpp').read_bytes(),'registry_preflight.json':(WORK/'registry_preflight.json').read_bytes()},tail,'PREFLIGHT_RESOURCE_RNG',180))
dump(CORE/'PREFLIGHT.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('jobs','RNG_initial_and_cache_SHA256','runtime_assets_SHA256')},indent=2))
