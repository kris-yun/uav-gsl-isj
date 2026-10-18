from pathlib import Path
import ast,difflib,json,shutil
R=Path(__file__).resolve().parent;plan=json.loads((R/'RUN_PRECOMMIT.json').read_text())
old=plan['roles'][0];newid='PF24_A2_T01';src=R/'cases'/old['id'];dst=R/'cases'/newid;dst.mkdir(exist_ok=True)
assert not (dst/'RUN_STARTED.json').exists()
def fix_wait(text):
 before=text
 oldcode="""   for k,v in META['expected_parameters'].items():
    assert k in values and values[k]==v,('RESOLVED_BASELINE_PARAMETER_MISMATCH',k,values.get(k),v)
   (R/'BASELINE_PARAMETER_GATE.json').write_text(json.dumps(dict(status='PASS_ACTUAL_NODE_PARAMETER_VALUES',checked=META['expected_parameters']),indent=2))
   dump_started=True"""
 newcode="""   missing=[k for k in META['expected_parameters']if k not in values]
   if missing:
    (R/'PARAMETER_DECLARATION_WAIT.json').write_text(json.dumps(dict(missing=missing,elapsed_after_goal_s=time.time()-starttime),indent=2))
    if time.time()-starttime>20:raise RuntimeError('REQUIRED_PARAMETERS_NOT_DECLARED:'+str(missing))
   else:
    for k,v in META['expected_parameters'].items():
     assert values[k]==v,('RESOLVED_BASELINE_PARAMETER_MISMATCH',k,values.get(k),v)
    (R/'BASELINE_PARAMETER_GATE.json').write_text(json.dumps(dict(status='PASS_ACTUAL_NODE_PARAMETER_VALUES',checked=META['expected_parameters']),indent=2))
    dump_started=True"""
 if oldcode not in text:
  assert newcode in text
  return before,text
 assert text.count(oldcode)==1;text=text.replace(oldcode,newcode);ast.parse(text)
 return before,text
for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','CASE_META.json','AUTHOR_WALL_FILE_CADENCE.csv']:
 text=(src/name).read_text().replace(old['id'],newid)
 if name=='runtime_driver.py':
  before,text=fix_wait(text)
  (dst/'PARAMETER_OBSERVER_WAIT.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile='observer_early_snapshot',tofile='observer_wait_declared_params')),encoding='utf-8')
 (dst/name).write_text(text,encoding='utf-8',newline='\n')
# B2 has not been launched. Apply the same observer-only qualification fix before its first execution.
bdir=R/'cases'/plan['roles'][1]['id'];path=bdir/'runtime_driver.py';before,text=fix_wait(path.read_text())
if not (bdir/'runtime_driver_before_parameter_wait.py').exists():(bdir/'runtime_driver_before_parameter_wait.py').write_text(before)
path.write_text(text,encoding='utf-8',newline='\n')
retry={**old,'id':newid,'guest_path':old['guest_path'].replace(old['id'],newid),'runtime_shared':old['runtime_shared'].replace(old['id'],newid)}
nextplan=dict(plan);nextplan['roles']=[retry,plan['roles'][1]];nextplan['technical_attempt_already_retained']=old['id'];nextplan['cumulative_goals_if_all_complete']=3
(R/'RUN_PRECOMMIT_NEXT.json').write_text(json.dumps(nextplan,indent=2))
(R/'TECHNICAL_RETRY_AMENDMENT_01.json').write_text(json.dumps(dict(reason='Observer snapshot arrived before lazy constructor declared stop_and_measure_time. Native algorithm not modified.',retained_original=old['id'],retry=newid,code_binary_changed=False,parameters_changed=False,source_or_wind_changed=False,original_total_goal_cap=4,new_total_goal_cap=4,max_wait_for_parameter_declaration_s=20),indent=2))
print(json.dumps(dict(status='OBSERVER_WAIT_RETRY_PREPARED',roles=[r['id']for r in nextplan['roles']])))
