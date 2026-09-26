"""Finite-alphabet prototype of a shared-realization robust source channel.

This is NOT a GADEN implementation and NOT a scientific experiment.
Input A[s,r,m,z] is an explicitly supplied, normalized observation channel:
source s, whole-realization r, observation protocol m, observation symbol z.
The same realization weight is used for every m. Positivity must be supplied
by the declared observation model; this module does not add a posterior floor.

Dependencies: numpy, scipy. Solver: deterministic SLSQP; output includes an
independent worst-case risk certificate, not only optimizer.success.
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize, brentq
from scipy.special import logsumexp, xlogy

@dataclass
class Fit:
    weights: np.ndarray
    posterior: np.ndarray
    least_favorable_entropy: float
    worst_case_risk: float
    saddle_gap: float
    max_constraint_violation: float
    iterations: int


def _validate(A, prior, protocol_prior, radius):
    A = np.asarray(A, dtype=float)
    if A.ndim != 4 or not np.isfinite(A).all() or (A <= 0).any():
        raise ValueError('A must be finite, strictly positive, and have shape S,R,M,Z; no automatic smoothing.')
    if not np.allclose(A.sum(-1), 1., atol=1e-11, rtol=1e-11):
        raise ValueError('Every observation-channel row must sum to one.')
    S,R,M,Z=A.shape
    p=np.asarray(prior,dtype=float); v=np.asarray(protocol_prior,dtype=float)
    if p.shape!=(S,) or v.shape!=(M,) or (p<=0).any() or (v<=0).any():
        raise ValueError('Positive priors of matching dimension are required.')
    if not np.isclose(p.sum(),1.) or not np.isclose(v.sum(),1.):
        raise ValueError('Priors must be normalized; they are never silently changed.')
    rho=np.broadcast_to(np.asarray(radius,dtype=float),(S,)).copy()
    if not np.isfinite(rho).all() or (rho<0).any(): raise ValueError('Invalid KL radius.')
    return A,p,v,rho


def posterior_and_entropy(A,p,v,w):
    P=np.einsum('sr,srmz->smz',w,A)
    J=p[:,None,None]*P
    Q=J/J.sum(axis=0,keepdims=True)
    H=-np.sum(v[None,:,None]*J*np.log(Q))
    return Q,float(H)


def worst_kl_expectation(loss, radius):
    """Independent linear risk maximization over KL(w||uniform)<=radius."""
    loss=np.asarray(loss,dtype=float); R=len(loss)
    if radius<=1e-14:return float(loss.mean())
    mx=loss.max(); tied=np.isclose(loss,mx,rtol=0,atol=1e-13)
    if radius >= np.log(R/tied.sum())-1e-13:return float(mx)
    spread=loss.max()-loss.min()
    if spread<=1e-14:return float(mx)
    z=(loss-mx)/spread
    def stats(beta):
        logw=beta*z-logsumexp(beta*z)
        w=np.exp(logw)
        return float(np.sum(xlogy(w,w*R))),float(w@loss)
    upper=1.
    while stats(upper)[0]<radius: upper*=2.
    beta=brentq(lambda b:stats(b)[0]-radius,0.,upper,xtol=1e-12)
    return stats(beta)[1]


def fit_shared(A, prior, protocol_prior, radius, maxiter=2000, tol=1e-10):
    A,p,v,rho=_validate(A,prior,protocol_prior,radius)
    S,R,M,Z=A.shape
    def report(w,nit):
        Q,H=posterior_and_entropy(A,p,v,w)
        loss=np.einsum('srmz,smz,m->sr',A,-np.log(Q),v)
        worst=float(sum(p[s]*worst_kl_expectation(loss[s],rho[s]) for s in range(S)))
        kl=np.sum(xlogy(w,R*w),axis=1)
        violation=max(float(np.max(np.abs(w.sum(1)-1.))),float(np.maximum(kl-rho,0).max()))
        return Fit(w,Q,H,worst,worst-H,violation,nit)
    if np.all(rho==0):return report(np.full((S,R),1/R),0)
    if np.any(rho==0):raise ValueError('For this minimal prototype use all-zero or all-positive radii.')
    def objective(x):
        w=x.reshape(S,R); Q,H=posterior_and_entropy(A,p,v,w)
        gradH=-p[:,None]*np.einsum('srmz,smz,m->sr',A,np.log(Q),v)
        return -H,-gradH.ravel()
    def eq(x):return x.reshape(S,R).sum(1)-1.
    def ineq(x):
        w=x.reshape(S,R);return rho-np.sum(xlogy(w,R*w),axis=1)
    # The tiny lower bound is a numerical interior restriction on realization
    # weights, NOT a floor added to the source posterior. Certificate checks it.
    result=minimize(objective,np.full(S*R,1/R),jac=True,method='SLSQP',
                    bounds=[(1e-12,1.)]*(S*R),
                    constraints=[{'type':'eq','fun':eq},{'type':'ineq','fun':ineq}],
                    options={'maxiter':maxiter,'ftol':tol,'disp':False})
    fit=report(result.x.reshape(S,R),result.nit)
    if not result.success or fit.max_constraint_violation>2e-7 or fit.saddle_gap>2e-6:
        raise RuntimeError(f'Uncertified optimization: {result.message}; violation={fit.max_constraint_violation}; gap={fit.saddle_gap}')
    return fit
