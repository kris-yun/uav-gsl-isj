"""M1: O(N × short-history) identity-preserving egocentric flow–olfaction.

This is a *control feature* rather than a source measurement likelihood. It
computes causal approximate sensor footprints, a past relative-motion Gram,
and per-instrument signed flow. It does not access any source posterior or truth.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.special import ndtr
from .types import Reading


@dataclass(frozen=True)
class Signature:
    stage: str
    wind_along: np.ndarray
    wind_cross: np.ndarray
    signed_flow: np.ndarray
    radial_flow: np.ndarray
    contact_prob: np.ndarray
    eccentricity: float
    contact_count: int
    crosswind_spread_m: float
    time_cert: bool
    shape_cert: bool
    reason: str
    effective_positions: np.ndarray
    missing_axis: np.ndarray
    motion_gram: np.ndarray
    motion_rank: int
    footprint_available: bool


def _footprint(history: list[Reading], target_t: float) -> tuple[np.ndarray,bool]:
    """Causal interpolation of historical INS position at the approximate
    effective gas readout time. This is a footprint proxy, not a correction of
    unknown puff release age or a claim of deconvolved methane concentration.
    """
    ts=np.array([x.t for x in history],float)
    if target_t < ts[0] or target_t > ts[-1]:
        return history[-1].pos.copy(), False
    hi=int(np.searchsorted(ts,target_t,side='left'))
    if hi==0:return history[0].pos.copy(),True
    before=history[hi-1];after=history[hi]
    w=(target_t-before.t)/(after.t-before.t)
    return (1-w)*before.pos+w*after.pos,True


def encode(history: list[Reading], sigma: float=.02, threshold: float=.06,
           min_wind: float=.1, stationarity_window: int=4,
           sensor_delay_s: float=2., sensor_tau_s: float=1.) -> Signature:
    if not history:raise ValueError('Empty sensor history')
    if sigma<=0 or stationarity_window<2:raise ValueError('invalid signature parameters')
    b=history[-1];n=len(b.pos)
    dt=(b.t-history[-2].t) if len(history)>1 else 1.
    if dt<=0:raise ValueError('invalid sensor history clock')
    rho=np.exp(-dt/sensor_tau_s) if sensor_tau_s>0 else 0.
    effective_age=sensor_delay_s+dt*rho/max(1-rho,1e-12)
    effective,footprint_available=_footprint(history,b.t-effective_age)
    p=effective if footprint_available else b.pos
    d=p-p.mean(axis=0)
    radii=np.linalg.norm(d,axis=1)
    normals=d/np.maximum(radii[:,None],1e-12)
    # Essential correction to V35: flow in each receptor's moving frame.
    vel=(b.pos-history[-2].pos)/dt if len(history)>1 else np.zeros_like(b.pos)
    relwind=b.wind-vel
    radial=np.einsum('ij,ij->i',relwind,normals)
    weights=np.where(b.valid,ndtr((b.gas_ppm-threshold)/sigma),0.)
    signed=(weights*radial)[:,None]*normals
    u=b.wind[:,:2].mean(axis=0)
    speed=float(np.linalg.norm(u))
    along=u/speed if speed>min_wind else np.array([1.,0.])
    cross=np.array([-along[1],along[0]])
    spread=float(np.ptp(d[:,:2]@cross))
    count=int(np.sum(b.valid & (b.gas_ppm>=threshold)))
    # Rank of identity-aligned RELATIVE motions, not a source Fisher matrix.
    gram=np.zeros((2,2),float)
    recent=history[-9:]
    for prev,next_ in zip(recent[:-1],recent[1:]):
        a=prev.pos[:,:2]-prev.pos[:,:2].mean(axis=0)
        v=next_.pos[:,:2]-next_.pos[:,:2].mean(axis=0)-a
        gram+=v.T@v
    evals,evecs=np.linalg.eigh(gram)
    rank=int((evals>max(1e-9,1e-6*evals[-1])).sum())
    gap=evecs[:,0] if evals[-1]>1e-9 else cross
    if float(gap@cross)<0:gap=-gap
    if abs(float(gap@cross))<1e-12 and float(gap@along)<0:gap=-gap
    gap=gap/max(1e-12,float(np.linalg.norm(gap)))
    clocks=np.array([h.t for h in history[-stationarity_window:]])
    time_cert=(len(clocks)==stationarity_window and
               np.allclose(np.diff(clocks),dt,atol=1e-7))
    # Provisional signal-geometry condition; NEVER claims puff-age coherence.
    steady=(len(history)>=stationarity_window and all(
        np.all(h.valid & (h.gas_ppm>=threshold)) for h in history[-stationarity_window:]))
    aligned=np.ptp(d[:,:2]@along)<1.0 and np.ptp(p[:,2])<.5
    shape_cert=bool(steady and time_cert and aligned and speed>min_wind and footprint_available)
    ecc=float(np.dot(weights,d[:,:2]@cross)/max(float(weights.sum()),1e-12))
    if not np.all(b.valid):stage='invalid'; reason='invalid instrument; not a negative gas sample'
    elif speed<=min_wind:stage='wind_weak';reason='wind azimuth unqualified'
    elif count==0:stage='precontact';reason='physical coverage: no source probability from wind alone'
    elif count<n:stage='partial';reason='partial gas support; feedback and recenter'
    elif shape_cert:stage='section';reason='provisional common slice; puff-age not certified'
    else:stage='contact_uncertain';reason='gas seen but causal section qualification weak'
    return Signature(stage,along,cross,signed,radial,weights,ecc,count,spread,
                     time_cert,shape_cert,reason,p.copy(),gap,gram,rank,footprint_available)