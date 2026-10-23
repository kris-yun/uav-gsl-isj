"""Analytical paired-sensor backend for Level 1 only.

An intermittent 2-D Gaussian footprint plus a shared moving patch is useful
for exercising synchronization, real clocks and correlation. It is NOT
GADEN, a validated lake model, ROS, CFD, or a source-localization result.
"""
from __future__ import annotations
import os
import numpy as np
from ..m1_opponent import first_order_sensor,SamplingContract


class ControlledPlume:
    def __init__(self,sources,actions,times=None):
        self.sources=np.asarray(sources,dtype=float);self.actions=list(actions)
        self.times=np.arange(21)*.1 if times is None else np.asarray(times)
        self.wind_angles=np.array([-.18,0.,.18])
        self.contract=SamplingContract(continuous=True,maximum_step_s=.101,
             bandwidth_calibrated=True,provenance="CONTROLLED_ANALYTICAL_SECONDS_NOT_NATIVE_GADEN")

    def mean_response(self,points,source,mechanism):
        src=self.sources[source]; x=np.asarray(points)-src
        angle=self.wind_angles[mechanism]
        wind=np.array([np.cos(angle),np.sin(angle)]); cross=np.array([-wind[1],wind[0]])
        along=x@wind;across=x@cross
        width=.65+.25*np.maximum(along,0)
        mu=9*np.exp(-.5*(across/width)**2)/(1+np.maximum(along,0))
        return np.where(along>0,mu,.03*np.exp(-np.linalg.norm(x,axis=-1)))

    def observe(self,action,source,mechanism,rng,physical_start_s=0.):
        a=self.actions[action];points=a.points
        mu=self.mean_response(points,source,mechanism)
        t=self.times; values=np.empty((len(t),2))
        # Shared low-frequency intermittency, plus individual innovations.
        # Blocks are conditionally independent given (source,mechanism).
        shared=np.zeros(len(t));shared[0]=rng.normal()
        for k in range(1,len(t)):shared[k]=.75*shared[k-1]+.5*rng.normal()
        phase=rng.uniform(-np.pi,np.pi)
        direction=np.array([-np.sin(self.wind_angles[mechanism]),np.cos(self.wind_angles[mechanism])])
        offset=(points-self.sources[source])@direction
        for sensor in range(2):
            moving=np.sin(3*t+phase-offset[sensor])
            values[:,sensor]=mu[sensor]*np.exp(.4*shared+.3*moving-.15)+rng.normal(0,.05,len(t))
        values=np.maximum(values,0)
        values=first_order_sensor(values,t,.18)
        return values,t+physical_start_s

    def calibration(self,n_worlds=48,seed=7721):
        rng=np.random.default_rng(seed)
        a,s,r=len(self.actions),len(self.sources),len(self.wind_angles)
        if not isinstance(n_worlds,int) or n_worlds<2:raise ValueError('at least two calibration blocks per state required')
        required_bytes=a*s*r*n_worlds*len(self.times)*2*8
        limit=float(os.environ.get('GSL_V7_MAX_CALIBRATION_MB','512'))*1024**2
        if not np.isfinite(limit) or limit<=0 or required_bytes>limit:
            raise MemoryError('calibration exceeds declared GSL_V7_MAX_CALIBRATION_MB; split the native design before allocation')
        data=np.empty((a,s,r,n_worlds,len(self.times),2))
        for i in range(a):
            for j in range(s):
                for k in range(r):
                    for w in range(n_worlds):data[i,j,k,w]=self.observe(i,j,k,rng)[0]
        return data

    def response_geometry(self,centers,mechanism=1,epsilon=.05):
        q=np.asarray(centers)
        means=np.stack([self.mean_response(q,s,mechanism) for s in range(len(self.sources))],axis=1)
        gradients=np.zeros((len(q),len(self.sources),2))
        for k in range(2):
            e=np.eye(2)[k]*epsilon
            gradients[:,:,k]=np.stack([(self.mean_response(q+e,s,mechanism)-self.mean_response(q-e,s,mechanism))/(2*epsilon)
                                       for s in range(len(self.sources))],axis=1)
        return means,gradients

