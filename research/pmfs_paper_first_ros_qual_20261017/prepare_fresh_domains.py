from pathlib import Path
import ast,json
R=Path(__file__).resolve().parent;p=json.loads((R/'RUN_PRECOMMIT_NEXT.json').read_text());old=p['roles'][0];rid='PF24_A2_T02';dst=R/'cases'/rid;dst.mkdir(exist_ok=False)
def change_domain(text,domain):
 return text.replace('ROS_DOMAIN_ID=226','ROS_DOMAIN_ID='+str(domain)).replace("ROS_DOMAIN_ID='226'","ROS_DOMAIN_ID='"+str(domain)+"'").replace('ROS_DOMAIN_ID226','ROS_DOMAIN_ID'+str(domain))
for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','CASE_META.json','AUTHOR_WALL_FILE_CADENCE.csv']:
 text=(R/'cases'/old['id']/name).read_text().replace(old['id'],rid);text=change_domain(text,227)
 if name=='CASE_META.json':v=json.loads(text);v['ROS_DOMAIN_ID']=227;text=json.dumps(v,indent=2)
 if name.endswith('.py'):ast.parse(text)
 (dst/name).write_text(text,encoding='utf-8',newline='\n')
role={**old,'id':rid,'guest_path':old['guest_path'].replace(old['id'],rid),'runtime_shared':old['runtime_shared'].replace(old['id'],rid),'domain':227}
b=p['roles'][1];bdir=R/'cases'/b['id']
for name in ['runtime_driver.py','RUN_SHELL.sh','CASE_META.json']:
 path=bdir/name;text=change_domain(path.read_text(),228)
 if name=='CASE_META.json':v=json.loads(text);v['ROS_DOMAIN_ID']=228;text=json.dumps(v,indent=2)
 if name.endswith('.py'):ast.parse(text)
 path.write_text(text,encoding='utf-8',newline='\n')
b={**b,'domain':228};p['roles']=[role,b];p['retained_attempts']=['PF24_A2_Q01','PF24_A2_T01'];p['cumulative_goals_before_this_plan']=1;p['technical_retry_used']=2
(R/'RUN_PRECOMMIT_FINAL.json').write_text(json.dumps(p,indent=2))
(R/'TECHNICAL_RETRY_AMENDMENT_02.json').write_text(json.dumps(dict(retained='PF24_A2_T01',native_goals_in_retained_trial=0,observation='Nav2 lifecycle change_state response timed out; map server never activated and no map was delivered. Same-domain rapid restart is a candidate explanation, not proven root cause.',adaptation='Use separate fresh ROS_DOMAIN_ID 227 for A2 and228 for B2; same physics, algorithm, parameters, GMRF and clock.',new_algorithm_code=False,new_physical_world=False,cumulative_native_goal_cap=4),indent=2))
print(json.dumps(dict(status='FRESH_DOMAINS_FROZEN',roles=p['roles'])))
