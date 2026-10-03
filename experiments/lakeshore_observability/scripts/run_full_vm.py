"""Full matrix dispatched once; original binaries/environment remain unchanged."""
import pathlib,json,subprocess,tarfile
from run_gaden_matrix import ROOT,EXP,OUT,REMOTE,HOST,PREFIX
assert json.loads((OUT/'smoke_matrix_validation.json').read_text())['pass']
assert json.loads((OUT/'R0_wisco_effect_summary.json').read_text())['decision']=='R0_GO'
assert (OUT/'PRE_R1_FREEZE_SHA256SUMS.txt').exists()
for env in ['N0','L1','F1','F2']:
 assert json.loads((OUT/f'wind_{env}_QC.json').read_text())['pass']
 subprocess.run(['scp',str(EXP/f'generated_project/wind_simulations/{env}/wind_0.csv'),HOST+':'+REMOTE+'/'+env+'.csv'],check=True)
code='''import subprocess,pathlib,os,time,json,tarfile
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
'''
script=EXP/'scripts/full_matrix_remote.py';script.write_text(code)
subprocess.run(['scp',str(script),HOST+':'+REMOTE+'/full_matrix_remote.py'],check=True)
subprocess.run(['ssh',HOST,PREFIX+'python3 '+REMOTE+'/full_matrix_remote.py'],check=True)
archive=OUT/'observations.tar.gz';subprocess.run(['scp',HOST+':'+REMOTE+'/observations.tar.gz',str(archive)],check=True)
with tarfile.open(archive) as t:
 for m in t.getmembers():
  assert pathlib.PurePosixPath(m.name).name==m.name and m.isfile()
  with (OUT/'observations'/m.name).open('wb') as f:f.write(t.extractfile(m).read())
(OUT/'full_execution.json').write_text(json.dumps({'realizations':864,'environments':['N0','L1','F1','F2'],'sources':9,'releases_filaments_s':[5,10,20],'seeds':list(range(30001,30009))},indent=2))
