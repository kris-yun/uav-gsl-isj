"""Read-only, portable B2 source-support evidence for Pro. No new propagation."""
from pathlib import Path
import csv,hashlib,json,shutil,subprocess
import numpy as np
R=Path(__file__).resolve().parent
A=R.parent/'O24_MULTIWORLD_BASELINE_20261024'
O=R/'domain_audit';I=O/'inputs';I.mkdir(parents=True,exist_ok=True)
G=A/'PAPER_IDENTITY/official_history.git'
commit='a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533'
def sha(b):return hashlib.sha256(b).hexdigest()
def original(path):
 q=subprocess.run(['git','--git-dir='+str(G),'show',commit+':'+path],capture_output=True,check=True)
 return q.stdout
paths={'official_B_map.pgm':'Environment_config/PMFS/scenarios/B/_occupancy.pgm',
 'official_B_map.yaml':'Environment_config/PMFS/scenarios/B/_occupancy.yaml',
 'official_B2_simulation.yaml':'Environment_config/PMFS/scenarios/B/simulations/B2.yaml'}
for name,path in paths.items():(I/name).write_bytes(original(path))
source_proofs=[];excerpts=[]
for path,local,ranges in [
 ('gsl_server/src/gsl_server/algorithms/Common/Grid2D.hpp','src/gsl_server/algorithms/Common/Grid2D.hpp',[(91,125)]),
 ('gsl_server/src/gsl_server/algorithms/PMFS/PMFSLib.cpp','src/gsl_server/algorithms/PMFS/PMFSLib.cpp',[(195,242),(273,278)])]:
 b=original(path);f=R.parent/'PMFS_O24_FROZEN_CODE_PACKAGE_20261019/source_runtime'/local
 assert b==f.read_bytes(),path
 source_proofs.append(dict(path=path,author_commit=commit,sha256=sha(b),O24_file_byte_identical=True))
 lines=b.decode().splitlines()
 for low,high in ranges:
  excerpts.append(path+f' L{low}-L{high}\n'+'\n'.join(f'{j+1}: {lines[j]}'for j in range(low-1,min(high,len(lines)))))
(O/'OFFICIAL_SOURCE_RELEVANT_EXCERPTS.txt').write_text('\n\n'.join(excerpts)+'\n')
(O/'OFFICIAL_SOURCE_PARITY.json').write_text(json.dumps(source_proofs,indent=2)+'\n')
T=R/'cases/B2_R03/runtime'
for name in ['NAVIGATION_MAP_METADATA.json','navigation_map.s8','BASELINE_PARAMETER_GATE.json']:
 shutil.copyfile(T/name,I/name)
for name in ['WORLD_QUALIFICATION.json','OccupancyGrid3D.csv']:
 shutil.copyfile(A/'G0_AE/B2'/name,I/name)
shutil.copyfile(A/'PAPER_IDENTITY/LIVE_DEPENDENCY_AND_MAP_AUDIT/LIVE_DEPENDENCY_AND_MAP_VERDICT.json',I/'LIVE_DEPENDENCY_AND_MAP_VERDICT.json')
rows=list(csv.DictReader((T/'native_posterior_updates.csv').open()))
rows=[x for x in rows if x['update']==rows[0]['update']]
with(I/'B2_R03_FIRST_NATIVE_POSTERIOR.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
shutil.copyfile(__file__,O/'build_source_domain_handoff.py')
# This portable verifier reads only the bundled immutable files.
verifier='''from pathlib import Path
import csv,hashlib,json
import numpy as np
from PIL import Image
import yaml
R=Path(__file__).resolve().parent;I=R/'inputs'
m=json.loads((I/'NAVIGATION_MAP_METADATA.json').read_text())
y=yaml.safe_load((I/'official_B_map.yaml').read_text())
s=yaml.safe_load((I/'official_B2_simulation.yaml').read_text())
truth=np.array([s['source_x'],s['source_y'],s['source_z']],dtype='f8')
image=np.array(Image.open(I/'official_B_map.pgm'),dtype='f8')
occ=(255-image)/255
official=np.flipud(np.where(occ>y['occupied_thresh'],100,np.where(occ<y['free_thresh'],0,-1))).astype('i1')
fine=np.fromfile(I/'navigation_map.s8',dtype='i1').reshape(m['height'],m['width'])
assert official.shape==fine.shape and np.array_equal(official,fine)
res=np.float32(m['resolution']);origin=np.array([m['origin_x'],m['origin_y']],dtype='f4');cell=np.float32(res*25)
ny,nx=fine.shape[0]//25,fine.shape[1]//25
coarse=(fine[:ny*25,:nx*25].reshape(ny,25,nx,25)==0).all(axis=(1,3))
ci=((truth[:2]-origin.astype('f8'))/float(cell)).astype(int)
fi=((truth[:2]-origin.astype('f8'))/float(res)).astype(int)
block=fine[ci[1]*25:(ci[1]+1)*25,ci[0]*25:(ci[0]+1)*25]
lines=(I/'OccupancyGrid3D.csv').read_text().splitlines();lo=np.array(lines[0].split()[1:],dtype='f4');dims=np.array(lines[2].split()[1:],int);dx=np.float32(lines[3].split()[1])
parts=[v for v in '\\n'.join(lines[4:]).split(';')if v.strip()]
grid=np.stack([np.fromstring(v,sep=' ',dtype='i1').reshape(dims[0],dims[1]).T for v in parts])
gi=((truth.astype('f4')-lo)/dx).astype(int)
assert np.all(gi>=0) and np.all(gi<dims)
physical_state=int(grid[tuple(gi[::-1])])
assert physical_state==0 and int(fine[fi[1],fi[0]])==100 and not coarse[ci[1],ci[0]]
rows=list(csv.DictReader((I/'B2_R03_FIRST_NATIVE_POSTERIOR.csv').open()))
assert not any(int(x['col'])==ci[0] and int(x['row'])==ci[1] for x in rows)
nearest=min(rows,key=lambda x:(float(x['x_m'])-truth[0])**2+(float(x['y_m'])-truth[1])**2)
xy=[float(nearest['x_m']),float(nearest['y_m'])]
out=dict(status='PASS_REPRODUCED_OFFICIAL_MAP_SOURCE_SUPPORT_MISMATCH',source_xyz=truth.tolist(),physical_3D_source_voxel=gi.tolist(),physical_3D_source_state=physical_state,
 fine_pixel=fi.tolist(),fine_occupancy=int(fine[fi[1],fi[0]]),coarse_cell=ci.tolist(),block_free_pixels=int((block==0).sum()),block_occupied_pixels=int((block==100).sum()),
 actual_map_vs_official_different_pixels=int((fine!=official).sum()),source_cell_present_in_native_posterior=False,
 nearest_legal_native_center_xy=xy,nearest_legal_center_distance_m=float(np.linalg.norm(np.array(xy)-truth[:2])),
 native_navigation_map_sha256=hashlib.sha256(fine.tobytes()).hexdigest(),
 conclusion='Published a8 inputs and unchanged source-domain operations reproduce the exclusion. This alone does not explain the full localization error; the exact paper experimental commit remains unknown.',new_simulations=0)
(R/'SOURCE_DOMAIN_REPRODUCTION.json').write_text(json.dumps(out,indent=2)+'\\n')
print(json.dumps(out,indent=2))
'''
(O/'reproduce_domain_mismatch.py').write_text(verifier)
print(str(O))
