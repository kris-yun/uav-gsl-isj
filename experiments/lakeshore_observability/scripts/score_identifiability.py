"""LOO stochastic-realization Brier ranking; no PMFS or learned model."""
import pathlib,json,numpy as np,pandas as pd
from extract_fixed_paths import ROOT,OUT,parse
ENVS=['N0','L1','F1','F2'];SOURCES=[(x,y) for x in [20,50,80] for y in [-20,0,20]];HEIGHTS=[10,30,60,100];RATES=[5,10,20]
def load():
 a=np.empty((4,3,9,8,4,300));xy=None
 for p in (OUT/'observations').glob('*.csv'):
  meta=parse(p)
  if not meta:continue
  env,x,y,rate,seed=meta;d=pd.read_csv(p);e=ENVS.index(env);r=RATES.index(rate);s=SOURCES.index((x,y));k=seed-30001
  for h,height in enumerate(HEIGHTS):a[e,r,s,k,h]=d[d.z==height].concentration.to_numpy()
  if xy is None:xy=d[d.z==10][['x','y']].to_numpy()
 return a,xy
def score(a,threshold):
 hit=a>=threshold;rows=[]
 for e,env in enumerate(ENVS):
  for r,rate in enumerate(RATES):
   for h,height in enumerate(HEIGHTS):
    v=hit[e,r,:,:,h,:]
    for k in range(8):
     prob=(1+v.sum(axis=1)-v[:,k,:])/9
     for s,(sx,sy) in enumerate(SOURCES):
      brier=np.mean((prob-v[s,k,:])**2,axis=1);true=brier[s];less=int((brier<true-1e-12).sum());equal=int(np.isclose(brier,true,rtol=0,atol=1e-12).sum())
      rank=less+(equal+1)/2
      rows.append(dict(environment=env,release=rate,height=height,source_x=sx,source_y=sy,seed=30001+k,true_rank=rank,top1=max(0,min(equal,1-less))/equal,top3=max(0,min(equal,3-less))/equal,true_brier=true,best_false_brier=float(np.delete(brier,s).min())))
 return pd.DataFrame(rows)
def primary(d):
 result=[]
 for env in ENVS:
  for rate in RATES:
   q=d[(d.environment==env)&(d.release==rate)];g=q.groupby('height').agg(top1=('top1','mean'),rank=('true_rank','median'));best=g.top1.idxmax();worst=g.top1.idxmin();spread=float(g.top1.max()-g.top1.min());rd=float(g.loc[worst,'rank']-g.loc[best,'rank'])
   pair=q[q.height.isin([best,worst])].pivot_table(index=['source_x','source_y','seed'],columns='height',values=['top1','true_rank'])
   if best==worst:xs=0;seeds=0
   else:
    delta=pair['true_rank'][worst]-pair['true_rank'][best];t=pair['top1'][best]-pair['top1'][worst]
    xs=int(((delta.groupby(level=0).median()>0)&(t.groupby(level=0).mean()>0)).sum());seeds=int(((delta.groupby(level=2).median()>0)&(t.groupby(level=2).mean()>0)).sum())
   n=d[(d.environment=='N0')&(d.release==rate)].groupby('height').top1.mean();nspread=float(n.max()-n.min());control=nspread<.10 or nspread<spread/2
   result.append(dict(environment=env,release=rate,best_height=int(best),worst_height=int(worst),top1_spread_pp=100*spread,median_rank_difference=rd,source_x_groups_same_direction=xs,seeds_same_direction=seeds,N0_spread_pp=100*nspread,control_pass=control,primary_pass=bool(env in ['F1','F2'] and spread>=.25 and rd>=2 and xs>=2 and seeds>=6 and control)))
 return result
if __name__=='__main__':
 a,xy=load();summaries={}
 for factor in [.5,1,2]:
  d=score(a,.001*factor);d.to_csv(OUT/f'M4_trials_threshold_{factor:g}.csv',index=False);d.groupby(['environment','release','height']).agg(top1=('top1','mean'),top3=('top3','mean'),median_true_rank=('true_rank','median')).to_csv(OUT/f'M4_summary_threshold_{factor:g}.csv')
  rows=primary(d);summaries[str(factor)]={'primary_rows':rows,'primary_pass':any(sum(q['primary_pass'] for q in rows if q['environment']==env)>=2 for env in ['F1','F2'])}
 (OUT/'M4_gate.json').write_text(json.dumps(summaries,indent=2));print(json.dumps(summaries['1'],indent=2))
