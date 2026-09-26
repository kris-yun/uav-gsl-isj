#!/usr/bin/env python3
"""
QA-PMFS V0 core likelihood.

For candidate source s and event marginals p_e(s), introduce a latent
episode environment Z~N(0,1).  For rho in [0,1):

    U_e = sqrt(rho) Z + sqrt(1-rho) eps_e
    H_e = 1[U_e <= Phi^{-1}(p_e)]

Then P(H_e=1|s)=p_e exactly, for every event.  Only the joint dependence
changes.  rho=0 exactly recovers the independent Bernoulli likelihood.

For time-block length L, one latent Z is shared inside each consecutive block
of L time slices.  L=T is the quasi-quenched episode model.
"""
import math, numpy as np
from scipy.special import ndtr, ndtri, logsumexp
from numpy.polynomial.hermite import hermgauss

def marginal_preserving_probit_loglik(hits, probs, rho, groups=None, gh_n=40):
    hits=np.asarray(hits,dtype=np.int8).reshape(-1)
    probs=np.clip(np.asarray(probs,dtype=float).reshape(-1),1e-8,1-1e-8)
    if groups is None:
        groups=np.zeros(len(hits),dtype=int)
    groups=np.asarray(groups)
    if rho==0:
        return float((hits*np.log(probs)+(1-hits)*np.log1p(-probs)).sum())
    x,w=hermgauss(gh_n)
    z=np.sqrt(2.0)*x
    logw=np.log(w)-0.5*np.log(np.pi)
    tau=ndtri(probs)
    sr=math.sqrt(rho); s1=math.sqrt(1-rho)
    total=0.0
    for g in np.unique(groups):
        m=groups==g
        cond=ndtr((tau[m][None,:]-sr*z[:,None])/s1)
        cond=np.clip(cond,1e-15,1-1e-15)
        yy=hits[m]
        lf=(yy[None,:]*np.log(cond)+(1-yy)[None,:]*np.log1p(-cond)).sum(axis=1)
        total += float(logsumexp(logw+lf))
    return total

def independent_loglik(hits, probs):
    return marginal_preserving_probit_loglik(hits,probs,0.0)

if __name__=="__main__":
    # deterministic identity check
    h=np.array([0,1,0,1],dtype=np.int8)
    p=np.array([0.1,0.3,0.8,0.6])
    a=independent_loglik(h,p)
    b=marginal_preserving_probit_loglik(h,p,0.0)
    assert abs(a-b)<1e-12
    print("QA_PMFS_CORE_SELFTEST_PASS")
