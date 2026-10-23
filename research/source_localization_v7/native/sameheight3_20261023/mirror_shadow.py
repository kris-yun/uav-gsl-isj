"""User-requested frozen mirror diagnostic, same selected action and data.

An addendum to the ordinary observability trial, not a rewritten primary
protocol. No DEV fitting, no new threshold and no M2/M3/active robot.
"""
import json,sys,time
from dataclasses import asdict
import numpy as np
from protocol import *
from analysis import load,csvout,classify
from gsl_discrimination.m1_opponent import OpponentBank,SamplingContract,calibrate_source_contrast
from gsl_discrimination.m1_opponent.calibration import SourceContrastModel
from gsl_discrimination.m1_opponent.raw_joint import calibrate_raw_joint,load_observation_model
from gsl_discrimination.m1_opponent.operator import _kernel,time_weights

def feature_sets(x,t,bank,contract):
 z=np.log1p(x);w=time_weights(t);even,h=bank.extract(x,t,contract)
 # Ordinary delayed linear measurements use the identical kernels; no
 # mother mirror/ReLU combination. More dimensions are disclosed.
 ordinary=[]
 for lag in (1.8,3.,6.):
  k=_kernel(t,t[-1],1.5);kd=_kernel(t,t[-1]-lag,1.5)
  ordinary.extend([np.einsum('...tp,t->...p',z,k),np.einsum('...tp,t->...p',z,kd)])
 return {'static_two_means':np.einsum('...tp,t->...p',z,w),
 'full_joint_window':z.reshape(z.shape[:-2]+(-1,)),
 'static_even_gradient':np.stack([even,h[...,0]],axis=-1),
 'ordinary_delayed_linear':np.concatenate(ordinary,axis=-1),
 'frozen_all_mirror_features':np.concatenate([even[...,None],h],axis=-1)}

def fit():
 start=time.perf_counter();assert not (OUT/'MIRROR_MODEL_FREEZE.json').exists()
 assert not (OUT/'DEV_EXTRACTION.json').exists()
 cfg=config();s=json.loads((OUT/'SELECTION_FREEZE.json').read_text())['selected'];v,t,receipt=load('train')
 idx=np.array(s['window_indices']);t=t[idx];x=v[:,:,idx][:,:,:,np.array([s['probe_L']-1,s['probe_R']-1])]
 old=json.loads((PROJECT/'results/native_20261023/TRAIN_FIT_RECEIPT.json').read_text())
 bank=OpponentBank.from_dict(old['selected_bank'])
 contract=SamplingContract(continuous=True,synchronous=True,maximum_step_s=.61,bandwidth_calibrated=True,
 provenance='conditional ideal identity simulator readout only, NOT physical PID calibration')
 raw=x[None,:,None];xy=np.array(cfg['source_xyz_m'])[:,:2];models={};selections={}
 for variant in ('even','mother','secondary','raw_joint'):
  if variant=='raw_joint':model=calibrate_raw_joint(raw,t,contract,xy,['frozen_pair'],['A','B','C'],[float(t[-1]-t[0])],n_symbols=4)
  else:model=calibrate_source_contrast(raw,t,contract,xy,['frozen_pair'],['A','B','C'],[float(t[-1]-t[0])],
    bank=bank,variant=variant,max_filters=2,separation_target=.04,calibration_world_ids=[w['run_id'] for w in receipt['worlds']])
  model.save(OUT/'mirror_models'/variant)
  if variant!='raw_joint':selections[variant]=model.selection[0]
  models[variant]=model
 features=feature_sets(x,t,bank,contract);e,h=bank.extract(x,t,contract)
 for variant in ('mother','secondary'):features[variant+'_gaussian']=np.concatenate([e[...,None],h[...,selections[variant]]],axis=-1)
 # An order-destroyed pair multiset, sorted lexicographically, is a diagnostic
 # control rather than a physical wind replay. Freeze the transform now.
 order=np.lexsort((x[...,1],x[...,0]),axis=-1);unordered=np.take_along_axis(x,order[...,None],axis=-2)
 features['unordered_mirror_gaussian']=feature_sets(unordered,t,bank,contract)['frozen_all_mirror_features']
 records={}
 for name,a in features.items():
  d=a.shape[-1];mu=a.mean(axis=1);r=a-mu[:,None]
  pooled=np.einsum('srd,sre->de',r,r)/(3*(2-1));floor=.1*np.trace(pooled)/d+1e-6;cov=pooled+floor*np.eye(d)
  path=OUT/'mirror_models'/(name+'.npz');np.savez_compressed(path,mean=mu,covariance=cov,floor=floor)
  records[name]={'dimension':d,'floor':float(floor),'sha256':sha(path)}
 files={str(p.relative_to(OUT)):sha(p) for p in (OUT/'mirror_models').rglob('*') if p.is_file()}
 write('MIRROR_MODEL_FREEZE.json',{'status':'FROZEN_TRAIN_ONLY_BEFORE_DEV','selection_sha256':sha(OUT/'SELECTION_FREEZE.json'),
 'ordinary_model_freeze_sha256':sha(OUT/'MODEL_FREEZE.json'),'code_sha256':sha(__file__),'models':files,
 'Gaussian_heads':records,'selection':selections,'bank':bank.to_dict(),'contract':asdict(contract),
 'separation_target':.04,'changed_M1_source':False,'same_selected_pair_not_M1_optimized':True,
 'new_user_steering':'2026-10-23 user requested strongest defensible examination of mirror value in hard conditions, while preserving thresholds and excluding M2/M3/ROS',
 'original_primary_protocol_unchanged':True,'exploratory_addendum_not_new_main_claim':True,'wall_s':time.perf_counter()-start})
 print('MIRROR_SHADOW_FROZEN',json.dumps(selections),flush=True)

