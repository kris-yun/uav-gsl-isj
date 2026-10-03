"""3888 new realizations; unchanged native kernel, independent seeded processes."""
import subprocess,tarfile
from common import *
for line in (OUT/'PRE_GAS_SHA256SUMS.txt').read_text().splitlines():
 h,name=line.split('  ',1);assert sha(ROOT/name)==h,name
code='''import pathlib,subprocess,os,time,concurrent.futures,tarfile,json
p=pathlib.Path(%r);start=time.time();envs=%r
jobs=[(e,x,y,r,k) for e in envs for x in [20,50,80] for y in [-20,0,20] for r in [5,10,20] for k in range(32001,32009)]
def run(j):
 e,x,y,r,k=j;tag=f'{e}_x{x}_y{y}_r{r}_seed{k}';dst=p/(tag+'.csv');tmp=p/(tag+'.partial');env=os.environ.copy();env['OMP_NUM_THREADS']='1';env['GADEN_RNG_SEED']=str(k)
 if not dst.exists():
  with (p/(tag+'.log')).open('w') as log:subprocess.run([%r,str(p/(e+'.csv')),str(tmp),str(x),str(y),str(r)],check=True,stdout=log,stderr=log,env=env)
  assert len(tmp.read_text().splitlines())==1201
  tmp.rename(dst)
 return tag
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for n,f in enumerate(concurrent.futures.as_completed([pool.submit(run,j) for j in jobs]),1):
  f.result()
  if n%%96==0:print(json.dumps({'done':n,'total':len(jobs),'seconds':round(time.time()-start,1)}),flush=True)
with tarfile.open(p/'observations.tar.gz','w:gz') as tar:
 for e,x,y,r,k in jobs:
  tag=f'{e}_x{x}_y{y}_r{r}_seed{k}'
  for ext,folder in [('.csv','observations'),('.log','native_logs')]:tar.add(p/(tag+ext),arcname=folder+'/'+tag+ext)
print('COMPLETE',len(jobs),round(time.time()-start,1),flush=True)
'''%(REMOTE,ENVS,ADAPTER)
local=OUT/'remote_dispatch.py';local.write_text(code,encoding='utf-8',newline='')
subprocess.run(['scp',str(local),HOST+':'+REMOTE+'/'+local.name],check=True)
proc=subprocess.Popen(['ssh',HOST,PREFIX+'python3 '+REMOTE+'/'+local.name],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
with (OUT/'execution.log').open('w',encoding='utf-8') as log:
 for line in proc.stdout:print(line,end='',flush=True);log.write(line);log.flush()
assert proc.wait()==0
archive=OUT/'observations.tar.gz';subprocess.run(['scp',HOST+':'+REMOTE+'/'+archive.name,str(archive)],check=True)
with tarfile.open(archive) as tar:
 for m in tar.getmembers():
  path=pathlib.PurePosixPath(m.name);assert m.isfile() and len(path.parts)==2 and path.parts[0] in ['observations','native_logs'] and '..' not in path.parts
  dst=OUT/path.as_posix();dst.parent.mkdir(exist_ok=True);dst.write_bytes(tar.extractfile(m).read())
archive.unlink();write_json('execution.json',{'realizations':3888,'rows':4665600,'seeds':SEEDS,'native_kernel_unchanged':True})
