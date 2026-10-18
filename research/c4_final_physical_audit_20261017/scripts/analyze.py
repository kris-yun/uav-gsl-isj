"""Final, bounded attribution. Truth-world event evidence is not a candidate bank."""
from pathlib import Path
import csv,json,gzip,math,hashlib,os
import numpy as np
R=Path(__file__).resolve().parents[1];O=Path(os.environ.get('C4_CLOSE_ANALYSIS_OUT',str(R/'analysis')));O.mkdir(exist_ok=True)
def rows(p):return list(csv.DictReader(p.open(newline='')))
def write(n,a):
    with (O/n).open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
def dump(n,a):(O/n).write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
rx=rows(R/'inputs/C4_update_1/receivers.csv');inp=rows(R/'inputs/C4_update_1/input.csv');m=rows(R/'inputs/C4_update_1/metadata.csv')[0]
cutoff=int(m['stamp_ns']) # frozen historical update_1; no later observations included
free=np.array([r['occupancy']=='1' for r in inp]);conf=np.array([float(r['confidence']) for r in inp]);prob=1-1/(1+np.exp(np.array([float(r['logOdds']) for r in inp])))
D=float(rows(R/'inputs/C4_update_1/settings.csv')[0]['sourceDiscriminationPower'])
def score(mp):return float(np.log(1-D*conf[free]*np.abs(prob[free]-mp[free])).sum())
jobs={(int(x['seed']),x['job_id']):x for x in rows(R/'inputs/jobs.csv')}
sources=[];responses=[];blocks=[];pairs=[];cum=[];cost=[];blockpairs=[];maxerr=0
for state in [2026101701,2026101702,2026101703]:
    root=R/'results/six'/str(state);ss=rows(root/'scores.csv');scores={};twenty={}
    for s in ss:
        ident=s['job_id'];p=root/ident;mp=np.fromfile(p/'blur.f32','<f4');raw=np.fromfile(p/'raw.f32','<f4')
        error=abs(score(mp)-float(s['source_logscore']));maxerr=max(maxerr,error);assert error<1e-12
        tr=np.frombuffer(gzip.decompress((p/'trace.u32.gz').read_bytes()),'<u4').reshape(-1,9+3*len(rx))
        assert len(tr)==3600 and (tr[:,0]==1).all()
        assert np.all(tr[:,5].astype('i8')-tr[:,6].astype('i8')==tr[:,3])
        assert int(tr[:,2].astype('u8').sum())==int(s['particle_moves'])
        assert (int(s['gaussian_before'])+2*int(s['particle_moves']))%2500==int(s['gaussian_after'])
        scores[ident]=float(s['source_logscore']);sources.append(dict(**s,late_60s_survivor_delta=int(tr[-1,3])-int(tr[-601,3])))
        cost.append(dict(type='2D_forward',state=state,source=ident,cpu_s=float(s['cpu_s']),particle_moves=int(s['particle_moves']),calls=1))
        for i,x in enumerate(rx):
            k=int(x['cell_index']);assert np.float32(np.mean(tr[:,9+3*i]>0))==raw[k]
            responses.append(dict(state=state,source=ident,stop=x['stop'],raw_frequency=float(raw[k]),blurred_frequency=float(mp[k]),observed_consumed_hit_fraction=x['hit_fraction']))
            for b in range(18):
                a=tr[b*200:(b+1)*200]
                blocks.append(dict(state=state,source=ident,stop=x['stop'],begin_s=20*b,end_s=20*(b+1),occupied_fraction=float(np.mean(a[:,9+3*i]>0)),new_lifetime_visitors=int(a[:,10+3*i].sum()),survivors=int(a[-1,3])))
        for t in range(200,3601,200):
            b=np.fromfile(p/f'cumulative_{t}_blur.f32','<f4')
            cum.append(dict(state=state,source=ident,end_s=t*.1,source_logscore=score(b)))
            last=(np.fromfile(p/f'block_{t-100}_blur.f32','<f4').astype('f8')+np.fromfile(p/f'block_{t}_blur.f32','<f4'))*.5
            twenty[(ident,t)]=score(last)
    for t in range(200,3601,200):
        blockpairs.append(dict(state=state,begin_s=(t-200)*.1,end_s=t*.1,
          truth_logscore=twenty[('fine_truth_1272',t)],competitor_logscore=twenty[('fine_competitor',t)],
          gap=twenty[('fine_truth_1272',t)]-twenty[('fine_competitor',t)],
          note='Frozen non-overlapping 20s blocks; averages of two saved 10s blurred maps, possible float32 rounding difference from direct 20s blur'))
    pairs.append(dict(state=state,source_true_logscore=scores['fine_truth_1272'],prelocked_competitor_logscore=scores['fine_competitor'],gap=scores['fine_truth_1272']-scores['fine_competitor'],truth_outranks_competitor=scores['fine_truth_1272']>scores['fine_competitor']))
