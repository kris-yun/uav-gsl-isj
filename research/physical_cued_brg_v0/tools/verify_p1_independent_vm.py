"""Independent raw-log geometric endpoint recomputation; no network/source relabel."""
import json,math,hashlib,csv
import numpy as np
from pathlib import Path
P=Path('/mnt/hgfs/workspace/_staging/BRG_NATIVE615_PILOT_P1_V2_20260927')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 records=[];checks=[]
 for file in sorted(P.glob('source_*__*.json')):
  a=json.loads(file.read_text());raw=Path(a['raw_run_directory'])
  lines=[json.loads(x) for x in (raw/'beliefs.jsonl').read_text().splitlines()]
  legal=[x for x in lines if 0<=x['search_time_s']<=300 and all(math.isfinite(v) for key in ['estimate_xy','source_map','variance_map'] for v in x[key])]
  assert legal and a['actual_native_support_count']==615 and a['common615_support_matches']
  last=legal[-1];estimate=last['estimate_xy'];assert estimate==a['estimate_xy']
  cells=sorted(last['free_cells'],key=lambda i:-last['source_map'][i]);n=math.ceil(len(cells)*.05)
  cutoff_tied=last['source_map'][cells[n-1]]==last['source_map'][cells[n]]
  # Native Vector2/grid coordinate arithmetic uses float32; tolerate its roundoff.
  weights=np.array([last['source_map'][i] for i in cells[:n]],dtype=np.float64)
  coords=np.array([[last['origin_x']+(i%last['width']+.5)*last['resolution'],last['origin_y']+(i//last['width']+.5)*last['resolution']] for i in cells[:n]])
  recomputed=(weights[:,None]*coords).sum(0)/weights.sum()
  if not cutoff_tied:assert np.max(np.abs(recomputed-estimate))<2e-5,'Native top5-percent estimate differs from probability map'
  error=math.hypot(estimate[0]-a['truth_xy'][0],estimate[1]-a['truth_xy'][1]);assert abs(error-a['final_source_error_m'])<1e-12
  success=int(a['status'] in ['completed','time_budget'] and error<=.5);assert success==a['geometric_success']
  assert a['wrong_declaration']==int(a['algorithm_declared_success'] and error>.5)
  if not a['truth_in_support']:assert a['exact_cell_rank'] is None and a['extended_true_label_probability']==0 and a['extended_true_label_nll']=='positive_infinity'
  with (raw/'sim_pose_trace.csv').open() as f:poses=[r for r in csv.DictReader(f) if float(r['t_sim_s'])<=300]
  distance=sum(math.hypot(float(v['x'])-float(u['x']),float(v['y'])-float(u['y'])) for u,v in zip(poses,poses[1:]));assert abs(distance-a['path_length_m'])<1e-9
  checks.append({'case':a['case_id'],'arm':a['arm'],'error_m':error,'success':success,'path_m':distance,'top5pct_recomputed_xy':recomputed.tolist(),'top5pct_cutoff_tied':cutoff_tied,'raw_belief_sha256':sha(raw/'beliefs.jsonl')});records.append(a)
 assert len(records)==16 and len({a['case_id'] for a in records})==4
 pairs={}
 for row in records:
  context=[row[k] for k in ['source_id','plume_id','initial_pose_id','observation_contract_id','candidate_support_id','truth_xy','truth_in_support','budget_s']]
  assert pairs.setdefault(row['case_id'],context)==context,'four-arm context mismatch'
 summary={}
 for arm in ['native_pmfs','candidate_gru','brg','brg_ungated']:
  rows=[a for a in records if a['arm']==arm];assert len(rows)==4
  summary[arm]={'successes':sum(x['geometric_success'] for x in rows),'cases':4,'mean_error_m':sum(x['final_source_error_m'] for x in rows)/4,'mean_path_m':sum(x['path_length_m'] for x in rows)/4,'timeouts':sum(x['timeout'] for x in rows),'declared':sum(x['algorithm_declared_success'] for x in rows),'wrong_declarations':sum(x['wrong_declaration'] for x in rows)}
 out={'status':'INDEPENDENT_RAW_LOG_GEOMETRY_RECOMPUTATION_PASS','runs':16,'comparison':summary,'checks':checks,'fixed_pilot_not_all96':True}
 (P/'INDEPENDENT_RECOMPUTATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['comparison'],indent=2))
if __name__=='__main__':main()
