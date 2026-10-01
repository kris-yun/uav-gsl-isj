"""Post-result independent geometric support check; no new forward/scoring."""
import csv,json,struct
from pathlib import Path
import numpy as np
root=Path('/mnt/hgfs/workspace');bank=root/'P3T_D0_CENTERS_20261001';inputs=root/'PMFS3D_R1_AUDIT_20261001/replay_inputs'
truths={'House01_seed0_off_off':'quadtree_23_16_1_1','House01_seed1_off_off':'quadtree_23_16_1_1','House02_seed0_off_off':'quadtree_16_21_5_1','House02_seed1_off_off':'quadtree_16_21_5_1'}
checks=[]
for name,truth in truths.items():
 cfg=list(csv.DictReader((inputs/name/'config.csv').open()))[0]
 cells=[r for r in csv.DictReader((inputs/name/'measured_hit_probability.csv').open()) if r['occupancy']=='Free' and float(r['confidence'])>0]
 queries=np.array([[float(r['x']),float(r['y']),float(cfg['sensor_z'])] for r in cells],np.float32)
 lines=Path(cfg['occupancy3d']).read_text().splitlines();origin=np.array([float(v) for v in lines[0].split()[1:]]);dims=tuple(int(v) for v in lines[2].split()[1:]);cell=float(lines[3].split()[1]);planes=[];plane=[]
 for line in lines[4:]:
  if line==';':
   if plane:planes.append(plane);plane=[]
  elif line.strip():plane.append([int(v) for v in line.split()])
 if plane:planes.append(plane)
 volume=np.array(planes)
 def isfree(p):
  ij=np.floor((p.astype(float)-origin)/cell).astype(int)
  return bool(np.all(ij>=0) and np.all(ij<dims) and volume[ij[2],ij[0],ij[1]]==0)
 def los(q,p):
  if not isfree(q) or not isfree(p):return False
  v=p-q;distance=np.float32(np.sqrt(np.sum(v*v,dtype=np.float32)));steps=int(distance/np.float32(cell))
  if steps<=1:return True
  v/=distance;increment=np.float32(distance/steps)
  return all(isfree(q+v*np.float32(increment*j)) for j in range(1,steps))
 for arm in ['oracle2d','oracle3d']:
  raw=(bank/name/arm/'trajectories'/f'{truth}.trajbin').read_bytes();offset=0;minimum=float('inf');counts=0;total=0;maxage=0;visible=0
  for t in range(200):
   n=struct.unpack_from('<I',raw,offset)[0];offset+=4
   fil=np.ndarray((n,),dtype=np.dtype([('pos','<f4',3),('age','<f8')]),buffer=raw,offset=offset);offset+=n*20;total+=n
   if n:
    sigma=np.sqrt(100+15*fil['age'])/100;maxage=max(maxage,float(fil['age'].max()))
    delta=queries[:,None,:].astype(float)-fil['pos'][None,:,:].astype(float)
    ratio=np.sqrt(np.sum(delta*delta,axis=2))/sigma[None,:]
    minimum=min(minimum,float(ratio.min()));counts+=int(np.count_nonzero(ratio<3))
    for qi,fi in zip(*np.nonzero(ratio<3)):visible+=int(los(queries[qi],fil['pos'][fi]))
  assert offset==len(raw)
  assert visible==0,'saved zero concentrations contradicted by independent geometric query'
  checks.append(dict(case=name,arm=arm,truth_leaf=truth,confident_cells=len(cells),confident_queries_in_fine_3d_free_space=sum(isfree(q) for q in queries),total_recorded_centers=total,maximum_filament_age_seconds=maxage,minimum_query_center_distance_in_sigma=minimum,query_center_pairs_within_3sigma=counts,pairs_passing_historical_cutoff_and_los=visible,all_confident_queries_outside_physical_cutoff=counts==0,equivalent_dense_volume_float32_bytes=int(np.prod(dims))*4))
(root/'P3T_D0_GAUSSIAN_OUTPUT_20261001/TRUTH_GEOMETRIC_SUPPORT_AUDIT.json').write_text(json.dumps(dict(checks=checks),indent=2,sort_keys=True)+'\n')
print(json.dumps(checks,indent=2))
