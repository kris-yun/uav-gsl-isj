from common import *
import numpy as np,yaml,io
from PIL import Image
meta=yaml.safe_load((OUT/'official/scenarios/E/_occupancy.yaml').read_text());im=np.flipud(np.asarray(Image.open(OUT/'official/scenarios/E/_occupancy.pgm')))
prob=1-im.astype(float)/255
raw=np.where(prob>meta['occupied_thresh'],100,np.where(prob<meta['free_thresh'],0,-1))
a=f'{raw.shape[1]} {raw.shape[0]} {meta["resolution"]} {meta["origin"][0]} {meta["origin"][1]}\n'+' '.join(map(str,raw.ravel().tolist()))
files={'native_map_check.cpp':(ROOT/'work/pmfs_e3/native_map_check.cpp').read_bytes(),'RAW_NAV_MAP.txt':a.encode()}
code=r'''
import subprocess,math,struct,hashlib,shutil,numpy as np
assert json.loads((t/'PREPROCESSING_RESULT.json').read_text())['exit_code']==0
build=json.loads(Path('/home/zyc/pmfs_native_capture_r4_20261009/BUILD_CONTEXT.json').read_text())
# Only compile a new entry point; linked official map functions and core stay unchanged.
cmd=['/usr/bin/c++',*build['compileflags'],str(t/'native_map_check.cpp'),'-o',str(t/'native_map_check'),'-Wl,--gc-sections',*build['link_tail']]
(t/'MAP_CHECK_BUILD_COMMAND.json').write_text(json.dumps(cmd,indent=2))
with (t/'map_check_build.log').open('w') as f:q=subprocess.run(cmd,stdout=f,stderr=f,timeout=60)
assert q.returncode==0,'Map entry compile error: '+(t/'map_check_build.log').read_text()[-2500:]
with (t/'map_check.log').open('w') as f:q=subprocess.run(['bash','-lc','source /opt/ros/humble/setup.bash; '+str(t/'native_map_check')+' '+str(t/'RAW_NAV_MAP.txt')+' '+str(t/'NATIVE_2D_SUPPORT.json')],stdout=f,stderr=f,timeout=30)
assert q.returncode==0,'Native source support failed'
support=json.loads((t/'NATIVE_2D_SUPPORT.json').read_text())
lines=(t/'derived_E3/OccupancyGrid3D.csv').read_text().splitlines()
minimum=list(map(float,lines[0].split()[1:]));maximum=list(map(float,lines[1].split()[1:]));dims=list(map(int,lines[2].split()[1:]));step=float(lines[3].split()[1]);ijk=((np.array([-4,-1.9,.7],dtype=np.float32)-np.array(minimum,dtype=np.float32))/np.float32(step)).astype(int).tolist()
assert all(0<=i<n for i,n in zip(ijk,dims)) and abs(step-.1)<1e-7
planes=[];rows=[]
for line in lines[4:]:
 if line.strip()==';':
  if rows:planes.append(rows);rows=[]
 elif line.strip():rows.append(list(map(int,line.split())))
if rows:planes.append(rows)
occ=np.array(planes,dtype=np.int32)
assert occ.shape==(dims[2],dims[0],dims[1]) and set(np.unique(occ)).issubset({0,1,2})
state=int(occ[ijk[2],ijk[0],ijk[1]])
assert state==0,'STOP official release voxel occupied; no source or map correction allowed'
assert np.all(np.isfinite(minimum+maximum)) and np.all(np.array(maximum)>minimum)
binary=list((t/'preprocess_inputs/wind/W1/wind_at_cell_centers').glob('wind_iteration_*'));assert len(binary)==1
b=binary[0].read_bytes();header=struct.unpack_from('<Q',b)[0];v=np.frombuffer(b,offset=8,dtype='<f4').reshape(-1,3)
assert len(v)==np.prod(dims) and np.isfinite(v).all()
w=t/'derived_E3/wind';w.mkdir(exist_ok=True);shutil.copyfile(binary[0],w/binary[0].name)
raw=np.loadtxt(t/'official_E3/scenarios/E/wind_simulations/W1/wind_at_cell_centers_0.csv',delimiter=',',skiprows=1)
# CFD columns in supplied file are U,V,W,x,y,z; inspect column header before using indices.
head=(t/'official_E3/scenarios/E/wind_simulations/W1/wind_at_cell_centers_0.csv').open().readline().strip()
columns=head.replace('"','').split(',')
xyzcols=[next(i for i,n in enumerate(columns) if n.strip().lower() in [key,'points:'+str(k),'points_'+str(k)]) for k,key in enumerate(['x','y','z'])] if all(any(n.strip().lower() in [key,'points:'+str(k),'points_'+str(k)] for n in columns) for k,key in enumerate(['x','y','z'])) else [3,4,5]
xyz=raw[:,xyzcols];uvwcols=[i for i in range(6) if i not in xyzcols];expected=raw[:,uvwcols]
assert raw.shape[1]==6 and np.isfinite(raw).all()
ind=((xyz.astype(np.float32)-np.array(minimum,dtype=np.float32))/np.float32(step)).astype(int)
inside=np.all((ind>=0)&(ind<dims),axis=1);assert inside.all()
flat=ind[:,0]+ind[:,1]*dims[0]+ind[:,2]*dims[0]*dims[1]
reference=np.zeros(v.shape,dtype=np.float32)
for i,vec in zip(flat,expected):reference[i]=vec
delta=np.max(np.abs(v-reference));assert delta<1e-7,('wind registration mismatch',head,delta)
for n,h in json.loads((t/'OFFICIAL_ASSETS_BEFORE.json').read_text()).items():assert hashlib.sha256((t/n).read_bytes()).hexdigest()==h
g=dict(verdict='PASS',source_xyz=[-4,-1.9,.7],source_indices=ijk,source_state=state,free_enum=0,grid_minimum=minimum,grid_maximum=maximum,grid_dimensions=dims,cell_size=step,voxel_counts={str(int(x)):int((occ==x).sum()) for x in np.unique(occ)},wind_header_integer=header,wind_vector_count=len(v),wind_raw_header=head,CFD_rows=len(raw),wind_registration_max_abs_error=float(delta),finite=True,wind_frames=1,wind_time_class='STATIC',native_2D=support,official_assets_unchanged=True,preprocessing_executions=1,gas_generation_executions=0,native_goals=0)
(t/'GATE1.json').write_text(json.dumps(g,indent=2));print(json.dumps(g))
'''
print(put(files,code,'GATE1',60))