write('SIX_SOURCE_SCORES.csv',sources);write('SIX_PAIR_GAPS.csv',pairs);write('SIX_RECEIVER_RESPONSES.csv',responses);write('SIX_20S_RECEIVER_BLOCKS.csv',blocks);write('SIX_CUMULATIVE_SCORES.csv',cum);write('SIX_20S_PAIR_GAPS.csv',blockpairs)
Q={int(x['serial']):x for x in rows(R/'inputs/physical_queries.csv')};E=rows(R/'results/PHYSICAL_EVENTS.csv')
assert len(E)==len(Q)==878
maximum=max(float(x['absolute_ppm_error']) for x in E);assert maximum==0,'Historical operator parity failed'
joined=[]
for x in E:
    q=Q[int(x['serial'])];ppm=float(x['recomputed_ppm']);assert float(q['recorded_service_ppm'])==ppm
    near=min(rx,key=lambda a:math.hypot(float(q['x'])-float(a['receiver_x']),float(q['y'])-float(a['receiver_y'])))
    dist=math.hypot(float(q['x'])-float(near['receiver_x']),float(q['y'])-float(near['receiver_y']))
    stop=int(near['stop']) if dist<1e-4 else ''
    within=bool(q['consumer_stamp_ns'] and int(q['consumer_stamp_ns'])<=cutoff)
    joined.append(dict({**q,**x},position_stop=stop,within_update1_consumer_history=within,
      diagnostic_instantaneous_ppm_threshold_hit=ppm>.1,projected_native_centre_hit=int(x['native_projected_centres'])>0,
      same_xy_sensor_slab_centre_hit=int(x['native_xy_sensor_slab_centres'])>0,physical_voxel_centre_hit=int(x['physical_voxel_centres'])>0,
      outside_native_xy_contribution_fraction=float(x['ppm_from_outside_native_xy'])/ppm if ppm>0 else '',
      outside_sensor_slab_contribution_fraction=float(x['ppm_from_outside_sensor_slab'])/ppm if ppm>0 else ''))
write('SAME_FRAME_EVENTS_ALL_QUALIFIED.csv',joined)
summ=[]
for stop in range(7):
    a=[x for x in joined if x['position_stop']==stop and x['within_update1_consumer_history']]
    if not a:continue
    summ.append(dict(stop=stop,n_matched_raw_PID_queries=len(a),distinct_physical_frames=len({x['frame'] for x in a}),
      ppm_min=min(float(x['recomputed_ppm']) for x in a),ppm_max=max(float(x['recomputed_ppm']) for x in a),
      instantaneous_ppm_above_threshold=sum(x['diagnostic_instantaneous_ppm_threshold_hit'] for x in a),
      projected_centre_hits=sum(x['projected_native_centre_hit'] for x in a),
      slab_centre_hits=sum(x['same_xy_sensor_slab_centre_hit'] for x in a),physical_voxel_centre_hits=sum(x['physical_voxel_centre_hit'] for x in a),
      ppm_hit_without_projected_centre=sum(x['diagnostic_instantaneous_ppm_threshold_hit'] and not x['projected_native_centre_hit'] for x in a),
      projected_centre_without_ppm_hit=sum(x['projected_native_centre_hit'] and not x['diagnostic_instantaneous_ppm_threshold_hit'] for x in a),
      ppm_hit_without_slab_centre=sum(x['diagnostic_instantaneous_ppm_threshold_hit'] and not x['same_xy_sensor_slab_centre_hit'] for x in a),
      mean_fraction_ppm_from_outside_xy=float(np.mean([float(x['outside_native_xy_contribution_fraction']) for x in a if x['outside_native_xy_contribution_fraction']!=''])) if any(x['outside_native_xy_contribution_fraction']!='' for x in a) else '',
      mean_fraction_ppm_from_outside_sensor_slab=float(np.mean([float(x['outside_sensor_slab_contribution_fraction']) for x in a if x['outside_sensor_slab_contribution_fraction']!=''])) if any(x['outside_sensor_slab_contribution_fraction']!='' for x in a) else '',
      note='Same exact gas queries linked by time/value to recorded PID; stationary-position grouping is not an exact consumption-window owner label'))
