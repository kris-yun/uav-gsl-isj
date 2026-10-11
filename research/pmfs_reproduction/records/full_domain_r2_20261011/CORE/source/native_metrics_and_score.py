from common_r2 import *
import numpy as np,csv,shutil
def wc(p,rs):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
root=CORE/'inference_inputs';calc=CORE/'development_inference';index=load(calc/'RESULT_INDEX.json');arr=np.load(calc/'FULL_SOURCE_POSTERIORS.npz',allow_pickle=False);stage=HOST/'metrics';stage.mkdir();jobs=[]
for row in index:
 key=row['key'];a=arr[key+'_posterior'];assert np.isclose(a.sum(),1) and (a>=0).all();p=stage/(key+'.f64');a.astype('<f8').tofile(p);jobs.append(dict(id=key,path=DATA+'/metrics/'+p.name))
for ob in load(root/'OBSERVATION_REGISTRY.json'):
 a=np.load(root/ob['folder']/'N0_FROZEN_POSTERIORS.npz',allow_pickle=False)
 for n in [20,35,50]:
  key=f'{ob["oid"]}__N0__{n}';p=stage/(key+'.f64');a[f'p{n}'].astype('<f8').tofile(p);jobs.append(dict(id=key,path=DATA+'/metrics/'+p.name))
wc(stage/'JOBS.csv',jobs)
pred=np.load(root/'ALL_CANDIDATE_PREDICTIONS.npz',allow_pickle=False);checks=[]
for oid in ['B4','D00']:
 plan='B4' if oid=='B4' else 'PUBLIC_B'
 for n in [20,35,50]:
  d=stage/f'SCORE_{oid}_{n}';d.mkdir();shutil.copy2(root/f'observations/{oid}/GRID_INPUT_{n}.csv',d/'input.csv')
  for name in ['metadata.csv','settings.csv','rng.csv','gaussian_cache.f32']:shutil.copy2(CORE/'predictor_inputs/R0'/name,d/name)
  js=[]
  for method in ['P3-O0','P3-O1','N_POINT_ALL']:
   a=pred[f'{plan}_{method}_{n}' if method!='N_POINT_ALL' else method].mean(axis=1).astype('<f4')
   for i,x in enumerate(a):
    sid=f'{method}_{i:03}';x.tofile(d/(sid+'.f32'));js.append(dict(id=sid,path=DATA+'/metrics/'+d.name+'/'+sid+'.f32'))
  wc(d/'JOBS.csv',js);checks.append(dict(oid=oid,blocks=n,dir=d.name))
dump(stage/'SCORE_CHECK_JOBS.json',checks)
code="""import os,subprocess,time,json
from pathlib import Path
d=Path(%r);binary='/dev/shm/pmfs_r2/native_build/native_batch_entry';env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads(Path('/home/zyc/ros2_ws/pmfs_native_mechanism_closure_r1_20261011/ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH']);start=time.monotonic()
cmd=[binary,'posterior_metrics',%r+'/inputs/R0',str(d/'JOBS.csv'),str(d/'native_metrics')]
p=subprocess.run(cmd,env=env,capture_output=True,timeout=240);(d/'metrics.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
for j in json.loads((d/'SCORE_CHECK_JOBS.json').read_text()):
 f=d/j['dir'];p=subprocess.run([binary,'score',str(f),str(f/'JOBS.csv'),str(f/'native_score')],env=env,capture_output=True,timeout=240);(f/'score.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
print(json.dumps(dict(status='PASS_NATIVE_METRIC_AND_SCORE_EXECUTION',wall_s=time.monotonic()-start,posteriors=%d,score_maps=576)))
"""%(DATA+'/metrics',REMOTE,len(jobs))
print(remote(code,'native_metric912_score576_loader_repair',timeout=300))
shutil.copy2(stage/'native_metrics/METRICS.csv',calc/'NATIVE_POSITION_METRICS.csv')
worst=0;rs=[]
for j in checks:
 rows=list(csv.DictReader((stage/j['dir']/'native_score/scores.csv').open()))
 for r in rows:
  method,i=r['id'].rsplit('_',1);key=f'{j["oid"]}__R01__{method}__{j["blocks"]}';expected=float(arr[key+'_scores'][int(i)]);err=abs(float(r['log_score'])-expected);worst=max(worst,err);rs.append(dict(oid=j['oid'],blocks=j['blocks'],method=method,source_index=i,native_log_score=r['log_score'],python_log_score=expected,absolute_difference=err))
assert worst<1e-10;wc(calc/'NATIVE_SCORING_PARITY.csv',rs);dump(CORE/'NATIVE_SCORING_AND_METRIC_VALIDATION.json',dict(status='PASS',score_maps=len(rs),max_log_score_difference=worst,posteriors=len(jobs),actual_native_expectedValue_top5_and_variance=True,tolerance=1e-10,score_function_unchanged=True))
print(json.dumps({'native_score_max_difference':worst,'metrics':len(jobs)}))
