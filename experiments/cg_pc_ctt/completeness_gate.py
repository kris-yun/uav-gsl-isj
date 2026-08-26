#!/usr/bin/env python3
"""Completeness/identifiability gate for CG-PC-CTT.

Input per decision context: phi[s,m,d], where s indexes source candidates,
m transport members, and d response features.

The gate does not invert a high-dimensional dxd covariance. It first projects
transport residuals into a pre-registered low-dimensional source-contrast
subspace, then whitens source contrast by transport uncertainty.

V1 freezes rank_k=3 by default, matching the historical four-source
observability screen (sigma_3/sigma_1). This avoids the degenerate mistake of
requiring all feature dimensions to be identifiable when using a dense
206-candidate source grid.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
import numpy as np

@dataclass(frozen=True)
class GateConfig:
    gamma_min: float = 0.05
    alpha_min: float = 1.0
    beta_min: Optional[float] = None
    ridge_rel: float = 1e-3
    eig_floor: float = 1e-9
    rank_k: int = 3
    def validate(self):
        if self.gamma_min < 0 or self.alpha_min < 0: raise ValueError('gate thresholds must be >=0')
        if self.beta_min is not None and self.beta_min < 0: raise ValueError('beta_min must be >=0')
        if self.ridge_rel < 0 or self.eig_floor <= 0: raise ValueError('invalid regularization')
        if self.rank_k < 1: raise ValueError('rank_k must be >=1')

@dataclass(frozen=True)
class GateResult:
    gamma: float; alpha: float; beta: float; sigma_max: float; sigma_min: float
    numerical_rank: int; target_rank: int; accepted: bool; reason: str; ridge: float
    def to_dict(self): return asdict(self)

def _as_finite_3d(phi):
    x=np.asarray(phi,dtype=np.float64)
    if x.ndim!=3: raise ValueError(f'phi must be [S,M,D], got {x.shape}')
    S,M,D=x.shape
    if S<2 or M<2 or D<1: raise ValueError(f'need S>=2,M>=2,D>=1, got {x.shape}')
    if not np.all(np.isfinite(x)): raise ValueError('phi contains NaN/Inf')
    return x

def compute_gate(phi, cfg=GateConfig()):
    cfg.validate(); x=_as_finite_3d(phi); S,M,D=x.shape
    target_rank=min(cfg.rank_k,S-1,D)
    mu=x.mean(axis=1); B=mu-mu.mean(axis=0,keepdims=True)
    _,sraw,vt=np.linalg.svd(B,full_matrices=False)
    if len(sraw)<target_rank or sraw[0]<=cfg.eig_floor:
        return GateResult(0.,0.,0.,0.,0.,0,target_rank,False,'NO_SOURCE_CONTRAST',cfg.eig_floor)
    Q=vt[:target_rank].T
    resid=x-mu[:,None,:]; R=resid.reshape(S*M,D)@Q
    C=(R.T@R)/max(R.shape[0]-1,1)
    scale=float(np.trace(C)/target_rank)
    ridge=max(cfg.eig_floor,cfg.ridge_rel*max(scale,cfg.eig_floor))
    evals,evecs=np.linalg.eigh(C+ridge*np.eye(target_rank)); evals=np.maximum(evals,cfg.eig_floor)
    Winv=(evecs*(1./np.sqrt(evals)))@evecs.T
    Bw=(B@Q)@Winv
    sw=np.linalg.svd(Bw,compute_uv=False)
    smax=float(sw[0]); smin=float(sw[target_rank-1])
    nrank=int(np.sum(sw>max(cfg.eig_floor,smax*1e-8)))
    gamma=float(smin/smax) if smax>cfg.eig_floor else 0.; alpha=smin
    beta=np.inf
    for i in range(S):
        for j in range(i+1,S): beta=min(beta,float(np.linalg.norm(Bw[i]-Bw[j])))
    if not np.isfinite(beta): beta=0.
    reasons=[]
    if nrank<target_rank: reasons.append('RANK')
    if gamma<cfg.gamma_min: reasons.append('GAMMA')
    if alpha<cfg.alpha_min: reasons.append('ALPHA')
    if cfg.beta_min is not None and beta<cfg.beta_min: reasons.append('BETA')
    accepted=not reasons
    return GateResult(gamma,alpha,beta,smax,smin,nrank,target_rank,accepted,'PASS' if accepted else '+'.join(reasons),ridge)

def no_update_posterior(previous_q):
    q=np.asarray(previous_q,dtype=np.float64)
    if q.ndim!=1 or q.size<2 or np.any(q<0) or not np.all(np.isfinite(q)): raise ValueError('invalid posterior')
    z=q.sum()
    if z<=0: raise ValueError('posterior must have positive mass')
    return (q/z).copy()
