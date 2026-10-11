"""Compile and run only a synthetic source-level single-cell anchor on existing VM."""
import sys
sys.dont_write_bytecode=True
import base64,hashlib,json
from pathlib import Path
WORK=Path(__file__).resolve().parent
ROOT=WORK.parents[2]
sys.path.insert(0,str(ROOT/'work/pmfs_b4_m1'))
import remote_local
remote_local.WORK=WORK
frozen=ROOT/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
payload={
    'semantic_anchor.cpp':base64.b64encode((WORK/'semantic_anchor.cpp').read_bytes()).decode(),
    'PMFSLib_frozen.cpp':base64.b64encode((frozen/'frozen_M0/evidence/source/gsl/PMFS/PMFSLib.cpp').read_bytes()).decode(),
}
remote=r'''from pathlib import Path
import base64,hashlib,json,os,signal,subprocess,time
target=Path('/home/zyc/pmfs_m2_semantic_anchor_20261010_build2');target.mkdir(exist_ok=False)
r4=Path('/home/zyc/pmfs_native_capture_r4_20261009');m1=Path('/home/zyc/pmfs_b4_m1_representation_20261010')
payload=PAYLOAD
for name,data in payload.items():(target/name).write_bytes(base64.b64decode(data))
context=json.loads((r4/'BUILD_CONTEXT.json').read_text())
commands=[['/usr/bin/c++',*context['compileflags'],'-c',str(target/'semantic_anchor.cpp'),'-o',str(target/'semantic_anchor.o')],
 ['/usr/bin/c++',*context['compileflags'],'-c',str(target/'PMFSLib_frozen.cpp'),'-o',str(target/'PMFSLib_frozen.o')],
 ['/usr/bin/c++','-fopenmp','-fsanitize=undefined','-Wl,--gc-sections',str(target/'semantic_anchor.o'),str(target/'PMFSLib_frozen.o'),
  str(m1/'Simulations_native.o'),str(r4/'Math_accessors.o'),str(r4/'NQAQuadtree.o'),'-o',str(target/'semantic_anchor'),*context['link_tail']]]
(target/'BUILD_COMMANDS.json').write_text(json.dumps(commands,indent=2))
hashfiles=[target/'PMFSLib_frozen.cpp',m1/'Simulations_native_with_state_access.cpp',m1/'Simulations_native.o',r4/'code/Math_accessors.cpp',r4/'Math_accessors.o']
srcroot=Path('/home/zyc/native_pmfs_recovery_v1/src/gsl_server/src/gsl_server/algorithms')
hashfiles += [srcroot/'PMFS/internal/HitProbability.hpp',srcroot/'PMFS/internal/Settings.hpp',srcroot/'PMFS/internal/VisibilityMap.hpp',srcroot/'PMFS/PMFSLib.hpp',srcroot/'Common/Grid2D.hpp']
source_hash={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in hashfiles}
for p in hashfiles:
 if p.suffix=='.hpp':(target/p.name).write_bytes(p.read_bytes())
(target/'SOURCE_HASHES.json').write_text(json.dumps(source_hash,indent=2))
start=time.monotonic();peak=0;exitcodes=[]
with (target/'build.log').open('w') as log:
 for cmd in commands:
  process=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
  while process.poll() is None:
   rss=0
   for entry in Path('/proc').iterdir():
    if not entry.name.isdigit():continue
    try:
     if os.getpgid(int(entry.name))!=process.pid:continue
     for line in (entry/'status').read_text().splitlines():
      if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
    except (ProcessLookupError,PermissionError,FileNotFoundError):pass
   peak=max(peak,rss)
   if time.monotonic()-start>150 or rss>1610612736:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    raise RuntimeError('semantic compile resource cap exceeded')
   time.sleep(.1)
  exitcodes.append(process.returncode)
  if process.returncode:raise RuntimeError((target/'build.log').read_text()[-6000:])
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
env['LD_LIBRARY_PATH']=':'.join(['/opt/ros/humble/lib',*[f'/home/zyc/ros2_ws/install/{p}/lib' for p in ['olfaction_msgs','gsl_actions','gmrf_msgs','gaden_msgs']],env.get('LD_LIBRARY_PATH','')])
ldd=subprocess.run(['ldd',str(target/'semantic_anchor')],capture_output=True,text=True,env=env,check=True)
(target/'loader_check.txt').write_text(ldd.stdout)
if 'not found' in ldd.stdout:raise RuntimeError('missing loader dependency')
build=dict(wall_seconds=time.monotonic()-start,peak_RSS_bytes=peak,exitcodes=exitcodes,executable_sha256=hashlib.sha256((target/'semantic_anchor').read_bytes()).hexdigest())
(target/'BUILD_RESULT.json').write_text(json.dumps(build,indent=2))
start=time.monotonic()
result=subprocess.run([str(target/'semantic_anchor'),str(target/'native')],capture_output=True,text=True,timeout=90,env=env)
(target/'native_stdout.txt').write_text(result.stdout);(target/'native_stderr.txt').write_text(result.stderr)
run=dict(wall_seconds=time.monotonic()-start,exit_code=result.returncode,candidate_forward_calls=0,ROS_nodes=0,GADEN_realizations=0)
(target/'RUN_RESULT.json').write_text(json.dumps(run,indent=2))
if result.returncode:raise RuntimeError('semantic anchor exit '+str(result.returncode)+' '+result.stderr[-2500:])
for p in hashfiles:
 if hashlib.sha256(p.read_bytes()).hexdigest()!=source_hash[str(p)]:raise RuntimeError('input source changed')
files={str(p.relative_to(target)):base64.b64encode(p.read_bytes()).decode() for p in target.rglob('*') if p.is_file() and p.suffix not in ['.o'] and p.name!='semantic_anchor'}
print(json.dumps(dict(build=build,run=run,files=files)))
'''.replace('PAYLOAD',repr(payload))
text=remote_local.run(remote,'SEMANTIC_NATIVE_BUILD_AND_RUN_2',300)
result=json.loads(text)
for name,data in result['files'].items():
    path=WORK/'vm_evidence'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(data))
print(json.dumps({k:result[k] for k in ['build','run']},indent=2))
