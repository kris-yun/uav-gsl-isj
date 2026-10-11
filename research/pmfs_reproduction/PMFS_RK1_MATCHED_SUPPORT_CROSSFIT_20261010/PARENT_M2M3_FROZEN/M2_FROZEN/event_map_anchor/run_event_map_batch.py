"""Anonymous frozen-event -> native map replay. No physics generation/query.

Input shape: {"maps": {"opaque_id": [50 binary events], ...}}.
All covariates/settings/support come from the fully validated observed anchor.
Max 16 anonymous maps permits the two preregistered block-40 schedules for
eight banks; this does not authorize new physical banks or new forward calls.
"""
import sys
sys.dont_write_bytecode=True
import base64,json,re
from pathlib import Path
WORK=Path(__file__).resolve().parent;ROOT=WORK.parents[2]
sys.path.insert(0,str(ROOT/'work/pmfs_b4_m1'));import remote_local
remote_local.WORK=WORK

def run_maps(source:Path,destination:Path,run_id:str):
    assert re.fullmatch(r'[A-Za-z0-9_-]{1,48}',run_id)
    data=json.loads(source.read_text(encoding='utf-8'))
    assert set(data)=={'maps'} and 1<=len(data['maps'])<=16
    assert not destination.exists()
    for name,event in data['maps'].items():
        assert re.fullmatch(r'[A-Za-z0-9_-]{1,64}',name)
        assert len(event)==50 and all(type(x)==int and x in (0,1) for x in event)
    remote=r'''from pathlib import Path
import base64,csv,hashlib,json,os,signal,subprocess,time
target=Path('/home/zyc/pmfs_m2_event_map_replay_20261010')
exe=target/'event_map_replay';assert hashlib.sha256(exe.read_bytes()).hexdigest()=='7d05e5124bd8e2bc6c6e1eb9b567599a6a456b3baf92c9dec9e698fed669cfbc'
folder=target/RUN_ID;folder.mkdir(exist_ok=False)
data=PAYLOAD
(folder/'SOURCE_BLIND_MAP_INPUT.json').write_text(json.dumps(data,indent=2))
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
env['LD_LIBRARY_PATH']=':'.join(['/opt/ros/humble/lib',*[f'/home/zyc/ros2_ws/install/{x}/lib' for x in ['olfaction_msgs','gsl_actions','gmrf_msgs','gaden_msgs']],env.get('LD_LIBRARY_PATH','')])
inputs=[exe,target/'snapshot/occupancy.csv',target/'snapshot/wind.csv',target/'event_covariates.csv']
inputsha={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
expected={'snapshot/occupancy.csv':'99ad97da56e7020e210506762cb6de63faf54ae350cc13d6991b544e08a3f3ae',
          'snapshot/wind.csv':'63ffd2e912032763ce034487107ca92f2d6b216c3ece9ed0cf60a9bfc5036504',
          'event_covariates.csv':'d1cff8a252e8c0437709e013eccb031f280720a57bc2e353925b67b054f763fb'}
for name,sha in expected.items():assert hashlib.sha256((target/name).read_bytes()).hexdigest()==sha
records=[];start=time.monotonic();peak=0
for name,event in data['maps'].items():
 label=folder/(name+'_labels.csv')
 with label.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['block_id','event_hit']);w.writerows(enumerate(event))
 cmd=[str(exe),str(target/'snapshot'),str(target/'event_covariates.csv'),str(label),str(folder/name)]
 begin=time.monotonic()
 with (folder/(name+'_stdout.txt')).open('w') as stdout,(folder/(name+'_stderr.txt')).open('w') as stderr:
  p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=env,start_new_session=True)
  while p.poll() is None:
   rss=0
   for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:
     if os.getpgid(int(proc.name))!=p.pid:continue
     for line in (proc/'status').read_text().splitlines():
      if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
    except (ProcessLookupError,FileNotFoundError,PermissionError):pass
   peak=max(peak,rss)
   if time.monotonic()-start>120 or rss>536870912:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    raise RuntimeError('pure event map budget exceeded')
   time.sleep(.02)
 if p.returncode:raise RuntimeError('map replay failed for '+name)
 records.append(dict(opaque_map_id=name,exitcode=p.returncode,wall_seconds=time.monotonic()-begin,native_measurement_calls=50,forward_calls=0))
for p in inputs:assert hashlib.sha256(p.read_bytes()).hexdigest()==inputsha[str(p)]
result=dict(verdict='ANONYMOUS_NATIVE_EVENT_MAP_REPLAY_COMPLETE',maps=len(records),native_measurement_calls=50*len(records),forward_calls=0,GADEN_realizations=0,ROS_nodes=0,wall_seconds=time.monotonic()-start,peak_RSS_bytes=peak,records=records,input_sha256=inputsha)
(folder/'BATCH_RESULT.json').write_text(json.dumps(result,indent=2))
files={str(p.relative_to(folder)):base64.b64encode(p.read_bytes()).decode() for p in folder.rglob('*') if p.is_file()}
print(json.dumps(dict(result=result,files=files)))
'''.replace('RUN_ID',repr('batch_'+run_id)).replace('PAYLOAD',repr(data))
    text=remote_local.run(remote,'EVENT_MAP_BATCH_'+run_id,180)
    r=json.loads(text);destination.mkdir()
    for name,blob in r['files'].items():
        p=destination/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(blob))
    return r['result']

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--run-id',required=True)
    a=p.parse_args();print(json.dumps(run_maps(a.input,a.out,a.run_id),indent=2))
