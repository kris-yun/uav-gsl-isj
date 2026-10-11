import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,hashlib,importlib.util,struct
import numpy as np
W=Path(__file__).resolve().parent;B=W.parents[1]
M2=B/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
M1=B/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
O=B/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010'
D=O/'domain_support_intervention';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def writecsv(p,rs):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
contract=dict(
 reason='Existing 3D paths occupy physically free voxels above native planar navigation obstacles. Point, wall slide and height slice interventions did not remove wrong preference. Test gas transport domain restriction directly.',
 adaptive_exploratory_stage=True,
 primary_intervention='Only the gas movement free-space/visibility domain is extended to candidate-independent union of existing 3D free columns. Candidate generation, measured probability, confidence, scoring cells and Gaussian readout mask remain native.',
 observable_rule='Set non-native-navigation-free hit map cells to zero before native normalization/blur. Normalize native free cells with unchanged record steps. Never blur raw unnormalised off-navigation counts.',
 wind_rule='Complete the predeclared free-column uniform mean field for all native XY cells. Old navigation-free u/v exactly match completed height experiment. Old-mask baseline never visits extended cells; new entries therefore do not change its used transition kernel.',
 source_form='Exact two point sources, oracle diagnostic only',wall_rule='native rollback',
 sources={'C7':[-3.2,-3.3],'K2':[-1.675,1.495]},RNG_bundles=['T','W'],
 reuse_baseline='Four existing COLUMN_FREE_UNIFORM_MEAN point/native-wall forwards',
 maximum_scientific_forward_calls=4,maximum_parity_calls=2,maximum_total_new_calls=6,
 forward_wall_s=60,forward_RSS_bytes=536870912,build_wall_s=180,build_RSS_bytes=1610612736,
 new_GADEN=0,new_CFD=0,new_ROS=0,new_navigation=0,new_seed=0,
 decision='Report all four contrasts and ratio, path residence in non-navigation support and first divergence. No additional parameter, source or mask selection after results.',
 limitation='Column union is a transport-support upper bound, may connect disjoint free layers and is not self-consistent 3D physics, a new deployed model, or a localization performance result. A flip would implicate this restricted-domain intervention under these two saved RNG bundles, not prove sole cause.')
p=D/'DOMAIN_SUPPORT_FROZEN_CONTRACT.json';p.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'DOMAIN_SUPPORT_PRE_COMPUTE_SHA256.txt').write_text(sha(p)+'  '+p.name+'\n',encoding='ascii')
sp=importlib.util.spec_from_file_location('raw',M2/'independent_raw_query_verify/verify_raw_receiver_queries.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
occ=r.occupancy(M2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv');nx,ny,nz=occ['dimensions']
wp=M2/'frozen_B4_inputs/derived_B4/wind/wind_iteration_10';raw=wp.read_bytes();assert struct.unpack('<ii',raw[:8])==(3,0)
wind=np.frombuffer(raw,dtype='<f4',offset=8).reshape(nz,ny,nx,3)
inp=rows(M1/'snapshot/input.csv');old=rows(O/'height_intervention/COLUMN_FREE_UNIFORM_MEAN_input.csv')
meta=rows(M1/'snapshot/metadata.csv')[0];cs=np.float32(float(meta['cell_size']));origin=np.array([float(meta['origin_x']),float(meta['origin_y'])],np.float32)
field=[];mask=[];changed=0;freecount=0
for row,oldrow in zip(inp,old):
    i=int(row['cell_index']);point=np.array([origin[0]+(int(row['grid_i'])+.5)*cs,origin[1]+(int(row['grid_j'])+.5)*cs],dtype=np.float32)
    xy=np.trunc((point-occ['minimum'][:2])/occ['cell_size']).astype(int);x,y=xy
    valid=0<=x<nx and 0<=y<ny
    zs=np.flatnonzero(occ['data'][:,x,y]==0) if valid else np.array([],dtype=int)
    gasfree=bool(len(zs));freecount+=gasfree
    q=dict(oldrow)
    if gasfree:
        vc=wind[zs,y,x].astype(np.float64).mean(axis=0).astype(np.float32)
        if row['occupancy']=='1':
            assert np.float32(float(oldrow['u']))==vc[0] and np.float32(float(oldrow['v']))==vc[1]
        else:q['u']=repr(float(vc[0]));q['v']=repr(float(vc[1]));changed+=1
    assert all(q[k]==oldrow[k] for k in q if k not in ['u','v'])
    assert row['occupancy']!='1' or gasfree
    field.append(q);mask.append(dict(cell_index=i,grid_i=row['grid_i'],grid_j=row['grid_j'],native_navigation_free=int(row['occupancy']),gas_transport_free=int(gasfree),world_x=float(point[0]),world_y=float(point[1]),CFD_x=int(x),CFD_y=int(y),free_voxel_count=len(zs)))
writecsv(D/'COMPLETE_COLUMN_MEAN_input.csv',field);writecsv(D/'GAS_TRANSPORT_MASK.csv',mask)
qualification=dict(contract_SHA256=sha(p),input_SHA256=sha(D/'COMPLETE_COLUMN_MEAN_input.csv'),mask_SHA256=sha(D/'GAS_TRANSPORT_MASK.csv'),
 native_navigation_free=sum(x['occupancy']=='1' for x in inp),gas_transport_free=freecount,newly_allowed=freecount-sum(x['occupancy']=='1' for x in inp),
 old_free_wind_identical=True,nonwind_input_fields_identical=True,nonfree_wind_rows_completed=changed,
 occupancy_SHA256=sha(M2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv'),wind10_SHA256=sha(wp))
(D/'DOMAIN_INPUT_QUALIFICATION.json').write_text(json.dumps(qualification,indent=2)+'\n',encoding='utf-8')
print(json.dumps(qualification,indent=2))
