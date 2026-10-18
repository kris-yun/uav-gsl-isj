from pathlib import Path
import datetime,json
R=Path(__file__).resolve().parent
cleanup=json.loads((R/'POST_RUN_CLEANUP.json').read_text());row=cleanup['preserved'][0]
assert row['pid']==130966 and row['domain']=='225'
params=[]
for name in ['/tmp/launch_params_nhi0st46','/tmp/launch_params_avcp94rc','/tmp/launch_params_u35c1m3p']:
 p=Path(name);params.append(dict(path=name,mtime_epoch_s=p.stat().st_mtime,text=p.read_text()))
start=json.loads((R/'BATCH_STARTED.json').read_text())['wall_time']
assert row['create_time']<start-86400 and all(x['mtime_epoch_s']<start-86400 for x in params)
out=dict(status='HOLD_A2_R02_DOMAIN225_PREEXISTING_LIFECYCLE_MANAGER_COLLISION',evidence=row,launch_params=params,existed_before_batch_days=(start-row['create_time'])/86400,affected_role='O24G_A2_R02',same_namespace='/PioneerP3DX',potential_targets=['map_server','planner_server','controller_server','bt_navigator','behavior_server'],cause='Pre-run name-filter checked ros2/basic_sim/runtime_driver/gsl_actionserver/gmrf_wind, omitted lifecycle_manager. Domain225 incorrectly treated as vacant.',qualified_claim='Four real ROS episodes and RNG evidence remain recorded; A2 R02 isolation and task-performance qualification HOLD. No proof of intervention and no proof of no intervention.',correction='POST_RUN_CLEANUP initially called it current-owned leftover. Creation time and saved launch-file times show a historical orphan; that initial label is withdrawn. Files retained unchanged as audit history.',retry_policy='Frozen total_goal_cap4,technical_retry_cap0. No automatic fifth goal.',new_ROS=0,new_worlds=0)
(R/'DOMAIN_ISOLATION_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False))
