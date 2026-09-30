"""Frozen T02 diagnostic on exactly 64 discovery binary tensors."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import beta, binomtest

ROOT=Path(__file__).resolve().parents[2]
PREVIOUS=ROOT/'research/cdsi_t01b/run_audit.py'
spec=importlib.util.spec_from_file_location('t01b_frozen',PREVIOUS)
prior=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
EV=ROOT/'evidence/source_spatial_information_t02'
INPUT=ROOT/'evidence/ocb_r2/mechanism_census_r0/inputs'
ARMS=('TOTAL_RATE_1D','STATIC_SPATIAL_30D','AMPLITUDE_REMOVED_SPATIAL_30D','COMPOSITIONAL_SPATIAL_30D','LOCATION_DESTROYED')
N_LOCATION=1000


def read_rows(path):
    with path.open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f,delimiter='\t'))


def compose(x):
    result=np.zeros_like(x,dtype=float)
    total=x.sum(axis=1)
    np.divide(x,total[:,None],out=result,where=total[:,None]>0)
    return result


def location_destroyed(v,cidx):
    banks=[]
    for i in range(8):
        rng=np.random.default_rng(np.random.SeedSequence([2026100103,cidx,i]))
        permutation=np.argsort(rng.random((N_LOCATION,30)),axis=-1,kind='stable')
        banks.append(v[i][permutation])
    banks=np.stack(banks,axis=1)
    assert banks.shape==(N_LOCATION,8,30)
    assert np.array_equal(np.sort(banks,axis=2),np.broadcast_to(np.sort(v,axis=1),(N_LOCATION,8,30)))
    assert np.allclose(banks.sum(axis=2),v.sum(axis=1)[None,:],atol=1e-12,rtol=0)
    assert np.allclose(np.square(banks).sum(axis=2),np.square(v).sum(axis=1)[None,:],atol=1e-12,rtol=0)
    distance=np.sqrt(np.square(banks[:,:,None,:]-banks[:,None,:,:]).sum(axis=3)/30)
    avg=distance.mean(axis=0)
    scores=np.array([prior.energy_matrix(avg,a,b) for a,b in zip(prior.ASSIGN,prior.COMPLEMENT)])
    per_draw=[]
    for a,b in zip(prior.ASSIGN,prior.COMPLEMENT):
        per_draw.append(2*distance[:,a[:,None],b[None,:]].mean(axis=(1,2))-
            distance[:,a[:,None],a[None,:]].mean(axis=(1,2))-
            distance[:,b[:,None],b[None,:]].mean(axis=(1,2)))
    per_draw=np.stack(per_draw)
    assert np.allclose(scores,per_draw.mean(axis=1),atol=1e-12,rtol=0)
    for draw in (0,1,999):
        direct=prior.all_energy(banks[draw])
        assert np.allclose(direct,per_draw[:,draw],atol=1e-12,rtol=0)
    return scores,per_draw


def self_test():
    z=np.zeros((8,30))
    assert np.array_equal(compose(z),z)
    v=np.tile(np.arange(30,dtype=float),(8,1))
    assert np.allclose(compose(v),compose(v*np.arange(1,9)[:,None]),atol=1e-15,rtol=0)
    uniform=np.tile(np.arange(8,dtype=float)[:,None]/8,(1,30))
    score,_=location_destroyed(uniform,0)
    assert np.allclose(score,prior.all_energy(uniform),atol=1e-12,rtol=0)
    assert np.allclose((v-v.mean(axis=1)[:,None]).mean(axis=1),0,atol=1e-15)
    return dict(zero_composition_pass=True,composition_positive_gain_invariance_pass=True,
        uniform_profile_location_shuffle_identity_pass=True,centering_removes_common_level_pass=True,
        energy_implementation_reused=True,previous_energy_script_sha256=prior.sha(PREVIOUS))


def aggregate(z,indices):
    obs=float(z[:,0].mean())
    null=z[np.arange(8)[:,None],indices].mean(axis=0)
    exceeds=int(np.count_nonzero(null>=obs-prior.TOL))
    n=prior.N_AGGREGATE
    ci=[float(beta.ppf(.025,exceeds,n-exceeds+1)) if exceeds else 0.,float(beta.ppf(.975,exceeds+1,n-exceeds)) if exceeds<n else 1.]
    return dict(observed_mean_z=obs,draws=n,seed=2026100102,exceedances=exceeds,
        p_plus_one=(1+exceeds)/(n+1),mc_binomial_95_interval=ci,method='Monte Carlo stratified 70-assignment source-label permutation'),null


def run(out,metadata_only=False):
    out.mkdir(parents=True,exist_ok=True)
    checks=self_test()
    runs,contexts=prior.metadata(out)
    prior.js(out/'IMPLEMENTATION_CHECKS.json',checks)
    if metadata_only:
        print('Metadata contract and synthetic implementation checks PASS; no target values loaded.')
        return
    frozen=prior.load_json(ROOT/'evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json')
    vectors,bindings={},[]
    for r in runs:
        p=INPUT/(r['run_id']+'.pooled.npy')
        digest=prior.sha(p)
        assert digest==frozen['pooled_tensor_sha256'][r['run_id']]
        x=np.load(p,allow_pickle=False)
        assert x.shape==(10,30) and np.isfinite(x).all() and (x>=0).all()
        vectors[r['run_id']]=x>0
        bindings.append(dict(run_id=r['run_id'],sha256=digest,threshold='C>0',time_probe_contract_unchanged=True))
    prior.table(out/'INPUT_HASH_BINDING.tsv',bindings)
    previous=read_rows(ROOT/'evidence/cdsi_t01b/pass1/CONTEXT_ENERGY_RESULTS.tsv')
    records,null_rows,zeros,draws,zero_rows=[],[],[],[],[]
    z_all={arm:[] for arm in ARMS}
    for cidx,c in enumerate(contexts):
        rr=sorted([r for r in runs if r['context']==c['context']],key=lambda r:(r['source_id'],int(r['replicate_ordinal'])))
        b=np.stack([vectors[r['run_id']] for r in rr])
        v=b.mean(axis=1)
        total=b.mean(axis=(1,2))[:,None]
        assert np.allclose(total[:,0],v.mean(axis=1),atol=1e-15,rtol=0)
        representations=dict(TOTAL_RATE_1D=total,STATIC_SPATIAL_30D=v,
            AMPLITUDE_REMOVED_SPATIAL_30D=v-v.mean(axis=1)[:,None],COMPOSITIONAL_SPATIAL_30D=compose(v))
        for i,r in enumerate(rr):
            zero=bool(v[i].sum()==0)
            zero_rows.append(dict(run_id=r['run_id'],context=c['context'],source=r['source_id'],
                static_profile_zero=zero,total_fraction=float(total[i,0]),zero_rule='all-zero vector'))
            if zero:
                zeros.append(r['run_id'])
        loc,per_draw=location_destroyed(v,cidx)
        draws.append(per_draw)
        per={arm:prior.all_energy(value) for arm,value in representations.items()}
        per['LOCATION_DESTROYED']=loc
        for arm,values in per.items():
            s,z=prior.summary(values)
            z_all[arm].append(z)
            assert np.allclose(values,values[prior.COMPLEMENT_INDEX],atol=1e-12,rtol=0)
            records.append(dict(context=c['context'],house=c['house'],wind=c['wind'],gas=c['gas'],arm=arm,**s))
            for i,value in enumerate(values):
                null_rows.append(dict(context=c['context'],arm=arm,assignment_index=i,
                    group_a_indices=','.join(map(str,prior.ASSIGN[i])),energy=float(value),z=float(z[i]),observed=i==0))
            if arm=='STATIC_SPATIAL_30D':
                prev=next(r for r in previous if r['context']==c['context'] and r['arm']=='STATIC_COLLAPSED_30D')
                assert all(abs(float(prev[k])-s[k])<1e-12 for k in ('energy','z','exact_p','null_mean','null_sd'))
        print(json.dumps(dict(context=c['context'],stats={r['arm']:dict(z=r['z'],exact_p=r['exact_p']) for r in records if r['context']==c['context']}),sort_keys=True),flush=True)
    prior.table(out/'CONTEXT_REPRESENTATION_RESULTS.tsv',records)
    prior.table(out/'EXACT_70_ASSIGNMENT_NULLS.tsv',null_rows)
    prior.table(out/'ZERO_PROFILE_AND_TOTAL_RATE.tsv',zero_rows)
    np.save(out/'LOCATION_ALL_ASSIGNMENT_DRAW_ENERGIES.npy',np.stack(draws),allow_pickle=False)
    rng=np.random.default_rng(2026100102)
    indices=rng.integers(0,70,(8,prior.N_AGGREGATE))
    status,aggregates,agg_null_hashes={}, {}, {}
    for arm in ARMS:
        z=np.stack(z_all[arm])
        ag,null=aggregate(z,indices)
        aggregates[arm]=ag
        agg_null_hashes[arm]=dict(dtype=str(null.dtype),shape=list(null.shape),
            sha256=hashlib.sha256(null.tobytes(order='C')).hexdigest(),
            regeneration='default_rng(2026100102), frozen exact context Z values and common indices')
        arm_records=[r for r in records if r['arm']==arm]
        n_above=sum(r['above_null_median'] for r in arm_records)
        n_sig=sum(r['exact_p']<=.05 for r in arm_records)
        p_sign=float(binomtest(n_above,8,.5,alternative='greater').pvalue)
        status[arm]=dict(above_null_median_contexts=n_above,exact_p_le_005_contexts=n_sig,
            exact_direction_sign_test_p=p_sign,aggregate_mc_p=ag['p_plus_one'],
            stable=n_above>=7 and n_sig>=6 and p_sign<.05 and ag['p_plus_one']<.05)
    prior.js(out/'AGGREGATE_NULL_BYTE_HASHES.json',agg_null_hashes)
    prior.js(out/'AGGREGATE_PERMUTATION_BY_ARM.json',aggregates)
    effects=[]
    for c in contexts:
        r={r['arm']:r for r in records if r['context']==c['context']}
        effects.append(dict(context=c['context'],house=c['house'],
            z_total=r['TOTAL_RATE_1D']['z'],z_static=r['STATIC_SPATIAL_30D']['z'],
            z_centered=r['AMPLITUDE_REMOVED_SPATIAL_30D']['z'],z_composition=r['COMPOSITIONAL_SPATIAL_30D']['z'],
            z_location_destroyed=r['LOCATION_DESTROYED']['z'],
            delta_location_z=r['STATIC_SPATIAL_30D']['z']-r['LOCATION_DESTROYED']['z'],
            delta_location_energy=r['STATIC_SPATIAL_30D']['energy']-r['LOCATION_DESTROYED']['energy']))
    prior.table(out/'LOCATION_IDENTITY_EFFECTS.tsv',effects)
    locvals=[r['delta_location_z'] for r in effects]
    drop=dict(median_delta_z=float(np.median(locvals)),**prior.sign_test(locvals))
    drop['diagnostic_drop']=drop['median_delta_z']>0 and drop['positive']>=6 and drop['exact_one_sided_p']<.05
    t,cent,comp=[status[a]['stable'] for a in ('TOTAL_RATE_1D','AMPLITUDE_REMOVED_SPATIAL_30D','COMPOSITIONAL_SPATIAL_30D')]
    if t and not cent and not comp:
        decision='STATIC_SIGNAL_PRIMARILY_AMPLITUDE'
    elif cent and comp and drop['diagnostic_drop']:
        decision='STATIC_SIGNAL_PRIMARILY_SPATIAL_PATTERN'
    elif t and (cent or comp):
        decision='STATIC_SIGNAL_MIXED'
    else:
        decision='STATIC_SIGNAL_UNRESOLVED'
    houses=[]
    for h in ('House01','House02'):
        for arm in ARMS:
            rr=[r for r in records if r['house']==h and r['arm']==arm]
            houses.append(dict(house=h,arm=arm,contexts=4,exact_p_le_005_count=sum(r['exact_p']<=.05 for r in rr),
                median_z=float(np.median([r['z'] for r in rr])),above_null_median=sum(r['above_null_median'] for r in rr)))
    prior.table(out/'HOUSE_REPRESENTATION_SUMMARY.tsv',houses)
    prior.js(out/'LOCATION_PRESERVATION_AUDIT.json',dict(pass_=True,draws_per_context=1000,
        actual_runs=64,profile_multisets_checked=64000,all_profile_sums_means_norms_preserved=True,
        independent_per_actual_sample=True,rng_source_blind=True,transformation_reused_under_all_70_labels=True,
        direct_draw_arithmetic_pass=True,source_surrogates_are_new_independent_samples=False))
    prior.js(out/'IMPLEMENTATION_SHA256.json',{p.relative_to(ROOT).as_posix():prior.sha(p) for p in
        (PREVIOUS,Path(__file__),ROOT/'research/source_spatial_information_t02/T02_PROTOCOL_FREEZE.md')})
    result=dict(decision=decision,diagnostic_only=True,new_main_innovation_pass=False,source_stability=status,
        location_identity_drop=drop,zero_profile_count=len(zeros),zero_profile_runs=zeros,
        independent_sample_contract='PASS',source_geometry_scope='xyz configuration; not pure xy or continuous identifiability',
        static_t01b_parity_pass=True,prior_scientific_decisions_unchanged=True,new_plumes=0,pmfs_runs=0,
        networks_trained=0,confirmation_or_house03_opened=False,fixed_z_experiment_not_authorized=True,
        completed_and_stopped=True)
    prior.js(out/'T02_RESULT.json',result)
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--metadata-only',action='store_true')
    args=p.parse_args()
    run(args.output.resolve(),args.metadata_only)
