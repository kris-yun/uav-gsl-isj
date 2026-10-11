import sys
sys.dont_write_bytecode=True
import base64,json
from pathlib import Path
WORK=Path(__file__).resolve().parent;ROOT=WORK.parents[2]
sys.path.insert(0,str(ROOT/'work/pmfs_b4_m1'));import remote_local
remote_local.WORK=WORK
OUT=ROOT/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/native_reference_evidence'
payload={'rng_header_parity.cpp':(WORK/'rng_header_parity.cpp').read_bytes(),
 'pristine/gaden/internal/MathUtils.hpp':(OUT/'pristine_MathUtils.hpp').read_bytes(),
 'isolated/gaden/internal/MathUtils.hpp':(OUT/'include/gaden/internal/MathUtils.hpp').read_bytes()}
blob={k:base64.b64encode(v).decode() for k,v in payload.items()}
script=r'''from pathlib import Path
import base64,hashlib,json,os,subprocess,time
t=Path('/home/zyc/pmfs_m2_rng_header_parity_20261010_build2');t.mkdir(exist_ok=False)
for name,data in PAYLOAD.items():
 p=t/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
core=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/src/gaden_common/third_party/gaden_core')
env=os.environ.copy()
for k in ['M2_GAUSSIAN_SEED','M2_UNIFORM_SEED','M2_RNG_TRACE']:env.pop(k,None)
start=time.monotonic();records=[];outputs={}
for name in ['pristine','isolated']:
 cmd=['c++','-O2','-std=c++20',str(t/'rng_header_parity.cpp'),'-o',str(t/name/'draw_parity'),
 '-I'+str(t/name),'-I'+str(core/'include'),'-I'+str(core/'third_party/DDA/include'),'-I'+str(core/'third_party/DDA/third_party/glm'),'-lfmt']
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
 (t/(name+'_compile.log')).write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError(p.stderr[-3000:])
 p=subprocess.run([str(t/name/'draw_parity')],capture_output=True,text=True,env=env,timeout=5)
 (t/(name+'_draws.txt')).write_text(p.stdout);(t/(name+'_stderr.txt')).write_text(p.stderr)
 assert p.returncode==0
 outputs[name]=p.stdout
 records.append(dict(header_variant=name,compile_command=cmd,exitcode=p.returncode,draw_sha256=hashlib.sha256(p.stdout.encode()).hexdigest()))
result=dict(verdict='PASS_HEADER_ONLY_DEFAULT_RNG_DRAW_PARITY' if outputs['pristine']==outputs['isolated'] else 'FAIL_HEADER_ONLY_DEFAULT_RNG_DRAW_PARITY',
 wall_seconds=time.monotonic()-start,bytes_equal=outputs['pristine']==outputs['isolated'],seed_override=False,trace_enabled=False,
 Gaussian_draw_calls=1100,uniform_draw_calls=101,precalculated_cache_values_checked=64,records=records,
 sqrt_exp_return_sizes=outputs['pristine'].splitlines()[:3],new_GADEN_realizations=0,new_ROS_nodes=0,new_forward_calls=0)
(t/'RNG_PARITY_RESULT.json').write_text(json.dumps(result,indent=2))
files={str(p.relative_to(t)):base64.b64encode(p.read_bytes()).decode() for p in t.rglob('*') if p.is_file() and p.name!='draw_parity'}
print(json.dumps(dict(result=result,files=files)))
'''.replace('PAYLOAD',repr(blob))
r=json.loads(remote_local.run(script,'RNG_HEADER_DEFAULT_PARITY_2',90))
for name,data in r['files'].items():
    p=WORK/'rng_header_parity_evidence'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
print(json.dumps(r['result'],indent=2))
