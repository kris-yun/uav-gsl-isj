import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,hashlib,math,numpy as np
from analyse_domain import analyse
r=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((r/'DOMAIN_EXECUTION_CONTRACT.json').read_text());assert sha(r/'DOMAIN_EXECUTION_CONTRACT.json')==(r/'DOMAIN_EXECUTION_CONTRACT_SHA256.txt').read_text().strip();assert sha(r/'DOMAIN_SUPPORT_FROZEN_CONTRACT.json')==c['parent_SHA256']=='a5acfa58fcc28f6300abe1a263213122cc0cf7dfe91922d71ac8dc5afd71b42e'
for n,d in c['source_SHA256'].items():assert sha(r/n)==d,n
assert sha(r/'snapshot/input.csv')==sha(r/'COMPLETE_COLUMN_MEAN_input.csv')==c['input_SHA256'];assert sha(r/'snapshot/gas_mask.csv')==sha(r/'GAS_TRANSPORT_MASK.csv')==c['mask_SHA256']
old=list(csv.DictReader((r.parent/'height_intervention/COLUMN_FREE_UNIFORM_MEAN_input.csv').open(encoding='utf-8')));new=list(csv.DictReader((r/'snapshot/input.csv').open(encoding='utf-8')));gas=list(csv.DictReader((r/'snapshot/gas_mask.csv').open(encoding='utf-8')));assert len(old)==len(new)==len(gas)==1530
mask=np.array([a['occupancy']=='1' for a in old]);assert int(sum(mask))==447
for a,b,g in zip(old,new,gas):
 for k in a:
  if k not in ['u','v']:assert a[k]==b[k]
 if a['occupancy']=='1':
  for k in ['u','v']:assert np.float32(a[k]).tobytes()==np.float32(b[k]).tobytes()
 assert int(g['gas_transport_free'])==1 and int(g['free_voxel_count'])>0
for n in ['metadata.csv','metadata.json','gaussian_cache.f32','simulation_parameters.csv']:assert sha(r/'snapshot'/n)==sha(r.parent/'boundary_point_experiment/snapshot'/n)
led=json.loads((r/'DOMAIN_EXECUTION_LEDGER.json').read_text());assert led==json.loads((r/'DOMAIN_EXECUTION_LEDGER_LOCAL.json').read_text());assert led['status']=='PASS_2_OLD_MASK_PARITY_4_TRANSPORT_DOMAIN_FORWARDS' and led['completed_calls']==6 and led['scientific_calls']==4 and led['wall_seconds']<60 and led['RSS_bytes']<536870912
assert all(led[k]==0 for k in ['new_GADEN','new_CFD','new_ROS_init','new_navigation'])
for anchor in led['anchors']:
 for item in anchor['checks']:assert sha(r/'forward_calls'/anchor['job']/item['file'])==item['SHA256']
for j in c['jobs']:
 p=r/'forward_calls'/j['job'];z=json.loads((p/'RESULT.json').read_text());g=json.loads((p/'GAS_DOMAIN_COUNTERS.json').read_text());m=json.loads((p/'MOVEMENT_COUNTERS.json').read_text());h=np.fromfile(next((p/'maps').glob('*_unblurred.f32')),dtype='<f4');assert np.all(h[~mask]==0) and np.all(np.isfinite(h)) and np.all((h[mask]>=0)&(h[mask]<=1))
 assert z['source_form']=='point' and z['boundary']=='native' and z['forward_calls']==1 and z['ROS_nodes']==z['native_updates']==0
 assert z['rng_before']==z['rng_after']==j['rng_before'] and z['gaussian_index_before']==j['gaussian_index_before'] and z['release_points']==2000
 assert m['slide_attempts']==m['recursion_guard_hits']==m['invalid_start_cell']==0
 assert g['enabled']==(j['gas_domain']=='column_union')
 if g['enabled']:assert g['gas_free_extra_cells']==1083 and g['recorded_particle_cell_instances_in_nav_obstacles']>0
res=analyse(r);assert res['summary']==json.loads((r/'DOMAIN_EXPERIMENT_RESULT.json').read_text())
for n,k in [('DOMAIN_FORWARD_SCORES.csv','rows'),('DOMAIN_PAIRED_COMPARISONS.csv','comparisons'),('DOMAIN_PER_CELL_CONTRIBUTIONS.csv','cells'),('DOMAIN_MOVEMENT_SUMMARY.csv','movement')]:
 with (r/n).open(encoding='utf-8') as f:saved=list(csv.DictReader(f))
 assert len(saved)==len(res[k])
 for a,b in zip(saved,res[k]):
  for key,v in b.items():
   if isinstance(v,bool):assert a[key]==str(v)
   elif isinstance(v,(float,int)):assert math.isclose(float(a[key]),v,rel_tol=3e-13,abs_tol=1e-14)
   else:assert a[key]==str(v)
assert json.loads((r/'DOMAIN_FINAL_PROCESS_RESOURCE_CHECK.json').read_text())['own_process_count']==0
print(json.dumps(dict(status='PASS_DOMAIN_SOURCE_HASH_INPUT_MASK_ANCHOR_NATIVE_SCORE_MOVEMENT_VERIFICATION',calls=6,scientific=4,parity=2,all_warmup_steps=200,all_record_steps=200,nav_readout_cells=447,gasfree=1530,both_pair_choices='K2'),indent=2))
