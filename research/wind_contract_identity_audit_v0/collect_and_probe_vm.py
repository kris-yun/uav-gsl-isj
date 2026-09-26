#!/usr/bin/env python3
"""Read existing assets only; do not import ROS or execute a simulator."""
import csv, hashlib, json, math, re, shutil
from pathlib import Path
import numpy as np

out=Path('/home/zyc/wind_contract_identity_audit_20260926/evidence')
assert not out.exists(), 'refuse evidence overwrite'
(out/'assets').mkdir(parents=True)
root=Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House01')
run=Path('/home/zyc/native_pmfs_recovery_v1/runs/NATIVE_RECOVERY_R1_House01_S0_20260923T071027Z')
core=Path('/home/zyc/hcmc_gaden_seed_build_20260922/src/GADEN/gaden_common/third_party/gaden_core')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inventory=[]
def preserve(p,name=None):
    target=out/'assets'/(name or p.name)
    shutil.copyfile(p,target)
    inventory.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'copy':target.name})
for p in [Path('/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/wind_value_server.py'),
          Path('/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/vgr_sim_node.py'),
          Path('/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/sim_timebase.py'),
          Path('/home/zyc/native_pmfs_recovery_v1/checkout/reference/house1_raw_query.cpp'),
          Path('/home/zyc/native_pmfs_recovery_v1/vgr_native_pmfs_recovery_20260923.launch.py'),
          core/'src/WindSequence.cpp',core/'src/PlaybackSimulation.cpp',
          core/'src/Simulation.cpp',core/'src/Environment.cpp',core/'include/gaden/internal/MathUtils.hpp']:
    preserve(p)
preserve(run/'measurement_events.csv')
preserve(run/'wind_trace.csv')
preserve(run/'wind_source_update.csv')
preserve(run/'wind_query.csv')
preserve(run/'wind_value_server.log')
manifest=json.loads((run/'runtime_manifest.json').read_text())
server_hash=sha(out/'assets/wind_value_server.py')
assert server_hash==manifest['wind_server_sha256'], 'server differs from R1 manifest'
selected={k:v for k,v in manifest.items() if k not in ('launch_arguments','launch_args','effective_parameters','ground_truth_use') and not k.startswith('source_')}
# Preserve only wind-relevant run arguments, rather than source-truth fields.
arglines=(run/'launch_args.txt').read_text().splitlines()
allowed=('vgr_data_path','config_id','flight_height','seed','realtime_factor','gas_backend','raw_query_executable','run_id','run_dir')
selected['wind_launch_arguments']=[s for s in arglines if s.split(':=',1)[0] in allowed]
(out/'assets/wind_runtime_manifest.json').write_text(json.dumps(selected,indent=2,sort_keys=True)+'\n')
excerpt=[]
for i,line in enumerate((run/'launch.log').read_text(errors='replace').splitlines(),1):
    if any(s in line for s in ('Loading VGR data','Gas backend=raw_house1_snapshot','anemometer z is')):
        excerpt.append(f'{i}: {line}')
(out/'assets/R1_wind_launch_excerpt.txt').write_text('\n'.join(excerpt)+'\n')
with (run/'wind_trace.csv').open(newline='') as f: trace=list(csv.DictReader(f))
assert {float(r['z']) for r in trace}=={0.3}
assert any('anemometer z is 0' in s for s in excerpt)
events=list(csv.DictReader((Path(__file__).parent/'event_vectors.csv').open(newline='')))
historical=list(csv.DictReader((run/'measurement_events.csv').open(newline='')))
assert len(events)==len(historical)==20
for a,b in zip(events,historical):
    for key in ('event_id','steady_ns','robot_x','robot_y','wind_speed','wind_direction'):
        assert math.isclose(float(a[key]),float(b[key]),rel_tol=0,abs_tol=1e-12), (key,a,b)
sites=[]
for r in events:
    xy=(float(r['robot_x']),float(r['robot_y']))
    if xy not in sites: sites.append(xy)
assert len(sites)==4

def write_probe(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['wind_state','x','y','z','u','v','speed','direction','source_file'])
        w.writeheader(); w.writerows(rows)
csv_rows={0.3:[],0.0:[]}; details=[]
wind_dir=root/'wind_simulations/2,4-1_fast'
files=[]
for p in sorted(wind_dir.iterdir()):
    if not p.name.endswith('.csv') or any(s in p.name for s in ('_U','_V','_W')): continue
    match=re.search(r'_(\d+)\.csv$',p.name)
    if match: files.append((int(match.group(1)),p))
