"""Reference math for matched SOURCE support. Not a new localization algorithm.
No physics, fitting, source-truth access, or cell deletion. NumPy only.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
import numpy as np


def checked_prob(a,name):
    a=np.asarray(a,dtype=np.float64)
    if not np.all(np.isfinite(a)) or np.any((a<0)|(a>1)):
        raise ValueError(f'{name}: must be finite probabilities in [0,1]')
    return a


def native_log_score(measured,confidence,predicted,free_mask,D=0.4):
    """predicted [...,G], shared measured/confidence [G]. No hidden clipping."""
    m=checked_prob(measured,'measured');c=checked_prob(confidence,'confidence')
    q=checked_prob(predicted,'predicted');mask=np.asarray(free_mask,dtype=bool)
    if m.ndim!=1 or c.shape!=m.shape or mask.shape!=m.shape or q.shape[-1:]!=m.shape:
        raise ValueError('Shared readout support shape mismatch')
    if not np.any(mask) or not (0<=D<1):raise ValueError('Need nonempty mask and 0<=D<1')
    factors=1-float(D)*c[mask]*np.abs(q[...,mask]-m[mask])
    if np.any(factors<=0): raise ValueError('Nonpositive native factor; do not silently clip')
    return np.log(factors).sum(axis=-1)


def event_composite_log_score(reference_events,observed_events,alpha=0.5):
    """Candidate [S,M,T] Bernoulli references; mean log score, NOT a joint likelihood."""
    x=np.asarray(reference_events);y=np.asarray(observed_events)
    if x.ndim!=3 or y.shape!=(x.shape[2],) or x.shape[1]<1:
        raise ValueError('Expected [S,M,T] references and [T] observation')
    if not np.isin(x,[0,1]).all() or not np.isin(y,[0,1]).all():raise ValueError('Binary only')
    if not np.isfinite(alpha) or alpha<=0:raise ValueError('Positive fixed smoothing required')
    p=(x.sum(axis=1)+alpha)/(x.shape[1]+2*alpha)
    return (y*np.log(p)+(1-y)*np.log1p(-p)).mean(axis=1)


def normalized_source_weights(log_scores,prior):
    s=np.asarray(log_scores,dtype=float);p=np.asarray(prior,dtype=float)
    if s.ndim!=1 or p.shape!=s.shape or not np.all(np.isfinite(s)):
        raise ValueError('Finite source scores [S] and matching prior required')
    if not np.all(np.isfinite(p)) or np.any(p<=0) or not np.isclose(p.sum(),1,atol=1e-12):
        raise ValueError('All registered candidates need positive normalized prior')
    a=s+np.log(p);a-=a.max();w=np.exp(a);return w/w.sum()


def validate_partition(cell_to_source,active_mask,source_count):
    """A coarse partition is complete coverage, but is NOT an atomic-source experiment."""
    ids=np.asarray(cell_to_source,dtype=int);active=np.asarray(active_mask,dtype=bool)
    if ids.shape!=active.shape:raise ValueError('Partition shape mismatch')
    if source_count<1 or np.any(ids[active]<0) or np.any(ids[active]>=source_count):
        raise ValueError('An active source cell is missing or has invalid source ID')
    n=np.bincount(ids[active],minlength=source_count)
    if np.any(n==0):raise ValueError('Registered source has no mapped cell')
    return n


def rasterize_source_mass(source_mass,cell_to_source,active_mask):
    w=checked_prob(source_mass,'source_mass')
    if w.ndim!=1 or not np.isclose(w.sum(),1,atol=1e-12):raise ValueError('Need normalized source mass')
    ids=np.asarray(cell_to_source,dtype=int);active=np.asarray(active_mask,dtype=bool)
    n=validate_partition(ids,active,len(w));out=np.zeros(ids.shape,dtype=float)
    out[active]=w[ids[active]]/n[ids[active]]
    if not np.isclose(out.sum(),1,atol=1e-12):raise ValueError('Raster mass loss')
    return out


def score_perturbation(reference_scores,new_scores):
    a=np.asarray(reference_scores,dtype=float);b=np.asarray(new_scores,dtype=float)
    if a.shape!=b.shape or a.ndim!=1 or len(a)<2 or not np.isfinite(a+b).all():
        raise ValueError('Need two finite scores on same >=2 sources')
    r=float(np.ptp(b-a));ref_gap=float(np.sort(a)[-1]-np.sort(a)[-2])
    return dict(range_delta=r,reference_top_gap=ref_gap,
                reference_top_preserved_by_bound=bool(ref_gap>r),
                nll_change_bound=r,kl_reference_to_new_bound=r*r/8,
                scope='same prior and unit score temperature; fidelity to reference, not truth')


def contract_diff(before,after,allowed_paths=()):
    """Exact nested contract comparison. Paths not registered as changes are errors."""
    def flat(x,p=''):
        if isinstance(x,dict):
            out={}
            for k,v in sorted(x.items()):out.update(flat(v,f'{p}.{k}' if p else k))
            return out
        return {p:x}
    a,b=flat(before),flat(after);changes=[]
    for k in sorted(set(a)|set(b)):
        if json.dumps(a.get(k,'__MISSING__'),sort_keys=True)!=json.dumps(b.get(k,'__MISSING__'),sort_keys=True):
            changes.append(k)
    bad=[k for k in changes if k not in allowed_paths]
    if bad:raise ValueError('Unregistered changes: '+', '.join(bad))
    return changes
