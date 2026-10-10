from pathlib import Path
import subprocess,json,time,os,signal,hashlib,shutil
t=Path(__file__).resolve().parent
assert not (t/'GENERATION_STARTED.json').exists() and not (t/'one_realization_E3').exists()
assert (t/'one_realization_E3').resolve().is_relative_to(t.resolve())
start=time.time();(t/'GENERATION_STARTED.json').write_text(json.dumps(dict(generation_executions=1,start_wall_time=start,source=[-4,-1.9,.7],scope='ONE_E3_ONLY')))
reason=None;peakbytes=0
with (t/'generation.log').open('w') as log:
 p=subprocess.Popen(['bash',str(t/'generate_once.sh')],stdout=log,stderr=log,start_new_session=True)
 while p.poll() is None:
  files=list((t/'one_realization_E3').rglob('*')) if (t/'one_realization_E3').exists() else []
  total=sum(f.stat().st_size for f in files if f.is_file());peakbytes=max(peakbytes,total)
  if total>1_000_000_000:reason='OUTPUT_DISK_LIMIT_1GB'
  if time.time()-start>1200:reason='GENERATION_WALL_TIME_LIMIT_20MIN'
  if shutil.disk_usage(t).free<1_000_000_000:reason='FREE_DISK_BELOW_1GB'
  if reason:
   os.killpg(p.pid,signal.SIGINT);p.wait(timeout=20);break
  time.sleep(.5)
 exitcode=p.wait()
(t/'GENERATION_RESULT.json').write_text(json.dumps(dict(exit_code=exitcode,wall_seconds=time.time()-start,generation_executions=1,output_peak_bytes=peakbytes,resource_stop_reason=reason),indent=2))
