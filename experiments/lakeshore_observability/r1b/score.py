"""Release-unknown cross-environment Brier re-score; same-template negative controls."""
import numpy as np,pandas as pd,sys
from common import *

def load_bank(folder,envs,seeds,record=False):
 a=np.full((len(envs),3,9,8,2,300),np.nan);ref=pd.read_csv(OLD/'fixed_path_contract.csv');manifest=[]
 for e,env in enumerate(envs):
  for r,rate in enumerate(RATES):
   for s,(x,y) in enumerate(SOURCES):
    for k,seed in enumerate(seeds):
     p=folder/f'{env}_x{x}_y{y}_r{rate}_seed{seed}.csv';d=pd.read_csv(p)
     assert len(d)==1200 and np.isfinite(d.to_numpy()).all() and (d.concentration>=0).all()
     assert np.array_equal(d[['time','x','y','z']].to_numpy(),ref.to_numpy())
     for h,z in enumerate([10,30]):a[e,r,s,k,h]=d[d.z==z].concentration
     if record:manifest.append(dict(path=p.relative_to(ROOT).as_posix(),environment=env,source_x=x,source_y=y,release=rate,seed=seed,rows=len(d),sha256=sha(p)))
 assert np.isfinite(a).all()
 if record:pd.DataFrame(manifest).to_csv(OUT/'observation_manifest.csv',index=False)
 return a

def score_bank(a,envs,seeds,pairs):
 rows=[];xy=np.array(SOURCES);distance=np.linalg.norm(xy[:,None]-xy[None,:],axis=-1)
 for factor in [.5,1,2]:
  hits=(a>=.001*factor).astype(float)
  # Equal-prior pooling: each release contributes seven realizations, one Beta prior.
  total=hits.sum(axis=3)
  for truth,model,arm,scene in pairs:
   et=envs.index(truth);em=envs.index(model)
   for k,seed in enumerate(seeds):
    templates=(1+total[em].sum(axis=0)-hits[em,:,:,k].sum(axis=0))/23
    for h,z in enumerate([10,30]):
     for prefix in [30,60,120,300]:
      probabilities=templates[:,h,:prefix]
      for r,rate in enumerate(RATES):
       observed=hits[et,r,:,k,h,:prefix]
       scores=((observed[:,None,:]-probabilities[None,:,:])**2).mean(axis=2)
       for s,(x,y) in enumerate(SOURCES):
        sc=scores[s];best=sc.min();mins=np.flatnonzero(np.abs(sc-best)<=1e-12);weight=1/len(mins)
        correct=float(s in mins)*weight;predx=xy[mins,0];bias=predx-x
        rank=float((sc<sc[s]-1e-12).sum()+(np.abs(sc-sc[s])<=1e-12).sum()/2+.5)
        false=np.delete(sc,s)
        rows.append(dict(scene=scene,truth=truth,model=model,arm=arm,threshold_factor=factor,height=z,prefix_s=prefix,release=rate,source_x=x,source_y=y,seed=seed,top1=correct,true_rank=rank,brier_margin=float(false.min()-sc[s]),candidate_error=float(distance[s,mins].mean()),error_fraction=1-correct,signed_x_bias=float(bias.mean()),positive_x_error=float((bias>0).sum())*weight,negative_x_error=float((bias<0).sum())*weight,zero_x_wrong=float(((bias==0)&(mins!=s)).sum())*weight,prediction_candidates=';'.join(str(int(q)) for q in mins),candidate_brier=';'.join(format(q,'.12g') for q in sc)))
 return pd.DataFrame(rows)

