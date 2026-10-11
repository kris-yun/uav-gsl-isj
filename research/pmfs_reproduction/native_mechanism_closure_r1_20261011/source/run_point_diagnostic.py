from common_n import *
import csv,io,shutil,numpy as np
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def cb(rs):
 s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs);return s.getvalue().encode()
p=load(CORE/'FACTORIAL_CONTRACT.json');sources={j['candidate']:j['source_xyz'] for j in p['jobs']};old=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime/updates/update_0';states=rows(old/'candidates.csv')[:2];files={};jobs=[]
for rep,r in enumerate(states):
 folder='point_inputs/R'+str(rep);base=CORE/'native_inputs/inputs/B4'
 for n in ['input.csv','metadata.csv','settings.csv']:files[folder+'/'+n]=(base/n).read_bytes()
 files[folder+'/gaussian_cache.f32']=(old/'gaussian_cache.f32').read_bytes();files[folder+'/rng.csv']=cb([dict(phase=r['gaussian_index_before'],engine=r['rng_before'])])
 for c,xyz in sources.items():
  i=int((np.float32(xyz[0])-np.float32(-7.55))/.25);j=int((np.float32(xyz[1])-np.float32(-7.88))/.25);name=folder+'/'+c+'.csv'
  files[name]=cb([dict(origin_i=i,origin_j=j,size_i=1,size_j=1,point_x=xyz[0],point_y=xyz[1])]);jobs.append(dict(id=f'{c}_R{rep}',candidate=c,replicate=rep,point_xyz=xyz,mode='point_forward',input=DATA+'/'+folder,payload=DATA+'/'+name))
dump(CORE/'POINT_DIAGNOSTIC_CONTRACT.json',dict(status='PRE_EXECUTION_FROZEN',jobs=jobs,scope='N_POINT_DIAGNOSTIC native existing Mode::Point; five exactXY sources; not native adaptive posterior',
 random_states='Two already saved native update0 states and sameGaussian cache; not two independent physical realizations',native_original_functions=True,forwards=10,
 unmatched_3D_fields=['native2D has no z/sigma/buoyancy/3D LOS; native injection50/s, versusGADEN7/s; native warmup=.2s and record=.1s, not existing3D physical query times'],
 point_source_audit='Mode::Point returns constant directly; old leaf-point audit does not record these emissions. Config + fixed native code prove definition; do not fabricate point count. RNG Gaussian phase recorded; total cache-cycle count not captured by old native kernel.'))
host=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011')
for n,b in files.items():q=host/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
code='''from pathlib import Path
import json,os,subprocess,time,hashlib
t=Path(REMOTE);D=Path(DATA);jobs=JOBS;env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads((t/'ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH'])
out=D/'point_results';out.mkdir();receipt=[]
for label in ['E3','B4']:
 i=t/'inputs'/label;p=subprocess.run(['/dev/shm/nmc_point/native_point_entry','anchor_forward',str(i),str(i/'anchor_job.csv'),str(out/('OFF_'+label))],env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
 old=D/'native_results'/(label+'_short_forward_OFF')/'forward';new=out/('OFF_'+label)/'forward'
 for f in old.rglob('*'):
  if f.is_file():assert hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256((new/f.relative_to(old)).read_bytes()).digest()
 receipt.append({'id':'OFF_'+label,'identical_all_saved_files':True,'forward_calls':1})
for job in jobs:
 start=time.time();p=subprocess.run(['/dev/shm/nmc_point/native_point_entry',job['mode'],job['input'],job['payload'],str(out/job['id'])],env=env,capture_output=True,text=True,timeout=60);assert p.returncode==0,p.stderr
 receipt.append(dict(job,wall_s=time.time()-start,forward_calls=1,exitcode=0))
print(json.dumps({'status':'PASS_EXACT_POINT_DIAGNOSTIC_AND2_OFF','records':receipt,'forward_calls':12}))
'''.replace('REMOTE',repr(REMOTE)).replace('DATA',repr(DATA)).replace('JOBS',repr(jobs))
r=json.loads(run_remote(code,'native_point_five_hypotheses_two_states',120));dump(CORE/'POINT_DIAGNOSTIC_EXECUTION.json',r);print(json.dumps({'status':r['status'],'forwards':r['forward_calls']}))
