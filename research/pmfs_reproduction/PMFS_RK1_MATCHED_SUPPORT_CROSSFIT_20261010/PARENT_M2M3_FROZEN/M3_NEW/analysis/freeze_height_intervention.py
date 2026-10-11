import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,hashlib,importlib.util,struct
import numpy as np
W=Path(__file__).resolve().parent;B=W.parents[1]
M2=B/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
M1=B/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
O=B/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010'
H=O/'height_intervention';H.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def csvwrite(p,r):
    with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
contract=dict(reason='Point/wall interventions leave strong wrong preference; same 3D centre-readout preserves signal. Test fixed-height planar drift representation with input-only interventions.',
 exploratory_after_M2_and_M3a=True,
 hypotheses=['H_source_slice: using wind at sensor height rather than known release height contributes to wrong source preference.',
             'H_column_closure: a fixed single-height horizontal drift misses vertically heterogeneous airflow; predeclared free-column mean can diagnose this without selecting a lucky plane.'],
 source_form='Exact same two points, oracle diagnostic',wall='native rollback, no slide',
 changed_component='Only u/v in native frozen input CSV; source locations, obstacle mask, event map, Gaussian cache/phase, noise, dt, warmup/record duration, blur, D, and score are unchanged.',
 candidate_independent_wind_fields=['SOURCE_PLANE z=-0.5 m, the fixed release height shared by both candidates',
                                    'COLUMN_FREE_UNIFORM_MEAN over all pre-existing free CFD voxel heights at each same native XY receptor cell centre'],
 source_plane_not_chosen_from_results=True,column_mean_not_source_conditioned=True,
 native_baseline='Reuse four M3 exactpoint/native-wall sensor-plane forwards; no baseline rerun.',
 source_points={'C7':[-3.2,-3.3],'K2':[-1.675,1.495]},RNG_bundles=['T','W'],
 maximum_new_forward_calls=8,forward_combined_wall_s=60,forward_RSS_bytes=536870912,
 new_GADEN_realizations=0,new_CFD=0,new_ROS_nodes=0,new_navigation=0,no_extra_seed_or_threshold=True,
 limitation='These are explicit planar oracle drift contrasts, not repaired official results or a self-consistent 3D model. Column averaging changes a closure assumption; improvements alone do not prove a unique mechanism or deployment utility.')
p=H/'HEIGHT_FROZEN_CONTRACT.json';p.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(H/'HEIGHT_PRE_COMPUTE_SHA256.txt').write_text(sha(p)+'  '+p.name+'\n',encoding='ascii')
spec=importlib.util.spec_from_file_location('raw',M2/'independent_raw_query_verify/verify_raw_receiver_queries.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
occ=r.occupancy(M2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv');nx,ny,nz=occ['dimensions'];rawpath=M2/'frozen_B4_inputs/derived_B4/wind/wind_iteration_10'
raw=rawpath.read_bytes();assert struct.unpack('<ii',raw[:8])==(3,0)
wind=np.frombuffer(raw,dtype='<f4',offset=8).reshape(nz,ny,nx,3);assert wind.size==int(nx*ny*nz*3)
inp=rows(M1/'snapshot/input.csv')
query={int(q['query_id'].split('_c')[-1]):q for q in rows(M2/'native_reference_evidence/realizations/C7_0/QUERY_OUTPUT.csv') if q['query_id'].startswith('grid_b0_v0_')}
profiles=[];sourcefield=[];columnfield=[];native_max=0
for row in inp:
    i=int(row['cell_index']);s=dict(row);c=dict(row)
    if row['occupancy']=='1':
        q=query[i];point=np.array([np.float32(float(q[a])) for a in ['x','y','z']],dtype=np.float32)
        indices=np.trunc((point-occ['minimum'])/occ['cell_size']).astype(int);x,y,z=indices
        v=wind[z,y,x];native_max=max(native_max,abs(float(v[0])-float(row['u'])),abs(float(v[1])-float(row['v'])))
        assert np.array_equal(v,np.array([np.float32(float(q[a])) for a in ['wind_x','wind_y','wind_z']]))
        sourcepoint=point.copy();sourcepoint[2]=np.float32(-.5);zs=int(np.trunc((sourcepoint[2]-occ['minimum'][2])/occ['cell_size']))
        assert occ['data'][zs,x,y]==0
        vs=wind[zs,y,x]
        free=np.flatnonzero(occ['data'][:,x,y]==0);assert len(free)>0
        vc=wind[free,y,x].astype(np.float64).mean(axis=0).astype(np.float32)
        for field,val in [(s,vs),(c,vc)]:field['u']=repr(float(val[0]));field['v']=repr(float(val[1]))
        profiles.append(dict(cell_index=i,grid_i=row['grid_i'],grid_j=row['grid_j'],x=float(point[0]),y=float(point[1]),native_u=float(v[0]),native_v=float(v[1]),native_w=float(v[2]),source_u=float(vs[0]),source_v=float(vs[1]),source_w=float(vs[2]),column_u=float(vc[0]),column_v=float(vc[1]),column_w=float(vc[2]),free_column_voxels=len(free),column_horizontal_wind_std=float(np.std(wind[free,y,x,:2].astype(np.float64),axis=0).sum())))
    sourcefield.append(s);columnfield.append(c)
assert native_max==0
csvwrite(H/'SOURCE_PLANE_input.csv',sourcefield);csvwrite(H/'COLUMN_FREE_UNIFORM_MEAN_input.csv',columnfield);csvwrite(H/'HEIGHT_WIND_FIELDS.csv',profiles)
capture=dict(contract_SHA256=sha(p),actual_fields=[dict(name=n,SHA256=sha(H/(n+'_input.csv'))) for n in ['SOURCE_PLANE','COLUMN_FREE_UNIFORM_MEAN']],
 raw_wind10_SHA256=sha(rawpath),native_sensor_plane_u_v_max_abs_difference=native_max,source_plane_free_cells=447,column_fields_candidate_independent=True)
(H/'HEIGHT_INPUT_FIELD_QUALIFICATION.json').write_text(json.dumps(capture,indent=2)+'\n',encoding='utf-8')
print(json.dumps(capture,indent=2))
