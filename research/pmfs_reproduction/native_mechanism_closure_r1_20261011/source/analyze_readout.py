from common_n import *
import numpy as np,csv,math,io,shutil
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');R=D/'readout';ledger=load(R/'READOUT_LEDGER.json');assert ledger['status'].startswith('PASS')
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 p=Path(p);p.parent.mkdir(exist_ok=True,parents=True)
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
def rpath(p):return DATA+'/'+str(Path(p).relative_to(D)).replace('\\','/')
out=D/'readout_scores';out.mkdir(exist_ok=False);sources=['C7','K2','B000','B001','B002'];predmeta=[];rawaudit=[];candidateevents={}
for schedule in ['B4','PUBLIC_B']:
 for group,ids in [('R01',[0,1]),('R23',[2,3]),('R0123',[0,1,2,3]),('R0',[0]),('R1',[1])]:
  for c in sources:
   folders=[R/f'{schedule}_{c}_{i}' for i in ids];event=np.array([[float(r['event_hit']) for r in rows(f/'EVENTS_O1.csv')] for f in folders]);candidateevents[schedule,group,c]=event.mean(0)
   for method in ['O0','O1','A1']:
    paths=[f/f'native_blur/{method}/blurred.f32' if method!='A1' else f/'A1.f32' for f in folders]
    a=np.mean([np.fromfile(p,dtype='<f4') for p in paths],axis=0).astype('<f4');dest=out/f'{schedule}_{group}_{c}_{method}.f32';a.tofile(dest)
    predmeta.append(dict(id=f'{schedule}_{group}_{c}_{method}',schedule=schedule,group=group,candidate=c,method=method,path=rpath(dest),SHA256=sha(dest)))
    if method!='A1':
     for f in folders:
      p=load(f/f'native_blur/{method}/PRECLAMP.json');raw=np.fromfile(f/f'native_blur/{method}/preclamp.f32',dtype='<f4')
      rawaudit.append(dict(bank=f.name,method=method,above_one=p['above_one'],below_zero=p['below_zero'],minimum=float(raw.min()),maximum=float(raw.max())))
wc(CORE/'PRECLAMP_AUDIT.csv',rawaudit);dump(CORE/'READOUT_PREDICTIONS_FREEZE_BEFORE_OBS_TRUTH.json',predmeta)
jobs=[]
for oid,schedule in [('B4','B4')]+[(r['oid'],'PUBLIC_B') for r in load(CORE/'DERIVED_NATIVE_TASKS.json')]:
 inp=out/('input_'+oid);inp.mkdir()
 if oid=='B4':
  source=CORE/'native_inputs/inputs/B4';shutil.copyfile(source/'input.csv',inp/'input.csv')
 else:
  source=CORE/'native_inputs/inputs/DERIVED';shutil.copyfile(D/f'native_results/N0_{oid}/final_map.csv',inp/'input.csv')
 for n in ['metadata.csv','settings.csv']:shutil.copyfile(source/n,inp/n)
 selected=[r for r in predmeta if r['schedule']==schedule];wc(inp/'jobs.csv',[dict(id=r['id'],path=r['path']) for r in selected])
 jobs.append(dict(oid=oid,schedule=schedule,input=rpath(inp),payload=rpath(inp/'jobs.csv'),output=rpath(out/('scores_'+oid))))
