"""TRAIN-only native-sampled M1 pilot; explicit ideal/coarse adaptation.

This does not turn sensor_response_calibrated=False into a true assertion.
Delivered fast filtering remains unqualified. The separately frozen coarse
profile is a conditional, ideal simulator-readout diagnostic, not a hardware
or UAV validation and not deployment without a source response calibration set.
"""
from pathlib import Path
import json,os,sys,time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gsl_discrimination.data import SynchronousBlock
from gsl_discrimination.m1_opponent import OpponentBank,SamplingContract,calibrate_source_contrast
from gsl_discrimination.m1_opponent.operator import FilterSpec,time_weights
from gsl_discrimination.m1_opponent.raw_joint import calibrate_raw_joint
from recover_assets import ROOT,OUT,PROTO,sha,write

def features(x,times,bank,contract,selection):
    log=np.log1p(np.maximum(x,0))
    e,h=bank.extract(x,times,contract)
    w=time_weights(times)
    return {'single_left_full_window':log[...,0],
            'single_left_mean':np.einsum('...t,t->...',log[...,0],w)[...,None],
            'ordinary_two_time_means':np.einsum('...tp,t->...p',log,w),
            'ordinary_full_raw_window':log.reshape(log.shape[:-2]+(-1,)),
            'mother_features':np.concatenate((e[...,None],h[...,selection['mother']]),axis=-1),
            'selected_M1_features':np.concatenate((e[...,None],h[...,selection['secondary']]),axis=-1)}

def main():
    begin=time.perf_counter();begin_cpu=time.process_time()
    if (OUT/'MODEL_FREEZE.json').exists():raise RuntimeError('model freeze exists')
    proto=json.loads(PROTO.read_text());r1=json.loads((OUT/'R1_EXTRACTION_RESULT.json').read_text())
    assert r1['readout_regression_pass'] and r1['wind_regression_pass']
    records=[r for r in r1['blocks'] if r['split']=='train']
    assert len(records)==4
    loaded={r['run_id']:SynchronousBlock.load_npz(OUT/r['path']) for r in records}
    times=next(iter(loaded.values())).times_s
    for b in loaded.values():
        assert np.array_equal(b.times_s,times)
        assert not b.qualification.sensor_response_calibrated
    x=np.stack([[loaded[r['run_id']].values for r in records if r['source_id']==s] for s in ('A','B')])
    raw=x[None,:,None,:,:,:]  # action,source,nuisance,world,time,two-sensors
    cfg=proto['coarse_sampling_profile']
    specs=[FilterSpec('static_gradient',kind='gradient')]
    for lag in cfg['lags_s']:
        for inhibition in cfg['inhibitions']:
            specs.append(FilterSpec(f'coarse_delay_{lag:g}_inhibit_{inhibition:g}',lag,cfg['decay_s'],inhibition))
    bank=OpponentBank(specs)
    # In this isolated adapter, the timing contract describes an analytical
    # identity readout sampled at native instants; it is not a PID calibration.
    # Persist that distinction in model scope and do not use the manifest
    # loader's hardware gate to misrepresent missing physical capabilities.
    contract=SamplingContract(continuous=True,synchronous=True,maximum_step_s=cfg['maximum_step_s'],
             bandwidth_calibrated=True,provenance='CONDITIONAL_IDEAL_NATIVE_SAMPLED_READOUT_identity_transfer_no_hardware_bandwidth_claim')
    # Prove that the original fast profile is rejected; retain this negative.
    fast=SamplingContract(continuous=True,synchronous=True,maximum_step_s=.25,bandwidth_calibrated=True)
    try:OpponentBank.causal_default().extract(raw,times,fast)
    except ValueError as exc:write('ORIGINAL_FAST_PROFILE_GATE.json',{'status':'REJECTED_AS_REQUIRED','reason':str(exc)})
    else:raise RuntimeError('original fast bank unexpectedly passed')
    xy=np.array(proto['source_xyz_m'])[:,:2]
    fits=[];models={};selection={}
    for variant in proto['variants']:
        s=time.perf_counter();c=time.process_time()
        if variant=='raw_joint':
            model=calibrate_raw_joint(raw,times,contract,xy,['frozen_pool12_pool17'],['A','B'],[float(times[-1]-times[0])],n_symbols=4)
        else:
            model=calibrate_source_contrast(raw,times,contract,xy,['frozen_pool12_pool17'],['A','B'],[float(times[-1]-times[0])],
                 bank=bank,variant=variant,max_filters=2,calibration_world_ids=sorted(loaded))
            selection[variant]=model.selection[0]
        model.channel.metadata.update({'scope':'CONDITIONAL_IDEAL_NATIVE_COARSE_PILOT',
           'hardware_qualified':False,'active_flight':False,'calibration_worlds':sorted(loaded),
           'data_protocol_sha256':sha(PROTO),'no_heldout_worlds_opened_at_fit':True})
        model.save(OUT/'models'/variant);models[variant]=model
        fits.append({'variant':variant,'wall_s':time.perf_counter()-s,'cpu_s':time.process_time()-c,
                     'selected_filters':selection.get(variant),'alphabet_size':model.channel.shape[-1]})
    sets=features(x,times,bank,contract,selection)
    ordinary={}
    for name,arr in sets.items():
        d=arr.shape[-1];mean=arr.mean(axis=1);residual=arr-mean[:,None,:]
        pooled=np.einsum('swd,swe->de',residual,residual)/(arr.shape[0]*(arr.shape[1]-1))
        floor=float(.1*np.trace(pooled)/d+1e-6)
        covariance=pooled+floor*np.eye(d)
        file=OUT/'models'/(name+'.npz')
        np.savez_compressed(file,mean=mean,covariance=covariance,diagonal_floor=floor)
        ordinary[name]={'dimension':d,'floor':floor,'sha256':sha(file)}
    write('TRAIN_FIT_RECEIPT.json',{'training_worlds':sorted(loaded),'dev_opened':False,'fits':fits,
        'shared_gaussian_controls':ordinary,'wall_s':time.perf_counter()-begin,'cpu_s':time.process_time()-begin_cpu,
        'selected_bank':bank.to_dict(),'selection':selection,
        'hardware_sensor_response_calibrated':False,'ideal_identity_readout_assumption':True,
        'sampling_adaptation_is_not_innovation':True})
    files={str(p.relative_to(OUT)):sha(p) for p in sorted((OUT/'models').rglob('*')) if p.is_file()}
    write('MODEL_FREEZE.json',{'models':files,'protocol_sha256':sha(PROTO),'training_block_hashes':{r['run_id']:r['sha256'] for r in records},
          'code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'native').rglob('*.py'))},
          'first_DEV_response_not_yet_scored':True,'scope':'conditional native coarse ideal-readout pilot, not full R2 hardware or flight PASS'})
    print(json.dumps({'fits':fits,'selection':selection,'freeze_sha256':sha(OUT/'MODEL_FREEZE.json')},indent=2))

if __name__=='__main__':main()
