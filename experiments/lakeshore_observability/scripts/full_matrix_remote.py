import subprocess,pathlib,os,time,json,tarfile
p=pathlib.Path('/home/zyc/lakeshore_observability_20261003'); start=time.time(); n=0; os.environ['OMP_NUM_THREADS']='1'
for env in ['N0','L1','F1','F2']:
 for x in [20,50,80]:
  for y in [-20,0,20]:
   for rate in [5,10,20]:
    for seed in range(30001,30009):
     tag=f'{env}_x{x}_y{y}_r{rate}_seed{seed}';dest=p/(tag+'.csv')
     if not dest.exists():
      os.environ['GADEN_RNG_SEED']=str(seed)
      with (p/(tag+'.log')).open('w') as log: subprocess.run([str(p/'adapter'),str(p/(env+'.csv')),str(dest),str(x),str(y),str(rate)],stdout=log,stderr=log,check=True)
     n+=1
     if n%48==0:print(json.dumps({'completed':n,'total':864,'elapsed_s':round(time.time()-start,1)}),flush=True)
with tarfile.open(p/'observations.tar.gz','w:gz') as tar:
 for f in sorted(p.glob('*_x*_y*_r*_seed*.csv')):tar.add(f,arcname=f.name)
print('FULL_MATRIX_COMPLETE',n,round(time.time()-start,1),flush=True)
