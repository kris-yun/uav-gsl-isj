"""Collect existing evidence only; never launch any simulator or mutate parents."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,csv,shutil
W=Path(__file__).resolve().parent
BASE=W.parents[1]
O=BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
B4=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert sha(dst)==sha(src),(src,dst)
    else:shutil.copy2(src,dst)
for p in (W/'scoring_contract').iterdir():
    if p.is_file():copy(p,O/'observation_lineage/final_contract_delivery'/p.name)
for n in ['consumer_messages.csv','measurement_events.csv','raw_ros_cdr.jsonl.gz','service_queries.jsonl.gz','physical_clock_trace.csv','launch.log']:
    copy(B4/'runtime'/n,O/'frozen_B4_inputs/runtime'/n)
for p in (B4/'derived_B4').rglob('*'):
    if p.is_file():copy(p,O/'frozen_B4_inputs/derived_B4'/p.relative_to(B4/'derived_B4'))
for p in (B4/'source').rglob('*'):
    if p.is_file():copy(p,O/'frozen_B4_inputs/source'/p.relative_to(B4/'source'))
for n in ['B4_TERMINAL_RESULT.json','TOP5_SNAPSHOT_ESTIMATOR_REVIEW.json','B4_OBSERVATION_AND_POSTERIOR_AUDIT.csv']:
    copy(B4/n,O/'frozen_B4_inputs'/n)
copy(W/'M2_RAW_REFERENCE_QUERY_EVIDENCE.tar.gz',O/'archive_metadata_only_DO_NOT_DUPLICATE.tar.gz') if False else None
# New analysis metadata correction only. Scores, source definitions and raw evidence are unaffected.
for p in [W/'analyse_discrimination.py',O/'analyse_discrimination.py']:
    t=p.read_text(encoding='utf-8').replace('independent_stops=10','distinct_stops=10')
    p.write_text(t,encoding='utf-8',newline='\n')
p=O/'REALIZATION_EVENT_COUNTS.csv'
p.write_text(p.read_text(encoding='utf-8').replace('independent_stops,','distinct_stops,'),encoding='utf-8',newline='\n')
execution=O/'execution_scripts'
for p in W.iterdir():
    if p.is_file() and p.suffix in ['.py','.stdout','.stderr'] and p.name not in ['finalize_evidence.py']:
        copy(p,execution/p.name)
gens=[json.loads(p.read_text()) for p in (O/'native_reference_evidence/realizations').glob('*/GENERATION_QUALIFICATION.json')]
queries=[json.loads(p.read_text()) for p in (O/'native_reference_evidence/realizations').glob('*/QUERY_QUALIFICATION.json')]
rows=[]
for g,q in zip(sorted(gens,key=lambda a:(a['candidate_id'],a['realization'])),sorted(queries,key=lambda a:(a['candidate_id'],a['realization']))):
    assert (g['candidate_id'],g['realization'])==(q['candidate_id'],q['realization'])
    rows.append(dict(bank_id=g['candidate_id']+'_'+str(g['realization']),split=g['role'],generation_wall_s=g['generation_wall_s'],query_wall_s=q['query_wall_s'],generation_peak_RSS_bytes=g['peak_RSS_bytes'],query_peak_RSS_bytes=q['peak_RSS_bytes'],bank_bytes=g['bank_bytes'],frames=g['frames'],exit_code=g['exit_code']))
with (O/'RESOURCE_COST_PER_REALIZATION.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
sem=json.loads((O/'semantic_anchor/SEMANTIC_ANCHOR_RESULT.json').read_text())
summary=json.loads((O/'EIGHT_REFERENCE_CAPTURE_SUMMARY.json').read_text())
budget=dict(gas_generation_status='PASS_WITHIN_15_MIN_1_GiB_2_GiB_GENERATION_BUDGET',generation_total_wall_s=sum(x['generation_wall_s'] for x in gens),query_total_wall_s=sum(x['query_wall_s'] for x in queries),generation_peak_RSS_bytes=max(x['peak_RSS_bytes'] for x in gens),query_peak_RSS_bytes=max(x['peak_RSS_bytes'] for x in queries),task_disk_before_archiving_bytes=summary['task_disk_bytes'],source_conditioned_gas_realizations=8,smoke_included_in_eight=True,CFD_generations=0,navigation_goals=0,new_2D_candidate_forwards=0,training_runs=0,GADEN_generator_ROS_processes=8,pure_query_and_map_ROS_nodes=0,auxiliary_semantic_compiler_peak_RSS_bytes=1185017856,compiler_memory_exception='Auxiliary semantic C++ compilation exceeded 1 GiB (1.104 GiB). The supplied generation resource paragraph was implemented for generators; frozen_contract wording did not explicitly scope single-process RSS. Record the discrepancy, do not claim a universal process limit PASS.',distinct_stops_not_proven_independent=10,metadata_correction='New derived count column independent_stops renamed distinct_stops before final evidence freeze; no scores or raw data changed.')
(O/'RESOURCE_BUDGET_ACTUAL.json').write_text(json.dumps(budget,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(budget,ensure_ascii=False,indent=2))
