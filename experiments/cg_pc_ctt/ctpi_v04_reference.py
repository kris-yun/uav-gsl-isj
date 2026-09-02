#!/usr/bin/env python3
"""CTPI V0.4 reference operators: CREL -> PSRG -> APRS.

PSRG local_resolution_scale is NOT a calibrated localization error bar.
APRS scores the current measured-hit field and must not double-assimilate the
same observation through native PMFS and APRS in one posterior update.
"""
from __future__ import annotations
import argparse, math
import numpy as np


def _clip_prob(p, finite_mc_n=None):
    p=np.asarray(p,float)
    eps=np.finfo(float).eps if finite_mc_n is None else 0.5/(finite_mc_n+1.0)
    return np.clip(p,eps,1.0-eps)


def crel_marginal(member_prob):
    x=np.asarray(member_prob,float)
    if x.ndim!=3 or x.shape[0]<1: raise ValueError("expected [member,source,observation]")
    if not np.all(np.isfinite(x)) or np.any((x<0)|(x>1)): raise ValueError("invalid probability")
    return x.mean(axis=0)


def fisher_rao_coordinate(prob):
    p=np.clip(np.asarray(prob,float),0.0,1.0)
    return 2.0*np.arcsin(np.sqrt(p))


def shared_edge_graph(rectangles):
    ids=list(rectangles); out={s:set() for s in ids}
    for ia,a in enumerate(ids):
        ax,ay,aw,ah=map(int,rectangles[a]); ax2,ay2=ax+aw,ay+ah
        for b in ids[ia+1:]:
            bx,by,bw,bh=map(int,rectangles[b]); bx2,by2=bx+bw,by+bh
            vertical=(ax2==bx or bx2==ax) and max(ay,by)<min(ay2,by2)
            horizontal=(ay2==by or by2==ay) and max(ax,bx)<min(ax2,bx2)
            if vertical or horizontal: out[a].add(b); out[b].add(a)
    return out


def psrg_pullback(member_prob, source_ids, source_xy, neighbor_graph):
    x=np.asarray(member_prob,float)
    if x.ndim!=3 or x.shape[1]!=len(source_ids): raise ValueError("shape mismatch")
    z=fisher_rao_coordinate(x).mean(axis=0)
    pos={s:i for i,s in enumerate(source_ids)}; result={}
    for sid in source_ids:
        i=pos[sid]; neigh=[n for n in neighbor_graph.get(sid,set()) if n in pos and n in source_xy]
        if len(neigh)<2: continue
        dx=np.asarray([[source_xy[n][0]-source_xy[sid][0],source_xy[n][1]-source_xy[sid][1]] for n in neigh],float)
        if np.linalg.matrix_rank(dx)<2: continue
        dy=np.asarray([z[pos[n]]-z[i] for n in neigh],float)
        B=np.linalg.lstsq(dx,dy,rcond=None)[0]
        resid=float(np.linalg.norm(dy-dx@B)/(np.linalg.norm(dy)+1e-15))
        J=B@B.T; vals,vecs=np.linalg.eigh(J); vals=np.maximum(vals,0.0)
        r=math.inf if vals[0]<=0 else 1.0/math.sqrt(float(vals[0]))
        result[sid]={"J":J,"eigenvalues":vals,"eigenvectors":vecs,"fit_residual":resid,"local_resolution_scale":r}
    return result


def aprs_log_score(member_prob, measured_hit_probability, confidence, finite_mc_n=200):
    p=_clip_prob(crel_marginal(member_prob),finite_mc_n)
    y=np.asarray(measured_hit_probability,float); w=np.asarray(confidence,float)
    if y.ndim!=1 or w.ndim!=1 or p.shape[1]!=y.size or y.size!=w.size: raise ValueError("observation mismatch")
    if np.any((y<0)|(y>1)) or np.any(w<0) or not np.all(np.isfinite(w)): raise ValueError("invalid observation")
    return np.sum(w[None,:]*(y[None,:]*np.log(p)+(1-y[None,:])*np.log(1-p)),axis=1)


def selftest(iterations=1000):
    rng=np.random.default_rng(20260902)
    for _ in range(iterations):
        y=rng.uniform(.05,.95,12); w=rng.uniform(.1,2,12)
        true=np.broadcast_to(y,(4,1,y.size)).copy()
        q=np.clip(y+rng.normal(0,.15,y.size),.01,.99); wrong=np.broadcast_to(q,(4,1,y.size)).copy()
        assert aprs_log_score(true,y,w)[0] >= aprs_log_score(wrong,y,w)[0]-1e-12
    x=rng.uniform(.01,.99,(4,5,10)); y=rng.uniform(0,1,10); w=rng.uniform(.1,1,10); mp=rng.permutation(4)
    np.testing.assert_allclose(crel_marginal(x),crel_marginal(x[mp]),rtol=0,atol=2e-15)
    np.testing.assert_allclose(aprs_log_score(x,y,w),aprs_log_score(x[mp],y,w),rtol=0,atol=1e-12)
    sp=rng.permutation(5); np.testing.assert_allclose(aprs_log_score(x[:,sp],y,w),aprs_log_score(x,y,w)[sp],atol=1e-12)
    ids=["a","b","c","d","e"]; xy={"a":(0.,0.),"b":(1.,0.),"c":(-1.,0.),"d":(0.,1.),"e":(0.,-1.)}
    rect={"a":(1,1,1,1),"b":(2,1,1,1),"c":(0,1,1,1),"d":(1,2,1,1),"e":(1,0,1,1)}; graph=shared_edge_graph(rect)
    obs=[]
    for sid in ids:
        sx,sy=xy[sid]; obs.append(np.array([.5+.08*sx,.5+.06*sy,.5+.04*(sx+sy),.5+.03*(sx-sy)]))
    z=np.repeat(np.asarray(obs)[None,:,:],4,axis=0); a=psrg_pullback(z,ids,xy,graph); b=psrg_pullback(z[mp],ids,xy,graph)
    assert "a" in a and np.isfinite(a["a"]["local_resolution_scale"]); np.testing.assert_allclose(a["a"]["J"],b["a"]["J"],atol=1e-12)
    print(f"CTPI_V04_REFERENCE_SELFTEST=PASS iterations={iterations}")


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--selftest",action="store_true"); ap.add_argument("--iterations",type=int,default=1000); a=ap.parse_args()
    if a.selftest: selftest(a.iterations)
    else: ap.error("run --selftest; see V0.4 VM runbook for integration")

if __name__=="__main__": main()
