from pathlib import Path
import json,csv,collections
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';O=R/'results';idx=json.loads((P/'CASE_INDEX.json').read_text());entries=idx['cases'];controls=json.loads((O/'STRONG_CONTROLS.json').read_text());stops=list(csv.DictReader((O/'OBSERVABLE_STOPS.csv').open()));influence=list(csv.DictReader((O/'STOP_INFLUENCE.csv').open()));rows=[];trace=[]
def write(name,data):
 keys=list(dict.fromkeys(k for r in data for k in r))
 with (O/name).open('w',newline='') as f:w=csv.DictWriter(f,keys);w.writeheader();w.writerows(data)
for e in entries:
 c=e['case'];root=P/e['native_path'];a=json.loads((O/'native20_recomputed'/(c+'.json')).read_text());last=a['updates'][-1];n=[x for x in controls if x['case']==c and x['arm']=='O0' and x['confidence']=='native' and x['forward']=='native_blur'][-1];final=[x for x in controls if x['case']==c and x['update']==n['update'] and x['confidence']=='native' and x['forward']=='native_blur'];ev=np.loadtxt(root/'runtime/measurement_events.csv',delimiter=',',ndmin=2);ss=[s for s in stops if s['case']==c];mixed=[s for s in ss if s['mixed']=='True'];inc=[s for s in mixed if int(s['last_stamp_ns'])<=last['metadata']['stamp_ns']];invalid=[s for s in ss if s['sensor_support']!='ALL_MATCHED_QUERY_POSITIONS_GAS_FREE'];row=dict(case=c,world_identity=e['identity'],version='2026_4e141e1_plus_logged_runtime_adaptations',original_outcome=a['status'],original_native_top5_error_m=(a['native_returned_point_metrics'] or {}).get('best5pct_error_m'),source_supported=n['source_supported'],actual_sensor_position_ambiguous=bool(invalid),sensor_ambiguous_stops=','.join(s['stop'] for s in invalid),mixed_stops=len(mixed),mixed_stops_consumed_by_last_source_update=len(inc),mixed_stops_only_after_last_source_update=len(mixed)-len(inc),last_complete_update=n['update'],last_update_windows=n['windows'],total_consumed_windows=len(ev),forward_event_alignment='MISSING_3D_MASS_SIGMA_SUBWINDOW_SENSOR_MODEL',closed_loop_counterfactual='NOT_RUN',qualification='SOURCE_DOMAIN_EXCLUDED' if not n['source_supported'] else 'HOLD_SENSOR_POSITION_BINDING' if invalid else 'QUALIFIED_FIXED_HISTORY_SOURCE_SCORE',verdict='NO_GO_FOR_MAIN_INNOVATION' if not inc else 'HOLD_OBSERVATION_SEMANTICS_ONLY')
 for b in final:
  for k in ['truth_rank','truth_mass','source_score_gap','official_top5_error_m','posterior_mean_error_m','variance_m2','working_nll','working_brier']:row[b['arm']+'_'+k]=b[k]
 rows.append(row)
 # Reconstruct the path from each consumed mean-ppm event to the two full-grid
 # source scores, conditional on a later captured epoch's fixed forward maps.
 base=[b for b in controls if b['case']==c and b['arm']=='O0' and b['confidence']=='native' and b['forward']=='native_blur']
 for b in base:
  u=b['update'];z=np.load(O/'controls'/(c+'_'+u+'.npz'));free=z['free_indices'];owner=z['owner'];h=z['forward_blurred'];nf=len(free);rr=np.fromfile(O/'replay20'/(c+'.f64'),dtype='<f8').reshape(len(ev),nf,4);m=json.loads((root/'runtime/updates'/u/'metadata.json').read_text());truth=e['metadata']['source_xyz'];tx=int((np.float32(truth[0])-np.float32(m['origin_x']))/np.float32(m['cell_size']));ty=int((np.float32(truth[1])-np.float32(m['origin_y']))/np.float32(m['cell_size']));ti=np.flatnonzero(free==tx+ty*m['width']);comp=b['competitor_locked_cell'];ci=np.flatnonzero(free==comp) if comp is not None else [];loc={int(v):i for i,v in enumerate(free)};D=a['source_discrimination_power'];fixedconf=rr[b['windows']-1,:,1]
  for k in range(b['windows']):
   event=ev[k];rx=int((np.float32(event[4])-np.float32(m['origin_x']))/np.float32(m['cell_size']));ry=int((np.float32(event[5])-np.float32(m['origin_y']))/np.float32(m['cell_size']));ri=loc.get(rx+ry*m['width']);p=np.exp(-np.logaddexp(0,-rr[k,:,0]));gap=None
   if len(ti) and len(ci):gap=float((np.log(1-D*fixedconf*np.abs(p-h[owner[ti[0]]]))-np.log(1-D*fixedconf*np.abs(p-h[owner[ci[0]]]))).sum())
   t=dict(case=c,epoch=u,prefix_window=k+1,stamp_ns=int(event[0]),stop=int(event[6]),unthresholded_consumed_mean_ppm=float(event[1]),hit=bool(event[1]>.1),x=float(event[4]),y=float(event[5]),wind_speed=float(event[2]),wind_direction=float(event[3]),source_supported=bool(len(ti)),competitor_locked_cell=comp,full_grid_truth_minus_competitor_gap_fixed_epoch_confidence=gap,scope='RETROSPECTIVE_PREFIX_DECOMPOSITION_ON_CAPTURED_EPOCH_FORWARD_NOT_AN_ONLINE_PREDICTION')
   if ri is not None:t.update(receiver_log_odds=float(rr[k,ri,0]),receiver_contact_probability=float(p[ri]),receiver_native_confidence=float(rr[k,ri,1]),receiver_spatial_kernel_weight=float(rr[k,ri,2]))
   if len(ti):t.update(truth_cell_contact_probability=float(p[ti[0]]),truth_cell_native_confidence=float(rr[k,ti[0],1]),truth_leaf_forward_at_receiver=float(h[owner[ti[0]],ri]) if ri is not None else None)
   if len(ci):t['competitor_leaf_forward_at_receiver']=float(h[owner[ci[0]],ri]) if ri is not None else None
   trace.append(t)
