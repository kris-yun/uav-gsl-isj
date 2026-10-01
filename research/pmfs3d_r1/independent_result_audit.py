"""Post-result verification only; does not generate or change any forward score."""
import csv, hashlib, json, math, statistics
from pathlib import Path
import numpy as np
base=Path('evidence/pmfs3d_r1_oracle_ranking_20261001')
science=base/'PMFS3D_R1_SCIENTIFIC_20261001'
load=lambda p:json.loads(p.read_text())
rows=lambda p:list(csv.DictReader(p.open(newline='')))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=load(science/'evaluation1/R1_RESULT.json')
assert (science/'evaluation1/R1_RESULT.json').read_bytes()==(science/'evaluation2/R1_RESULT.json').read_bytes()
repeat=load(science/'DETERMINISTIC_REPEAT.json')
for section,folder1,folder2 in [('forward_hashes','repeat1','repeat2'),('evaluation_hashes','evaluation1','evaluation2')]:
 for name,digest in repeat[section].items():
  assert sha(science/folder1/name)==sha(science/folder2/name)==digest
checks=[];summary=[]
for c in r['cases']:
 name=c['case'];snapshot=base/'frozen_inputs'/name/'context_bank/source_update_0005'
 measured=rows(snapshot/'measured_hit_probability.csv')
 free=np.array([int(v['cell_index']) for v in measured if v['occupancy']=='Free'])
 probabilities=np.array([float(v['probability']) for v in measured])[free]
 confidence=np.array([float(v['confidence']) for v in measured])[free]
 archived={int(v['cell_index']):float(v['source_probability']) for v in rows(snapshot/'source_posterior.csv')}
 record={'case':name,'arms':{}}
 for arm in ('native','oracle2d','oracle3d'):
  folder=science/'repeat1'/name/arm
  scores={v['candidate_id']:float(v['log_score']) for v in rows(folder/'candidate_log_scores.csv')}
  err=[]
  for cid,score in scores.items():
   hit=np.fromfile(folder/'maps'/f'{cid}.f32',dtype='<f4')[free].astype(float)
   factors=1-confidence*np.abs(probabilities-hit)
   assert (factors>=0).all()
   with np.errstate(divide='ignore'): recalculated=float(np.log(factors).sum())
   if math.isinf(score): assert recalculated==score
   else:err.append(abs(recalculated-score))
  assert max(err)<1e-9
  truth_score=scores[c['truth_owner_leaf']]
  others=[v for k,v in scores.items() if k!=c['truth_owner_leaf']]
  rank=1+sum(v>truth_score for v in others)+.5*sum(v==truth_score for v in others)
  assert rank==c['arms'][arm]['truth_leaf_midrank']
  assert abs(truth_score-max(others)-c['arms'][arm]['source_margin'])<1e-10
  q={int(v['cell_index']):float(v['source_probability']) for v in rows(science/'evaluation1'/name/arm/'sourceProbability.csv')}
  assert set(q)==set(free)
  assert abs(sum(q.values())-1)<1e-12
  entropy=-sum(v*math.log(v) for v in q.values() if v>0)
  assert abs(entropy-c['arms'][arm]['source_map_entropy_nats'])<1e-12
  template=np.fromfile(folder/'maps'/f"{c['truth_owner_leaf']}.f32",dtype='<f4')
  record['arms'][arm]={'max_logscore_recomputation_error':max(err),'posterior_sum':sum(q.values()),'truth_template_nonzero_cells':int(np.count_nonzero(template)),'truth_template_sum':float(template.sum()),'truth_template_nonzero_at_confident_cells':int(np.count_nonzero(template[free][confidence>0])),'truth_log_score':truth_score,'rank_verified':True,'entropy_verified':True}
  if arm=='native':
   diff=max(abs(q[i]-archived[i]) for i in q)
   assert diff<1e-10
   record['native_historical_posterior_max_abs_error']=diff
 # Archived alignment probabilities must still match the actual scientific Native replay.
 maps={cid:np.fromfile(science/'repeat1'/name/'native/maps'/f'{cid}.f32',dtype='<f4') for cid in scores}
 diffs=[abs(float(maps[v['candidate_id']][int(v['cell_index'])])-float(v['simulated_hit_probability'])) for v in rows(snapshot/'candidate_support_alignment.csv') if v['candidate_id'] in maps]
 assert max(diffs)==0
 record['native_alignment_entries']=len(diffs);record['native_alignment_max_abs_error']=max(diffs)
 checks.append(record)
 summary.append({'case':name,'active_leaves':c['active_leaves'],'native_rank':c['arms']['native']['truth_leaf_midrank'],'oracle2d_rank':c['arms']['oracle2d']['truth_leaf_midrank'],'oracle3d_rank':c['arms']['oracle3d']['truth_leaf_midrank'],'delta_margin':c['delta_margin_3d_vs_oracle2d'],'entropy2d':c['arms']['oracle2d']['source_map_entropy_nats'],'entropy3d':c['arms']['oracle3d']['source_map_entropy_nats'],'delta_entropy':c['delta_entropy_2d_minus_3d'],'rank_worsened':int(c['arms']['oracle3d']['truth_leaf_midrank']>c['arms']['oracle2d']['truth_leaf_midrank'])})
assert r['positive_margin_cases']==sum(v['delta_margin']>0 for v in summary)
assert r['rank_worsening_cases']==sum(v['rank_worsened'] for v in summary)
margin=statistics.median(v['delta_margin'] for v in summary)>0 and r['positive_margin_cases']>=3
rank=statistics.median(v['oracle3d_rank'] for v in summary)<=statistics.median(v['oracle2d_rank'] for v in summary) and r['rank_worsening_cases']<=1
assert r['margin_gate_pass']==margin and r['rank_gate_pass']==rank
assert r['verdict']==('PASS' if margin and rank else 'HOLD' if margin else 'NO_GO')
(base/'INDEPENDENT_RESULT_AUDIT.json').write_text(json.dumps({'status':'PASS','gate_verified':True,'actual_repeat_hashes_verified':True,'cases':checks},indent=2,sort_keys=True)+'\n')
with (base/'CASE_METRICS.tsv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=summary[0],delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(summary)
print(json.dumps({'verification':'PASS','verdict':r['verdict'],'truth_template_nonzero_cells':[[a['truth_template_nonzero_cells'] for a in c['arms'].values()] for c in checks]}))
