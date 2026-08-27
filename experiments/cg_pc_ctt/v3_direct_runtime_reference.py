#!/usr/bin/env python3
"""Reference runtime for V3 Observation-Resolved Reversible Update.

This is the executable mathematical contract for the direct closed-loop path.
It deliberately does NOT require the proximal bridge as a prerequisite.

Inputs
------
probability[S,M,E]
    Candidate x keyed transport member x causally available completed event
    hit probabilities. In PMFS this is the pre-Hellinger `rawProbabilities`.
observed_hit[E]
    Binary completed-block outcomes.
block_id[E]
    Stable completed-block IDs; parity defines the two reproducibility folds.
rect[S,4]
    Geometry-only persistent carrier rectangles (x0,y0,w,h) in map cells.
prior_mass[S]
    Fixed geometry/design prior mass; never the same-window native posterior.

Frozen structure
----------------
* first 4 members: resolution/calibration only;
* last 4 members: Bernoulli outcome scoring only;
* transport nuisance metric: full pair-difference covariance + pseudoinverse;
* unresolved physical-adjacency edges are joined into resolution cells;
* an edge is resolved only when cross-member strength and every leave-one-member
  replicate remain positive up to numerical tolerance;
* even and odd folds must each contain both hit and miss outcomes;
* candidate scores are projected to current resolution cells before rank fusion;
* posterior uses fixed prior * exp(tie-safe fold-consistent normal-rank evidence);
* no source truth, native same-window posterior, online p-value, temperature,
  blend weight, House-specific threshold, or proximal bridge is required.
"""
from __future__ import annotations
import math
from statistics import NormalDist
import numpy as np

ND=NormalDist()
EMPIRICAL_PROB_EPS=0.5/201.0  # 200-record native PMFS frequency resolution
CALIBRATION_MEMBERS=4


def _logmeanexp(x):
    x=np.asarray(x,dtype=np.float64)
    m=float(np.max(x))
    return m+math.log(float(np.mean(np.exp(x-m))))


def _normal_mid_ranks(scores):
    x=np.asarray(scores,dtype=np.float64)
    if x.ndim!=1 or len(x)<2 or not np.isfinite(x).all():
        raise ValueError('scores must be finite 1-D with n>=2')
    n=len(x); order=np.argsort(-x,kind='mergesort'); rank=np.empty(n,float)
    i=0
    while i<n:
        j=i+1
        while j<n and np.isclose(x[order[j]],x[order[i]],rtol=1e-12,atol=1e-12): j+=1
        rank[order[i:j]]=(i+1+j)/2.0
        i=j
    p=1.0-(rank-.5)/n
    return np.asarray([ND.inv_cdf(float(v)) for v in p],dtype=np.float64)


def _nuisance_precision(prob_cal):
    x=np.asarray(prob_cal,dtype=np.float64)
    if x.ndim!=3: raise ValueError('prob_cal must be [S,M,E]')
    S,M,E=x.shape
    if M<3: raise ValueError('need >=3 calibration members')
    cov=np.zeros((E,E),dtype=np.float64); n=0
    for m in range(M):
        for h in range(m+1,M):
            d=x[:,m]-x[:,h]
            cov += .5*(d.T@d); n += S
    cov/=float(max(n,1)); cov=.5*(cov+cov.T)
    val,vec=np.linalg.eigh(cov)
    lmax=max(float(np.max(val)),0.0)
    tol=max(E,1)*np.finfo(np.float64).eps*max(lmax,1.0)*100.0
    keep=val>tol; inv=np.zeros_like(val); inv[keep]=1.0/val[keep]
    precision=(vec*inv[None,:])@vec.T
    return .5*(precision+precision.T),val,float(tol)


def _pair_cross(d,precision):
    d=np.asarray(d,dtype=np.float64); M=len(d)
    if M<3: raise ValueError('need >=3 calibration members')
    total=d.sum(axis=0)
    self_term=sum(float(v@precision@v) for v in d)
    observed=(float(total@precision@total)-self_term)/float(M*(M-1))
    loo=[]
    for r in range(M):
        dd=np.delete(d,r,axis=0); mm=M-1; total=dd.sum(axis=0)
        self_term=sum(float(v@precision@v) for v in dd)
        loo.append((float(total@precision@total)-self_term)/float(mm*(mm-1)))
    return float(observed),float(min(loo))


def _rect_adjacent(a,b):
    ax0,ay0,aw,ah=map(int,a); bx0,by0,bw,bh=map(int,b)
    ax1,ay1=ax0+aw,ay0+ah; bx1,by1=bx0+bw,by0+bh
    # Closed physical rectangles touch or overlap. Persistent carriers form a
    # non-overlapping partition, so this is a geometry-only local adjacency.
    dx=max(bx0-ax1,ax0-bx1,0); dy=max(by0-ay1,ay0-by1,0)
    return dx==0 and dy==0


