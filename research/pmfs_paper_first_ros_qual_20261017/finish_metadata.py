from pathlib import Path
import hashlib,json,re,shutil
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(R/'PATCH_CLASSIFICATION.json',R/'PATCH_CLASSIFICATION_BEFORE_RECTANGULAR.json')
before=json.loads((R/'PATCH_CLASSIFICATION.json').read_text());allowed={r['path']:r['kind']for r in before['patches']};allowed['src/gsl_server/algorithms/PMFS/PMFS_utils.cpp']='RECTANGULAR_READOUT'
changed=[];unchanged=[]
for p in sorted((R/'official_exact/gsl_server').rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(R/'official_exact/gsl_server');q=R/'source_runtime'/rel
 assert q.exists()
 if p.read_bytes()==q.read_bytes():unchanged.append(dict(path=rel.as_posix(),sha256=sha(p)))
 else:
  assert rel.as_posix()in allowed,('Unclassified change',rel)
  changed.append(dict(path=rel.as_posix(),kind=allowed[rel.as_posix()],official_raw_sha256=sha(p),actual_runtime_sha256=sha(q)))
assert len(changed)==6
put(R/'PATCH_CLASSIFICATION.json',dict(status='FINAL_CLASSIFICATION_INCLUDES_RECTANGULAR_FIX',patches=changed,byte_unchanged_author_files=unchanged,unclassified_changed_files=0,source_changes_are_not_innovation=True,policy_parameter_overrides={'sourceDiscriminationPower':1,'convergence_thr':1,'useWindGroundTruth':False},native_GitHub_default_maxSearchTime_seconds=300,age_coverage_remains_disclosed_center_event=True))
counts=[]
for role in ['PF24_A2_T02','PF24_B2_Q01']:
 text=(R/'cases'/role/'runtime/launch.log').read_text(errors='replace')
 n=[int(x)for x in re.findall(r'Total number of simulations: (\d+)',text)]
 s=[float(x)for x in re.findall(r'Time ellapsed in simulation = ([0-9.eE+-]+) s',text)]
 counts.append(dict(role=role,source_updates=len(n),native_forward_calls=sum(n),native_forward_batch_wall_s=s))
put(R/'NATIVE_FORWARD_COST.json',dict(rows=counts,total_native_forward_calls=sum(r['native_forward_calls']for r in counts),note='Native forwards executed inside the authorized new ROS episodes. No new GADEN physical world or AIMMD comparison. These calls are not charged to or merged with the old completed900-call AIMMD pilot.'))
issues=[
 dict(stage='source acquisition',result='Pinned Git commit/tree fetched; sparse checkout network stalled and owned process tree was stopped; partial checkout preserved. Reconstructed185selected files by exact Git blob identity, reused118local files, downloaded67pinned raw files; all hashes/OIDs verified.'),
 dict(stage='source manifest script',result='First selection assumed every blob mode100644; an executable launch file mode100755 triggered an assertion before source execution. Selection corrected to allow both legal committed file modes; no source content was changed.'),
 dict(stage='rectangular unit harness',result='First minimal vector stub lacked a default constructor. Original failing source and compiler stderr retained. Stub corrected, exact author/fixed method bodies unchanged; deterministic rectangle control passed.'),
 dict(stage='runtime preparation',result='Old shared export did not include the guest-only AUTHOR_WALL_FILE_CADENCE.csv. Retrieved its exact existing guest bytes. A Python duplicate-key construction error in retry-role preparation was corrected before that retry ran; no additional ROS goal was issued by preparation.'),
 dict(stage='PF24_A2_Q01',result='Observer queried before lazy algorithm initialization completed; stop_and_measure_time had not been declared. One goal, zero source updates. Original result/CDR retained. Observer now waits up to20seconds for required parameters, without algorithm changes.'),
 dict(stage='PF24_A2_T01',result='Nav2 lifecycle service response timeout; no map delivery, zero goals. All logs retained. Candidate explanation is rapid reuse of a DDS domain; not asserted as unique root cause. Final roles use separate227/228 domains.'),
 dict(stage='wind audit',result='Initial offline audit collapsed duplicate ROS message header stamps into one dictionary entry and compared an undefined zero-speed direction as if nonzero. Raw CDR retained every message. Final audit retains lists per stamp, matches accepted speed exactly, follows original zero-speed direction0 branch, and checks latest-TF consistency over observed delivery intervals; initial result retained, no new ROS run.'),
 dict(stage='patch classification',result='Initial table predated the extra two rectangular-readout lines. Preserved initial table, then emitted final six-file classification using raw original-file SHA and actual runtime SHA. No unclassified author source changes.'),
]
put(R/'TECHNICAL_ISSUES.json',issues)
print(json.dumps(dict(status='FINAL_IDENTITY_AND_COSTS_RECORDED',changed_author_files=len(changed),unchanged_author_files=len(unchanged),forward_calls=sum(r['native_forward_calls']for r in counts))))
