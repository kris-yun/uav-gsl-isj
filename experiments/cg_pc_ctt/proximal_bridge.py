#!/usr/bin/env python3
"""Minimal falsifiable proximal-bridge surrogate for CG-PC-CTT.

This is intentionally not a full neural model. It estimates a regularized
bridge h(R,Z(s)) for development screening and checks conditional moments.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class BridgeConfig:
    ridge: float = 1e-3
    interaction: bool = True

def _finite2(name, x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1: x = x[:, None]
    if x.ndim != 2 or not np.all(np.isfinite(x)):
        raise ValueError(f"{name} must be finite 2-D")
    return x

def bridge_design(R, Z, cfg):
    R, Z = _finite2("R", R), _finite2("Z", Z)
    if len(R) != len(Z): raise ValueError("R and Z length mismatch")
    blocks = [np.ones((len(R),1)), R, Z]
    if cfg.interaction:
        blocks.append(np.einsum("ni,nj->nij", R, Z).reshape(len(R), -1))
    return np.concatenate(blocks, axis=1)

class LinearProximalBridge:
    def __init__(self, cfg=BridgeConfig()):
        self.cfg = cfg; self.coef_ = None
    def fit(self, R, Z, Y):
        X, Y = bridge_design(R,Z,self.cfg), _finite2("Y",Y)
        if len(X) != len(Y): raise ValueError("X/Y length mismatch")
        reg = self.cfg.ridge*np.eye(X.shape[1]); reg[0,0]=0.0
        self.coef_ = np.linalg.solve(X.T@X + reg, X.T@Y)
        return self
    def predict(self, R, Z):
        if self.coef_ is None: raise RuntimeError("bridge not fitted")
        return bridge_design(R,Z,self.cfg) @ self.coef_
    def residual(self, R, Z, Y):
        return _finite2("Y",Y)-self.predict(R,Z)

def conditional_moment_score(residual, instruments):
    e, z = _finite2("residual",residual), _finite2("instruments",instruments)
    if len(e) != len(z): raise ValueError("length mismatch")
    z = np.concatenate([np.ones((len(z),1)),z],axis=1)
    es=np.std(e,axis=0,ddof=1); es=np.where(es>1e-12,es,1.0)
    zs=np.std(z,axis=0,ddof=1); zs=np.where(zs>1e-12,zs,1.0)
    moments=(z.T@e)/len(e)
    return float(np.mean(np.abs(moments/(zs[:,None]*es[None,:]))))

def candidate_squared_error_score(bridge, R_current, Z_candidates, Y_current):
    Zc=np.asarray(Z_candidates,dtype=np.float64)
    if Zc.ndim != 3: raise ValueError("Z_candidates must be [S,N,Dz]")
    R,Y=_finite2("R_current",R_current),_finite2("Y_current",Y_current)
    if Zc.shape[1] != len(R) or len(R) != len(Y): raise ValueError("sample mismatch")
    out=[]
    for s in range(Zc.shape[0]):
        pred=bridge.predict(R,Zc[s]); out.append(-float(np.mean((Y-pred)**2)))
    return np.asarray(out)
