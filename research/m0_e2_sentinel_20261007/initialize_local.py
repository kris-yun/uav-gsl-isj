"""New, narrowly scoped E2 authorization. Never edits R0 or E1."""
from pathlib import Path
import csv,hashlib,json,subprocess,datetime
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';E=R.parent/'m0_e0_e1_20261007'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(n,x):(R/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def verify(folder,manifest):
    with (folder/manifest).open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    for q in rows:
        p=folder/q['path'];assert sha(p)==q['sha256'] and p.stat().st_size==int(q['bytes']),q['path']
    return len(rows)
assert not (R/'M0_E2_AUTHORIZATION.json').exists()
assert verify(F,'M0_R0_FILES_SHA256.csv')==39
es=read(E/'E1_EVIDENCE_SEAL.json');assert sha(E/'E1_EVIDENCE_FILES_SHA256.csv')==es['manifest_sha256']
n=verify(E,'E1_EVIDENCE_FILES_SHA256.csv');assert read(E/'E1_DECISION.json')['verdict']=='M0_E1_BASELINE_QUALIFIED'
ids=['m0r0_'+a+'_S0_r01' for a in ['A_on','A_off','B_shear','B_speed']]
with (F/'M0_RUNLIST_PREVIEW.csv').open(encoding='utf-8') as f:allrows=list(csv.DictReader(f))
selected=[next(q for q in allrows if q['run_id']==rid) for rid in ids]
assert len(allrows)==40 and all(q['launch_authorized']=='False' for q in allrows)
for q in selected:assert q['source_id']=='S0' and q['realization']=='1' and q['master_seed']=='2026100701'
head=subprocess.check_output(['git','rev-parse','FETCH_HEAD'],cwd=R).decode().strip()
review=subprocess.check_output(['git','show',head+':handoff/pro_20261007/M0_E0_E1_REVIEW_AND_E2_SENTINEL_AUTHORIZATION_PLAN_20261007.md'],cwd=R)
(R/'M0_E0_E1_REVIEW_AND_E2_SENTINEL_AUTHORIZATION_PLAN_20261007.md').write_bytes(review)
write('M0_E2_AUTHORIZATION.json',{'stage':'E2_ONLY','direct_user_authorization':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'allowed_run_ids':ids,'frozen_rows':selected,'reference_id':'m0r0_U0_S0_r01','master_seed':2026100701,'new_scientific_runs_max':4,'remaining_28_authorized':False,'E3_authorized':False,'mandatory_stop_after_E2':True,'scientific_design_changes':0,'original_runlist_unchanged':True,'remote_root':'/home/zyc/ros2_ws/m0_clean_support_r0_20261007/e2_sentinel','parent_e1_commit':'653dae35a72b1e29c52c37745806571bff016ef6','review_commit':head,'review_sha256':hashlib.sha256(review).hexdigest(),'R0_seal_sha256':sha(F/'M0_R0_FREEZE.json'),'E1_seal_sha256':sha(E/'E1_EVIDENCE_SEAL.json'),'E1_full_package_sha256':'09c07dbf7acbb7587267a31681d803aa1287b878a4dd98086357dd7c357636d1','E1_files_verified':n,'qualified_verdict':'M0_E2_CRN_SENTINEL_QUALIFIED','failed_verdict':'M0_E2_PREREQUISITE_HOLD','no_material_effect_scoring_in_E2':True})
for name in ['E0_QUALIFICATION.json','E1_HELPER_BUILD.json','E1_DECISION.json','E1_EVIDENCE_SEAL.json','ASSET_MANIFEST.json']:(R/('PARENT_'+name)).write_bytes((E/name).read_bytes())
(R/'M0_UAV_ROUTE_POINTS.csv').write_bytes((F/'M0_UAV_ROUTE_POINTS.csv').read_bytes())
(R/'remote_env.sh').write_bytes((E/'remote_env.sh').read_bytes())
print(json.dumps({'R0_files_verified':39,'E1_files_verified':n,'allowed_ids':ids,'E3_authorized':False},indent=2))
