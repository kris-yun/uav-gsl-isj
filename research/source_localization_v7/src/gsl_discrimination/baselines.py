"""Explicit comparison operators. These are not a full ROS PMFS reproduction."""
from __future__ import annotations
import numpy as np
from scipy.special import logsumexp


def pmfs_map_compatibility(measured_hit,confidence,predicted_hit,difference_factor=1.,free_mask=None):
    """The active non-frequency-distribution sourceProbFromMaps branch.

    Recomputed from accumulated maps, not multiplied into the previous source
    posterior. Exact source pin and limitations are in docs/SOURCE_AUDIT.json.
    """
    m=np.asarray(measured_hit,dtype=float);c=np.asarray(confidence,dtype=float)
    h=np.asarray(predicted_hit,dtype=float)
    if h.ndim!=2 or h.shape[1]!=len(m) or c.shape!=m.shape:
        raise ValueError("expected measured/confidence[cell], predicted[source,cell]")
    if np.any((m<0)|(m>1)) or np.any((c<0)|(c>1)) or np.any((h<0)|(h>1)):
        raise ValueError("hit fractions and confidence must be in [0,1]")
    mask=np.ones(len(m),dtype=bool) if free_mask is None else np.asarray(free_mask,dtype=bool)
    if mask.shape!=m.shape or not np.any(mask):raise ValueError("nonempty free-cell mask required")
    factors=1-difference_factor*c[None,:]*np.abs(m[None,:]-h)
    if np.any(factors[:,mask]<0):raise ValueError("invalid compatibility factor; inspect native configuration")
    with np.errstate(divide='ignore'):scores=np.log(factors[:,mask]).sum(1)
    if not np.isfinite(logsumexp(scores)):raise ValueError("all native compatibility products vanish")
    return np.exp(scores-logsumexp(scores)),scores


def pmfs_variance_interest(predicted_hit,source_probability,confidence):
    h=np.asarray(predicted_hit,dtype=float);p=np.asarray(source_probability,dtype=float)
    if h.shape[0]!=len(p) or not np.isclose(p.sum(),1):raise ValueError("source weights do not match")
    mean=p@h
    return (p@(h*h)-mean*mean)*(1-np.asarray(confidence))


def joint_eig(predictives,source_probability,costs=None):
    """Exact finite-alphabet one-block EIG under the same conditional model."""
    q=np.asarray(predictives,dtype=float);p=np.asarray(source_probability,dtype=float)
    if q.ndim!=3 or q.shape[1]!=len(p):raise ValueError("expected [action,source,outcome]")
    if np.any(p<0) or not np.isclose(p.sum(),1):raise ValueError("normalized source posterior required")
    active=p>0;q=q[:,active,:];p=p[active]
    mix=np.einsum('s,aso->ao',p,q)
    with np.errstate(divide='ignore',invalid='ignore'):
        terms=np.where(q>0,q*(np.log(q)-np.log(mix[:,None,:])),0)
    val=np.einsum('s,as->a',p,terms.sum(-1))
    return val if costs is None else val/np.asarray(costs)


def standard_chernoff(predictives,source_probability,costs):
    """Direct cost-aware mother baseline, without the gas audit modifications."""
    from .m3_audit import cost_aware_allocation,pairwise_kl
    i=int(np.argmax(source_probability));q=np.asarray(predictives)
    rivals=[j for j in range(q.shape[1]) if j!=i]
    d=pairwise_kl(q)[:,i,rivals]
    if not np.isfinite(d).all():raise ValueError("singular mother channel; use explicit support handling")
    return cost_aware_allocation(d,np.asarray(costs))

