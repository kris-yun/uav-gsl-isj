"""Ordinary continuous source inversion. No gas truth/source label imports.

Affine puff dynamics are compiled from the same causal local wind prefixes as
LocalPuffFilter. The evaluator receives an arbitrary source coordinate, not
the true one. This module does not know the world identity.
"""
from __future__ import annotations
import numpy as np
from scipy.signal import lfilter
from scipy.special import gammaln
from scipy.optimize import minimize


class CompiledLocalPuffs:
    def __init__(self, observations, physics):
        self.p=physics
        self.length=observations[-1]['tick']+1
        self.rows=[]; self.center=[];self.coeff=[];self.sigma=[];self.sensor_positions=[]
        self.winds=[];self.heights=[]
        # Nontrivial z-to-xyz affine maps for each live puff and mode.
        center=np.zeros((2,0,3)); coeff=center.copy(); sigma=np.empty(0)
        self.readout_positions=np.asarray([o['position_ENU_m'] for o in observations])
        for k,obs in enumerate(observations):
            if k:
                hist=np.asarray(self.winds); h=np.asarray(self.heights)
                dz=h-h.mean(); mean=hist.mean(axis=0)
                slope=(dz[:,None]*(hist-mean)).sum(axis=0)/(dz@dz+25.)
                intercept=mean-slope*h.mean()
                old=self.readout_positions[k-1]; new=self.readout_positions[k]
                for subtick in range(1,11):
                    tick=(k-1)*10+subtick
                    if center.shape[1]:
                        center[0]+=.1*hist[-1]
                        bz=center[1,:,2].copy(); az=coeff[1,:,2].copy()
                        center[1]+=.1*(intercept+bz[:,None]*slope)
                        coeff[1]+=.1*az[:,None]*slope
                        sigma+=.1/(2*sigma)
                    birth=np.zeros((2,1,3)); cbirth=birth.copy();cbirth[:,:,2]=1
                    center=np.concatenate((center,birth),axis=1)
                    coeff=np.concatenate((coeff,cbirth),axis=1)
                    sigma=np.r_[sigma,1.]
                    n=center.shape[1]
                    self.rows.append(np.full(n,tick,dtype=np.int32))
                    self.center.append(center.copy());self.coeff.append(coeff.copy())
                    self.sigma.append(sigma.copy())
                    self.sensor_positions.append(np.broadcast_to(old+(new-old)*(subtick/10),(n,3)).copy())
            self.winds.append(obs['local_wind_m_s']);self.heights.append(obs['position_ENU_m'][2])
        self.tick=np.concatenate(self.rows)
        self.base=np.concatenate(self.center,axis=1)
        self.zcoef=np.concatenate(self.coeff,axis=1)
        self.sigma=np.concatenate(self.sigma)
        positions=np.concatenate(self.sensor_positions)
        self.base-=positions[None,:,:]
        self.invvar=.5/self.sigma**2
        self.norm=1e6*physics['Q_mol_s']*.1/(physics['air_mol_m3']*(2*np.pi)**1.5*self.sigma**3)
        self.calls=0

    def prediction(self, xyz, mode, sensor_model):
        self.calls+=1
        xyz=np.asarray(xyz,float)
        delta=self.base[mode]+xyz[2]*self.zcoef[mode]
        delta=delta.copy();delta[:,:2]+=xyz[:2]
        values=self.norm*np.exp(-np.sum(delta*delta,axis=1)*self.invvar)
        raw=np.bincount(self.tick,weights=values,minlength=self.length)
        if sensor_model=='instantaneous': return raw[::10]
        delayed=np.r_[np.zeros(20),raw[:-20]]
        alpha=-np.expm1(-.1)
        sensed=lfilter([alpha],[1,-(1-alpha)],delayed)
        return sensed[::10]

    def fit(self, measured_excess, mode, sensor_model, starts, settings):
        y=np.asarray(measured_excess,float)
        constant=gammaln(2)-gammaln(1.5)-.5*np.log(3*np.pi)-np.log(.05)
        def objective(xyz):
            residual=(y-self.prediction(xyz,mode,sensor_model))/.05
            return float(np.sum(-constant+2*np.log1p(residual*residual/3)))
        outcomes=[]
        for x0 in starts:
            before=self.calls
            opt=minimize(objective,np.asarray(x0),method='Powell',
                         bounds=[(3370,3490),(4690,4810),(40,100)],
                         options={key:settings[key] for key in ['maxiter','xtol','ftol']}
                                 | {'maxfev':settings['maxfev_per_start']})
            initial=objective(np.asarray(x0))
            # A bounded Powell search can abandon a good narrow initial mode.
            # Retaining the start is a shared ordinary safeguard, frozen here.
            chosen=np.asarray(x0) if initial < opt.fun else opt.x
            outcomes.append({'start_xyz_m':list(map(float,x0)),
                             'estimated_xyz_m':chosen.tolist(),
                             'negative_log_likelihood':float(min(initial,opt.fun)),
                             'optimizer_success':bool(opt.success),
                             'optimizer_message':str(opt.message),
                             'continuous_forward_calls':self.calls-before,
                             'raw_optimizer_xyz_m':opt.x.tolist(),
                             'raw_optimizer_NLL':float(opt.fun)})
        return outcomes
