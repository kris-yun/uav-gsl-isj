import subprocess,pathlib,os,time,json,tarfile,concurrent.futures
p=pathlib.Path('/home/zyc/lakeshore_r1a_deconfound_20261003');start=time.time();n=0
envs=['C20', 'C06', 'C08', 'S06', 'S08', 'H1', 'H2', 'F1', 'F2'];rates=[10];seeds=list(range(31001,31009));os.environ['OMP_NUM_THREADS']='1'
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
  if n%48==0:print(json.dumps({'done':n,'total':len(jobs),'seconds':round(time.time()-start,1)}),flush=True)
with tarfile.open(p/'primary.tar.gz','w:gz') as tar:
 for env in envs:
  for rate in rates:
   for f in sorted(p.glob(f'{env}_x*_y*_r{rate}_seed*.csv')):tar.add(f,arcname='observations/'+f.name)
   for f in sorted(p.glob(f'{env}_x*_y*_r{rate}_seed*.log')):tar.add(f,arcname='native_logs/'+f.name)
print('COMPLETE',n,round(time.time()-start,1),flush=True)
