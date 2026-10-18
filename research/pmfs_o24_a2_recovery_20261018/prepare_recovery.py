from pathlib import Path
import ast,difflib,hashlib,json,shutil
P=Path(__file__).resolve().parent;OLD=P/'PMFS_O24_ROS_QUAL_20261018';R=P/'PMFS_O24_A2_RECOVERY_20261018'
assert not R.exists();R.mkdir()
role='O24G_A2_ISO_R03';oldrole='O24G_A2_R02';domain=228
shared='/mnt/hgfs/workspace/'+R.name;guest='/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018/cases/'+role
F=R/'cases'/role;F.mkdir(parents=True);(F/'runtime').mkdir()
for d in ['source_runtime','p24_reference']:
 src=OLD/d
 if d=='p24_reference':src=Path(r'D:\ZYC\UAV\.codex\worktrees\pmfs-paper-eq6-20261017\A-gas\research\pmfs_o24_ros_qual_20261018\p24_reference')
 shutil.copytree(src,R/d)
for name in ['BUILD_RESULT.json','RNG_RECORDING_QUALIFICATION.json','PHASE1_DIAGNOSTIC_SOURCE_PAIRS.json','analyze.py','native_readout_check.cpp','verify_readout_guest.py','rng_stream_replay.cpp','validate_rng_guest.py','DEPENDENCY_LIVE_MANIFEST.json']:
 shutil.copyfile(OLD/name,R/name)
meta=json.loads((OLD/'cases'/oldrole/'CASE_META.json').read_text())
meta=json.loads(json.dumps(meta).replace('/mnt/hgfs/workspace/'+OLD.name+'/cases/'+oldrole,shared+'/cases/'+role).replace('/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018/cases/'+oldrole,guest))
meta['audit_setting']['id']=role;meta['ROS_DOMAIN_ID']=domain;meta['frozen_repeat']=3
meta['replacement_for']=oldrole;meta['execution_policy']='One user-approved isolation recovery; all readable process environments plus graph vacancy; no scientific retry.'
(F/'CASE_META.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
patches=[]
for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','AUTHOR_WALL_FILE_CADENCE.csv']:
 before=(OLD/'cases'/oldrole/name).read_text(encoding='utf-8')
 after=before.replace('/mnt/hgfs/workspace/'+OLD.name,shared).replace('/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018/cases/'+oldrole,guest).replace(oldrole,role)
 after=after.replace("ROS_DOMAIN_ID='225'","ROS_DOMAIN_ID='228'").replace('ROS_DOMAIN_ID=225','ROS_DOMAIN_ID=228').replace('ROS_DOMAIN_ID227','ROS_DOMAIN_ID228')
 if name=='RUN_SHELL.sh':after=after.replace('exec python3 -B ',"export ROS_LOG_DIR="+shared+'/cases/'+role+'/runtime/ros_logs\nexport TMPDIR='+shared+'/cases/'+role+'/runtime/tmp\nexec python3 -B ')
 if name=='runtime_driver.py':
  start=after.index('# Fail before creating DDS nodes/services')
  end=after.index('rclpy.init();',start)
  after=after[:start]+"# Reject all matching-domain processes, without executable-name filters.\nimport sys\nsys.path.insert(0,'"+shared+"')\nfrom isolation_guard import inventory, require_vacant\nrequire_vacant(inventory(228,exclude={os.getpid()}),R/'IMMEDIATE_PRE_DDS_GATE.json')\n\n"+after[end:]
  after=after.replace("+2400.0)","+900.0)")
  s=after.index('def stop_all():');e=after.index('\nstatus=dict(',s)
  after=after[:s]+'''def stop_all():
 rows=[]
 for name,p,f in reversed(processes):
  row=dict(name=name,pid=p.pid)
  for sig,wait in [(signal.SIGINT,5),(signal.SIGTERM,3),(signal.SIGKILL,3)]:
   if p.poll()is not None:break
   try:os.killpg(p.pid,sig)
   except ProcessLookupError:break
   try:p.wait(timeout=wait)
   except subprocess.TimeoutExpired:continue
  row['returncode']=p.poll();rows.append(row);f.close()
 (R/'DRIVER_SHUTDOWN.json').write_text(json.dumps(rows,indent=2))
''' + after[e:]
  # Native executable checks belong to this isolated domain only.
  after=after.replace("if exe==expected_binary.resolve():","if exe==expected_binary.resolve() and b'ROS_DOMAIN_ID=228' in (proc/'environ').read_bytes().split(b'\\0'):")
 if name.endswith('.py'):ast.parse(after)
 (F/name).write_text(after,encoding='utf-8',newline='\n')
 if after!=before:patches.append(dict(file=name,diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='old/'+name,tofile='recovery/'+name))))
for d in ['ros_logs','tmp']:(F/'runtime'/d).mkdir()
(R/'EXECUTION_ADAPTER_DIFFS.json').write_text(json.dumps(patches,ensure_ascii=False,indent=2),encoding='utf-8')
oldplan=json.loads((OLD/'PRECOMMIT.json').read_text());plan=dict(user_authorization='2026-10-18 user approved exactly one A2 recovery after domain cleanup, same scientific parameters, keep all old evidence, no AIMMD',roles=[dict(id=role,case='A2',repeat=3,domain=domain,guest_path=guest,runtime_shared=shared+'/cases/'+role+'/runtime')],primary_goals=1,total_goal_cap=1,technical_retry_cap=0,total_batch_wall_s=900,max_goal_wall_s=420,guest_free_floor_bytes=5*1024**3,host_free_floor_bytes=2*1024**3,parameters=oldplan['parameters'],expected_parameters=meta['expected_parameters'],source_files=oldplan['source_files'],binary_sha256=meta['actual_binary_sha256'],new_worlds=0,AIMMD=0,RNG=oldplan['RNG'])
assert meta['expected_parameters']==json.loads((OLD/'cases'/oldrole/'CASE_META.json').read_text())['expected_parameters']
for x in plan['source_files']:assert hashlib.sha256((R/'source_runtime'/x['path']).read_bytes()).hexdigest()==x['sha256']
(R/'PRECOMMIT.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(__file__,R/'prepare_recovery.py')
print(json.dumps(dict(root=str(R),role=role,domain=domain,parameters_unchanged=True,ELF_unchanged=True)))
