from pathlib import Path
import hashlib,json,os,resource,subprocess,time,sys
import numpy as np
B=Path('/mnt/hgfs/workspace/METHOD_COMPARISON_O24_1M2_20261024/V11_REVIEW_20261024')
T=B/'function_trial';S=Path('/mnt/hgfs/workspace/FROZEN_O24_1M2_SCREEN12_20261024/source_snapshot')
G=Path('/home/zyc/ros2_ws/research_runs/v11_function_trial_20261024');G.mkdir(exist_ok=False)
out=T/'results';out.mkdir(exist_ok=False)
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
plan=read(T/'PREREGISTERED_16.json');start=time.monotonic();cost=[]
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(120,125))
 resource.setrlimit(resource.RLIMIT_FSIZE,(16777216,16777216))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
def execute(name,argv,timeout):
 before=resource.getrusage(resource.RUSAGE_CHILDREN);t=time.monotonic()
 with (out/(name+'.stdout.log')).open('wb') as o,(out/(name+'.stderr.log')).open('wb') as e:
  q=subprocess.run(argv,stdout=o,stderr=e,env=env,timeout=timeout,preexec_fn=limits)
 after=resource.getrusage(resource.RUSAGE_CHILDREN)
 cost.append({'stage':name,'argv':argv,'exit_code':q.returncode,'wall_s':time.monotonic()-t,'cpu_s':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime})
 dump(out/'COST.json',cost)
 assert q.returncode==0,(name,'see stderr')
 assert time.monotonic()-start<plan['full_stage_wall_cap_s'],'BATCH_WALL_LIMIT'
compiler=['g++','-std=gnu++17','-O3','-DNDEBUG','-include','bits/stdc++.h','-I'+str(T/'compatibility_headers'),'-I'+str(S/'src'),'-I'+str(S/'third_party/DDA/include'),'-I'+str(S/'third_party/xxHash/include'),str(T/'native_function_runner.cpp'),str(S/'src/gsl_server/algorithms/Common/Utils/NQAQuadtree.cpp'),'-o',str(G/'native_function_runner')]
try:
 execute('compile',compiler,120)
 dump(out/'RUNNER_IDENTITY.json',{'binary':str(G/'native_function_runner'),'sha256':hashlib.sha256((G/'native_function_runner').read_bytes()).hexdigest(),'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],'scope':'Standalone diagnostic binary, not frozen O24 replacement. No ROS or GADEN launch.'})
 parity=[]
 for call in plan['mandatory_original_replay_calls']:
  spec=read(T/f'replay_call_{call}.json');tid=spec['rng']['before']['tid'];prefix=out/f'replay_{call}'
  execute('replay_'+str(call),[str(G/'native_function_runner'),str(T/'scene.json'),'replay',str(T/f'replay_call_{call}.json'),str(prefix),str(T/f'native_rng_states.jsonl.cache.thread{tid}.f32')],120)
  actual=np.fromfile(str(prefix)+'.f32',dtype='<f4');expected=np.fromfile(T/f'expected_call_{call}.f32',dtype='<f4');r=read(Path(str(prefix)+'.json'))
  error=float(np.max(np.abs(actual-expected)));score=abs(r['score']-float(spec['candidate']['score']))/float(spec['candidate']['score'])
  keys=['seed','state','uc','uh','gc','gh','index'];rng_equal={k:r['after'][k]==spec['rng']['after'][k] for k in keys}
  parity.append({'call':call,'map_max_abs_error':error,'score_relative_error':score,'RNG_endpoint_equal':rng_equal,'map_float32_exact':bool(np.array_equal(actual,expected))})
 dump(out/'NATIVE_FUNCTION_REPLAY_QA.json',parity)
 assert all(x['map_float32_exact'] and x['score_relative_error']<1e-12 and all(x['RNG_endpoint_equal'].values()) for x in parity),'REPLAY_MISMATCH_STOP_NO_MECHANISM_ARMS'
 for arm in ['A','B','C','D']:
  for j,seed in enumerate(plan['replicate_uniform_seeds']):
   spec={'arm':arm,'replicate':j,'seed':seed}
   if arm=='B':spec['point']=plan['B_fixed_points'][j]
   if arm=='C':spec['point']=plan['C_fixed_point']
   if arm=='D':spec['point']=plan['D_fixed_point']
   p=out/f'spec_{arm}_{j}.json';dump(p,spec);prefix=out/f'{arm}_{j}'
   execute(f'run_{arm}_{j}',[str(G/'native_function_runner'),str(T/'scene.json'),'arm',str(p),str(prefix),str(T/'native_rng_states.jsonl.cache.thread1.f32')],120)
   bytes_used=sum(p.stat().st_size for p in out.rglob('*') if p.is_file());assert bytes_used<plan['new_output_cap_bytes'],'OUTPUT_BYTE_LIMIT'
 dump(out/'EXECUTION_RECEIPT.json',{'status':'PASS_EXACT_REPLAY_THEN16_ARMS','mechanism_runs':16,'native_replay_runs':2,'new_ROS_goals':0,'new_GADEN_worlds':0,'training':0,'cost':cost,'total_wall_s':time.monotonic()-start})
 print(json.dumps(read(out/'EXECUTION_RECEIPT.json')))
except Exception as e:
 dump(out/'STOP_RECEIPT.json',{'status':'STOP_PRESERVE_FIRST_FAILURE','error':str(e),'cost':cost,'new_ROS_goals':0,'new_GADEN_worlds':0})
 raise
