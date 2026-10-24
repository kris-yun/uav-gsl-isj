"""One E3 startup recovery, with no prior native goal or posterior outcome."""
from pathlib import Path
import datetime,hashlib,json,shutil
R=Path(__file__).resolve().parent
assert not(R/'BATCH_PROCESS_ACTIVE.json').exists()
C=R/'cases/E3_R01';q=json.loads((C/'RUN_RESULT.json').read_text())
assert q['native_goal_count']==0 and not q.get('goal_accepted')and q['nonzero_cmd_vel_messages']==0
assert not(C/'runtime/native_posterior_updates.csv').exists()
text=(C/'runtime/launch.log').read_text()
assert 'Read map 'in text and 'failed to send response to /PioneerP3DX/map_server/change_state (timeout)'in text
records=json.loads((R/'BATCH_LEDGER.json').read_text());old=next(x for x in records if x['role']=='E3_R01')
D=R/'recovery/E3_R01_PREGOAL_LIFECYCLE_TIMEOUT';D.mkdir(exist_ok=False)
for name in ['BATCH_STOP.json','BATCH_PROCESS_FINISHED.json','BATCH_CHECKPOINT.json','BATCH_LEDGER.json','EPISODE_RESULTS.csv','FINAL_DELIVERY_RECEIPT.json','GITHUB_DELIVERY_RECEIPT.json']:
 p=R/name
 if p.exists():
  shutil.copyfile(p,D/('SNAPSHOT_'+name))
  if name in ['BATCH_STOP.json','BATCH_PROCESS_FINISHED.json']:p.rename(D/('ORIGINAL_'+name))
attempts=json.loads((R/'TECHNICAL_PREGOAL_ATTEMPTS.json').read_text())
attempts.append(dict(canonical_slot='E3_R01',attempt='E3_R01_PREGOAL_ATTEMPT1',native_goal_count=0,official_success=None,
 classification='TECHNICAL_PREGOAL_MAP_LIFECYCLE_RESPONSE_TIMEOUT',original_entry=old,raw_files_not_modified=True,
 cause='Official map image was read successfully; map_server change_state response timed out, leaving lifecycle initialization incomplete. No map topic or native source update followed.',replacement_is_outcome_retry=False))
(R/'TECHNICAL_PREGOAL_ATTEMPTS.json').write_text(json.dumps(attempts,indent=2)+'\n')
(R/'BATCH_LEDGER.json').write_text(json.dumps([x for x in records if x['role']!='E3_R01'],indent=2)+'\n')
N=R/'cases/E3_R01_RESTART_R6';N.mkdir(exist_ok=False)
g='/home/zyc/ros2_ws/research_runs/o24_paper_screen12_20261024/cases/E3_R01'
s='/mnt/hgfs/workspace/'+R.name+'/cases/E3_R01'
for name in ['CASE_META.json','N1_launch.py','runtime_driver.py','RUN_SHELL.sh','PHYSICAL_FRAME_TIME.csv']:
 b=(C/name).read_bytes()
 if name!='PHYSICAL_FRAME_TIME.csv':b=b.replace(g.encode(),(g+'_RESTART_R6').encode()).replace(s.encode(),(s+'_RESTART_R6').encode())
 (N/name).write_bytes(b)
assert json.loads((N/'CASE_META.json').read_text().replace(s+'_RESTART_R6',s).replace(g+'_RESTART_R6',g))==json.loads((C/'CASE_META.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
over=json.loads((R/'ROLE_EXECUTION_OVERRIDES_R4.json').read_text())
over['E3_R01']=dict(host_case=str(N),shared_case=s+'_RESTART_R6',guest_case=g+'_RESTART_R6',parameter_sha256=sha(N/'CASE_META.json'),timeline_sha256=sha(N/'PHYSICAL_FRAME_TIME.csv'))
(R/'ROLE_EXECUTION_OVERRIDES_R6.json').write_text(json.dumps(over,indent=2)+'\n')
source=(R/'run_case_guest_R4.py').read_text().replace('ROLE_EXECUTION_OVERRIDES_R4.json','ROLE_EXECUTION_OVERRIDES_R6.json')
(R/'run_case_guest_R6.py').write_text(source)
source=(R/'run_batch_host_RESUME_R5.py').read_text().replace('ROLE_EXECUTION_OVERRIDES_R4.json','ROLE_EXECUTION_OVERRIDES_R6.json').replace('run_case_guest_R4.py','run_case_guest_R6.py')
(R/'run_batch_host_RESUME_R6.py').write_text(source)
receipt=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='ONE_ZERO_GOAL_E3_STARTUP_RECOVERY',
 original_native_goals=0,original_source_updates=0,new_native_goal_cap=1,new_startup_recovery_cap=1,
 no_outcome_retry=True,original_failures_preserved=True,scientific_parameters_and_map_unchanged=True,
 scientific_protocol_sha256=sha(R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json'),
 code={n:sha(R/n)for n in ['run_case_guest_R6.py','run_batch_host_RESUME_R6.py','ROLE_EXECUTION_OVERRIDES_R6.json']})
(R/'RESUME_AMENDMENT_R6.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
