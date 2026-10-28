"""Shared ordinary Bayesian source posterior. No bio features in likelihood."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.special import logsumexp
from .types import Reading, Configuration
from .physics import ForwardModel


@dataclass(frozen=True)
class Posterior:
    sources: np.ndarray
    mass: np.ndarray
    q_values: np.ndarray
    joint_source_q: np.ndarray
    map_source: np.ndarray
    entropy: float
    xy_covariance: np.ndarray
    ess: float
    log_evidence: float

    def source_xy_probability(self) -> tuple[np.ndarray,np.ndarray]:
        xy=self.sources[:,:2]
        keys,inverse=np.unique(xy,axis=0,return_inverse=True)
        p=np.bincount(inverse,weights=self.mass,minlength=len(keys))
        return keys,p

    def conditional_mean_q(self):
        return (self.joint_source_q @ self.q_values)/np.maximum(self.mass,1e-30)


def joint_posterior(observations: list[Reading], sources: np.ndarray,
                    model: ForwardModel, cfg: Configuration,
                    source_prior: np.ndarray | None = None) -> Posterior:
    """Recompute entire observed history exactly once; no multiplying a bio feature.

    Model forecasts unit-amplitude causal sensor responses, while q is a
    *shared nuisance parameter* integrated over one common prior. Sensor
    validity selects actual observed entries, not future data or oracle labels.
    """
    s=np.asarray(sources,float)
    if s.ndim!=2 or s.shape[1]!=3 or len(s)<2:raise ValueError('Need [S,3] candidates')
    p0=np.ones(len(s))/len(s) if source_prior is None else np.asarray(source_prior,float)
    if p0.shape!=(len(s),) or np.any(p0<0) or not np.isclose(p0.sum(),1.):
        raise ValueError('invalid source prior')
    F=np.asarray(model.response(s,observations),float)
    y=np.stack([o.gas_ppm for o in observations]);mask=np.stack([o.valid for o in observations])
    if F.shape!=(len(s),len(observations),y.shape[1]):raise ValueError('bad forward shape')
    if not np.isfinite(F).all() or np.any(F<0):raise ValueError('invalid response')
    yy=y[mask]; FF=F[:,mask]
    q=np.asarray(cfg.q_values); pq=np.asarray(cfg.q_prior)
    # log likelihood: [S,Q], arbitrary shared background already subtracted
    z=(yy[None,None,:]-FF[:,None,:]*q[None,:,None])/cfg.sensor_sigma
    ll=-.5*np.einsum('sqi,sqi->sq',z,z)
    logjoint=ll+np.log(np.maximum(p0[:,None],1e-300))+np.log(np.maximum(pq[None,:],1e-300))
    norm=logsumexp(logjoint)
    joint=np.exp(logjoint-norm)
    mass=joint.sum(axis=1)
    mapidx=int(np.argmax(mass)); mean=(mass[:,None]*s[:,:2]).sum(axis=0)
    diff=s[:,:2]-mean; cov=diff.T@(mass[:,None]*diff)
    return Posterior(s,mass,q,joint,s[mapidx].copy(),float(-np.sum(mass*np.log(np.maximum(mass,1e-300)))),
                     cov,float(1/np.sum(mass**2)),float(norm))