"""Ordinary three-source comparisons; freeze one task before DEV decoding."""
import itertools,json,csv,time,sys
import numpy as np
from protocol import *
from analyze_train import make_features,METHODS,score

def csvout(name,rows):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def load(stage):
 r=json.loads((OUT/(stage.upper()+'_EXTRACTION.json')).read_text());arrays=[]
 for w in r['worlds']:
  assert sha(OUT/w['file'])==w['sha256']
  with np.load(OUT/w['file']) as z:arrays.append(z['values_ppm'])
 return np.array(arrays).reshape(3,2,len(r['times_s']),len(r['probe_ranks'])),np.array(r['times_s']),r
def classify(d):
 ties=np.sum(np.abs(d-d.min(axis=-1,keepdims=True))<=1e-12*np.maximum(1,np.max(np.abs(d),axis=-1,keepdims=True)),axis=-1)>1
 pred=np.argmin(d,axis=-1).astype(np.int8);return np.where(ties,-1,pred).astype(np.int8)
def cross(x,unknown):
 ds=[];truth=np.repeat(np.arange(3),2)
 for s in range(3):
  for r in range(2):ds.append(np.stack([score(x[s,r],x[k,1-r],unknown) for k in range(3)],axis=-1))
 d=np.array(ds);pred=classify(d)
 other=np.array([np.min(np.delete(d[w],truth[w],axis=-1),axis=-1) for w in range(6)])
 own=np.array([d[w,:,truth[w]] for w in range(6)])
 margin=(other-own)/np.maximum(np.sum(np.abs(d),axis=-1),1e-12)
 return pred,margin
def train():
 started=time.perf_counter();c=config();values,times,receipt=load('train');assert not (OUT/'SELECTION_FREEZE.json').exists()
 pairs=np.array(list(itertools.combinations(range(30),2)))
 pp=c['all_probe_pools'];pos=np.array([[float(p['center_x_m']),float(p['center_y_m']),float(p['z_m'])] for p in pp])
 sep=np.linalg.norm(pos[pairs[:,0]]-pos[pairs[:,1]],axis=-1);eligible=(sep>=.3)&(sep<=2.)
 truth=np.repeat(np.arange(3),2);candidates=[];rows=[];global_rows=[];results=[];margins=[]
 for anchor in c['window_anchors_s']:
  idx=np.flatnonzero((times>=anchor)&(times<=anchor+20));t=times[idx];v=values[:,:,idx,:]
  ps=[];ms=[]
  for known in (True,False):
   f=make_features(v,t,pairs,known);preds=[];mars=[]
   for method in METHODS:
    if not known and 'hitfraction' in method:pred=np.full((6,len(pairs)),-2,dtype=np.int8);margin=np.full((6,len(pairs)),np.nan)
    else:pred,margin=cross(f[method],not known)
    preds.append(pred);mars.append(margin)
   ps.append(np.array(preds));ms.append(np.array(mars))
  pred=np.array(ps);margin=np.array(ms);correct=(pred==truth[None,None,:,None]).sum(axis=2)
  same=np.c_[np.arange(30),np.arange(30)];gf=make_features(v,t,same,True);singles=[]
  for method,priority in [('single_L_mean',0),('single_L_hitfraction',1),('single_L_full',2)]:
   sp,sm=cross(gf[method],False);counts=(sp==truth[:,None]).sum(axis=0)
   for p in range(30):
    item={'anchor_s':anchor,'probe_rank':p+1,'method':method,'strict_correct':int(counts[p]),'worst_margin':float(sm[:,p].min()),'priority':priority}
    singles.append(item);global_rows.append(item)
  singles.sort(key=lambda x:(-x['strict_correct'],-x['worst_margin'],x['priority'],x['probe_rank']));best=singles[0]
  for k,(i,j) in enumerate(pairs):
   row={'anchor_s':anchor,'probe_L':int(i+1),'probe_R':int(j+1),'separation_m':float(sep[k]),'eligible':bool(eligible[k]),
    'strongest_global_single_TRAIN_correct':best['strict_correct'],'equal_budget_dual_increment':int(correct[0,7,k])-best['strict_correct']}
   for a,prefix in enumerate(('known','unknown_gain')):
    for m,method in enumerate(METHODS):
     row[prefix+'__'+method]=int(correct[a,m,k]) if not(a==1 and 'hitfraction' in method) else 'NOT_APPLICABLE'
   rows.append(row)
   if eligible[k]:candidates.append({'anchor_s':anchor,'window_indices':idx.tolist(),'probe_L':int(i+1),'probe_R':int(j+1),
    'distance_m':float(sep[k]),'global_single':best,'TRAIN_dual_correct':int(correct[0,7,k]),
    'TRAIN_increment':int(correct[0,7,k])-best['strict_correct'],'worst_margin':float(margin[0,7,:,k].min())})
  results.append(pred);margins.append(margin)
 candidates.sort(key=lambda x:(-x['TRAIN_increment'],-x['TRAIN_dual_correct'],-x['worst_margin'],x['distance_m'],x['anchor_s'],x['probe_L'],x['probe_R']))
 selected=candidates[0];csvout('TRAIN_PAIR_WINDOWS.csv',rows);csvout('TRAIN_GLOBAL_SINGLE.csv',global_rows)
 target=OUT/'TRAIN_CLASSIFICATIONS.npz';np.savez_compressed(target,predictions=np.array(results),margins=np.array(margins),pairs=pairs,truth=truth,anchors=np.array(c['window_anchors_s']))
 write('SELECTION_FREEZE.json',{'status':'ONE_PAIR_AND_STRONG_GLOBAL_SINGLE_FROZEN','selected':selected,
 'protocol_sha256':sha(OUT/'PROTOCOL.json'),'analysis_code_sha256':sha(__file__),'classification_sha256':sha(target),
 'TRAIN_arrays':receipt['worlds'],'DEV_numeric_responses_seen':0,'M1_not_used':True,
 'TRAIN_positive_increment_pair_windows':sum(r['eligible'] and r['equal_budget_dual_increment']>0 for r in rows),
 'all_windows_have_saturated_global_single':all(max(r['strict_correct'] for r in global_rows if r['anchor_s']==a)==6 for a in c['window_anchors_s']),
 'wall_s':time.perf_counter()-started})
 # Fit only ordinary source prototypes from the two TRAIN worlds, no tuning.
 idx=np.array(selected['window_indices']);pair=np.array([[selected['probe_L']-1,selected['probe_R']-1]])
 model={};v=values[:,:,idx,:];t=times[idx]
 for known,prefix in ((True,'known'),(False,'unknown_gain')):
  features=make_features(v,t,pair,known)
  for method,x in features.items():
   if not known and 'hitfraction' in method:continue
   model[prefix+'__'+method]=x[:,:,0].mean(axis=1)
  p=selected['global_single']['probe_rank']-1;method=selected['global_single']['method']
  f=make_features(v,t,np.array([[p,p]]),known)
  if known or 'hitfraction' not in method:model[prefix+'__strongest_global_single']=f[method][:,:,0].mean(axis=1)
 np.savez_compressed(OUT/'FROZEN_ORDINARY_MODELS.npz',**model)
 write('MODEL_FREEZE.json',{'status':'FROZEN_BEFORE_DEV','selection_sha256':sha(OUT/'SELECTION_FREEZE.json'),
 'model_sha256':sha(OUT/'FROZEN_ORDINARY_MODELS.npz'),'analysis_code_sha256':sha(__file__),
 'training_unit':'six physical worlds grouped into two shared-master-seed groups; no frame splitting',
 'thresholds_changed':False,'DEV_evaluation_count_allowed':1})
 print('TRAIN_SELECTION_AND_MODELS_FROZEN',json.dumps(selected),flush=True)

