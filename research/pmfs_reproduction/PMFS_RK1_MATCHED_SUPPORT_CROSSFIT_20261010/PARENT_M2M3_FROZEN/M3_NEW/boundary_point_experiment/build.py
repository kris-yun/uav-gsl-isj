import sys
sys.dont_write_bytecode=True
from remote import run,WORK,REMOTE
import base64,json,hashlib
blobs={p.name:base64.b64encode(p.read_bytes()).decode() for p in [WORK/'candidate_forward.cpp',WORK/'Simulations_boundary_diagnostic.cpp',WORK/'M3Audit.hpp',WORK/'PREPARED_CONTRACT.json']}
for p in (WORK/'jobs').glob('*.csv'):blobs['jobs/'+p.name]=base64.b64encode(p.read_bytes()).decode()
code='''from pathlib import Path
import base64,json,hashlib,os,subprocess,time,signal
t=Path(REMOTE);assert not t.exists();t.mkdir(parents=True)
for n,b in BLOBS.items():
 p=t/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
r4=Path('/home/zyc/pmfs_native_capture_r4_20261009');context=json.loads((r4/'BUILD_CONTEXT.json').read_text())
flags=['-I'+str(t),*context['compileflags']]
commands=[['/usr/bin/c++',*flags,'-c',str(t/'candidate_forward.cpp'),'-o',str(t/'entry.o')],['/usr/bin/c++',*flags,'-c',str(t/'Simulations_boundary_diagnostic.cpp'),'-o',str(t/'Simulations.o')],['/usr/bin/c++','-fopenmp','-fsanitize=undefined','-Wl,--gc-sections',str(t/'entry.o'),str(t/'Simulations.o'),*[str(r4/(n+'.o')) for n in ['Math_accessors','NQAQuadtree','PMFSLib']],'-o',str(t/'candidate_forward'),*context['link_tail']]]
(t/'BUILD_COMMANDS.json').write_text(json.dumps(commands,indent=2))
start=time.monotonic();peak=0;exits=[]
with (t/'build.log').open('w') as log:
 for cmd in commands:
  proc=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
  while proc.poll() is None:
   rss=0
   for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
     if os.getpgid(int(p.name))!=proc.pid:continue
     for l in (p/'status').read_text().splitlines():
      if l.startswith('VmRSS:'):rss+=int(l.split()[1])*1024
    except (ProcessLookupError,PermissionError,FileNotFoundError):pass
   peak=max(peak,rss)
   if rss>1610612736 or time.monotonic()-start>180:
    os.killpg(proc.pid,signal.SIGTERM)
    try:proc.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
    raise RuntimeError('build resource cap')
   time.sleep(.05)
  exits.append(proc.returncode)
  if proc.returncode:raise RuntimeError('build failed: '+(t/'build.log').read_text()[-4000:])
result=dict(verdict='BUILD_PASS_NO_FORWARD_EXECUTED',wall_seconds=time.monotonic()-start,max_RSS_bytes=peak,exitcodes=exits,executable_sha256=hashlib.sha256((t/'candidate_forward').read_bytes()).hexdigest(),source_sha256={n:hashlib.sha256((t/n).read_bytes()).hexdigest() for n in ['candidate_forward.cpp','Simulations_boundary_diagnostic.cpp','M3Audit.hpp']},new_forward_calls=0,ros_init_calls=0,target=str(t))
(t/'BUILD_RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
'''.replace('REMOTE',repr(REMOTE)).replace('BLOBS',repr(blobs))
result=json.loads(run(code,'ISOLATED_BUILD',240));(WORK/'BUILD_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
