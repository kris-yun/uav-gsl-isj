from pathlib import Path
import io,collections,hashlib
import numpy as np
from PIL import Image

def sha(b):return hashlib.sha256(b).hexdigest()
def source_support(pgm,meta,source,scale=25,start=None):
    image=np.asarray(Image.open(io.BytesIO(pgm)))
    tokens=[]
    stream=io.BytesIO(pgm)
    while len(tokens)<4:
        line=stream.readline()
        if not line:raise ValueError('incomplete PGM header')
        tokens.extend(line.split(b'#',1)[0].split())
    maximum=int(tokens[3])
    ratio=image.astype(float)/maximum
    if meta.get('negate',0):ratio=1-ratio
    prob=1-ratio
    raw=np.flipud(np.where(prob>meta['occupied_thresh'],100,np.where(prob<meta['free_thresh'],0,-1)))
    h,w=raw.shape;ch,cw=h//scale,w//scale
    free=np.all(raw[:ch*scale,:cw*scale].reshape(ch,scale,cw,scale)==0,axis=(1,3))
    step=float(np.float32(meta['resolution'])*scale);origin=np.array(meta['origin'][:2]);xy=np.array(source[:2])
    ij=np.floor((xy-origin)/step).astype(int);fi=np.floor((xy-origin)/meta['resolution']).astype(int)
    legal=free.copy()
    if start is not None:
        si=np.floor((np.array(start[:2])-origin)/step).astype(int)
        todo=collections.deque([tuple(si)]);visited=set()
        while todo:
            x,y=todo.popleft()
            if (x,y) in visited:continue
            visited.add((x,y))
            for xx in range(max(0,x-1),min(cw,x+2)):
                for yy in range(max(0,y-1),min(ch,y+2)):
                    if free[yy,xx] and (xx,yy) not in visited:todo.append((xx,yy))
        for y,x in np.argwhere(free):legal[y,x]=(int(x),int(y)) in visited
    ci=0<=ij[0]<cw and 0<=ij[1]<ch;fine=0<=fi[0]<w and 0<=fi[1]<h
    centers=origin+(np.argwhere(legal)[:,::-1]+.5)*step
    coarse=bool(free[ij[1],ij[0]]) if ci else False
    return dict(source_indices=ij.tolist(),source_fine_occupancy=int(raw[fi[1],fi[0]]) if fine else None,
        source_coarse_free=coarse,source_supported=(bool(legal[ij[1],ij[0]]) if ci else False) if start is not None else (None if coarse else False),
        start_provided=start is not None,candidate_cell_size_m=step,num_free_before_prune=int(free.sum()),
        num_free_after_prune=int(legal.sum()) if start is not None else None,
        nearest_legal_center_distance_m=float(np.linalg.norm(centers-xy,axis=1).min()) if len(centers) else None)

def occupancy3d(path,source):
    lines=Path(path).read_text().splitlines()
    minimum=np.array(list(map(float,lines[0].split()[1:])))
    dims=list(map(int,lines[2].split()[1:]));step=float(lines[3].split()[1]);ijk=np.floor((np.array(source)-minimum)/step).astype(int)
    if not all(0<=ijk[k]<dims[k] for k in range(3)):
        return dict(source_indices=ijk.tolist(),source_state=None,source_free=False,dimensions=dims,minimum=minimum.tolist(),cell_size=step)
    z=x=0;state=None
    for line in lines[4:]:
        if line.strip()==';':z+=1;x=0;continue
        if not line.strip():continue
        if z==ijk[2] and x==ijk[0]:state=int(line.split()[ijk[1]]);break
        x+=1
    return dict(source_indices=ijk.tolist(),source_state=state,source_free=state==0,
        dimensions=dims,minimum=minimum.tolist(),cell_size=step,free_enum=0,
        qualification='Point occupancy only; original preprocessing/mesh/version lineage must also match the release contract')
