from common_n import *
import csv,numpy as np,math
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');ledger=load(D/'C_readout/READOUT_LEDGER.json');assert ledger['status'].startswith('PASS');assert load(D/'factorial/GAS_LEDGER.json')['status']=='PASS_THIRTY_SAME_ENGINE_COUNTERFACTUAL_BANKS'
out=D/'C_scores';out.mkdir(exist_ok=False);sources=['C7','K2','B000','B001','B002'];pred=[];receivers={};eventsraw={}
for schedule in ['B4','PUBLIC_B']:
 for d,v in [(0,0),(0,1),(1,0),(1,1)]:
  cond=f'D{d}V{v}'
  for cid in sources:
   dirs=[D/'readout'/f'{schedule}_{cid}_{i}' if cond=='D1V1' else D/'C_readout'/f'{schedule}_{cid}_{i}_{cond}' for i in [0,1]]
   ee=np.array([[float(r['event_hit']) for r in rows(folder/'EVENTS_O1.csv')] for folder in dirs]);eventsraw[schedule,cond,cid]=ee
   for group,index in [('R0',[0]),('R1',[1]),('R01',[0,1])]:
    receivers[schedule,cond,group,cid]=ee[index].mean(0)
    for method in ['O0','O1','A1']:
     paths=[dirs[i]/f'native_blur/{method}/blurred.f32' if method!='A1' else dirs[i]/'A1.f32' for i in index];a=np.mean([np.fromfile(p,dtype='<f4') for p in paths],axis=0).astype('<f4');pid=f'{schedule}_{cond}_{group}_{cid}_{method}';p=out/(pid+'.f32');a.tofile(p);pred.append(dict(id=pid,schedule=schedule,condition=cond,group=group,candidate=cid,method=method,path=DATA+'/C_scores/'+p.name,SHA256=sha(p)))
dump(CORE/'C_PREDICTIONS_FREEZE.json',pred)
tasks=[]
for oid,schedule in [('B4','B4')]+[(r['oid'],'PUBLIC_B') for r in load(CORE/'DERIVED_NATIVE_TASKS.json')]:
 jobs=out/(oid+'_jobs.csv');wc(jobs,[dict(id=r['id'],path=r['path']) for r in pred if r['schedule']==schedule]);tasks.append(dict(oid=oid,schedule=schedule,input=DATA+'/readout_scores/input_'+oid,payload=DATA+'/C_scores/'+jobs.name,output=DATA+'/C_scores/scores_'+oid))
code='''from pathlib import Path
import os,json,subprocess
t=Path(REMOTE);env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads((t/'ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH'])
for j in JOBS:
 p=subprocess.run([str(t/'native_entry'),'score',j['input'],j['payload'],j['output']],env=env,capture_output=True,text=True,timeout=60);assert p.returncode==0,p.stderr
print(json.dumps({'status':'PASS_SAME_NATIVE_SCORER_C_FACTORIAL','objects':2340,'new_forwards':0}))
'''.replace('REMOTE',repr(REMOTE)).replace('JOBS',repr(tasks))
receipt=json.loads(run_remote(code,'C_all_four_cells_native_scoring',240));dump(CORE/'C_NATIVE_SCORER_EXECUTION.json',receipt)
lookup={r['id']:r for r in pred};scores=[];maximum=0
for task in tasks:
 m=rows(D/'readout_scores'/('input_'+task['oid'])/'input.csv');pr=np.array([float(r['probability']) if 'probability' in r else 1-1/(1+math.exp(float(r['logOdds']))) for r in m]);conf=np.array([float(r['confidence']) for r in m]);free=np.array([r['occupancy']=='1' for r in m]);
 for r in rows(out/('scores_'+task['oid'])/'scores.csv'):
  info=lookup[r['id']];q=np.fromfile(out/(r['id']+'.f32'),dtype='<f4').astype(float);value=math.fsum(np.log(1-.4*np.abs(pr-q)*conf)[free]);maximum=max(maximum,abs(value-float(r['log_score'])));assert maximum<1e-10
  scores.append(dict(oid=task['oid'],schedule=task['schedule'],condition=info['condition'],group=info['group'],candidate=info['candidate'],method=info['method'],native_log_similarity=float(r['log_score']),independent_log_similarity=value))
wc(CORE/'SAME_ENGINE_FACTORIAL_SOURCE_SCORES.csv',scores)
truth=load(CORE/'evaluation_only/PUBLIC_TASK_TRUTH.json');pairs=[];metrics=[];classification=[]
for task in tasks:
 oid,schedule=task['oid'],task['schedule'];true='C7' if oid=='B4' else truth[oid]['candidate_id'].replace('candidate_B_','B')
 obs=rows(CORE/f'native_inputs/events/{oid}.csv') if oid!='B4' else rows(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/observation_lineage/MAP_REPLAY_EVENT_COVARIATES.csv');y=np.array([int(r.get('event_hit',r.get('observed_event'))) for r in obs])
 for group in ['R0','R1','R01']:
  for method in ['O0','O1','A1']:
   margins={}
   for cond in ['D0V0','D0V1','D1V0','D1V1']:
    s=[r for r in scores if r['oid']==oid and r['group']==group and r['method']==method and r['condition']==cond];by={r['candidate']:r['native_log_similarity'] for r in s};top=max(by.values());selected=[c for c,z in by.items() if top-z<=1e-12]
    classification.append(dict(oid=oid,condition=cond,group=group,method=method,selected=','.join(selected),tied_max_count=len(selected),unique_top1_correct=len(selected)==1 and selected[0]==true,true_minus_bestwrong=by[true]-max(z for c,z in by.items() if c!=true)))
    margins[cond]={c:by[true]-by[c] for c in sources if c!=true}
    if method=='O1':
     p=receivers[schedule,cond,group,true];metrics.append(dict(oid=oid,true_candidate=true,condition=cond,group=group,receptor_Brier=float(np.mean((p-y)**2)),blocks=50,independence_unit='whole realization, not block'))
   for wrong in sources:
    if wrong==true:continue
    m00,m01,m10,m11=[margins[c][wrong] for c in ['D0V0','D0V1','D1V0','D1V1']]
    pairs.append(dict(oid=oid,true_candidate=true,wrong_candidate=wrong,group=group,method=method,m00=m00,m01=m01,m10=m10,m11=m11,D_at_V0=m10-m00,D_at_V1=m11-m01,V_at_D0=m01-m00,V_at_D1=m11-m10,interaction=m11-m10-m01+m00,no_unique_native_PMFS_root_claim=True))
wc(CORE/'CONTROLLED_FACTORIAL_CONTRASTS.csv',pairs);wc(CORE/'FACTORIAL_RECEPTOR_METRICS.csv',metrics);wc(CORE/'FACTORIAL_RESTRICTED_SOURCE_RESULTS.csv',classification)
dump(CORE/'C_INDEPENDENT_SCALAR_VERIFICATION.json',dict(status='PASS',maximum_logscore_abs=maximum,complete_four_cell_contrasts=len(pairs),actual_engine_differences='D0 additionalnav constraint; V0 cancel vertical motion, all three Gaussian draws still consumed',matched_CFDSolved_new_environment=False))
print(json.dumps({'status':'PASS_C_ALL4_CONTRASTS','max_abs':maximum,'B4_O1_R01':[r for r in classification if r['oid']=='B4' and r['group']=='R01' and r['method']=='O1']}))
