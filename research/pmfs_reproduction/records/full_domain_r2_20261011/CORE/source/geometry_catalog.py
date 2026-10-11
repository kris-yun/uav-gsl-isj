from common_r2 import *
import csv,math,numpy as np,importlib.util,collections,shutil
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
spec=importlib.util.spec_from_file_location('r2_geom_decode',R1/'source/portable/raw_decode.py');raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
occpath=R1RAW/'support/geometry/OccupancyGrid3D.csv';occ=raw.occupancy(occpath);grid=rows(R1/'native_inputs/inputs/DERIVED/input.csv');nav=np.array([r['occupancy']=='1' for r in grid]);meta=rows(R1/'native_inputs/inputs/DERIVED/metadata.csv')[0]
w=int(meta['width']);h=int(meta['height']);size=float(meta['cell_size']);origin=np.array([np.float32(meta['origin_x']),np.float32(meta['origin_y'])]);z=np.float32(-.5);legal=[];invalid=[]
for cell in np.flatnonzero(nav):
 i=int(cell)%w;j=int(cell)//w;lower=origin+np.array([i,j])*size;upper=lower+size;centre=(lower+upper)/2;p=np.array([*centre,z],np.float32)
 if raw.cell_state(p,occ,occ)==0:point=p;rule='legal_grid_centre'
 else:
  choices=[];vmin=np.floor((lower-occ['minimum'][:2])/occ['cell_size']).astype(int);vmax=np.floor((upper-occ['minimum'][:2])/occ['cell_size']).astype(int);k=int(np.trunc((z-occ['minimum'][2])/occ['cell_size']))
  for x in range(max(vmin[0],0),min(vmax[0]+1,int(occ['dimensions'][0]))):
   for y in range(max(vmin[1],0),min(vmax[1]+1,int(occ['dimensions'][1]))):
    if occ['data'][k,x,y]!=0:continue
    a=np.maximum(lower,occ['minimum'][:2]+np.array([x,y])*occ['cell_size']);b=np.minimum(upper,occ['minimum'][:2]+np.array([x+1,y+1])*occ['cell_size'])
    if (b-a<=2e-5).any():continue
    xy=np.clip(centre,a+1e-5,b-1e-5);q=np.array([*xy,z],np.float32)
    if raw.cell_state(q,occ,occ)==0:choices.append((float(np.sum((q[:2]-centre)**2)),x,y,q))
  if not choices:invalid.append(dict(cell=int(cell),i=i,j=j,reason='No3Dfreevolumeatfixedsourceheight'));continue
  point=min(choices,key=lambda t:t[:3])[3];rule='nearest_geometric_interior_of_free_voxel'
 legal.append(dict(atomic_id=f'S{int(cell):04d}',cell=int(cell),i=i,j=j,x=float(point[0]),y=float(point[1]),z=float(point[2]),grid_centre_x=float(centre[0]),grid_centre_y=float(centre[1]),representative_rule=rule,physical_free=True,area_m2=size*size))
wc(CORE/'geometry/ATOMIC_SOURCE_CATALOG.csv',legal);dump(CORE/'geometry/ILLEGAL_SOURCE_CELLS.json',invalid)
active=np.zeros(len(nav),bool);active[[r['cell'] for r in legal]]=True;np.save(CORE/'geometry/ACTIVE_SOURCE_SUPPORT.npy',active,allow_pickle=False)
coarse={}
bycell={r['cell']:r for r in legal}
for tile in range(3,15):
 buckets=collections.defaultdict(set)
 for r in legal:buckets[(r['i']//tile,r['j']//tile)].add(r['cell'])
 regions=[];cell_to=np.full(len(nav),-1,np.int32)
 for key,cells in sorted(buckets.items()):
  remaining=set(cells)
  while remaining:
   seen={min(remaining)};q=collections.deque(seen);remaining-=seen
   while q:
    c=q.popleft();i=c%w;j=c//w
    for nx,ny in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
     n=nx+ny*w
     if 0<=nx<w and 0<=ny<h and n in remaining:remaining.remove(n);seen.add(n);q.append(n)
   ids=sorted(seen);points=np.array([[bycell[c]['grid_centre_x'],bycell[c]['grid_centre_y']] for c in ids]);centroid=points.mean(0);representative=min(ids,key=lambda c:(float(np.sum((np.array([bycell[c]['grid_centre_x'],bycell[c]['grid_centre_y']])-centroid)**2)),c));r=bycell[representative];rid=len(regions);cell_to[ids]=rid
   regions.append(dict(source_id=f'R{rid:03d}',source_index=rid,representative_cell=representative,x=r['x'],y=r['y'],z=r['z'],cell_count=len(ids),area_m2=len(ids)*size*size,prior=len(ids)/len(legal),tile_x=key[0],tile_y=key[1],tile_size_cells=tile,representative_rule='nearest_legal_cell_centre_to_component_centroid_then_cellID',cells=ids))
 if len(regions)<=64:
  coarse[str(tile)]=regions;np.save(CORE/f'geometry/COARSE_TILE{tile}_CELL_TO_SOURCE.npy',cell_to,allow_pickle=False);dump(CORE/f'geometry/COARSE_TILE{tile}_SOURCE_CATALOG.json',regions)
dump(CORE/'geometry/CANDIDATE_MODES_PRECHECK.json',dict(ATOMIC_sources=len(legal),navigation_scoring_cells=int(nav.sum()),illegal_source_cells=invalid,COARSE_sources={k:len(v) for k,v in coarse.items()},source_height=-.5,source_truth_not_used=True,complete_coverage=True,not_all_scoring_cells_assumed_sources=True,geometry_SHA256=sha(occpath),nav_input_SHA256=sha(R1/'native_inputs/inputs/DERIVED/input.csv')))
print(json.dumps(load(CORE/'geometry/CANDIDATE_MODES_PRECHECK.json')))
