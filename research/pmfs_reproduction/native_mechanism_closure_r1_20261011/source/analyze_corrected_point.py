from common_n import *
import csv,numpy as np,math
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,r):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(r[0]),lineterminator='\n');w.writeheader();w.writerows(r)
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');out=D/'point_corrected_scores';out.mkdir(exist_ok=False);maps=[];audit=[]
for c in ['C7','K2','B000','B001','B002']:
 a=[]
 for i in [0,1]:
  d=D/f'point_corrected_results/{c}_R{i}/forward';r=rows(d/'candidates.csv')[0];assert r['rng_before']==r['rng_after'];q=np.fromfile(d/r['map_file'],dtype='<f4');a.append(q)
  audit.append(dict(candidate=c,replicate=i,LCG_unchanged_in_native_point_mode=True,Gaussian_phase_before=r['gaussian_index_before'],Gaussian_phase_after=r['gaussian_index_after'],native_point_old_leaf_audit_count=int(r['point_count']),does_not_claim_zero_physical_emissions=True,map_SHA256=sha(d/r['map_file'])))
 for group,values in [('R0',a[:1]),('R1',a[1:]),('R01',a)]:
  p=out/f'{c}_{group}.f32';np.mean(values,axis=0).astype('<f4').tofile(p);maps.append(dict(id=f'{c}_{group}',candidate=c,group=group,path=DATA+'/point_corrected_scores/'+p.name,SHA256=sha(p)))
dump(CORE/'QUALIFIED_N_POINT_PREDICTIONS_FREEZE.json',maps);wc(CORE/'QUALIFIED_N_POINT_RNG_SCOPE.csv',audit)
tasks=[]
for oid in ['B4']+[r['oid'] for r in load(CORE/'DERIVED_NATIVE_TASKS.json')]:
 jobs=out/(oid+'_jobs.csv');wc(jobs,[dict(id=r['id'],path=r['path']) for r in maps]);tasks.append(dict(oid=oid,input=DATA+'/readout_scores/input_'+oid,payload=DATA+'/point_corrected_scores/'+jobs.name,output=DATA+'/point_corrected_scores/scores_'+oid))
code='''from pathlib import Path
import os,json,subprocess
t=Path(REMOTE);env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads((t/'ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH'])
for j in JOBS:
 p=subprocess.run([str(t/'native_entry'),'score',j['input'],j['payload'],j['output']],env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
print(json.dumps({'status':'PASS','tasks':13,'new_forwards':0}))
'''.replace('REMOTE',repr(REMOTE)).replace('JOBS',repr(tasks))
receipt=json.loads(run_remote(code,'point_corrected_similarity_all_observations',120));dump(CORE/'QUALIFIED_N_POINT_SCORE_EXECUTION.json',receipt)
truth=load(CORE/'evaluation_only/PUBLIC_TASK_TRUTH.json');scores=[];results=[]
for j in tasks:
 true='C7' if j['oid']=='B4' else truth[j['oid']]['candidate_id'].replace('candidate_B_','B');raw=rows(out/('scores_'+j['oid'])/'scores.csv')
 for r in raw:
  c,group=r['id'].split('_');scores.append(dict(oid=j['oid'],candidate=c,group=group,method='N_POINT_NATIVE_2D',native_log_similarity=float(r['log_score'])))
 for group in ['R0','R1','R01']:
  s=[r for r in scores if r['oid']==j['oid'] and r['group']==group];best=max(r['native_log_similarity'] for r in s);top=[r['candidate'] for r in s if best-r['native_log_similarity']<=1e-12];mt=next(r['native_log_similarity'] for r in s if r['candidate']==true)-max(r['native_log_similarity'] for r in s if r['candidate']!=true)
  results.append(dict(oid=j['oid'],true_candidate=true,group=group,method='N_POINT_NATIVE_2D',selected=','.join(top),tied_max_count=len(top),top1_correct=len(top)==1 and top[0]==true,true_minus_bestwrong=mt,not_full_map_gain=True))
wc(CORE/'QUALIFIED_N_POINT_NATIVE_SOURCE_SCORES.csv',scores);wc(CORE/'QUALIFIED_N_POINT_DIAGNOSTIC_RESULTS.csv',results)
print(json.dumps({'R01_correct':sum(r['top1_correct'] for r in results if r['group']=='R01'),'B4':[r for r in results if r['oid']=='B4']}))
