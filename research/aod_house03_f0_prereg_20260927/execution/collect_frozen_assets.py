#!/usr/bin/env python3
"""Read only geometry, navigation configuration, wind, and generator code; no gas."""
import ast, hashlib, json, re, shutil, tarfile
from pathlib import Path
import numpy as np

OUT=Path('/tmp/aod_h03_f0_assets_20260927_v4')
OUT.mkdir(exist_ok=False)
ROWS=[]
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def collect(p,name,expected=None):
    p=Path(p); h=sha(p)
    if expected: assert h==expected,(str(p),h,expected)
    q=OUT/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
    ROWS.append(dict(path=str(p),copy=name,bytes=p.stat().st_size,sha256=h,expected_sha256=expected,passed=True))
    return q

E1=Path('/home/zyc/E1_CROSS_HOUSE_CONTRACT_REVIEW_20260925_FINAL')
SC=Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House03')
NAV=Path('/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4')
collect(SC/'OccupancyGrid3D.csv','geometry/OccupancyGrid3D.csv','ac8c9e69e762c8941dab46cd7e804684c2aa50dc6f0912806d19b070c135c4af')
collect(NAV/'H03_seed0/off/geometry_export/pruned_meta.json','geometry/pruned_meta.json','cdda9e893a35fb2ee3e094a5d66b23acb1503afc61210f2a038a1117b607c3e5')
for s in [0,1]:
    collect(NAV/f'H03_seed{s}/off/geometry_export/pruned_occupancy.bin',f'geometry/pruned_seed{s}.bin','32d362e73211532547d76f699e957ca3c0f3f6f2b3f6cc4f4fa862cf4f4943d7')
for name in ['E1_RESULT.json','E1_INDEPENDENT_CHECK.json','E1_GEOMETRY_PROVENANCE.md','E1_HOUSE_PROBE_CONTRACTS.tsv','E1_HOUSE_SOURCE_PANELS.tsv','SHA256SUMS.txt']:
    collect(E1/'evidence/e1'/name,'e1/'+name)

launch=collect(NAV/'H03_seed0/off/launch_command.sh','navigation/frozen_launch_command.sh')
lc=collect('/home/zyc/rmfe_v2_runtime_causal_20260814_a2_001/code/rmfe_pmfs_closedloop_v2.launch.py','navigation/frozen_launch.py')
old=collect('/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/vgr_sim_node.py.pre_nav_v4_1786262252','navigation/archived_vgr_sim_node.py')
cur=collect('/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/vgr_sim_node.py','navigation/current_vgr_sim_node.py')
tb=collect('/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/sim_timebase.py','navigation/sim_timebase.py')
texts=[old.read_text(encoding='utf-8-sig'),cur.read_text(encoding='utf-8-sig')]
defaults=[]
for t in texts:
    d={}
    for node in ast.walk(ast.parse(t)):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='declare_parameter' and len(node.args)>=2:
            if isinstance(node.args[0],ast.Constant) and node.args[0].value in ['step_size','max_uav_speed','sim_dt_s']:
                d[node.args[0].value]=ast.literal_eval(node.args[1])
    defaults.append(d)
assert defaults[0]==defaults[1] and defaults[0]['max_uav_speed']==1.5,defaults
cmd=launch.read_text();assert 'start_x:=2.0' in cmd and 'start_y:=0.0' in cmd
assert 'step_size:=' not in cmd and 'max_uav_speed:=' not in cmd
assert "'max_uav_speed':" not in lc.read_text() and "'step_size':" not in lc.read_text()
dt=float(re.search(r'\bsim_dt_s:=([0-9.]+)',cmd)[1])
v=min(defaults[0]['max_uav_speed'],defaults[0]['step_size']/dt)
(OUT/'NAVIGATION_SPEED_AUDIT.json').write_text(json.dumps(dict(passed=True,start_xy=[2.0,0.0],archived_defaults=defaults[0],current_defaults=defaults[1],frozen_sim_dt_s=dt,nominal_navigation_speed_m_s=v,launch_overrides_motion_speed=False,selection_used_gas=False),indent=2)+'\n')

