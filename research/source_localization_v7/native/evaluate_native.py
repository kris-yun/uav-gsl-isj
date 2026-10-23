"""Only evaluate after all methods and all input hashes have been frozen."""
import csv,json,sys,time
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gsl_discrimination.data import SynchronousBlock
from gsl_discrimination.m1_opponent.raw_joint import load_observation_model
from gsl_discrimination.evaluation.metrics import source_metrics
from fit_native import features
from recover_assets import ROOT,OUT,PROTO,sha,write

def main():
    if (OUT/'R2_RESULT.json').exists():raise RuntimeError('DEV results already frozen; no retuning')
    freeze=json.loads((OUT/'MODEL_FREEZE.json').read_text())
    for f,h in freeze['models'].items():assert sha(OUT/f)==h
    for f,h in freeze['code_sha256'].items():assert sha(ROOT/f)==h
    start=time.perf_counter();proto=json.loads(PROTO.read_text())
    r1=json.loads((OUT/'R1_EXTRACTION_RESULT.json').read_text());fit=json.loads((OUT/'TRAIN_FIT_RECEIPT.json').read_text())
    dev=[r for r in r1['blocks'] if r['split']=='dev'];assert len(dev)==4
    models={v:load_observation_model(OUT/'models'/v) for v in proto['variants']}
    bank=models['secondary'].bank;contract=models['secondary'].contract
    xy=np.array(proto['source_xyz_m'])[:,:2];rows=[];posterior_arrays=[];timings=[]
    ordinary_names=list(fit['shared_gaussian_controls'])
    for record in dev:
        block=SynchronousBlock.load_npz(OUT/record['path']);truth=proto['source_ids'].index(record['source_id'])
        feature=features(block.values,block.times_s,bank,contract,fit['selection'])
        for name,model in models.items():
            began=time.perf_counter();symbol=model.encode(0,block.values,block.times_s,contract)
            logp=np.log(model.channel.probabilities[0,:,0,int(symbol)])
            p=np.exp(logp-logsumexp(logp));elapsed=time.perf_counter()-began
            rows.append({'method':name,'world_id':record['run_id'],'true_source_id':record['source_id'],
                         'inference_s':elapsed,'symbol':int(symbol),**source_metrics(p,truth,xy)})
            posterior_arrays.append(p);timings.append({'method':name,'seconds':elapsed})
        for name in ordinary_names:
            began=time.perf_counter();v=np.asarray(feature[name]).ravel()
            with np.load(OUT/'models'/(name+'.npz')) as f:mu=f['mean'];cov=f['covariance']
            delta=v[None,:]-mu;inv=np.linalg.inv(cov)
            logp=-.5*np.einsum('sd,de,se->s',delta,inv,delta)
            p=np.exp(logp-logsumexp(logp));elapsed=time.perf_counter()-began
            rows.append({'method':'gaussian_'+name,'world_id':record['run_id'],'true_source_id':record['source_id'],
                         'inference_s':elapsed,'symbol':None,**source_metrics(p,truth,xy)})
            posterior_arrays.append(p);timings.append({'method':'gaussian_'+name,'seconds':elapsed})
    summaries=[]
    for method in sorted({r['method'] for r in rows}):
        r=[x for x in rows if x['method']==method]
        summaries.append({'method':method,'independent_dev_worlds':len(r),'correct_with_stable_tie_break':sum(x['top1'] for x in r),
           'strict_correct':sum(x['top1'] and not x['top1_tie'] for x in r),'ties':sum(x['top1_tie'] for x in r),
           'mean_MAP_error_m':float(np.mean([x['map_error_m'] for x in r])),
           'mean_Brier':float(np.mean([x['brier'] for x in r])),
           'mean_log_margin':float(np.mean([x['log_margin'] for x in r])),
           'inference_s_total':float(sum(x['inference_s'] for x in r))})
    def csvout(name,data):
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    csvout('PER_WORLD_M1.csv',rows);csvout('SUMMARY_M1.csv',summaries)
    np.savez_compressed(OUT/'FROZEN_DEV_POSTERIORS.npz',probability=np.array(posterior_arrays))
    main=next(r for r in summaries if r['method']=='secondary')
    ordinary=[r for r in summaries if r['method'] in ('raw_joint','gaussian_ordinary_full_raw_window','gaussian_ordinary_two_time_means')]
    best=min(ordinary,key=lambda r:r['mean_MAP_error_m'])
    numerical_gain=best['mean_MAP_error_m']>0 and main['mean_MAP_error_m']<=.9*best['mean_MAP_error_m']
    # This is a bounded discovery diagnostic. No full R2 upgrade solely from
    # four worlds, uncalibrated physical PID, or the coarse adapted filter.
    write('R2_RESULT.json',{'status':'CONDITIONAL_NATIVE_COARSE_IDEAL_READOUT_PILOT_COMPLETE',
          'primary':main,'best_ordinary_descriptive_reference':best,'has_10_percent_descriptive_MAP_gain':bool(numerical_gain),
          'broad_independent_gain_established':False,'R3_R4_authorized_by_science_gate':False,
          'R3_R4_status':'NOT_EXECUTED: no established independent M1 gain / hardware-temporal qualification / M2 action geometry',
          'original_fast_profile':'REJECTED_NATIVE_MAX_GAP','sampling_adaptation_not_innovation':True,
          'source_support':'two TRAIN-calibrated alternatives only; no full O24 map or unseen source claim',
          'source_height_confound':True,'known_prior_static_negative_results_unchanged':True,
          'new_ROS':0,'new_physical_worlds':0,'duration_s':time.perf_counter()-start,
          'summaries':summaries,'model_freeze_sha256':sha(OUT/'MODEL_FREEZE.json')})
    print(json.dumps(summaries,indent=2));print('R3/R4 STOP: no established independent M1 gain')

if __name__=='__main__':main()
