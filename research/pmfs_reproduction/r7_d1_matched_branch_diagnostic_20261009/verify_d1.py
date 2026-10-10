"""Verify saved D1, D0, and fixed-library comparisons. NumPy/PyYAML required.
Default is read-only: no compilation, ROS, or forward simulation.
--write-summary regenerates derived JSON/CSV only.
"""
from pathlib import Path
import json,csv,hashlib,sys
import numpy as np
import yaml
p=Path(__file__).resolve().parent
def js(n):return json.loads((p/n).read_text(encoding='utf-8'))
def rows(n):
    with (p/n).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def binary(n,dtype='<f8'):return np.frombuffer((p/n).read_bytes(),dtype=dtype)
run=js('run/RUN_RESULT.json');complete=js('result/COMPLETE.json')
assert run['exit_code']==0 and run['shadow_source_updates']==1 and run['native_goals']==run['ROS_nodes_started']==run['new_gas_generations']==0
assert complete['observations']==35 and complete['appended_observations']==0
assert js('run/SOURCE_HASH_GATE.json')['actual_SHA256']==js('EXPECTED_FROZEN_SOURCE_HASHES.json')
assert js('run/BUILD_RESULT.json')['objects_SHA256']==js('frozen_D0/run/BUILD_RESULT.json')['objects_SHA256']
assert js('result/CONTINUATION_RNG.json')==js('frozen_D0/result/CONTINUATION_RNG.json')
gate=js('result/MEASUREMENT_GATE.json');assert gate['max_logOdds_abs']==gate['max_omega_abs']==gate['max_confidence_abs']==0
oldcode=(p/'frozen_D0/shadow_update.cpp').read_text()
expectedcode=oldcode.replace('e < events.size()','e < 35').replace('\\"observations\\":40,\\"appended_observations\\":5','\\"observations\\":35,\\"appended_observations\\":0')
assert (p/'shadow_update.cpp').read_text()==expectedcode
for name in ['Fixture.hpp','Audit.hpp']:assert (p/name).read_bytes()==(p/'frozen_D0'/name).read_bytes()
m=js('diagnostic_input/metadata.json');old=rows('diagnostic_input/input.csv');one=rows('result/shadow_update/input.csv');two=rows('frozen_D0/result/shadow_update/input.csv')
mask=np.array([int(r['occupancy'])==1 for r in old]);assert mask.sum()==518
events=rows('diagnostic_input/measurement_events.csv');reconstructed=rows('result/measurement_reconstruction.csv')
assert len(events)==40 and len(reconstructed)==35 and [r['stamp_ns'] for r in reconstructed]==[r['stamp_ns'] for r in events[:35]]
for i,r in enumerate(one):
    for key in ['logOdds','omega','confidence','u','v','occupancy']:assert r[key]==old[i][key],(i,key)
    assert float(r['prior_posterior'])==binary('diagnostic_input/posterior.f64')[i]
assert rows('result/shadow_update/coarse_tree.csv')==rows('diagnostic_input/coarse_tree.csv')==rows('frozen_D0/result/shadow_update/coarse_tree.csv')
assert (p/'result/shadow_update/gaussian_cache.f32').read_bytes()==(p/'frozen_D0/result/shadow_update/gaussian_cache.f32').read_bytes()
wind=js('WIND_CONTINUATION_QUALIFICATION.json');assert wind['max_abs_difference']==0 and len(wind['free_wind_cells'])==518
params=yaml.safe_load((p/'diagnostic_input/resolved_GSL_parameters.yaml').read_text())['/PioneerP3DX/GSL']['ros__parameters']
assert params['useWindGroundTruth'] is True and params['sourceDiscriminationPower']==.3
q0=binary('diagnostic_input/posterior.f64');q1=binary('result/shadow_update/posterior.f64');q2=binary('frozen_D0/result/shadow_update/posterior.f64')
for q in [q0,q1,q2]:assert np.all(q>=0) and np.all(q[~mask]==0) and abs(q.sum()-1)<1e-12
c1=rows('result/shadow_update/candidates.csv');c2=rows('frozen_D0/result/shadow_update/candidates.csv')
assert len(c1)==106 and len(c2)==104
coarse=rows('diagnostic_input/coarse_tree.csv');assert len(coarse)==72
assert [r['candidate_id'] for r in c1[:72]]==[r['node_id'] for r in coarse]==[r['candidate_id'] for r in c2[:72]]
same_fields=['candidate_id','rng_before','rng_after','gaussian_index_before','gaussian_index_after','point_count']
for a,b in zip(c1[:72],c2[:72]):
    for key in same_fields:assert a[key]==b[key]
    for suffix in ['.f32','_unblurred.f32']:
        name='maps/'+a['candidate_id']+suffix
        assert (p/'result/shadow_update'/name).read_bytes()==(p/'frozen_D0/result/shadow_update'/name).read_bytes()
    assert (p/'result/shadow_update'/a['points_file']).read_bytes()==(p/'frozen_D0/result/shadow_update'/b['points_file']).read_bytes()
