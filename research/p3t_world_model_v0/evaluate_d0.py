"""Post-freeze four-arm D0 evaluation; no tuning or transport computation."""
import argparse,csv,json,math,re,statistics
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--repeat',default='repeat1');a=p.parse_args()
root=Path(__file__).resolve().parents[2];e=root/'evidence/p3t_d0_gaussian_support_20261001'
old=root/'evidence/pmfs3d_r1_oracle_ranking_20261001';r1=json.loads((old/'R1_RESULT.json').read_text())
science=e/'gaussian_outputs';repeat=json.loads((science/'DETERMINISTIC_REPEAT.json').read_text());assert repeat['pass_']
assert json.loads((science/'INDEPENDENT_QUERY_AUDIT.json').read_text())['pass_']
rows=lambda path:list(csv.DictReader(path.open(newline='')))
runtime=json.loads((science/'RUNTIME.json').read_text())
a.out.mkdir(parents=True,exist_ok=False);summary=[];candidate_summary=[];cases=[]
for original in r1['cases']:
 name=original['case'];truth=original['truth_owner_leaf'];inputs=e/'inputs'/name
 cells=rows(inputs/'measured_hit_probability.csv');leaves=rows(inputs/'active_candidates.csv')
 free=[r for r in cells if r['occupancy']=='Free'];free_indices=np.array([int(r['cell_index']) for r in free]);conf=np.array([float(r['confidence']) for r in free]);conf_indices=free_indices[conf>0]
 owns=lambda leaf,row:int(leaf['origin_i'])<=int(row['grid_i'])<int(leaf['origin_i'])+int(leaf['size_i']) and int(leaf['origin_j'])<=int(row['grid_j'])<int(leaf['origin_j'])+int(leaf['size_j'])
 owners={int(row['cell_index']):next(leaf['candidate_id'] for leaf in leaves if owns(leaf,row)) for row in free}
 record=dict(case=name,house=name[:7],truth_owner_leaf=truth,candidates=len(leaves),free_cells=len(free),confident_cells=len(conf_indices),arms={},deltas={})
 for arm,folder in [('P2',e/'point_controls'/name/'oracle2d'),('P3',e/'point_controls'/name/'oracle3d'),('G2',science/a.repeat/name/'g2'),('G3',science/a.repeat/name/'g3')]:
  scores={r['candidate_id']:float(r['log_score']) for r in rows(folder/'candidate_log_scores.csv')};assert set(scores)=={r['candidate_id'] for r in leaves}
  target=scores[truth];wrong=[v for cid,v in scores.items() if cid!=truth];assert math.isfinite(target)
  better=sum(v>target for v in wrong);tied=sum(v==target for v in wrong);peak=max(scores.values())
  weights={idx:math.exp(scores[cid]-peak) for idx,cid in owners.items()};den=sum(weights.values());posterior={idx:w/den for idx,w in weights.items()}
  hit=np.fromfile(folder/'maps'/f'{truth}.f32',dtype='<f4');assert len(hit)==len(cells)
  metric=dict(truth_log_score=target,truth_midrank=1+better+tied/2,truth_pessimistic_rank=1+better+tied,truth_ties=tied,source_margin=target-max(wrong),entropy_nats=-sum(q*math.log(q) for q in posterior.values() if q>0),truth_template_nonzero_hit_cells=int(np.count_nonzero(hit[free_indices])),truth_template_hit_probability_sum=float(hit[free_indices].astype(float).sum()),truth_hit_cells_with_positive_confidence=int(np.count_nonzero(hit[conf_indices])),unique_top1=bool(better==0 and tied==0),recall_at5=bool(1+better+tied<=5),top5_candidate_ids=sorted(scores,key=lambda cid:(-scores[cid],cid))[:5])
  if arm.startswith('G'):
   mean=np.fromfile(folder/'concentration'/f'{truth}_mean.f32','<f4');maximum=np.fromfile(folder/'concentration'/f'{truth}_max.f32','<f4');fraction=np.fromfile(folder/'concentration'/f'{truth}_nonzero_fraction.f32','<f4')
   metric['truth_continuous_support_at_confident_cells']=int(np.count_nonzero(maximum[conf_indices]));metric['truth_mean_concentration_ppm_sum_at_confident_cells']=float(mean[conf_indices].astype(float).sum());metric['truth_max_concentration_ppm_at_confident_cells']=float(maximum[conf_indices].max())
   diag={r['candidate_id']:r for r in rows(folder/'gaussian_diagnostics.csv')}[truth]
   metric['gaussian_filament_diagnostics']={k:int(v) for k,v in diag.items() if k!='candidate_id'}
   rt=next(r for r in runtime if r['repeat']=='repeat1' and r['case']==name and r['arm']==arm.lower())
   metric['runtime_wall_seconds']=rt['wall_seconds'];metric['peak_memory_kib']=int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',rt['time_output']).group(1))
   with (a.out/f'{name}_{arm}_truth_confident_concentration.tsv').open('w',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['cell_index','confidence','observed_hit_probability','predicted_hit_probability','mean_concentration_ppm','max_concentration_ppm','nonzero_fraction'])
    for row in free:
     idx=int(row['cell_index'])
     if float(row['confidence'])>0:w.writerow([idx,row['confidence'],row['probability'],float(hit[idx]),float(mean[idx]),float(maximum[idx]),float(fraction[idx])])
  else:
   assert metric['truth_midrank']==original['arms']['oracle2d' if arm=='P2' else 'oracle3d']['truth_leaf_midrank']
   metric['truth_continuous_support_at_confident_cells']=None
  with (a.out/f'{name}_{arm}_sourceProbability.csv').open('w',newline='') as f:
   w=csv.writer(f,lineterminator='\n');w.writerow(['cell_index','leaf_id','source_probability'])
   for idx,cid in owners.items():w.writerow([idx,cid,format(posterior[idx],'.17g')])
  record['arms'][arm]=metric
  summary.append(dict(case=name,arm=arm,**{k:v for k,v in metric.items() if isinstance(v,(int,float,bool))}))
  for cid,score in scores.items():candidate_summary.append(dict(case=name,arm=arm,candidate_id=cid,log_score=score,is_truth=int(cid==truth)))
 for new,baseline in [('G3','P3'),('G2','P2'),('G3','G2')]:
  record['deltas'][new+'-'+baseline]={k:record['arms'][new][k]-record['arms'][baseline][k] for k in ['truth_log_score','truth_midrank','truth_ties','source_margin','entropy_nats']}
 cases.append(record)
