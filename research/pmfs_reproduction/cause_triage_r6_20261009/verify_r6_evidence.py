"""Read-only R6 verification. Python 3, numpy, Pillow. No ROS or simulation.
Run: python verify_r6_evidence.py [extracted_package_directory]
"""
from pathlib import Path
import csv, hashlib, json, struct, sys, zlib
import numpy as np
from PIL import Image

p=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
def js(name):return json.loads((p/name).read_text(encoding='utf-8'))
e=js('SOURCE_SUPPORT_EVIDENCE.json');m=js('inputs/R5_update/metadata.json')
a=js('inputs/R5_update/native_map_CDR.json')
b=bytes.fromhex(a['cdr_hex'])[4:];pos=0
def read(fmt):
    global pos
    size=struct.calcsize(fmt);alignment=min(size,8)
    pos=(pos+alignment-1)//alignment*alignment
    result=struct.unpack_from('<'+fmt,b,pos)[0];pos+=size;return result
read('i');read('I');length=read('I');pos+=length
read('i');read('I');resolution=read('f');width,height=read('I'),read('I')
origin=[read('d') for _ in range(3)];quaternion=[read('d') for _ in range(4)]
length=read('I');raw=np.frombuffer(b[pos:pos+length],dtype='i1').reshape(height,width)
assert quaternion==[0,0,0,1] and length==width*height
official=np.array(Image.open(p/'inputs/official/C/_occupancy.pgm'))
official_ros=np.flipud(np.where(official>255*.9,0,np.where(official<255*.1,100,-1))).astype('i1')
assert np.array_equal(raw,official_ros)
assert np.array_equal(raw,np.load(p/'inputs/native_ROS_map.npy',allow_pickle=False))
source=np.array([0.,-1.,.2]);i,j=((source[:2]-np.array([m['origin_x'],m['origin_y']]))/m['cell_size']).astype(int)
assert [int(i),int(j)]==[21,25]
with (p/'inputs/R5_update/input.csv').open() as f:rows=list(csv.DictReader(f))
mask=np.array([int(q['occupancy']) for q in rows],dtype='u1').reshape(m['height'],m['width'])
posterior=np.frombuffer((p/'inputs/R5_update/posterior.f64').read_bytes(),dtype='<f8').reshape(mask.shape)
assert mask[j,i]==0 and posterior[j,i]==0 and np.all(raw[j*25:(j+1)*25,i*25:(i+1)*25]==100)
coarse=np.all(raw[:m['height']*25,:m['width']*25].reshape(m['height'],25,m['width'],25)==0,axis=(1,3))
assert coarse.sum()==531 and mask.sum()==518 and not coarse[j,i]
free=np.argwhere(mask==1)[:,::-1];mins=np.array([m['origin_x'],m['origin_y']])+free*m['cell_size']
centers=mins+.5*m['cell_size']
assert abs(np.linalg.norm(centers-source[:2],axis=1).min()-e['nearest_free_center_distance_m'])<1e-12
distance=np.maximum(np.maximum(mins-source[:2],source[:2]-mins-m['cell_size']),0)
assert abs(np.linalg.norm(distance,axis=1).min()-e['nearest_continuous_free_support_distance_m'])<1e-12
lines=(p/'inputs/existing_house02/OccupancyGrid3D.csv').read_text().splitlines()
minimum=np.array(list(map(float,lines[0].split()[1:])))
dimensions=list(map(int,lines[2].split()[1:]));step=float(lines[3].split()[1])
cells=np.empty((dimensions[2],dimensions[0],dimensions[1]),dtype='u1');z=x=0
for line in lines[4:]:
    if line.strip()==';':z+=1;x=0;continue
    if not line.strip():continue
    values=np.fromstring(line,dtype='u1',sep=' ');assert len(values)==dimensions[1]
    cells[z,x]=values;x+=1