write('STOP_EVENT_SUMMARY.csv',summ)
write('COSTS.csv',cost+[dict(type='saved_frame_observation_operator',state='',source='existing C4 truth physical realization',cpu_s=sum(float(x['cpu_s']) for x in E),particle_moves=0,calls=len(E))])
binding=json.loads((R/'lineage/TIME_BINDING.json').read_text());fields=json.loads((R/'lineage/PHYSICAL_ASSET_AVAILABILITY.json').read_text())
prior=R/'lineage/prior_CONVERGENCE_FLAGS.csv';f=rows(prior);rejected=sum(x['meets_frozen_raw_and_blur_and_score_plateau_screen']=='False' for x in f)
dump('AUDIT_CHECKS.json',dict(six_forward_calls=6,six_score_max_error=maxerr,six_trace_checks_pass=True,
  saved_frame_operator_queries=len(E),historical_concentration_max_abs_error=maximum,
  raw_PID_unique_query_bindings=sum(x['consumer_matches']=='1' for x in joined),
  service_frame_ambiguous_requests_excluded=binding['ambiguous'],
  prior_descriptive_platform_screen_rejections=rejected,prior_screen_rows=len(f),formal_statistical_convergence_proven=False,
  physical_realizations=1,no_3D_propagation_counterfactual_run=True,new_ROS_calls=0,new_worlds=0,
  new_full_candidate_posterior=False,source_ranking_rescue_established=False))
decision=dict(verdict='C4_MAIN_INNOVATION_PURSUIT_CLOSED',attribution='C4_CURRENTLY_NOT_UNIQUELY_ATTRIBUTABLE',
  new_module_necessity='NOT_ESTABLISHED',new_task_gain=False,
  numerical_last_control='Six phase-consistent source-pair simulations complete; all final true-minus-competitor score gaps remain negative. No extension authorized.',
  operator_fact='Same-frame centre contact and ppm-threshold events are demonstrably different observables; native R6 concentration reproduces 878 historical gas responses exactly.',
  not_established=['Event operator mismatch explains the entire C4 discrimination loss','A correct ordinary sensor operator restores source ordering','3D transport is the isolated cause','A new cross-domain operation is necessary'],
  ordinary_methods_sufficient_for=['Exact reconstruction of historical simulator concentration from existing filament xyz, sigma and shared gas constants', 'Recovering some nonzero 2D remote response by longer warmup in the prior audit, without restoring source discrimination'],
  unidentifiable=['No same-realization same-budget alternative-source 3D prediction with consistent PID operator, hence no fair counterfactual competitor logscore for this change',
    '2D candidates lack gas amount, sigma and z needed for a physically defined PID operator; no occupancy-to-ppm calibration fitted',
    'No shared request ID links every gas service callback to its exact PID/consumption-window owner; five overlapping request intervals are excluded',
    'Snapshot vector lacks persistent filament ID and exact age; frames are correlated, one physical realization'],
  closure='Preserve C4 as an operator/forward-response development counterexample. End all C4 time/seed/score search and main-innovation pursuit; do not chain another C4 experiment.',
  next_action='Only specify minimum discriminating evidence for future independent House/lakeshore conditions. No dataset generation, new module or ROS launch in this task.')
decision_path=O/'FINAL_DECISION.json' if os.environ.get('C4_CLOSE_ANALYSIS_OUT') else R/'FINAL_DECISION.json'
decision_path.write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(pairs=pairs,physical_stop_summary=summ,checks=json.loads((O/'AUDIT_CHECKS.json').read_text())),ensure_ascii=False,indent=2))
