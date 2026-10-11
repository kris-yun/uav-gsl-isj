from common_n import *
code='''from pathlib import Path
import subprocess,time,json,hashlib,shutil,shlex
t=Path(REMOTE);m=Path('/home/zyc/pmfs_m2_process_observation_20261010');ws=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws')
flags=(ws/'build/gaden_common/third_party/gaden_core/CMakeFiles/gaden.dir/flags.make').read_text()
args=[]
for key in ['CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS']:args+=shlex.split(next(x.split(' = ',1)[1] for x in flags.splitlines() if x.startswith(key+' = ')))
args=[x for x in args if x!='-g']
cmd=['/usr/bin/c++','-I'+str(t/'C_include'),'-I'+str(ws/'src/gaden_common/third_party/gaden_core/src'),*args,'-g0','-c',str(t/'C_source/RunningSimulation.cpp'),'-o','/dev/shm/nmc_C/RunningSimulation.o']
link=json.loads((m/'RNG_LIBRARY_LINK_COMMAND.json').read_text());link=[x.replace(str(m/'objects/src/RunningSimulation.cpp.o'),'/dev/shm/nmc_C/RunningSimulation.o') for x in link];link[link.index('-o')+1]='/dev/shm/nmc_C/libgaden.so'
rr=[]
for i,c in enumerate([cmd,link]):
 start=time.time();p=subprocess.run(c,stdout=(t/f'C_repair_{i}.stdout').open('w'),stderr=(t/f'C_repair_{i}.stderr').open('w'),timeout=180)
 rr.append({'command':c,'exitcode':p.returncode,'wall_s':time.time()-start})
 if p.returncode:print((t/f'C_repair_{i}.stderr').read_text()[-4000:]);raise SystemExit(1)
keep=Path(DATA)/'C_binary_preservation';keep.mkdir()
for f in Path('/dev/shm/nmc_C').iterdir():shutil.copy2(f,keep/f.name)
r={'status':'COMPILE_PASS_NOT_PHYSICAL_QUALIFICATION','builds':rr,'library_SHA256':hashlib.sha256(Path('/dev/shm/nmc_C/libgaden.so').read_bytes()).hexdigest(),'technical_repair':'restore relative original YAML_Conversions include path; no model change'}
(t/'C_BUILD.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
'''.replace('REMOTE',repr(REMOTE)).replace('DATA',repr(DATA))
r=json.loads(run_remote(code,'C_include_repair_build',240));dump(CORE/'C_BUILD.json',r)
print(json.dumps({'status':r['status'],'compile_s':sum(x['wall_s'] for x in r['builds'])}))
