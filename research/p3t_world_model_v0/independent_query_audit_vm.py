"""Source-blind independent brute-query check against saved Gaussian outputs."""
import csv,json,struct
from pathlib import Path
import numpy as np
bank=Path('/mnt/hgfs/workspace/P3T_D0_CENTERS_20261001')
inputs=Path('/mnt/hgfs/workspace/PMFS3D_R1_AUDIT_20261001/replay_inputs')
outputs=Path('/mnt/hgfs/workspace/P3T_D0_GAUSSIAN_OUTPUT_20261001/repeat1')
rows=lambda p:list(csv.DictReader(p.open()))
checks=[]
for case in sorted(inputs.glob('House*_off_off')):
 cfg=rows(case/'config.csv')[0];cells=rows(case/'measured_hit_probability.csv');leaf=sorted(rows(case/'active_candidates.csv'),key=lambda r:r['candidate_id'])[0]
 # Geometric query set near first lexical candidate; no truth/observed concentration selection.
 free=[r for r in cells if r['occupancy']=='Free']
 free.sort(key=lambda r:(abs(int(r['grid_i'])-int(leaf['origin_i']))+abs(int(r['grid_j'])-int(leaf['origin_j'])),int(r['cell_index'])))
 selected=free[:3]
 lines=Path(cfg['occupancy3d']).read_text().splitlines();origin=np.array([float(v) for v in lines[0].split()[1:]],float);dims=tuple(int(v) for v in lines[2].split()[1:]);cell=float(lines[3].split()[1])
 planes=[];plane=[]
 for line in lines[4:]:
  if line==';':
   if plane:planes.append(plane);plane=[]
  elif line.strip():plane.append([int(v) for v in line.split()])
 if plane:planes.append(plane)
 volume=np.array(planes);assert volume.shape==(dims[2],dims[0],dims[1])
 def isfree(p):
  ij=np.floor((p.astype(float)-origin)/cell).astype(int)
  return bool(np.all(ij>=0) and np.all(ij<dims) and volume[ij[2],ij[0],ij[1]]==0)
 def los(q,p):
  if not isfree(q) or not isfree(p):return False
  vec=p-q;distance=np.float32(np.sqrt(np.sum(vec*vec,dtype=np.float32)));steps=int(distance/np.float32(cell))
  if steps<=1:return True
  direction=vec/distance;increment=np.float32(distance/steps)
  return all(isfree(q+direction*np.float32(increment*j)) for j in range(1,steps))
 for arm,transport in [('g2','oracle2d'),('g3','oracle3d')]:
  cid=leaf['candidate_id'];raw=(bank/case.name/transport/'trajectories'/f'{cid}.trajbin').read_bytes();offset=0
  values=np.zeros((200,3),np.float32)
  # Recreate sensor query coordinates using the same Grid2D float center formula.
  queries=[np.array([np.float32(np.float32(cfg['origin_x'])+np.float32((int(r['grid_i'])+.5)*np.float32(cfg['cell']))),np.float32(np.float32(cfg['origin_y'])+np.float32((int(r['grid_j'])+.5)*np.float32(cfg['cell']))),np.float32(cfg['sensor_z'])],np.float32) for r in selected]
  for t in range(200):
   count=struct.unpack_from('<I',raw,offset)[0];offset+=4
   fil=np.ndarray((count,),dtype=np.dtype([('pos','<f4',3),('age','<f8')]),buffer=raw,offset=offset);offset+=count*20
   sigma=np.sqrt(100+15*fil['age']).astype(np.float32)
   for j,q in enumerate(queries):
    delta=fil['pos']-q;ds=np.sum(delta*delta,axis=1,dtype=np.float32);radius=sigma*3/100
    indices=np.flatnonzero(ds<radius*radius)
    c=np.float32(0)
    for i in indices:
     if los(q,fil['pos'][i]):
      # Independent normalized Gaussian density in cm, double precision, cast per contribution.
      density=(2*np.pi*float(sigma[i])**2)**(-1.5)*np.exp(-10000*float(ds[i])/(2*float(sigma[i])**2))
      c+=np.float32(1e6*6.440736978853164e-06/4.0894632701667424e-05*density)
    values[t,j]=c
  assert offset==len(raw)
  folder=outputs/case.name/arm;indices=[int(r['cell_index']) for r in selected]
  saved_mean=np.fromfile(folder/'concentration'/f'{cid}_mean.f32','<f4')[indices]
  saved_max=np.fromfile(folder/'concentration'/f'{cid}_max.f32','<f4')[indices]
  saved_hit=np.fromfile(folder/'maps'/f'{cid}.f32','<f4')[indices]
  calculated_mean=values.astype(float).mean(axis=0);calculated_max=values.max(axis=0);calculated_hit=(values>=.1).mean(axis=0).astype(np.float32)
  assert np.allclose(saved_mean,calculated_mean,rtol=2e-5,atol=1e-7)
  assert np.allclose(saved_max,calculated_max,rtol=2e-5,atol=1e-7)
  assert np.array_equal(saved_hit,calculated_hit)
  checks.append(dict(case=case.name,arm=arm,candidate_id=cid,query_cells=indices,source_blind=True,mean_absolute_error=float(np.max(abs(saved_mean-calculated_mean))),max_concentration_absolute_error=float(np.max(abs(saved_max-calculated_max))),hit_probability_exact=True,nonzero_query_count=int(np.count_nonzero(calculated_max)),minimum_threshold_distance=float(abs(values-.1).min())))
  print('INDEPENDENT_QUERY_PASS',case.name,arm,flush=True)
(outputs.parent/'INDEPENDENT_QUERY_AUDIT.json').write_text(json.dumps(dict(pass_=True,method='brute 200-timestep per-query Gaussian sum with independently parsed occupancy/LOS; no neighborhood bounding-box shortcut',checks=checks),indent=2,sort_keys=True)+'\n')
