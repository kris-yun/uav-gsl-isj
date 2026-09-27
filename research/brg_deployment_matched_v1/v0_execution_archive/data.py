from __future__ import annotations
import json,heapq
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset
from .features import FeatureConfig,encode

def reachable_probe_distances(occ,meta,xy):
    nx=int(meta['width']);ny=int(meta['height']);step=float(meta['resolution'])
    free=np.asarray(occ).reshape(ny,nx)>0
    points=np.rint((xy-np.array([meta['origin_x'],meta['origin_y']]))/step-.5).astype(int)
    answer=np.full((len(points),len(points)),np.inf)
    for i,(x0,y0) in enumerate(points):
        if not(0<=x0<nx and 0<=y0<ny and free[y0,x0]):raise ValueError('probe not on free projection')
        ds={(x0,y0):0.};heap=[(0.,x0,y0)]
        while heap:
            d,x,y=heapq.heappop(heap)
            if d!=ds[(x,y)]:continue
            for a,b in [(1,0),(-1,0),(0,1),(0,-1)]:
                xx,yy=x+a,y+b
                if 0<=xx<nx and 0<=yy<ny and free[yy,xx]:
                    dd=d+step
                    if dd<ds.get((xx,yy),np.inf):ds[(xx,yy)]=dd;heapq.heappush(heap,(dd,xx,yy))
        for j,(xx,yy) in enumerate(points):answer[i,j]=ds.get((xx,yy),np.inf)
    return answer

def fixed_routes(dist,count,length,rng,max_leg_m=30.):
    """Geometry-only sparse sub-trajectories; not a closed-loop policy simulation."""
    routes=[]
    for r in range(count):
        current=int(rng.integers(len(dist)));path=[]
        for _ in range(length):
            path.append(current)
            legal=np.flatnonzero(np.isfinite(dist[current])&(dist[current]<=max_leg_m))
            fresh=np.array([i for i in legal if i not in path],dtype=int)
            choices=fresh if len(fresh) else legal
            current=int(rng.choice(choices))
        routes.append(path)
    return np.array(routes,dtype=int)

class OpenPaths(Dataset):
    def __init__(self,directory,split,route_count=8,seed=2026092701,feature_cfg=FeatureConfig()):
        if split not in {'train','dev'}:raise ValueError(split)
        self.items=[];self.groups=set();self.feature_cfg=feature_cfg; self.routes=[]
        for e in range(3):
            with np.load(Path(directory)/f'env_{e}_open.npz',allow_pickle=False) as z:
                yy=z['concentration'];xy=z['probe_xy'];sxy=z['source_xy'];p=z['p'];u=z['rawu'];meta=json.loads(z['metadata'].item())
                dist=reachable_probe_distances(z['occupancy'],meta,xy)
                truth_indices=z['truth_candidate_indices'] if 'truth_candidate_indices' in z else np.arange(6)
                if len(truth_indices)!=6 or np.any(truth_indices<0) or np.any(truth_indices>=len(sxy)):
                    raise ValueError('truth/support alignment')
            rng=np.random.default_rng(np.random.SeedSequence([seed,e,0 if split=='train' else 1]))
            routes=fixed_routes(dist,route_count,10,rng)
            self.routes.append(routes.tolist())
            reps=range(12) if split=='train' else range(12,16)
            for s in range(6):
                for r in reps:
                    group=f'{e}/{s}/{r}';self.groups.add(group)
                    for path in routes:
                        c=yy[s,r,np.arange(10),path]
                        obs,cue=encode(c,xy[path],sxy,p[path],u[path],feature_cfg)
                        self.items.append((obs,cue,int(truth_indices[s]),e,r,group))
    def __len__(self):return len(self.items)
    def __getitem__(self,i):
        o,c,s,e,r,g=self.items[i]
        return torch.from_numpy(o),torch.from_numpy(c),torch.tensor(s,dtype=torch.long)

class LoggedEpisodes(Dataset):
    """General sparse causal episodes collected by an existing OPEN harness.
    Each JSON line: bank_npz, split, plume_group, source_id, events.
    Every event: concentration_ppm,x,y,z,time_s. Labels live ONLY in this
    training file, not the sidecar protocol. Variable candidate counts supported
    with batch_size=1 in train.py. All augmentations of a plume share a split.
    """
    def __init__(self,path,split,feature_cfg=FeatureConfig()):
        from .bank import TemplateBank
        path=Path(path);rows=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        assignment={};self.items=[];self.groups=set();self.routes=[]
        for row in rows:
            key=row['plume_group'];part=row['split']
            if part not in {'train','dev'}:raise ValueError('only explicit OPEN train/dev episodes accepted')
            if key in assignment and assignment[key]!=part:raise ValueError('same plume across splits')
            assignment[key]=part
        cache={}
        for row in rows:
            if row['split']!=split:continue
            bp=(path.parent/row['bank_npz']).resolve()
            if bp not in cache:cache[bp]=TemplateBank.load(bp)
            b=cache[bp];ev=row['events']
            if not ev or len(ev)>128:raise ValueError('invalid episode length')
            times=[float(x['time_s']) for x in ev]
            if not np.isfinite(times).all() or np.any(np.diff(times)<=0):raise ValueError('bad event times')
            if any(abs(float(x['z'])-float(b.meta['height_m']))>1e-4 for x in ev):raise ValueError('height contract mismatch')
            xy=np.array([[x['x'],x['y']] for x in ev]);c=np.array([x['concentration_ppm'] for x in ev])
            p,u=b.project(xy,(b.meta['footprint_x_m'],b.meta['footprint_y_m']))
            obs,cue=encode(c,xy,b.xy,p,u,feature_cfg);truth=b.ids.index(row['source_id'])
            self.items.append((obs,cue,truth));self.groups.add(row['plume_group'])
        if not self.items:raise ValueError('empty split')
    def __len__(self):return len(self.items)
    def __getitem__(self,i):
        a,b,c=self.items[i];return torch.from_numpy(a),torch.from_numpy(b),torch.tensor(c,dtype=torch.long)
