#!/usr/bin/env python3
"""CG-PC-CTT V4 final research reference.

Three-module runtime core used to constrain the C++ implementation:
M1 supplies source x transport-member probabilities at completed physical stops.
M2 performs strict leave-one-physical-stop-out source-vs-context validation.
M3 applies a minimum KL/I-projection correction to native PMFS.

No source truth, House id, seed-specific threshold, temperature or blend weight is an input.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import numpy as np

K_CAL = 4
K_SCORE = 4

def frequency_floor(timesteps: int) -> float:
    if timesteps <= 0:
        raise ValueError("timesteps must be positive")
    return 0.5 / (float(timesteps) + 1.0)

def _norm(q, name="mass"):
    q = np.asarray(q, dtype=float)
    if q.ndim != 1 or np.any(q < 0) or not np.all(np.isfinite(q)) or q.sum() <= 0:
        raise ValueError(f"invalid {name}")
    total = float(q.sum())
    if abs(total - 1.0) <= 8.0 * np.finfo(float).eps:
        return q.copy()
    return q / total

def _numzero(*xs):
    scale = 1.0
    for x in xs:
        a = np.asarray(x, dtype=float)
        if a.size:
            scale += float(np.max(np.abs(a)))
    return 128.0 * np.finfo(float).eps * scale

def _logmeanexp(x):
    x = np.asarray(x, dtype=float)
    m = np.max(x)
    return float(m + np.log(np.mean(np.exp(x - m))))

def _weighted_lse(logv, w):
    logv = np.asarray(logv, dtype=float); w = np.asarray(w, dtype=float)
    keep = w > 0; logv, w = logv[keep], w[keep]
    if len(logv) == 0:
        raise ValueError("empty weighted lse")
    w = w / w.sum(); m = np.max(logv)
    return float(m + np.log(np.sum(w * np.exp(logv - m))))

@dataclass
class StopBank:
    p: np.ndarray
    r: np.ndarray
    stop_id: np.ndarray
    block_count: np.ndarray
    max_prediction_drift: float

@dataclass
class StableState:
    q_causal: np.ndarray
    last_mask: np.ndarray | None = None
    consumed: set[str] = field(default_factory=set)
    def clone(self):
        return StableState(self.q_causal.copy(), None if self.last_mask is None else self.last_mask.copy(), set(self.consumed))

@dataclass
class M2Decision:
    accepted: bool
    reason: str
    selected_component: int | None
    selected_mask: np.ndarray | None
    informative_heldout: int
    heldout_context_gain: np.ndarray | None
    heldout_rival_margin: np.ndarray | None
    best_sets: tuple[tuple[int, ...], ...]

def collapse_blocks_to_stops(probability, hit, physical_stop_id, drift_tol=1e-12) -> StopBank:
    p = np.asarray(probability, dtype=float); y = np.asarray(hit, dtype=float); sid = np.asarray(physical_stop_id)
    if p.ndim != 3 or p.shape[2] != len(y) or len(y) != len(sid): raise ValueError("shape mismatch")
    if np.any((y < 0) | (y > 1)): raise ValueError("hit outside [0,1]")
    if p.shape[1] < K_CAL + K_SCORE: raise ValueError("need at least 8 keyed members")
    outp=[]; outr=[]; outid=[]; outn=[]; seen=set(); maxdrift=0.0; start=0; E=len(y)
    for e in range(1, E+1):
        if e == E or sid[e] != sid[start]:
            key = sid[start].item() if hasattr(sid[start], "item") else sid[start]
            if key in seen: raise ValueError("physical stop replay/noncontiguous id")
            seen.add(key); idx=np.arange(start,e); ref=p[:,:,idx[0]][:,:,None]
            drift=float(np.max(np.abs(p[:,:,idx]-ref))); maxdrift=max(maxdrift,drift)
            if drift > drift_tol: raise ValueError("within-stop forward prediction drift")
            outp.append(np.mean(p[:,:,idx],axis=2)); outr.append(float(np.mean(y[idx]))); outid.append(key); outn.append(len(idx)); start=e
    return StopBank(np.stack(outp,axis=2),np.asarray(outr),np.asarray(outid),np.asarray(outn),maxdrift)

def source_member_stop_logscore(stop_p, stop_r, timesteps, scoring_members=None):
    p=np.asarray(stop_p,dtype=float); r=np.asarray(stop_r,dtype=float)
    if scoring_members is None: scoring_members=list(range(K_CAL,K_CAL+K_SCORE))
    eps=frequency_floor(timesteps); pp=np.clip(p[:,scoring_members,:],eps,1.0-eps)
    return r[None,None,:]*np.log(pp)+(1.0-r[None,None,:])*np.log1p(-pp)

def coherent_source_score(member_stop_logscore, stops):
    a=np.asarray(member_stop_logscore,dtype=float); stops=np.asarray(stops,dtype=int); out=np.empty(a.shape[0])
    for s in range(a.shape[0]): out[s]=_logmeanexp(np.sum(a[s,:,stops],axis=1))
    return out

def single_stop_source_score(member_stop_logscore,h):
    a=np.asarray(member_stop_logscore,dtype=float)
    return np.asarray([_logmeanexp(a[s,:,h]) for s in range(a.shape[0])])

def components_from_labels(labels):
    lab=np.asarray(labels,dtype=int); vals=sorted(np.unique(lab).tolist())
    return [np.flatnonzero(lab==v) for v in vals], vals

def strict_loso_m2(stop_p, stop_r, component_labels, geometry_prior, timesteps, scoring_members=None, min_informative=2) -> M2Decision:
    p=np.asarray(stop_p,dtype=float); J=p.shape[2]
    if J<3: return M2Decision(False,"NEED_3_PHYSICAL_STOPS",None,None,0,None,None,tuple())
    q0=_norm(geometry_prior,"geometry prior"); comps,comp_values=components_from_labels(component_labels)
    if len(comps)<2: return M2Decision(False,"ONE_COMPONENT",None,None,0,None,None,tuple())
    a=source_member_stop_logscore(p,stop_r,timesteps,scoring_members); best_sets=[]
    for h in range(J):
        train=[j for j in range(J) if j!=h]; sscore=coherent_source_score(a,train)
        cscore=np.asarray([_weighted_lse(sscore[ix],q0[ix]) for ix in comps]); mx=np.max(cscore); tol=_numzero(cscore)
        best_sets.append(tuple(np.flatnonzero(cscore>=mx-tol).tolist()))
    common=set(best_sets[0])
    for bs in best_sets[1:]: common &= set(bs)
    if len(common)!=1: return M2Decision(False,"LOSO_COMPONENT_DISAGREE",None,None,0,None,None,tuple(best_sets))
    b=int(next(iter(common))); ctx_gain=[]; rival_margin=[]; informative=0
    for h in range(J):
        sh=single_stop_source_score(a,h); comp_h=np.asarray([_weighted_lse(sh[ix],q0[ix]) for ix in comps]); context_h=_weighted_lse(sh,q0)
        gain=float(comp_h[b]-context_h); rival=float(comp_h[b]-np.max(np.delete(comp_h,b))); tol=_numzero(comp_h,context_h)
        mask=np.asarray(component_labels)==comp_values[b]
        if rival < -tol: return M2Decision(False,"HELDOUT_RIVAL_CONTRADICTION",b,mask,informative,np.asarray(ctx_gain+[gain]),np.asarray(rival_margin+[rival]),tuple(best_sets))
        if gain <= tol: return M2Decision(False,"HELDOUT_CONTEXT_NULL_FAIL",b,mask,informative,np.asarray(ctx_gain+[gain]),np.asarray(rival_margin+[rival]),tuple(best_sets))
        if rival > tol: informative += 1
        ctx_gain.append(gain); rival_margin.append(rival)
    mask=np.asarray(component_labels)==comp_values[b]
    if informative<min_informative: return M2Decision(False,"INSUFFICIENT_INFORMATIVE_HELDOUT",b,mask,informative,np.asarray(ctx_gain),np.asarray(rival_margin),tuple(best_sets))
    return M2Decision(True,"ACCEPT",b,mask,informative,np.asarray(ctx_gain),np.asarray(rival_margin),tuple(best_sets))

def member_loo_robust(stop_p, stop_r, labels, q0, timesteps, reference_mask, min_informative=1):
    for removed in range(K_CAL,K_CAL+K_SCORE):
        members=[m for m in range(K_CAL,K_CAL+K_SCORE) if m!=removed]
        d=strict_loso_m2(stop_p,stop_r,labels,q0,timesteps,members,min_informative=min_informative)
        if d.accepted and not np.array_equal(d.selected_mask,reference_mask): return False
        if d.reason=="HELDOUT_RIVAL_CONTRADICTION": return False
    return True

def binary_causal_update(q_causal, stop_p, stop_r, selected_mask, timesteps):
    qc=_norm(q_causal,"causal state"); mask=np.asarray(selected_mask,dtype=bool); a=source_member_stop_logscore(stop_p,stop_r,timesteps)
    sscore=coherent_source_score(a,list(range(a.shape[2]))); inside=float(qc[mask].sum()); outside=1.0-inside
    if inside<=0 or outside<=0: raise ValueError("degenerate causal state")
    sb=_weighted_lse(sscore[mask],qc[mask]); so=_weighted_lse(sscore[~mask],qc[~mask]); inc=sb-so
    logodds=math.log(inside)-math.log(outside)+inc
    if logodds>=0: post=1.0/(1.0+math.exp(-min(logodds,700.0)))
    else:
        z=math.exp(max(logodds,-700.0)); post=z/(1.0+z)
    out=np.zeros_like(qc); out[mask]=qc[mask]/inside*post; out[~mask]=qc[~mask]/outside*(1.0-post)
    return out/out.sum(),float(inc)

def information_projection(native, mask, alpha, geometry_prior=None):
    qn=_norm(native,"native"); mask=np.asarray(mask,dtype=bool); beta=float(qn[mask].sum()); tol=_numzero(alpha,beta)
    if beta+tol>=alpha: return qn.copy(),False,beta
    if not (0<=alpha<=1): raise ValueError("alpha outside [0,1]")
    out=np.zeros_like(qn)
    if beta>0: out[mask]=alpha*qn[mask]/beta
    else:
        if geometry_prior is None: raise ValueError("geometry prior required for zero native support")
        q0=_norm(geometry_prior,"geometry prior"); out[mask]=alpha*q0[mask]/q0[mask].sum()
    obeta=1.0-beta
    if obeta>0: out[~mask]=(1.0-alpha)*qn[~mask]/obeta
    else:
        if geometry_prior is None: raise ValueError("geometry prior required for zero native complement")
        q0=_norm(geometry_prior,"geometry prior"); out[~mask]=(1.0-alpha)*q0[~mask]/q0[~mask].sum()
    return out/out.sum(),True,beta

def initialize_state(geometry_prior): return StableState(_norm(geometry_prior,"geometry prior"))

def apply_window(stop_p, stop_r, labels, q0, native_post, timesteps, state: StableState, window_id: str):
    if not window_id or window_id in state.consumed: raise ValueError("DUPLICATE_OR_EMPTY_WINDOW")
    st=state.clone(); st.consumed.add(window_id); d=strict_loso_m2(stop_p,stop_r,labels,q0,timesteps)
    if not d.accepted: return _norm(native_post),st,d,False,None,None
    if not member_loo_robust(stop_p,stop_r,labels,q0,timesteps,d.selected_mask):
        d.accepted=False; d.reason="SCORING_MEMBER_LOO_FAIL"; return _norm(native_post),st,d,False,None,None
    st.q_causal,_=binary_causal_update(st.q_causal,stop_p,stop_r,d.selected_mask,timesteps); st.last_mask=d.selected_mask.copy()
    alpha=float(st.q_causal[d.selected_mask].sum()); out,active,beta=information_projection(native_post,d.selected_mask,alpha,q0)
    return out,st,d,active,alpha,beta
