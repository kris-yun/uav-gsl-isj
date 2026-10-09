# Diagnostic only: re-score archived confident cells with D=1, optionally omit cell 28.
# Requires the frozen R1 ZIP PMFS_H02_FAILURE_ROOT_CAUSE_R1_SMALL.zip.
import csv, math, collections
from zipfile import ZipFile
from pathlib import Path
zip_path=Path('PMFS_H02_FAILURE_ROOT_CAUSE_R1_SMALL.zip')
with ZipFile(zip_path) as z:
 for suf in ('11','12'):
  root=f'evidence/raw/H02_R20260922{suf}/context_bank/source_update_0001/'
  rows=csv.DictReader(z.read(root+'candidate_support_alignment.csv').decode().splitlines())
  factors=collections.defaultdict(list)
  for row in rows:
   factors[row['candidate_id']].append((int(row['cell_index']),1-float(row['measured_confidence'])*abs(float(row['measured_probability'])-float(row['simulated_hit_probability']))))
  sc=list(csv.DictReader(z.read(f'H02_R20260922{suf}_D1_candidate_scores.csv').decode().splitlines()))
  active=[x['candidate_id'] for x in sc if x['active_leaf']=='True']
  truth=next(x['candidate_id'] for x in sc if x['truth_owner']=='True')
  for arm in ('full','drop28'):
   result={}
   for k in active:
    w=[v for i,v in factors[k] if arm=='full' or i!=28]
    result[k]=sum(map(math.log,w)) if all(x>0 for x in w) else -math.inf
   t=result[truth]; gt=sum(v>t for v in result.values());eq=sum(v==t for v in result.values())
   print(suf,arm,'rank',1+gt+(eq-1)/2,'hard_zero_candidates',sum(v==-math.inf for v in result.values()))
