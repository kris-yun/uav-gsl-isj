"""Preserve one aborted slot and resume only untouched preregistered slots."""
from pathlib import Path
import ast,csv,datetime,hashlib,json,os,shutil
R=Path(__file__).resolve().parent
D=R/'recovery/B2_R04_ISOLATION_INTERRUPT'
gate=json.loads((D/'RECOVERY_GATE.json').read_text())
assert gate['status']=='PASS_CURRENT_DOMAIN_VACANT_FROZEN_BINARY_UNCHANGED'
assert not (R/'BATCH_PROCESS_ACTIVE.json').exists()
P=R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json'
plan=json.loads(P.read_text())
C=R/'cases/B2_R04'
monitor=json.loads((C/'PROCESS_OWNERS_AND_MONITOR.json').read_text())
assert monitor['forced']=='ISOLATION_FAILURE'
assert any(v.get('unknown') for v in monitor['monitor'])
assert all(not v.get('foreign') for v in monitor['monitor'])
assert json.loads((C/'RUN_RESULT.json').read_text())['goal_accepted']
records=json.loads((R/'BATCH_LEDGER.json').read_text())
assert len(records)==4 and not any(v['role']=='B2_R04' for v in records)
q=dict(case='B2',role='B2_R04',qualification='TECHNICAL_ISOLATION_UNVERIFIED_ABORT_RETAINED',
 official_success=None,stop_reason='ENGINEERING_ISOLATION_UNVERIFIED_NO_DECLARATION',
 source_domain_class='EXCLUDED_DIAGNOSTIC_ONLY',native_goal_count=1,
 accepted_goal=True,source_updates_before_abort=len({z['update']for z in csv.DictReader((C/'runtime/native_posterior_updates.csv').open())}),
 scientific_performance_eligible=False,independent_randomness_claim=False,new_worlds=0,
 explanation='A same-UID OpenSSH sftp-server environment could not be read. No foreign domain process was observed; historical isolation cannot be certified. This is not a native source-inference failure. The slot is retained without a replacement goal.',
 parameters_or_native_binary_changed=False)
(C/'FINAL_RUN_QA.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
# Load only the existing evidence helper definitions, never the controller body.
source=(R/'run_batch_host.py').read_text()
tree=ast.parse(source)
safe=ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[])
ns={'__file__':str(R/'run_batch_host.py'),'R':R,'archives':Path(plan['archive_destination'])}
exec(compile(safe,str(R/'run_batch_host.py')+':helpers_only','exec'),ns)
archive=ns['archive']('B2_R04',C)
records.append(dict(role='B2_R04',QA=q,archive=archive))
ns['put'](R/'BATCH_LEDGER.json',records)
ns['table'](records)
for name in ['BATCH_STOP.json','BATCH_PROCESS_FINISHED.json','BATCH_CHECKPOINT.json','FINAL_DELIVERY_RECEIPT.json','GITHUB_DELIVERY_RECEIPT.json']:
    p=R/name
    if p.exists():
        dest=D/('PRE_RESUME_'+name)
        assert not dest.exists()
        shutil.copyfile(p,dest)
        if name in ['BATCH_STOP.json','BATCH_PROCESS_FINISHED.json']:p.rename(D/('ORIGINAL_'+name))
amendment=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 status='RESUME_UNTOUCHED_SLOTS_AFTER_FRESH_ISOLATION_GATE',
 original_protocol_sha256=hashlib.sha256(P.read_bytes()).hexdigest(),
 B2_R04='Accepted goal aborted by conservative isolation guard. Retained technical slot; no replacement or outcome retry.',
 remaining_roles=[v['id']for v in plan['roles']if not any(x['role']==v['id']for x in records)],
 new_goal_cap=len([v for v in plan['roles']if not any(x['role']==v['id']for x in records)]),
 isolation_guard_unchanged=True,scientific_parameters_unchanged=True,
 frozen_binary_unchanged=True,original_raw_evidence_retained=True,
 previous_partial_delivery_retained=True,
 expected_final_report='12 slots accounted, at most 11 full scientific runs and one technical abort; do not claim 12 completed localization runs.')
(R/'RESUME_AMENDMENT_R3.json').write_text(json.dumps(amendment,ensure_ascii=False,indent=2)+'\n')
old="dict(stage='TWELVE_NATIVE_REPETITIONS_COMPLETE',completed=[x['role']for x in records],total=12,independent_seed_claim=False)"
new="dict(stage='TWELVE_PREREGISTERED_SLOTS_ACCOUNTED',completed=[x['role']for x in records],total=12,full_scientific_runs=sum(x['QA']['qualification'].startswith('PASS')for x in records),technical_abort_slots=sum(not x['QA']['qualification'].startswith('PASS')for x in records),independent_seed_claim=False)"
assert old in source
dest=R/'run_batch_host_RESUME_R3.py'
assert not dest.exists()
dest.write_text(source.replace(old,new),encoding='utf8')
print(json.dumps(amendment,ensure_ascii=False,indent=2))
