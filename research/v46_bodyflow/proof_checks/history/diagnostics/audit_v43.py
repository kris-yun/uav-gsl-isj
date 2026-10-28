#!/usr/bin/env python3
"""Reproducible code/assumption diagnostics. NOT native plume experiments.

Read-only with respect to supplied version archives. Uses a V41 base overlaid
with the V43 files supplied in the task package. Outputs diagnostic JSON.
"""
from pathlib import Path
import sys, json, importlib.util
import numpy as np
from scipy.special import ndtr
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'legacy_v43'))
from v41_flowolf import Configuration, Reading, Controller, GaussianAdvectionDemo
from v41_flowolf.encoder import encode
from v41_flowolf.control import all_actions, _bipolar_motor_score
from v41_flowolf.physics import speculative_path

def diagnostic_run(mode='bio',q_values=(.5,1.,2.,4.),horizon=3,steps=20,seed=9001):
    true_s=np.array([0.,0.,10.]);qtrue=1.15
    model=GaussianAdvectionDemo(peak_ppm=.8,spread0_m=5.,spread_rate=.07)
    sources=np.array([[x,y,10.] for x in np.linspace(-12,12,7) for y in np.linspace(-12,12,7)])
    cfg=Configuration(mode=mode,sensor_sigma=.02,hit_threshold=.06,
                      horizon_steps=horizon,distance_max_per_uav=54.,
                      speed_xy_max=1.75,min_separation=3.,
                      q_values=tuple(q_values),q_prior=tuple(np.ones(len(q_values))/len(q_values)))
    ctrl=Controller(sources,model,cfg,random_seed=seed+777)
    pos=np.array([[10.,-5.,10.],[10.,0.,10.],[10.,5.,10.]])
    wind=np.tile([1.6,0,0.],(3,1));true_hist=[];records=[]
    noise=np.random.default_rng(seed).normal(0,cfg.sensor_sigma,(steps,3))
    for t in range(steps):
        true_hist.append(Reading(float(t),pos.copy(),np.zeros(3),wind.copy(),np.ones(3,bool)))
        gas=qtrue*model.response(true_s[None,:],true_hist)[0,-1]+noise[t]
        obs=Reading(float(t),pos.copy(),gas,wind.copy(),np.ones(3,bool))
        dec=ctrl.step(obs);sig=encode(ctrl.history,cfg.sensor_sigma,cfg.hit_threshold,
                                     sensor_delay_s=cfg.sensor_lag_s,sensor_tau_s=cfg.sensor_tau_s)
        acts=all_actions(obs,sig,t)
        ms={a.name:_bipolar_motor_score(sig,a) for a in acts}
        records.append({'t':t,'pos':pos.tolist(),'gas':gas.tolist(),
                        'weight':sig.contact_prob.tolist(),'radial':sig.radial_flow.tolist(),
                        'stage':sig.stage,'action':dec.action.name,
                        'velocity':dec.action.velocity.tolist(),'map_xy':ctrl.posterior.map_xy.tolist(),
                        'posterior_mean_xy':(ctrl.posterior.mass[:,None]*sources[:,:2]).sum(0).tolist(),
                        'motor_score':ms,'candidate_scores':dec.evaluated})
        pos+=dec.action.velocity
    true_index=np.flatnonzero(np.all(sources==true_s,axis=1))[0]
    return {'mode':mode,'q_values':list(q_values),'horizon':horizon,'steps':steps,'seed':seed,
            'map_xy':ctrl.posterior.map_xy.tolist(),
            'map_error':float(np.linalg.norm(ctrl.posterior.map_xy-true_s[:2])),
            'mean_error':float(np.linalg.norm((ctrl.posterior.mass[:,None]*sources[:,:2]).sum(0)-true_s[:2])),
            'truth_probability':float(ctrl.posterior.mass[true_index]),
            'truth_rank':int(1+np.sum(ctrl.posterior.mass>ctrl.posterior.mass[true_index])),
            'pathlength':float(ctrl.usage.sum()),'records':records}

