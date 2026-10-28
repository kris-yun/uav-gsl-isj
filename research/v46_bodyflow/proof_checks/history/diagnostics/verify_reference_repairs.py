#!/usr/bin/env python3
"""Minimal old/fixed certificates and q refinement on the SAME observed path."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.special import logsumexp
from scipy.integrate import quad
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'legacy_v43'))
from v41_flowolf import Reading,Configuration,GaussianAdvectionDemo
from v41_flowolf.inference import joint_posterior
from v41_flowolf.control import _estimate_eig,_safe_velocity,OpenGeometry
from reference_repairs import uniform_q_log_marginal,xy_expected_information,safe_linear_velocity,closest_pair_distance

def q_refinement():
    src=np.array([[x,y,10.] for x in np.linspace(-12,12,7) for y in np.linspace(-12,12,7)])
    raw=json.loads((ROOT/'data'/'frozen_historical_observations.json').read_text())['runs']
    model=GaussianAdvectionDemo(peak_ppm=.8,spread0_m=5.,spread_rate=.07)
    out=[]
    for run in raw[:3]:
        hist=[Reading(float(r['t']),np.array(r['pos']),np.array(r['gas']),np.tile([1.6,0,0.],(3,1)),np.ones(3,bool)) for r in run['records']]
        F=model.response(src,hist).reshape(len(src),-1);y=np.stack([h.gas_ppm for h in hist]).ravel()
        ti=np.flatnonzero(np.all(src==[0,0,10.],axis=1))[0]
        results=[]
        for count in [4,17,33,65,129,257,513]:
            q=np.geomspace(.5,4.,count)
            # Fixed prior: uniform in log q, composite trapezoid weights.
            w=np.ones(count);w[[0,-1]]=.5;w/=w.sum()
            loglik=-.5*np.sum(((y[None,None,:]-F[:,None,:]*q[None,:,None])/.02)**2,axis=2)
            lm=logsumexp(loglik+np.log(w)[None,:],axis=1)
            p=np.exp(lm-logsumexp(lm));m=src[np.argmax(p),:2]
            results.append({'q_count':count,'q_rule':'fixed geomspace[0.5,4] log-uniform trapezoid',
                            'map_xy':m.tolist(),'map_error':float(np.linalg.norm(m)),
                            'truth_probability':float(p[ti]),'truth_rank':int(1+np.sum(p>p[ti]))})
        lm=uniform_q_log_marginal(F,y,.02,.5,4.);p=np.exp(lm-logsumexp(lm));m=src[np.argmax(p),:2]
        results.append({'q_count':'analytic continuous uniform','q_rule':'uniform[0.5,4], no true q input',
                        'map_xy':m.tolist(),'map_error':float(np.linalg.norm(m)),
                        'truth_probability':float(p[ti]),'truth_rank':int(1+np.sum(p>p[ti]))})
        out.append({'path_from_mode':run['mode'],'records_fixed':len(hist),'results':results})
    return out

def entropy_and_safety():
    class HeightOnly:
        def response(self,sources,observations):return np.tile(np.asarray(sources)[:,2,None,None]/10.,(1,len(observations),2))
    src=np.array([[0.,0.,0.],[0.,0.,10.]])
    hist=[Reading(0,np.array([[2.,0,1.],[3.,0,1.]]),np.zeros(2),np.tile([1.,0,0],(2,1)),np.zeros(2,bool))]
    cfg=Configuration(q_values=(1.,),q_prior=(1.,),sensor_sigma=.02,horizon_steps=1)
    p=joint_posterior(hist,src,HeightOnly(),cfg);rng=np.random.default_rng(0)
    nd=rng.normal(size=(100,2));un=rng.random(100);future=np.array([[[0.,0]],[[1.,1.]]])
    old=_estimate_eig(future,p,cfg,nd,un);new=xy_expected_information(future,p,cfg.sensor_sigma,nd,un)
    assert old>.6 and abs(new)<1e-12
    cfg=Configuration(horizon_steps=1,dt_action=1.,min_separation=4.,speed_xy_max=2.)
    pos=np.array([[-.05,1.9999,0],[.05,-1.9999,0.]])
    vel=np.array([[1.,0,0],[-1.,0,0]])
    oldv,oldok=_safe_velocity(vel,pos,np.zeros(2),OpenGeometry(),cfg)
    newv,newok=safe_linear_velocity(vel,pos,np.zeros(2),OpenGeometry(),cfg)
    oldd,t=closest_pair_distance(*pos,*oldv,1.)
    newd,_=closest_pair_distance(*pos,*newv,1.)
    assert oldok and oldd<4 and not newok and newd>=4
    # Independent numerical integration checks exact q marginal under a small
    # well-conditioned example and large-response scientific diagnostics.
    F=np.array([[.2,.3],[.1,.4],[0.,0.]]);y=np.array([.3,.5]);sigma=.2
    analytic=uniform_q_log_marginal(F,y,sigma,.5,4.)
    numeric=np.array([np.log(quad(lambda q:np.exp(-.5*np.sum(((y-q*f)/sigma)**2))/3.5,.5,4,epsabs=1e-13)[0]) for f in F])
    assert np.max(abs(analytic-numeric))<1e-10
    return {'XY_EIG':{'before':old,'after':new,'correct':0.},
            'continuous_separation':{'before_accepted':oldok,'before_min_distance':oldd,'time_of_min':t,
                'after_accepted':newok,'after_returned_hover_distance':newd,'min_required':4.},
            'continuous_q_integral_max_abs_log_error_vs_quad':float(np.max(abs(analytic-numeric)))}

def main():
    result={'scope':'Code and quadrature diagnostics; fixed historical observations; not publication performance evidence.',
            'q_refinement':q_refinement(),'repairs':entropy_and_safety()}
    (ROOT/'results'/'reference_repair_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
