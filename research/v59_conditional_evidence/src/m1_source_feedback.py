"""V58 research prototype: source-sensitive body/history action proposals.

This module supplies a precise experimental candidate, NOT a validated plume
controller. A shared, qualified forward model must supply the derivatives of
future RAW observations after its nuisance treatment. Internal half-wave and
lag features are used ONLY to propose actions, never as independent likelihoods.

Biological inspiration: retain sensor position and flow polarity before motor
readout. Engineering additions: complete horizontal directions, qualified lag
tokens, source-sensitive curvature, and coupled translation/reconfiguration.

An ordinary full second-order planner is deliberately included. It matches or
dominates restricted bases in the unconstrained local quadratic problem.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable
import numpy as np


def encode_causal_history(times, positions, relative_wind, odor_eligibility,
                          *, now, lag_edges, support_qualified,
                          quality=None, sample_weights=None):
    """Retain (lag, radial/tangential, polarity, modality, sensor) groups.

    Input times are actual exposure-support timestamps, NOT decision indices.
    Sensor response/latency alignment must be performed and qualified by the
    shared observation model. odor_eligibility is a CONTROL feature from that
    same history, not a second observation or an exact deconvolved concentration.
    Wind-only groups remain active when odor eligibility is zero.
    relative_wind must be air-minus-UAV velocity EXPRESSED IN WORLD AXES;
    body-frame instrument readings must be rotated before this call.
    Historical vectors remain in their recorded world orientation; they are
    never recomputed using only the CURRENT body geometry.
    """
    if not support_qualified:
        raise ValueError('Missing qualified wind/odor/pose time support')
    t = np.asarray(times, float)
    p = np.asarray(positions, float)
    w = np.asarray(relative_wind, float)
    o = np.asarray(odor_eligibility, float)
    edges = np.asarray(lag_edges, float)
    if p.ndim != 3 or p.shape[-1] != 2 or p.shape != w.shape:
        raise ValueError('Need time x sensor x 2 positions and relative wind')
    nt, ns, _ = p.shape
    if t.shape != (nt,) or o.shape != (nt, ns) or ns < 2 or nt == 0:
        raise ValueError('History dimensions do not agree')
    if any(not np.isfinite(x).all() for x in [t,p,w,o,edges]):
        raise ValueError('Finite inputs required')
    if not np.isfinite(now) or np.any(np.diff(t) <= 0) or np.any(t > now):
        raise ValueError('Strictly ordered causal timestamps required')
    if np.any(o < 0) or len(edges) < 2 or edges[0] != 0 or np.any(np.diff(edges) <= 0):
        raise ValueError('Nonnegative eligibility and increasing lag edges from 0 required')
    quality = np.ones((nt,ns), bool) if quality is None else np.asarray(quality, bool)
    sw = np.ones(nt) if sample_weights is None else np.asarray(sample_weights, float)
    if quality.shape != (nt,ns) or sw.shape != (nt,) or np.any(sw < 0) or not np.isfinite(sw).all():
        raise ValueError('Invalid quality or sample weights')
    delta = p - p.mean(axis=1, keepdims=True)
    radius = np.linalg.norm(delta, axis=-1)
    normal = np.divide(delta, radius[...,None], out=np.zeros_like(delta),
                       where=radius[...,None] > 1e-12)
    tangent = np.stack((-normal[...,1], normal[...,0]), axis=-1)
    axes = (normal, tangent)
    age = now-t
    groups = []
    for ell in range(len(edges)-1):
        take = (age >= edges[ell]) & (age < edges[ell+1])
        if ell == len(edges)-2:
            take |= age == edges[ell+1]
        for b, axis in enumerate(axes):
            flow = np.einsum('tnd,tnd->tn', w, axis)
            for sign in (-1, 1):
                a = np.maximum(sign*flow, 0) * quality * (radius > 1e-12)
                a *= (take*sw)[:,None]
                for modality, eligibility in [('wind',np.ones_like(o)),('odor_tagged',o)]:
                    weight = a*eligibility
                    # Opponent motor template; BOTH action signs are generated later.
                    vector = np.sum((-sign)*weight[...,None]*axis, axis=0)
                    groups.append({'lag':ell,'axis':b,'polarity':sign,
                                   'modality':modality,'mass':float(weight.sum()),
                                   'vector':vector})
    return groups


def split_translation_relative(vector):
    v = np.asarray(vector, float)
    if v.ndim != 2 or v.shape[1] != 2:
        raise ValueError('Need sensor x 2 actual displacement template')
    translation = np.broadcast_to(v.mean(axis=0), v.shape).copy()
    return translation, v-translation


def gaussian_contrast_quadratic(delta_mean, contrast_jacobian, covariance):
    """Local COMMON-covariance Gaussian proxy, not universal source MI.

    delta_mean and contrast_jacobian concern two source-conditional predictive
    distributions after nuisance treatment. Rows must represent unique future
    RAW gas/wind measurements. Full correlated covariance is required.
    For exact distribution crossing delta_mean=0, Q=D.T Sigma^-1 D; the source
    MI coefficient is pi*(1-pi)/2. Changing/mode-dependent covariance needs the
    score-distribution version of the theorem, not this simplified function.
    """
    delta = np.asarray(delta_mean, float)
    d = np.asarray(contrast_jacobian, float)
    cov = np.asarray(covariance, float)
    if d.ndim != 2 or delta.shape != (len(d),) or cov.shape != (len(d),len(d)):
        raise ValueError('Predictive dimensions mismatch')
    if any(not np.isfinite(a).all() for a in [delta,d,cov]):
        raise ValueError('Finite predictive arrays required')
    if not np.allclose(cov,cov.T,atol=1e-12):
        raise ValueError('Covariance must be symmetric')
    chol = np.linalg.cholesky(cov)
    dw = np.linalg.solve(chol,d)
    rw = np.linalg.solve(chol,delta)
    return {'Q':dw.T@dw,'linear':dw.T@rw,'constant':float(rw@rw)}


def _basis(matrix, tol=1e-12):
    b = np.asarray(matrix, float)
    if b.size == 0:
        return np.empty((b.shape[0],0))
    u,s,_ = np.linalg.svd(b,full_matrices=False)
    return u[:,s>tol]


def _quadratic_ball_max(H, g, radius):
    """Global maximum of PSD quadratic u'Hu+2g'u over ||u||<=radius.

    The secular equation handles ordinary cases; the top-eigenspace hard case
    is explicit. Multiple maximizers are represented by a numerical basis,
    not by the entire continuum; finite ties are NOT rotation-equivariant.
    """
    eig,V=np.linalg.eigh((H+H.T)/2)
    tol=1e-12*max(1.,abs(eig[-1]),np.linalg.norm(g))
    if eig[0] < -tol:
        raise ValueError('The source-contrast quadratic must be PSD')
    top=eig[-1]; ge=V.T@g; tied=(top-eig <= tol)
    if np.linalg.norm(g)<tol and top<tol:
        return [],int(tied.sum())
    base=np.zeros_like(ge)
    base[~tied]=ge[~tied]/(top-eig[~tied])
    if np.linalg.norm(ge[tied])<=tol and np.linalg.norm(base)<=radius:
        extra=np.sqrt(max(0.,radius**2-base@base))
        out=[]
        for j in np.flatnonzero(tied):
            for sign in (-1,1):
                a=base.copy();a[j]=sign*extra;out.append(V@a)
        return out,int(tied.sum())
    lo=top
    hi=top+max(1.,np.linalg.norm(g)/radius)
    def norm_at(lam): return np.linalg.norm(ge/(lam-eig))
    while norm_at(hi)>radius:
        hi=top+2*(hi-top)
    for _ in range(100):
        mid=(lo+hi)/2
        if mid==lo or mid==hi: break
        if norm_at(mid)>radius:lo=mid
        else:hi=mid
    u=V@(ge/(hi-eig))
    u*=radius/np.linalg.norm(u)
    return [u],int(tied.sum())


def _restricted_proposals(Q, linear, B, C, budget, label):
    # Whiten PHYSICAL action cost after restricting the motor subspace.
    U = _basis(B)
    if U.shape[1] == 0:
        return []
    m = U.T@C@U
    vals, vecs = np.linalg.eigh((m+m.T)/2)
    if np.min(vals) <= 0:
        raise ValueError('Physical cost must be positive definite in the subspace')
    V = U @ (vecs / np.sqrt(vals)[None,:])
    h = V.T@Q@V
    solutions,multiplicity=_quadratic_ball_max(h,V.T@linear,budget)
    result = []
    for number, u in enumerate(solutions):
        for sign in (-1,1):
            a = sign*(V@u)
            result.append({'key':f'{label}:quadratic:{number}:{sign:+d}',
                           'action':a,'proxy':float(a@Q@a+2*linear@a),
                           'physical_cost':float(a@C@a),
                           'top_eigenvalue_multiplicity':multiplicity,
                           'tie_scope':'Finite numerical representatives; no degenerate/tie-break execution equivariance guarantee'})
    return result


def body_feedback_proposals(Q, linear, groups, *, budget, physical_cost=None):
    """Generate coupled T/R candidates per retained sensory group.

    B_g=[P_T g, P_R g]. Cross terms B_T.T Q B_R are retained. Source feedback
    chooses their relative signs/amplitudes instead of assigning an entire
    polarity rigidly to translation or reconfiguration. This is a restricted
    action proposal heuristic. It can miss directions: always include shared
    ordinary upwind/crosswind/coverage proposals in a real comparison.
    """
    Q = np.asarray(Q,float); linear = np.asarray(linear,float)
    dim = len(Q)
    C = np.eye(dim) if physical_cost is None else np.asarray(physical_cost,float)
    if Q.shape != (dim,dim) or linear.shape != (dim,) or C.shape != Q.shape or budget <= 0:
        raise ValueError('Bad action model')
    proposals = []
    for j,group in enumerate(groups):
        v = np.asarray(group['vector'],float)
        if v.size != dim:
            raise ValueError('Sensory template and action dimension mismatch')
        t,r = split_translation_relative(v)
        B = np.column_stack([t.ravel(),r.ravel()])
        label = f"g{j}:lag{group['lag']}:{group['modality']}:a{group['axis']}:p{group['polarity']}"
        proposals.extend(_restricted_proposals(Q,linear,B,C,budget,label))
    # Deduplicate identical actual motions, never count duplicate channels as trials.
    unique = []
    for p in sorted(proposals,key=lambda p:(-p['proxy'],p['key'])):
        if not any(np.allclose(p['action'],q['action'],atol=1e-10,rtol=1e-10) for q in unique):
            unique.append(p)
    return unique


def ordinary_full_second_order(Q,linear,*,budget,physical_cost=None):
    """Mandatory same-input strong comparator, not a BIO component."""
    Q=np.asarray(Q,float); C=np.eye(len(Q)) if physical_cost is None else np.asarray(physical_cost,float)
    return _restricted_proposals(Q,np.asarray(linear,float),np.eye(len(Q)),C,budget,'ordinary_full')


@dataclass
class CostLedger:
    # Do not equate these differently sized operations. Production logs must add
    # particle/time steps, mode counts, query counts, wall time and peak memory.
    field_builds: int = 0
    sensitivity_forward_calls: int = 0
    cheap_candidates_scored: int = 0
    expensive_callbacks: int = 0


def lazy_score(proposals, *, k, expensive_score:Callable, ledger:CostLedger,
               model_qualified, legal:Callable=lambda a:True):
    """No per-candidate response matrices before selection.

    Scores supplied in proposals must come from a DECLARED shared local model.
    Qualification here is an external assertion; this module cannot qualify
    a physical forward model. Safety must check the whole proposed path.
    """
    if not model_qualified:
        return None,{'stage':'MODEL_NOT_QUALIFIED','cost':asdict(ledger)}
    if not isinstance(k,int) or k <= 0:
        raise ValueError('Positive integer budget required')
    feasible=[]
    for p in proposals:
        ledger.cheap_candidates_scored += 1
        if legal(p['action']):
            feasible.append(p)
    chosen=sorted(feasible,key=lambda p:(-p['proxy'],p['key']))[:k]
    evaluated=[]
    for p in chosen:
        ledger.expensive_callbacks += 1
        score=float(expensive_score(p['action']))
        evaluated.append({'key':p['key'],'score':score,'action':p['action']})
    winner=max(evaluated,key=lambda p:(p['score'],p['key'])) if evaluated else None
    return winner,{'stage':'ANALYTICAL_OR_EXTERNALLY_QUALIFIED_SCORE',
                   'selected_keys':[p['key'] for p in chosen],
                   'evaluated_scores':[p['score'] for p in evaluated],
                   'cost':asdict(ledger),
                   'cost_claim':'K limits callback evaluations only; all upstream costs remain counted'}
