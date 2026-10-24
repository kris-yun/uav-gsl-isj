"""Diagnostic only: posterior of nearest legal cell, never an algorithm input."""
from pathlib import Path
import csv,json,math
R=Path(__file__).resolve().parent
records=json.loads((R/'BATCH_LEDGER.json').read_text());out=[]
for run in records:
 if run['QA']['case']!='B2'or not run['QA']['qualification'].startswith('PASS'):continue
 C=Path(run['archive']['source_case']);truth=json.loads((C/'CASE_META.json').read_text())['source_xyz'][:2]
 rows=list(csv.DictReader((C/'runtime/native_posterior_updates.csv').open()))
 first=[x for x in rows if x['update']==rows[0]['update']]
 nearest=min(first,key=lambda x:math.dist([float(x['x_m']),float(x['y_m'])],truth))
 for update in sorted({int(x['update'])for x in rows}):
  z=[x for x in rows if int(x['update'])==update]
  near=next(x for x in z if x['col']==nearest['col']and x['row']==nearest['row'])
  p=float(near['source_probability']);best=max(z,key=lambda x:float(x['source_probability']))
  out.append(dict(role=run['role'],update=update,legal_cells=len(z),near_col=near['col'],near_row=near['row'],nearest_legal_distance_m=math.dist([float(near['x_m']),float(near['y_m'])],truth),nearest_legal_probability=p,nearest_legal_rank=1+sum(float(x['source_probability'])>p for x in z),nearest_legal_tie_count=sum(float(x['source_probability'])==p for x in z),best_col=best['col'],best_row=best['row'],best_probability=float(best['source_probability']),best_to_nearest_legal_ratio=float(best['source_probability'])/p if p else 'INF',best_center_error_m=math.dist([float(best['x_m']),float(best['y_m'])],truth)))
with(R/'B2_LEGAL_PROXY_POSTERIOR_AUDIT.csv').open('w',newline='',encoding='utf-8-sig')as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
last=[next(z for z in reversed(out)if z['role']==x['role'])for x in records if x['QA']['case']=='B2'and x['QA']['qualification'].startswith('PASS')]
receipt=dict(status='READ_ONLY_POSTERIOR_DIAGNOSTIC_NOT_TRUE_SOURCE_RANK',
 definition='Choose the geometrically nearest existing legal source-cell center, using truth only for retrospective diagnosis. Its probability is a native cell value, potentially shared across a multiresolution simulation region. It is not the excluded true-source hypothesis or a new candidate prediction.',
 native_inputs_changed=False,new_predictions=0,rows=len(out),terminal=last)
(R/'B2_LEGAL_PROXY_POSTERIOR_AUDIT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
