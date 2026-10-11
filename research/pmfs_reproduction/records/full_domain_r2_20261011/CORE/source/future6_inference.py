from common_r2 import *
import numpy as np,csv,shutil,sys
sys.path.insert(0,str(WORK/'pro_plan/code'));from infer_source_matrix import run
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
ledger=load(HOST/'FUTURE_OBSERVATION_LEDGER.json');assert ledger['status']=='PASS_ALL_SIX_PREREGISTERED_OBSERVATIONS' and len(ledger['records'])==6;shutil.copy2(HOST/'FUTURE_OBSERVATION_LEDGER.json',CORE/'FUTURE_OBSERVATION_LEDGER.json')
root=CORE/'future_inference_inputs';root.mkdir();truth={};registry=[]
for name in ['SOURCE_CATALOG.json','SCORING_FREE_MASK.npy','SOURCE_CELL_TO_REGION.npy','ALL_CANDIDATE_PREDICTIONS.npz']:shutil.copy2(CORE/'inference_inputs'/name,root/name)
assert sha(root/'ALL_CANDIDATE_PREDICTIONS.npz')==load(CORE/'FUTURE_EXECUTION_FREEZE.json')['candidate_prediction_SHA256']
for j in load(CORE/'evaluation_only/FUTURE6_PREREGISTRATION.json')['jobs']:
 oid=j['oid'];src=HOST/'observations'/oid;dest=root/'observations'/oid;dest.mkdir(parents=True);events=rows(src/'PUBLIC_B_RECEIVER_EVENTS.csv');maps={};posts={}
 for n in [20,35,50]:
  wc(dest/f'EVENTS_{n}.csv',events[:n]);r=rows(src/'N0'/f'map_blocks_{n}.csv');wc(dest/f'GRID_INPUT_{n}.csv',r);maps[f'p{n}']=np.array([float(x['probability']) for x in r]);maps[f'c{n}']=np.array([float(x['confidence']) for x in r]);posts[f'p{n}']=np.fromfile(src/'N0'/f'update_{[20,35,50].index(n)}'/'posterior.f64',dtype='<f8')
 np.savez_compressed(dest/'MEASURED_MAPS.npz',**maps);np.savez_compressed(dest/'N0_FROZEN_POSTERIORS.npz',**posts);registry.append(dict(oid=oid,plan='PUBLIC_B',folder='observations/'+oid,role='six_preregistered_new_observation',truth_fields_in_consumer_files=False));truth[oid]=dict(source_group=j['source_id'],source_xyz=j['source_xyz'],source_cell=j['source_cell'],true_region=j['true_region'],continuous_ppm_available=True,role='independent_new_observation')
dump(root/'OBSERVATION_REGISTRY.json',registry);dump(CORE/'evaluation_only/FUTURE_TRUTH.json',truth);print(json.dumps(run(root,CORE/'future_inference')))
calc=CORE/'future_inference';arr=np.load(calc/'FULL_SOURCE_POSTERIORS.npz');stage=HOST/'future_metrics';stage.mkdir();jobs=[]
for row in load(calc/'RESULT_INDEX.json'):
 key=row['key'];p=stage/(key+'.f64');arr[key+'_posterior'].astype('<f8').tofile(p);jobs.append(dict(id=key,path=DATA+'/future_metrics/'+p.name))
for ob in registry:
 a=np.load(root/ob['folder']/'N0_FROZEN_POSTERIORS.npz')
 for n in [20,35,50]:
  key=f'{ob["oid"]}__N0__{n}';p=stage/(key+'.f64');a[f'p{n}'].astype('<f8').tofile(p);jobs.append(dict(id=key,path=DATA+'/future_metrics/'+p.name))
wc(stage/'JOBS.csv',jobs)
code="""import subprocess,os,json,time
from pathlib import Path
d=Path(%r);env=dict(os.environ,OMP_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads(Path('/home/zyc/ros2_ws/pmfs_native_mechanism_closure_r1_20261011/ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH']);st=time.monotonic()
p=subprocess.run(['/dev/shm/pmfs_r2/native_build/native_batch_entry','posterior_metrics',%r+'/inputs/R0',str(d/'JOBS.csv'),str(d/'native_metrics')],env=env,capture_output=True,timeout=240);(d/'metrics.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0;print(json.dumps(dict(status='PASS_NATIVE_FUTURE288_METRICS',wall_s=time.monotonic()-st)))
"""%(DATA+'/future_metrics',REMOTE)
print(remote(code,'future288_native_coordinate_metrics',300));shutil.copy2(stage/'native_metrics/METRICS.csv',calc/'NATIVE_POSITION_METRICS.csv')
# Apply the exact already-frozen evaluator to a separate destination; no development output is overwritten.
src=(WORK/'evaluate_development.py').read_text().replace("root=CORE/'inference_inputs';folder=CORE/'development_inference';truth=load(CORE/'evaluation_only/DEVELOPMENT_TRUTH.json')","root=CORE/'future_inference_inputs';folder=CORE/'future_inference';truth=load(CORE/'evaluation_only/FUTURE_TRUTH.json')")
src=src.replace("CORE/'PAIRED_SOURCE_METRICS.csv'","CORE/'FUTURE_PAIRED_SOURCE_METRICS.csv'").replace("CORE/'READOUT_PAIRED_EFFECTS.csv'","CORE/'FUTURE_READOUT_PAIRED_EFFECTS.csv'").replace("CORE/'DEVELOPMENT_GATE_RESULT.json'","CORE/'FUTURE_DESCRIPTIVE_EFFECT_SUMMARY.json'").replace("CORE/'DEVELOPMENT_ALL_HEAD_SUMMARY.json'","CORE/'FUTURE_ALL_HEAD_SUMMARY.json'")
exec(compile(src,'same_frozen_evaluation_future','exec'))
g=load(CORE/'FUTURE_DESCRIPTIVE_EFFECT_SUMMARY.json');harm=[r for r in rows(CORE/'FUTURE_READOUT_PAIRED_EFFECTS.csv') if r['blocks']=='50' and r['new_wrong_MAP_region']=='True'];passed=g['mean_NLL_delta']<0 and g['improved_source_groups']>=2 and g['source_equal_mean_top5_delta']<=1e-10 and not harm
dump(CORE/'FUTURE_CONFIRMATION_DECISION.json',dict(status='DESCRIPTIVE_CONFIRMATION_PASS' if passed else 'DESCRIPTIVE_CONFIRMATION_NOT_MET_END_THIS_CONSTRUCTION',all_six_retained=True,registered_source_groups=3,mean_region_NLL_delta=g['mean_NLL_delta'],improved_source_groups=g['improved_source_groups'],source_equal_mean_nativeTop5_delta=g['source_equal_mean_top5_delta'],new_wrong_MAP_cases=[r['oid'] for r in harm],no_more_seeds_or_retuning=True,not_publishable_sample_size=True,no_cross_environment_claim=True))
print(json.dumps(load(CORE/'FUTURE_CONFIRMATION_DECISION.json')))
