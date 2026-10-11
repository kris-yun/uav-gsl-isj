from common_n import *
import csv,numpy as np,math,shutil
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,r):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(r[0]),lineterminator='\n');w.writeheader();w.writerows(r)
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');plan=load(CORE/'FRESH_CONFIRMATION_PREREGISTRATION.json');assert load(D/'fresh/GENERATION_LEDGER.json')['status'].startswith('PASS');out=D/'fresh_scores';out.mkdir(exist_ok=False);scores=[];native=[];metric=[];events=[];jobs=[];allmeta=rows(CORE/'native_inputs/inputs/DERIVED/metadata.csv')[0]
free=np.array([r['occupancy']=='1' for r in rows(CORE/'native_inputs/inputs/DERIVED/input.csv')]);x=np.float32(-7.55)+(np.arange(len(free))%34+.5)*.25;y=np.float32(-7.88)+(np.arange(len(free))//34+.5)*.25
for job in plan['jobs']:
 oid=job['oid'];run=D/'native_results'/('FRESH_N0_'+oid);assert (run/'EXECUTION.json').exists(),'fresh native history not complete'
 freeze={p.relative_to(run).as_posix():sha(p) for p in run.rglob('*') if p.is_file()};dump(CORE/'evaluation_only'/(oid+'_FRESH_OUTPUT_FREEZE_BEFORE_METRICS.json'),freeze)
 inp=out/('input_'+oid);inp.mkdir();shutil.copyfile(run/'final_map.csv',inp/'input.csv')
 for n in ['metadata.csv','settings.csv']:shutil.copyfile(CORE/'native_inputs/inputs/DERIVED'/n,inp/n)
 fields=[dict(id=r['candidate']+'_'+r['method'],path=r['path']) for r in plan['references']]
 for cid in ['C7','K2','B000','B001','B002']:fields.append(dict(id=cid+'_N_POINT',path=DATA+'/point_scores/'+cid+'_R01.f32'))
 wc(inp/'score_jobs.csv',fields);jobs.append(dict(oid=oid,input=DATA+'/fresh_scores/input_'+oid,payload=DATA+'/fresh_scores/input_'+oid+'/score_jobs.csv',output=DATA+'/fresh_scores/scores_'+oid))
code='''from pathlib import Path
import os,json,subprocess
t=Path(REMOTE);env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads((t/'ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH'])
for j in JOBS:
 p=subprocess.run([str(t/'native_entry'),'score',j['input'],j['payload'],j['output']],env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
print(json.dumps({'status':'PASS_FROZEN_PREDICTIONS_FRESH6_NATIVE_SCORE','navigation':False,'new_forwards':0}))
'''.replace('REMOTE',repr(REMOTE)).replace('JOBS',repr(jobs))
receipt=json.loads(run_remote(code,'fresh6_frozen_predictors_native_scores',120));dump(CORE/'FRESH_SCORER_EXECUTION.json',receipt);maximum=0
with np.load(D/'confirmation_reference_freeze/FIXED_RECEPTOR_PREDICTIONS.npz',allow_pickle=False) as z:pred={k:z[k].copy() for k in z.files}
results=[]
for job in plan['jobs']:
 oid=job['oid'];truth=job['candidate'];sx,sy=job['source_xyz'][:2];run=D/'native_results'/('FRESH_N0_'+oid);mr=rows(out/('input_'+oid)/'input.csv');p=np.array([float(r['probability']) for r in mr]);confidence=np.array([float(r['confidence']) for r in mr])
 for r in rows(out/('scores_'+oid)/'scores.csv'):
  cid,method=r['id'].split('_',1);ref=next((a for a in plan['references'] if a['candidate']==cid and a['method']==method),None)
  path=D/'confirmation_reference_freeze'/Path(ref['path']).name if ref else D/'point_scores'/f'{cid}_R01.f32';q=np.fromfile(path,dtype='<f4').astype(float);value=math.fsum(np.log(1-.4*abs(p-q)*confidence)[free]);maximum=max(maximum,abs(value-float(r['log_score'])));assert maximum<1e-10
  scores.append(dict(oid=oid,method=method,candidate=cid,native_log_similarity=float(r['log_score']),independent_log_similarity=value))
 for method in ['O0','O1','N_POINT']:
  s=[r for r in scores if r['oid']==oid and r['method']==method];largest=max(r['native_log_similarity'] for r in s);chosen=[r['candidate'] for r in s if largest-r['native_log_similarity']<=1e-12];true_score=next(r['native_log_similarity'] for r in s if r['candidate']==truth);total=sum(math.exp(r['native_log_similarity']-largest) for r in s)
  results.append(dict(oid=oid,true_candidate=truth,method=method,selected=','.join(chosen),unique_top1_correct=len(chosen)==1 and chosen[0]==truth,tied_max_count=len(chosen),true_minus_bestwrong=true_score-max(r['native_log_similarity'] for r in s if r['candidate']!=truth),restricted_true_source_weight=math.exp(true_score-largest)/total,scope='five point hypotheses, not447-cell N0 method gain'))
 qr={r['query_id']:r for r in rows(D/'fresh/realizations'/job['id']/'QUERY_OUTPUT.csv')};rr=[qr[f'b{b}_p{e["pose_id"]}'] for b,e in enumerate(plan['receiver_plan'])];ppm=np.array([np.float32(float(r['ppm_float32'])) for r in rr]);observed=(ppm>np.float32(.1)).astype(int);ci=list(pred['candidate_order']).index(truth)
 for method in ['O0','O1']:metric.append(dict(oid=oid,true_candidate=truth,method=method,Brier=float(np.mean((pred[method][ci]-observed)**2)),MAE_ppm='',RMSE_ppm='',blocks=50,independent_stops=10,realization_unit=True))
 delta=pred['O1_ppm'][ci]-ppm.astype(float)
 metric.append(dict(oid=oid,true_candidate=truth,method='O1_CONTINUOUS_PPM',Brier='',MAE_ppm=float(np.mean(np.abs(delta))),RMSE_ppm=float(np.sqrt(np.mean(delta**2))),blocks=50,independent_stops=10,realization_unit=True))
 for b,e in enumerate(plan['receiver_plan']):events.append(dict(oid=oid,block=b,stop=e['pose_id'],physical_target_s=e['physical_s'],actual_frame=rr[b]['frame'],x=rr[b]['x'],y=rr[b]['y'],z=rr[b]['z'],observed_ppm=float(ppm[b]),observed_hit=int(observed[b]),true_O0_prediction=float(pred['O0'][ci,b]),true_O1_prediction=float(pred['O1'][ci,b]),true_O1_ppm=float(pred['O1_ppm'][ci,b])))
 for lr in rows(run/'update_ledger.csv'):
  u=run/('update_'+lr['update']);post=np.fromfile(u/'posterior.f64',dtype='<f8');dist=np.hypot(x-sx,y-sy);ix=int((np.float32(sx)-np.float32(-7.55))/.25);iy=int((np.float32(sy)-np.float32(-7.88))/.25);index=ix+34*iy
  native.append(dict(oid=oid,source=truth,update=int(lr['update']),blocks=int(lr['blocks']),variance=float(lr['variance']),native_Top5_error_m=math.hypot(float(lr['top5_x'])-sx,float(lr['top5_y'])-sy),MAP_error_m=float(dist[np.argmax(post)]),posterior_mean_error_m=math.hypot(float(lr['mean_x'])-sx,float(lr['mean_y'])-sy),source1m_mass=float(post[dist<=1].sum()),true_cell_rank_mid=float((post[free]>post[index]).sum()+1+((post[free]==post[index]).sum()-1)/2),native_first_variance_convergence=lr['official_rule_first_convergence'],new_official_Action_executed=False))
wc(CORE/'FRESH_RESTRICTED_CANDIDATE_SCORES.csv',scores);wc(CORE/'FRESH_CONFIRMATION_RESULTS.csv',results);wc(CORE/'FRESH_RECEPTOR_PREDICTION_METRICS.csv',metric);wc(CORE/'FRESH_EVENTS_AND_PREDICTIONS.csv',events);wc(CORE/'FRESH_N0_COMPLETE_MAP_RESULTS.csv',native)
dump(CORE/'FRESH_INDEPENDENT_NATIVE_SCORE_VERIFY.json',dict(status='PASS',maximum_scalar_error=maximum,realizations=6,scope='fresh realization replication of readout constituent; no new geometry, not full-map treatment or deployed method'))
print(json.dumps({'status':'PASS_FRESH6','correct_unique':{m:sum(r['unique_top1_correct'] for r in results if r['method']==m) for m in ['O0','O1','N_POINT']},'fresh_N0_updates':len(native)}))
