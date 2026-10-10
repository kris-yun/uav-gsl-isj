from pathlib import Path
import subprocess,json,os,signal,time,shutil,traceback
t=Path(__file__).resolve().parent;start=time.monotonic();reason=None
assert t.resolve()==Path('/home/zyc/pmfs_b4_official_terminal_completion_20261009')
assert not (t/'RUNTIME_GUARD_STARTED.json').exists() and not (t/'RUN_STARTED.json').exists()
with (t/'RUNTIME_GUARD_STARTED.json').open('x') as f:json.dump({'executions':1,'start_monotonic':start,'wall_time':time.time()},f)
result={'replacement_goal_budget':1,'new_generation_executions':0,'resource_stop_reason':None};p=None;terminal_seen=None
def read_json(path):
 try:return json.loads(path.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return None
def stop_group(pid):
 for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGKILL]:
  try:os.killpg(pid,sig)
  except ProcessLookupError:return
  time.sleep(.2)
try:
 with (t/'driver.stdout').open('w') as f,(t/'driver.stderr').open('w') as e:
  p=subprocess.Popen(['bash',str(t/'RUN_SHELL.sh')],stdout=f,stderr=e,start_new_session=True);result['driver_pid']=p.pid
  while p.poll() is None:
   now=time.monotonic();run=read_json(t/'RUN_STARTED.json');status=read_json(t/'RUNTIME_STATUS.json') or {}
   if status.get('result') is not None and terminal_seen is None:terminal_seen=now
   memory=next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
   total=sum(q.stat().st_size for q in (t/'runtime').rglob('*') if q.is_file())
   if run and terminal_seen is None and now-run['guard_start_monotonic']>345:reason='NATIVE_GOAL_WALL_LIMIT_345S'
   elif terminal_seen is not None and now-terminal_seen>25:reason='POST_TERMINAL_CLEANUP_WALL_LIMIT_25S'
   elif now-start>445:reason='OVERALL_NATIVE_DRIVER_WALL_LIMIT_445S'
   elif total>1_000_000_000:reason='RUNTIME_OUTPUT_LIMIT_1GB'
   elif shutil.disk_usage(t).free<1_000_000_000:reason='FREE_DISK_BELOW_1GB'
   elif memory<250_000_000:reason='MEMORY_AVAILABLE_BELOW_250MB'
   if reason:
    result['resource_stop_reason']=reason;(t/'RESOURCE_STOP.json').write_text(json.dumps({'reason':reason,'monotonic_wall':now,'terminal_already_recorded':terminal_seen is not None}))
    for child in status.get('processes',[]):
     if child.get('returncode') is None:stop_group(child['pid'])
    stop_group(p.pid);break
   time.sleep(.25)
  result['driver_returncode']=p.wait(timeout=4)
except Exception as e:result.update(error=str(e),traceback=traceback.format_exc())
finally:
 result['total_wall_seconds']=time.monotonic()-start
 (t/'RUNTIME_GUARD_RESULT.json').write_text(json.dumps(result,indent=2))
