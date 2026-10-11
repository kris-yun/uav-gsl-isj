"""Arithmetic attribution of saved candidate-reference errors; no new model/head.
Uses only already built reference phi and frozen model coefficients, including
the precommitted extra pair excluded from M2 fitting. No hidden test readout.
"""
from common_b import *
import csv,collections,numpy as np
import rk2b_models as models
def write(p,a):
    with Path(p).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(a[0]),lineterminator='\n');w.writeheader();w.writerows(a)
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def main():
    begin=time.perf_counter();reg=load(CORE/'experiment_registry.json');ci=load(RAW/'reference_cache/CACHE_INDEX.json');cached={};detail=[];info=[]
    refjobs=[j for j in reg['jobs'] if j['role'] in ['reference','extra_reference']];ids=[s['future_candidate_id'] for s in reg['sources']]
    for e in ci['entries']:
        with np.load(RAW/'reference_cache'/e['file'],allow_pickle=False) as z:cached[e['job_id'],e['frame']]=(z['filaments'].copy(),z['contributions'].copy(),z['native_totals'].copy())
    for M in [2,4]:
        with np.load(CORE/f'M{M}/forecasts/F.npz',allow_pickle=False) as z:F=z['reference_response_ppm']
        hit=np.count_nonzero(F[:,:M].astype(np.float32)>np.float32(.1),axis=1)/M;p=(M*hit+.5)/(M+1)
        for b in range(50):
            f2=np.count_nonzero(F[:,:2].astype(np.float32)>np.float32(.1),axis=1)/2;f4=np.count_nonzero(F.astype(np.float32)>np.float32(.1),axis=1)/4
            for c in range(3):info.append(dict(M=M,candidate_id=ids[c],block=b,empirical_hit_frequency=hit[c,b],Jeffreys_probability=p[c,b],candidate_probability_spread=float(np.ptp(p[:,b])),H0_informative=bool(np.ptp(p[:,b])>0),p4_minus_p2_sampling_component=float(f4[c,b]-f2[c,b]),p4_minus_p2_Jeffreys_component=float((.5-f4[c,b])/5-(.5-f2[c,b])/3)))
        for name in ['U_query','S_query','L']:
            with np.load(CORE/f'M{M}/models/{name}.npz',allow_pickle=False) as z:keys=z['keys'];h=z['decoder'];prior=z['prior'];spec=json.loads(str(z['routing_spec']))
            look={tuple(map(int,k)):i for i,k in enumerate(keys)}
            with np.load(CORE/f'M{M}/forecasts/{name}.npz',allow_pickle=False) as z:prediction=z['reference_response_ppm']
            for job in refjobs:
                c=ids.index(job['candidate_id']);ri=job['replicate']+(2 if job['role']=='extra_reference' else 0)
                lines=rows(Path(reg['host_data_path'])/'realizations'/job['job_id']/'QUERY_PHYSICAL_LINEAGE.csv')
                for line in lines:
                    b=int(line['block_id']);pose=b//5;f,phi,native=cached[job['job_id'],int(line['frame'])];cells,features=models.physical_features(f);cl=models.route(features,spec);kk=models.state_keys(cells,cl);idx=np.array([look.get(tuple(map(int,k)),-1) for k in kk]);known=idx>=0;counts=np.bincount(idx[known],minlength=len(keys))
                    scalar_phi=phi[:,pose].astype(float);known_F=float(np.sum(scalar_phi[known]));unknown_F=float(np.sum(scalar_phi[~known]));fallback=float(np.cumsum(phi[~known,pose],dtype=np.float32)[-1]) if (~known).any() else 0.;decode=float(counts@h[:,pose]);value=decode+fallback;actual=float(native[pose])
                    assert abs(value-prediction[c,ri,b])<=3e-7+5e-6*abs(value)
                    fit=float(counts@(h[:,pose]-prior[:,pose]));physical=float(counts@prior[:,pose])-known_F;fr=fallback-unknown_F;nr=known_F+unknown_F-actual;error=value-actual
                    assert abs(fit+physical+fr+nr-error)<=1e-10*(1+abs(error))
                    extra=dict(cutoff_eligible_particles='NA_NOT_ZERO_FALSE_POSITIVE',positive_native_particles=int(np.count_nonzero(phi[:,pose])),known_decoder_positive_particles=int(np.count_nonzero(h[idx[known],pose]>0)))
                    false_zero=actual==0 and np.float32(value)>np.float32(.1)
                    if false_zero:
                        q=np.array(reg['all_receiver_xyz'][pose],np.float32);dd=f[:,:3]-q;squared=np.zeros(len(f),np.float32)
                        for ax in range(3):np.add(squared,np.multiply(dd[:,ax],dd[:,ax],dtype=np.float32),out=squared)
                        limit=np.divide(np.multiply(f[:,3],np.float32(3),dtype=np.float32),np.float32(100),dtype=np.float32);eligible=squared<np.multiply(limit,limit,dtype=np.float32)
                        extra['cutoff_eligible_particles']=int(eligible.sum());assert fallback==0 and known_F==0 and unknown_F==0
                    detail.append(dict(M=M,method=name,job_id=job['job_id'],reference_role=job['role'],candidate_id=job['candidate_id'],reference=ri,block=b,pose=pose,F_ppm=actual,frozen_prediction_ppm=float(prediction[c,ri,b]),reconstructed_prediction_ppm=value,error_ppm=error,fit_coefficient_adjustment_ppm=fit,physical_conditional_prior_transfer_ppm=physical,fallback_serial_rounding_ppm=fr,F_serial_rounding_ppm=nr,unknown_particles=int((~known).sum()),all_particles=len(f),F_zero_model_positive=false_zero,known_decoder_ppm=decode,physical_F_fallback_ppm=fallback,**extra))
    aggregate=[]
    for M in [2,4]:
        for method in ['U_query','S_query','L']:
            for role in ['reference','extra_reference']:
                rr=[r for r in detail if r['M']==M and r['method']==method and r['reference_role']==role];e=np.array([r['error_ppm'] for r in rr]);fit=np.array([r['fit_coefficient_adjustment_ppm'] for r in rr]);prior=np.array([r['physical_conditional_prior_transfer_ppm'] for r in rr]);zeros=[r for r in rr if r['F_zero_model_positive']]
                aggregate.append(dict(M=M,method=method,reference_role=role,queries=len(rr),MSE_ppm=float(np.mean(e*e)),event_flips_vs_F=sum((np.float32(r['frozen_prediction_ppm'])>np.float32(.1))!=(np.float32(r['F_ppm'])>np.float32(.1)) for r in rr),mean_absolute_fit_adjustment_ppm=float(np.mean(np.abs(fit))),mean_absolute_physical_prior_transfer_ppm=float(np.mean(np.abs(prior))),mean_fit_square=float(np.mean(fit*fit)),mean_prior_transfer_square=float(np.mean(prior*prior)),twice_mean_fit_prior_cross=float(2*np.mean(fit*prior)),native_zero_false_positives=len(zeros),native_zero_false_positives_no_cutoff_eligible_particles=sum(r['cutoff_eligible_particles']==0 for r in zeros),maximum_native_zero_false_positive_ppm=max([r['frozen_prediction_ppm'] for r in zeros],default=0)))
    write(CORE/'reference_transfer_error_attribution.csv',detail);write(CORE/'reference_transfer_summary.csv',aggregate);write(CORE/'registered_H0_information_and_smoothing.csv',info)
    dump(CORE/'REGISTERED_DIAGNOSTIC_DESCRIPTION.json',dict(wall_s=time.perf_counter()-begin,scope='Arithmetic decomposition of already frozen all-reference forecasts and cached phi; no new inference, head, fitting or physical readout',new_source_inference_calls=0,generated_physical_data=0,model_changed=False,identity='hatC-F=sum_known n*(h-prior)+[sum_known n*prior-sum_known phi]+fallback_rounding+native_serial_rounding',fixed_pair_count_change_note='p_M=f_M+(0.5-f_M)/(M+1): M4/M2 changes include Jeffreys shrinkage as well as empirical reference variation; no causal NLL percentage attribution'))
    print(json.dumps(dict(summary=aggregate,wall_s=time.perf_counter()-begin),indent=2))
if __name__=='__main__':main()