rng=js('result/CONTINUATION_RNG.json');previous_rng=rng['rng_before_shadow'];previous_noise=rng['gaussian_index_before_shadow']
for r in c1:
    assert r['rng_before']==previous_rng and int(r['gaussian_index_before'])==previous_noise and int(r['gaussian_ready_before'])==1
    assert int(r['rng_after'])==int(r['rng_before'])*pow(16807,2*int(r['point_count']),2147483647)%2147483647
    previous_rng=r['rng_after'];previous_noise=int(r['gaussian_index_after'])
assert previous_rng==complete['rng_after_shadow'] and previous_noise==complete['gaussian_index_after_shadow']
def rescore(library,candidates,measured):
    prob=1-1/(1+np.exp(np.array([float(r['logOdds']) for r in measured])))
    weight=np.minimum(1,np.array([float(r['confidence']) for r in measured]))
    raw=np.zeros(len(mask));score_error=0
    for r in candidates:
        hit=binary(library+'/'+r['map_file'],'<f4').astype(float)
        assert len(hit)==1551 and np.all(np.isfinite(hit)) and np.all((hit>=0)&(hit<=1))
        score=float(np.prod((1+((1-np.abs(prob-hit)*.3)-1)*weight)[mask]))
        i,j,wi,hj=[int(r[k]) for k in ['origin_i','origin_j','size_i','size_j']]
        cells=[x+y*m['width'] for y in range(j,j+hj) for x in range(i,i+wi)]
        assert all(mask[x] for x in cells);raw[cells]=score
        score_error=max(score_error,abs(score-float(r['score']))/float(r['score']))
    assert np.all(raw[mask]>0)
    return raw/raw.sum(),score_error
