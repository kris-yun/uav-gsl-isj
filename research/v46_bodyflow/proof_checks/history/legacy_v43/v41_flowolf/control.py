"""M1/M3 executable two-path controller with shared ordinary inference.

BIO is an algorithmic *candidate*: its main operator is identity-preserving
stage-conditioned action proposal; nuisance projection, EIG and GLS are
ordinary statistics and retained as a strong identical-model baseline.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import numpy as np
from scipy.special import logsumexp
from .types import Configuration, Reading, Trajectory
from .encoder import Signature, encode
from .physics import ForwardModel, speculative_path
from .inference import Posterior, joint_posterior


class OpenGeometry:
    """Unrestricted synthetic demo geometry; NEVER certifies S2 legality."""
    def segment_legal(self, a, b):
        return bool(np.all(np.isfinite(a)) and np.all(np.isfinite(b)))


def _safe_velocity(v: np.ndarray, pos: np.ndarray, used: np.ndarray,
                   geometry, cfg: Configuration) -> tuple[np.ndarray,bool]:
    """Group line-search with 0.1-s substeps, path budgets, separation & geometry."""
    v=np.asarray(v,float)
    n=len(pos)
    if v.shape!=(n,3) or not np.isfinite(v).all():raise ValueError('bad velocity')
    was_commanded=bool(np.linalg.norm(v)>1e-12)
    limits=cfg.speed_xy_max/np.maximum(np.linalg.norm(v[:,:2],axis=1),1e-12)
    zlimits=cfg.speed_z_max/np.maximum(np.abs(v[:,2]),1e-12)
    scale=min(1.,float(limits.min()),float(zlimits.min()))
    v=v*scale
    remaining=np.maximum(0,cfg.distance_max_per_uav-used)
    if np.linalg.norm(v,axis=1).max()>0:
        allowed=np.min(remaining/np.maximum(np.linalg.norm(v,axis=1)*cfg.dt_action*cfg.horizon_steps,1e-12))
        v*=min(1.,float(allowed))
    # In native S2 we must NOT repair an illegal path based on hidden field.
    for fraction in [1.,.75,.5,.25,.125,0.]:
        trial=v*fraction
        ok=True
        delta=cfg.dt_action/10.
        for f in np.linspace(0,cfg.dt_action*cfg.horizon_steps,10*cfg.horizon_steps+1):
            here=pos+trial*f
            for i in range(n):
                if not geometry.segment_legal(pos[i]+trial[i]*max(0,f-delta),here[i]):
                    ok=False;break
            if not ok:break
            for i in range(n):
                for j in range(i+1,n):
                    if np.linalg.norm(here[i]-here[j]) < cfg.min_separation-1e-8:
                        ok=False;break
                if not ok:break
            if not ok:break
        if ok:
            # A clipped-to-zero non-hover command is not a successful move;
            # otherwise action-name metrics would report fictitious sampling.
            if was_commanded and np.linalg.norm(trial)<1e-10:
                return np.zeros_like(v),False
            return trial,True
    return np.zeros_like(v),False


def _physical_order(pos: np.ndarray, along: np.ndarray, cross: np.ndarray) -> np.ndarray:
    """Permutation-equivariant receptor ordering by real ENU/wind geometry.

    Distinct sensor positions are required by the flight separation contract.
    Merely permuting array rows must permute assigned motor commands, not
    change the action in world coordinates.
    """
    d=np.asarray(pos,float)-np.asarray(pos,float).mean(axis=0)
    along_coord=d[:,:2]@along
    cross_coord=d[:,:2]@cross
    return np.lexsort((d[:,2],along_coord,cross_coord))


def _bipolar_motor_score(sig: Signature, action: Trajectory, speed: float=.9)->float:
    """Source-independent IN/OUT-to-motor alignment; bounded and cheap.

    The mapping is an *engineering hypothesis* motivated by differentiated
    biological motor projections, not a claim about zebrafish motor decoding.
    A shared action library is mandatory for BIO/noidentity comparisons.
    """
    if sig.contact_count==0 or sig.stage in ('wind_weak','invalid'):
        return 0.
    v=np.asarray(action.velocity,float)
    loc=sig.effective_positions
    d=loc-loc.mean(axis=0)
    n=d/np.maximum(np.linalg.norm(d,axis=1,keepdims=True),1e-9)
    relative=v-v.mean(axis=0)
    radial_motion=np.einsum('ij,ij->i',relative,n)
    # Positive outflow favors relative expansion; inflow favors contraction.
    # Zero for whole-team translations (tested), so the primitive differs
    # from ordinary EIG only when identity-conditioned reconfiguration matters.
    balance=sig.outward_flow-sig.inward_flow
    denominator=(np.sum(sig.outward_flow+sig.inward_flow)+1e-9)*max(speed,1e-9)
    return float(np.clip(np.dot(balance,radial_motion)/denominator,-1.,1.))


def all_actions(b: Reading, sig: Signature, t: float, speed=.9) -> list[Trajectory]:
    p=b.pos;n=len(p)
    u=sig.wind_along;c=sig.wind_cross
    center=p.mean(axis=0)
    d=p[:,:2]-center[:2]
    proj=d@c
    indexed=_physical_order(p,sig.wind_along,sig.wind_cross)
    rank=np.empty(n,dtype=float);rank[indexed]=np.linspace(-1.,1.,n)
    rank-=rank.mean()
    def tri(name,velocity,family,reason):
        return Trajectory(name,np.asarray(velocity,float),family,reason)
    def trans(name,xy=(0.,0.),z=0.):
        v=np.repeat([[*xy,z]],n,axis=0)*speed
        return tri(name,v,'translation','ordinary whole-team translation')
    actions=[tri('hover',np.zeros((n,3)),'safe','safest available fallback'),
             trans('translate_upwind',-u),trans('translate_downwind',u),
             trans('translate_cross+',c),trans('translate_cross-',-c),
             trans('translate_z+',z=0.6),trans('translate_z-',z=-0.6)]
    span=rank[:,None]*c[None,:]*speed
    v=np.c_[span,np.zeros(n)]
    actions.append(tri('reconfigure_cross',v,'reconfiguration','source-free wind-normal split'))
    actions.append(tri('reconfigure_cross_reverse',-v,'reconfiguration','flank shrink/return'))
    # V41 main candidate: the identity-preserving flow/odor signal biases each
    # physical receptor's relative movement, while the missing-motion axis
    # complements previously sampled relative positions. SOURCE-INDEPENDENT.
    gap=sig.missing_axis
    scores=d@gap
    order=_physical_order(p,sig.wind_along,gap)
    ranks=np.empty(n,dtype=float);ranks[order]=np.linspace(-1.,1.,n)
    # A fixed, receptor-identity-neutral action library: BIO and the
    # noidentity control see exactly the same trajectory vectors.  Identity
    # enters only via the separated M1 motor-readout bonus in the scorer.
    move=ranks[:,None]*gap[None,:]
    move-=move.mean(axis=0)
    vgap=np.c_[speed*move,np.zeros(n)]
    actions.append(tri('reconfigure_gap_indexed',vgap,'reconfiguration',
                       'identity-specific flow and olfaction along under-sampled axis'))
    actions.append(tri('reconfigure_gap_reverse',-vgap,'reconfiguration',
                       'identity-indexed complementary inverse action'))
    # 2D full-rank deformation for N>=3; geometry is not a source certificate.
    if n>=3:
        physical_order=_physical_order(p,u,c)
        angles=2*np.pi*np.arange(n)/n
        simplex=np.c_[np.cos(angles),np.sin(angles)]
        xy=np.zeros((n,2),float)
        xy[physical_order]=speed*(simplex@np.stack([u,c]))
        actions.append(tri('reconfigure_2d_rank',np.c_[xy,np.zeros(n)],'reconfiguration',
                           'two-dimensional relative-motion Gram rank proposal'))
        actions.append(tri('reconfigure_2d_reverse',np.c_[-xy,np.zeros(n)],'reconfiguration',
                           'reverse 2D relative motion'))
    # Signal asymmetry only used to generate direction, not as likelihood.
    if sig.contact_count:
        shift=np.sign(sig.eccentricity)*speed*.8*c
        actions.append(trans('recenter_on_contact',shift/speed))
    return actions


def shortlisted_actions(actions: list[Trajectory], sig: Signature, mode: str) -> list[Trajectory]:
    by={a.name:a for a in actions}
    names=[]
    if mode in ('ordinary_eig','ordinary_projected',
                'ordinary_eig_full','ordinary_projected_full'):return actions
    if mode=='ordinary_coverage':
        names=['translate_cross+','translate_cross-','translate_upwind','translate_z+']
    elif mode=='bio_noflow':
        names=['reconfigure_2d_rank','reconfigure_2d_reverse','translate_z+','hover']
    elif mode=='bio_nogap':
        names=['reconfigure_cross','reconfigure_cross_reverse',
               'reconfigure_2d_rank','translate_upwind','hover']
    elif sig.stage in ('precontact','wind_weak','invalid'):
        names=['reconfigure_gap_indexed','reconfigure_cross','translate_cross+',
               'translate_cross-','translate_z+','hover']
    elif sig.stage=='partial':
        names=['reconfigure_gap_indexed','reconfigure_gap_reverse',
               'reconfigure_cross_reverse','recenter_on_contact','translate_upwind',
               'reconfigure_2d_rank','hover']
    elif sig.stage=='section':
        names=['reconfigure_gap_indexed','reconfigure_gap_reverse',
               'reconfigure_2d_rank','reconfigure_2d_reverse',
               'translate_upwind','translate_downwind','hover']
    else:
        names=['reconfigure_gap_indexed','reconfigure_2d_rank','reconfigure_cross',
               'translate_upwind','translate_z+','hover']
    return [by[x] for x in names if x in by]


def _project_source_information(F0:np.ndarray, Fs_perturbed:np.ndarray,
                                qmean:float,sigma:float,eps:float,
                                height_sensitivity:np.ndarray|None=None) -> tuple[float,int]:
    """Whitened Schur complement to UNKNOWN q (ordinary conditional Fisher).

    F0: [H,N], perturbed order s±eps e_x,s±eps e_y.
    Note: this is for *future conditional observables*, not source posterior.
    """
    y=np.asarray(F0).ravel()
    f=np.asarray(Fs_perturbed).reshape(4,-1)
    J=qmean*np.c_[(f[0]-f[1])/(2*eps),(f[2]-f[3])/(2*eps)]/sigma
    nuisance=(y/sigma).reshape(-1,1)
    if height_sensitivity is not None:
        nuisance=np.c_[nuisance,np.asarray(height_sensitivity).ravel()*qmean/sigma]
    active=nuisance[:,np.linalg.norm(nuisance,axis=0)>1e-12]
    projection=(np.eye(len(y))-active@np.linalg.pinv(active) if active.shape[1]
                else np.eye(len(y)))
    I=J.T@projection@J
    eig=np.linalg.eigvalsh(I)
    return float(max(0.,eig.min())),int(np.sum(eig>1e-6))


def _future_legal(v:np.ndarray, pos:np.ndarray, used:np.ndarray, horizon_steps:int,
                  geometry, cfg:Configuration)->bool:
    """Every intermediate 0.1-s position in the PROPOSED future planning path."""
    dt=cfg.dt_action
    speed=np.linalg.norm(v,axis=1)
    if np.any(used+speed*(dt*horizon_steps)>cfg.distance_max_per_uav+1e-8):return False
    for f in np.linspace(0,dt*horizon_steps,10*horizon_steps+1):
        here=pos+v*f
        for i in range(len(here)):
            if not geometry.segment_legal(pos[i]+v[i]*max(0,f-.1*dt),here[i]):return False
            for j in range(i+1,len(here)):
                if np.linalg.norm(here[i]-here[j])<cfg.min_separation-1e-8:return False
    return True


def _pairs(p: Posterior, count:int) -> list[tuple[int,int]]:
    # Never use truth; posterior and XY grid only.
    order=np.argsort(-p.mass)
    inds=order[:min(len(order),max(4,count))]
    pairs=[]
    for a in inds:
        for b in inds:
            if b>a and np.linalg.norm(p.sources[a,:2]-p.sources[b,:2])>1.e-6:
                pairs.append((int(a),int(b)))
    pairs.sort(key=lambda ij:-p.mass[ij[0]]*p.mass[ij[1]]*
               np.linalg.norm(p.sources[ij[0],:2]-p.sources[ij[1],:2]))
    return pairs[:count]


def _bounded_q_pair_distance(a:np.ndarray,b:np.ndarray,lo:float,hi:float)->float:
    """Exact two-interval convex quadratic minimization on four box edges.

    If lo==0, both sources can choose zero emissions, hence distance=0.
    The interval is a frozen nuisance PRIOR assumption; not inferred truth.
    """
    a=np.asarray(a).ravel();b=np.asarray(b).ravel()
    if lo<0 or hi<lo:raise ValueError('invalid profile interval')
    if lo==0:return 0.
    def value(q1,q2):return float(np.linalg.norm(q1*a-q2*b))
    best=min(value(i,j) for i in (lo,hi) for j in (lo,hi))
    aa=max(1e-25,float(a@a));bb=max(1e-25,float(b@b));ab=float(a@b)
    for q1 in (lo,hi):
        q2=np.clip(q1*ab/bb,lo,hi)
        best=min(best,value(q1,q2))
    for q2 in (lo,hi):
        q1=np.clip(q2*ab/aa,lo,hi)
        best=min(best,value(q1,q2))
    return max(0.,best)


def _pair_profile_margin(future: np.ndarray, p: Posterior,
                         cfg: Configuration) -> float:
    """Weighted bounded-q *proposal score*, not an unconditional certificate.

    q range is a frozen modeling assumption; model error bound is an additional
    and separate requirement. Freely allowing q=0 makes global separation 0.
    """
    fm=np.asarray(future).reshape(len(p.mass),-1)/cfg.sensor_sigma
    lo=min(cfg.q_values);hi=max(cfg.q_values)
    vals=[]
    for i,j in _pairs(p,cfg.source_pair_count):
        margin=_bounded_q_pair_distance(fm[i],fm[j],lo,hi)
        vals.append((p.mass[i]*p.mass[j],margin))
    if not vals:return 0.
    return float(sum(x*y for x,y in vals)/max(1e-12,sum(x for x,_ in vals)))


def _estimate_eig(future:np.ndarray, posterior:Posterior,
                  cfg:Configuration, noise_draws:np.ndarray,
                  random_uniform:np.ndarray) -> float:
    """Ordinary joint (source,q) Monte-Carlo expected XY entropy reduction.

    Every action uses identical pseudo-random draws (common-random-number fair
    comparison). Whole posterior q is shared; no bio score enters likelihood.
    """
    nsrc=len(posterior.mass);nq=len(posterior.q_values)
    mu=(future[:,None,:,:]*posterior.q_values[None,:,None,None]).reshape(nsrc*nq,-1)
    weights=posterior.joint_source_q.reshape(-1)
    cdf=np.cumsum(weights);cdf[-1]=1.
    sampled=np.searchsorted(cdf,random_uniform,side='right')
    outcomes=mu[sampled]+noise_draws*cfg.sensor_sigma
    # [draw,source*q,dim] memory bounded by small design horizon.
    d=(outcomes[:,None,:]-mu[None,:,:])/cfg.sensor_sigma
    ll=-.5*np.sum(d*d,axis=2)+np.log(np.maximum(weights,1e-300))[None,:]
    ll=ll.reshape(len(outcomes),nsrc,nq)
    logsource=logsumexp(ll,axis=2)
    cond=np.exp(logsource-logsumexp(logsource,axis=1)[:,None])
    entropy=-np.sum(cond*np.log(np.maximum(cond,1e-300)),axis=1)
    return float(max(0.,posterior.entropy-np.mean(entropy)))


@dataclass(frozen=True)
class ActionDecision:
    action: Trajectory
    stage: str
    reason: str
    proposal_count: int
    qualified: bool
    source_rank: int
    projected_min_eigenvalue: float
    pair_margin: float
    ordinary_eig: float
    model_bound: float | None
    forward_calls: int
    evaluated: tuple


class Controller:
    """Shared backend; BIO differs ONLY in causal action proposals/gating."""
    def __init__(self, sources:np.ndarray, model:ForwardModel, cfg:Configuration,
                 *,geometry=None,random_seed=20261028,prior=None):
        self.sources=np.asarray(sources,float).copy()
        self.model=model;self.cfg=cfg;self.geometry=geometry if geometry is not None else OpenGeometry()
        self.prior=prior
        self.history:list[Reading]=[]
        self.usage=None
        self.last_pos=None
        self.last_time=None
        self.posterior=None
        self.trace=[]
        self.random_seed=int(random_seed)
        self.calls=0

    def observe(self, reading:Reading):
        if self.last_time is not None:
            if reading.sensor_ids != self.history[-1].sensor_ids:
                raise ValueError('sensor identity silently reordered between observations')
            if not np.isclose(reading.t-self.last_time,self.cfg.dt_action,atol=1e-6):
                raise ValueError('noncausal or skipped observation time')
            self.usage+=np.linalg.norm(reading.pos-self.last_pos,axis=1)
        else:self.usage=np.zeros(len(reading.pos))
        if np.any(self.usage>self.cfg.distance_max_per_uav+1e-4):
            raise ValueError('budget violation in real flown track')
        self.last_pos=reading.pos.copy();self.last_time=reading.t
        self.history.append(reading)
        self.posterior=joint_posterior(self.history,self.sources,self.model,self.cfg,self.prior)
        self.calls+=1

    def step(self, reading:Reading) -> ActionDecision:
        self.observe(reading)
        sig=encode(self.history,self.cfg.sensor_sigma,self.cfg.hit_threshold,
                   sensor_delay_s=self.cfg.sensor_lag_s,
                   sensor_tau_s=self.cfg.sensor_tau_s)
        allcand=all_actions(reading,sig,reading.t)
        subset=shortlisted_actions(allcand,sig,self.cfg.mode)
        # A model-error certificate is a declared deployment-side provenance,
        # not an uncertainty number inferred from simulator truth. If absent,
        # strict mode never exploits an unqualified source-dependent forecast.
        # Scout/recenter can still proceed as source-blind physical actions.
        if (self.cfg.strict_model_gate and not self.cfg.model_error_calibrated
                and self.cfg.mode!='ordinary_coverage'):
            available={a.name:a for a in subset}
            preference=(['translate_cross+','translate_z+','hover']
                        if self.cfg.mode.startswith('ordinary_') else
                        (['reconfigure_gap_reverse','recenter_on_contact',
                         'translate_cross+','translate_upwind','hover']
                        if sig.stage=='partial' else
                        ['reconfigure_gap_indexed','translate_cross+',
                         'translate_z+','translate_cross-','hover']))
            for name in preference:
                if name not in available: continue
                c=available[name]
                v,ok=_safe_velocity(c.velocity,reading.pos,self.usage,
                                    self.geometry,self.cfg)
                if ok and (np.linalg.norm(v)>1e-8 or name=='hover'):
                    act=Trajectory(c.name,v,c.family,c.rationale)
                    result=ActionDecision(act,sig.stage,
                        'MODEL_UNCALIBRATED_PHYSICAL_COVERAGE_FALLBACK',
                        len(subset),False,0,0.,0.,0.,None,0,())
                    self.trace.append(result)
                    return result
            raise RuntimeError('NO_LEGAL_PHYSICAL_ACTION_UNDER_MODEL_UNCERTAINTY')
        if self.cfg.mode=='ordinary_coverage':
            names=['translate_cross+','translate_cross-','translate_z+',
                   'translate_downwind','translate_cross-','translate_upwind']
            offset=int(max(0,reading.t)//5)%len(names)
            for name in names[offset:]+names[:offset]:
                a=next((x for x in subset if x.name==name),None)
                if a is None:continue
                v,ok=_safe_velocity(a.velocity,reading.pos,self.usage,self.geometry,self.cfg)
                if ok and np.linalg.norm(v)>1e-8:
                    result=ActionDecision(Trajectory(a.name,v,a.family,a.rationale),sig.stage,
                        'ordinary deterministic wind-cast/height coverage; no future source forecast',
                        len(subset),False,0,0,0,0,None,0,())
                    self.trace.append(result);return result
        if self.cfg.mode in ('bio','bio_noidentity','bio_nogap') and sig.stage in ('precontact','wind_weak','invalid'):
            # Index-retaining stage-conditioned SCOUT, unqualified to use log,
            # Fisher or any source-conditional response to infer zero-contact.
            order=(['reconfigure_gap_indexed','reconfigure_cross','translate_cross+',
                    'translate_cross-','translate_z+','hover'] if self.cfg.mode in ('bio','bio_noidentity') else
                   ['reconfigure_cross','translate_cross+','translate_cross-',
                    'translate_z+','hover'])
            i=min(int(max(0,reading.t)//6)%len(order),len(order)-1)
            choices=order[i:]+order[:i]
            for name in choices:
                a=next((x for x in subset if x.name==name),None)
                if a is None:continue
                v,ok=_safe_velocity(a.velocity,reading.pos,self.usage,self.geometry,self.cfg)
                if ok and np.linalg.norm(v)>1e-8:
                    out=ActionDecision(Trajectory(a.name,v,a.family,a.rationale),sig.stage,
                          'physical precontact exploration; NOT a source-location certificate',
                          len(subset),False,0,0,0,0,self.cfg.forecast_error_bound,0,())
                    self.trace.append(out);return out
        candidates=[]
        scoring=(subset if self.cfg.mode in ('ordinary_eig_full','ordinary_projected_full')
                 else subset[:self.cfg.max_candidates_scored])
        for c in scoring:
            v,ok=_safe_velocity(c.velocity,reading.pos,self.usage,self.geometry,self.cfg)
            if ok:
                if _future_legal(v,reading.pos,self.usage,self.cfg.horizon_steps,
                                 self.geometry,self.cfg):
                    candidates.append(Trajectory(c.name,v,c.family,c.rationale))
        if not candidates:
            raise RuntimeError('NO_LEGAL_ACTION_AVAILABLE_IN_THE_VALIDATED_GEOMETRY')
        # All policies get the same q, source grid, wind hold, horizon, and
        # common random numbers. No planning access to source truth.
        dim=len(reading.pos)*self.cfg.horizon_steps
        # Common random draws keyed by timestamp; changing candidate count or
        # early no-contact decisions cannot shift future seeds between methods.
        rng=np.random.default_rng(self.random_seed+int(round(reading.t*1000))*13)
        noise=rng.standard_normal((20,dim));rand=rng.random(20)
        entries=[];minrank=0
        qmean=float(np.sum(self.posterior.joint_source_q*self.posterior.q_values[None,:]))
        s0=(self.posterior.sources*self.posterior.mass[:,None]).sum(axis=0)
        eps=self.cfg.source_fd_eps_m
        pert=np.tile(s0,(4,1));pert[0,0]+=eps;pert[1,0]-=eps;pert[2,1]+=eps;pert[3,1]-=eps
        hz=None
        if self.cfg.project_height_nuisance:
            hz=np.tile(s0,(2,1));hz[0,2]+=self.cfg.source_height_eps_m
            hz[1,2]-=self.cfg.source_height_eps_m
        for candidate in candidates:
            speculative=speculative_path(self.history,candidate.velocity,self.cfg.horizon_steps,self.cfg.dt_action)
            f=self.model.response(self.sources,speculative)[:,-self.cfg.horizon_steps:,:]
            self.calls+=1
            eig=_estimate_eig(f,self.posterior,self.cfg,noise,rand)
            margin=_pair_profile_margin(f,self.posterior,self.cfg)
            group=np.r_[s0[None,:],pert] if hz is None else np.r_[s0[None,:],pert,hz]
            near=self.model.response(group,speculative)[:,-self.cfg.horizon_steps:,:]
            self.calls+=1
            dheight=(near[5]-near[6])/(2*self.cfg.source_height_eps_m) if hz is not None else None
            lam,rank=_project_source_information(near[0],near[1:5],qmean,
                                    self.cfg.sensor_sigma,eps,height_sensitivity=dheight)
            # A validated per-source whitened error bound must come from
            # separate calibration, not inferred from source labels online.
            eb=self.cfg.forecast_error_bound
            robust_margin=(0. if (eb is None or not self.cfg.model_error_calibrated)
                           else max(0.,margin-2*eb))
            length=float(np.linalg.norm(candidate.velocity,axis=1).sum()*self.cfg.dt_action)
            # Score is a finite-budget heuristic; not claimed superior to
            # unconstrained optimal EIG over all legal actions.
            if self.cfg.mode in ('ordinary_eig','ordinary_eig_full'):score=eig-1e-4*length
            elif self.cfg.mode=='ordinary_coverage':score=.01*length+eig*.01
            elif self.cfg.mode in ('ordinary_projected','ordinary_projected_full'):score=np.log1p(lam)+.01*margin-1e-4*length
            else:score=eig+.10*np.log1p(lam)+.10*robust_margin-1e-4*length
            # Clean one-factor identity ablation: identical candidate actions,
            # response calls and Bayesian likelihood. Only the biologically
            # motivated identity-conditioned motor-readout term is removed.
            if self.cfg.mode=='bio':
                score+=.05*_bipolar_motor_score(sig,candidate)
            # Do not grant model-reliability certificate when eps unknown.
            qualified=bool(eb is not None and self.cfg.model_error_calibrated and
                           robust_margin>self.cfg.gain_min and
                           rank>=1 and sig.stage not in ('invalid','wind_weak'))
            if self.cfg.strict_model_gate and not qualified:
                score=-np.inf
            entries.append((float(score),candidate,lam,rank,margin,eig,qualified,length))
        entries.sort(key=lambda d:(-d[0],d[7],d[1].name))
        score,a,lam,rank,margin,eig,qualified,_=entries[0]
        if not np.isfinite(score):
            alt=next((v for v in candidates if v.name=='hover'),None)
            a=alt if alt is not None else Trajectory('hover',np.zeros_like(reading.pos),'safe','unqualified fallback')
        # Ensure output qualified flag distinguishes a causal action from a
        # genuine externally validated model-error certificate.
        report=tuple({'name':x[1].name,'score':x[0] if np.isfinite(x[0]) else None,
                      'rank':x[3],'projected_min_eig':x[2], 'profile_margin':x[4],
                      'ordinary_eig':x[5],'qualified':x[6]} for x in entries)
        result=ActionDecision(a,sig.stage,
             'bio candidate: indexed spatial/flow stage + ordinary conditional model qualification'
             if self.cfg.mode=='bio' else 'ordinary shared inference/action baseline',
             len(candidates),bool(qualified and np.isfinite(score)),rank,lam,margin,eig,
             self.cfg.forecast_error_bound,2*len(candidates),report)
        self.trace.append(result);return result
