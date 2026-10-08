"""Verify all prior seals and derive the ONLY 28 legal E3 rows."""
from pathlib import Path
import csv,datetime,hashlib,json,shutil,subprocess
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';E1=R.parent/'m0_e0_e1_20261007';E2=R.parent/'m0_e2_sentinel_20261007'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p):
    with Path(p).open(encoding='utf-8') as f:return list(csv.DictReader(f))
def write(n,x):(R/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
assert not (R/'E3_AUTHORIZATION.json').exists()
checks={}
for root,manifest in [(F,'M0_R0_FILES_SHA256.csv'),(E1,'E1_EVIDENCE_FILES_SHA256.csv'),(E2,'E2_EVIDENCE_FILES_SHA256.csv')]:
    files=rows(root/manifest)
    for q in files:assert sha(root/q['path'])==q['sha256'] and (root/q['path']).stat().st_size==int(q['bytes']),q['path']
    checks[root.name]=len(files)
assert read(E1/'E1_DECISION.json')['verdict']=='M0_E1_BASELINE_QUALIFIED';assert read(E2/'E2_DECISION.json')['verdict']=='M0_E2_CRN_SENTINEL_QUALIFIED'
allrows=rows(F/'M0_RUNLIST_PREVIEW.csv');done1=read(E1/'E1_COMPLETED_RUNS.json');done2=read(E2/'E2_COMPLETED_RUNS.json');done={q['run_id'] for q in done1+done2}
assert len(allrows)==40 and len(done)==12 and len(done1)==8 and len(done2)==4 and all(q['launch_authorized']=='False' for q in allrows)
todo=[q for q in allrows if q['run_id'] not in done];assert len(todo)==28 and all(q['wind_arm']!='U0' for q in todo)
head=subprocess.check_output(['git','rev-parse','FETCH_HEAD'],cwd=R).decode().strip();review=subprocess.check_output(['git','show',head+':handoff/pro_20261007/M0_E2_REVIEW_E3_28_RUN_CONDITIONAL_PLAN_20261007.md'],cwd=R)
(R/'M0_E2_REVIEW_E3_28_RUN_CONDITIONAL_PLAN_20261007.md').write_bytes(review)
for q in todo:assert q['run_id'] in review.decode(),q['run_id']
write('E3_AUTHORIZATION.json',{'stage':'E3_FINAL_28','direct_user_authorization':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all_frozen_rows':allrows,'previous_completed_ids':sorted(done),'allowed_rows':todo,'allowed_run_ids':[q['run_id'] for q in todo],'science_runs_max_this_turn':28,'science_runs_max_total':40,'review_commit':head,'review_sha256':hashlib.sha256(review).hexdigest(),'parent_E1_commit':'653dae35a72b1e29c52c37745806571bff016ef6','parent_E2_commit':'49ba99301a4c963244d423b07b8aa179c8e4eb3c','R0_E1_E2_files_verified':checks,'remote_root':'/home/zyc/ros2_ws/m0_clean_support_r0_20261007/e3_final','stop_on_any_qualification_failure':True,'automatic_retry_allowed':False,'final_scoring_authorized_if_all40_qualified':True,'scientific_contract_changes':0,'no_additional_design_or_training':True})
with (R/'E3_RUNLIST_AUTHORIZED.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(todo[0]),lineterminator='\n');w.writeheader();w.writerows(todo)
shutil.copytree(F,R/'frozen')
for root,names in [(E1,['E0_QUALIFICATION.json','E1_HELPER_BUILD.json','E1_DECISION.json','E1_EVIDENCE_SEAL.json','ASSET_MANIFEST.json']),(E2,['E2_DECISION.json','E2_EVIDENCE_SEAL.json','E2_AUDIT_CLOCK_SERIALIZATION_ERRATUM.json'])]:
    for name in names:(R/('PARENT_'+name)).write_bytes((root/name).read_bytes())
(R/'remote_env.sh').write_bytes((E1/'remote_env.sh').read_bytes());(R/'M0_UAV_ROUTE_POINTS.csv').write_bytes((F/'M0_UAV_ROUTE_POINTS.csv').read_bytes())
print(json.dumps({'verified':checks,'already_completed':12,'unique_remaining':28,'frozen_order':[q['run_id'] for q in todo]},indent=2))
