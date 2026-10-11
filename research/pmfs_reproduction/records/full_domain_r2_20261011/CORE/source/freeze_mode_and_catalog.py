from common_r2 import *
import csv,math,shutil,numpy as np
profile=load(HOST/'PROFILE_LEDGER.json');assert profile['status'].startswith('PASS')
dump(CORE/'COST_PROFILE_RESULT.json',profile)
# Conservative allowance includes residual dispatch/storage, uncertain new-source
# survival, two full query plans, native maps/blur and all saved prefix fields.
bank_allowance=max(72.0,max(r['historical_generation_wall_s']+r['two_plan_query']['wall_s']+r['transfer_ram_s']+10 for r in profile['records']))
factor=1.5;atomic_sources=load(CORE/'geometry/CANDIDATE_MODES_PRECHECK.json')['ATOMIC_sources']
fixed_other=1+6+4;atomic_estimate=factor*bank_allowance*(atomic_sources*2+fixed_other)
possible=load(CORE/'geometry/CANDIDATE_MODES_PRECHECK.json')['COARSE_sources'];choices=[]
for tile,n in possible.items():
 estimate=factor*bank_allowance*(n*2+fixed_other)
 if estimate<=8400:choices.append((n,-int(tile),int(tile),estimate))
assert atomic_estimate>9000 and choices,'No unregistered smaller/better source subset allowed'
n,_,tile,estimate=max(choices);catalog=load(CORE/f'geometry/COARSE_TILE{tile}_SOURCE_CATALOG.json')
assert len(catalog)==n;shutil.copy2(CORE/f'geometry/COARSE_TILE{tile}_CELL_TO_SOURCE.npy',CORE/'SOURCE_CELL_TO_REGION.npy')
dump(CORE/'SOURCE_CATALOG_AND_COVERAGE.json',dict(mode='COARSE',source_count=n,atomic_cells_covered=atomic_sources,receiver_scoring_cells=447,time_blocks=50,reference_count=2,source_height=-.5,tile_size_cells=tile,catalog=catalog,atomic_source_endpoint='NOT_TESTED_BY_THIS_COARSE_CAMPAIGN',catalog_rule='geometry-only fixed tile plus4-connected components; centroid medoid, fixed ties; uniform fine-cell source-area prior',source_truth_used_for_catalog=False))
known=set()
for j in load(BASE/'outputs/PMFS_RK2B_CONTINUOUS_20261010_CORE/experiment_registry.json')['jobs']:known.update([j['gaussian_seed'],j['uniform_seed']])
for j in load(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/frozen_contract.json')['jobs']:known.update(j['seeds'])
for j in load(R1/'FRESH_CONFIRMATION_PREREGISTRATION.json')['jobs']:known.update(j['seeds'])
refs=[]
for c in catalog:
 for rep in [0,1]:
  tag=f'PMFS_FULL_DOMAIN_R2|984cab0356872db354c909b1d534a510827ddbd2|COARSE{tile}|{c["source_id"]}|REFERENCE{rep}'
  seeds=[int.from_bytes(hashlib.sha256((tag+'|'+k).encode()).digest()[:4],'big') for k in ['gaussian','uniform']];assert not known.intersection(seeds);known.update(seeds)
  refs.append(dict(id=f'{c["source_id"]}_REF{rep}',source_id=c['source_id'],source_index=c['source_index'],source_xyz=[c['x'],c['y'],c['z']],replicate=rep,seeds=seeds,tag=tag))
old_cells=set(load(R1/'GEOMETRY_SUPPORT_INTERSECTION.json')['source_nav_indexes'].values());pool=[c for c in catalog if c['representative_cell'] not in old_cells]
def key(c):return hashlib.sha256(('R2-FRESH-SOURCE-SELECTION-984cab0|'+c['source_id']).encode()).hexdigest()
selected=[min(pool,key=key)]
for _ in range(2):selected.append(max([c for c in pool if c not in selected],key=lambda c:(min((c['x']-q['x'])**2+(c['y']-q['y'])**2 for q in selected),key(c))))
fresh=[]
for c in selected:
 for rep in [0,1]:
  tag=f'PMFS_FULL_DOMAIN_R2|984cab0|FUTURE_OBSERVATION|{c["source_id"]}|{rep}'
  seeds=[int.from_bytes(hashlib.sha256((tag+'|'+k).encode()).digest()[:4],'big') for k in ['gaussian','uniform']];assert not known.intersection(seeds);known.update(seeds)
  fresh.append(dict(oid=f'Z{len(fresh):02d}',source_id=c['source_id'],true_region=c['source_index'],source_cell=c['representative_cell'],source_xyz=[c['x'],c['y'],c['z']],seeds=seeds,tag=tag))
dump(CORE/'evaluation_only/FUTURE6_PREREGISTRATION.json',dict(status='FROZEN_BEFORE_ANY_NEW_REFERENCE_RESULTS',selection='first minimumfixedSHA, then maximin Euclidean geometry distance; SHA tie; excludeold5source cells',jobs=fresh,old_observation_cells=sorted(old_cells),plan='PUBLIC_B unchanged',activation='Only development gate passes and resource is available; no rerun/rescue'))
freeze=dict(status='COARSE_FROZEN_BEFORE_NEW_SCIENTIFIC_REFERENCE',mode='COARSE',source_count=n,tile=tile,geometry_complete=True,atomic_sources=atomic_sources,atomic_estimate_s=atomic_estimate,conservative_bank_allowance_s=bank_allowance,conservative_factor=factor,coarse_estimate_s=estimate,physics_query_cap_s=9000,reference_calls=n*2,IO_anchor_calls=1,max_new_observation_calls=6,technical_retry_reserve_calls=4,gas_call_limit=140,total_wall_cap_s=14400,mode_changed_after_results=False,parameters_reduced=False,COST_PROFILE_SHA256=sha(CORE/'COST_PROFILE_RESULT.json'),CATALOG_SHA256=sha(CORE/'SOURCE_CATALOG_AND_COVERAGE.json'),prefix_generation=False,full_original1000s=True)
dump(CORE/'MODE_AND_BUDGET_FREEZE.json',freeze);dump(CORE/'REFERENCE_JOBS_PREREGISTRATION.json',refs)
print(json.dumps(freeze));print('preflight_elapsed_s',time.time()-load(WORK/'ENTRY_TIME.json')['start_unix'])
