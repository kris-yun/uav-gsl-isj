"""Read-only D0 verification; requires NumPy and PyYAML, no ROS or simulation.
Use --write-summary only to regenerate derived JSON/CSV, never raw evidence.
"""
from pathlib import Path
import csv,hashlib,json,sys
import numpy as np
import yaml

p=Path(__file__).resolve().parent
def js(n):return json.loads((p/n).read_text(encoding='utf-8'))
def rows(n):
    with (p/n).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def vec(n):return np.frombuffer((p/n).read_bytes(),dtype='<f8')
base=vec('diagnostic_input/posterior.f64');shadow=vec('result/shadow_update/posterior.f64')
m=js('diagnostic_input/metadata.json');initial=rows('diagnostic_input/input.csv');new=rows('result/shadow_update/input.csv')
mask=np.array([int(r['occupancy']) for r in initial])==1
assert mask.sum()==518 and len(base)==len(shadow)==1551
for q in [base,shadow]:assert np.all(q>=0) and np.all(q[~mask]==0) and abs(q.sum()-1)<1e-12
run=js('run/RUN_RESULT.json');complete=js('result/COMPLETE.json');gate=js('result/MEASUREMENT_GATE.json')
assert run['exit_code']==0 and run['shadow_source_updates']==1 and run['native_goals']==run['ROS_nodes_started']==run['new_gas_generations']==0
assert complete['classification']=='COUNTERFACTUAL_DIAGNOSTIC_NOT_NATIVE_RUN' and complete['shadow_source_updates']==1
assert gate['max_logOdds_abs']==gate['max_omega_abs']==gate['max_confidence_abs']==0
assert js('pre_shadow_harness_failure/RUN_RESULT.json')['shadow_source_updates']==0
boundary=rows('result/hit_at_native_boundary_35.csv')
for i in np.flatnonzero(mask):
    for a,b in [('log_odds','logOdds'),('omega','omega'),('confidence','confidence')]:assert float(boundary[i][a])==float(initial[i][b])
events=rows('diagnostic_input/measurement_events.csv');held=rows('HELD_OUT_LAST_STOP.csv')
with (p/'frozen_R7_runtime/measurement_events.csv').open() as f:raw=list(csv.reader(f))
assert [list(r.values()) for r in events]==raw and held==events[35:]
assert len(events)==40 and all(int(r['iteration_counter'])==7 and float(r['concentration'])>.1 for r in held)
assert [int(r['block_counter']) for r in held]==list(range(5))
reconstructed=rows('result/measurement_reconstruction.csv');assert len(reconstructed)==40
assert [r['stamp_ns'] for r in reconstructed]==[r['stamp_ns'] for r in events]
assert all(int(r['hit'])==int(float(e['concentration'])>.1) for r,e in zip(reconstructed,events))
final_hit=rows('result/hit_after_event_39.csv')
for i,r in enumerate(new):
    assert r['occupancy']==initial[i]['occupancy'] and r['u']==initial[i]['u'] and r['v']==initial[i]['v']
    assert float(r['prior_posterior'])==base[i]
    for a,b in [('log_odds','logOdds'),('omega','omega'),('confidence','confidence')]:assert float(final_hit[i][a])==float(r[b])
wind=js('WIND_CONTINUATION_QUALIFICATION.json');assert len(wind['free_wind_cells'])==518 and wind['max_abs_difference']==0
clock=rows('frozen_R7_runtime/physical_clock_trace.csv');assert all(int(r['wind_index'])==10 for r in clock)
assert (p/'diagnostic_input/gaussian_cache.f32').read_bytes()==(p/'result/shadow_update/gaussian_cache.f32').read_bytes()
assert rows('diagnostic_input/coarse_tree.csv')==rows('result/shadow_update/coarse_tree.csv')
state=js('CONTINUATION_STATE.json');rng=js('result/CONTINUATION_RNG.json')
last=rows('diagnostic_input/candidates.csv')[-1]
assert rng['rng_at_last_simulation_end']==last['rng_after'] and rng['gaussian_index_before_shadow']==int(last['gaussian_index_after'])
assert rng['movement_uniform_calls']==1 and int(rng['rng_before_shadow'])==int(last['rng_after'])*pow(16807,2,2147483647)%2147483647
params=yaml.safe_load((p/'diagnostic_input/resolved_GSL_parameters.yaml').read_text())['/PioneerP3DX/GSL']['ros__parameters']
assert params['useWindGroundTruth'] is True and params['sourceDiscriminationPower']==.3 and params['refineFraction']==.1
candidates=rows('result/shadow_update/candidates.csv');assert len(candidates)==104
measured=1-1/(1+np.exp(np.array([float(r['logOdds']) for r in new])))
confidence=np.array([float(r['confidence']) for r in new])
raw_reconstructed=np.zeros(1551);max_relative_score_error=0
origin=np.float32([m['origin_x'],m['origin_y']]);size=np.float32(m['cell_size'])
previous_rng=rng['rng_before_shadow'];previous_noise=rng['gaussian_index_before_shadow']
for r in candidates:
    assert r['rng_before']==previous_rng and int(r['gaussian_index_before'])==previous_noise and int(r['gaussian_ready_before'])==1
    assert int(r['rng_after'])==int(r['rng_before'])*pow(16807,2*int(r['point_count']),2147483647)%2147483647
    previous_rng=r['rng_after'];previous_noise=int(r['gaussian_index_after'])
    h=np.frombuffer((p/'result/shadow_update'/r['map_file']).read_bytes(),dtype='<f4').astype(float)
    assert len(h)==1551 and np.all(np.isfinite(h)) and np.all((h>=0)&(h<=1))
    factor=1+((1-np.abs(measured-h)*params['sourceDiscriminationPower'])-1)*np.minimum(confidence,1)
    score=float(np.prod(factor[mask]));expected=float(r['score'])
    max_relative_score_error=max(max_relative_score_error,abs(score-expected)/expected)
    assert abs(score-expected)/expected<1e-10
    i,j,wi,hj=[int(r[k]) for k in ['origin_i','origin_j','size_i','size_j']]
    cells=[x+y*m['width'] for y in range(j,j+hj) for x in range(i,i+wi)]
    assert all(mask[x] for x in cells)
    raw_reconstructed[cells]=expected
    points=np.frombuffer((p/'result/shadow_update'/r['points_file']).read_bytes(),dtype='<f4').reshape(-1,2)
    assert len(points)==int(r['point_count'])
    low=np.float32(origin+np.float32([i,j])*size);high=np.float32(origin+np.float32([i+wi,j+hj])*size)
    assert np.all(points>=low) and np.all(points<high)
