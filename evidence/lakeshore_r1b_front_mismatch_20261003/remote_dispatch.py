import pathlib,subprocess,os,time,concurrent.futures,tarfile,json
p=pathlib.Path('/home/zyc/lakeshore_r1b_front_mismatch_20261003');start=time.time();envs=['F_XF90_F1', 'C_XF90_F1', 'S_XF90_F1', 'F_XF90_F2', 'C_XF90_F2', 'S_XF90_F2', 'F_XF120_F1', 'C_XF120_F1', 'S_XF120_F1', 'F_XF120_F2', 'C_XF120_F2', 'S_XF120_F2', 'F_XF150_F1', 'C_XF150_F1', 'S_XF150_F1', 'F_XF150_F2', 'C_XF150_F2', 'S_XF150_F2']
jobs=[(e,x,y,r,k) for e in envs for x in [20,50,80] for y in [-20,0,20] for r in [5,10,20] for k in range(32001,32009)]
def run(j):
 e,x,y,r,k=j;tag=f'{e}_x{x}_y{y}_r{r}_seed{k}';dst=p/(tag+'.csv');tmp=p/(tag+'.partial');env=os.environ.copy();env['OMP_NUM_THREADS']='1';env['GADEN_RNG_SEED']=str(k)
 if not dst.exists():
  with (p/(tag+'.log')).open('w') as log:subprocess.run(['/home/zyc/lakeshore_observability_20261003/adapter',str(p/(e+'.csv')),str(tmp),str(x),str(y),str(r)],check=True,stdout=log,stderr=log,env=env)
  assert len(tmp.read_text().splitlines())==1201
  tmp.rename(dst)
 return tag
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for n,f in enumerate(concurrent.futures.as_completed([pool.submit(run,j) for j in jobs]),1):
  f.result()
  if n%96==0:print(json.dumps({'done':n,'total':len(jobs),'seconds':round(time.time()-start,1)}),flush=True)
with tarfile.open(p/'observations.tar.gz','w:gz') as tar:
 for e,x,y,r,k in jobs:
  tag=f'{e}_x{x}_y{y}_r{r}_seed{k}'
  for ext,folder in [('.csv','observations'),('.log','native_logs')]:tar.add(p/(tag+ext),arcname=folder+'/'+tag+ext)
print('COMPLETE',len(jobs),round(time.time()-start,1),flush=True)
