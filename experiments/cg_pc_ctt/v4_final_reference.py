#!/usr/bin/env python3
"""CG-PC-CTT V4 scientific reference.

Three-module runtime core:
M1 constructs observation-resolved source components from calibration transport members.
M2 performs strict leave-one-physical-stop-out coherent posterior-predictive validation
   against both rival components and a source-independent Jeffreys-Beta null.
M3 applies minimum KL/I-projection correction to native PMFS only after acceptance.

No source truth, House id, seed-specific threshold, localization error, temperature,
blend weight, or outcome-fitted scientific threshold is an input.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import numpy as np

K_CAL = 4
K_SCORE = 4

def frequency_floor(timesteps: int) -> float:
    if int(timesteps) <= 0:
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
    if x.size == 0 or not np.all(np.isfinite(x)):
        raise ValueError("invalid logmeanexp input")
    m = np.max(x)
    return float(m + np.log(np.mean(np.exp(x - m))))

def _weighted_lse(logv, w):
    logv = np.asarray(logv, dtype=float)
    w = np.asarray(w, dtype=float)
    if logv.ndim != 1 or w.ndim != 1 or len(logv) != len(w):
        raise ValueError("weighted lse shape mismatch")
    keep = w > 0
    logv, w = logv[keep], w[keep]
    if len(logv) == 0 or not np.all(np.isfinite(logv)):
        raise ValueError("empty/invalid weighted lse")
    w = w / w.sum()
    m = np.max(logv)
    return float(m + np.log(np.sum(w * np.exp(logv - m))))

@dataclass
class StopBank:
    p: np.ndarray
    r: np.ndarray
    stop_id: np.ndarray
    block_count: np.ndarray
    max_prediction_drift: float

@dataclass
class ComponentBuild:
    labels: np.ndarray
    precision: np.ndarray
    c_tr: np.ndarray
    c_y: np.ndarray
    c_eff_eigenvalues: np.ndarray
    resolved_edges: tuple[tuple[int, int], ...]
    unresolved_edges: tuple[tuple[int, int], ...]

@dataclass
class StableState:
    q_causal: np.ndarray
    last_mask: np.ndarray | None = None
    consumed: set[str] = field(default_factory=set)
    def clone(self):
        return StableState(self.q_causal.copy(),
                           None if self.last_mask is None else self.last_mask.copy(),
                           set(self.consumed))

@dataclass
class M2Decision:
    accepted: bool
    reason: str
    selected_component: int | None
    selected_mask: np.ndarray | None
    informative_heldout: int
    heldout_absolute_gain: np.ndarray | None
    heldout_rival_margin: np.ndarray | None
    heldout_component_score: np.ndarray | None
    heldout_null_score: np.ndarray | None
    best_sets: tuple[tuple[int, ...], ...]
    @property
    def heldout_context_gain(self):
        # Backward-compatible alias. Semantics are now absolute source-null gain.
        return self.heldout_absolute_gain

def collapse_blocks_to_stops(probability, hit, physical_stop_id, drift_tol=1e-12) -> StopBank:
    p = np.asarray(probability, dtype=float)
    y = np.asarray(hit, dtype=float)
    sid = np.asarray(physical_stop_id)
    if p.ndim != 3 or p.shape[2] != len(y) or len(y) != len(sid):
        raise ValueError("shape mismatch")
    if not np.all(np.isfinite(p)) or not np.all(np.isfinite(y)):
        raise ValueError("nonfinite input")
    if np.any((y < 0) | (y > 1)):
        raise ValueError("hit outside [0,1]")
    if p.shape[1] < K_CAL + K_SCORE:
        raise ValueError("need at least 8 keyed members")
    outp=[]; outr=[]; outid=[]; outn=[]; seen=set(); maxdrift=0.0; start=0; E=len(y)
    for e in range(1, E+1):
        if e == E or sid[e] != sid[start]:
            key = sid[start].item() if hasattr(sid[start], "item") else sid[start]
            if key in seen:
                raise ValueError("physical stop replay/noncontiguous id")
            seen.add(key)
            idx=np.arange(start,e)
            ref=p[:,:,idx[0]][:,:,None]
            drift=float(np.max(np.abs(p[:,:,idx]-ref)))
            maxdrift=max(maxdrift,drift)
            if drift > drift_tol:
                raise ValueError("within-stop forward prediction drift")
            outp.append(np.mean(p[:,:,idx],axis=2))
            outr.append(float(np.mean(y[idx])))
            outid.append(key); outn.append(len(idx)); start=e
    return StopBank(np.stack(outp,axis=2),np.asarray(outr),np.asarray(outid),
                    np.asarray(outn),maxdrift)

def _adjacent_rect(a, b) -> bool:
    ax0, ay0, aw, ah = map(int, a); bx0, by0, bw, bh = map(int, b)
    ax1, ay1 = ax0+aw, ay0+ah; bx1, by1 = bx0+bw, by0+bh
    dx=max(bx0-ax1, ax0-bx1, 0); dy=max(by0-ay1, ay0-by1, 0)
    return dx == 0 and dy == 0

class _DSU:
    def __init__(self,n): self.p=list(range(n))
    def find(self,a):
        while self.p[a] != a:
            self.p[a]=self.p[self.p[a]]; a=self.p[a]
        return a
    def unite(self,a,b):
        a,b=self.find(a),self.find(b)
        if a!=b: self.p[b]=a

def effective_precision(stop_p, timesteps):
    """Finite stable-complement precision from calibration-member transport + sensor floor."""
    p=np.asarray(stop_p,dtype=float)
    if p.ndim!=3 or p.shape[1] < K_CAL or p.shape[2] < 1:
        raise ValueError("stop_p must be [S,M,J]")
    S,_,J=p.shape
    c_tr=np.zeros((J,J),dtype=float); count=0
    for s in range(S):
        for m in range(K_CAL):
            for n in range(m+1,K_CAL):
                d=p[s,m,:]-p[s,n,:]
                c_tr += 0.5*np.outer(d,d); count += 1
    c_tr /= float(max(count,1))
    c_tr=0.5*(c_tr+c_tr.T)
    eps=frequency_floor(timesteps)
    c_y=np.eye(J,dtype=float)*(0.25+eps*eps)
    c_eff=c_tr+c_y
    vals,vecs=np.linalg.eigh(0.5*(c_eff+c_eff.T))
    if not np.all(np.isfinite(vals)) or np.min(vals) <= 0:
        raise ValueError("non-positive effective covariance")
    precision=(vecs*(1.0/vals))@vecs.T
    precision=0.5*(precision+precision.T)
    return precision, vals, c_tr, c_y

def _pair_cross(difference, precision):
    d=np.asarray(difference,dtype=float)
    if d.ndim!=2: raise ValueError("difference must be [M,J]")
    def calc(mask):
        x=d[np.asarray(mask,dtype=bool)]
        mm=len(x)
        if mm<2: raise ValueError("need >=2 calibration members")
        total=x.sum(axis=0)
        self_term=sum(float(v@precision@v) for v in x)
        return (float(total@precision@total)-self_term)/float(mm*(mm-1))
    full=calc(np.ones(d.shape[0],dtype=bool))
    loo=min(calc(np.arange(d.shape[0])!=r) for r in range(d.shape[0]))
    return float(full),float(loo)

def build_components(stop_p, rectangles, timesteps) -> ComponentBuild:
    """Canonical observation-resolved component construction.

    Uses only actual physical-stop predictions from calibration members 0..3,
    persistent source geometry, and a fixed finite observation-noise floor.
    Outcome r_j is not an input.
    """
    p=np.asarray(stop_p,dtype=float); rect=np.asarray(rectangles,dtype=int)
    if p.ndim!=3: raise ValueError("stop_p must be [S,M,J]")
    S=p.shape[0]
    if rect.shape!=(S,4): raise ValueError("rectangles shape mismatch")
    precision,vals,c_tr,c_y=effective_precision(p,timesteps)
    dsu=_DSU(S); resolved=[]; unresolved=[]
    for i in range(S):
        for j in range(i+1,S):
            # Exact geometric aliases are never allowed to masquerade as resolvable sources.
            if np.array_equal(rect[i],rect[j]):
                dsu.unite(i,j); unresolved.append((i,j)); continue
            if not _adjacent_rect(rect[i],rect[j]):
                continue
            d=p[i,:K_CAL,:]-p[j,:K_CAL,:]
            full,loo=_pair_cross(d,precision)
            zero=_numzero(full,loo,d,precision)
            if full > zero and loo > zero:
                resolved.append((i,j))
            else:
                dsu.unite(i,j); unresolved.append((i,j))
    root_to_label={}; labels=np.zeros(S,dtype=int)
    for s in range(S):
        root=dsu.find(s)
        if root not in root_to_label: root_to_label[root]=len(root_to_label)
        labels[s]=root_to_label[root]
    return ComponentBuild(labels,precision,c_tr,c_y,vals,tuple(resolved),tuple(unresolved))

def source_member_stop_logscore(stop_p, stop_r, timesteps, scoring_members=None):
    p=np.asarray(stop_p,dtype=float); r=np.asarray(stop_r,dtype=float)
    if p.ndim!=3 or p.shape[2]!=len(r): raise ValueError("score shape mismatch")
    if np.any((r<0)|(r>1)): raise ValueError("stop outcome outside [0,1]")
    if scoring_members is None: scoring_members=list(range(K_CAL,K_CAL+K_SCORE))
    eps=frequency_floor(timesteps)
    pp=np.clip(p[:,scoring_members,:],eps,1.0-eps)
    return r[None,None,:]*np.log(pp)+(1.0-r[None,None,:])*np.log1p(-pp)

def coherent_source_score(member_stop_logscore, stops):
    a=np.asarray(member_stop_logscore,dtype=float); stops=np.asarray(stops,dtype=int)
    out=np.empty(a.shape[0])
    for s in range(a.shape[0]):
        out[s]=_logmeanexp(np.sum(a[s][:,stops],axis=1))
    return out

def components_from_labels(labels):
    lab=np.asarray(labels,dtype=int); vals=sorted(np.unique(lab).tolist())
    return [np.flatnonzero(lab==v) for v in vals], vals

def _component_train_logevidence(a, ix, train, q0):
    src=coherent_source_score(a,train)
    return _weighted_lse(src[ix],q0[ix])

def _component_conditional_predictive(a, ix, train, h, q0):
    """p(y_h | y_train, source in component), preserving source+member identity."""
    train=np.asarray(train,dtype=int)
    train_src=coherent_source_score(a,train)
    joint_src=coherent_source_score(a,np.append(train,h))
    return _weighted_lse(joint_src[ix],q0[ix]) - _weighted_lse(train_src[ix],q0[ix])

def jeffreys_beta_null_predictive(stop_r, train, h):
    """Source-independent prequential Bernoulli null with frozen Beta(1/2,1/2) prior."""
    r=np.asarray(stop_r,dtype=float); train=np.asarray(train,dtype=int)
    alpha=0.5+float(np.sum(r[train]))
    beta=0.5+float(len(train)-np.sum(r[train]))
    q=alpha/(alpha+beta)
    return float(r[h]*math.log(q)+(1.0-r[h])*math.log1p(-q)), float(q)

def strict_loso_m2(stop_p, stop_r, component_labels, geometry_prior, timesteps,
                   scoring_members=None, min_informative=2) -> M2Decision:
    p=np.asarray(stop_p,dtype=float); r=np.asarray(stop_r,dtype=float); J=p.shape[2]
    empty=lambda reason: M2Decision(False,reason,None,None,0,None,None,None,None,tuple())
    if J<3: return empty("NEED_3_PHYSICAL_STOPS")
    q0=_norm(geometry_prior,"geometry prior")
    comps,comp_values=components_from_labels(component_labels)
    if len(comps)<2: return empty("ONE_COMPONENT")
    a=source_member_stop_logscore(p,r,timesteps,scoring_members)
    best_sets=[]; trains=[]
    for h in range(J):
        train=np.asarray([j for j in range(J) if j!=h],dtype=int); trains.append(train)
        cscore=np.asarray([_component_train_logevidence(a,ix,train,q0) for ix in comps])
        mx=np.max(cscore); tol=_numzero(cscore)
        best_sets.append(tuple(np.flatnonzero(cscore>=mx-tol).tolist()))
    common=set(best_sets[0])
    for bs in best_sets[1:]: common &= set(bs)
    if len(common)!=1:
        return M2Decision(False,"LOSO_COMPONENT_DISAGREE",None,None,0,None,None,None,None,tuple(best_sets))
    b=int(next(iter(common))); mask=np.asarray(component_labels)==comp_values[b]
    abs_gain=[]; rival_margin=[]; comp_score=[]; null_score=[]; informative=0
    for h,train in enumerate(trains):
        pred=np.asarray([_component_conditional_predictive(a,ix,train,h,q0) for ix in comps])
        selected=float(pred[b])
        rival=float(selected-np.max(np.delete(pred,b)))
        null,_=jeffreys_beta_null_predictive(r,train,h)
        gain=float(selected-null)
        tol=_numzero(pred,null,gain)
        abs_gain.append(gain); rival_margin.append(rival); comp_score.append(selected); null_score.append(null)
        if rival < -tol:
            return M2Decision(False,"HELDOUT_RIVAL_CONTRADICTION",b,mask,informative,
                              np.asarray(abs_gain),np.asarray(rival_margin),
                              np.asarray(comp_score),np.asarray(null_score),tuple(best_sets))
        if gain <= tol:
            return M2Decision(False,"HELDOUT_ABSOLUTE_NULL_FAIL",b,mask,informative,
                              np.asarray(abs_gain),np.asarray(rival_margin),
                              np.asarray(comp_score),np.asarray(null_score),tuple(best_sets))
        if rival > tol: informative += 1
    if informative<min_informative:
        return M2Decision(False,"INSUFFICIENT_INFORMATIVE_HELDOUT",b,mask,informative,
                          np.asarray(abs_gain),np.asarray(rival_margin),
                          np.asarray(comp_score),np.asarray(null_score),tuple(best_sets))
    return M2Decision(True,"ACCEPT",b,mask,informative,np.asarray(abs_gain),
                      np.asarray(rival_margin),np.asarray(comp_score),
                      np.asarray(null_score),tuple(best_sets))

def member_loo_robust(stop_p, stop_r, labels, q0, timesteps, reference_mask, min_informative=1):
    for removed in range(K_CAL,K_CAL+K_SCORE):
        members=[m for m in range(K_CAL,K_CAL+K_SCORE) if m!=removed]
        d=strict_loso_m2(stop_p,stop_r,labels,q0,timesteps,members,min_informative=min_informative)
        if d.accepted and not np.array_equal(d.selected_mask,reference_mask): return False
        if d.reason=="HELDOUT_RIVAL_CONTRADICTION": return False
    return True

def binary_causal_update(q_causal, stop_p, stop_r, selected_mask, timesteps):
    qc=_norm(q_causal,"causal state"); mask=np.asarray(selected_mask,dtype=bool)
    a=source_member_stop_logscore(stop_p,stop_r,timesteps)
    sscore=coherent_source_score(a,list(range(a.shape[2])))
    inside=float(qc[mask].sum()); outside=1.0-inside
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

def initialize_state(geometry_prior):
    return StableState(_norm(geometry_prior,"geometry prior"))

def apply_window(stop_p, stop_r, rectangles, q0, native_post, timesteps,
                 state: StableState, window_id: str):
    """Normative window path: components are always built internally from calibration members."""
    if not window_id or window_id in state.consumed:
        raise ValueError("DUPLICATE_OR_EMPTY_WINDOW")
    st=state.clone(); st.consumed.add(window_id)
    build=build_components(stop_p,rectangles,timesteps)
    d=strict_loso_m2(stop_p,stop_r,build.labels,q0,timesteps)
    if not d.accepted:
        return _norm(native_post),st,d,False,None,None,build
    if not member_loo_robust(stop_p,stop_r,build.labels,q0,timesteps,d.selected_mask):
        d.accepted=False; d.reason="SCORING_MEMBER_LOO_FAIL"
        return _norm(native_post),st,d,False,None,None,build
    st.q_causal,_=binary_causal_update(st.q_causal,stop_p,stop_r,d.selected_mask,timesteps)
    st.last_mask=d.selected_mask.copy()
    alpha=float(st.q_causal[d.selected_mask].sum())
    out,active,beta=information_projection(native_post,d.selected_mask,alpha,q0)
    return out,st,d,active,alpha,beta,build
