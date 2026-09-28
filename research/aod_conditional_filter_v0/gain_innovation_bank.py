"""Ordinary, exact linear-Gaussian reference for AOD-conditioned source inference.

NOT a new UKF algorithm or a calibrated deployable model. All prior/noise
parameters are explicit constructor arguments and must be fixed from legitimate
calibration/OPEN training, not from a test source or its outcomes.

Observation: y_t = m_s(t) * g + d_t + noise_t.
  m_s(t): an AOD template already passed through the actual sensor/window map.
  g: ONE static gain for the whole episode, NOT re-fitted independently each t.
  d_t: an event-level, stationary AR(1) model-discrepancy working state.
  noise: common specified variance across candidates.
Optional g>=0 is handled by exact Gaussian half-space normalization, not clipping.
The internally stored Gaussian is an ENVELOPE, not the moments of its truncation.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.special import log_ndtr, logsumexp

@dataclass
class Update:
    source_probability: np.ndarray
    predictive_log_likelihood: np.ndarray
    gaussian_envelope_prediction: np.ndarray
    gaussian_envelope_innovation_variance: np.ndarray

class GainInnovationBank:
    def __init__(self, source_prior, *, gain_mean: float, gain_variance: float,
                 discrepancy_variance: float, correlation_time_s: float,
                 measurement_variance: float, positive_gain: bool):
        p=np.asarray(source_prior,dtype=float)
        vals=np.array([gain_mean,gain_variance,discrepancy_variance,
                       correlation_time_s,measurement_variance],dtype=float)
        if p.ndim!=1 or not len(p) or not np.isfinite(p).all() or (p<=0).any():
            raise ValueError('Explicit strictly positive candidate prior required')
        if not np.isfinite(vals).all() or gain_variance<=0 or discrepancy_variance<0 or correlation_time_s<=0 or measurement_variance<=0:
            raise ValueError('Invalid prior/noise contract; no automatic variance floor')
        self.n=len(p);self.logq=np.log(p/p.sum())
        self.mu=np.zeros((self.n,2));self.mu[:,0]=gain_mean
        self.P=np.broadcast_to(np.diag([gain_variance,discrepancy_variance]),(self.n,2,2)).copy()
        self.vd=discrepancy_variance;self.tc=correlation_time_s;self.R=measurement_variance
        self.positive=bool(positive_gain);self.last_id=-1;self.log_evidence=np.zeros(self.n)

    def update(self, event_id: int, dt_s: float, measured_y: float, template):
        m=np.asarray(template,dtype=float)
        if event_id<=self.last_id:raise ValueError('Duplicate/out-of-order event')
        if not np.isfinite(dt_s) or dt_s<0 or not np.isfinite(measured_y):raise ValueError('Invalid time/observation')
        if m.shape!=(self.n,) or not np.isfinite(m).all() or (m<0).any():raise ValueError('Candidate alignment/finite/nonnegative template required')
        phi=np.exp(-dt_s/self.tc);F=np.diag([1.,phi])
        mu=self.mu@F.T
        P=np.einsum('ij,sjk,lk->sil',F,self.P,F)
        P[:,1,1]+=self.vd*(-np.expm1(-2*dt_s/self.tc))
        H=np.column_stack([m,np.ones(self.n)])
        hp=np.einsum('si,sij->sj',H,P)
        var=np.einsum('si,si->s',hp,H)+self.R
        if (var<=0).any() or not np.isfinite(var).all():raise FloatingPointError('Invalid innovation covariance')
        pred=np.einsum('si,si->s',H,mu);err=measured_y-pred
        K=hp/var[:,None]
        post=mu+K*err[:,None]
        # Joseph covariance form; no template EPS and no arbitrary covariance repair.
        IKH=np.eye(2)[None,:,:]-K[:,:,None]*H[:,None,:]
        postP=np.einsum('sij,sjk,slk->sil',IKH,P,IKH)+self.R*K[:,:,None]*K[:,None,:]
        postP=.5*(postP+postP.transpose(0,2,1))
        logL=-.5*(np.log(2*np.pi*var)+err*err/var)
        if self.positive:
            if (postP[:,0,0]<=0).any() or (P[:,0,0]<=0).any():raise FloatingPointError('Degenerate gain posterior')
            logL+=log_ndtr(post[:,0]/np.sqrt(postP[:,0,0]))-log_ndtr(mu[:,0]/np.sqrt(P[:,0,0]))
        if not np.isfinite(logL).all():raise FloatingPointError('Nonfinite predictive evidence')
        self.log_evidence+=logL
        lq=self.logq+logL;self.logq=lq-logsumexp(lq)
        self.mu=post;self.P=postP;self.last_id=event_id
        return Update(np.exp(self.logq).copy(),logL,pred,var)


def fopdt_template_samples(inputs, dt_s: float, tau_s: float, dead_time_s: float):
    """Causal symmetric FOPDT mean operator, independent of source labels.

    inputs has shape (raw_sample_time, candidate). It MUST include motion-time
    positions, not only dwell events. Zero initial state and input are assumed.
    No noise draws, clipping, rescaling, or fitted hyperparameters are used.
    For actual asymmetric or saturating sensors use the actual process instead.
    """
    x=np.asarray(inputs,float)
    if x.ndim!=2 or not np.isfinite(x).all() or (x<0).any():raise ValueError('Invalid templates')
    if dt_s<=0 or tau_s<0 or dead_time_s<0:raise ValueError('Invalid sensor contract')
    output=np.empty_like(x);r=np.zeros(x.shape[1]);times=[0.];clock=0.
    a=0. if tau_s==0 else np.exp(-dt_s/tau_s)
    for k in range(len(x)):
        clock+=dt_s;times.append(clock);q=clock-dead_time_s
        if q<=0: delayed=np.zeros(x.shape[1])
        elif q>=times[-1]:delayed=x[k]
        else:
            hi=int(np.searchsorted(times,q,side='left'));lo=hi-1
            vl=np.zeros(x.shape[1]) if lo==0 else x[lo-1]
            vh=x[hi-1];w=(q-times[lo])/(times[hi]-times[lo]);delayed=vl+w*(vh-vl)
        r=a*r+(1-a)*delayed;output[k]=r
    return output


def aggregate_exact_sample_ids(samples, groups):
    a=np.asarray(samples,float);seen=set();rows=[]
    for group in groups:
        ids=np.asarray(group,dtype=int)
        if ids.ndim!=1 or not len(ids) or len(np.unique(ids))!=len(ids) or (ids<0).any() or (ids>=len(a)).any():raise ValueError('Invalid raw publication IDs')
        if any(int(i) in seen for i in ids):raise ValueError('Repeated raw publication across event windows')
        seen.update(map(int,ids));rows.append(a[ids].mean(axis=0))
    return np.stack(rows)
