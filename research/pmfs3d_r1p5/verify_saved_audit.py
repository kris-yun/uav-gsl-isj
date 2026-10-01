"""Independent post-result verification using saved CSVs; no forward or method construction."""
import csv,hashlib,json,statistics
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
base=Path('evidence/pmfs3d_r1p5_suppression_audit_20261001')
result=json.loads((base/'R1P5_RESULT.json').read_text())
read=lambda p:list(csv.DictReader(p.open(newline='')))
original=json.loads((base/'inputs/R1_RESULT.json').read_text())
reports=[];bycase={};truths={}
for c in result['cases']:
 name=c['case'];old=next(x for x in original['cases'] if x['case']==name);truth=old['truth_owner_leaf'];truths[name]=truth
 tables=[]
 for arm in ('oracle2d','oracle3d'):
  rows=read(base/'inputs/repeat1'/name/arm/'candidate_log_scores.csv')
  table={r['candidate_id']:float(r['log_score']) for r in rows}
  assert len(table)==len(rows), 'duplicate candidate ID'
  assert all(np.isfinite(list(table.values())))
  tables.append(table)
 a,b=tables;assert a.keys()==b.keys()
 ids=sorted(set(a)-{truth});s2=np.array([a[j] for j in ids]);s3=np.array([b[j] for j in ids])
 gain=(b[truth]-s3)-(a[truth]-s2)
 # Arithmetic grouping can differ by roundoff; signs and medians must agree with the frozen formula.
 dtruth=b[truth]-a[truth];assert dtruth==0
 formula=dtruth-(s3-s2);assert np.max(np.abs(formula-gain))<1e-10
 ahead=s2>a[truth];after=s3>b[truth];tie2=s2==a[truth];tie3=s3==b[truth]
 assert int(ahead.sum())==c['ahead2d_count']
 assert abs(float(np.mean(formula[ahead]>0))-c['frac_A_pos_ahead2d'])<1e-15
 assert float(np.median(formula[ahead]))==c['median_A_ahead2d']
 assert int(np.sum(ahead & ~after))==c['repaired_crossings']
 assert int(np.sum(~ahead & after))==c['harmful_crossings']
 assert int(np.sum(~tie2 & tie3))==c['truth_ties_added']
 assert int(np.sum(tie2 & ~tie3))==c['truth_ties_removed']
 assert 1+int(ahead.sum())+int(tie2.sum())/2==c['rank2d']
 assert 1+int(after.sum())+int(tie3.sum())/2==c['rank3d']
 assert c['rank3d']-c['rank2d']==c['harmful_crossings']-c['repaired_crossings']+.5*(c['truth_ties_added']-c['truth_ties_removed'])
 bycase[name]={j:b[j]-a[j] for j in ids}
 reports.append({'case':name,'candidate_rows':len(ids),'ranks_crossings_advantage_verified':True})
houses={}
for house in ('House01','House02'):
 n0=house+'_seed0_off_off';n1=house+'_seed1_off_off'
 ids=sorted(set(bycase[n0])&set(bycase[n1])-{truths[n0],truths[n1]})
 rho=float(spearmanr([bycase[n0][j] for j in ids],[bycase[n1][j] for j in ids]).statistic)
 stored=result['house_stability'][house]
 assert len(ids)==stored['n_common'] and abs(rho-stored['spearman_delta'])<1e-12
 houses[house]={'n_common':len(ids),'scipy_spearman':rho,'custom_spearman_verified':True}
selective=sum(c['ahead2d_count']>0 and c['frac_A_pos_ahead2d']>=.6 and c['median_A_ahead2d']>0 for c in result['cases'])
stable=all(v['n_common']>=50 and v['scipy_spearman']>=.5 for v in houses.values())
partial=any(v['n_common']>=50 and v['scipy_spearman']>=.3 for v in houses.values())
expected='PMFS3D_R1P5_SELECTIVE_FALSE_SUPPRESSION' if selective>=3 and stable else 'PMFS3D_R1P5_HOLD_PARTIAL_SELECTIVITY' if selective>=2 or partial else 'PMFS3D_R1P5_FRAGILE_TOP_COMPETITOR_SUPPRESSION_STOP'
assert result['integrity_pass'] and result['decision']==expected
(base/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps({'status':'PASS','decision_verified':expected,'cases':reports,'houses':houses,'no_new_forward':True},indent=2,sort_keys=True)+'\n')
print(json.dumps({'verification':'PASS','decision':expected,'houses':houses}))
