import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,math,hashlib
from analyse import analyse
root=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((root/'EXECUTION_CONTRACT.json').read_text());assert sha(root/'EXECUTION_CONTRACT.json')==(root/'EXECUTION_CONTRACT_SHA256.txt').read_text().strip()
assert sha(root.parent/'M3_FROZEN_CONTRACT.json')==c['main_contract_sha256']
for n,d in c['source_sha256'].items():assert sha(root/n)==d,n
led=json.loads((root/'EXECUTION_LEDGER.json').read_text());assert led['status']=='PASS_2_ANCHORS_12_NEW_FORWARD_FACTORIAL_COMPLETE' and led['completed_calls']==14 and led['new_science_calls']==12
assert led['forward_wall_seconds']<120 and led['peak_RSS_bytes']<536870912 and led['new_remote_disk_bytes']<200000000
assert led['ros_init']==led['new_GADEN']==led['new_navigation']==0
for anchor in led['anchors']:
 for check in anchor['checks']:assert sha(root/'forward_calls'/anchor['job']/check['file'])==check['sha256']
jobmapping={j['job']:j for j in c['jobs']}
for n,j in jobmapping.items():
 p=root/'forward_calls'/n;r=json.loads((p/'RESULT.json').read_text());s=json.loads((p/'MOVEMENT_COUNTERS.json').read_text())
 assert r['forward_calls']==1 and r['native_updates']==r['ROS_nodes']==0
 assert s['recursion_guard_hits']==s['invalid_start_cell']==0
 assert r['rng_before']==j['rng_before'] and r['gaussian_index_before']==j['gaussian_index_before']
 if j['source_form']=='point':assert r['rng_after']==r['rng_before']
r=analyse(root);old=json.loads((root/'FACTORIAL_RESULT.json').read_text());assert r['summary']==old
for fn,key in [('FORWARD_SCORE_AND_SUPPORT.csv','rows'),('PAIRWISE_FACTORIAL_EFFECTS.csv','comparisons'),('PAIRWISE_PER_CELL_DIFFERENCES.csv','percell'),('MOVEMENT_PHASE_SUMMARY.csv','moves')]:
 with (root/fn).open(encoding='utf-8') as f:original=list(csv.DictReader(f))
 assert len(original)==len(r[key])
 for a,b in zip(original,r[key]):
  for k,v in b.items():
   if isinstance(v,bool):assert a[k]==str(v)
   elif isinstance(v,(float,int)):assert math.isclose(float(a[k]),float(v),rel_tol=3e-13,abs_tol=1e-14),(fn,k)
   else:assert a[k]==str(v)
print(json.dumps(dict(status='PASS_BOUNDARY_POINT_RAW_SCORE_RNG_PHASE_MOVEMENT_VERIFICATION',new_science_calls=12,parity_calls=2,old_native_uniform_reused=4,all_8_factorial_choices='K2',native_score_max_relative_tolerance=3e-13),indent=2))
