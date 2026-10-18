from pathlib import Path
import ast,csv,difflib,hashlib,json,re,shutil,time,subprocess
R=Path(__file__).resolve().parent;PROJECT=R.parents[1];OLD=PROJECT/'workspace/PMFS_OFFICIAL_REPRO_AUDIT_20261016'
old_guest='/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016';guest='/home/zyc/ros2_ws/pmfs_paper_first_qual_20261017';shared='/mnt/hgfs/workspace/PMFS_PAPER_FIRST_ROS_QUAL_20261017'
build=json.loads((R/'BUILD_RESULT.json').read_text());assert build['status']=='PASS_COMPLETE_SEPTEMBER_BASELINE_BUILD'and build['attempt']=='attempt2_rectangular'
assert json.loads((R/'RECTANGULAR_PROBE_RESULT.json').read_text())['status']=='PASS'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
expected=dict(use_sim_time=False,useWindGroundTruth=False,sourceDiscriminationPower=1.,convergence_thr=1.,maxSearchTime=300.,stop_and_measure_time=.4,confidenceMeasurementWeight=1.,confidenceSigmaSpatial=1.,kernelSigma=1.5,kernelStretchConstant=1.5,hitPriorProbability=.3,scale=25,maxUpdatesPerStop=5,stepsSourceUpdate=3,refineFraction=.1,maxRegionSize=5,deltaTime=.1,noiseSTDev=.5,iterationsToRecord=200,maxWarmupIterations=500)
roles=[]
for case in ['A2','B2']:
 oldid=f'P24_{case}_WALL5_VALID_V2_R01';rid=f'PF24_{case}_Q01';src=OLD/'runs'/oldid;dst=R/'cases'/rid;dst.mkdir(parents=True,exist_ok=True)
 assert not (dst/'RUN_STARTED.json').exists() and not (R/'RUN_PRECOMMIT.json').exists()
 oldT=old_guest+'/cases/'+oldid;T=guest+'/cases/'+rid;runtime=shared+'/cases/'+rid+'/runtime'
 meta=json.loads((src/'CASE_META.json').read_text());meta.update(audit_profile='PAPER_FIRST_SEP2024_EQ6_RECTANGULAR_DISCLOSED_ADAPTATIONS',baseline_source_commit=build['source_commit'],actual_binary_sha256=build['binary_sha256'],clock_policy='Native pinned public clock conventions retained and measured separately; not confirmed original experimental clock',ROS_DOMAIN_ID=226,declared_not_original_author_gas_realization=True)
 meta['audit_setting'].update(id=rid,profile=meta['audit_profile'],ground_truth_wind=False,convergence_variance_m2=1.)
 meta['player']['r7_frame_time_csv']=T+'/AUTHOR_WALL_FILE_CADENCE.csv';meta['player']['r7_clock_trace_path']=runtime+'/physical_clock_trace.csv'
 meta['expected_parameters']=expected
 put(dst/'CASE_META.json',meta)
 for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','AUTHOR_WALL_FILE_CADENCE.csv']:
  if (src/name).exists():text=(src/name).read_text()
  else:
   assert name=='AUTHOR_WALL_FILE_CADENCE.csv'
   text=subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','zyc@192.168.111.128','cat '+oldT+'/'+name],timeout=15).decode('utf-8')
  before=text
  text=text.replace(oldT+'/runtime',runtime).replace(oldT,T).replace(str(src/'runtime'),runtime).replace(oldid,rid)
  text=text.replace('ROS_DOMAIN_ID=229','ROS_DOMAIN_ID=226').replace("ROS_DOMAIN_ID='229'","ROS_DOMAIN_ID='226'").replace('ROS_DOMAIN_ID229','ROS_DOMAIN_ID226')
  text=text.replace(old_guest+'/pmfs_observation_validity_node_v2',build['binary'])
  if name=='N1_launch.py':
   text=text.replace('{"maxSearchTime": 1000000.0}','{"maxSearchTime": 300.0}')
   needle='{"sourceDiscriminationPower": parse_substitution("$(var sourceDiscriminationPower)")}';assert text.count(needle)==1;text=text.replace(needle,'{"sourceDiscriminationPower": 1.0}')
   # Keep literal player frame/file identities; only the two owned output paths change.
  elif name=='runtime_driver.py':
   text=text.replace("T=Path('"+T+"');R=Path('"+runtime+"')","T=Path('"+T+"');R=Path('"+runtime+"')")
   text=text.replace("'physical_qualification='", "'physical_qualification='")
   old_deadline="deadline=datetime.datetime.fromisoformat(json.loads((Path('/mnt/hgfs/workspace/PMFS_OFFICIAL_REPRO_AUDIT_20261016')/'BATCH_STARTED.json').read_text())['UTC']).timestamp()+10800"
   assert text.count(old_deadline)==1;text=text.replace(old_deadline,'deadline=time.time()+420.0')
   text=text.replace("shutil.disk_usage('/mnt/hgfs/workspace').free<10*1024**3","shutil.disk_usage('/mnt/hgfs/workspace').free<2*1024**3")
   text=text.replace('maxSearchTime=1000000.,max_goal_wall_s=None','maxSearchTime=300.,max_goal_wall_s=420.')
   # Parameter capture occurs after native lazy declaration, before any accepted interpretation of the run.
   needle="   snapshot_parameters('/PioneerP3DX/GSL','resolved_GSL_parameters.json')\n   dump_started=True";assert text.count(needle)==1
   text=text.replace(needle,"""   snapshot_parameters('/PioneerP3DX/GSL','resolved_GSL_parameters.json')
   pp=json.loads((R/'resolved_GSL_parameters.json').read_text())
   values={}
   for k,v in zip(pp['names'],pp['values']):
    values[k]=v['bool_value'] if v['type']==1 else v['integer_value'] if v['type']==2 else v['double_value'] if v['type']==3 else v['string_value']
   for k,v in META['expected_parameters'].items():
    assert k in values and values[k]==v,('RESOLVED_BASELINE_PARAMETER_MISMATCH',k,values.get(k),v)
   (R/'BASELINE_PARAMETER_GATE.json').write_text(json.dumps(dict(status='PASS_ACTUAL_NODE_PARAMETER_VALUES',checked=META['expected_parameters']),indent=2))
   dump_started=True""")
   needle=" (R/'PREFLIGHT.json').write_text(json.dumps(pre,indent=2));status['preflight']='PASS';save_status()";assert text.count(needle)==1
   text=text.replace(needle,""" navmap=latest['/PioneerP3DX/map'];rawmap=bytes((int(v)&255)for v in navmap.data)
 (R/'navigation_map.s8').write_bytes(rawmap)
 (R/'NAVIGATION_MAP_METADATA.json').write_text(json.dumps(dict(width=navmap.info.width,height=navmap.info.height,resolution=navmap.info.resolution,origin_x=navmap.info.origin.position.x,origin_y=navmap.info.origin.position.y,occupancy_sha256=__import__('hashlib').sha256(rawmap).hexdigest()),indent=2))
"""+needle)
   # All new process identities are checked against the new baseline binary.
   assert build['binary']in text and 'pmfs_observation_validity_node_v2'not in text
  elif name=='RUN_SHELL.sh':
   text=text.replace('exec python3 -B '+T+'/runtime_driver.py','export AMENT_PREFIX_PATH="'+guest+'/install:${AMENT_PREFIX_PATH}"\nexec python3 -B '+T+'/runtime_driver.py')
  (dst/name).write_text(text,encoding='utf-8',newline='\n')
  if name.endswith('.py'):ast.parse(text)
  if name!='AUTHOR_WALL_FILE_CADENCE.csv':(dst/(name+'.adaptation.patch')).write_text(''.join(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile='previous_qualified_runtime/'+name,tofile='paper_first_Sep24/'+name)),encoding='utf-8')
 roles.append(dict(id=rid,case=case,guest_path=T,runtime_shared=runtime,domain=226,goal_limit=1,max_wall_s=420))
put(R/'RUN_PRECOMMIT.json',dict(status='FROZEN_BEFORE_A2_B2_NEW_GOALS',roles=roles,primary_goals=2,technical_retry_cap=2,total_goal_cap=4,retry_condition='Infrastructure or qualification failure only. Native timeout/nondeclaration is retained, not retried to seek a positive result.',native_time_limit_s=300,limit_source='Pinned GitHub launch, NOT claimed a universal paper PMFS cutoff',clock_profile='Public native5x robot clock/wall PMFS/player-wall cadence',parameters=expected,no_new_gas_worlds=True,no_AIMMD=True))
print(json.dumps(dict(status='TWO_PRIMARY_RUNS_PREPARED',roles=roles)))