dump(CORE/'READOUT_SCORING_TASKS.json',jobs)
code='''from pathlib import Path
import json,subprocess,os,time
t=Path(REMOTE);jobs=JOBS;env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads((t/'ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH'])
rs=[]
for job in jobs:
 start=time.time();p=subprocess.run([str(t/'native_entry'),'score',job['input'],job['payload'],job['output']],env=env,capture_output=True,text=True,timeout=30)
 assert p.returncode==0,(job,p.stderr);rs.append(dict(oid=job['oid'],wall_s=time.time()-start))
print(json.dumps({'status':'PASS_ACTUAL_NATIVE_SCORER_ALL13','tasks':rs}))
'''.replace('REMOTE',repr(REMOTE)).replace('JOBS',repr(jobs))
receipt=json.loads(run_remote(code,'B_same_scorer_native_comparisons',180));dump(CORE/'READOUT_SCORING_EXECUTION.json',receipt)
scores=[];cells=[];source_pred={r['id']:r for r in predmeta};maximum=0;regular=[]
for job in jobs:
 inp=out/('input_'+job['oid']);m=rows(inp/'input.csv');p=np.array([float(r['probability']) if 'probability' in r else 1-1/(1+math.exp(float(r['logOdds']))) for r in m]);conf=np.array([float(r['confidence']) for r in m]);free=np.array([r['occupancy']=='1' for r in m]);native=rows(out/('scores_'+job['oid'])/'scores.csv')
 observed_events=rows(CORE/'native_inputs/events'/f'{job["oid"]}.csv') if job['oid']!='B4' else rows(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/observation_lineage/MAP_REPLAY_EVENT_COVARIATES.csv')
 y=np.array([int(r.get('event_hit',r.get('observed_event'))) for r in observed_events])
 for r in native:
  meta=source_pred[r['id']];a=np.fromfile(out/(r['id']+'.f32'),dtype='<f4').astype(float);contribution=np.log(1-.4*np.abs(p-a)*conf);value=math.fsum(contribution[free]);maximum=max(maximum,abs(value-float(r['log_score'])));assert maximum<1e-10
  q=candidateevents[job['schedule'],meta['group'],meta['candidate']]
  scores.append(dict(oid=job['oid'],schedule=job['schedule'],group=meta['group'],candidate=meta['candidate'],method=meta['method'],native_log_similarity=float(r['log_score']),independent_log_similarity=value,receptor_Brier_O1=float(np.mean((q-y)**2)),classification='POINT_SOURCE_RESTRICTED_FIVE_DIAGNOSTIC_NOT_FULL_N0'))
  for i in np.flatnonzero(free):cells.append(dict(oid=job['oid'],group=meta['group'],candidate=meta['candidate'],method=meta['method'],cell=int(i),observed_probability=p[i],confidence=conf[i],prediction=a[i],log_factor=contribution[i]))
 for group in ['R01','R23','R0123','R0','R1']:
  for c in sources:
   q=candidateevents[job['schedule'],group,c];regular.append(dict(oid=job['oid'],group=group,candidate=c,ordinary_event_log_similarity=math.fsum(np.log(1-.4*np.abs(y-q))),Brier=float(np.mean((q-y)**2)),blocks=50,stops=10,independence_claim=False))
wc(CORE/'SAME_BANK_READOUT_CONTRASTS.csv',scores);wc(CORE/'POINT_CANDIDATE_CELL_SCORE_CONTRIBUTIONS.csv',cells);wc(CORE/'ORDINARY_EVENT_BASELINE.csv',regular)
dump(CORE/'B_NATIVE_SCORER_INDEPENDENT_VERIFY.json',dict(status='PASS',maximum_abs_log_difference=maximum,objects=len(scores),scalar_cells=len(cells),new_gas=0))
# Truth begins here, after candidate fields and native scores are preserved.
truth=load(CORE/'evaluation_only/PUBLIC_TASK_TRUTH.json');evalrows=[];pairs=[]
for oid in [j['oid'] for j in jobs]:
 true='C7' if oid=='B4' else truth[oid]['candidate_id'].replace('candidate_B_','B')
 for group in ['R01','R23','R0123','R0','R1']:
  for method in ['O0','O1','A1']:
   ss=[r for r in scores if r['oid']==oid and r['group']==group and r['method']==method];by={r['candidate']:r for r in ss};assert true in by
   best=max(ss,key=lambda x:x['native_log_similarity']);topwrong=max((r for r in ss if r['candidate']!=true),key=lambda x:x['native_log_similarity']);margin=by[true]['native_log_similarity']-topwrong['native_log_similarity']
   evalrows.append(dict(oid=oid,true_candidate=true,group=group,method=method,selected=best['candidate'],top1_correct=best['candidate']==true,true_minus_bestwrong=margin,receptor_Brier_true=by[true]['receptor_Brier_O1']))
   for c in sources:
    if c!=true:pairs.append(dict(oid=oid,true_candidate=true,wrong_candidate=c,group=group,method=method,true_minus_wrong=by[true]['native_log_similarity']-by[c]['native_log_similarity']))
wc(CORE/'MAP_OPERATOR_CONTRASTS.csv',evalrows);wc(CORE/'PAIRWISE_LOG_MARGINS.csv',pairs)
dump(CORE/'FULL_VS_RESTRICTED_SCOPE.json',dict(N0='447 legal cells, actual adaptive native history',point_readout='5 fixed point hypotheses; native similarity comparator; not PMFS full map',full_map_treatment='FULL_MAP_TREATMENT_NOT_TESTED',no_new_method_gain_claim=True))
print(json.dumps({'status':'PASS_B_SCORER','maximum_scalar_difference':maximum,'R01_top1':{method:sum(r['top1_correct'] for r in evalrows if r['group']=='R01' and r['method']==method) for method in ['O0','O1','A1']}}))
