"""Shared numerical repairs, independent of the proposed biological controller.

These routines repair specific implementation/approximation issues in the
historical prototype. They are not a native S2 backend or a performance claim.
"""
import numpy as np
from scipy.special import logsumexp, log_ndtr

def log_normal_cdf_difference(a, b):
    """log(Phi(b)-Phi(a)) for a <= b, with stable positive-tail evaluation."""
    a,b=np.broadcast_arrays(np.asarray(a,float),np.asarray(b,float))
    if np.any(a>b):raise ValueError('a must not exceed b')
    # For a>0, Phi(b)-Phi(a)=Phi(-a)-Phi(-b).
    lo=np.where(a>0,-b,a); hi=np.where(a>0,-a,b)
    lhi=log_ndtr(hi);llo=log_ndtr(lo)
    with np.errstate(divide='ignore',invalid='ignore'):
        out=lhi+np.log(-np.expm1(llo-lhi))
    return out

def uniform_q_log_marginal(F,y,sigma,qlo=.5,qhi=4.):
    """Exact scalar-q Gaussian likelihood integral for a uniform prior.

    F[S,D] is an existing unit-amplitude response; all sources use the same
    finite, positive q interval. Bounds must be preregistered. q is shared
    over the whole supplied history, not refitted independently per reading.
    Gaussian normalization independent of the source is omitted.
    """
    F=np.asarray(F,float);y=np.asarray(y,float)
    if F.ndim!=2 or y.shape!=(F.shape[1],) or sigma<=0 or not 0<=qlo<qhi:
        raise ValueError('invalid likelihood arguments')
    A=np.sum((F/sigma)**2,axis=1);b=F@(y/sigma**2);c=float(y@y/sigma**2)
    out=np.full(len(F),-.5*c);active=A>1e-14
    aa=A[active];bb=b[active];mu=bb/aa
    # Residual computation avoids c-b^2/A cancellation in near-perfect fits.
    residual=np.sum(((y[None,:]-mu[:,None]*F[active])/sigma)**2,axis=1)
    zlo=(qlo-mu)*np.sqrt(aa);zhi=(qhi-mu)*np.sqrt(aa)
    out[active]=-.5*residual+.5*np.log(2*np.pi/aa)-np.log(qhi-qlo)+log_normal_cdf_difference(zlo,zhi)
    return out

def xy_expected_information(future, posterior, sigma, noise_draws, random_uniform):
    """Finite-MC XY information, marginalizing q and duplicate XY heights.

    The prior on (s,h,q) is already conditional on all actual past data. This
    function counts hypothetical new data once. A finite Monte Carlo estimate
    can be slightly negative; it is deliberately not clipped to hide error.
    """
    future=np.asarray(future,float)
    nsrc=len(posterior.mass);nq=len(posterior.q_values)
    mu=(future[:,None,:,:]*posterior.q_values[None,:,None,None]).reshape(nsrc*nq,-1)
    weights=posterior.joint_source_q.reshape(-1)
    cdf=np.cumsum(weights);cdf[-1]=1.
    u=np.asarray(random_uniform,float)
    if np.any(u<0) or np.any(u>=1):raise ValueError('uniform samples must be in [0,1)')
    sampled=np.searchsorted(cdf,u,side='right')
    outcomes=mu[sampled]+np.asarray(noise_draws)*sigma
    diff=(outcomes[:,None,:]-mu[None,:,:])/sigma
    logw=np.full_like(weights,-np.inf);positive=weights>0;logw[positive]=np.log(weights[positive])
    ll=-.5*np.sum(diff*diff,axis=2)+logw[None,:]
    ls=logsumexp(ll.reshape(len(outcomes),nsrc,nq),axis=2)
    cond=np.exp(ls-logsumexp(ls,axis=1)[:,None])
    _,inverse=np.unique(posterior.sources[:,:2],axis=0,return_inverse=True)
    nxy=inverse.max()+1
    xy0=np.bincount(inverse,weights=posterior.mass,minlength=nxy)
    pxy=np.zeros((len(outcomes),nxy))
    for j in range(nsrc):pxy[:,inverse[j]]+=cond[:,j]
    def entropy(x,axis=-1):return -np.sum(np.where(x>0,x*np.log(np.maximum(x,1e-300)),0),axis=axis)
    return float(entropy(xy0)-np.mean(entropy(pxy)))

def closest_pair_distance(p_i,p_j,v_i,v_j,duration):
    """Exact closest distance for two constant velocities on [0,duration]."""
    r=np.asarray(p_i,float)-p_j;w=np.asarray(v_i,float)-v_j
    ww=float(w@w)
    t=0. if ww<=1e-30 else float(np.clip(-(r@w)/ww,0,duration))
    return float(np.linalg.norm(r+t*w)),t

def continuous_pair_separation_ok(pos,vel,duration,min_separation,tolerance=1e-10):
    for i in range(len(pos)):
        for j in range(i+1,len(pos)):
            d,_=closest_pair_distance(pos[i],pos[j],vel[i],vel[j],duration)
            if d<min_separation-tolerance:return False
    return True

def safe_linear_velocity(v,pos,used,geometry,cfg):
    """Original common-scaling repair with continuous inter-UAV certification.

    Assumes geometry.segment_legal(a,b) certifies the complete segment. If the
    geometry API samples without clearance bounds, its certificate remains
    unqualified. Physical tracking error must be added as a safety margin.
    """
    v=np.asarray(v,float).copy();pos=np.asarray(pos,float);used=np.asarray(used,float)
    if v.shape!=pos.shape or pos.ndim!=2 or pos.shape[1]!=3 or not np.isfinite(v).all():
        raise ValueError('invalid geometry')
    was_commanded=np.linalg.norm(v)>1e-12
    duration=cfg.dt_action*cfg.horizon_steps
    scale=min(1.,float(np.min(cfg.speed_xy_max/np.maximum(np.linalg.norm(v[:,:2],axis=1),1e-12))),
              float(np.min(cfg.speed_z_max/np.maximum(np.abs(v[:,2]),1e-12))))
    v*=scale
    remaining=np.maximum(0,cfg.distance_max_per_uav-used)
    v*=min(1.,float(np.min(remaining/np.maximum(np.linalg.norm(v,axis=1)*duration,1e-12))))
    for fraction in [1.,.75,.5,.25,.125,0.]:
        trial=v*fraction
        if not continuous_pair_separation_ok(pos,trial,duration,cfg.min_separation):continue
        if not all(geometry.segment_legal(p,p+duration*vv) for p,vv in zip(pos,trial)):continue
        if was_commanded and np.linalg.norm(trial)<1e-10:return np.zeros_like(v),False
        return trial,True
    return np.zeros_like(v),False
