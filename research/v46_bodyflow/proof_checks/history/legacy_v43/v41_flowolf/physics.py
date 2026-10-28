"""Causal, source-conditioned forward interface and a self-contained demo model.

The included Gaussian advective surrogate is **not** the S2 native puff solver.
It produces source-conditioned instantaneous ppms, followed by a measured-time
sensor delay / first order filter, and never uses future realized observations.
A genuine native source-conditioned forecaster can implement response().
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
import numpy as np
from .types import Reading


class ForwardModel(Protocol):
    def response(self, sources: np.ndarray, observations: list[Reading]) -> np.ndarray:
        """Unit-amplitude causal sensor response [S,T,N] for supplied paths.

        Past and proposed future Reading records may be passed; future gas
        values are zeros and wind is a *held causal estimate*, not true wind.
        Current measured gas MUST NOT enter source response prediction.
        """


@dataclass(frozen=True)
class GaussianAdvectionDemo:
    """Simple affine-power plume kernel for *software* qualification only.

    Wind is observed Earth-frame and evaluated at each observed time; the model
    is intentionally a low-cost ordinary conditional forward, not novel physics.
    q=1 scales to the peak concentration parameter ``amplitude_ppm``.
    """
    peak_ppm: float = .36
    lag_s: float = 2.0
    tau_s: float = 1.0
    spread0_m: float = 3.5
    spread_rate: float = .09
    along_scale_m: float = 45.0

    def response(self, sources: np.ndarray, observations: list[Reading]) -> np.ndarray:
        s = np.asarray(sources, float)
        if s.ndim != 2 or s.shape[1] != 3: raise ValueError('sources must be [S,3]')
        if not observations: raise ValueError('Empty history')
        t = np.array([a.t for a in observations],float)
        if len(t)>1 and not np.allclose(np.diff(t),np.diff(t)[0],atol=1e-7):
            raise ValueError('Equally spaced causal time grid required')
        dt=float(t[1]-t[0]) if len(t)>1 else 1.
        if dt<=0:raise ValueError('Time order error')
        n=len(observations[0].pos)
        pos=np.stack([o.pos for o in observations])
        wind=np.stack([o.wind for o in observations])
        if np.any(~np.isfinite(pos)) or np.any(~np.isfinite(wind)):
            raise ValueError('nonfinite positions/wind')
        dx=pos[None,:,:,:]-s[:,None,None,:]       # S,T,N,3
        u=wind.copy()
        speed=np.linalg.norm(u[:,:,:2],axis=2)
        e=u[:,:,:2]/np.maximum(speed[:,:,None],1e-6) # T,N,2
        down=np.einsum('stnd,tnd->stn', dx[:,:,:,:2],e)
        across=np.einsum('stnd,tnd->stn', dx[:,:,:,:2],np.stack([-e[:,:,1],e[:,:,0]],axis=-1))
        sigma=self.spread0_m + self.spread_rate*np.maximum(down,0)
        # No source azimuth from ambient wind alone; this conditional field is
        # a physical hypothesis, and zeros are retained for upwind points.
        spatial = np.exp(-.5*((across/sigma)**2 + (dx[:,:,:,2]/(sigma*.8))**2))
        along = np.exp(-np.maximum(down,0)/self.along_scale_m)
        raw=self.peak_ppm*spatial*along*(down>0)*(speed[None,:,:]>.05)
        if self.lag_s < 0 or self.tau_s < 0:raise ValueError('invalid sensor params')
        if len(t)==1:return np.zeros_like(raw)
        lag=self.lag_s/dt
        if not np.isclose(lag,round(lag),atol=1e-6):
            raise ValueError('delay not divisible by time step')
        nlag=int(round(lag));alpha=1. if self.tau_s==0 else -np.expm1(-dt/self.tau_s)
        out=np.zeros_like(raw)
        # Use initial zero prehistory, as validated from the native adapter.
        for k in range(1,len(t)):
            target=raw[:,k-nlag,:] if k>=nlag else np.zeros_like(raw[:,k,:])
            out[:,k,:]=out[:,k-1,:]+alpha*(target-out[:,k-1,:])
        return out


def speculative_path(history: list[Reading], v: np.ndarray, steps: int, dt: float) -> list[Reading]:
    """Forecast inputs: uses only the last observed local wind, no future true measurements."""
    if not history:raise ValueError('Need actual prefix before planning')
    last=history[-1]
    p=last.pos.copy()
    w=last.wind.copy()
    out=list(history)
    for k in range(1,steps+1):
        p=p+v*dt
        out.append(Reading(last.t+k*dt,p.copy(),np.zeros(len(p)),w.copy(),
                           np.ones(len(p),dtype=bool),last.background_ppm,last.sensor_ids))
    return out
