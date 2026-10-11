import sys
sys.dont_write_bytecode=True
from remote import run,WORK
import base64,json,hashlib
from pathlib import Path
O=WORK.parents[2]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/domain_support_intervention';p=O/'DOMAIN_SUPPORT_FROZEN_CONTRACT.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=='a5acfa58fcc28f6300abe1a263213122cc0cf7dfe91922d71ac8dc5afd71b42e'
blobs={x.name:base64.b64encode(x.read_bytes()).decode() for x in [WORK/'candidate_domain.cpp',WORK/'Simulations_gas_domain.cpp',WORK/'GasDomain.hpp',WORK/'M3Audit.hpp',p]}
code='''from pathlib import Path
import base64,json,hashlib,os,subprocess,time,signal
t=Path('/home/zyc/pmfs_m3_root_discrimination_20261010/domain_support_intervention');assert not t.exists();t.mkdir()
for n,b in @@FILES@@.items():(t/n).write_bytes(base64.b64decode(b))
r4=Path('/home/zyc/pmfs_native_capture_r4_20261009');ctx=json.loads((r4/'BUILD_CONTEXT.json').read_text());flags=['-I'+str(t),*ctx['compileflags']]
cmds=[['/usr/bin/c++',*flags,'-c',str(t/'candidate_domain.cpp'),'-o',str(t/'entry.o')],['/usr/bin/c++',*flags,'-c',str(t/'Simulations_gas_domain.cpp'),'-o',str(t/'Simulations.o')],['/usr/bin/c++','-fopenmp','-fsanitize=undefined','-Wl,--gc-sections',str(t/'entry.o'),str(t/'Simulations.o'),*[str(r4/(n+'.o')) for n in ['Math_accessors','NQAQuadtree','PMFSLib']],'-o',str(t/'candidate_domain'),*ctx['link_tail']]]
(t/'DOMAIN_BUILD_COMMANDS.json').write_text(json.dumps(cmds,indent=2));start=time.monotonic();peak=0;exits=[]
with (t/'domain_build.log').open('w') as log:
 for cmd in cmds:
  p=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
  while p.poll() is None:
   rss=0
   for z in Path('/proc').iterdir():
    if not z.name.isdigit():continue
    try:
     if os.getpgid(int(z.name))!=p.pid:continue
     for l in (z/'status').read_text().splitlines():
      if l.startswith('VmRSS:'):rss+=int(l.split()[1])*1024
    except (ProcessLookupError,PermissionError,FileNotFoundError):pass
   peak=max(peak,rss)
   if rss>1610612736 or time.monotonic()-start>180:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    raise RuntimeError('domain build resource cap')
   time.sleep(.05)
  exits.append(p.returncode)
  if p.returncode:raise RuntimeError('domain compile error: '+(t/'domain_build.log').read_text()[-4000:])
r=dict(status='PASS_DOMAIN_COPY_COMPILED_NO_FORWARD',wall_seconds=time.monotonic()-start,RSS_bytes=peak,exitcodes=exits,executable_SHA256=hashlib.sha256((t/'candidate_domain').read_bytes()).hexdigest(),source_SHA256={n:hashlib.sha256((t/n).read_bytes()).hexdigest() for n in ['candidate_domain.cpp','Simulations_gas_domain.cpp','GasDomain.hpp','M3Audit.hpp']})
(t/'DOMAIN_BUILD_RESULT.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
'''.replace('@@FILES@@',repr(blobs))
r=json.loads(run(code,'DOMAIN_ISOLATED_BUILD',240));(O/'DOMAIN_BUILD_RESULT.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,indent=2))
