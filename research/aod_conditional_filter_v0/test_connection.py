"""Deterministic synthetic checks; not gas-source performance experiments."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from scipy.special import log_ndtr,logsumexp
from gain_innovation_bank import GainInnovationBank, fopdt_template_samples,aggregate_exact_sample_ids

def batch(m,y,t,g0,vg,vd,tc,R,positive):
    T=len(y);K=vd*np.exp(-np.abs(t[:,None]-t[None,:])/tc)+R*np.eye(T)
    cov=K+vg*m[:,None]*m[None,:]
    cf=cho_factor(cov,lower=True);res=y-g0*m
    ll=-.5*(T*np.log(2*np.pi)+2*np.log(np.diag(cf[0])).sum()+res@cho_solve(cf,res))
    if positive:
        ck=cho_factor(K,lower=True);km=cho_solve(ck,m);ky=cho_solve(ck,y)
        v=1/(1/vg+m@km);mu=v*(g0/vg+m@ky)
        ll+=log_ndtr(mu/np.sqrt(v))-log_ndtr(g0/np.sqrt(vg))
    return ll

def main(out):
    checks=[]
    t=np.array([.2,2.6,4.8,9.1,11.4]);y=np.array([0.,1.1,.9,1.8,.7])
    M=np.array([[.1,.4,.3,.8,.2],[.3,.1,.2,.6,.5],[0.,0.,0.,0.,0.]])
    hyper=dict(gain_mean=.8,gain_variance=.7,discrepancy_variance=.4,correlation_time_s=5.,measurement_variance=.2)
    for positive in [False,True]:
        f=GainInnovationBank(np.ones(3),positive_gain=positive,**hyper)
        mx=0.
        for k in range(len(t)):
            r=f.update(k,t[k]-(t[k-1] if k else 0),y[k],M[:,k])
            ref=np.array([batch(m[:k+1],y[:k+1],t[:k+1],.8,.7,.4,5.,.2,positive) for m in M])
            mx=max(mx,float(abs(ref-f.log_evidence).max()))
            assert np.allclose(f.log_evidence,ref,atol=1e-11,rtol=0)
            assert abs(r.source_probability.sum()-1)<1e-13
        checks.append(dict(test=f'prefix_batch_identity_positive_{positive}',max_error=mx,passed=True))
        try:f.update(4,1.,0.,M[:,0]);raise AssertionError('Duplicate accepted')
        except ValueError:checks.append(dict(test=f'duplicate_rejected_{positive}',passed=True))
    # Repeated observations with a shared bias: all inputs are deterministic.
    yy=np.full(20,5.);tt=np.arange(20,dtype=float)
    # tc is not used for this exact constant-bias calculation.
    K=np.eye(20)*.1+np.ones((20,20));cf=cho_factor(K,lower=True)
    ll=np.array([-.5*(yy-u)@cho_solve(cf,yy-u) for u in [5.,6.]])
    q=np.exp(ll-logsumexp(ll))
    independent=np.array([-.5*((yy-u)**2/1.1).sum() for u in [5.,6.]])
    qi=np.exp(independent-logsumexp(independent))
    assert q[0]<.63 and qi[0]>.999
    checks.append(dict(test='shared_bias_example_not_real_data',correlated_q=q.tolist(),independent_q=qi.tolist(),passed=True))
    X=np.array([[0,1],[1,2],[3,1],[2,0],[0,0],[1,4]],float)
    Z=fopdt_template_samples(X,.2,1.2,.4)
    Z2=fopdt_template_samples(3*X,.2,1.2,.4)
    assert np.allclose(Z2,3*Z,atol=1e-15)
    checks.append(dict(test='sensor_linear_gain_homogeneity',max_error=float(abs(Z2-3*Z).max()),passed=True))
    W=aggregate_exact_sample_ids(Z,[[0,1,2],[3,4,5]])
    assert W.shape==(2,2)
    checks.append(dict(test='exact_publication_window_averaging',passed=True))
    try:aggregate_exact_sample_ids(Z,[[0,1],[1,2]]);raise AssertionError()
    except ValueError:checks.append(dict(test='duplicate_raw_samples_rejected',passed=True))
    # AOD is the plug-in / profile component, not identical to Bayesian evidence.
    m=np.array([.2,.6,1.2,.1]); obs=np.array([.1,.8,1.,.3]);a=np.cumsum(m*m);b=np.cumsum(m*obs);c=np.cumsum(obs*obs)
    direct=np.array([np.square(obs[:k]-max(0,b[k-1]/a[k-1])*m[:k]).sum() for k in range(1,5)])
    assert np.allclose(direct,c-b*b/a,atol=1e-15)
    checks.append(dict(test='B2_recursive_sufficient_statistics',passed=True))
    # Collinear templates contain no scale-free source identity.
    ray=np.array([0.,2.,0.,0.]);yr=np.array([0.,3.,0.,0.])
    r1=np.square(yr-ray*(yr@ray)/(ray@ray)).sum();r2=np.square(yr-7*ray*(yr@(7*ray))/((7*ray)@(7*ray))).sum()
    assert r1==0 and r2==0
    checks.append(dict(test='no_EPS_injected_source_identity',passed=True))
    result=dict(checks=checks,n=len(checks),all_pass=True,scope='Deterministic algebra and software only; no real filter localization scoring or calibration.')
    Path(out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    import sys;main(sys.argv[1])
