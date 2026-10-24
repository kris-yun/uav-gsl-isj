"""One preregistered native goal, with process/graph/isolation evidence."""
from pathlib import Path
import datetime,hashlib,json,os,psutil,resource,shutil,signal,subprocess,time,sys
R=Path(__file__).resolve().parent;batch=json.loads((R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json').read_text());role=next(x for x in batch['roles']if x['id']==sys.argv[1]);plan=dict(batch,role=role['id'],guest_case=role['guest_case']);sys.path.insert(0,str(R));from isolation_guard import inventory,require_vacant
from process_ownership_R4 import adopt_new_children
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
override=json.loads((R/'ROLE_EXECUTION_OVERRIDES_R6.json').read_text()).get(plan['role'],{});C=Path(override.get('shared_case',str(R/'cases'/plan['role'])));V=Path(override.get('guest_case',plan['guest_case']));assert not V.exists()and not(C/'RUN_STARTED.json').exists();assert sha(plan['binary_path'])==plan['binary_sha256']
assert all(sha(Path(plan['source_snapshot_guest'])/x['path'])==x['sha256']for x in plan['source_files'])
assert shutil.disk_usage('/home/zyc').free>1024**3 and shutil.disk_usage(R).free>768*1024**2
put(C/'RESOURCE_PREFLIGHT.json',dict(host_free=shutil.disk_usage(R).free,guest_free=shutil.disk_usage('/home/zyc').free,retained_historical_duplicate_cleanup_receipt='/mnt/hgfs/workspace/../RESEARCH_DATA_REGISTRY_20261024/99_SAFE_CLEANUP_RECEIPTS/SAFE_CLEANUP_ACTION_RECEIPTS.json',new_worlds=0))
def graph(phase):
 D=C/phase;D.mkdir();s=(C/'RUN_SHELL.sh').read_text();target='exec python3 -B '+str(C/'runtime_driver.py');assert target in s;s=s.replace(target,'exec python3 -B '+str(R/'graph_probe.py')+' '+str(D));p=C/(phase+'.sh');p.write_text(s);q=subprocess.run(['bash',str(p)],capture_output=True,timeout=25);(D/'stdout').write_bytes(q.stdout);(D/'stderr').write_bytes(q.stderr);assert q.returncode==0,q.stderr.decode(errors='replace')
require_vacant(inventory(228,exclude={os.getpid()}),C/'PRE_DOMAIN_PROCESS_GATE.json');graph('PRE_GRAPH')
V.mkdir(parents=True)
for n in ['CASE_META.json','N1_launch.py','runtime_driver.py','RUN_SHELL.sh','PHYSICAL_FRAME_TIME.csv']:shutil.copyfile(C/n,V/n)
put(C/'EXECUTION_STARTED.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_time=time.time(),goal_cap=1,preregistration_sha256=sha(R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json')))
t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);owners={};monitor=[];forced=None;proc=None
with (C/'driver.log').open('wb')as f:
 proc=subprocess.Popen(['bash',str(V/'RUN_SHELL.sh')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True);parent=psutil.Process(proc.pid)
 while proc.poll()is None:
  try:family=[parent]+parent.children(recursive=True)
  except psutil.NoSuchProcess:family=[]
  for p in family:
   try:owners[p.pid]=dict(pid=p.pid,create_time=p.create_time(),name=p.name(),command=p.cmdline())
   except(psutil.NoSuchProcess,psutil.AccessDenied):pass
  snap=inventory(228,exclude={os.getpid()});ownership_proofs=adopt_new_children(snap['matching_domain_processes'],owners);foreign=[x for x in snap['matching_domain_processes']if x['pid']not in owners or x['create_time']!=owners[x['pid']]['create_time']];unknown=[]
  for x in snap['blocking_unreadable']:
   try:
    if x['pid']not in owners or psutil.Process(x['pid']).create_time()!=owners[x['pid']]['create_time']:unknown.append(x)
   except psutil.NoSuchProcess:pass
  monitor.append(dict(wall_s=time.monotonic()-t,domain_pids=[x['pid']for x in snap['matching_domain_processes']],foreign=foreign,unknown=unknown,ownership_proofs=ownership_proofs))
  put(C/'PROGRESS.json',dict(stage='NATIVE_'+role['case']+'_IN_PROGRESS',elapsed_wall_s=time.monotonic()-t,domain=228,owned_pids=len(owners),host_free=shutil.disk_usage(R).free,guest_free=shutil.disk_usage('/home/zyc').free))
  if foreign or unknown or time.monotonic()-t>1250:
   forced='ISOLATION_FAILURE'if foreign or unknown else'RESOURCE_WATCHDOG_CENSOR';os.killpg(proc.pid,signal.SIGINT)
   try:proc.wait(timeout=15)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
   break
  time.sleep(1)
cleanup=[]
for pid,x in owners.items():
 try:
  p=psutil.Process(pid)
  if p.create_time()!=x['create_time']:continue
  if not p.is_running()or p.status()==psutil.STATUS_ZOMBIE:continue
  row=dict(pid=pid,signals=[])
  for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGKILL]:
   if not p.is_running()or p.status()==psutil.STATUS_ZOMBIE:break
   p.send_signal(sig);row['signals'].append(int(sig))
   try:p.wait(timeout=2)
   except psutil.TimeoutExpired:pass
  cleanup.append(row)
 except psutil.NoSuchProcess:pass
put(C/'PROCESS_OWNERS_AND_MONITOR.json',dict(owners=list(owners.values()),monitor=monitor,cleanup=cleanup,forced=forced))
for n in ['RUN_STARTED.json','RUN_RESULT.json','RUNTIME_STATUS.json']:
 if (V/n).exists():shutil.copyfile(V/n,C/n)
result=json.loads((C/'RUN_RESULT.json').read_text())if(C/'RUN_RESULT.json').exists()else dict(result='NO_RESULT_RECEIVED')
after=resource.getrusage(resource.RUSAGE_CHILDREN);require_vacant(inventory(228,exclude={os.getpid()}),C/'POST_DOMAIN_PROCESS_GATE.json');graph('POST_GRAPH')
out=dict(status='ONE_PREREGISTERED_ATTEMPT_COMPLETE',result=result,forced=forced,wall_s=time.monotonic()-t,child_CPU_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,binary_unchanged=sha(plan['binary_path'])==plan['binary_sha256'],host_free=shutil.disk_usage(R).free,guest_free=shutil.disk_usage('/home/zyc').free,new_gas_worlds=0)
put(C/'EXECUTION_COMPLETE.json',out);print(json.dumps(out,ensure_ascii=False,indent=2))