check1,e1=rescore('result/shadow_update',c1,one);assert e1<1e-10 and np.max(abs(check1-q1))<1e-12
check2,e2=rescore('frozen_D0/result/shadow_update',c2,two);assert e2<1e-10 and np.max(abs(check2-q2))<1e-12
fixed35,_=rescore('frozen_D0/result/shadow_update',c2,old)
xy=np.array([[m['origin_x']+(i%m['width']+.5)*m['cell_size'],m['origin_y']+(i//m['width']+.5)*m['cell_size']] for i in range(1551)])
truth=np.array([0.,-1.]);distance=np.linalg.norm(xy-truth,axis=1)
origin=np.float32([m['origin_x'],m['origin_y']]);size=np.float32(m['cell_size'])
xy32=np.float32(origin+np.float32([[i%m['width']+.5,i//m['width']+.5] for i in range(1551)])*size)
def stats(q):
    mean=(q[:,None]*xy).sum(0);native_mean=np.float32((q[:,None]*xy32).sum(0));delta=np.float32(xy32-native_mean).astype(float)
    maximum=np.flatnonzero(q==q.max());variance=float((q[:,None]*(xy-mean)**2).sum())
    return dict(variance_world_grid=variance,native_float_variance=float((q[:,None]*delta**2).sum()),
                MAP_error_m=float(distance[maximum[0]]),MAP_xy=xy[maximum[0]].tolist(),MAP_ties=len(maximum),
                mean_error_m=float(np.linalg.norm(mean-truth)),mean_xy=mean.tolist(),
                truth_1m_mass=float(q[distance<=1].sum()),max_cell_probability=float(q.max()))
summary_rows=dict(R7_original35=stats(q0),D0_fixed_library35=stats(fixed35),D1_matched_branch35=stats(q1),D0_matched_branch40=stats(q2))
assert abs(summary_rows['D1_matched_branch35']['native_float_variance']-complete['native_variance_formula'])<1e-10
review=js('PAIRED_REVIEW_REPRODUCTION.json');assert abs(summary_rows['D0_fixed_library35']['mean_error_m']-review['old35']['mean_error'])<1e-12
assert abs(summary_rows['D0_fixed_library35']['variance_world_grid']-review['old35']['variance'])<1e-12
assert summary_rows['D1_matched_branch35']['MAP_xy']==summary_rows['D0_matched_branch40']['MAP_xy']
ids1={r['candidate_id'] for r in c1};ids2={r['candidate_id'] for r in c2};common=ids1&ids2
same_maps=sum((p/'result/shadow_update/maps'/(n+'.f32')).read_bytes()==(p/'frozen_D0/result/shadow_update/maps'/(n+'.f32')).read_bytes() for n in common)
changes={}
for key in ['logOdds','omega','confidence']:
    a=np.array([float(r[key]) for r in old]);b=np.array([float(r[key]) for r in two])
    changes[key]=dict(changed_cells=int(np.count_nonzero(a!=b)),max_abs_change=float(np.max(abs(a-b))))
assert not mask[846] and q0[846]==q1[846]==q2[846]==0
decision=dict(verdict='MATCHED_BRANCH_DIAGNOSTIC_PASS_PHYSICAL_MECHANISM_HOLD',D1_updates=1,new_native_goals=0,
    paired_review='PASS_FIXED_LIBRARY_CONDITIONAL_DIAGNOSTIC',matched_state='PASS_SAME_RNG_NOISE_WIND_GEOMETRY_AND_PARAMETERS',
    comparison=summary_rows,coarse_simulations_identical=72,D1_candidate_simulations=len(c1),D0_candidate_simulations=len(c2),
    common_candidate_nodes=len(common),common_maps_identical=same_maps,common_fine_maps_different=len(common)-same_maps,
    D1_only_candidate_nodes=sorted(ids1-ids2),D0_only_candidate_nodes=sorted(ids2-ids1),
    measurement_map_changes=changes,D1_rng_after=complete['rng_after_shadow'],D0_rng_after=js('frozen_D0/result/COMPLETE.json')['rng_after_shadow'],
    original_R7_success=False,geometry_changed=False,source_cell_supported=False,wind_is_time_varying=False,
    model_failure_proven=False,D1_score_max_relative_error=e1,D1_posterior_reconstruction_max_abs=float(np.max(abs(check1-q1))),
    next_action='STOP_AWAIT_REVIEW_NO_AUTOMATIC_PHYSICAL_SAMPLE_GENERATION')
if '--write-summary' in sys.argv:
    (p/'D1_RESULT.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')
    with (p/'R7_D1_COMPARISON.csv').open('w',newline='',encoding='utf-8-sig') as f:
        keys=['condition','variance_world_grid','native_float_variance','MAP_error_m','mean_error_m','truth_1m_mass','max_cell_probability']
        w=csv.DictWriter(f,keys);w.writeheader()
        for condition,r in summary_rows.items():w.writerow(dict(condition=condition,**{k:r[k] for k in keys[1:]}))
    with (p/'R7_D1_CAUSE_EVIDENCE.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['factor','observed_evidence','interpretation','limit'])
        w.writerow(['measurement_map',json.dumps(changes),'Extra five blocks change weights and posterior spread; D0/D1 MAP remains same.','Five same-stop blocks are correlated; no independent observation qualification.'])
        w.writerow(['simulation_refinement',f'72 coarse maps identical; common fine maps differing={len(common)-same_maps}; D1=106 D0=104','Without the extra five blocks, D1 MAP already equals D0 MAP and differs from R7.','Branch comparison includes adaptive refinement and different downstream RNG consumption.'])
        w.writerow(['geometry','Truth cell 846 excluded in R7/D0/D1; nearest legal center 0.424490m','Fixed support limits exact source representation.','Unchanged support cannot alone explain between-posterior differences; means need not stay within support.'])
manifest=p/'SHA256_MANIFEST.json'
if manifest.exists():
    for n,h in js('SHA256_MANIFEST.json').items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
print(json.dumps(decision))