def finalize(t):
 keys=['scene','truth','model','arm','threshold_factor','height','prefix_s']
 summary=t.groupby(keys).agg(top1=('top1','mean'),candidate_error=('candidate_error','mean'),error_fraction=('error_fraction','mean'),signed_x_bias=('signed_x_bias','mean'),positive_x_error=('positive_x_error','sum'),negative_x_error=('negative_x_error','sum'),errors=('error_fraction','sum'),median_rank=('true_rank','median'),median_margin=('brier_margin','median')).reset_index()
 summary['direction_fraction']=summary[['positive_x_error','negative_x_error']].max(axis=1)/summary.errors.replace(0,np.nan)
 summary.to_csv(OUT/'endpoint_summary.csv',index=False)
 primary=t[(t.threshold_factor==1)&(t.height==10)&(t.prefix_s==300)]
 src=primary.groupby(['scene','arm','source_x']).agg(error_fraction=('error_fraction','mean'),signed_x_bias=('signed_x_bias','mean')).reset_index();src.to_csv(OUT/'source_region_errors.csv',index=False)
 locks=[];lockmap={}
 for strength in [1,2]:
  for arm in ['uniform','profile']:
   regions=[];centroids=[];allerrors=True
   for front in [90,120,150]:
    scene=f'XF{front}_F{strength}';q=src[(src.scene==scene)&(src.arm==arm)]
    allerrors=allerrors and q.error_fraction.sum()>0
    modal=q[np.isclose(q.error_fraction,q.error_fraction.max(),atol=1e-12,rtol=0)].source_x.mean()
    centroid=float((q.source_x*q.error_fraction).sum()/q.error_fraction.sum()) if q.error_fraction.sum()>0 else None
    regions.append(float(modal));centroids.append(centroid)
   locked=bool(allerrors and np.all(np.diff(regions)>=-1e-12) and regions[-1]-regions[0]>=30-1e-12)
   locks.append(dict(strength=strength,arm=arm,fronts=[90,120,150],most_affected_source_x=regions,error_centroid_x=centroids,front_locked=locked));lockmap[strength,arm]=locked
 write_json('front_lock_diagnostics.json',locks)
 gates=[];seedrows=[];negatives=[]
 for scene in SCENES:
  st=int(scene[-1]);q=primary[primary.scene==scene];oracle=q[q.arm=='oracle'];negative=q[q.arm=='negative_uniform'];negatives.append(dict(scene=scene,top1=float(negative.top1.mean()),pass_control=bool(negative.top1.mean()>=.9)))
  for arm in ['uniform','profile']:
   b=q[q.arm==arm];err=b.error_fraction.sum();pos=b.positive_x_error.sum();neg=b.negative_x_error.sum();direction=1 if pos>=neg else -1;direction_fraction=float(max(pos,neg)/err) if err else 0.
   nseed=0
   for seed in SEEDS:
    o=oracle[oracle.seed==seed];bb=b[b.seed==seed];delta=float(o.top1.mean()-bb.top1.mean());bias=float(bb.signed_x_bias.mean());consistent=bool(delta>0 and bias*direction>0);nseed+=consistent
    seedrows.append(dict(scene=scene,arm=arm,seed=seed,penalty=delta,mean_x_bias=bias,same_direction=consistent))
   c=[bool(oracle.top1.mean()>=.9),bool(oracle.top1.mean()-b.top1.mean()>=.2-1e-12),bool(b.candidate_error.mean()>=5 or b.error_fraction.mean()>=.2-1e-12),bool(direction_fraction>=.7),bool(lockmap[st,arm]),bool(nseed>=6)]
   gates.append(dict(scene=scene,arm=arm,oracle_top1=float(oracle.top1.mean()),baseline_top1=float(b.top1.mean()),penalty_pp=float(100*(oracle.top1.mean()-b.top1.mean())),mean_error_m=float(b.candidate_error.mean()),error_fraction=float(b.error_fraction.mean()),mean_x_bias=float(b.signed_x_bias.mean()),direction=direction,direction_fraction=direction_fraction,consistent_seed_count=nseed,gates=c,local_mismatch=all(c[i] for i in [0,1,2,3,5]),all_six=all(c)))
 pd.DataFrame(seedrows).to_csv(OUT/'seed_direction_checks.csv',index=False)
 passscenes=sum(any(q['all_six'] for q in gates if q['scene']==s) for s in SCENES);local=sum(any(q['local_mismatch'] for q in gates if q['scene']==s) for s in SCENES);negpass=all(q['pass_control'] for q in negatives)
 decision='R1B_PASS_FRONT_SPATIAL_MISMATCH' if passscenes>=4 and negpass else ('R1B_HOLD_MISMATCH_NOT_FRONT_LOCKED' if local>=4 and negpass else 'R1B_FAIL_STOP_FRONT_MISMATCH')
 write_json('R1B_FINAL_DECISION.json',{'decision':decision,'passed_scene_count':passscenes,'local_mismatch_scene_count':local,'negative_controls_pass':negpass,'negative_controls':negatives,'scene_gates':gates,'front_lock':locks,'original_R1_decision':'R1_HOLD_WEAK_OR_UNSTABLE','original_R1A_decision':'R1A_RESIDENCE_SUFFICIENT_STOP_UPLIFT_ATTRIBUTION','R1_1':'NOT_EXECUTED','R2':'NOT_EXECUTED','CFD':'NOT_EXECUTED','primary':'z10/300s/threshold.001ppm;equal-prior release-pooled Brier','seed_exclusion':'paired seed excluded from all3 releases and all9 candidates in each template bank'})
 print(decision,'passed',passscenes,'local',local,'negative',negpass)
 print(pd.DataFrame(gates)[['scene','arm','oracle_top1','baseline_top1','penalty_pp','mean_error_m','direction_fraction','consistent_seed_count','all_six']].to_string(index=False))

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='posthoc':
  envs=['F1','F2','C06','C08','S06','S08','H1','H2'];seeds=list(range(31001,31009));a=load_bank(ROOT/'evidence/lakeshore_r1a_deconfound_20261003/observations',envs,seeds)
  pairs=[(f'F{i}',m,arm,f'F{i}') for i in [1,2] for m,arm in [(f'F{i}','oracle'),(f'C0{6 if i==1 else 8}','uniform'),(f'S0{6 if i==1 else 8}','profile'),(f'H{i}','horizontal_diagnostic')]]
  t=score_bank(a,envs,seeds,pairs);t.to_csv(OUT/'R1A_POSTHOC_EXPLORATORY_trials.csv',index=False)
  t.groupby(['scene','arm','threshold_factor','height','prefix_s']).agg(top1=('top1','mean'),mean_error_m=('candidate_error','mean'),signed_x_bias=('signed_x_bias','mean')).reset_index().to_csv(OUT/'R1A_POSTHOC_EXPLORATORY_summary.csv',index=False)
  print('Exploratory original R1A re-score saved; frozen decisions unchanged.')
 else:
  a=load_bank(OUT/'observations',ENVS,SEEDS,True);pairs=[]
  for s in SCENES:pairs.extend([('F_'+s,'F_'+s,'oracle',s),('F_'+s,'C_'+s,'uniform',s),('F_'+s,'S_'+s,'profile',s),('C_'+s,'C_'+s,'negative_uniform',s)])
  t=score_bank(a,ENVS,SEEDS,pairs);t.to_csv(OUT/'candidate_trials.csv',index=False);finalize(t)
