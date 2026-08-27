#!/usr/bin/env python3
"""Bernoulli trajectory adequacy for PMFS candidate/member predictive responses.

For candidate s and transport member m, raw PMFS hit probabilities at actual
measurement events define a trajectory likelihood:
  log L_sm = sum_e [y_e log p_sme + (1-y_e) log(1-p_sme)].

Candidate ensemble support preserves member identity across events:
  log L_s = logmeanexp_m(log L_sm).

This is an observation-compatibility diagnostic, not a new source posterior.
No adequacy threshold is frozen here.
"""
from __future__ import annotations
import math
import numpy as np


def _logsumexp(x):
    x=np.asarray(x,dtype=np.float64)
    m=float(np.max(x))
    return m+math.log(float(np.sum(np.exp(x-m))))


def candidate_log_trajectory_support(probability: np.ndarray, observed_hit: np.ndarray,
                                     numerical_eps: float = 1e-12):
    P=np.asarray(probability,dtype=np.float64)
    y=np.asarray(observed_hit,dtype=np.float64).reshape(-1)
    if P.ndim!=2 or P.shape[1]!=len(y):
        raise ValueError("probability must be [M,E], observed_hit [E]")
    if not np.all(np.isfinite(P)) or np.any(P<0) or np.any(P>1):
        raise ValueError("probabilities must be finite in [0,1]")
    if not np.all((y==0)|(y==1)):
        raise ValueError("observed_hit must be binary")
    if len(y)<1 or P.shape[0]<2:
        raise ValueError("need >=1 event and >=2 members")
    p=np.clip(P,numerical_eps,1.0-numerical_eps)
    ll=np.sum(y[None,:]*np.log(p)+(1.0-y[None,:])*np.log1p(-p),axis=1)
    mix=_logsumexp(ll)-math.log(len(ll))
    return {
        "member_log_likelihood":ll,
        "ensemble_log_trajectory_likelihood":float(mix),
        "ensemble_log_trajectory_likelihood_per_event":float(mix/len(y)),
        "best_member_log_likelihood_per_event":float(np.max(ll)/len(y)),
        "worst_member_log_likelihood_per_event":float(np.min(ll)/len(y)),
        "events":int(len(y)),
        "members":int(len(ll)),
    }


def family_log_trajectory_support(probability: np.ndarray, observed_hit: np.ndarray):
    P=np.asarray(probability,dtype=np.float64)
    if P.ndim!=3:
        raise ValueError("probability must be [S,M,E]")
    rows=[candidate_log_trajectory_support(P[s],observed_hit) for s in range(P.shape[0])]
    score=np.asarray([r["ensemble_log_trajectory_likelihood_per_event"] for r in rows])
    best=int(np.argmax(score))
    return rows,{
        "best_candidate_idx":best,
        "best_ensemble_log_likelihood_per_event":float(score[best]),
        "median_candidate_log_likelihood_per_event":float(np.median(score)),
        "worst_candidate_log_likelihood_per_event":float(np.min(score)),
        "candidate_count":int(P.shape[0]),
        "member_count":int(P.shape[1]),
        "event_count":int(P.shape[2]),
    }
