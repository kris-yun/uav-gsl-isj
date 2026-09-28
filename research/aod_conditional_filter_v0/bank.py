"""Model-generated template interface; never accepts target plume observations."""
from __future__ import annotations
import numpy as np
import json,hashlib
from pathlib import Path

class TemplateBank:
    def __init__(self, metadata, source_ids, source_xy, source_cells, p, rawu):
        self.meta=dict(metadata); self.ids=tuple(str(v) for v in source_ids)
        self.xy=np.asarray(source_xy,dtype='float64'); self.cells=np.asarray(source_cells,dtype='int64')
        self.p=np.asarray(p,dtype='float64'); self.u=np.asarray(rawu,dtype='float64')
        self.nx=int(self.meta['width']);self.ny=int(self.meta['height']);self.n=self.nx*self.ny
        self.dx=float(self.meta['resolution']);self.ox=float(self.meta['origin_x']);self.oy=float(self.meta['origin_y'])
        s=len(self.ids)
        if len(set(self.ids))!=s or len(set(self.cells.tolist()))!=s or s<2:raise ValueError('candidate identity is not unique')
        if self.xy.shape!=(s,2) or self.cells.shape!=(s,) or self.p.shape!=(s,self.n) or self.u.shape!=self.p.shape:
            raise ValueError('bank shape')
        if min(self.nx,self.ny,self.dx)<=0 or np.any(self.cells<0) or np.any(self.cells>=self.n):raise ValueError('bank grid')
        if not all(np.isfinite(a).all() for a in [self.xy,self.p,self.u]) or (self.u<0).any() or ((self.p<0)|(self.p>1)).any():raise ValueError('bank range')
        cellxy=np.stack((self.ox+(self.cells%self.nx+.5)*self.dx,self.oy+(self.cells//self.nx+.5)*self.dx),1)
        if not np.allclose(cellxy,self.xy,atol=2e-5,rtol=0):raise ValueError('source cell/coordinate mismatch')
        h=hashlib.sha256()
        h.update(json.dumps(self.meta,sort_keys=True,separators=(',',':')).encode());h.update('\n'.join(self.ids).encode())
        for a in (self.xy,self.cells,self.p,self.u): h.update(a.astype(a.dtype.newbyteorder('<'),copy=False).tobytes())
        self.fingerprint=h.hexdigest()

    def project(self, xy, footprint=(.2,.2)):
        xy=np.asarray(xy,dtype=float).reshape(-1,2); fw,fh=map(float,footprint)
        if min(fw,fh)<=0 or not np.isfinite(xy).all():raise ValueError('invalid footprint')
        left=self.ox+np.arange(self.nx)*self.dx;bottom=self.oy+np.arange(self.ny)*self.dx
        values_p=[];values_u=[]
        for x,y in xy:
            wx=np.maximum(0,np.minimum(left+self.dx,x+fw/2)-np.maximum(left,x-fw/2))
            wy=np.maximum(0,np.minimum(bottom+self.dx,y+fh/2)-np.maximum(bottom,y-fh/2))
            w=(wy[:,None]*wx[None,:]/(fw*fh)).ravel()
            if abs(w.sum()-1)>1e-8:raise ValueError('outside-map footprint; no support renormalization')
            ind=np.flatnonzero(w); ww=w[ind]
            values_p.append(self.p[:,ind]@ww);values_u.append(self.u[:,ind]@ww)
        projected_p=np.stack(values_p)
        # Floating overlap arithmetic can produce 1+4e-16 for an all-one field.
        # Reject real contract violations; correct only roundoff at physical bounds.
        if np.any(projected_p < -1e-12) or np.any(projected_p > 1+1e-12):
            raise ValueError('projected presence probability outside physical bounds')
        return np.clip(projected_p,0.,1.),np.stack(values_u)

    def planner_maps(self, q):
        q=np.asarray(q,dtype=float)
        if q.shape!=(len(self.ids),) or not np.isfinite(q).all() or (q<0).any() or abs(q.sum()-1)>1e-6:raise ValueError('invalid posterior')
        src=np.zeros(self.n);src[self.cells]=q
        mu=q@self.p
        # Native planner's population variance, not Bernoulli variance.
        variance=np.maximum(0,q@(self.p*self.p)-mu*mu)
        return src,variance

    def save(self,path):
        np.savez_compressed(path,metadata=np.array(json.dumps(self.meta,sort_keys=True)),source_ids=np.array(self.ids),source_xy=self.xy,source_cells=self.cells,p=self.p,rawu=self.u)
    @classmethod
    def load(cls,path):
        with np.load(path,allow_pickle=False) as a:
            return cls(json.loads(a['metadata'].item()),a['source_ids'],a['source_xy'],a['source_cells'],a['p'],a['rawu'])
