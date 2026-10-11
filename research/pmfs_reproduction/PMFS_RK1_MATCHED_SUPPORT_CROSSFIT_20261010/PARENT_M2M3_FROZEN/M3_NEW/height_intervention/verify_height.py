import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,csv,math
from analyse_height import analyse
r=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((r/'HEIGHT_EXECUTION_CONTRACT.json').read_text());assert sha(r/'HEIGHT_EXECUTION_CONTRACT.json')==(r/'HEIGHT_EXECUTION_CONTRACT_SHA256.txt').read_text().strip()
assert sha(r/'HEIGHT_FROZEN_CONTRACT.json')==c['contract_sha256']=='f47b4a2028f9b79fc81c947c5e4c78beadb6c55a83d80c930c8b3a7b065d4f63'
old=list(csv.DictReader((r.parent/'boundary_point_experiment/snapshot/input.csv').open(encoding='utf-8')))
for field in c['field_checks']:
 p=r/'inputs'/(field['field']+'_input.csv');assert sha(p)==field['sha256'];new=list(csv.DictReader(p.open(encoding='utf-8')));assert len(new)==len(old)==1530
 for a,b in zip(old,new):
  for k in a:
   if k not in ['u','v']:assert a[k]==b[k]
 snapshot=r/'snapshots'/field['field'];assert sha(snapshot/'input.csv')==sha(p)
 for n in ['metadata.csv','metadata.json','gaussian_cache.f32','simulation_parameters.csv']:assert sha(snapshot/n)==sha(r.parent/'boundary_point_experiment/snapshot'/n)
led=json.loads((r/'HEIGHT_EXECUTION_LEDGER.json').read_text());assert led==json.loads((r/'HEIGHT_EXECUTION_LEDGER_REMOTE_EXACT.json').read_text());assert led['status']=='PASS_EIGHT_INPUT_ONLY_HEIGHT_FORWARDS_NO_RERUN' and led['completed_calls']==8 and led['entered_calls']==8 and led['wall_seconds']<60 and led['peak_RSS_bytes']<536870912
assert all(led[k]==0 for k in ['new_GADEN','new_CFD','ROS_init','new_navigation','baseline_reruns'])
for j in c['jobs']:
 p=r/'forward_calls'/j['job'];z=json.loads((p/'RESULT.json').read_text());m=json.loads((p/'MOVEMENT_COUNTERS.json').read_text())
 assert z['forward_calls']==1 and z['native_updates']==z['ROS_nodes']==0 and z['source_form']=='point' and z['boundary']=='native'
 assert z['rng_before']==z['rng_after']==j['rng_before'] and z['gaussian_index_before']==j['gaussian_index_before']
 assert m['slide_attempts']==m['recursion_guard_hits']==m['invalid_start_cell']==0
res=analyse(r);assert res['summary']==json.loads((r/'HEIGHT_EXPERIMENT_RESULT.json').read_text())
for n,k in [('HEIGHT_FORWARD_SCORES.csv','rows'),('HEIGHT_PAIRED_COMPARISONS.csv','comparisons'),('HEIGHT_PER_CELL_CONTRIBUTIONS.csv','percell')]:
 with (r/n).open(encoding='utf-8') as f:oldrows=list(csv.DictReader(f))
 assert len(oldrows)==len(res[k])
 for a,b in zip(oldrows,res[k]):
  for key,v in b.items():
   if isinstance(v,(float,int)):assert math.isclose(float(a[key]),v,rel_tol=3e-13,abs_tol=1e-14)
   else:assert a[key]==str(v)
print(json.dumps(dict(status='PASS_HEIGHT_INPUT_ONLY_SCORES_RNG_PHASE_AND_CAPTURE',new_calls=8,baseline_reused=4,all_six_pairwise_choices='K2',sourceplane_true_warmup='500 steps as native max; other cases200, params unchanged'),indent=2))