def fixed_prefix_horizon_test():
    model=GaussianAdvectionDemo(peak_ppm=.8,spread0_m=5.,spread_rate=.07)
    p=np.array([[10.,-5.,10.],[10.,0.,10.],[10.,5.,10.]])
    w=np.tile([1.6,0,0.],(3,1));s=np.array([[0.,0.,10.]])
    h=[Reading(float(t),p.copy(),np.array([.3,.5,.3]),w.copy(),np.ones(3,bool)) for t in range(6)]
    v=np.tile([.9,0,0.],(3,1));zero=np.zeros_like(v)
    f=model.response(s,speculative_path(h,v,7,1.))[0,-7:]
    f0=model.response(s,speculative_path(h,zero,7,1.))[0,-7:]
    return {'lag':model.lag_s,'tau':model.tau_s,'difference_by_future_second':np.linalg.norm(f-f0,axis=1).tolist()}

def entropy_label_test():
    from v41_flowolf.inference import joint_posterior
    from v41_flowolf.control import _estimate_eig
    class HeightOnly:
        def response(self,sources,observations):
            return np.tile(np.asarray(sources)[:,2,None,None]/10.,(1,len(observations),2))
    s=np.array([[0.,0.,0.],[0.,0.,10.]])
    h=[Reading(0.,np.array([[2.,0.,1.],[3.,0.,1.]]),np.zeros(2),np.tile([1.,0,0],(2,1)),np.zeros(2,bool))]
    cfg=Configuration(q_values=(1.,),q_prior=(1.,),sensor_sigma=.02,horizon_steps=1)
    p=joint_posterior(h,s,HeightOnly(),cfg)
    rng=np.random.default_rng(0)
    eig=_estimate_eig(np.array([[[0.,0.]],[[1.,1.]]]),p,cfg,rng.normal(size=(100,2)),rng.random(100))
    return {'unique_xy_count':1,'true_xy_entropy':0.,'implemented_posterior_entropy':p.entropy,
            'implemented_eig':eig,'interpretation':'EIG over 3D source candidates; not XY-marginal EIG when multiple heights share XY.'}

def safety_between_samples_test():
    from v41_flowolf.control import _safe_velocity,OpenGeometry
    cfg=Configuration(horizon_steps=1,dt_action=1.,min_separation=4.,speed_xy_max=2.)
    p=np.array([[-.05,1.9999,0.],[.05,-1.9999,0.]])
    v=np.array([[1.,0,0.],[-1.,0,0.]])
    safe,ok=_safe_velocity(v,p,np.zeros(2),OpenGeometry(),cfg)
    t=np.clip(-((p[0]-p[1])@(safe[0]-safe[1]))/max(1e-30,np.sum((safe[0]-safe[1])**2)),0,1)
    return {'sampled_safety_returned_legal':ok,'minimum_exact_separation':float(np.linalg.norm(p[0]-p[1]+t*(safe[0]-safe[1]))),
            'required_separation':4.,'t_min':float(t),'returned_velocity':safe.tolist()}

def corrected_encoder_tests():
    f=ROOT/'legacy_v43/tests/test_v43_scientific_fixes.py'
    spec=importlib.util.spec_from_file_location('scientific',f);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    rows=[]
    for name in sorted(n for n in dir(m) if n.startswith('test_')):
        try:getattr(m,name)();rows.append({'name':name,'status':'PASS'})
        except Exception as e:rows.append({'name':name,'status':'FAIL','error':repr(e)})
    return rows

def main():
    runs=[]
    for q in [(.5,1.,2.,4.),(.5,1.,1.15,2.,4.)]:
        for mode in ['bio','bio_noidentity','ordinary_projected_full']:
            r=diagnostic_run(mode,q);runs.append(r)
            print({k:v for k,v in r.items() if k!='records'},flush=True)
    result={'scope':'Deterministic/minimal synthetic code diagnostics, not native S2, not performance validation.',
            'runs':runs,'sensor_horizon':fixed_prefix_horizon_test(),
            'entropy_label':entropy_label_test(),'continuous_safety':safety_between_samples_test(),
            'v43_scientific_assertions':corrected_encoder_tests(),
            'contact_weight_saturation':{'gas':[.06,.10,.16,.30,.50],
                'weight':ndtr((np.array([.06,.10,.16,.30,.50])-.06)/.02).tolist()}}
    (ROOT/'results'/'audit_v43_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps({k:v for k,v in result.items() if k!='runs'},indent=2,ensure_ascii=False))
if __name__=='__main__':main()