def evaluate():
 start=time.perf_counter();assert not (OUT/'MIRROR_DEV_RESULT.json').exists()
 f=json.loads((OUT/'MIRROR_MODEL_FREEZE.json').read_text());assert sha(__file__)==f['code_sha256']
 for name,digest in f['models'].items():assert sha(OUT/name)==digest
 s=json.loads((OUT/'SELECTION_FREEZE.json').read_text())['selected'];v,t,r=load('dev');ranks=r['probe_ranks']
 x=v[:,:,:,np.array([ranks.index(s['probe_L']),ranks.index(s['probe_R'])])]
 bank=OpponentBank.from_dict(f['bank']);contract=SamplingContract(**f['contract']);features=feature_sets(x,t,bank,contract)
 e,h=bank.extract(x,t,contract)
 for variant in ('mother','secondary'):features[variant+'_gaussian']=np.concatenate([e[...,None],h[...,f['selection'][variant]]],axis=-1)
 order=np.lexsort((x[...,1],x[...,0]),axis=-1);unordered=np.take_along_axis(x,order[...,None],axis=-2)
 features['unordered_mirror_gaussian']=feature_sets(unordered,t,bank,contract)['frozen_all_mirror_features']
 xy=np.array(config()['source_xyz_m'])[:,:2];rows=[]
 def add(name,source,rep,d,dim):
  pred=int(classify(d));lp=-d;lp-=lp.max();prob=np.exp(lp);prob/=prob.sum()
  rows.append({'method':name,'world_id':r['worlds'][2*source+rep]['run_id'],'source':('A','B','C')[source],
  'prediction':('A','B','C')[pred] if pred>=0 else 'TIE','strict_correct':pred==source,'tie':pred<0,
  'MAP_xy_error_non_tie_m':float(np.linalg.norm(xy[pred]-xy[source])) if pred>=0 else None,
  'score_A':float(d[0]),'score_B':float(d[1]),'score_C':float(d[2]),'dimension':dim,
  'Brier':float(np.sum((prob-np.eye(3)[source])**2))})
 for name in f['Gaussian_heads']:
  with np.load(OUT/'mirror_models'/(name+'.npz')) as q:mu=q['mean'];inv=np.linalg.inv(q['covariance'])
  for source in range(3):
   for rep in range(2):
    delta=features[name][source,rep][None]-mu;d=.5*np.einsum('sd,de,se->s',delta,inv,delta);add(name,source,rep,d,mu.shape[-1])
 for variant in ('even','mother','secondary','raw_joint'):
  model=load_observation_model(OUT/'mirror_models'/variant)
  for source in range(3):
   for rep in range(2):
    symbol=model.encode(0,x[source,rep],t,contract);d=-np.log(model.channel.probabilities[0,:,0,symbol]);add('original_'+variant,source,rep,d,len(model.selection[0])+1 if variant!='raw_joint' else 2)
 csvout('MIRROR_DEV_PER_WORLD.csv',rows);summary=[]
 for name in sorted({r['method'] for r in rows}):
  sub=[r for r in rows if r['method']==name]
  summary.append({'method':name,'strict_correct':sum(r['strict_correct'] for r in sub),'ties':sum(r['tie'] for r in sub),
  'BC_correct':sum(r['strict_correct'] for r in sub if r['source']!='A'),'A_correct':sum(r['strict_correct'] for r in sub if r['source']=='A'),
  'mean_non_tie_xy_error_m':float(np.mean([r['MAP_xy_error_non_tie_m'] for r in sub if not r['tie']])) if any(not r['tie'] for r in sub) else None,
  'mean_Brier':float(np.mean([r['Brier'] for r in sub]))})
 csvout('MIRROR_DEV_SUMMARY.csv',summary);write('MIRROR_DEV_RESULT.json',{'status':'ONE_FROZEN_SHADOW_CHECK_COMPLETE','summary':summary,
 'old_coarse_operator_not_fast_motion_qualification':True,'same_information_and_selected_pair':True,
 'two_DEV_master_seed_groups_only':True,'not_M2_M3_or_robot_closed_loop':True,'wall_s':time.perf_counter()-start})
 print('MIRROR_SHADOW_COMPLETE',json.dumps(summary),flush=True)

if __name__=='__main__':
 if sys.argv[1:]==['train']:fit()
 elif sys.argv[1:]==['dev']:evaluate()
 else:raise SystemExit('train|dev')
