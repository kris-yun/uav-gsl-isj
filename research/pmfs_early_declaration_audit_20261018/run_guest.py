from pathlib import Path
import hashlib,json,os,psutil,shutil,signal,subprocess,time,sys
R=Path('/mnt/hgfs/workspace/PMFS_EARLY_DECLARATION_AUDIT_20261018')
plan=json.loads((R/'PRECOMMIT.json').read_text());build=json.loads((R/'BUILD_RESULT.json').read_text())
assert hashlib.sha256(Path(build['binary']).read_bytes()).hexdigest()==build['binary_sha256']
assert not (R/'BATCH_STARTED.json').exists()
start=time.monotonic();(R/'BATCH_STARTED.json').write_text(json.dumps(dict(wall_time=time.time(),plan_sha256=hashlib.sha256((R/'PRECOMMIT.json').read_bytes()).hexdigest(),binary=build)))
receipts=[]
for role in plan['roles']:
 assert time.monotonic()-start<plan['total_batch_wall_s']
 assert shutil.disk_usage('/home/zyc').free>plan['guest_free_floor_bytes'] and shutil.disk_usage(R).free>plan['host_free_floor_bytes']
 for p in psutil.process_iter(['pid','cmdline']):
  try:
   if p.pid!=os.getpid() and p.environ().get('ROS_DOMAIN_ID')==str(role['domain']) and any(x in ' '.join(p.info['cmdline']or[])for x in ['ros2','basic_sim','runtime_driver','gsl_actionserver','gmrf_wind']):raise RuntimeError('Domain occupied:'+str(p.pid))
  except(psutil.NoSuchProcess,psutil.AccessDenied):pass
 F=R/'cases'/role['id'];T=Path(role['guest_path']);assert not T.exists();T.mkdir(parents=True)
 Path(role['runtime_shared']).mkdir()
 for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','CASE_META.json','AUTHOR_WALL_FILE_CADENCE.csv']:shutil.copyfile(F/name,T/name)
 t=time.monotonic()
 with (F/'driver.log').open('wb')as f:
  proc=subprocess.Popen(['bash',str(T/'RUN_SHELL.sh')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  while proc.poll()is None:
   (R/'PROGRESS.json').write_text(json.dumps(dict(active=role,role_wall_s=time.monotonic()-t,batch_wall_s=time.monotonic()-start,completed=receipts),indent=2))
   if time.monotonic()-t>520:
    os.killpg(proc.pid,signal.SIGINT);proc.wait(timeout=25);break
   time.sleep(2)
 for name in ['RUN_STARTED.json','RUN_RESULT.json','RUNTIME_STATUS.json']:
  if (T/name).exists():shutil.copyfile(T/name,F/name)
 result=json.loads((T/'RUN_RESULT.json').read_text())if (T/'RUN_RESULT.json').exists()else dict(result='NO_RESULT_RECEIVED')
 row=dict(**role,wall_s=time.monotonic()-t,exit_code=proc.returncode,result=result);receipts.append(row)
 (R/'RUN_RESULTS.json').write_text(json.dumps(receipts,indent=2))
 print(json.dumps(dict(id=role['id'],wall_s=row['wall_s'],result=result.get('result'),error=result.get('error'))),flush=True)
 if result.get('result')!='NATIVE_ACTION_RETURNED':break
(R/'BATCH_COMPLETE.json').write_text(json.dumps(dict(recorded=len(receipts),requested=len(plan['roles']),rows=receipts,wall_s=time.monotonic()-start),indent=2))
