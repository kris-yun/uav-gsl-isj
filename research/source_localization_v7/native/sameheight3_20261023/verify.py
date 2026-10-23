"""Independent arithmetic/C++/degeneracy QA. Does not fit or query gas worlds."""
import ctypes as ct,csv,json
import numpy as np
from protocol import *
from analysis import load
from analyze_train import make_features
from gsl_discrimination.m1_opponent.raw_joint import load_observation_model
from gsl_discrimination.m1_opponent.operator import time_weights,_kernel

def main():
 cfg=config();selection=json.loads((OUT/'SELECTION_FREEZE.json').read_text());s=selection['selected']
 for name in ('MODEL_FREEZE.json','MIRROR_MODEL_FREEZE.json','UNKNOWN_SINGLE_CONTROL_FREEZE.json'):
  f=json.loads((OUT/name).read_text())
  source={'MODEL_FREEZE.json':'analysis.py','MIRROR_MODEL_FREEZE.json':'mirror_shadow.py','UNKNOWN_SINGLE_CONTROL_FREEZE.json':'unknown_single.py'}[name]
  assert sha(Path(__file__).with_name(source))==f.get('analysis_code_sha256',f.get('code_sha256'))
 # Independently recompute all ordinary DEV score triples.
 v,t,r=load('dev');pair=np.array([[r['probe_ranks'].index(s['probe_L']),r['probe_ranks'].index(s['probe_R'])]])
 with (OUT/'DEV_PER_WORLD.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
 errors=[]
 with np.load(OUT/'FROZEN_ORDINARY_MODELS.npz') as model:
  for known,prefix in ((True,'known'),(False,'unknown_gain')):
   features=make_features(v,t,pair,known)
   p=r['probe_ranks'].index(s['global_single']['probe_rank']);method=s['global_single']['method']
   features['strongest_global_single']=make_features(v,t,np.array([[p,p]]),known)[method]
   for name,x in features.items():
    if prefix+'__'+name not in model:continue
    mu=model[prefix+'__'+name]
    for source in range(3):
     for rep in range(2):
      y=x[source,rep,0];d=[]
      for m in mu:
       if known:value=sum(float(a-b)**2 for a,b in zip(y,m))/len(y)
       else:
        denom=sum(float(b)**2 for b in m);gain=max(0.,sum(float(a)*float(b) for a,b in zip(y,m))/denom) if denom else 0.
        residual=sum((float(a)-gain*float(b))**2 for a,b in zip(y,m));energy=sum(float(a)**2 for a in y);value=residual/energy if energy else 0.
       d.append(value)
      ref=next(a for a in rows if a['scope']==prefix and a['method']==name and a['world_id']==r['worlds'][2*source+rep]['run_id'])
      errors.extend(abs(d[i]-float(ref['score_'+('A','B','C')[i]])) for i in range(3))
 assert max(errors)<1e-10
 # C++17 uses the unchanged general-source-count kernels from prior V7.
 lib=ct.CDLL(str((NATIVE/'native_query.dll').resolve()));f64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');i32=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
 lib.m1_features.argtypes=[f64,f64,ct.c_int,f64,ct.c_int,f64,f64];lib.m1_features.restype=ct.c_int
 lib.m1_symbol.argtypes=[ct.c_double,f64,ct.c_double,f64,i32,ct.c_int];lib.m1_symbol.restype=ct.c_int
 lib.raw_joint_symbol.argtypes=[f64,ct.c_int,f64,ct.c_int,ct.c_double];lib.raw_joint_symbol.restype=ct.c_int
 lib.categorical_posterior.argtypes=[f64,ct.c_int,ct.c_int,ct.c_int,f64];lib.categorical_posterior.restype=ct.c_int
 models={name:load_observation_model(OUT/'mirror_models'/name) for name in ('even','mother','secondary','raw_joint')}
 raw=v[:,:,:,pair[0]];feature_error=post_error=0.;checks=0;mirror_swap_error=0.
 for source in range(3):
  for rep in range(2):
   x=np.ascontiguousarray(raw[source,rep]);tt=np.ascontiguousarray(t)
   for name,m in models.items():
    expected=int(m.encode(0,x,tt,m.contract))
    if name=='raw_joint':symbol=lib.raw_joint_symbol(x,x.size,np.ascontiguousarray(m.centers[0]),m.channel.shape[-1],float(m.scales[0]))
    else:
     specs=np.ascontiguousarray([[a.lag_s,a.decay_s,a.inhibition,a.bias,0 if a.kind=='gradient' else 1] for a in m.bank.specs],dtype=float)
     e=np.zeros(1);h=np.zeros(len(specs));assert lib.m1_features(x,tt,len(tt),specs,len(specs),e,h)==0
     pe,ph=m.bank.extract(x,tt,m.contract);se,sh=m.bank.extract(x[:,::-1],tt,m.contract)
     feature_error=max(feature_error,abs(pe-e[0]),float(np.max(abs(ph-h))))
     mirror_swap_error=max(mirror_swap_error,abs(float(pe-se)),float(np.max(abs(ph+sh))))
     inds=np.array(m.selection[0],dtype=np.int32);symbol=lib.m1_symbol(e[0],h,float(m.even_thresholds[0]),np.ascontiguousarray(m.odd_thresholds[0]),inds,len(inds))
    assert symbol==expected
    table=np.ascontiguousarray(m.channel.probabilities[0,:,0]);post=np.zeros(3)
    assert lib.categorical_posterior(table,3,m.channel.shape[-1],symbol,post)==0
    post_error=max(post_error,float(np.max(abs(post-table[:,symbol]/table[:,symbol].sum()))));checks+=1
 assert feature_error<1e-12 and post_error<1e-14 and mirror_swap_error<1e-12
 # The selected right probe is identically zero: paired mirror features
 # reduce EXACTLY to single-side rectified delayed intensity, not motion.
 all_right=[];deg_error=0.
 m=models['secondary']
 for stage in ('train','dev'):
  vv,tt,rr=load(stage)
  if stage=='train':vv=vv[:,:,np.array(s['window_indices'])];tt=tt[np.array(s['window_indices'])];ii=[s['probe_L']-1,s['probe_R']-1]
  else:ii=[rr['probe_ranks'].index(s['probe_L']),rr['probe_ranks'].index(s['probe_R'])]
  x=vv[:,:,:,ii];all_right.append(float(x[...,1].max()));L=np.log1p(x[...,0]);e,h=m.bank.extract(x,tt,m.contract)
  for k,spec in enumerate(m.bank.specs):
   if spec.kind=='gradient':equiv=.5*np.einsum('...t,t->...',L,time_weights(tt))
   else:
    w=_kernel(tt,tt[-1],spec.decay_s);wd=_kernel(tt,tt[-1]-spec.lag_s,spec.decay_s)
    equiv=np.maximum(np.einsum('...t,t->...',L,w-spec.inhibition*wd),0)
   deg_error=max(deg_error,float(np.max(abs(h[...,k]-equiv))))
 assert max(all_right)==0 and deg_error<1e-12
 write('INDEPENDENT_QA.json',{'status':'PASS_WITH_SCIENTIFIC_NEGATIVES','ordinary_DEV_scalar_scores':len(errors),
 'max_score_error':max(errors),'CPP_inference_checks':checks,'max_CPP_feature_error':feature_error,
 'max_CPP_posterior_error':post_error,'mirror_swap_equivariance_error':mirror_swap_error,
 'TRAIN_and_DEV_right_probe_max':all_right,'mirror_to_single_lag_exact_degeneracy_error':deg_error,
 'frozen_models_and_code_unchanged':True,'no_refit_or_new_DEV_queries':True})
 print('INDEPENDENT_QA_PASS',len(errors),checks,feature_error,deg_error)
if __name__=='__main__':main()
