from common import *
code=r'''
import subprocess,hashlib,time
c=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws')
cmd=['c++','-O2','-std=c++20',str(t/'query_native.cpp'),'-o',str(t/'query_native'),
 '-I'+str(c/'src/gaden_common/third_party/gaden_core/include'),
 '-I'+str(c/'src/gaden_common/third_party/gaden_core/third_party/DDA/include'),
 '-I'+str(c/'src/gaden_common/third_party/gaden_core/third_party/DDA/third_party/glm'),
 '-L'+str(c/'install/gaden_common/lib'),'-lgaden','-lfmt','-fopenmp',
 '-Wl,-rpath,'+str(c/'install/gaden_common/lib')+':'+str(c/'build/gaden_common/third_party/gaden_core/third_party/libbsc')+':/opt/ros/humble/lib']
start=time.monotonic();p=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
(t/'query_build.log').write_text(p.stdout+p.stderr);(t/'QUERY_BUILD_COMMAND.json').write_text(json.dumps(cmd,indent=2));assert p.returncode==0,p.stderr
q=dict(verdict='PASS_NATIVE_SAMPLE_CONCENTRATION_QUERY_COMPILED_NO_ROS_INIT',wall_s=time.monotonic()-start,
 query_source_sha256=hashlib.sha256((t/'query_native.cpp').read_bytes()).hexdigest(),query_executable_sha256=hashlib.sha256((t/'query_native').read_bytes()).hexdigest())
(t/'QUERY_BUILD_RESULT.json').write_text(json.dumps(q,indent=2));print(json.dumps(q))
'''
r=json.loads(upload({'query_native.cpp':(W/'query_native.cpp').read_bytes()},code,'BUILD_NATIVE_QUERY',75))
(OUT/'QUERY_BUILD_RESULT.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,indent=2))
