#!/usr/bin/env python3
"""End-to-end executable synthetic V41 algorithm comparison (NOT S2 native)."""
from __future__ import annotations
import argparse,copy,json,time
from pathlib import Path
import numpy as np
from v41_flowolf import Configuration,Reading,Controller,GaussianAdvectionDemo


def run(mode='bio',source=(0.,0.,10.),steps=24,seed=9001,error_bound=None,
        save_trace=False):
    rng=np.random.default_rng(seed)
    # The evaluator alone owns true source and its physical q. This parameter
    # is never supplied to the Controller or shared source posterior model.
    true_s=np.asarray(source,float)
    qtrue=1.15
    model=GaussianAdvectionDemo(peak_ppm=.8,spread0_m=5.,spread_rate=.07)
    # Same true source domain for every method, but no true label in controller.
    sx=np.linspace(-12.,12.,7);sy=np.linspace(-12.,12.,7)
    sources=np.array([[x,y,10.] for x in sx for y in sy])
    cfg=Configuration(mode=mode,forecast_error_bound=error_bound,
          sensor_sigma=.02,hit_threshold=.06,horizon_steps=3,
          distance_max_per_uav=54.,speed_xy_max=1.75,min_separation=3.)
    ctrl=Controller(sources,model,cfg,random_seed=seed+777)
    positions=np.array([[10.,-5.,10.],[10.,0.,10.],[10.,5.,10.]])
    wind=np.repeat([[1.6,0.,0.]],3,axis=0)
    # World is not a source-conditional posterior model: policy cannot inspect it.
    true_hist=[];records=[];tic=time.perf_counter()
    common_noise=rng.normal(0,cfg.sensor_sigma,size=(steps,3))
    for t in range(steps):
        stamp=float(t)
        dummy=Reading(stamp,positions.copy(),np.zeros(3),wind.copy(),np.ones(3,bool))
        true_hist.append(dummy)
        response=model.response(true_s[None,:],true_hist)[0,-1]
        gas=qtrue*response+common_noise[t]
        obs=Reading(stamp,positions.copy(),gas,wind.copy(),np.ones(3,bool))
        dec=ctrl.step(obs)
        records.append({'t':t,'stage':dec.stage,'action':dec.action.name,
                        'gas_ppm':gas.tolist(),'map':ctrl.posterior.map_source.tolist(),
                        'ess':ctrl.posterior.ess,'rank':dec.source_rank,
                        'model_certified':dec.qualified,
                        'm3_candidate_scores':dec.evaluated})
        positions=positions+dec.action.velocity
    estimate=ctrl.posterior.map_source[:2]
    result={'mode':mode,'seed':seed,'steps':steps,
            'synthetic_truth_xy_eval_only':true_s[:2].tolist(),
            'estimated_source_xy':estimate.tolist(),
            'map_error_m_eval_only':float(np.linalg.norm(estimate-true_s[:2])),
            'contacts':int(sum(np.any(np.array(x['gas_ppm'])>=cfg.hit_threshold) for x in records)),
            'distance_per_uav_m':ctrl.usage.tolist(),
            'action_names':[x['action'] for x in records],
            'elapsed_s':time.perf_counter()-tic,
            'forward_model':'GaussianAdvectionDemo (synthetic software test, NOT S2 GADEN)',
            'independently_validated_error_certificate':False}
    if save_trace:result['records']=records
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='v41_demo_results.json')
    p.add_argument('--steps',type=int,default=20)
    p.add_argument('--seed',type=int,default=9001)
    a=p.parse_args()
    outputs=[run(mode=m,steps=a.steps,seed=a.seed,save_trace=True) for m in
         ('bio','ordinary_eig','ordinary_projected','ordinary_coverage','bio_noidentity','bio_noflow')]
    Path(a.out).write_text(json.dumps(outputs,indent=2,ensure_ascii=False))
    for x in outputs:print(x['mode'],'error',round(x['map_error_m_eval_only'],3),
                 'contactsteps',x['contacts'],'moves',x['action_names'][:9],
                 'runtime',round(x['elapsed_s'],2),'s')
    print('NOTE: synthetic software test only; no S2 native experimental claim')

if __name__=='__main__':main()