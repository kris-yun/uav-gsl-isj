"""Frozen independent-realization Energy audit; discovery inputs only."""
import argparse
import csv
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import binomtest, beta

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT/'evidence/ocb_r2'
INPUT = EV/'mechanism_census_r0/inputs'
ASSIGN = np.array(list(itertools.combinations(range(8), 4)), dtype=np.int64)
COMPLEMENT = np.array([[i for i in range(8) if i not in a] for a in ASSIGN])
COMPLEMENT_INDEX = np.array([next(i for i,b in enumerate(ASSIGN) if np.array_equal(b,a)) for a in COMPLEMENT])
N_C2, N_AGGREGATE, TOL = 1000, 1000000, 1e-12


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def table(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def js(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def energy_matrix(distance, a, b):
    return (2*distance[np.ix_(a,b)].mean()-distance[np.ix_(a,a)].mean()-distance[np.ix_(b,b)].mean())


def all_energy(x):
    distance = cdist(x,x)/np.sqrt(x.shape[1])
    return np.array([energy_matrix(distance,a,b) for a,b in zip(ASSIGN,COMPLEMENT)])


def c2_permutations(k, cidx, group, n=N_C2):
    rng = np.random.default_rng(np.random.SeedSequence([2026093002,cidx,group,0,0]))
    return np.argsort(rng.random((n,10,k)), axis=-1, kind='stable')


def apply_c2(ref, permutation):
    base = ref.transpose(1,0,2)
    return np.take_along_axis(np.broadcast_to(base,(len(permutation),10,len(ref),30)),
        permutation[:,:,:,None],axis=2).transpose(0,2,1,3)


def c2_energy(x, cidx):
    # x=(8,10,30). The lookup gives exact binary squared Euclidean distances.
    hamming = np.count_nonzero(x.transpose(1,0,2)[:,:,None,:] != x.transpose(1,0,2)[:,None,:,:],axis=-1)
    permutations = [c2_permutations(4,cidx,g) for g in range(2)]
    per_draw = np.empty((70,N_C2), dtype=np.float64)
    for index,(a,b) in enumerate(zip(ASSIGN,COMPLEMENT)):
        banks = [apply_c2(x[ids],permutations[g]) for g,ids in enumerate((a,b))]
        for ids,bank in zip((a,b),banks):
            assert np.array_equal(bank.sum(axis=1),np.broadcast_to(x[ids].sum(axis=0),(N_C2,10,30)))
            assert np.array_equal(np.sort(bank,axis=1),np.broadcast_to(np.sort(x[ids],axis=0),(N_C2,4,10,30)))
            # Sorting coordinates alone is not a full snapshot-multiset proof.
            codes = (bank.astype(np.int64)*(1 << np.arange(30))).sum(axis=-1)
            original = (x[ids].astype(np.int64)*(1 << np.arange(30))).sum(axis=-1)
            assert np.array_equal(np.sort(codes,axis=1),np.broadcast_to(np.sort(original,axis=0),(N_C2,4,10)))
        ids = np.concatenate([a[permutations[0]], b[permutations[1]]],axis=2)
        squared = np.zeros((N_C2,8,8), dtype=np.int16)
        for t in range(10):
            squared += hamming[t,ids[:,t,:,None],ids[:,t,None,:]]
        distance = np.sqrt(squared.astype(np.float64)/300)
        values = 2*distance[:,:4,4:].mean(axis=(1,2))-distance[:,:4,:4].mean(axis=(1,2))-distance[:,4:,4:].mean(axis=(1,2))
        per_draw[index] = values
        if index == 0:
            for draw in (0,1,2):
                direct = np.concatenate([banks[0][draw],banks[1][draw]]).reshape(8,300).astype(float)
                actual = energy_matrix(cdist(direct,direct)/np.sqrt(300),np.arange(4),np.arange(4,8))
                assert abs(actual-values[draw]) < 1e-12
    means = per_draw.mean(axis=1)
    means = (means+means[COMPLEMENT_INDEX])/2
    return means, per_draw


def summary(values):
    sd = float(values.std(ddof=0))
    zvalues = (values-values.mean())/sd if sd>0 else np.zeros_like(values)
    return dict(energy=float(values[0]), null_mean=float(values.mean()), null_sd=sd,
        null_median=float(np.median(values)), exact_p=float(np.count_nonzero(values>=values[0]-TOL)/70),
        null_percentile=float(np.count_nonzero(values<=values[0]+TOL)/70),
        z=float(zvalues[0]), above_null_median=bool(values[0]>np.median(values)+TOL)), zvalues


def sign_test(values):
    v = np.asarray(values)
    plus, minus = int(np.count_nonzero(v>TOL)), int(np.count_nonzero(v < -TOL))
    return dict(positive=plus,negative=minus,ties=len(v)-plus-minus,
        exact_one_sided_p=float(binomtest(plus,plus+minus,.5,alternative='greater').pvalue) if plus+minus else 1.)


def metadata(out):
    runs = list(csv.DictReader((ROOT/'evidence/cdsi_t01/EXACT_64_RUN_MANIFEST.tsv').open(encoding='utf-8'), delimiter='\t'))
    assert len(runs)==64 and len({r['run_id'] for r in runs})==64
    assert len({int(r['master_seed']) for r in runs})==64
    contexts, result = [], []
    for c in range(8):
        items = sorted([r for r in runs if r['context']==f'X{c:02d}'],key=lambda r:(r['source_id'],int(r['replicate_ordinal'])))
        assert len(items)==8
        sources = sorted({r['source_id'] for r in items})
        assert len(sources)==2
        keys, params, xyz = [], [], []
        for r in items:
            p = ROOT/r['metadata_file']
            m = load_json(p)
            assert sha(p)==r['metadata_sha256']
            assert load_json(Path(r['archive_metadata_path']))==m
            assert m['master_seed']==int(r['master_seed']) and m['source_id']==r['source_id']
            assert m['omp_num_threads']==1
            s = m['simulation_parameters']
            keys.append((m['house'],m['wind_id'],s['gas_type'],json.dumps(m['asset_checks'],sort_keys=True),
                m['generator_binary_sha256'],m['qualification_standard']['timeline_sha256'],
                m['qualification_standard']['wind_index_sequence_sha256']))
            params.append({k:v for k,v in s.items() if k not in {'source_position_x','source_position_y','source_position_z','results_location'}})
            xyz.append(tuple(float(s['source_position_'+a]) for a in 'xyz'))
        assert len(set(keys))==1 and all(p==params[0] for p in params)
        assert all(len([r for r in items if r['source_id']==s])==4 for s in sources)
        assert len(set(xyz[:4]))==len(set(xyz[4:]))==1 and xyz[0]!=xyz[4]
        contexts.append(dict(context=f'X{c:02d}',house=items[0]['house'],wind=items[0]['wind_id'],gas=params[0]['gas_type'],
            source_a=sources[0],source_b=sources[1],source_a_xyz=list(xyz[0]),source_b_xyz=list(xyz[4]),z_differs=xyz[0][2]!=xyz[4][2]))
        result.append(dict(context=f'X{c:02d}',house=items[0]['house'],run_count=8,distinct_seeds=8,
            non_source_parameters_match=True,asset_generator_timebase_match=True,same_rng_law_contract=True,
            same_master_seed_required=False,decision='PASS'))
    table(out/'EXACT_64_RUN_MANIFEST.tsv',runs)
    table(out/'INDEPENDENT_SAMPLE_CONTRACT.tsv',result)
    js(out/'SOURCE_GEOMETRY.json',dict(contexts=contexts,interpretation='Source xyz configuration, not pure xy displacement.'))
    return runs, contexts


def self_test():
    assert len(ASSIGN)==70 and np.array_equal(COMPLEMENT_INDEX[COMPLEMENT_INDEX],np.arange(70))
    zeros = np.zeros((8,300))
    assert np.array_equal(all_energy(zeros),np.zeros(70))
    s,_ = summary(all_energy(zeros))
    assert s['exact_p']==1 and s['z']==0
    example = np.concatenate([np.zeros((4,1)),np.ones((4,1))])
    assert abs(all_energy(example)[0]-2)<1e-12
    assert np.array_equal(all_energy(example),all_energy(example)[COMPLEMENT_INDEX])
    # Synthetic parity against the actual, hash-bound R0 routine, at its K=3.
    file = ROOT/'research/ocb_r2/mechanism_census_r0/run_census.py'
    spec = importlib.util.spec_from_file_location('r0_frozen',file)
    r0 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r0)
    rng = np.random.default_rng(1234567)
    ref = rng.integers(0,2,(3,10,30)).astype(bool)
    target = rng.integers(0,2,(10,30)).astype(bool)
    perm = c2_permutations(3,0,0)
    generated = apply_c2(ref,perm)
    audits={'C2':dict(banks=0,binary=0,marginals=0,snapshot_multiset=0)}
    actual = r0.surrogate_scores(ref,target,'C2',0,0,0,0,audits)
    expected = r0.energy_batch(generated.reshape(N_C2,3,300),target.reshape(300))
    assert np.array_equal(actual,expected)
    return dict(assignment_count=70,zero_null_pass=True,known_energy_two_pass=True,
        complement_symmetry_pass=True,r0_c2_k3_bitwise_parity=True,r0_script_sha256=sha(file))


def main(out, metadata_only=False):
    out.mkdir(parents=True,exist_ok=True)
    checks = self_test()
    runs, contexts = metadata(out)
    js(out/'IMPLEMENTATION_CHECKS.json',checks)
    if metadata_only:
        print('Metadata independent-sample contract PASS: 8 contexts, 64 runs. No target values loaded.')
        return
    frozen = load_json(EV/'mechanism_census_r0/R0_INPUT_HASHES.json')
    inputs, tensors = [], {}
    for r in runs:
        p = INPUT/(r['run_id']+'.pooled.npy')
        digest = sha(p)
        assert digest==frozen['pooled_tensor_sha256'][r['run_id']]
        x = np.load(p,allow_pickle=False)
        assert x.shape==(10,30) and np.isfinite(x).all() and (x>=0).all()
        tensors[r['run_id']]=x>0
        inputs.append(dict(run_id=r['run_id'],sha256=digest,binary_definition='C>0',shape='10x30'))
    table(out/'FROZEN_INPUT_SHA256.tsv',inputs)
    rows, null_rows, z_full, c2_arrays = [], [], [], []
    for cidx,c in enumerate(contexts):
        rr = sorted([r for r in runs if r['context']==c['context']],key=lambda r:(r['source_id'],int(r['replicate_ordinal'])))
        x = np.stack([tensors[r['run_id']] for r in rr])
        values = dict(FULL_DYNAMIC_300D=all_energy(x.reshape(8,300).astype(float)),
            STATIC_COLLAPSED_30D=all_energy(x.mean(axis=1)))
        values['C2_PAIRING_DESTROYED'], draw_values = c2_energy(x,cidx)
        c2_arrays.append(draw_values)
        summaries = {}
        for arm,vec in values.items():
            s,z = summary(vec)
            assert np.allclose(vec,vec[COMPLEMENT_INDEX],atol=1e-12,rtol=0)
            summaries[arm]=s
            rows.append(dict(context=c['context'],house=c['house'],wind=c['wind'],gas=c['gas'],arm=arm,**s))
            if arm=='FULL_DYNAMIC_300D':
                z_full.append(z)
            for i,v in enumerate(vec):
                null_rows.append(dict(context=c['context'],arm=arm,assignment_index=i,
                    group_a_indices=','.join(str(j) for j in ASSIGN[i]),energy=float(v),z=float(z[i]),observed=i==0))
        print(json.dumps(dict(context=c['context'],statistics=summaries),sort_keys=True),flush=True)
    table(out/'CONTEXT_ENERGY_RESULTS.tsv',rows)
    table(out/'EXACT_70_ASSIGNMENT_NULLS.tsv',null_rows)
    np.save(out/'C2_ALL_ASSIGNMENT_DRAW_ENERGIES.npy',np.stack(c2_arrays),allow_pickle=False)
    effect_rows = []
    for c in contexts:
        arm = {r['arm']:r for r in rows if r['context']==c['context']}
        f,s,q = [arm[a] for a in ('FULL_DYNAMIC_300D','STATIC_COLLAPSED_30D','C2_PAIRING_DESTROYED')]
        effect_rows.append(dict(context=c['context'],house=c['house'],z_full=f['z'],z_static=s['z'],z_c2=q['z'],
            delta_static=f['z']-s['z'],delta_pairing=f['z']-q['z'],
            full_above_null_median=f['above_null_median'],full_exact_p=f['exact_p']))
    table(out/'DYNAMIC_INFORMATION_EFFECTS.tsv',effect_rows)
    z_full=np.stack(z_full)
    aggregate_observed=float(z_full[:,0].mean())
    rng=np.random.default_rng(2026100102)
    assignment_indices=rng.integers(0,70,size=(8,N_AGGREGATE))
    aggregate_null=z_full[np.arange(8)[:,None],assignment_indices].mean(axis=0)
    exceeds=int(np.count_nonzero(aggregate_null>=aggregate_observed-TOL))
    aggregate_p=(1+exceeds)/(N_AGGREGATE+1)
    ci=[float(beta.ppf(.025,exceeds,N_AGGREGATE-exceeds+1)) if exceeds else 0.,
        float(beta.ppf(.975,exceeds+1,N_AGGREGATE-exceeds)) if exceeds<N_AGGREGATE else 1.]
    np.save(out/'STRATIFIED_AGGREGATE_PERMUTATION.npy',aggregate_null,allow_pickle=False)
    aggregate=dict(statistic='mean of eight FULL exact-permutation-standardized effects',observed=aggregate_observed,
        method='Monte Carlo stratified source-label permutation',draws=N_AGGREGATE,seed=2026100102,
        exact_joint_assignments=70**8,exceedances=exceeds,p_plus_one=aggregate_p,
        monte_carlo_binomial_95_interval=ci,context_tests_exact=True,aggregate_exhaustive=False)
    js(out/'AGGREGATE_PERMUTATION.json',aggregate)
    above=[r['full_above_null_median'] for r in effect_rows]
    g1_sign=float(binomtest(sum(above),8,.5,alternative='greater').pvalue)
    g1=dict(above_null_median_count=sum(above),exact_context_p_le_005_count=sum(r['full_exact_p']<=.05 for r in effect_rows),
        exact_direction_sign_test_p=g1_sign,aggregate_p=aggregate_p)
    g1['pass']=g1['above_null_median_count']>=7 and g1['exact_context_p_le_005_count']>=6 and g1_sign<.05 and aggregate_p<.05
    gates={'G1_FULL_SOURCE_DISTRIBUTION':g1}
    for name,field in [('G2_DYNAMIC_ADVANTAGE','delta_static'),('G3_PAIRING_ADVANTAGE','delta_pairing')]:
        effects=[r[field] for r in effect_rows]
        gate=dict(median=float(np.median(effects)),**sign_test(effects),sign_p_is_descriptive=True)
        gate['pass']=gate['median']>0 and gate['positive']>=6
        gates[name]=gate
    if not g1['pass']:
        decision='CDSI_T01B_NO_STABLE_SOURCE_DISTRIBUTION_INFORMATION_STOP'
    elif gates['G2_DYNAMIC_ADVANTAGE']['pass'] or gates['G3_PAIRING_ADVANTAGE']['pass']:
        decision='CDSI_T01B_DYNAMIC_SOURCE_INFORMATION_PASS'
    else:
        decision='CDSI_T01B_SOURCE_INFORMATION_STATIC_ONLY_HOLD'
    house_rows=[]
    for house in ('House01','House02'):
        er=[r for r in effect_rows if r['house']==house]
        house_rows.append(dict(house=house,contexts=4,median_z_full=float(np.median([r['z_full'] for r in er])),
            median_delta_static=float(np.median([r['delta_static'] for r in er])),
            median_delta_pairing=float(np.median([r['delta_pairing'] for r in er])),
            positive_delta_static=sum(r['delta_static']>TOL for r in er),positive_delta_pairing=sum(r['delta_pairing']>TOL for r in er),
            full_exact_p_le_005=sum(r['full_exact_p']<=.05 for r in er)))
    table(out/'HOUSE_SUMMARY.tsv',house_rows)
    js(out/'C2_PRESERVATION_AUDIT.json',dict(pass_=True,contexts=8,assignments_per_context=70,
        draws_per_assignment=N_C2,source_banks_checked=8*70*N_C2*2,
        full_snapshot_multiset_pass=True,all_300_marginals_pass=True,binary_legal=True,
        rebuilt_after_every_label_assignment=True,realization_budget_per_source=4,
        surrogates_are_independent_physical_samples=False,lookup_direct_distance_parity=True))
    source_paths=[Path(__file__),ROOT/'research/cdsi_t01b/IMPLEMENTATION_FREEZE.md',ROOT/'research/cdsi_t01b/protocol/USER_EXECUTION_REQUEST.txt']
    js(out/'IMPLEMENTATION_SHA256.json',{p.relative_to(ROOT).as_posix():sha(p) for p in source_paths})
    result=dict(decision=decision,gates=gates,independent_sample_contract='PASS',runs=64,contexts=8,
        source_geometry_scope='Different xyz source configurations; not pure xy or continuous identifiability.',
        old_paired_protocol_result_unchanged='CDSI_T01_MATCHED_INTERVENTION_FAIL',
        simulation_count=0,network_training_count=0,pmfs_run_count=0,confirmation_or_house03_opened=False,
        aggregate_test='Monte Carlo stratified permutation; individual context tests exact 70 assignments',
        optional_secondary_not_executed=True,completed_and_stopped=True)
    js(out/'CDSI_T01B_RESULT.json',result)
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--metadata-only',action='store_true')
    args=parser.parse_args()
    main(args.output.resolve(),args.metadata_only)
