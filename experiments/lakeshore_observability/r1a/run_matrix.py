"""Dispatch frozen R1A through the unchanged native simulator, one process per seed."""
import sys,subprocess,tarfile
from common import *
mode=sys.argv[1] if len(sys.argv)>1 else 'primary'
assert mode in ['primary','secondary']
rates=[10] if mode=='primary' else [5,20]
if mode=='secondary':assert json.loads((OUT/'R1A_PRIMARY_DECISION.json').read_text())['decomposition_interpretable']
for line in (OUT/'PRE_GAS_SHA256SUMS.txt').read_text().splitlines():
 h,name=line.split('  ',1);assert sha(ROOT/name)==h,(name,'frozen file changed')
code='''import subprocess,pathlib,os,time,json,tarfile,concurrent.futures
p=pathlib.Path('/home/zyc/lakeshore_r1a_deconfound_20261003');start=time.time();n=0
envs=%s;rates=%s;seeds=list(range(31001,31009));os.environ['OMP_NUM_THREADS']='1'
jobs=[(env,x,y,rate,seed) for env in envs for x in [20,50,80] for y in [-20,0,20] for rate in rates for seed in seeds]
def run(job):
 env,x,y,rate,seed=job;tag=f'{env}_x{x}_y{y}_r{rate}_seed{seed}';dest=p/(tag+'.csv')
 if not dest.exists():
  procenv=os.environ.copy();procenv['GADEN_RNG_SEED']=str(seed)
  with (p/(tag+'.log')).open('w') as f:subprocess.run(['/home/zyc/lakeshore_observability_20261003/adapter',str(p/(env+'.csv')),str(dest),str(x),str(y),str(rate)],stdout=f,stderr=f,check=True,env=procenv)
 return tag
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for f in concurrent.futures.as_completed([pool.submit(run,j) for j in jobs]):
  f.result();n+=1
  if n%%48==0:print(json.dumps({'done':n,'total':len(jobs),'seconds':round(time.time()-start,1)}),flush=True)
with tarfile.open(p/'%s.tar.gz','w:gz') as tar:
 for env in envs:
  for rate in rates:
   for f in sorted(p.glob(f'{env}_x*_y*_r{rate}_seed*.csv')):tar.add(f,arcname='observations/'+f.name)
   for f in sorted(p.glob(f'{env}_x*_y*_r{rate}_seed*.log')):tar.add(f,arcname='native_logs/'+f.name)
print('COMPLETE',n,round(time.time()-start,1),flush=True)
'''%(repr(ENVS),repr(rates),mode)
local=OUT/f'{mode}_remote_dispatch.py';local.write_text(code,encoding='utf-8',newline='')
subprocess.run(['scp',str(local),HOST+':'+REMOTE+'/'+local.name],check=True)
r=subprocess.Popen(['ssh',HOST,PREFIX+'python3 '+REMOTE+'/'+local.name],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
with (OUT/f'{mode}_execution.log').open('w',encoding='utf-8') as log:
 for line in r.stdout:print(line,end='',flush=True);log.write(line);log.flush()
assert r.wait()==0
archive=OUT/f'{mode}_observations.tar.gz';subprocess.run(['scp',HOST+':'+REMOTE+'/'+mode+'.tar.gz',str(archive)],check=True)
with tarfile.open(archive) as tar:
 for m in tar.getmembers():
  path=pathlib.PurePosixPath(m.name);assert len(path.parts)==2 and path.parts[0] in ['observations','native_logs'] and '..' not in path.parts and m.isfile()
  dest=OUT/path.as_posix();dest.parent.mkdir(exist_ok=True);dest.write_bytes(tar.extractfile(m).read())
archive.unlink()
write_json(f'{mode}_execution.json',{'environments':ENVS,'rates':rates,'plume_seeds':SEEDS,'realizations':9*9*8*len(rates)})
