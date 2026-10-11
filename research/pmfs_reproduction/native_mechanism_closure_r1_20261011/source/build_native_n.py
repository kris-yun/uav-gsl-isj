from common_n import *
import base64,shutil
files={'code/native_entry.cpp':(WORK/'native_entry.cpp').read_bytes()}
code=r'''
import os,time,subprocess,hashlib,signal,re
r4=Path('/home/zyc/pmfs_native_capture_r4_20261009');m1=Path('/home/zyc/pmfs_b4_m1_representation_20261010');sem=Path('/home/zyc/pmfs_m2_semantic_anchor_20261010_build2')
ctx=json.loads((r4/'BUILD_CONTEXT.json').read_text())
objs=[m1/'Simulations_native.o',sem/'PMFSLib_frozen.o',r4/'Math_accessors.o',r4/'NQAQuadtree.o']
expected={'Simulations_native.o':'3ad2e338be07dbbd404e5c91f2d0e0dc9c245c168c50554153b166f8354183576'}
assert all(p.exists() for p in objs)
cmds=[['/usr/bin/c++',*ctx['compileflags'],'-c',str(t/'code/native_entry.cpp'),'-o',str(t/'entry.o')],
 ['/usr/bin/c++','-fopenmp','-fsanitize=undefined','-Wl,--gc-sections',str(t/'entry.o'),*[str(p) for p in objs],'-o',str(t/'native_entry'),*ctx['link_tail']]]
(t/'BUILD_COMMANDS.json').write_text(json.dumps(cmds,indent=2))
start=time.monotonic();peak=0;exitcodes=[]
with (t/'build.log').open('w') as log:
 for cmd in cmds:
  p=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
  while p.poll() is None:
   rss=0
   for x in Path('/proc').iterdir():
    if not x.name.isdigit():continue
    try:
     if os.getpgid(int(x.name))!=p.pid:continue
     for row in (x/'status').read_text().splitlines():
      if row.startswith('VmRSS:'):rss+=int(row.split()[1])*1024
    except (OSError,ProcessLookupError):pass
   peak=max(peak,rss)
   if rss>1610612736 or time.monotonic()-start>1200:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=3);raise RuntimeError('BUILD_RESOURCE_STOP')
   time.sleep(.1)
  exitcodes.append(p.returncode)
  if p.returncode:raise RuntimeError((t/'build.log').read_text()[-4000:])
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
env=os.environ.copy();env['LD_LIBRARY_PATH']=':'.join(['/opt/ros/humble/lib',*[f'/home/zyc/ros2_ws/install/{x}/lib' for x in ['olfaction_msgs','gsl_actions','gmrf_msgs','gaden_msgs']]])
ldd=subprocess.run(['ldd',str(t/'native_entry')],env=env,capture_output=True,text=True,check=True).stdout
assert 'not found' not in ldd
deps={}
for line in ldd.splitlines():
 m=re.search(r'=> (/\S+)',line)
 if m and Path(m.group(1)).is_file():deps[m.group(1)]=sh(Path(m.group(1)))
result=dict(status='PASS_NATIVE_FROZEN_OBJECT_LINK',build_wall_s=time.monotonic()-start,peak_RSS_bytes=peak,exitcodes=exitcodes,
 entry_SHA256=sh(t/'native_entry'),linked_objects_SHA256={str(p):sh(p) for p in objs},
 macros=[x for x in ctx['compileflags'] if x.startswith('-D')],
 actual_dynamic_dependencies_SHA256=deps,core_source_edited=False,entry_scope='Frozen native functions under controlled observation/history driver; no ROS or navigation goal',LD_LIBRARY_PATH=env['LD_LIBRARY_PATH'])
(t/'ACTUAL_BINARY_PROVENANCE.json').write_text(json.dumps(result,indent=2));(t/'ldd.txt').write_text(ldd)
sourcefiles={}
for prefix,p in [('native/Simulations_native_with_state_access.cpp',m1/'Simulations_native_with_state_access.cpp'),('native/PMFSLib_frozen.cpp',sem/'PMFSLib_frozen.cpp'),('native/Math_accessors.cpp',r4/'code/Math_accessors.cpp'),('native/Fixture.hpp',r4/'code/Fixture.hpp'),('native/Audit.hpp',r4/'code/Audit.hpp')]:
 if p.exists():sourcefiles[prefix]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps(dict(result=result,sourcefiles=sourcefiles)))
'''
r=json.loads(upload(files,code,'BUILD_NATIVE_FROZEN_ENTRY',180))
dump(CORE/'ACTUAL_BINARY_PROVENANCE.json',r['result'])
for n,b in r['sourcefiles'].items():p=CORE/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
shutil.copyfile(WORK/'native_entry.cpp',CORE/'source/native_entry.cpp')
print(json.dumps({k:v for k,v in r['result'].items() if k not in ['actual_dynamic_dependencies_SHA256','LD_LIBRARY_PATH','linked_objects_SHA256']},indent=2))
