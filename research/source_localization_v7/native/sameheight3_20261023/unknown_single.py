"""Fair unknown-gain single control, independent of the primary known-gain choice."""
import json,sys
import numpy as np
from protocol import *
from analysis import load,cross,classify,csvout
from analyze_train import make_features,score

def fit():
 assert not (OUT/'DEV_EXTRACTION.json').exists()
 assert not (OUT/'UNKNOWN_SINGLE_CONTROL_FREEZE.json').exists()
 selected=json.loads((OUT/'SELECTION_FREEZE.json').read_text())['selected'];v,t,r=load('train')
 idx=np.array(selected['window_indices']);t=t[idx];v=v[:,:,idx]
 feat=make_features(v,t,np.c_[np.arange(30),np.arange(30)],False);truth=np.repeat(np.arange(3),2);rows=[]
 for method in ('single_L_mean','single_L_full'):
  pred,margin=cross(feat[method],True)
  for p in range(30):rows.append({'probe_rank':p+1,'method':method,'strict_correct':int(np.sum(pred[:,p]==truth)),
   'worst_margin':float(margin[:,p].min())})
 rows.sort(key=lambda r:(-r['strict_correct'],-r['worst_margin'],r['method'],r['probe_rank']));best=rows[0]
 mu=feat[best['method']][:,:,best['probe_rank']-1].mean(axis=1);target=OUT/'UNKNOWN_SINGLE_CONTROL_MODEL.npz'
 np.savez_compressed(target,mean=mu)
 write('UNKNOWN_SINGLE_CONTROL_FREEZE.json',{'status':'ADDITIONAL_STRONG_ORDINARY_CONTROL_FROZEN_BEFORE_DEV',
 'selected':best,'all_TRAIN_controls':rows,'model_sha256':sha(target),'code_sha256':sha(__file__),
 'selection_sha256':sha(OUT/'SELECTION_FREEZE.json'),'primary_pair_and_known_single_unchanged':True,
 'reason':'a single picked under known amplitude need not be strongest under unknown amplitude; fit the strong unknown-gain control using TRAIN only, without modifying frozen primary results',
 'not_a_new_mirror_or_retuned_scientific_threshold':True})
 print('UNKNOWN_GAIN_STRONG_SINGLE_FROZEN',json.dumps(best))
def evaluate():
 f=json.loads((OUT/'UNKNOWN_SINGLE_CONTROL_FREEZE.json').read_text());assert sha(__file__)==f['code_sha256']
 assert sha(OUT/'UNKNOWN_SINGLE_CONTROL_MODEL.npz')==f['model_sha256']
 v,t,r=load('dev');p=r['probe_ranks'].index(f['selected']['probe_rank']);method=f['selected']['method']
 x=make_features(v,t,np.array([[p,p]]),False)[method];rows=[]
 with np.load(OUT/'UNKNOWN_SINGLE_CONTROL_MODEL.npz') as q:mu=q['mean']
 for s in range(3):
  for rep in range(2):
   d=np.array([score(x[s,rep,0],m,True) for m in mu]);pred=int(classify(d))
   rows.append({'world_id':r['worlds'][2*s+rep]['run_id'],'source':('A','B','C')[s],
    'prediction':('A','B','C')[pred] if pred>=0 else 'TIE','strict_correct':pred==s,'tie':pred<0,
    'score_A':float(d[0]),'score_B':float(d[1]),'score_C':float(d[2])})
 csvout('UNKNOWN_STRONG_SINGLE_DEV.csv',rows)
 write('UNKNOWN_STRONG_SINGLE_RESULT.json',{'strict_correct':sum(x['strict_correct'] for x in rows),
 'ties':sum(x['tie'] for x in rows),'BC_correct':sum(x['strict_correct'] for x in rows if x['source']!='A'),
 'selected':f['selected'],'primary_frozen_comparison_not_overwritten':True})
 print('UNKNOWN_SINGLE_DEV_COMPLETE',sum(x['strict_correct'] for x in rows))
if __name__=='__main__':
 if sys.argv[1:]==['train']:fit()
 elif sys.argv[1:]==['dev']:evaluate()
 else:raise SystemExit('train|dev')