inv=collect('/home/zyc/e1_repo_20260925/evidence/causal_compositional_plume_world_model_v1/C0_5_HOUSE_WIND_INVENTORY_20260923.json','configuration/historical_wind_inventory.json')
rec=json.loads(inv.read_text())['houses']['House03']['wind_configs']['1-2,5_fast']
windrows=[]
for s in range(11):
    p=SC/f'wind_simulations/1-2,5_fast/1-2,5_fast_{s}.csv'
    a=np.loadtxt(p,delimiter=',',skiprows=1)
    assert a.ndim==2 and a.shape[1]==6 and np.isfinite(a).all(),str(p)
    alt=SC/f'House03/wind_simulations/1-2,5_fast/1-2,5_fast_{s}.csv'
    assert sha(p)==sha(alt),(str(p),str(alt))
    r=next(x for x in rec['iteration_records'] if x['name']==f'wind_iteration_{s}')
    bp=Path(rec['path'])/r['name'];assert sha(bp)==r['sha256'] and bp.stat().st_size==r['size_bytes']
    windrows.append(dict(state=s,csv_path=str(p),csv_bytes=p.stat().st_size,csv_sha256=sha(p),duplicate_csv_path=str(alt),duplicate_csv_sha256=sha(alt),rows=int(a.shape[0]),columns=6,all_finite=True,xyz_min=a[:,3:6].min(axis=0).tolist(),xyz_max=a[:,3:6].max(axis=0).tolist(),preprocessed_path=str(bp),preprocessed_bytes=bp.stat().st_size,preprocessed_sha256=sha(bp),preprocessed_matches_historical_inventory=True))
(OUT/'WIND_ASSET_AUDIT.json').write_text(json.dumps(dict(passed=True,house='House03',wind='1-2,5_fast',state_count=11,states=windrows,gas_values_read=False),indent=2)+'\n')
generator=collect('/home/zyc/e2_repo_20260925/research/environment_level_benchmark_v0/acquire_e2_vm.py','configuration/frozen_gaden_acquisition.py')
gd=None
gt=ast.parse(generator.read_text(encoding='utf-8-sig'))
constants={}
for node in gt.body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='TIMES':
        constants['TIMES']=ast.literal_eval(node.value)
for node in ast.walk(gt):
    if isinstance(node,ast.Dict):
        for k,value in zip(node.keys,node.values):
            if isinstance(k,ast.Constant) and k.value=='simulation_parameters':
                gd={ast.literal_eval(kk):(constants[vv.id] if isinstance(vv,ast.Name) else ast.literal_eval(vv)) for kk,vv in zip(value.keys,value.values)}
assert gd is not None
(OUT/'GADEN_CONFIGURATION_AUDIT.json').write_text(json.dumps(dict(passed=True,source='frozen E2 acquisition configuration',simulation_parameters=gd,source_height_override_m=0.20,observation_height_m=0.20,generator_executed=False),indent=2)+'\n')
for p in ['/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator','/home/zyc/hcmc_gaden_seed_build_20260922/src/GADEN/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp']:
    pp=Path(p);ROWS.append(dict(path=p,copy=None,bytes=pp.stat().st_size,sha256=sha(pp),executed=False,passed=True))
(OUT/'ASSET_INPUT_HASHES.json').write_text(json.dumps(ROWS,indent=2)+'\n')
(OUT/'READ_SCOPE_AUDIT.json').write_text(json.dumps(dict(geometry_and_configuration_only=True,fresh_house03_gas_read=False,historical_house03_gas_read=False,source_truth_outcomes_read=False,pmfs_forward_executed=False,gaden_generated=False,score_executed=False),indent=2)+'\n')
archive=OUT.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as t:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():t.add(p,arcname=str(p.relative_to(OUT)))
print(json.dumps(dict(asset_archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,wind_states=11,navigation_speed_m_s=v),indent=2))
