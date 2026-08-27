#!/usr/bin/env python3
"""Resolution-cell projected reversible rank posterior for CG-PC-CTT V3.

This research posterior enforces the rule:
  evidence may not create finer source precision than the current
  observation-conditioned physical resolution partition supports.

A "component" is a resolution cell (connected component of unresolved local
physical edges), not a claim that every pair inside it has identical
statistical distributions.
"""
from __future__ import annotations
import math
from statistics import NormalDist
import numpy as np

ND=NormalDist()


def normal_mid_ranks(scores):
    x=np.asarray(scores,dtype=np.float64)
    n=len(x)
    if n<2 or not np.all(np.isfinite(x)):
        raise ValueError("scores must be finite with n>=2")
    order=np.argsort(-x,kind="mergesort")
    rank=np.empty(n,float)
    i=0
    while i<n:
        j=i+1; ref=x[order[i]]
        while j<n and np.isclose(x[order[j]],ref,rtol=1e-12,atol=1e-12):
            j+=1
        rank[order[i:j]]=(i+1+j)/2.0
        i=j
    p=1.0-(rank-.5)/n
    return np.asarray([ND.inv_cdf(float(v)) for v in p])


def validate_prior(q0,S):
    q=np.ones(S)/S if q0 is None else np.asarray(q0,dtype=np.float64)
    if q.shape!=(S,) or np.any(q<0) or not np.isfinite(q).all() or q.sum()<=0:
        raise ValueError("invalid q0")
    return q/q.sum()


def project_to_components(values, component_id, q0):
    """Project evidence to one value per current resolution cell.

    Projection uses the geometry/base prior q0 as the within-cell measure:
      v_C = sum_{s in C} q0_s v_s / sum_{s in C} q0_s.

    This prevents candidate-count or duplicate-ID weighting from defining
    unsupported precision.
    """
    v=np.asarray(values,dtype=np.float64)
    c=np.asarray(component_id)
    q=np.asarray(q0,dtype=np.float64)
    if v.ndim!=1 or c.shape!=v.shape or q.shape!=v.shape:
        raise ValueError("values/component_id/q0 shape mismatch")
    out=np.empty_like(v)
    for label in np.unique(c):
        idx=np.flatnonzero(c==label)
        mass=float(q[idx].sum())
        if mass<=0:
            raise ValueError(f"component {label} has zero prior mass")
        mean=float(np.sum(q[idx]*v[idx])/mass)
        out[idx]=mean
    return out


def posterior(events,current_component_id,q0=None):
    """Build reversible posterior from accepted event scores.

    Required event keys:
      candidate_id: stable common candidate order
      score: [S], higher is better
      accepted: bool
      component_id: [S] resolution partition at that event

    Final current_component_id [S] is applied again after cumulative evidence
    aggregation, so a later merge erases unsupported historical fine-scale
    distinctions while a later split only permits new evidence to distinguish
    the newly resolved candidates.
    """
    accepted=[e for e in events if bool(e["accepted"])]
    if not accepted:
        return None,{"released":False,"reason":"NO_ACCEPTED_EVENTS"}
    ids=list(accepted[0]["candidate_id"]); S=len(ids)
    prior=validate_prior(q0,S)
    current=np.asarray(current_component_id)
    if current.shape!=(S,):
        raise ValueError("current_component_id shape mismatch")

    folds=[[],[]]
    for k,e in enumerate(accepted):
        if list(e["candidate_id"])!=ids:
            raise ValueError("candidate order drift")
        comp=np.asarray(e["component_id"])
        if comp.shape!=(S,):
            raise ValueError("event component_id shape mismatch")
        z=normal_mid_ranks(e["score"])
        z=project_to_components(z,comp,prior)
        folds[k%2].append(z)

    if not folds[0] or not folds[1]:
        return None,{"released":False,"reason":"NEED_BOTH_FOLDS","accepted_events":len(accepted)}

    zf=[]; counts=[]
    for f in folds:
        A=np.sum(np.stack(f),axis=0)/math.sqrt(len(f))
        zf.append(normal_mid_ranks(A)); counts.append(len(f))
    g=(zf[0]+zf[1])/math.sqrt(2.0)

    # Binding resolution projection at current time.
    g=project_to_components(g,current,prior)
    logq=np.log(np.maximum(prior,1e-300))+g
    logq-=logq.max()
    q=np.exp(logq); q/=q.sum()
    return q,{
        "released":True,
        "accepted_events":len(accepted),
        "fold_counts":counts,
        "current_resolution_cells":int(len(np.unique(current))),
        "within_current_cell_evidence_equalized":True,
    }