def _resolution_cells(prob_cal,rect):
    x=np.asarray(prob_cal,dtype=np.float64); rect=np.asarray(rect,dtype=int)
    S=x.shape[0]
    precision,eigenvalues,cov_tol=_nuisance_precision(x)
    parent=list(range(S))
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]; a=parent[a]
        return a
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    resolved=unresolved=0; min_loo=math.inf
    for i in range(S):
        for j in range(i+1,S):
            if not _rect_adjacent(rect[i],rect[j]): continue
            strength,loo=_pair_cross(x[i]-x[j],precision)
            min_loo=min(min_loo,loo)
            numerical_tol=64*np.finfo(np.float64).eps*(1.0+abs(strength)+abs(loo))
            if strength>numerical_tol and loo>numerical_tol:
                resolved+=1
            else:
                unresolved+=1; union(i,j)
    roots=[find(i) for i in range(S)]; labels={}
    component=np.asarray([labels.setdefault(r,len(labels)) for r in roots],dtype=int)
    return component,{
        'resolution_cells':int(len(np.unique(component))),
        'resolved_local_edges':int(resolved),
        'unresolved_local_edges':int(unresolved),
        'minimum_loo_cross_strength':None if not np.isfinite(min_loo) else float(min_loo),
        'nuisance_rank':int(np.sum(eigenvalues>cov_tol)),
        'nuisance_tolerance':float(cov_tol),
    }


def _project(values,component,prior):
    v=np.asarray(values,dtype=np.float64); c=np.asarray(component); q=np.asarray(prior,dtype=np.float64)
    out=np.empty_like(v)
    for label in np.unique(c):
        idx=np.flatnonzero(c==label); mass=float(q[idx].sum())
        if mass<=0: raise ValueError('resolution cell has zero prior mass')
        out[idx]=float(np.sum(q[idx]*v[idx])/mass)
    return out


def observation_resolved_posterior(probability,observed_hit,block_id,rect,prior_mass):
    P=np.asarray(probability,dtype=np.float64)
    y=np.asarray(observed_hit,dtype=int).reshape(-1)
    block=np.asarray(block_id,dtype=np.int64).reshape(-1)
    rect=np.asarray(rect,dtype=int)
    q0=np.asarray(prior_mass,dtype=np.float64).reshape(-1)
    if P.ndim!=3: raise ValueError('probability must be [S,M,E]')
    S,M,E=P.shape
    if M<8: raise ValueError('direct V3 contract requires >=8 keyed members')
    if len(y)!=E or len(block)!=E or rect.shape!=(S,4) or len(q0)!=S: raise ValueError('shape mismatch')
    if np.any(P<0)|np.any(P>1)|(~np.isfinite(P)).any(): raise ValueError('invalid probability')
    if not np.all((y==0)|(y==1)): raise ValueError('observed_hit must be binary')
    if np.any(q0<0) or not np.isfinite(q0).all() or q0.sum()<=0: raise ValueError('invalid prior')
    q0=q0/q0.sum()

    # Resolution is calibrated without using the scoring members or outcomes.
    component,resolution=_resolution_cells(P[:,:CALIBRATION_MEMBERS,:],rect)
    scoring=P[:,CALIBRATION_MEMBERS:,:]
    fold_z=[]; fold_meta=[]
    for parity in (0,1):
        idx=np.flatnonzero(block%2==parity)
        if len(idx)<2:
            return None,{'released':False,'reason':'NEED_BOTH_FOLDS','resolution':resolution}
        yy=y[idx]; hits=int(yy.sum())
        if hits==0 or hits==len(idx):
            return None,{'released':False,'reason':'NON_IDENTIFYING_FOLD','fold':parity,'resolution':resolution}
        score=np.empty(S,dtype=np.float64)
        for s in range(S):
            member_ll=[]
            for m in range(scoring.shape[1]):
                p=np.clip(scoring[s,m,idx],EMPIRICAL_PROB_EPS,1.0-EMPIRICAL_PROB_EPS)
                member_ll.append(float(np.sum(yy*np.log(p)+(1-yy)*np.log1p(-p))))
            score[s]=_logmeanexp(member_ll)
        score=_project(score,component,q0)
        fold_z.append(_normal_mid_ranks(score))
        fold_meta.append({'parity':parity,'events':int(len(idx)),'hits':hits})

    evidence=(fold_z[0]+fold_z[1])/math.sqrt(2.0)
    evidence=_project(evidence,component,q0)
    logq=np.log(np.maximum(q0,1e-300))+evidence; logq-=float(np.max(logq))
    q=np.exp(logq); q/=float(q.sum())
    return q,{
        'released':True,
        'contract':'CG_PC_CTT_V3_OBSERVATION_RESOLVED_REVERSIBLE_UPDATE_V1',
        'calibration_members':CALIBRATION_MEMBERS,
        'scoring_members':int(M-CALIBRATION_MEMBERS),
        'folds':fold_meta,
        'resolution':resolution,
        'component_id':component,
        'within_resolution_cell_evidence_equalized':True,
        'same_window_native_posterior_used':False,
        'source_truth_used':False,
        'proximal_bridge_required':False,
    }