assert np.array_equal(cells,np.load(p/'inputs/existing_3D_cells.npy',allow_pickle=False))
ix,iy,iz=np.floor((source-minimum)/step).astype(int)
assert cells[iz,ix,iy]==0
parts=(p/'inputs/existing_house02/occupancy.pgm').read_text().split()
assert parts[0]=='P2';ow,oh,maximum=map(int,parts[1:4]);old=np.array(parts[4:],dtype='u1').reshape(oh,ow)
oldfree=np.flipud(old==maximum)
assert np.array_equal(oldfree,np.repeat(np.repeat((cells[3]==0).T,10,axis=0),10,axis=1))
layer=js('MAP_HEIGHT_REPRESENTATION_EVIDENCE.json')
assert abs(np.mean((old==maximum)!=(official>255*.9))-layer['old_vs_official_pixel_difference_fraction'])<1e-12
wind_indices={}
for n in [0,22,24]:
    data=zlib.decompress((p/f'inputs/legacy_C1_header_samples/iteration_{n}').read_bytes())
    assert struct.unpack_from('<i',data)[0]==1
    assert struct.unpack_from('<3d',data,88)==(0,-1,.2) and struct.unpack_from('<i',data,112)[0]==10
    wind_indices[n]=struct.unpack_from('<i',data,132)[0]
assert wind_indices=={0:0,22:10,24:1}
with (p/'MEASUREMENT_AND_UPDATE_TIMELINE.csv').open(encoding='utf-8-sig') as f:stops=list(csv.DictReader(f))
assert len(stops)==9 and sum(int(q['number_of_blocks']) for q in stops)==45
for q in stops:
    k=int(q['iteration_counter_before']);expected=k>=5 and k%3==0
    assert (q['source_update_trigger']=='True')==expected
assert [int(q['stop_number']) for q in stops if q['source_update_trigger']=='True']==[7]
assert next(k for k in range(9,20) if k>=5 and k%3==0)+1==10
assert sum(int(q['positive_blocks']) for q in stops)==15
assert sum(int(q['positive_blocks']) for q in stops if q['entered_saved_source_update']=='True')==5
assert all(float(q['search_elapsed_last_approx_s'])+float(q['elapsed_uncertainty_s'])<300 for q in stops)
s=js('SCHEDULING_EVIDENCE.json')
assert abs(sum(float(q['navigation_before_s']) for q in stops)-s['navigation_before_nine_stops_sum_s'])<1e-8
assert s['source_update_end_ROS_s']>s['source_update_start_ROS_s']
audit=js('CORRECTION_BUILD_AND_PARAMETER_AUDIT.json');v=audit['parameter_values']
assert audit['build']['exit_code']==0 and audit['parameter_audit_result']['exit_code']==0
assert v['simulation_started'] is False and v['temperature']==298 and v['pressure']==1 and v['wind_time_step']==1
assert v['allow_looping'] is False and not audit['gas_result_directory_exists']
original=(p/'inputs/gaden_humble/filament_simulator.cpp').read_text(encoding='utf-8')
corrected=(p/'correction_source/filament_simulator.cpp').read_text(encoding='utf-8')
assert '.temperature = getParameter("wind_time_step", 298.0f)' in original
assert '.pressure = getParameter("wind_time_step", 1.0f)' in original
assert '.temperature = getParameter("temperature", 298.0f)' in corrected
assert '.pressure = getParameter("pressure", 1.0f)' in corrected
assert corrected.index('if (!contractAudit.empty())')<corrected.index('gaden::paths::TryCreateDirectory(params.saveDataDirectory)')
lineage=js('LEGACY_HEADER_SAMPLE_LINEAGE.json')
for q in lineage:assert hashlib.sha256((p/q['file']).read_bytes()).hexdigest()==q['sha256']
manifest=p/'SHA256_MANIFEST.json';verified=0
if manifest.exists():
    entries=js('SHA256_MANIFEST.json')
    files={q.relative_to(p).as_posix() for q in p.rglob('*') if q.is_file() and q.name!='SHA256_MANIFEST.json'}
    assert files==set(entries),'Extra or missing package members'
    for name,expected in entries.items():
        assert hashlib.sha256((p/name).read_bytes()).hexdigest()==expected,name
    verified=len(entries)
approved_generation_count=js('clean_C1/GENERATION_RESULT.json')['generation_executions'] if (p/'clean_C1/GENERATION_RESULT.json').exists() else 0
print(json.dumps(dict(verdict='R6_EVIDENCE_VERIFIED',official_map_exact=True,source_2D_excluded=True,
    source_3D_free=True,legacy_wind_loop_proved=wind_indices,source_updates=1,next_update_stop=10,
    ninth_stop_before_deadline=True,engineering_parameter_read_PASS=True,preparation_audit_no_simulation=True,approved_C1_generations=approved_generation_count,
    SHA256_members_verified=verified)))
