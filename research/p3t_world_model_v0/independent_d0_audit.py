"""Independent recomputation from saved hit maps; no scientific redefinition."""
import csv,json,hashlib,math,statistics
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[2];e=root/'evidence/p3t_d0_gaussian_support_20261001';r=json.loads((e/'evaluation1/P3T_D0_RESULT.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=lambda p:list(csv.DictReader(p.open(newline='')))
checks=[];hashes=[]
for p in sorted((e/'evaluation1').glob('*')):
 q=e/'evaluation2'/p.name;assert sha(p)==sha(q);hashes.append(dict(path=p.name,sha256=sha(p)))
rep=json.loads((e/'gaussian_outputs/DETERMINISTIC_REPEAT.json').read_text())
for record in rep['pairs']:
 assert sha(e/'gaussian_outputs/repeat1'/record['path'])==record['sha256']==sha(e/'gaussian_outputs/repeat2'/record['path'])
for case in r['cases']:
 name=case['case'];cells=rows(e/'inputs'/name/'measured_hit_probability.csv');free=[x for x in cells if x['occupancy']=='Free'];indices=np.array([int(x['cell_index']) for x in free]);prob=np.array([float(x['probability']) for x in free]);conf=np.array([float(x['confidence']) for x in free])
 for arm in ['P2','P3','G2','G3']:
  folder=e/'point_controls'/name/('oracle2d' if arm=='P2' else 'oracle3d') if arm.startswith('P') else e/'gaussian_outputs/repeat1'/name/arm.lower()
  scores={x['candidate_id']:float(x['log_score']) for x in rows(folder/'candidate_log_scores.csv')};errors=[]
  for cid,score in scores.items():
   hit=np.fromfile(folder/'maps'/f'{cid}.f32','<f4')[indices].astype(float);assert ((hit>=0)&(hit<=1)).all()
   factors=1-conf*np.abs(prob-hit);assert (factors>=0).all()
   with np.errstate(divide='ignore'):rec=float(np.log(factors).sum())
   if math.isinf(score):assert rec==score
   else:errors.append(abs(rec-score))
  assert max(errors)<1e-9
  truth=scores[case['truth_owner_leaf']];wrong=[v for cid,v in scores.items() if cid!=case['truth_owner_leaf']];m=case['arms'][arm]
  assert 1+sum(x>truth for x in wrong)+.5*sum(x==truth for x in wrong)==m['truth_midrank']
  assert truth-max(wrong)==m['source_margin']
  posterior=[float(x['source_probability']) for x in rows(e/'evaluation1'/f'{name}_{arm}_sourceProbability.csv')];assert abs(sum(posterior)-1)<1e-12
  assert abs(-sum(v*math.log(v) for v in posterior if v>0)-m['entropy_nats'])<1e-12
  checks.append(dict(case=name,arm=arm,max_score_error=max(errors),rank_margin_entropy_and_posterior_verified=True))
assert sum(c['arms']['G3']['truth_log_score']>c['arms']['P3']['truth_log_score'] for c in r['cases'])==0
assert r['decision']=='P3T_D0_NO_POSITIVE_TRUTH_SUPPORT_STOP'
result=dict(status='PASS',new_score_values_generated=False,all_saved_scores_independently_recomputed=True,gate_decision_verified=True,forward_repeat_files=len(rep['pairs']),evaluation_repeat_files=len(hashes),evaluation_hashes=hashes,cases=checks)
(e/'INDEPENDENT_D0_AUDIT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('INDEPENDENT_D0_AUDIT_PASS',len(checks),len(hashes))
