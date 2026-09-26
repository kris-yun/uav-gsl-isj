#!/usr/bin/env python3
import hashlib, json, shlex, subprocess
from pathlib import Path
root=Path('/home/zyc/wind_alignment_d0_20260926')
build=Path('/home/zyc/native_pmfs_recovery_v1/build/gsl_server')
flags=build/'CMakeFiles/native_pmfs_r1_forward_replay.dir/flags.make'
link=build/'CMakeFiles/native_pmfs_r1_forward_replay.dir/link.txt'
compile_flags=[]
for line in flags.read_text().splitlines():
    if line.startswith(('CXX_DEFINES =','CXX_INCLUDES =','CXX_FLAGS =')):
        compile_flags+=shlex.split(line.split('=',1)[1])
args=shlex.split(link.read_text())
for i,arg in enumerate(args):
    if arg.endswith('.cpp.o'): args[i]=str(root/'code/wind_alignment_replay.cpp')
    if i>0 and args[i-1]=='-o': args[i]=str(root/'wind_alignment_replay')
args=args[:1]+compile_flags+args[1:]
assert 'R1_R2_REFERENCE_SOURCE' not in ' '.join(args)
with (root/'build.log').open('w') as f:
    subprocess.run(args,cwd=build,stdout=f,stderr=subprocess.STDOUT,check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
libs=[Path(s) if Path(s).is_absolute() else build/s for s in args if s.endswith('.a') and Path(s).name!='libpthread.a']
record={'binary_sha256':sha(root/'wind_alignment_replay'),'command':args,
        'historical_library_sha256':{str(p):sha(p) for p in libs},
        'historical_replay_source_sha256':sha(root/'code/historical_replay.cpp'),
        'instrumented_replay_source_sha256':sha(root/'code/wind_alignment_replay.cpp')}
(root/'build_provenance.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print('BUILD_PASS',record['binary_sha256'])
