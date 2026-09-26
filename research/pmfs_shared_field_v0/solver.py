"""Certified conditional-entropy optimization for smoothed categorical runs.

Same minimax problem as supplied SLSQP prototype. Sparse one-hot channels avoid
materializing A[s,r,m,z]. Entropic mirror ascent uses exact KL projection;
an independent KL linear dual oracle certifies worst risk minus entropy.
There is no target-data interface, probability floor, or sensor noise model.
"""
from dataclasses import dataclass
import time
import numpy as np
from scipy.special import xlogy, rel_entr

@dataclass
class Fit:
    weights: np.ndarray
    posterior: np.ndarray
    entropy: float
    worst_risk: float
    gap: float
    constraint_violation: float
    iterations: int
    seconds: float
    protocol_max_gap: float


def kl_oracle(loss, radius):
    """Batched max_w <w,loss> s.t. KL(w||uniform)<=radius.

    Feasible lower bracket is retained, so the returned weight is not outside
    the KL ball. An upper dual bracket supplies the numerical-risk certificate.
    """
    loss=np.asarray(loss,dtype=np.float64)
    R=loss.shape[-1]
    flat=loss.reshape(-1,R)
    mx=flat.max(1,keepdims=True); span=mx-flat.min(1,keepdims=True)
    g=np.divide(flat-mx,span,out=np.zeros_like(flat),where=span>1e-14)
    tied=np.abs(flat-mx)<=1e-13
    saturated=radius>=np.log(R/tied.sum(1))-1e-12
    constant=span[:,0]<=1e-14
    active=~(saturated|constant)
    out=np.full_like(flat,1/R)
    out[saturated]=tied[saturated]/tied[saturated].sum(1,keepdims=True)
    upper_risk=np.max(flat,axis=1)
    if np.any(active):
        ga=g[active]; fa=flat[active]; spans=span[active,0]
        def stats(beta):
            ew=np.exp(beta[:,None]*ga)
            w=ew/ew.sum(1,keepdims=True)
            kl=np.sum(xlogy(w,R*w),axis=1)
            return w,kl
        lo=np.zeros(len(ga)); hi=np.ones(len(ga))
        for _ in range(30):
            _,kl=stats(hi)
            mask=kl<radius
            if not np.any(mask):break
            hi[mask]*=2
        else:raise RuntimeError("KL dual bracket not found")
        for _ in range(32):
            mid=(lo+hi)/2
            _,kl=stats(mid)
            less=kl<=radius
            lo[less]=mid[less]; hi[~less]=mid[~less]
        w,_=stats(lo)
        out[active]=w
        # eta log mean exp(loss/eta) + eta*rho is an upper bound on
        # the linear worst risk. Work in shifted/scaled g for stability.
        beta=hi
        lme=np.log(np.exp(beta[:,None]*ga).mean(1))
        upper_risk[active]=mx[active,0]+spans*(lme+radius)/beta
    upper_risk[constant]=flat[constant].mean(1)
    return out.reshape(loss.shape),upper_risk.reshape(loss.shape[:-1])


def channel(codes, w, K, independent):
    S,R,M=codes.shape
    a=R/(R+1); b=1/(R+1)/K
    P=np.full((S,M,K),b,dtype=np.float64)
    ss=np.arange(S)[:,None]; mm=np.arange(M)[None,:]
    for r in range(R):
        wr=w[:,:,r] if independent else w[:,r,None]
        P[ss,mm,codes[:,r,:]]+=a*wr
    return P


def q_entropy(P,prior,nu):
    J=prior[:,None,None]*P
    Q=J/J.sum(0,keepdims=True)
    per=-np.sum(J*np.log(Q),axis=(0,2))
    return Q,float(per@nu),per


def run_losses(Q,codes,nu,independent):
    S,R,M=codes.shape; K=Q.shape[-1]
    logq=-np.log(Q); ss=np.arange(S)[:,None];mm=np.arange(M)[None,:]
    selected=np.stack([logq[ss,mm,codes[:,r,:]] for r in range(R)],axis=1)
    losses=R/(R+1)*selected+logq.mean(-1)[:,None,:]/(R+1)
    return losses.transpose(0,2,1) if independent else np.einsum('srm,m->sr',losses,nu)


def line_step(P,D,prior,nu,independent):
    """Concave line search; independent arms use one step per protocol."""
    def derivative(gamma):
        trial=P+D*(gamma[None,:,None] if independent else gamma)
        Q,_,_=q_entropy(trial,prior,nu)
        values=-np.sum(prior[:,None,None]*D*np.log(Q),axis=(0,2))
        return values if independent else float(values@nu)
    if independent:
        lo=np.zeros(P.shape[1]);hi=np.ones(P.shape[1]); end=derivative(hi)
        saturated=end>=0
        for _ in range(18):
            mid=(lo+hi)/2; value=derivative(mid); good=value>=0
            lo[good]=mid[good];hi[~good]=mid[~good]
        lo[saturated]=1
        return lo
    if derivative(1)>=0:return 1.
    lo,hi=0.,1.
    for _ in range(18):
        mid=(lo+hi)/2
        if derivative(mid)>=0:lo=mid
        else:hi=mid
    return lo


