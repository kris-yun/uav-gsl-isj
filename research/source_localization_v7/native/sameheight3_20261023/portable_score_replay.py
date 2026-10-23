"""Windows/Linux numerical replay. No DLL, original gas or model refitting.

Normalizes only stored relative path separators in memory; frozen inputs and
metadata stay byte-identical. Native C++ parity is separately recorded by
verify.py on the accepted Windows runtime.
"""
from pathlib import Path
import json,csv,sys
import numpy as np
from protocol import PROJECT,OUT,sha
from analyze_train import make_features
from mirror_shadow import feature_sets
from gsl_discrimination.m1_opponent import OpponentBank,SamplingContract
from gsl_discrimination.m1_opponent.raw_joint import load_observation_model

def read_csv(name):
 with (OUT/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 r=json.loads((OUT/'DEV_EXTRACTION.json').read_text());arrays=[]
 for w in r['worlds']:
  path=OUT/w['file'].replace('\\','/');assert sha(path)==w['sha256']
  with np.load(path) as z:arrays.append(z['values_ppm'])
 t=np.array(r['times_s']);v=np.array(arrays).reshape(3,2,len(t),len(r['probe_ranks']))
 s=json.loads((OUT/'SELECTION_FREEZE.json').read_text())['selected'];ranks=r['probe_ranks']
 pair=np.array([[ranks.index(s['probe_L']),ranks.index(s['probe_R'])]])
 rows=read_csv('DEV_PER_WORLD.csv');checks=0;worst=0.
 with np.load(OUT/'FROZEN_ORDINARY_MODELS.npz') as model:
  for known,prefix in ((True,'known'),(False,'unknown_gain')):
   feats=make_features(v,t,pair,known)
   p=ranks.index(s['global_single']['probe_rank']);method=s['global_single']['method']
   feats['strongest_global_single']=make_features(v,t,np.array([[p,p]]),known)[method]
   for name,x in feats.items():
    key=prefix+'__'+name
    if key not in model:continue
    for source in range(3):
     for rep in range(2):
      y=x[source,rep,0];ref=next(a for a in rows if a['scope']==prefix and a['method']==name and a['world_id']==r['worlds'][2*source+rep]['run_id'])
      for k,m in enumerate(model[key]):
       if known:val=float(np.dot(y-m,y-m)/len(y))
       else:
        gain=max(0.,float(np.dot(y,m)/np.dot(m,m))) if np.dot(m,m)>0 else 0.
        val=float(np.dot(y-gain*m,y-gain*m)/np.dot(y,y)) if np.dot(y,y)>0 else 0.
       error=abs(val-float(ref['score_'+('A','B','C')[k]]));assert error<1e-10
       worst=max(worst,error);checks+=1
 f=json.loads((OUT/'MIRROR_MODEL_FREEZE.json').read_text());bank=OpponentBank.from_dict(f['bank']);contract=SamplingContract(**f['contract'])
 x=v[:,:,:,pair[0]];features=feature_sets(x,t,bank,contract);e,h=bank.extract(x,t,contract)
 for name in ('mother','secondary'):features[name+'_gaussian']=np.concatenate([e[...,None],h[...,f['selection'][name]]],axis=-1)
 order=np.lexsort((x[...,1],x[...,0]),axis=-1)
 features['unordered_mirror_gaussian']=feature_sets(np.take_along_axis(x,order[...,None],axis=-2),t,bank,contract)['frozen_all_mirror_features']
 rows=read_csv('MIRROR_DEV_PER_WORLD.csv');mirror_checks=0;relative_error=0.
 for name in f['Gaussian_heads']:
  with np.load(OUT/'mirror_models'/(name+'.npz')) as q:mu=q['mean'];cov=q['covariance']
  for source in range(3):
   for rep in range(2):
    delta=features[name][source,rep][None]-mu
    solved=np.linalg.solve(cov,delta.T).T
    vals=.5*np.sum(delta*solved,axis=-1)
    ref=next(a for a in rows if a['method']==name and a['world_id']==r['worlds'][2*source+rep]['run_id'])
    for k,val in enumerate(vals):
     expected=float(ref['score_'+('A','B','C')[k]]);err=abs(val-expected)/max(1.,abs(expected))
     assert err<1e-10,(name,err);relative_error=max(relative_error,err);mirror_checks+=1
 for name in ('even','mother','secondary','raw_joint'):
  model=load_observation_model(OUT/'mirror_models'/name)
  for source in range(3):
   for rep in range(2):
    symbol=model.encode(0,x[source,rep],t,contract);vals=-np.log(model.channel.probabilities[0,:,0,symbol])
    ref=next(a for a in rows if a['method']=='original_'+name and a['world_id']==r['worlds'][2*source+rep]['run_id'])
    for k,val in enumerate(vals):assert abs(val-float(ref['score_'+('A','B','C')[k]]))<1e-12;mirror_checks+=1
 print(json.dumps({'status':'PORTABLE_NUMERICAL_REPLAY_PASS','ordinary_source_scores':checks,
 'mirror_source_scores':mirror_checks,'max_ordinary_abs_error':worst,'max_Gaussian_relative_error':relative_error,
 'new_fitting_or_native_gas_or_ROS':False,'frozen_metadata_rewritten':False},indent=2))
if __name__=='__main__':main()
