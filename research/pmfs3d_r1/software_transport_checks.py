"""Synthetic transport checks only; no historical truth or R1 effect is read."""
import argparse
import csv
import json
import struct
import subprocess
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
cells=[]
for j in range(2):
    for i in range(2):
        cells.append(dict(cell_index=i+2*j,occupancy='Free',logOdds=0,confidence=0.5))
write_csv(a.out/'measured_hit_probability.csv',cells)
write_csv(a.out/'estimated_wind.csv',[dict(cell_index=i,wind_x=0,wind_y=0) for i in range(4)])
write_csv(a.out/'active_candidates.csv',[dict(candidate_id='quadtree_0_0_2_2',origin_i=0,origin_j=0,size_i=2,size_j=2)])
occ=a.out/'OccupancyGrid3D.csv'
occ.write_text('#env_min(m) 0 0 0\n#env_max(m) 0.6 0.6 2\n#num_cells 6 6 20\n#cell_size(m) 0.1\n'+(''.join(['0 0 0 0 0 0\n']*6)+';\n')*20)
wind=a.out/'synthetic,wind.csv'
base=dict(width=2,height=2,cell=0.3,origin_x=0,origin_y=0,update_id=5,native_rng_seed=0,
          source_z=0.25,sensor_z=0.25,dt=0.2,noise=0,record_steps=20,min_warmup=1,max_warmup=3,
          power=1,cfd_csv=str(wind),occupancy3d=str(occ),cfd_state_id=0)
def run(name,arm,source_z,sensor_z,w):
    wind.write_text('u,v,w,x,y,z\n0,0,'+str(w)+',0,0,0\n')
    cfg=base|dict(source_z=source_z,sensor_z=sensor_z)
    config=a.out/(name+'_config.csv');write_csv(config,[cfg])
    out=a.out/name
    subprocess.run([str(a.binary),str(a.out),str(config),arm,str(out)],check=True)
    raw=(out/'maps/quadtree_0_0_2_2.f32').read_bytes()
    return struct.unpack('<4f',raw)
native=run('native_static','native',0.25,0.25,0)
flat=run('oracle2d_static','oracle2d',0.25,0.25,0)
volume=run('oracle3d_static','oracle3d',0.25,0.25,0)
assert native==flat==volume,(native,flat,volume)
below=run('oracle3d_below_without_w','oracle3d',0.05,0.45,0)
up=run('oracle3d_upward_transport','oracle3d',0.05,0.45,1)
assert all(x==0 for x in below),below
assert any(x>0 for x in up),up
report=dict(zero_wind_embedded_2d_parity=True,vertical_transport_changes_sensor_plane_hits=True,
            quoted_comma_path_parsing=True,volume_text_axis_layout='x rows, y columns, z planes',
            native_hit=native,oracle2d_hit=flat,oracle3d_hit=volume,below_hit=below,upward_hit=up,
            historical_targets_read=False,scientific_gate_evaluated=False)
(a.out/'SOFTWARE_CHECKS.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report))
