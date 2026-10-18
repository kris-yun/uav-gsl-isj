from pathlib import Path
import datetime,hashlib,json,os,psutil,shutil,time
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=json.loads((R/'PRECOMMIT.json').read_text())
deps=json.loads((R/'DEPENDENCY_LIVE_MANIFEST.json').read_text())
checks=[]
for row in deps['roots']:
 actual=sha(row['path']);assert actual==row['sha256']
 checks.append(dict(path=row['path'],sha256=actual))
for path,h in deps['libraries'].items():assert sha(path)==h,path
domains={str(x['domain'])for x in plan['roles']};owned=[]
for p in psutil.process_iter(['pid','cmdline']):
 try:
  if p.environ().get('ROS_DOMAIN_ID')in domains:owned.append(dict(pid=p.pid,domain=p.environ().get('ROS_DOMAIN_ID'),create_time=p.create_time(),command=p.info['cmdline']))
 except(psutil.NoSuchProcess,psutil.AccessDenied):pass
if owned:
 assert json.loads((R/'BATCH_COMPLETE.json').read_text())['recorded']==4
 # One lifecycle manager outlived its launch shutdown. Stop only this verified
 # owned process; no process-name-wide kill and no changes to any other domain.
 for row in owned:
  assert row['pid']==130966 and row['command'][0]=='/opt/ros/humble/lib/nav2_lifecycle_manager/lifecycle_manager',row
  proc=psutil.Process(row['pid']);assert proc.create_time()==row['create_time']and proc.environ().get('ROS_DOMAIN_ID')==row['domain']
  (R/'POST_RUN_CLEANUP_INITIAL.json').write_text(json.dumps(dict(owned=owned,previous_attempt='SIGINT then SIGTERM each timed out at5s; no episode rerun'),indent=2))
  proc.send_signal(2)
  try:proc.wait(timeout=5);row['shutdown']='SIGINT_EXIT'
  except psutil.TimeoutExpired:
   proc.terminate()
   try:proc.wait(timeout=5);row['shutdown']='SIGTERM_EXIT'
   except psutil.TimeoutExpired:
    row['status_after_SIGTERM']=proc.status()
    proc.kill()
    try:proc.wait(timeout=5);row['shutdown']='SIGKILL_EXIT'
    except psutil.TimeoutExpired:
     assert proc.status()==psutil.STATUS_ZOMBIE
     row['shutdown']='ZOMBIE_AWAITING_PARENT_REAP_NOT_EXECUTING'
 (R/'POST_RUN_CLEANUP.json').write_text(json.dumps(dict(initial_postcheck='FAIL_OWNED_LIFECYCLE_MANAGER_REMAINED_AFTER_BATCH',preserved=owned,scope='After all four results; only verified owned PID stopped. No episode rerun or scientific parameter change.'),indent=2))
remaining=[]
for p in psutil.process_iter(['pid']):
 try:
  if p.environ().get('ROS_DOMAIN_ID')in domains:remaining.append(p.pid)
 except(psutil.NoSuchProcess,psutil.AccessDenied):pass
assert not remaining,remaining
free=shutil.disk_usage('/home/zyc').free
assert free>plan['guest_free_floor_bytes']
B=R/'binaries';B.mkdir(exist_ok=True)
build=json.loads((R/'BUILD_RESULT.json').read_text())
shutil.copyfile(build['binary'],B/'gsl_actionserver_node')
assert sha(B/'gsl_actionserver_node')==build['binary_sha256']
result=dict(status='PASS_FROZEN_ELF_AND_ALL_RECORDED_LIBRARIES_NO_OWNED_ROS_LEFT',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),root_binaries=checks,shared_libraries_rechecked=len(deps['libraries']),owned_processes_after_cleanup=remaining,post_run_owned_cleanup_count=len(owned),guest_free_bytes=free,new_ROS_goals=0,new_forward_calls=0,new_worlds=0)
(R/'POST_RUN_GUEST_GATE.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
