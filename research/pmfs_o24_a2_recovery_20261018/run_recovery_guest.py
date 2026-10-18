from pathlib import Path
import datetime,hashlib,json,os,psutil,resource,shutil,signal,subprocess,time
from isolation_guard import inventory,require_vacant
R=Path(__file__).resolve().parent;plan=json.loads((R/'PRECOMMIT.json').read_text());role=plan['roles'][0];F=R/'cases'/role['id'];T=Path(role['guest_path'])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert len(plan['roles'])==plan['total_goal_cap']==1 and plan['technical_retry_cap']==0
assert not (R/'RECOVERY_STARTED.json').exists()and not T.exists()
assert sha('/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018/gsl_actionserver_node')==plan['binary_sha256']
deps=json.loads((R/'DEPENDENCY_LIVE_MANIFEST.json').read_text())
for row in deps['roots']:assert sha(row['path'])==row['sha256']
for p,h in deps['libraries'].items():assert sha(p)==h,p
for row in plan['source_files']:assert sha(R/'source_runtime'/row['path'])==row['sha256']
assert shutil.disk_usage('/home/zyc').free>plan['guest_free_floor_bytes']and shutil.disk_usage(R).free>plan['host_free_floor_bytes']
require_vacant(inventory(225,exclude={os.getpid()}),R/'DOMAIN_CONTROLLER_PRE_GATE.json')
assert json.loads((R/'DOMAIN_GRAPH_GATE.json').read_text())['status']=='PASS_DOMAIN_GRAPH_VACANT'
T.mkdir(parents=True)
for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','CASE_META.json','AUTHOR_WALL_FILE_CADENCE.csv']:shutil.copyfile(F/name,T/name)
start=time.monotonic();epoch=time.time();(R/'EXECUTION_STARTED.json').write_text(json.dumps(dict(wall_time=epoch,budget_s=900)))
(R/'RECOVERY_STARTED.json').write_text(json.dumps(dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_time=epoch,role=role,authorization=plan['user_authorization'],binary_sha256=plan['binary_sha256'])))
owners={};monitor=[];alien=[];before=resource.getrusage(resource.RUSAGE_CHILDREN)
with (F/'driver.log').open('wb')as log:
 proc=subprocess.Popen(['bash',str(T/'RUN_SHELL.sh')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 parent=psutil.Process(proc.pid)
 while proc.poll()is None:
  try:family=[parent]+parent.children(recursive=True)
  except psutil.NoSuchProcess:family=[]
  for p in family:
   try:owners[p.pid]=dict(pid=p.pid,create_time=p.create_time(),name=p.name(),command=p.cmdline())
   except(psutil.NoSuchProcess,psutil.AccessDenied):pass
  snap=inventory(225,exclude={os.getpid()});current=snap['matching_domain_processes']
  foreign=[x for x in current if x['pid']not in owners]
  if foreign:alien.extend(foreign)
  monitor.append(dict(wall_s=time.monotonic()-start,domain_processes=[dict(pid=x['pid'],create_time=x['create_time'],name=x['name'])for x in current],unowned=foreign))
  (R/'PROGRESS.json').write_text(json.dumps(dict(wall_s=time.monotonic()-start,pid=proc.pid,owned_pids=len(owners),unowned_domain_processes=foreign)))
  if foreign or time.monotonic()-start>520:
   os.killpg(proc.pid,signal.SIGINT)
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
   break
  time.sleep(.5)
after=resource.getrusage(resource.RUSAGE_CHILDREN)
cleanup=[]
for pid,row in owners.items():
 try:
  p=psutil.Process(pid)
  if p.create_time()!=row['create_time']:continue
  c=dict(**row,signals=[])
  for sig,wait in [(signal.SIGINT,2),(signal.SIGTERM,2),(signal.SIGKILL,2)]:
   if not p.is_running()or p.status()==psutil.STATUS_ZOMBIE:break
   p.send_signal(sig);c['signals'].append(int(sig))
   try:p.wait(timeout=wait)
   except psutil.TimeoutExpired:pass
  c['final_status']=p.status()if p.is_running()else 'gone';cleanup.append(c)
 except psutil.NoSuchProcess:pass
(R/'PROCESS_OWNERS_AND_MONITOR.json').write_text(json.dumps(dict(owners=list(owners.values()),monitor=monitor,cleanup=cleanup,unowned_domain_processes=alien),indent=2))
for name in ['RUN_STARTED.json','RUN_RESULT.json','RUNTIME_STATUS.json']:
 if (T/name).exists():shutil.copyfile(T/name,F/name)
result=json.loads((F/'RUN_RESULT.json').read_text())if (F/'RUN_RESULT.json').exists()else dict(result='NO_RESULT_RECEIVED')
post=inventory(225,exclude={os.getpid()});require_vacant(post,R/'DOMAIN_POST_RUN_PROCESS_GATE.json')
assert not alien,alien
assert sha('/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018/gsl_actionserver_node')==plan['binary_sha256']
out=dict(role=role,wall_s=time.monotonic()-start,child_cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,exit_code=proc.returncode,result=result,owned_process_count=len(owners),native_goal_cap=1,technical_retry=0,new_worlds=0,AIMMD=0,post_free_bytes=shutil.disk_usage('/home/zyc').free)
(R/'RECOVERY_COMPLETE.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out),flush=True)