def fit(codes,K,radius,independent=False,prior=None,nu=None,tol=2e-6,maxiter=4000,maxseconds=900):
    start=time.perf_counter()
    codes=np.asarray(codes,dtype=np.int64)
    S,R,M=codes.shape
    if np.any(codes<0) or np.any(codes>=K):raise ValueError("invalid channel symbol")
    prior=np.full(S,1/S) if prior is None else np.asarray(prior,dtype=float)
    nu=np.full(M,1/M) if nu is None else np.asarray(nu,dtype=float)
    if np.any(prior<=0) or np.any(nu<=0) or not np.isclose(prior.sum(),1) or not np.isclose(nu.sum(),1):
        raise ValueError("invalid priors")
    w=np.full((S,M,R) if independent else (S,R),1/R,dtype=np.float64)
    eta=1.
    for it in range(maxiter+1):
        P=channel(codes,w,K,independent)
        Q,H,_=q_entropy(P,prior,nu)
        loss=run_losses(Q,codes,nu,independent)
        if radius==0:
            vertex=w; risk=H; gap=0.;permax=0.
        elif it%10==0 or it==maxiter:
            vertex,upper=kl_oracle(loss,radius)
            if independent:
                gap_per=np.sum(prior[:,None]*(upper-np.sum(w*loss,axis=-1)),axis=0)
                gap=float(gap_per@nu);permax=float(gap_per.max())
            else:
                gap=float(prior@(upper-np.sum(w*loss,axis=-1)));permax=gap
            risk=H+gap
        else:
            gap=permax=float('inf');risk=float('inf')
        kl=np.sum(xlogy(w,R*w),axis=-1)
        violation=max(float(np.max(np.abs(w.sum(-1)-1))),float(np.maximum(kl-radius,0).max()))
        if gap<=tol and permax<=tol and violation<=2e-8:
            return Fit(w,Q,H,risk,gap,violation,it,time.perf_counter()-start,permax)
        if time.perf_counter()-start>maxseconds or it==maxiter:
            raise RuntimeError(f"uncertified optimization: it={it}, gap={gap}, max_protocol_gap={permax}, seconds={time.perf_counter()-start}")
        # Entropic mirror ascent. Bregman projection onto the KL ball has
        # w_new=softmax(beta*log(u)), beta in[0,1]. This is the exact prox,
        # not a change to the minimax ambiguity set or its risk certificate.
        for backtrack in range(30):
            logits=np.log(w)+eta*loss
            trial=kl_projection(logits,radius)
            Pnew=channel(codes,trial,K,independent)
            _,Hnew,_=q_entropy(Pnew,prior,nu)
            linear=np.sum((trial-w)*loss,axis=-1)
            div=np.sum(rel_entr(trial,w),axis=-1)
            if independent:
                tangent=float(np.sum(prior[:,None]*nu[None,:]*linear))
                bregman=float(np.sum(prior[:,None]*nu[None,:]*div))
            else:
                tangent=float(prior@linear);bregman=float(prior@div)
            if Hnew>=H+tangent-bregman/eta-1e-12:
                w=trial;eta=min(eta*1.3,1000.);break
            eta/=2
        else:raise RuntimeError('entropy-prox backtracking failed')
    raise AssertionError("unreachable")


def kl_projection(logits,radius):
    """KL-Bregman projection: softmax(beta*logits), feasible beta bracket."""
    shape=logits.shape;R=shape[-1];x=logits.reshape(-1,R)
    x=x-x.max(1,keepdims=True)
    def probs(beta):
        ew=np.exp(beta[:,None]*x)
        w=ew/ew.sum(1,keepdims=True)
        return w,np.sum(xlogy(w,R*w),axis=1)
    out,kl=probs(np.ones(len(x)))
    active=kl>radius
    if np.any(active):
        xa=x[active];lo=np.zeros(len(xa));hi=np.ones(len(xa))
        for _ in range(28):
            mid=(lo+hi)/2;ew=np.exp(mid[:,None]*xa);w=ew/ew.sum(1,keepdims=True)
            kval=np.sum(xlogy(w,R*w),axis=1);less=kval<=radius
            lo[less]=mid[less];hi[~less]=mid[~less]
        ew=np.exp(lo[:,None]*xa);out[active]=ew/ew.sum(1,keepdims=True)
    return out.reshape(shape)