assert previous_rng==complete['rng_after_shadow'] and previous_noise==complete['gaussian_index_after_shadow']
raw_stored=np.array([float(r['score']) for r in rows('result/shadow_update/raw_cell_scores.csv')])
assert np.max(np.abs(raw_reconstructed[mask]-raw_stored[mask]))<1e-15
recomputed=raw_reconstructed/raw_reconstructed[mask].sum()
posterior_error=float(np.max(np.abs(recomputed-shadow)));assert posterior_error<1e-12
xy=np.array([[m['origin_x']+(i%m['width']+.5)*m['cell_size'],m['origin_y']+(i//m['width']+.5)*m['cell_size']] for i in range(1551)])
xy32=np.float32(origin+np.float32([[i%m['width']+.5,i//m['width']+.5] for i in range(1551)])*size)
truth=np.array([0.,-1.]);distance=np.linalg.norm(xy-truth,axis=1)
def statistics(q):
    mean=(q[:,None]*xy).sum(0);native_mean=np.float32((q[:,None]*xy32).sum(0))
    native_delta=np.float32(xy32-native_mean).astype(float)
    native_variance=float((q[:,None]*native_delta**2).sum())
    peak=np.flatnonzero(q==q.max())
    return dict(native_variance=native_variance,posterior_mean_error_m=float(np.linalg.norm(mean-truth)),
                MAP_error_m=float(distance[peak[0]]),MAP_ties=len(peak),max_cell_probability=float(q.max()),
                truth_1m_probability_mass=float(q[distance<=1].sum()),nonzero_free_cells=int(np.count_nonzero(q)),
                posterior_mean_xy=mean.tolist(),MAP_xy=xy[peak[0]].tolist(),native_mean_xy=native_mean.astype(float).tolist())
b,a=statistics(base),statistics(shadow)
assert abs(b['native_variance']-4.36309)<1e-5 and abs(a['native_variance']-complete['native_variance_formula'])<1e-10
assert np.max(np.abs(np.array(a['native_mean_xy'])-[complete['native_mean_x'],complete['native_mean_y']]))<1e-7
assert 'FAILED' in (p/'frozen_R7_runtime/native_results.csv').read_text()
linear=int((0-m['origin_x'])/m['cell_size'])+int((-1-m['origin_y'])/m['cell_size'])*m['width']
assert linear==846 and not mask[linear] and base[linear]==shadow[linear]==0
nearest=int(np.where(mask,distance,np.inf).argmin())
lo=xy-.5*m['cell_size'];hi=xy+.5*m['cell_size'];rectangle=np.maximum(np.maximum(lo-truth,truth-hi),0)
continuous=np.linalg.norm(rectangle,axis=1)
geometry=dict(truth_xyz=[0,-1,.2],truth_coarse_cell=[21,25],truth_linear_index=846,source_cell_occupancy=0,
              nearest_legal_grid_center_xy=xy[nearest].tolist(),nearest_legal_grid_center_distance_m=float(distance[nearest]),
              nearest_legal_candidate_rectangle_distance_m=float(continuous[mask].min()),
              posterior_mean_error_has_no_such_lower_bound=True,candidate_support_changed=False)
summary=dict(verdict='CONCENTRATION_IMPROVED_BUT_LOCATION_ERRORS_WORSE',classification=complete['classification'],
             qualification='CONTINUATION_STATE_AND_NATIVE_CORE_GATE_PASS',shadow_source_updates=1,new_native_goals=0,
             original_R7_success=False,baseline=b,shadow=a,geometry=geometry,
             shadow_variance_below_1_5=False,score_max_relative_error=max_relative_score_error,
             posterior_reconstruction_max_abs_error=posterior_error,
             causal_last_five_observations_effect_isolated=False,
             explanation='One extra native-rule update includes resimulation and adaptive refinement; no same-RNG no-new-observation control was run.',
             propagation_model_failure_proven=False,next_action='STOP_AWAIT_REVIEW')
if '--write-summary' in sys.argv:
    (p/'D0_RESULT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (p/'GEOMETRY_SUPPORT_EVIDENCE.json').write_text(json.dumps(geometry,indent=2),encoding='utf-8')
    with (p/'R7_SHADOW_UPDATE_DIAGNOSTIC.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(['metric','frozen_R7','D0_shadow','change','classification'])
        for key in ['native_variance','MAP_error_m','posterior_mean_error_m','truth_1m_probability_mass','max_cell_probability','nonzero_free_cells']:
            writer.writerow([key,b[key],a[key],a[key]-b[key],complete['classification']])
manifest=p/'SHA256_MANIFEST.json'
if manifest.exists():
    for n,h in js('SHA256_MANIFEST.json').items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
print(json.dumps(summary))
