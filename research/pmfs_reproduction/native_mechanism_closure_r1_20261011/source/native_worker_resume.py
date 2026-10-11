"""Bounded serial native core calls on existing inputs; never a navigation goal."""
from pathlib import Path
import os,json,time,subprocess,signal,csv,hashlib,shutil
t=Path(__file__).resolve().parent
tasks=json.loads((t/'NATIVE_RESUME_TASKS.json').read_text());contract=json.loads((t/'CAMPAIGN_CONTRACT.json').read_text())
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',ROS_DOMAIN_ID='229',
 LD_LIBRARY_PATH=json.loads((t/'ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH'])
ledger=json.loads((t/'NATIVE_PRE_RESUME_LEDGER.json').read_text());ledger['status']='RUNNING';ledger['resumed_unix']=time.time()
lastprogress=0;lastresource=0
def save():(t/'NATIVE_EXECUTION_LEDGER.json').write_text(json.dumps(ledger,indent=2))
def heartbeat(task,pid=None,force=False):
 global lastprogress
 if not force and time.monotonic()-lastprogress<30:return
 lastprogress=time.monotonic();a=dict(task=task,pid=pid,done=len(ledger['records']),total=len(tasks),forward_calls=ledger['native_2D_forward_calls'],elapsed_s=time.time()-ledger['scientific_start_unix'])
 (t/'NATIVE_PROGRESS.json').write_text(json.dumps(a));print(json.dumps(a),flush=True)
def stop(p):
 for s in [signal.SIGINT,signal.SIGTERM,signal.SIGKILL]:
  try:os.killpg(p.pid,s);p.wait(timeout=3);return
  except subprocess.TimeoutExpired:pass
  except ProcessLookupError:return
save()
try:
 for task in tasks:
  mode=task['mode'];out=t/'native_results'/task['id'];out.parent.mkdir(exist_ok=True);assert not out.exists()
  cmd=[str(t/'native_entry'),mode,task['input'],task['payload'],str(out)]
  log=t/'native_results'/(task['id']+'.log');start=time.monotonic();peak=0;reason=None
  heartbeat(task['id'],force=True)
  with log.open('w') as f:
   p=subprocess.Popen(cmd,env=env,stdout=f,stderr=f,start_new_session=True)
   while p.poll() is None:
    rss=0
    for item in Path('/proc').iterdir():
     if not item.name.isdigit():continue
     try:
      if os.getpgid(int(item.name))!=p.pid:continue
      for row in (item/'status').read_text().splitlines():
       if row.startswith('VmRSS:'):rss+=int(row.split()[1])*1024
     except (OSError,ProcessLookupError):pass
    peak=max(peak,rss)
    elapsed=time.monotonic()-start
    if rss>1610612736:reason='RSS_CAP'
    if elapsed>180:reason='PER_OBSERVATION180S_CAP'
    if ledger['offline_wall_s']+elapsed>1800:reason='OFFLINE1800S_CAP'
    if time.time()-contract['entry_unix']>9000:reason='GLOBAL9000S_CAP'
    if time.monotonic()-lastresource>=60:
     lastresource=time.monotonic()
     size=sum(q.stat().st_size for q in Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011').rglob('*') if q.is_file())+315529864
     if size>6442450944:reason='NEW_DISK_CAP'
     if shutil.disk_usage(t).free<4294967296:reason='ROOT4GIB_RESERVE'
     with (t/'RESOURCE_CHECKS.jsonl').open('a') as rc:rc.write(json.dumps(dict(task=task['id'],elapsed=elapsed,RSS=rss,bytes=size,root_free=shutil.disk_usage(t).free,physical_calls=0))+'\n')
    if reason:stop(p);break
    heartbeat(task['id'],p.pid);time.sleep(.1)
   code=p.wait()
  calls=sum(sum(1 for _ in csv.DictReader(q.open())) for q in out.rglob('candidates.csv')) if out.exists() else 0
  ledger['native_2D_forward_calls']+=calls;ledger['offline_wall_s']+=time.monotonic()-start
  rec=dict(id=task['id'],mode=mode,exitcode=code,wall_s=time.monotonic()-start,peak_RSS_bytes=peak,forward_calls=calls,resource_stop=reason)
  if code:rec['last_log']=log.read_text(errors='replace')[-2500:]
  ledger['records'].append(rec);save();heartbeat(task['id'],force=True)
  if reason:ledger['status']='BUDGET_STOP';break
  if code:ledger['status']='TECHNICAL_FAULT_STOP_DEPENDENT_NATIVE_TASKS';break
  if ledger['native_2D_forward_calls']>24000:ledger['status']='FORWARD_BUDGET_STOP';break
 else:ledger['status']='PASS_ALL_NATIVE_TASKS_COMPLETED'
except Exception as e:ledger['status']='TECHNICAL_FAULT_STOP';ledger['error']=repr(e)
finally:save();heartbeat(ledger['status'],force=True)
raise SystemExit(0 if ledger['status'].startswith('PASS') else 1)