assert sorted(n for n,p in files)==list(range(11))
for state,p in files:
    positions=[]; vectors=[]
    with p.open() as f:
        reader=csv.reader(f); next(reader)
        for row in reader:
            if len(row)>=6:
                vectors.append([float(row[0]),float(row[1]),float(row[2])])
                positions.append([float(row[3]),float(row[4]),float(row[5])])
    pos=np.array(positions); vec=np.array(vectors)
    inventory.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'wind_state':state,'row_count':len(pos),'contract':'CSV nearest 3D'})
    for z in (0.3,0.0):
        for x,y in sites:
            query=np.array([x,y,z]); dists=np.linalg.norm(pos-query[np.newaxis,:],axis=1)
            index=int(np.argmin(dists)); u,v,_=map(float,vec[index])
            csv_rows[z].append(dict(wind_state=state,x=x,y=y,z=z,u=u,v=v,speed=math.hypot(u,v),direction=math.atan2(v,u),source_file=str(p)))
            details.append({'state':state,'query':[x,y,z],'csv_row':index,'selected_xyz':pos[index].tolist(),'selected_uvw':vec[index].tolist(),'distance':float(dists[index])})
write_probe(out/'wind_state_probe.csv',csv_rows[0.3])
write_probe(out/'forward_z_probe.csv',csv_rows[0.0])
(out/'CSV_NEAREST_POINTS.json').write_text(json.dumps(details,indent=2,sort_keys=True)+'\n')

# Binary-file diagnostics only: mirror WindSequence's legacy double-array decode
# and Simulation::SampleWind's voxel lookup. No GADEN process is started.
with (root/'OccupancyGrid3D.csv').open() as f: header=[next(f).strip() for _ in range(4)]
(out/'assets/OccupancyGrid3D_header.txt').write_text('\n'.join(header)+'\n')
mincoord=np.array([float(x) for x in header[0].split()[1:]],dtype=np.float32)
dims=tuple(int(x) for x in header[2].split()[1:]); n=math.prod(dims)
cellsize=np.float32(float(header[3].split()[1]))
gas_dirs=sorted(p for p in (root/'gas_simulations/2,4-1_fast').iterdir() if p.is_dir() and p.name.startswith('FilamentSimulation'))
gas_dir=gas_dirs[0]; binfiles=sorted((gas_dir/'wind').glob('wind_iteration_*'))
assert len(binfiles)==11
binary_rows=[]; order=[]
for seqindex,p in enumerate(binfiles):
    state=int(p.name.rsplit('_',1)[1]); order.append(state)
    raw=p.read_bytes(); assert len(raw)==24*n, 'legacy binary size mismatch'
    vec=np.frombuffer(raw,dtype='<f8').reshape(3,n).T.astype(np.float32)
    inventory.append({'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'wind_state':state,'sequence_index':seqindex,'contract':'legacy arrays raster voxel float32'})
    for x,y in sites:
        z=0.3; point=np.array([x,y,z],dtype=np.float32)
        ijk=((point-mincoord)/cellsize).astype(np.int32)
        assert all(0<=int(i)<d for i,d in zip(ijk,dims))
        k=int(ijk[0]+ijk[1]*dims[0]+ijk[2]*dims[0]*dims[1]); u,v,_=map(float,vec[k])
        binary_rows.append(dict(wind_state=state,x=x,y=y,z=z,u=u,v=v,speed=math.hypot(u,v),direction=math.atan2(v,u),source_file=str(p)))
write_probe(out/'binary_sensor_contract_probe.csv',binary_rows)
(out/'ASSET_INVENTORY.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
metadata={'csv_state_count':11,'binary_state_count':11,'sensor_z':0.3,'forward_z':0.0,
          'primary_match_z_arms':[0.3],'forward_z_diagnostic':[0.0],
          'binary_sequence_file_ids_in_loader_order':order,
          'sensor_iteration_mode':'seeded_time_replay','max_iteration':1999,'seed':0,
          'expected_trace_iteration_formula':'(1925 + step) % 1998',
          'trace_step_index_formula_verified':all(int(r['iteration'])==(1925+int(r['step']))%1998 for r in trace),
          'truth_read':False,'source_localization_scores_computed':False,'simulators_started':False}
(out/'CONTRACT_METADATA.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
print(json.dumps(metadata,indent=2))