write('EVIDENCE_MATRIX.csv',rows);write('03_OPERATOR_TO_SOURCE_SCORE_TRACE.csv',trace)
summary=dict(cases=len(rows),source_supported_cases=sum(r['source_supported'] for r in rows),qualified_fixed_history_cases=sum(r['qualification']=='QUALIFIED_FIXED_HISTORY_SOURCE_SCORE' for r in rows),all_mixed_cases=[r['case'] for r in rows if r['mixed_stops']],source_supported_mixed_cases=[r['case'] for r in rows if r['mixed_stops'] and r['source_supported']],qualified_mixed_cases_with_consumed_source_evidence=[r['case'] for r in rows if r['mixed_stops_consumed_by_last_source_update'] and r['qualification']=='QUALIFIED_FIXED_HISTORY_SOURCE_SCORE'],mixed_stop_influence_rows=len([r for r in influence if r['mixed']=='True']),mixed_stop_influence_distinct_stops=len({(r['case'],r['stop']) for r in influence if r['mixed']=='True'}),stop_influence_rows=len(influence),counterfactual_readouts=len(controls),main_innovation_established=False,verdict='NO_GO_FOR_MAIN_INNOVATION',secondary_verdict='HOLD_OBSERVATION_SEMANTICS_ONLY',native2024_exact_source_causal_verdict='HOLD_MISSING_MATCHED_FORWARD',no_new_worlds=0,no_new_ROS_episodes=0,new_module_search_started=False)
(O/'FINAL_DECISION.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
# A compact diagnostic figure, not a manuscript claim or a statistical test.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,3.8),layout='constrained');names=[r['case'] for r in rows];zero=[];mixed=[];one=[]
for c in names:
 a=[s for s in stops if s['case']==c];mixed.append(sum(s['mixed']=='True' for s in a));zero.append(sum(s['hits']=='0' for s in a));one.append(sum(int(s['hits'])==int(s['windows']) for s in a))
x=np.arange(20);axes[0].bar(x,zero,label='all no-hit',color='#9aa0a6');axes[0].bar(x,mixed,bottom=zero,label='mixed',color='#c56c39');axes[0].bar(x,one,bottom=np.array(zero)+mixed,label='all hit',color='#527ca3');axes[0].set_xticks(x,names,rotation=90);axes[0].set_ylabel('Actual sampled stops');axes[0].legend(fontsize=8);axes[0].set_title('All corrected20 records; not independent repeats')
colors=['#1f77b4','#ff7f0e','#2ca02c','#d62728']
for i,c in enumerate(['A1','A3','A4']):
 r=next(r for r in rows if r['case']==c)
 for j,arm in enumerate(['O0','O1','O2','O3']):axes[1].bar(i+(j-1.5)*.18,r[arm+'_source_score_gap'],width=.18,color=colors[j],label=arm if i==0 else None)
axes[1].axhline(0,color='black',lw=.6);axes[1].set_xticks(range(3),['A1','A3','A4']);axes[1].set_title('Same history, native confidence / forward');axes[1].set_ylabel('True minus prior-locked competitor log score');axes[1].legend(fontsize=8)
fig.savefig(O/'diagnostic.svg');fig.savefig(O/'diagnostic.png',dpi=160)
