from pathlib import Path
import csv,hashlib,json,math,collections
from PIL import Image
R=Path(__file__).resolve().parent;OLD=R.parent/'PMFS_PAPER_FIRST_ROS_QUAL_20261017';OFF=OLD/'official_exact/Environment_config/PMFS'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
out=[];a=R/'analysis';a.mkdir(exist_ok=True)
for case,template in [('A2','PF24_A2_T02'),('B2','PF24_B2_Q01')]:
 meta=json.loads((OLD/'cases'/template/'CASE_META.json').read_text());nav=json.loads((OLD/'cases'/template/'runtime/NAVIGATION_MAP_METADATA.json').read_text())
 source=meta['source_xyz'];pgm=OFF/'scenarios'/case[0]/'_occupancy.pgm';im=Image.open(pgm);w,h=im.size
 raw=(OLD/'cases'/template/'runtime/navigation_map.s8').read_bytes()
 expected=bytes(0 if im.getpixel((x,h-1-y))>229 else 100 if im.getpixel((x,h-1-y))<26 else 255 for y in range(h)for x in range(w))
 assert expected==raw
 x=int((source[0]-nav['origin_x'])/nav['resolution']);y=int((source[1]-nav['origin_y'])/nav['resolution'])
 row=dict(case=case,official_source_xyz=source,nav_origin=[nav['origin_x'],nav['origin_y']],resolution=nav['resolution'],width=w,height=h,actual_map_equals_official_PGM=True,official_PGM_sha256=sha(pgm),runtime_map_sha256=sha(OLD/'cases'/template/'runtime/navigation_map.s8'),fine_source_xy=[x,y],fine_source_occupancy=raw[x+y*w],source_config_sha256=sha(OFF/'scenarios'/case[0]/'simulations'/f'{case}.yaml'),xy_swapped_occupancy=raw[y+x*w]if y<w and x<h else None,missing_yflip_occupancy=raw[x+(h-1-y)*w])
 probs=list(csv.DictReader((OLD/'cases'/template/'runtime/native_posterior_updates.csv').open()));first=[p for p in probs if p['update']=='1'];nearest=min(first,key=lambda p:math.hypot(float(p['x_m'])-source[0],float(p['y_m'])-source[1]))
 row['nearest_legal_coarse_center']={k:nearest[k]for k in ['row','col','x_m','y_m']};row['nearest_legal_coarse_distance_m']=math.hypot(float(nearest['x_m'])-source[0],float(nearest['y_m'])-source[1])
 if case=='B2':
  occ=R.parent/'NATIVE_PMFS_FULL20_20261014/derived/5d9684e340a6/OccupancyGrid3D.csv';lines=occ.read_text().splitlines();minimum=list(map(float,lines[0].split()[1:]));dims=list(map(int,lines[2].split()[1:]));step=float(lines[3].split()[1]);layers=[];current=[]
  for line in lines[4:]:
   if line.strip()==';':layers.append(current);current=[]
   else:current.append(list(map(int,line.split())))
  assert len(layers)==dims[2]and all(len(g)==dims[0]and all(len(c)==dims[1]for c in g)for g in layers)
  ix,iy,iz=[int((v-o)/step)for v,o in zip(source,minimum)]
  row['gas_world_3D_source_indices']=[ix,iy,iz];row['gas_world_3D_source_occupancy']=layers[iz][ix][iy];row['gas_world_3D_occupancy_sha256']=sha(occ)
  row['same_xy_height_column']=[dict(z_cell=k,z_min=minimum[2]+step*k,z_max=minimum[2]+step*(k+1),state=g[ix][iy])for k,g in enumerate(layers)]
  row['interpretation']='3D release legality and 2D navigation/source-support legality are different tests; source and map are unchanged.'
 out.append(row)
put(a/'OFFICIAL_SOURCE_MAP_AUDIT.json',out)
clock=[dict(component='PMFS',paper='Paper gives variance declaration, not an exact ROS clock configuration',official='main_simbot_launch.py use_sim_time=False; Algorithm::startTime=node->now(); stop window0.4',runtime='Unchanged false/system-clock seconds'),dict(component='BasicSim',paper='Accelerated clock factor not recovered from manuscript',official='deltaTime0.1 speed5.0; currentTime=speed*(now-startTime)',runtime='5x slope confirmed from recorded /clock'),dict(component='PID/anemometer',paper='Local robot sensor inputs',official='use_sim_time=True; historical C++ main loops use rclcpp::Rate wall default clock',runtime='Stamped in robot clock; measured10Hz/20Hz wall'),dict(component='GADEN player',paper='Generated physical plume snapshots, original raw worlds/seeds unavailable',official='player_freq2Hz, node now() wall; initial A2=200 and exclusive100..199 loop; B2=500 nonloop',runtime='Existing disclosed public_clock_player maps actual files onto0.5wall-second cadence; no generated world'),dict(component='search time comparison',paper='30-trial means, Fig11 A2~87s B2~110.5s',official='PMFS saved search_t uses native node clock',runtime='Report native wall time and robot duration separately. Multiplying/dividing by5 does not recover author experimental semantics.')]
put(a/'CLOCK_ALIGNMENT_AUDIT.json',clock)
print(json.dumps([dict(case=x['case'],source_2D=x['fine_source_occupancy'],source_3D=x.get('gas_world_3D_source_occupancy'),nearest_legal_distance=x['nearest_legal_coarse_distance_m'])for x in out]))
