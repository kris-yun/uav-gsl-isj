from pathlib import Path
import csv,json,numpy as np
B=Path(__file__).resolve().parent;T=B/'function_trial';R=T/'results';scene=json.loads((T/'scene.json').read_text())
free=np.array(scene['occupancy'])==0;m=1-1/(1+np.exp(np.array(scene['logodds'])));confidence=np.array(scene['confidence']);D=scene['params']['sourceDiscriminationPower']
def score(p):return float(np.prod(1+((1-D*np.abs(m[free]-p[free]))-1)*confidence[free]))
summary={};windows=[]
for arm in 'ABCD':
 outputs=[json.loads((R/f'{arm}_{k}.json').read_text()) for k in range(4)]
 maps=np.stack([np.fromfile(R/f'{arm}_{k}.f32',dtype='<f4').astype(float) for k in range(4)])
 summary[arm]={'scores':[o['score'] for o in outputs],'mean_of_scores':float(np.mean([o['score'] for o in outputs])),'score_of_mean_map':score(maps.mean(0)),'critical_stops_9_to_13_frequency_matrix':[[q['prediction'] for q in o['stops'][8:]] for o in outputs],'stop8':[o['stops'][7]['prediction'] for o in outputs],'support_cells_per_replicate':[int((p>0).sum()) for p in maps],'total_filament_moves':sum(o['filament_moves'] for o in outputs)}
 for k,o in enumerate(outputs):
  for q in o['stops']:windows.append({'arm':arm,'replicate':k,'seed':o['spec']['seed'],'stop':q['stop'],'col':q['cell'][0],'row':q['cell'][1],'actual_hits':q['hits'],'actual_windows':q['n'],'native_center_frequency':q['prediction']})
summary['C_vs_D']={'D_over_C_each_replicate':[summary['D']['scores'][k]/summary['C']['scores'][k] for k in range(4)],'C_wins':sum(summary['C']['scores'][k]>summary['D']['scores'][k] for k in range(4)),'note':'Native compatibility score ratio only, not Bayes factor or new localization accuracy.'}
summary['verdict']={'original_replays':'EXACT_MAP_SCORE_AND_RNG_ENDPOINTS_FOR_BOTH_CALLS','coarse_source_only_rescue':'NOT_OBSERVED','critical_25_real_hit_windows':'All five stops9..13 are5/5hit, all A/B/C outputs at those stops zero for all4diagnostic initial states.','NGDB_necessity':'NOT_ESTABLISHED; no proof the persistent zeros are rare-event Monte Carlo error.','physical_zero_probability':'NOT_CLAIMED','new_ROS_goals':0,'new_gas_worlds':0,'new_full_posterior_maps':0,'RNG_scope':'Predetermined diagnostic states sharing original2500-value normal cache; not independent world repeats or native cold-start controlled-seed experiments.'}
(B/'FUNCTION_TRIAL_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (B/'FUNCTION_TRIAL_EACH_STOP.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=windows[0]);w.writeheader();w.writerows(windows)
# Exact two-source/two-puff enumeration: region source mixture and whole-scene source marginal differ.
codes=[0.,1.];same_scene=sum(1-(1-p)**2 for p in codes)/2
per_puff=sum((1-(1-p)*(1-q))/4 for p in codes for q in codes)
assert same_scene==.5 and per_puff==.75
(B/'JOINT_SOURCE_EVENT_ENUMERATION.json').write_text(json.dumps({'fixed_source_per_scene_probability':same_scene,'source_resampled_per_puff_probability':per_puff,'meaning':'Two hypothetical sources have individual-puff hit probabilities0and1. This exact toy only demonstrates non-equivalence of the multi-puff event; it is not a new algorithm or a GADEN result.','implication':'One-puff weights or region-mixture averages cannot automatically replace the native multi-puff-at-least-one event.'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'ANALYSIS_COMPLETE','arms':4,'new_calls':16,'C_wins':summary['C_vs_D']['C_wins'],'D_over_C_range':[min(summary['C_vs_D']['D_over_C_each_replicate']),max(summary['C_vs_D']['D_over_C_each_replicate'])]}))
