"""Build and call only saved-frame gas observation operators, never advance gas."""
from pathlib import Path
import subprocess,shlex,json,hashlib,time,os
R=Path(__file__).resolve().parents[1]
V=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws')
flags=(V/'build/gaden_common/third_party/gaden_core/CMakeFiles/gaden.dir/flags.make').read_text()
inc=next(x.split(' = ',1)[1] for x in flags.splitlines() if x.startswith('CXX_INCLUDES ='))
cmd=['g++','-std=c++20','-O3','-g0',*shlex.split(inc),str(R/'code/physical_events.cpp'),'-o','/tmp/c4_close_physical',
 '-L'+str(V/'install/gaden_common/lib'),'-lgaden','-lz',
 '-L'+str(V/'build/gaden_common/third_party/gaden_core/third_party/libbsc'),'-lbsc',
 '-Wl,-rpath,'+str(V/'build/gaden_common/third_party/gaden_core/third_party/libbsc'),
 '-Wl,-rpath,'+str(V/'install/gaden_common/lib')]
frozen=R/'logs/PHYSICAL_COMMANDS.json'
commands=json.loads(frozen.read_text()) if frozen.exists() else []
attempt=1+sum(x['command'][0]=='g++' for x in commands)
def run(cmd,n):
    t=time.monotonic()
    env=dict(os.environ);env['LD_LIBRARY_PATH']=str(V/'build/gaden_common/third_party/gaden_core/third_party/libbsc')+':'+env.get('LD_LIBRARY_PATH','')
    with (R/'logs'/f'{n}.stdout').open('w') as out,(R/'logs'/f'{n}.stderr').open('w') as err:q=subprocess.run(cmd,stdout=out,stderr=err,env=env)
    commands.append(dict(command=cmd,exit_code=q.returncode,wall_s=time.monotonic()-t));(R/'logs/PHYSICAL_COMMANDS.json').write_text(json.dumps(commands,indent=2));assert q.returncode==0,n
run(cmd,'build_physical_'+str(attempt))
run(['/tmp/c4_close_physical',str(R),str(R/'results/PHYSICAL_EVENTS.csv')],'physical_events_'+str(attempt))
(R/'lineage/PHYSICAL_EXECUTABLE_SHA256.json').write_text(json.dumps(dict(executable=hashlib.sha256(Path('/tmp/c4_close_physical').read_bytes()).hexdigest(),linked_gaden_sha256=hashlib.sha256((V/'install/gaden_common/lib/libgaden.so').read_bytes()).hexdigest()),indent=2))
print('Saved-frame C++ observation audit complete; no gas trajectories generated.')
