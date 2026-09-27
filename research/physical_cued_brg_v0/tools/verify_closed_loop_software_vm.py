"""Actual-source/variance/nav/observation execution check, no scientific gate."""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927');sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def main():
 raw=Path('/home/zyc/brg_closedloop_20260927/brg_common615_software_smoke_01_raw');b=TemplateBank.load(ROOT/'legal_support_v2/h03_native_legal_bank.npz')
 beliefs=[json.loads(x) for x in (raw/'beliefs.jsonl').read_text().splitlines()];steps=[json.loads(x) for x in (raw/'sidecar_events.jsonl').read_text().splitlines() if 'STEP ' in x]
 events=rows(raw/'measurement_events.csv');nav=rows(raw/'navigation_trace.csv');poses=rows(raw/'sim_pose_trace.csv')
 assert beliefs[0]['free_cells']==b.cells.tolist() and len(b.ids)==615
 assert len(steps)==len(events)==20
 pp=[];vv=[]
 for row in beliefs:
  if row['stage']!='source_update':continue
  q=np.asarray(row['source_map'])[b.cells];assert abs(q.sum()-1)<1e-12 and np.all(q>=0)
  expected,var=b.planner_maps(q);pp.append(float(np.max(np.abs(np.asarray(row['source_map'])-expected))));vv.append(float(np.max(np.abs(np.asarray(row['variance_map'])-var))))
 assert pp and max(pp)<1e-12 and max(vv)<1e-12
 sent=[r for r in nav if r['event']=='SENT'];done=[r for r in nav if r['event']=='RESULT' and r['outcome']=='SUCCEEDED']
 assert len(sent)>=2 and len(done)>=1
 positions={(round(float(r['x']),4),round(float(r['y']),4)) for r in poses};assert len(positions)>2
 report={'status':'SOFTWARE_INTERACTIVE_CLOSED_LOOP_VERIFIED_NOT_SCIENTIFIC_PASS','old_six_label_weights_function_check_only':True,'excluded_from_pilot':True,
  'support':615,'observations':len(events),'sidecar_steps':len(steps),'source_update_count':len(pp),'source_map_max_abs_error':max(pp),'variance_map_max_abs_error':max(vv),
  'goals_sent':len(sent),'vgr_goals_succeeded':len(done),'distinct_pose_positions':len(positions),'all_actual_belief_supports_match':all(r['free_cells']==b.cells.tolist() for r in beliefs),
  'hashes':{p.name:sha(p) for p in [raw/'beliefs.jsonl',raw/'sidecar_events.jsonl',raw/'navigation_trace.csv',raw/'measurement_events.csv',raw/'sim_pose_trace.csv']},
  'actual_sidecar_replaced_both_probability_and_variance_before_original_native_goal_selection':True,'different_four_arm_paths_not_required':True}
 (ROOT/'software_common615_result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