def evaluate():
 started=time.perf_counter();assert not (OUT/'DEV_RESULT.json').exists()
 freeze=json.loads((OUT/'MODEL_FREEZE.json').read_text());assert sha(__file__)==freeze['analysis_code_sha256']
 assert sha(OUT/'FROZEN_ORDINARY_MODELS.npz')==freeze['model_sha256']
 s=json.loads((OUT/'SELECTION_FREEZE.json').read_text())['selected'];values,t,receipt=load('dev');ranks=receipt['probe_ranks']
 pair=np.array([[ranks.index(s['probe_L']),ranks.index(s['probe_R'])]])
 rows=[];xy=np.array(config()['source_xyz_m'])[:,:2]
 with np.load(OUT/'FROZEN_ORDINARY_MODELS.npz') as model:
  for known,prefix in ((True,'known'),(False,'unknown_gain')):
   features=make_features(values,t,pair,known)
   p=ranks.index(s['global_single']['probe_rank']);method=s['global_single']['method']
   features['strongest_global_single']=make_features(values,t,np.array([[p,p]]),known)[method]
   for method,x in features.items():
    key=prefix+'__'+method
    if key not in model:continue
    mu=model[key]
    for source in range(3):
     for rep in range(2):
      y=x[source,rep,0];d=np.array([score(y,m,not known) for m in mu]);pred=int(classify(d))
      others=np.delete(d,source);margin=float((others.min()-d[source])/max(abs(d).sum(),1e-12))
      rows.append({'scope':prefix,'method':method,'world_id':receipt['worlds'][2*source+rep]['run_id'],
       'true_source':('A','B','C')[source],'predicted_source':('A','B','C')[pred] if pred>=0 else 'TIE',
       'strict_correct':pred==source,'tie':pred<0,'score_A':float(d[0]),'score_B':float(d[1]),'score_C':float(d[2]),
       'normalized_true_margin':margin,'xy_error_m':float(np.linalg.norm(xy[pred]-xy[source])) if pred>=0 else None})
 csvout('DEV_PER_WORLD.csv',rows);summary=[]
 for scope,method in sorted(set((r['scope'],r['method']) for r in rows)):
  sub=[r for r in rows if r['scope']==scope and r['method']==method];bc=[r for r in sub if r['true_source']!='A']
  summary.append({'scope':scope,'method':method,'strict_correct':sum(r['strict_correct'] for r in sub),
  'ties':sum(r['tie'] for r in sub),'BC_correct':sum(r['strict_correct'] for r in bc),
  'A_correct':sum(r['strict_correct'] for r in sub if r['true_source']=='A'),
  'mean_xy_error_non_tie_m':float(np.mean([r['xy_error_m'] for r in sub if not r['tie']])) if any(not r['tie'] for r in sub) else None})
 csvout('DEV_SUMMARY.csv',summary)
 write('DEV_RESULT.json',{'status':'ONE_FROZEN_DEVELOPMENT_CHECK_COMPLETE','selected':s,'summary':summary,
 'worlds':receipt['worlds'],'wall_s':time.perf_counter()-started,'population_precision_not_claimed':True,
 'A_DEV_controls_previously_open':True,'B_C_DEV_not_used_for_selection':True,'M1_M2_M3_or_ROS_not_run':True})
 print('ONE_FROZEN_DEV_COMPLETE',json.dumps(summary),flush=True)

if __name__=='__main__':
 if sys.argv[1:]==['train']:train()
 elif sys.argv[1:]==['dev']:evaluate()
 else:raise SystemExit('train|dev')
