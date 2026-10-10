from pathlib import Path
import subprocess,json,os,signal,time,shutil,traceback
t=Path(__file__).resolve().parent;start=time.time();reason=None
assert t.resolve()==Path('/home/zyc/pmfs_b4_native_validation_20261009')
assert not (t/'RUNTIME_GUARD_STARTED.json').exists() and not (t/'RUN_STARTED.json').exists()
(t/'RUNTIME_GUARD_STARTED.json').write_text(json.dumps({'executions':1,'wall_time':start}))
result={'native_goal_budget':1,'E3_runs':0,'B4_runs_budget':1,'resource_stop_reason':None};p=None
def stop_explicit_group(pid):
 for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGKILL]:
  try:os.killpg(pid,sig)
  except ProcessLookupError:return
  time.sleep(.2)
try:
 with (t/'driver.stdout').open('w') as f,(t/'driver.stderr').open('w') as e:
  p=subprocess.Popen(['bash',str(t/'RUN_SHELL.sh')],stdout=f,stderr=e,start_new_session=True);result['driver_pid']=p.pid
  while p.poll() is None:
   run=json.loads((t/'RUN_STARTED.json').read_text()) if (t/'RUN_STARTED.json').exists() else None
   memory=next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
   total=sum(q.stat().st_size for q in (t/'runtime').rglob('*') if q.is_file())
   if run and time.time()-run['wall_time']>345:reason='NATIVE_GOAL_WALL_LIMIT_345S'
   elif time.time()-start>445:reason='OVERALL_NATIVE_DRIVER_WALL_LIMIT_445S'
   elif total>1_000_000_000:reason='RUNTIME_OUTPUT_LIMIT_1GB'
   elif shutil.disk_usage(t).free<1_000_000_000:reason='FREE_DISK_BELOW_1GB'
   elif memory<250_000_000:reason='MEMORY_AVAILABLE_BELOW_250MB'
   if reason:
    result['resource_stop_reason']=reason
    (t/'RESOURCE_STOP.json').write_text(json.dumps({'reason':reason,'wall_time':time.time(),'native_goal_budget':1}))
    status=json.loads((t/'RUNTIME_STATUS.json').read_text()) if (t/'RUNTIME_STATUS.json').exists() else {}
    for child in status.get('processes',[]):
     if child.get('returncode') is None:stop_explicit_group(child['pid'])
    stop_explicit_group(p.pid);break
   time.sleep(.25)
  result['driver_returncode']=p.wait(timeout=4)
except Exception as e:result.update(error=str(e),traceback=traceback.format_exc())
finally:
 result['total_wall_seconds']=time.time()-start
 (t/'RUNTIME_GUARD_RESULT.json').write_text(json.dumps(result,indent=2))
