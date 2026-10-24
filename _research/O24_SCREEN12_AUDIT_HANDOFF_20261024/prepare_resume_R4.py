"""Repair only monitor ownership race; retain zero-goal A2 startup evidence."""
from pathlib import Path
import datetime,hashlib,json,shutil
R=Path(__file__).resolve().parent
D=R/'recovery/A2_R02_PREGOAL_OWNERSHIP_RACE';D.mkdir(exist_ok=True)
assert not(R/'BATCH_PROCESS_ACTIVE.json').exists()
P=R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json';plan=json.loads(P.read_text())
C=R/'cases/A2_R02'
res=json.loads((C/'RUN_RESULT.json').read_text());assert res['native_goal_count']==0 and not res.get('goal_accepted')
mon=json.loads((C/'PROCESS_OWNERS_AND_MONITOR.json').read_text())
bad=[s for s in mon['monitor']if s['foreign']or s['unknown']]
assert mon['forced']=='ISOLATION_FAILURE'and bad and not any(s['unknown']for s in bad)
owners={v['pid']:v for v in mon['owners']}
assert all(v['ppid']in owners and v['create_time']>=owners[v['ppid']]['create_time']for s in bad for v in s['foreign'])
records=json.loads((R/'BATCH_LEDGER.json').read_text())
entry=next(x for x in records if x['role']=='A2_R02')
assert entry['QA']['native_goal_count']==0
# Do not edit the archived original; corrected interpretation is a separate receipt.
attempt=dict(canonical_slot='A2_R02',attempt='A2_R02_PREGOAL_ATTEMPT1',
 native_goal_count=0,official_success=None,classification='TECHNICAL_PREGOAL_MONITOR_OWNERSHIP_RACE',
 original_entry=entry,raw_files_not_modified=True,
 cause='Native child processes born between descendant enumeration and process inventory were falsely classified foreign. Saved parent PID and creation time identify them as this attempt children.',
 replacement_is_outcome_retry=False)
(R/'TECHNICAL_PREGOAL_ATTEMPTS.json').write_text(json.dumps([attempt],indent=2)+'\n')
for name in ['BATCH_STOP.json','BATCH_PROCESS_FINISHED.json','BATCH_CHECKPOINT.json','FINAL_DELIVERY_RECEIPT.json','GITHUB_DELIVERY_RECEIPT.json','BATCH_LEDGER.json','EPISODE_RESULTS.csv']:
 p=R/name
 if p.exists():
  dst=D/('ORIGINAL_'+name);assert not dst.exists();shutil.copyfile(p,dst)
  if name in ['BATCH_STOP.json','BATCH_PROCESS_FINISHED.json']:p.rename(D/('RETAINED_'+name))
records=[x for x in records if x['role']!='A2_R02']
(R/'BATCH_LEDGER.json').write_text(json.dumps(records,indent=2)+'\n')
N=R/'cases/A2_R02_RESTART_R4';N.mkdir(exist_ok=False)
guest_original='/home/zyc/ros2_ws/research_runs/o24_paper_screen12_20261024/cases/A2_R02'
guest_new=guest_original+'_RESTART_R4'
shared_original='/mnt/hgfs/workspace/'+R.name+'/cases/A2_R02'
shared_new=shared_original+'_RESTART_R4'
for name in ['CASE_META.json','N1_launch.py','runtime_driver.py','RUN_SHELL.sh','PHYSICAL_FRAME_TIME.csv']:
 b=(C/name).read_bytes()
 if name!='PHYSICAL_FRAME_TIME.csv':b=b.replace(guest_original.encode(),guest_new.encode()).replace(shared_original.encode(),shared_new.encode())
 (N/name).write_bytes(b)
assert json.loads((N/'CASE_META.json').read_text().replace(shared_new,shared_original).replace(guest_new,guest_original))==json.loads((C/'CASE_META.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
override={'A2_R02':dict(host_case=str(N),shared_case=shared_new,guest_case=guest_new,
 parameter_sha256=sha(N/'CASE_META.json'),timeline_sha256=sha(N/'PHYSICAL_FRAME_TIME.csv'))}
(R/'ROLE_EXECUTION_OVERRIDES_R4.json').write_text(json.dumps(override,indent=2)+'\n')
source=(R/'run_case_guest.py').read_text()
old="C=R/'cases'/plan['role'];V=Path(plan['guest_case']);assert not V.exists()and not(C/'RUN_STARTED.json').exists();assert sha(plan['binary_path'])==plan['binary_sha256']"
new="override=json.loads((R/'ROLE_EXECUTION_OVERRIDES_R4.json').read_text()).get(plan['role'],{});C=Path(override.get('shared_case',str(R/'cases'/plan['role'])));V=Path(override.get('guest_case',plan['guest_case']));assert not V.exists()and not(C/'RUN_STARTED.json').exists();assert sha(plan['binary_path'])==plan['binary_sha256']"
assert old in source;source=source.replace(old,new)
old="snap=inventory(228,exclude={os.getpid()});foreign=[x for x in snap['matching_domain_processes']if x['pid']not in owners];unknown=[]"
new="snap=inventory(228,exclude={os.getpid()});ownership_proofs=adopt_new_children(snap['matching_domain_processes'],owners);foreign=[x for x in snap['matching_domain_processes']if x['pid']not in owners or x['create_time']!=owners[x['pid']]['create_time']];unknown=[]"
assert old in source;source=source.replace(old,new)
source=source.replace("from isolation_guard import inventory,require_vacant","from isolation_guard import inventory,require_vacant\nfrom process_ownership_R4 import adopt_new_children")
source=source.replace("foreign=foreign,unknown=unknown))","foreign=foreign,unknown=unknown,ownership_proofs=ownership_proofs))")
source=source.replace("stage='NATIVE_A2_IN_PROGRESS'","stage='NATIVE_'+role['case']+'_IN_PROGRESS'")
(R/'run_case_guest_R4.py').write_text(source)
source=(R/'run_batch_host_RESUME_R3.py').read_text()
source=source.replace("C=Path(role['host_case']);put(","override=json.loads((R/'ROLE_EXECUTION_OVERRIDES_R4.json').read_text()).get(role['id'],{});C=Path(override.get('host_case',role['host_case']));put(")
source=source.replace("role['parameter_sha256']","override.get('parameter_sha256',role['parameter_sha256'])").replace("role['timeline_sha256']","override.get('timeline_sha256',role['timeline_sha256'])")
source=source.replace("G+'/run_case_guest.py'","G+'/run_case_guest_R4.py'").replace("role['shared_case']","override.get('shared_case',role['shared_case'])")
(R/'run_batch_host_RESUME_R4.py').write_text(source)
amendment=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PREGOAL_RECOVERY_MONITOR_ONLY',
 scientific_protocol_sha256=sha(P),remaining_roles=[x['id']for x in plan['roles']if not any(v['role']==x['id']for v in records)],
 new_goal_cap=6,original_A2_R02_native_goals=0,original_A2_R02_preserved=True,
 B2_R04_not_retried=True,no_algorithm_or_scientific_parameter_change=True,
 guard_change='Certify newly-born children by live ancestor PID AND creation-time identity. Unknown/foreign processes still block. No executable-name exception.',
 new_files={n:sha(R/n)for n in ['process_ownership_R4.py','run_case_guest_R4.py','run_batch_host_RESUME_R4.py','ROLE_EXECUTION_OVERRIDES_R4.json']})
(R/'RESUME_AMENDMENT_R4.json').write_text(json.dumps(amendment,indent=2)+'\n')
print(json.dumps(amendment,indent=2))