g3=[c['arms']['G3'] for c in cases];p3=[c['arms']['P3'] for c in cases];g2=[c['arms']['G2'] for c in cases]
counts={key:sum(test(x,y) for x,y in zip(g3,p3)) for key,test in [('truth_log_score_improved',lambda x,y:x['truth_log_score']>y['truth_log_score']),('rank_improved',lambda x,y:x['truth_midrank']<y['truth_midrank']),('rank_worsened',lambda x,y:x['truth_midrank']>y['truth_midrank']),('ties_decreased',lambda x,y:x['truth_ties']<y['truth_ties']),('margin_improved',lambda x,y:x['source_margin']>y['source_margin'])]}
counts['continuous_support_present']=sum(x['truth_continuous_support_at_confident_cells']>0 for x in g3)
median_gain=statistics.median(y['truth_midrank']-x['truth_midrank'] for x,y in zip(g3,p3))
gatea={**counts,'median_rank_improvement':median_gain,'pass':counts['truth_log_score_improved']>=3 and counts['continuous_support_present']>=3 and counts['rank_improved']>=3 and counts['ties_decreased']>=3 and counts['margin_improved']>=3 and counts['rank_worsened']<=1 and median_gain>=10}
dm=[x['source_margin']-y['source_margin'] for x,y in zip(g3,g2)];gateb=dict(positive_margin_cases=sum(v>0 for v in dm),median_delta_margin=statistics.median(dm),median_rank_g3=statistics.median(x['truth_midrank'] for x in g3),median_rank_g2=statistics.median(x['truth_midrank'] for x in g2),rank_worsened_cases=sum(x['truth_midrank']>y['truth_midrank'] for x,y in zip(g3,g2)),both_houses_positive=all(any(v>0 and c['house']==h for v,c in zip(dm,cases)) for h in ['House01','House02']))
gateb['pass']=gateb['positive_margin_cases']>=3 and gateb['median_delta_margin']>0 and gateb['median_rank_g3']<=gateb['median_rank_g2'] and gateb['rank_worsened_cases']<=1 and gateb['both_houses_positive']
decision='P3T_D0_NO_POSITIVE_TRUTH_SUPPORT_STOP' if counts['truth_log_score_improved']<3 else ('P3T_D0_HOLD_SUPPORT_NOT_DISCRIMINATIVE' if not gatea['pass'] else ('P3T_D0_3D_GAUSSIAN_SOURCE_EVIDENCE_PASS' if gateb['pass'] else 'P3T_D0_GAUSSIAN_ONLY_HOLD'))
result=dict(decision=decision,p0_decision='P3T_D0_P0_PROVENANCE_AND_TRAJECTORY_PASS',p0_commit='a623e998',prescoring_driver_commit='03a930a2',gate_a=gatea,gate_b=gateb,cases=cases,deterministic_repeat=True,new_gaden_runs=0,training_runs=0,closed_loop_runs=0,threshold_boundary_effect='none: binary32 C cannot equal binary64 0.1 exactly',scope='four development terminal leaf-bank cases; not calibrated likelihood, full-grid localization confirmation, or world-model validation')
(a.out/'P3T_D0_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
for name,data in [('P3T_D0_CASES.tsv',summary),('P3T_D0_CANDIDATES.tsv',candidate_summary)]:
 columns=list(dict.fromkeys(k for row in data for k in row))
 with (a.out/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=columns,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(data)
print(json.dumps(dict(decision=decision,gate_a=gatea,gate_b=gateb)))
