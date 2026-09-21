"""Compile an isolated executable, reusing immutable R2 native library objects.
No cmake/make/install or modification of the frozen build is performed.
"""
import hashlib,json,pathlib,shlex,subprocess,sys,time
source=pathlib.Path(__file__).resolve().parent
build=pathlib.Path(sys.argv[1]).resolve()
out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
flags={}
for line in (build/'CMakeFiles/meaci_replay_true.dir/flags.make').read_text().splitlines():
    if ' = ' in line:
        k,v=line.split(' = ',1);flags[k]=shlex.split(v)
obj=out/'native_bank.o'; exe=out/'native_bank'
compile_cmd=['/usr/bin/c++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(source/'native_bank.cpp'),'-o',str(obj)]
link=shlex.split((build/'CMakeFiles/meaci_replay_true.dir/link.txt').read_text())
link=[str(obj) if x.endswith('tools/meaci_replay_true.cpp.o') else x for x in link]
link[link.index('-o')+1]=str(exe)
tracked=[build/'libPMFS.a',build/'libGSL_common.a']
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):digest(p) for p in tracked}
subprocess.run(compile_cmd,check=True,cwd=build)
subprocess.run(link,check=True,cwd=build)
assert before=={str(p):digest(p) for p in tracked}
(out/'build_provenance.json').write_text(json.dumps({'library_sha256':before,'executable_sha256':digest(exe),'source_sha256':digest(source/'native_bank.cpp'),'compile':compile_cmd,'link':link,'frozen_objects_unchanged':True},indent=2)+'\n')
