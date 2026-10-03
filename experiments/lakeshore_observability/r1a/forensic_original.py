"""Verify old exploratory claims without editing its data or frozen decision."""
import re, numpy as np,pandas as pd
from scipy.stats import spearmanr
from common import *
hit=[]; wind=[]; allocation=[]; prefix=[]; peaks=[]
for p in sorted((OLD/'observations').glob('*.csv')):
 m=re.fullmatch(r'(N0|L1|F1|F2)_x(\d+)_y(-?\d+)_r(\d+)_seed(\d+)',p.stem)
 if not m:continue
 env,x,y,r,k=m[1],int(m[2]),int(m[3]),int(m[4]),int(m[5]);d=pd.read_csv(p)
 for z,q in d.groupby('z'):
  hit.append(dict(environment=env,release=r,seed=k,source_x=x,source_y=y,height=z,hit_rate=float((q.concentration>=.001).mean())))
  if r==10 and x==20 and y==0 and k==30001:wind.append(dict(environment=env,height=z,mean_u=q.u.mean(),mean_w=q.w.mean()))
pk=pd.read_csv(OLD/'M3_threshold_1.csv')
for (env,r,k),q in pk.groupby(['environment','release','seed']):
 g=q.groupby('source_x').peak_x.mean();rho=spearmanr(g.index,g.values).statistic
 peaks.append(dict(environment=env,release=r,seed=k,rho=float(rho) if np.isfinite(rho) else None))
h=pd.DataFrame(hit);h.to_csv(OUT/'original_hit_rates_by_trial.csv',index=False)
h.groupby(['environment','release','height']).hit_rate.mean().to_csv(OUT/'original_hit_summary.csv')
pd.DataFrame(wind).to_csv(OUT/'original_path_wind_summary.csv',index=False)
for (env,r,k),q in h[h.height.isin([10,30])].groupby(['environment','release','seed']):
 g=q.groupby(['source_x','height']).hit_rate.mean().unstack();den=(g[10]+g[30]).to_numpy();ratio=np.divide(g[30].to_numpy(),den,out=np.zeros(3),where=den>0)
 rho=spearmanr(g.index,ratio).statistic
 allocation.append(dict(environment=env,release=r,seed=k,rho=float(rho) if np.isfinite(rho) else None,ratio_x20=float(ratio[0]),ratio_x50=float(ratio[1]),ratio_x80=float(ratio[2])))
pd.DataFrame(allocation).to_csv(OUT/'original_R30_source_x_spearman.csv',index=False)
pd.DataFrame(peaks).to_csv(OUT/'original_peak_source_x_spearman.csv',index=False)
m4=pd.read_csv(OLD/'M4_trials_threshold_1.csv');m4['margin']=m4.best_false_brier-m4.true_brier
marg=m4.groupby(['environment','release','height']).agg(margin_median=('margin','median'),margin_min=('margin','min'),top1=('top1','mean'),median_rank=('true_rank','median'))
marg.to_csv(OUT/'original_brier_margin_summary.csv')
assert json.loads((OLD/'FINAL_DECISION.json').read_text())['decision']=='R1_HOLD_WEAK_OR_UNSTABLE'
mid=h[(h.release==10)&(h.height.isin([10,30]))].groupby(['environment','height']).hit_rate.mean()
write_json('original_forensic_verification.json',{'original_decision_unchanged':True,'hit_summary_mid':{f'{e}_z{z:g}':float(v) for (e,z),v in mid.items()},'note':'All analyses here are exploratory verification, never retroactive original-gate changes.'})
print(mid.to_string());print(marg.loc[(slice(None),10,30),:].to_string())
