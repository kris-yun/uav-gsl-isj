"""R3: frozen source-blind instability, observability and history falsification.
No truth is loaded before every source-blind gate and decision is saved.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='4';os.environ['OMP_NUM_THREADS']='4'
from pathlib import Path
import sys,json,hashlib,subprocess,itertools,time
import numpy as np,pandas as pd
from scipy.special import logsumexp
from scipy.spatial.distance import pdist
REPO=Path(__file__).resolve().parents[2]
OLD=REPO/'evidence/public_data_first_20261003'
OUT=REPO/'evidence/r3_transport_20261003'
LOCAL=Path(r'C:\work\R3_REAL_TRANSPORT_AUDIT_20261003')
sys.path.insert(0,str(REPO/'experiments/public_data_first/mackenzie'))
from audit import inverse_inputs,kernel
CFG=dict(protocol_anchor_commit='17b31989e726b64ac95030a5b3f7dd635578af65',
 delivery_parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
 starting_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),seed=20261003,
 prior_truth_known_from_previous_audit=True,new_pipeline_truth_access='evaluation only after source-blind decision saved',
 hypothesis='between legal model source drift exceeds within-model sampling drift; this does not uniquely identify missing dynamic state causally',
 primary_conditions=['Svalbard_phase1','Svalbard_phase2','Mackenzie_CP','Mackenzie_OP'],negative_control='Svalbard_phase3',
 block_seconds=60,bootstrap_replicates=24,bootstrap='nonoverlapping 60s blocks, resampled with replacement within flight; shared draws across model arms',
 splits='alternating 60s blocks, reciprocal train/test; no random point split',
 source_estimator='Svalbard marginal-Q source MAP; Mackenzie profile-RSS source MAP',
 structural_gate=dict(min_ratio=2.,between_wind_only_gt_within_pairwise95=True,both_primary_conditions_per_dataset=True,
    require_both_datasets=True,exclude_background_only_or_phase3_driven_effect=True,boundary_primary_arms_invalid=True,
    denominator_floor='half candidate grid spacing, reported when floor applies; no infinite ratios'),
 observability=dict(primary_model='current local, frozen primary nuisance',enhancement_fraction_min=.05,
    sv_enhancement_threshold='background*(exp(log_sigma)-1)',entropy_fraction_max=.85,area_fraction_max=.25,
    q_zero_probability_max=.5,q_MAP_positive=True,boundary_mass_max=.10,split_drift_max_domain_fraction=.25,
    require_all=True,thresholds='dimensionless fixed rules, not tuned to desired phase labels'),
 history=dict(windows_seconds=[10,30,60],past='exclude current sample, strictly earlier within same flight',
    future='exclude current, matched later windows',matched_complete_windows_only=True,primary_nuisance_only=True,
    gate='each dataset both primary conditions: past improves held-out loss >=5% over current AND best future by >=5%; never choose window by truth',
    require_all_windows_for_robust_causal_claim=True,unknown_sensor_lag_precludes_causal_claim=True),
 Svalbard=dict(wind=['flight_mean','current_local'],background=[2.05,2.09,2.13],sigma=[.15,.30],K=1,
   grid_m=2.5,domain='all phase receptor GPS envelope +30m; identical to prior audited grid',Q_g_h=np.linspace(0,10000,81).tolist(),tau=286977600,T=273.95,P=102000),
 Mackenzie=dict(wind=['flight_mean','current_local','height_dependent'],background=['author_code','paper_background'],
    domain='same audited receptor-derived 31x31 mean-wind grid; source 10..400m upwind',
    primary_ty=[.04,.10,.25],primary_tz=[.025,.075,.20],broader_ty=[.03,.05,.08,.12,.18,.25,.35],broader_tz=[.015,.025,.04,.065,.10,.16,.25],
    sigma='not fitted; use equal-flight weighted concentration RSS support, not posterior',
    clock='prepared 1s CP/OP rows, approximate relative clock only; no absolute cross-flight synchronization or lag inference'),
 Lagoon='HOLD; excluded',no_new_CFD_GADEN=True,no_model_training=True)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else None),encoding='utf8')
def csv(name,rows):pd.DataFrame(rows).to_csv(OUT/name,index=False)
def summarize(sources,p,qmap):
 i=int(p.argmax());order=np.sort(p)[::-1];area_cells=int(np.searchsorted(np.cumsum(order),.95)+1)
 edge=(np.isclose(sources[:,0],sources[:,0].min())|np.isclose(sources[:,0],sources[:,0].max())|np.isclose(sources[:,1],sources[:,1].min())|np.isclose(sources[:,1],sources[:,1].max()))
 return dict(source_x=float(sources[i,0]),source_y=float(sources[i,1]),mean_x=float(p@sources[:,0]),mean_y=float(p@sources[:,1]),
   normalized_entropy=float(-np.sum(p*np.log(np.maximum(p,1e-300)))/np.log(len(p))),area_fraction=area_cells/len(p),boundary_probability=float(p[edge].sum()),q_map=float(qmap[i]),source_on_boundary=bool(edge[i]))
def blocks(d,step):
 ids=[];offset=0
 for flight,g in d.groupby('flight',sort=False):
  b=np.floor(g.t.to_numpy()/60).astype(int);unique=np.unique(b);mapping={x:offset+i for i,x in enumerate(unique)}
  ids.extend([mapping[x] for x in b]);offset+=len(unique)
 # Callers preserve flight groups in concatenation, never silently reorder.
 ids=np.array(ids);strata=[np.unique(ids[d.flight.to_numpy()==f]) for f in d.flight.unique()]
 rng=np.random.default_rng(CFG['seed']);draws=[]
 for _ in range(CFG['bootstrap_replicates']):
  count=np.zeros(offset)
  for group in strata:count+=np.bincount(rng.choice(group,len(group),replace=True),minlength=offset)
  draws.append(count)
 split=(np.arange(offset)%2).astype(float)
 return ids,np.array(draws),[split,1-split]
def vectors(d,arm):
 u=d.u.to_numpy().copy();v=d.v.to_numpy().copy()
 for _,g in d.groupby('flight',sort=False):
  m=d.index.isin(g.index)
  if arm=='flight_mean':u[m]=u[m].mean();v[m]=v[m].mean()
  elif arm=='height_dependent':
   z=d.z.to_numpy()[m];A=np.column_stack([np.ones(m.sum()),z-z.mean()]);u[m]=A@np.linalg.lstsq(A,u[m],rcond=None)[0];v[m]=A@np.linalg.lstsq(A,v[m],rcond=None)[0]
 return u,v

MODELS=[];BOOTS=[];SPLITS=[];HISTORY=[];PROFILE=[]
def record(condition,tag,sources,row,boot,split,primary=False,nuisance='',wind='',floor=1.25,predict=None):
 length=float(np.hypot(np.ptp(CASE_OBS[condition].e),np.ptp(CASE_OBS[condition].n)))
 row.update(condition=condition,model=tag,wind=wind,nuisance=nuisance,primary=primary,domain_characteristic_m=length,grid_resolution_floor_m=floor)
 MODELS.append(row)
 for b,point in enumerate(boot):BOOTS.append(dict(condition=condition,model=tag,replicate=b,source_x=float(point[0]),source_y=float(point[1]),drift_from_full_m=float(np.linalg.norm(point-np.array([row['source_x'],row['source_y']])))))
 for i,point in enumerate(split):SPLITS.append(dict(condition=condition,model=tag,split=i,source_x=float(point[0]),source_y=float(point[1]),heldout_score=float(predict[i]) if predict is not None else None))

def sv_loss(d,sources,u,v,bg,ids):
 Q=np.array(CFG['Svalbard']['Q_g_h']);nblock=ids.max()+1
 loss=np.zeros((len(sources),len(Q),nblock),dtype='float32')
 factor=8.314*273.95/(102000*16.04)*1e6/3600
 target=np.log(d.ch4.to_numpy());speed=np.hypot(u,v)
 for start in range(0,len(sources),192):
  s=sources[start:start+192];dx=d.e.to_numpy()[None,:]-s[:,0,None];dy=d.n.to_numpy()[None,:]-s[:,1,None]
  distance=np.sqrt(dx*dx+dy*dy+d.z.to_numpy()[None,:]**2)
  exponent=-distance*np.sqrt(1/286977600+speed[None,:]**2/4)+(dx*u+dy*v)/2
  unit=2*factor/(4*np.pi*np.maximum(distance,.1))*np.exp(np.clip(exponent,-745,20))
  residual=(target[None,:,None]-np.log(bg+unit[:,:,None]*Q[None,None,:]))**2/2
  for b in range(nblock):loss[start:start+len(s),:,b]=residual[:,ids==b,:].sum(axis=1)
 return loss
def sv_fit(loss,counts,sigma,sources):
 nll=np.tensordot(loss,counts,axes=([2],[0]))/sigma**2
 evidence=logsumexp(-nll,axis=1)-np.log(nll.shape[1]);p=np.exp(evidence-logsumexp(evidence));q=np.array(CFG['Svalbard']['Q_g_h'])[nll.argmin(axis=1)]
 row=summarize(sources,p,q);i=p.argmax()
 # Fully marginal Q=0 posterior, not MAP=0 alone.
 row['q_zero_probability']=float(np.exp(logsumexp(-nll[:,0])-logsumexp(-nll)))
 row['minimum_loss']=float(nll.min());return row,p,(int(i),int(nll[i].argmin()))
def sv_run(condition,d,sources,history=False):
 ids,draws,splits=blocks(d,10);CASE_OBS[condition]=d
 arms=['flight_mean','current_local'] if not history else list(HISTORY_VECTORS)
 for arm in arms:
  print('SV',condition,arm,'history' if history else '',flush=True)
  u,v=vectors(d,arm) if not history else HISTORY_VECTORS[arm]
  for bg in ([2.09] if history else CFG['Svalbard']['background']):
   loss=sv_loss(d,sources,u,v,bg,ids)
   for sigma in ([.15] if history else CFG['Svalbard']['sigma']):
    tag=f'{arm}_bg{bg}_sigma{sigma}';row,p,_=sv_fit(loss,np.ones(loss.shape[2]),sigma,sources)
    splitpoints=[];scores=[]
    for count in splits:
     r,_,(i,j)=sv_fit(loss,count,sigma,sources);splitpoints.append([r['source_x'],r['source_y']]);scores.append(float(loss[i,j]@(1-count)/sigma**2/max(np.sum((1-count)[ids]),1)))
    if history:
     HISTORY.append(dict(condition=condition,arm=arm,heldout_score=float(np.mean(scores)),split_source_drift_m=float(np.linalg.norm(np.diff(splitpoints,axis=0))),n_observations=len(d),sensor_lag_verified=False));continue
    boot=[]
    for count in draws:
     r,_,_=sv_fit(loss,count,sigma,sources);boot.append([r['source_x'],r['source_y']])
    record(condition,tag,sources,row,boot,splitpoints,primary=(bg==2.09 and sigma==.15),nuisance=f'bg{bg}_sigma{sigma}',wind=arm,predict=scores)
    pd.DataFrame(dict(x=sources[:,0],y=sources[:,1],probability=p)).to_csv(OUT/(condition+'_'+tag+'_posterior.csv'),index=False)

def mk_cache(d,sources,u,v,ids,ty,tz,bg):
 nblock=ids.max()+1;pairs=list(itertools.product(ty,tz));rho=(101987-12.26*d.z.to_numpy())*.01604/(292.4627*8.31446261815324)
 measured=(d.ch4.to_numpy()-bg)*rho
 weights=np.array([1/sum(d.flight==f) for f in d.flight])
 A=np.zeros((len(sources),len(pairs),nblock));B=A.copy();C=np.zeros(nblock)
 dx=d.e.to_numpy()[None,:]-sources[:,0,None];dy=d.n.to_numpy()[None,:]-sources[:,1,None]
 for b in range(nblock):C[b]=np.sum((weights*measured**2)[ids==b])
 for j,(ay,az) in enumerate(pairs):
  k=kernel(dx,dy,d.z.to_numpy()[None,:],u[None,:],v[None,:],ay,az)
  for b in range(nblock):
   m=ids==b;A[:,j,b]=(k[:,m]**2)@weights[m];B[:,j,b]=k[:,m]@(weights[m]*measured[m])
 return A,B,C
def mk_fit(cache,count,sources):
 A,B,C=cache;a=A@count;b=B@count;c=C@count;q=np.maximum(0,b/np.maximum(a,1e-30));rss=c-2*q*b+q*q*a
 idx=np.unravel_index(rss.argmin(),rss.shape);i,j=idx;profile=rss.min(axis=1);support=profile<=profile.min()*1.05
 # RSS support measure, deliberately not a fabricated posterior.
 p=support.astype(float)/max(support.sum(),1);row=summarize(sources,p,q[np.arange(len(sources)),rss.argmin(axis=1)])
 row.update(source_x=float(sources[i,0]),source_y=float(sources[i,1]),q_map=float(q[i,j]),minimum_loss=float(rss.min()),q_zero_probability=None,
   normalized_entropy=None,area_fraction=float(support.mean()),boundary_probability=None,
   source_on_boundary=bool(i//31 in [0,30] or i%31 in [0,30]),support_type='RSS <=1.05min; not posterior')
 return row,profile,(i,j,q[i,j])
def mk_run(condition,d,sources,history=False):
 ids,draws,splits=blocks(d,1);CASE_OBS[condition]=d
 arms=CFG['Mackenzie']['wind'] if not history else list(HISTORY_VECTORS)
 for arm in arms:
  print('MK',condition,arm,'history' if history else '',flush=True)
  u,v=vectors(d,arm) if not history else HISTORY_VECTORS[arm]
  for support in (['primary'] if history else ['primary','broader']):
   ty=CFG['Mackenzie'][support+'_ty'];tz=CFG['Mackenzie'][support+'_tz']
   for bgarm in (['author_code'] if history else CFG['Mackenzie']['background']):
    bg=2.031797 if 'CP' in condition else (2.064857 if bgarm=='author_code' else 2.0291)
    if 'CP' in condition and bgarm=='paper_background':bg=2.0318
    cache=mk_cache(d,sources,u,v,ids,ty,tz,bg);tag=f'{arm}_{support}_{bgarm}'
    row,profile,_=mk_fit(cache,np.ones(cache[2].shape),sources);sp=[];scores=[]
    for count in splits:
     r,_,(i,j,q)=mk_fit(cache,count,sources);sp.append([r['source_x'],r['source_y']]);other=1-count
     rss=float(cache[2]@other-2*q*(cache[1][i,j]@other)+q*q*(cache[0][i,j]@other));scores.append(rss/max(other.sum()/len(other),1e-9))
    if history:
     HISTORY.append(dict(condition=condition,arm=arm,heldout_score=float(np.mean(scores)),split_source_drift_m=float(np.linalg.norm(np.diff(sp,axis=0))),n_observations=len(d),sensor_lag_verified=False));continue
    boot=[]
    for count in draws:
     r,_,_=mk_fit(cache,count,sources);boot.append([r['source_x'],r['source_y']])
    record(condition,tag,sources,row,boot,sp,primary=(support=='primary' and bgarm=='author_code'),nuisance=support+'_'+bgarm,wind=arm,floor=6.5,predict=scores)
    pd.DataFrame(dict(x=sources[:,0],y=sources[:,1],profile_rss=profile)).to_csv(OUT/(condition+'_'+tag+'_support.csv'),index=False)

def prepare_history(d,step):
 pieces=[]
 for _,g in d.groupby('flight',sort=False):
  g=g.copy();g.index=np.round(g.t/step).astype(int);g=g[~g.index.duplicated()];g=g.reindex(np.arange(g.index.min(),g.index.max()+1))
  for w in CFG['history']['windows_seconds']:
   n=w//step
   for field in ['u','v']:
    g[f'past{w}_{field}']=g[field].shift(1).rolling(n,min_periods=n).mean()
    g[f'future{w}_{field}']=g[field][::-1].shift(1).rolling(n,min_periods=n).mean()[::-1]
  pieces.append(g.dropna())
 matched=pd.concat(pieces,ignore_index=True)
 vectors_out={'current_local':matched[['u','v']].to_numpy().T,'flight_mean':np.stack(vectors(matched,'flight_mean'))}
 for w in CFG['history']['windows_seconds']:
  for side in ['past','future']:vectors_out[side+str(w)]=matched[[side+str(w)+'_u',side+str(w)+'_v']].to_numpy().T
 return matched,vectors_out

CASE_OBS={};HISTORY_VECTORS={}
def gates():
 models=pd.DataFrame(MODELS);boot=pd.DataFrame(BOOTS);split=pd.DataFrame(SPLITS);drift=[];obs=[]
 for condition,g in models.groupby('condition',sort=False):
  primary=g[g.primary];all_dist=pdist(g[['source_x','source_y']]);winddist=pdist(primary[['source_x','source_y']])
  within=[];windwithin=[]
  for _,m in g.iterrows():
   b=boot[(boot.condition==condition)&(boot.model==m.model)];dist=pdist(b[['source_x','source_y']]);within.extend(dist)
   if m.primary:windwithin.extend(dist)
  floor=g.grid_resolution_floor_m.iloc[0];den=float(np.median(within));windden=float(np.median(windwithin));between=float(np.median(all_dist));bw=float(np.median(winddist))
  ratio=between/max(den,floor);wr=bw/max(windden,floor);w95=float(np.quantile(windwithin,.95))
  boundaries=bool(primary.source_on_boundary.any());passed=wr>=2 and bw>w95 and not boundaries
  drift.append(dict(condition=condition,between_model_source_drift_m=between,normalized_source_drift=between/g.domain_characteristic_m.iloc[0],within_model_bootstrap_drift_m=den,structural_drift_ratio=ratio,
    wind_only_source_drift_m=bw,wind_only_bootstrap_drift_m=windden,wind_only_ratio=wr,wind_only_bootstrap95_m=w95,
    denominator_floor_m=floor,floor_applies=den<floor,primary_boundary_invalid=boundaries,condition_pass=bool(passed),n_models=len(g)))
  if condition.startswith('Svalbard'):
   r=primary[primary.wind=='current_local'].iloc[0];s=split[(split.condition==condition)&(split.model==r.model)];sd=float(pdist(s[['source_x','source_y']])[0]);d=CASE_OBS[condition]
   fraction=float(np.mean(d.ch4>2.09*np.exp(.15)))
   criteria=[fraction>=.05,r.normalized_entropy<.85,r.area_fraction<.25,r.q_zero_probability<.5,r.q_map>0,r.boundary_probability<.1,sd<.25*r.domain_characteristic_m]
   obs.append(dict(condition=condition,enhancement_fraction=fraction,posterior_entropy_fraction=r.normalized_entropy,credible_area_fraction=r.area_fraction,Q_MAP=r.q_map,q_zero_probability=r.q_zero_probability,boundary_probability=r.boundary_probability,split_drift_m=sd,split_drift_domain_fraction=sd/r.domain_characteristic_m,informative=all(criteria),decision='INFORMATIVE' if all(criteria) else 'INSUFFICIENT_ABSTAIN',criteria_pass_count=sum(criteria),criteria_total=7))
 csv('R3_MODEL_ESTIMATES.csv',MODELS);csv('R3_BOOTSTRAP_DRIFT.csv',BOOTS);csv('R3_SPLIT_CONSISTENCY.csv',SPLITS);csv('R3_STRUCTURAL_DRIFT.csv',drift);csv('R3_OBSERVABILITY.csv',obs);csv('R3_HISTORY_PLACEBO.csv',HISTORY)
 d=pd.DataFrame(drift).set_index('condition');a_pass=all(bool(d.loc[c,'condition_pass']) for c in CFG['primary_conditions'])
 b_pass=all(o['informative']==(o['condition']!='Svalbard_phase3') for o in obs)
 history_gate=[];hh=pd.DataFrame(HISTORY)
 for c,g in hh.groupby('condition'):
  current=float(g[g.arm=='current_local'].heldout_score.iloc[0]);mean=float(g[g.arm=='flight_mean'].heldout_score.iloc[0]);past=[]
  for w in CFG['history']['windows_seconds']:
   p=float(g[g.arm=='past'+str(w)].heldout_score.iloc[0]);f=float(g[g.arm=='future'+str(w)].heldout_score.iloc[0]);past.append(p<=.95*current and p<=.95*f)
  history_gate.append(dict(condition=c,consistent_causal_score_advantage=all(past),lag_contract_verified=False,decision='STOP_HISTORY_ROUTE'))
 csv('R3_HISTORY_GATE.csv',history_gate)
 decision='R3_PASS_STRUCTURAL_TRANSPORT_INSUFFICIENCY' if a_pass and b_pass else ('R3_HOLD' if any(d.loc[c,'condition_pass'] for c in CFG['primary_conditions']) else 'R3_STOP')
 result=dict(decision=decision,R3_A_pass=a_pass,R3_B_negative_control_gate=b_pass,R3_C='STOP_HISTORY_ROUTE',history='score results retained; no consistent verified causal claim, no RNN or history module',
  condition_gates=drift,observability=obs,protocol_anchor_commit=CFG['protocol_anchor_commit'],delivery_parent_commit=CFG['delivery_parent_commit'],starting_commit=CFG['starting_commit'],
  truth_read_for_gate=False,R4_executed=False,model_training=False,causal_missing_state_proved=False)
 dump('R3_DECISION.json',result);return result

def main():
 global CFG
 resume='--resume-gates' in sys.argv
 OUT.mkdir(parents=True,exist_ok=True);LOCAL.mkdir(parents=True,exist_ok=True)
 if (OUT/'R3_FROZEN_CONFIG.json').exists():CFG=json.loads((OUT/'R3_FROZEN_CONFIG.json').read_text(encoding='utf8'))
 if not resume:dump('R3_FROZEN_CONFIG.json',CFG)
 inputs=[OLD/'van_hove/REAL_FIELD_OBSERVATIONS_10S.csv']+[OLD/f'mackenzie/{n}_processed.csv' for n in ['CP1','CP2','OP1','OP2']]
 if not resume:dump('INPUT_MANIFEST.json',[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in inputs])
 else:
  for item in json.loads((OUT/'INPUT_MANIFEST.json').read_text(encoding='utf8')):assert sha(Path(item['path']))==item['sha256']
 (LOCAL/'R3_FROZEN_CONFIG.json').write_bytes((OUT/'R3_FROZEN_CONFIG.json').read_bytes())
 sv=pd.read_csv(inputs[0]);sv=sv.rename(columns={'east_m':'e','north_m':'n','AERIS.CH4 [ppm]':'ch4','U_corrected':'u','V_corrected':'v'})
 sv['datetime']=pd.to_datetime(sv.datetime,utc=True);sv['flight']=sv.phase.astype(str)
 for f,g in sv.groupby('flight'):sv.loc[g.index,'t']=(g.datetime-g.datetime.min()).dt.total_seconds()
 xs=np.arange(np.floor(sv.e.min()/2.5)*2.5-30,np.ceil(sv.e.max()/2.5)*2.5+30.1,2.5);ys=np.arange(np.floor(sv.n.min()/2.5)*2.5-30,np.ceil(sv.n.max()/2.5)*2.5+30.1,2.5)
 gx,gy=np.meshgrid(xs,ys);ss=np.column_stack([gx.ravel(),gy.ravel()])
 datasets=[]
 for phase in [1,2,3]:
  name=f'Svalbard_phase{phase}';d=sv[sv.phase==phase].copy().reset_index(drop=True)
  if not resume:sv_run(name,d,ss)
  else:CASE_OBS[name]=d
  datasets.append((name,d,ss,10))
 frames={p.stem.split('_')[0]:pd.read_csv(p) for p in inputs[1:]}
 for platform in ['CP','OP']:
  name='Mackenzie_'+platform;d,sources,_,_=inverse_inputs(frames,[platform+'1',platform+'2']);d['t']=d.groupby('flight').cumcount().astype(float)
  if not resume:mk_run(name,d,sources)
  else:CASE_OBS[name]=d
  datasets.append((name,d,sources,1))
 # Preserve main observation dictionaries; matched history subsets never replace them.
 global HISTORY_VECTORS
 originals=CASE_OBS.copy()
 if not resume:
  for name,d,sources,step in datasets:
   if name=='Svalbard_phase3':continue
   matched,HISTORY_VECTORS=prepare_history(d,step)
   if step==10:sv_run(name,matched,sources,history=True)
   else:mk_run(name,matched,sources,history=True)
 else:
  for target,filename in [(MODELS,'R3_MODEL_ESTIMATES.csv'),(BOOTS,'R3_BOOTSTRAP_DRIFT.csv'),(SPLITS,'R3_SPLIT_CONSISTENCY.csv'),(HISTORY,'R3_HISTORY_PLACEBO.csv')]:target.extend(pd.read_csv(OUT/filename).to_dict('records'))
 CASE_OBS.update(originals)
 result=gates();dump('SOURCE_BLIND_DECISION_BEFORE_TRUTH.json',result)
 # No truth-based retuning or re-running is permitted below this boundary.
 sys.path.insert(0,r'C:\work\SVALBARD_BOREHOLE_REAL_DATA_20261003\dependencies')
 from pyproj import Transformer
 import re
 code=Path(r'C:\work\SVALBARD_BOREHOLE_REAL_DATA_20261003\raw\active\nature_run\preprocess_drone_data\05_coordinate_system.py').read_text()
 lat=float(re.search(r"'lat':\s*([\d.]+)",code).group(1));lon=float(re.search(r"'lon':\s*([\d.]+)",code).group(1))
 origin=json.loads((OLD/'van_hove/INVERSION_BEFORE_TRUTH.json').read_text())['origin_utm']
 truth_sv=np.array(Transformer.from_crs(4326,25833,always_xy=True).transform(lon,lat))-origin
 truth_mk=np.array(Transformer.from_crs(4326,32608,always_xy=True).transform(-135.477520,69.319583))
 evals=[]
 for r in MODELS:
  truth=truth_sv if r['condition'].startswith('Svalbard') else truth_mk
  evals.append(dict(condition=r['condition'],model=r['model'],localization_error_m=float(np.linalg.norm(np.array([r['source_x'],r['source_y']])-truth)),used_for_gate=False))
 csv('R3_LOCALIZATION_POSTHOC_ONLY.csv',evals)
 print(json.dumps(result,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else None),flush=True)

if __name__=='__main__':main()
