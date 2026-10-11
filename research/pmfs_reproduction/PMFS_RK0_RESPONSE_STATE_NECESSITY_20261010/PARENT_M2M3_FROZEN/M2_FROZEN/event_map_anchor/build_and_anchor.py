import sys
sys.dont_write_bytecode=True
import base64,csv,hashlib,io,json
from pathlib import Path
WORK=Path(__file__).resolve().parent;ROOT=WORK.parents[2]
sys.path.insert(0,str(ROOT/'work/pmfs_b4_m1'));import remote_local
remote_local.WORK=WORK
snapshot=ROOT/'work/pmfs_b4_m1/snapshot'
with (snapshot/'input.csv').open(encoding='utf-8',newline='') as f:cells=list(csv.DictReader(f))
with (snapshot/'metadata.csv').open(encoding='utf-8',newline='') as f:meta=list(csv.DictReader(f))[0]
def csvbytes(head,rows):
    s=io.StringIO(newline='');w=csv.writer(s);w.writerow(head);w.writerows(rows);return s.getvalue().encode()
occ=csvbytes(['cell_index','occupancy','grid_width','grid_height','cell_size','origin_x','origin_y'],[[r['cell_index'],'Free' if r['occupancy']=='1' else 'Obstacle',meta['width'],meta['height'],meta['cell_size'],meta['origin_x'],meta['origin_y']] for r in cells])
wind=csvbytes(['cell_index','u','v'],[[r['cell_index'],r['u'],r['v']] for r in cells])
labels=csvbytes(['block_id','event_hit'],[[i,1] for i in range(50)])
cov=ROOT/'work/pmfs_m2_observation_discrimination_20261010/scoring_contract/MAP_REPLAY_EVENT_COVARIATES.csv'
files={'event_map_replay.cpp':(WORK/'event_map_replay.cpp').read_bytes(),'snapshot/occupancy.csv':occ,'snapshot/wind.csv':wind,'event_covariates.csv':cov.read_bytes(),'observed_labels.csv':labels}
payload={k:base64.b64encode(v).decode() for k,v in files.items()}
remote=r'''from pathlib import Path
import base64,hashlib,json,os,signal,subprocess,time
target=Path('/home/zyc/pmfs_m2_event_map_replay_20261010');target.mkdir(exist_ok=False)
r4=Path('/home/zyc/pmfs_native_capture_r4_20261009');semantic=Path('/home/zyc/pmfs_m2_semantic_anchor_20261010_build2')
for name,data in PAYLOAD.items():
 p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
ctx=json.loads((r4/'BUILD_CONTEXT.json').read_text())
cmds=[['/usr/bin/c++',*ctx['compileflags'],'-c',str(target/'event_map_replay.cpp'),'-o',str(target/'event_map_replay.o')],
 ['/usr/bin/c++','-fopenmp','-fsanitize=undefined','-Wl,--gc-sections',str(target/'event_map_replay.o'),str(semantic/'PMFSLib_frozen.o'),str(r4/'Math_accessors.o'),str(r4/'NQAQuadtree.o'),'-o',str(target/'event_map_replay'),*ctx['link_tail']]]
(target/'BUILD_COMMANDS.json').write_text(json.dumps(cmds,indent=2))
start=time.monotonic();peak=0;exitcodes=[]
with (target/'build.log').open('w') as log:
 for cmd in cmds:
  p=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
  while p.poll() is None:
   rss=0
   for x in Path('/proc').iterdir():
    if not x.name.isdigit():continue
    try:
     if os.getpgid(int(x.name))!=p.pid:continue
     for line in (x/'status').read_text().splitlines():
      if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
    except (ProcessLookupError,FileNotFoundError,PermissionError):pass
   peak=max(peak,rss)
   if time.monotonic()-start>120 or rss>1610612736:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    raise RuntimeError('event replay compile cap exceeded')
   time.sleep(.1)
  exitcodes.append(p.returncode)
  if p.returncode:raise RuntimeError((target/'build.log').read_text()[-5000:])
build=dict(wall_seconds=time.monotonic()-start,peak_RSS_bytes=peak,exitcodes=exitcodes,executable_sha256=hashlib.sha256((target/'event_map_replay').read_bytes()).hexdigest())
(target/'BUILD_RESULT.json').write_text(json.dumps(build,indent=2))
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
env['LD_LIBRARY_PATH']=':'.join(['/opt/ros/humble/lib',*[f'/home/zyc/ros2_ws/install/{x}/lib' for x in ['olfaction_msgs','gsl_actions','gmrf_msgs','gaden_msgs']],env.get('LD_LIBRARY_PATH','')])
start=time.monotonic();p=subprocess.run([str(target/'event_map_replay'),str(target/'snapshot'),str(target/'event_covariates.csv'),str(target/'observed_labels.csv'),str(target/'observed_anchor')],capture_output=True,text=True,env=env,timeout=60)
(target/'anchor_stdout.txt').write_text(p.stdout);(target/'anchor_stderr.txt').write_text(p.stderr)
run=dict(wall_seconds=time.monotonic()-start,exitcode=p.returncode,forward_calls=0,new_ROS_nodes=0,GADEN_realizations=0)
(target/'ANCHOR_RUN_RESULT.json').write_text(json.dumps(run,indent=2))
if p.returncode:raise RuntimeError(p.stderr[-3000:])
files={str(p.relative_to(target)):base64.b64encode(p.read_bytes()).decode() for p in target.rglob('*') if p.is_file() and p.suffix!='.o' and p.name!='event_map_replay'}
print(json.dumps(dict(build=build,run=run,files=files)))
'''.replace('PAYLOAD',repr(payload))
text=remote_local.run(remote,'EVENT_MAP_BUILD_AND_ANCHOR',240)
r=json.loads(text)
for name,data in r['files'].items():
    p=WORK/'vm_evidence'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
print(json.dumps({k:r[k] for k in ['build','run']},indent=2))
