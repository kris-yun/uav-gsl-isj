from pathlib import Path
import subprocess,json,hashlib,io,collections,re
import numpy as np
import yaml
from PIL import Image

root=Path(__file__).resolve().parents[2]
out=root/'outputs/PMFS_OFFICIAL_SCENARIO_STATIC_QUALIFICATION_20261009'
out.mkdir(exist_ok=True)
repo=Path('D:/ZYC/A-gas/_reference_native_pmfs_upstream_20260923')
pin='4e141e162551e674f2f30ddb8859136c72139aac'
evidence=out/'evidence'
assets=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def official(n,save=True):
    b=subprocess.check_output(['git','-C',str(repo),'show',pin+':'+n])
    record=dict(provider='GSL_FIXED_GIT_OBJECT',repository=str(repo),revision=pin,path=n,bytes=len(b),sha256=sha(b))
    assets.append(record)
    if save:
        f=evidence/'official_pmfs'/n.removeprefix('Environment_config/PMFS/')
        f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
    return b
def map_support(image_bytes,meta,source,start,scale):
    arr=np.asarray(Image.open(io.BytesIO(image_bytes)))
    if arr.ndim!=2:raise ValueError('non-monochrome map')
    # ROS map_server trinary thresholds; image rows are flipped to map coordinates.
    q=arr.astype(float)/255
    if meta.get('negate',0):q=1-q
    prob=1-q
    raw=np.flipud(np.where(prob>meta['occupied_thresh'],100,np.where(prob<meta['free_thresh'],0,-1)))
    h,w=raw.shape;cw,ch=w//scale,h//scale
    free=np.all(raw[:ch*scale,:cw*scale].reshape(ch,scale,cw,scale)==0,axis=(1,3))
    origin=np.array(meta['origin'][:2]);step=float(np.float32(meta['resolution'])*scale)
    ij=np.floor((np.array(source[:2])-origin)/step).astype(int)
    si=np.floor((np.array(start[:2])-origin)/step).astype(int)
    visited=set();todo=collections.deque([tuple(si)])
    while todo:
        x,y=todo.popleft()
        if (x,y) in visited:continue
        visited.add((x,y))
        for xx in range(max(0,x-1),min(cw,x+2)):
            for yy in range(max(0,y-1),min(ch,y+2)):
                if free[yy,xx] and (xx,yy) not in visited:todo.append((xx,yy))
    inside=0<=ij[0]<cw and 0<=ij[1]<ch
    fi=np.floor((np.array(source[:2])-origin)/meta['resolution']).astype(int)
    fine_inside=0<=fi[0]<w and 0<=fi[1]<h
    legal=free.copy()
    for y,x in np.argwhere(free):legal[y,x]=(int(x),int(y)) in visited
    centers=origin+(np.argwhere(legal)[:,::-1]+.5)*step
    dist=np.linalg.norm(centers-np.array(source[:2]),axis=1)
    return dict(map_dimensions=[w,h],resolution_m=meta['resolution'],origin=meta['origin'],scale=scale,
        candidate_cell_size_m=step,coarse_dimensions=[cw,ch],source_indices=ij.tolist(),start_indices=si.tolist(),
        source_fine_occupancy=int(raw[fi[1],fi[0]]) if fine_inside else None,
        source_coarse_free=bool(free[ij[1],ij[0]]) if inside else False,
        source_supported=bool(legal[ij[1],ij[0]]) if inside else False,
        start_supported=bool(free[si[1],si[0]]) if 0<=si[0]<cw and 0<=si[1]<ch else False,
        num_free_before_prune=int(free.sum()),num_free_after_prune=int(legal.sum()),
        nearest_legal_center_distance_m=float(dist.min()) if len(dist) else None,
        method='Static reproduction of upstream trinary reduction and 8-neighbour reachable component; not an online map capture')

base='Environment_config/PMFS/'
launch=official(base+'launch/main_simbot_launch.py').decode()
for n in ['launch/gaden_player_launch.py','launch/gaden_sim_launch.py','navigation_config/simulation_base.py']:
    official(base+n)
paths=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','--name-only',pin,'--',base+'scenarios']).decode().splitlines()
rows=[];wind_groups={}
for scenario in 'ABCDE':
    prefix=base+'scenarios/'+scenario+'/'
    pgm=official(prefix+'_occupancy.pgm');meta=yaml.safe_load(official(prefix+'_occupancy.yaml'))
    gaden=yaml.safe_load(official(prefix+'params/gaden_params.yaml'))
    preproc=yaml.safe_load(official(prefix+'params/preproc_params.yaml'))
    for n in paths:
        if n.startswith(prefix+'cad_models/') and n.endswith('.stl'):
            b=official(n,False)
    for n in paths:
        if not n.startswith(prefix+'simulations/'):continue
        sim=yaml.safe_load(official(n));name=Path(n).stem
        basic=yaml.safe_load(official(prefix+'basicSim/'+name+'.yaml'))
        print(name,sim['source_x'],sim['source_y'],sim['source_z'],flush=True)
        source=[sim['source_'+q] for q in 'xyz']
        # Read official basicSim fields explicitly; no hand-picked start.
        rows.append(dict(id='PMFS_'+name,family='PMFS',scenario=scenario,simulation_id=name,source_xyz=source,
            simulation_config=n,gaden_params=prefix+'params/gaden_params.yaml',preproc_params=prefix+'params/preproc_params.yaml',
            map_config=prefix+'_occupancy.yaml',map_sha256=sha(pgm),simulation=sim,preproc=preproc,gaden=gaden,basic=basic,
            source_support=map_support(pgm,meta,source,basic['robots'][0]['position'],25),wind_prefix=prefix+'wind_simulations/'+sim['wind_sim_path']))
        wp=rows[-1]['wind_prefix']
        wind_groups[wp]=[x for x in paths if x.startswith(wp+'_') and x.endswith('.csv')]

(out/'OFFICIAL_PMFS_CONFIG_RAW.json').write_text(json.dumps(dict(rows=rows,wind_groups=wind_groups,launch=launch),indent=2),encoding='utf-8')
(out/'RAW_ASSET_HASHES.json').write_text(json.dumps(assets,indent=2),encoding='utf-8')
print(json.dumps(dict(PMFS_configs=len(rows),wind_groups=len(wind_groups),output=str(out))))
