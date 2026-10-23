"""Causal, mirror-equivariant opponent filters on actual paired observations.

The two-filter/ReLU/mirror subtraction is the PNAS 2026 mother operator.
Gas-specific source-pair selection lives in calibration.py.  This module
does not call a side-of-plume classifier a source-location likelihood.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np


@dataclass(frozen=True)
class SamplingContract:
    continuous: bool
    synchronous: bool = True
    clock_error_s: float = 0.0
    maximum_step_s: float = 0.25
    sensor_delay_difference_s: float = 0.0
    bandwidth_calibrated: bool = False
    paired_positions_known: bool = True
    provenance: str = "unspecified"

    def validate(self,times,temporal=False):
        t=np.asarray(times,dtype=float)
        if t.ndim!=1 or len(t)<1 or not np.isfinite(t).all() or (len(t)>1 and np.any(np.diff(t)<=0)):
            raise ValueError("physical timestamps must be finite and strictly increasing")
        if not self.synchronous or not self.paired_positions_known:
            raise ValueError("paired sensing requires synchronized timestamps and actual positions")
        if min(self.clock_error_s,self.maximum_step_s,self.sensor_delay_difference_s)<0:
            raise ValueError("timing uncertainties cannot be negative")
        if temporal:
            if not self.continuous or not self.bandwidth_calibrated:
                raise ValueError("temporal opponent sensing is BLOCKED without continuous clock and sensor calibration")
            if len(t)<3 or np.max(np.diff(t))>self.maximum_step_s*(1+1e-8):
                raise ValueError("sampling gap is too large for the declared temporal operator")
        return t


@dataclass(frozen=True)
class FilterSpec:
    name: str
    lag_s: float = 0.0
    decay_s: float = 0.25
    inhibition: float = 0.0
    bias: float = 0.0
    kind: str = "mnm"


def first_order_sensor(concentration,times,tau_s,initial=None):
    """Exact step response for piecewise constant input; never deconvolves noise."""
    c=np.asarray(concentration,dtype=float)
    t=np.asarray(times,dtype=float)
    if c.shape[-2]!=len(t) or c.shape[-1]!=2 or np.any(np.diff(t)<=0) or tau_s<0:
        raise ValueError("expected [...,time,2], monotone seconds and nonnegative tau")
    if tau_s==0:
        return c.copy()
    y=np.empty_like(c)
    y[...,0,:]=c[...,0,:] if initial is None else initial
    for k in range(1,len(t)):
        a=np.exp(-(t[k]-t[k-1])/tau_s)
        y[...,k,:]=a*y[...,k-1,:]+(1-a)*c[...,k,:]
    return y


def _kernel(t,end,decay):
    support=t<=end+1e-10
    if not np.any(support):
        raise ValueError("lag exceeds actual measured history")
    if len(t)==1:
        return np.ones(1)
    # Quadrature widths matter on a nonuniform real clock.
    dt=np.r_[np.diff(t)[0],np.diff(t)]
    w=np.where(support,np.exp(np.minimum((t-end)/decay,0))*dt,0.)
    return w/w.sum()


class OpponentBank:
    def __init__(self,specs=None,concentration_scale=1.0,background=0.0):
        self.specs=list(specs or [FilterSpec("static_gradient",kind="gradient")])
        self.concentration_scale=float(concentration_scale)
        self.background=float(background)
        if self.concentration_scale<=0 or not self.specs:
            raise ValueError("positive concentration scale and nonempty filter bank required")

    @classmethod
    def causal_default(cls):
        specs=[FilterSpec("static_gradient",kind="gradient")]
        for lag in (0.2,0.5,1.0):
            for inhibition in (0.5,1.0):
                specs.append(FilterSpec(f"delay_{lag:g}_inhibit_{inhibition:g}",lag,0.25,inhibition))
        return cls(specs)

    def extract(self,values,times,contract:SamplingContract):
        x=np.asarray(values,dtype=float)
        if x.ndim<2 or x.shape[-1]!=2 or not np.isfinite(x).all():
            raise ValueError("expected finite paired raw readings [...,time,2]")
        temporal=any(s.kind!="gradient" for s in self.specs)
        t=contract.validate(times,temporal)
        if x.shape[-2]!=len(t):
            raise ValueError("each sensor sample needs its actual timestamp")
        y=np.log1p(np.maximum(x-self.background,0)/self.concentration_scale)
        even=y.mean(axis=(-1,-2))
        L,R=y[...,0],y[...,1]
        features=[]
        for spec in self.specs:
            if spec.kind=="gradient":
                h=(L-R).mean(-1)/2
            else:
                if spec.decay_s<=0 or spec.lag_s<0:
                    raise ValueError("invalid filter timescale")
                uncertainty=contract.clock_error_s+contract.sensor_delay_difference_s
                if spec.lag_s>0 and uncertainty>=spec.lag_s/3:
                    raise ValueError("clock/response mismatch can mimic the filter lag")
                w=_kernel(t,t[-1],spec.decay_s)
                wd=_kernel(t,t[-1]-spec.lag_s,spec.decay_s)
                f1=w-spec.inhibition*wd
                f2=-w
                direct=np.einsum('...t,t->...',L,f1)+np.einsum('...t,t->...',R,f2)+spec.bias
                mirror=np.einsum('...t,t->...',R,f1)+np.einsum('...t,t->...',L,f2)+spec.bias
                h=np.maximum(direct,0)-np.maximum(mirror,0)
            features.append(h)
        return even,np.stack(features,axis=-1)

    def to_dict(self):
        return {"specs":[asdict(s) for s in self.specs],"concentration_scale":self.concentration_scale,"background":self.background}

    @classmethod
    def from_dict(cls,d):
        return cls([FilterSpec(**x) for x in d['specs']],d['concentration_scale'],d['background'])

