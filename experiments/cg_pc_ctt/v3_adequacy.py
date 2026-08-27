#!/usr/bin/env python3
"""Observation-adequacy diagnostics for CG-PC-CTT V3.

This module asks whether the actually observed response is supported by a
candidate/member predictive family. It is deliberately separate from
replicated source identifiability: members can agree strongly and still all be
wrong.

No acceptance threshold is defined here.
"""
from __future__ import annotations
import numpy as np


def candidate_predictive_adequacy(prediction: np.ndarray, observed: np.ndarray):
    """Scale-free adequacy diagnostics for one candidate.

    prediction: [M,E]
    observed:   [E]

    Returns:
      relative_center_distance:
        ||y-mu||^2 / mean_m ||z_m-mu||^2
      residual_in_member_span_fraction:
        fraction of residual energy lying in the empirical member-variation span
      nearest_member_relative_distance:
        min_m ||y-z_m||^2 / mean_{m<n} ||z_m-z_n||^2

    These are diagnostics only; calibration must be frozen on development data
    before any binary adequacy gate is claimed.
    """
    Z=np.asarray(prediction,dtype=np.float64)
    y=np.asarray(observed,dtype=np.float64).reshape(-1)
    if Z.ndim!=2 or Z.shape[1]!=len(y):
        raise ValueError("prediction must be [M,E] and observed [E]")
    if Z.shape[0]<2 or not np.all(np.isfinite(Z)) or not np.all(np.isfinite(y)):
        raise ValueError("need >=2 finite members and finite observed response")
    mu=Z.mean(axis=0)
    A=Z-mu
    r=y-mu
    spread=float(np.mean(np.sum(A*A,axis=1)))
    r2=float(r@r)
    scale=max(spread,np.finfo(float).tiny)
    relative_center=r2/scale

    _,s,Vt=np.linalg.svd(A,full_matrices=False)
    tol=max(A.shape)*np.finfo(float).eps*max(float(s[0]) if len(s) else 0.0,1.0)*100.0
    keep=s>tol
    if r2<=np.finfo(float).tiny:
        span_fraction=1.0
    elif np.any(keep):
        V=Vt[keep]
        proj=V.T@(V@r)
        span_fraction=float((proj@proj)/r2)
        span_fraction=float(np.clip(span_fraction,0.0,1.0))
    else:
        span_fraction=0.0

    pair=[]
    for m in range(len(Z)):
        for n in range(m+1,len(Z)):
            d=Z[m]-Z[n]; pair.append(float(d@d))
    pair_scale=max(float(np.mean(pair)),np.finfo(float).tiny)
    nearest=float(np.min(np.sum((Z-y[None,:])**2,axis=1)))/pair_scale

    return {
        "relative_center_distance":float(relative_center),
        "residual_in_member_span_fraction":span_fraction,
        "nearest_member_relative_distance":float(nearest),
        "member_span_rank":int(np.sum(keep)),
        "member_count":int(len(Z)),
        "observation_dimension":int(len(y)),
    }


def family_predictive_adequacy(predictions: np.ndarray, observed: np.ndarray):
    """Evaluate every candidate and summarize best-supported predictive family.

    predictions: [S,M,E]
    observed: [E]
    """
    P=np.asarray(predictions,dtype=np.float64)
    if P.ndim!=3:
        raise ValueError("predictions must be [S,M,E]")
    rows=[candidate_predictive_adequacy(P[s],observed) for s in range(P.shape[0])]
    rel=np.asarray([r["relative_center_distance"] for r in rows])
    near=np.asarray([r["nearest_member_relative_distance"] for r in rows])
    span=np.asarray([r["residual_in_member_span_fraction"] for r in rows])
    best=int(np.argmin(rel))
    return rows,{
        "best_candidate_by_relative_center_distance":best,
        "best_relative_center_distance":float(rel[best]),
        "best_nearest_member_relative_distance":float(np.min(near)),
        "max_residual_in_member_span_fraction":float(np.max(span)),
        "median_relative_center_distance":float(np.median(rel)),
    }
