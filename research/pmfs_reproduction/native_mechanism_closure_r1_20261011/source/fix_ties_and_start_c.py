from common_n import *
import csv,numpy as np,math
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
scores=rows(CORE/'SAME_BANK_READOUT_CONTRASTS.csv');old=rows(CORE/'MAP_OPERATOR_CONTRASTS.csv');fixed=[]
for r in old:
 ss=[s for s in scores if all(s[k]==r[k] for k in ['oid','group','method'])];maxval=max(float(s['native_log_similarity']) for s in ss)
 top=[s['candidate'] for s in ss if maxval-float(s['native_log_similarity'])<=1e-12]
 r['selected']='TIE:'+','.join(top) if len(top)>1 else top[0];r['top1_correct']=len(top)==1 and top[0]==r['true_candidate'];r['true_among_tied_max']=r['true_candidate'] in top;r['tied_max_count']=len(top);fixed.append(r)
wc(CORE/'MAP_OPERATOR_CONTRASTS.csv',fixed)
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');R=D/'readout';metrics=[]
truth=load(CORE/'evaluation_only/PUBLIC_TASK_TRUTH.json')
for oid in ['B4']+list(truth):
 schedule='B4' if oid=='B4' else 'PUBLIC_B';source='C7' if oid=='B4' else truth[oid]['candidate_id'].replace('candidate_B_','B')
 observed=rows(CORE/f'native_inputs/events/{oid}.csv') if oid!='B4' else rows(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/observation_lineage/MAP_REPLAY_EVENT_COVARIATES.csv')
 y=np.array([int(x.get('event_hit',x.get('observed_event'))) for x in observed])
 for rep in [0,1,2,3]:
  folder=R/f'{schedule}_{source}_{rep}';ev=rows(folder/'EVENTS_O1.csv')
  with np.load(folder/'READOUT_FIELDS.npz',allow_pickle=False) as z:
   indices=[int(np.floor((float(e['x'])-float(np.float32(-7.55)))/.25))+34*int(np.floor((float(e['y'])-float(np.float32(-7.88)))/.25)) for e in ev]
   o0=np.array([z['O0'][i,k] for i,k in enumerate(indices)]);o1=np.array([int(e['event_hit']) for e in ev])
  for name,p in [('O0_center_cell_proxy',o0),('O1_PID',o1)]:metrics.append(dict(oid=oid,source=source,replicate=rep,method=name,Brier=float(np.mean((p-y)**2)),false_positive=int(np.sum((p==1)&(y==0))),false_negative=int(np.sum((p==0)&(y==1))),events=50,stops=10))
wc(CORE/'RECEPTOR_READOUT_PREDICTION_METRICS.csv',metrics)
dump(CORE/'TIE_HANDLING_CORRECTION.json',dict(reason='Exact same candidate map predictions must be recorded as ties, not source-order wins',tolerance=1e-12,raw_scores_unchanged=True,R01_top1_unique={m:sum(r['top1_correct'] for r in fixed if r['group']=='R01' and r['method']==m) for m in ['O0','O1','A1']},R01_ties={m:sum(r['tied_max_count']>1 for r in fixed if r['group']=='R01' and r['method']==m) for m in ['O0','O1','A1']}))
ledger=load(D/'factorial/GAS_LEDGER.json');assert ledger['status']=='PASS_TWO_FULL_OFF_ANCHORS'
gate=dict(status='GO_SAME_ENGINE_FACTORIAL',full_OFF_anchors_pass=2,readout_bank_tasks_pass=40,
 reason='Readout correction explains restricted B4 proxy flip but native full-grid public tasks include poor source rankings where restricted original-physics O0 already identifies sources; O alone cannot establish the native bridge. Test registered extra nav-domain and vertical-state interaction.',
 not_L_rescue=True,native_unique_root_not_assumed=True,prohibited_new_source_seed_threshold=False)
dump(CORE/'C_ENTRY_GATE.json',gate)
code=r'''from pathlib import Path
import subprocess,os,json
t=Path(REMOTE);d=Path(DATA)/'factorial';assert json.loads((d/'GAS_LEDGER.json').read_text())['status']=='PASS_TWO_FULL_OFF_ANCHORS'
env=os.environ.copy();env['NMC_CAMPAIGN_MODE']='FACTORIAL'
p=subprocess.Popen(['python3',str(t/'factorial_worker.py')],env=env,stdout=(t/'factorial30.stdout').open('w'),stderr=(t/'factorial30.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'new_factorial_calls':30,'full_OFF_pass':2}))
'''.replace('REMOTE',repr(REMOTE)).replace('DATA',repr(DATA))
r=json.loads(run_remote(code,'start_factorial30_after_OFF_and_B_gate',45));dump(CORE/'FACTORIAL30_STARTED.json',r);print(json.dumps(r))
