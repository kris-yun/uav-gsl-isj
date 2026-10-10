from pathlib import Path
import subprocess,time,json,sys,os,signal,shutil,traceback
t=Path(__file__).resolve().parent;stage=sys.argv[1]
assert stage in ['PREPROCESS','GENERATION']
marker=t/(stage+'_STARTED.json');assert not marker.exists()
assert t.resolve()==Path('/home/zyc/pmfs_b4_native_validation_20261009')
start=time.time();marker.write_text(json.dumps(dict(stage=stage,executions=1,start_wall_time=start,one_case='B4')))
script='preprocess.sh' if stage=='PREPROCESS' else 'generate_once.sh';limit=900 if stage=='PREPROCESS' else 1200
resultfile='PREPROCESSING_RESULT.json' if stage=='PREPROCESS' else 'GENERATION_RESULT.json'
result={'stage':stage,'preprocessing_executions':1 if stage=='PREPROCESS' else 0,'generation_executions':1 if stage=='GENERATION' else 0,'resource_stop_reason':None};peak=0;p=None
try:
 with (t/('preprocessing.log' if stage=='PREPROCESS' else 'generation.log')).open('w') as f:
  p=subprocess.Popen(['bash',str(t/script)],stdout=f,stderr=f,start_new_session=True);result['process_group_pid']=p.pid
  while p.poll() is None:
   size=sum(q.stat().st_size for q in t.rglob('*') if q.is_file());peak=max(peak,size)
   memory=next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
   reason=('WALL_TIME_LIMIT' if time.time()-start>limit else 'OUTPUT_LIMIT_1GB' if size>1_000_000_000 else 'FREE_DISK_BELOW_1GB' if shutil.disk_usage(t).free<1_000_000_000 else 'MEMORY_AVAILABLE_BELOW_250MB' if memory<250_000_000 else None)
   if reason:
    result['resource_stop_reason']=reason
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGKILL]:
     try:os.killpg(p.pid,sig);p.wait(timeout=3);break
     except subprocess.TimeoutExpired:continue
     except ProcessLookupError:break
    break
   time.sleep(.5)
  result['exit_code']=p.wait(timeout=3)
except Exception as e:
 result.update(error=str(e),traceback=traceback.format_exc(),exit_code=None)
 if p is not None and p.poll() is None:
  try:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
  except ProcessLookupError:pass
finally:
 result.update(wall_seconds=time.time()-start,total_output_peak_bytes=peak)
 (t/resultfile).write_text(json.dumps(result,indent=2))
