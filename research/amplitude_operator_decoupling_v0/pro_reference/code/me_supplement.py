import os
from pathlib import Path
exec(open(Path(__file__).with_name('me_current_audit.py')).read().split('rows=[]; diag=[];bankstat=[];debugdiff=0.')[0])
# Posthoc mechanism diagnostics: a single physically motivated fixed-exponent restriction.
# No parameter search, no new random draws or simulator use.
rec=[];pairs=[]; truecorr=[]
for e in range(3):
 be=bank[bank.environment_index==e].sort_values(['source_index','probe_rank'])
 p=be.presence_prob.to_numpy().reshape(6,30);u=be.multiplicity_mean_unconditional.to_numpy().reshape(6,30);mu=be.multiplicity_mean_conditional.to_numpy().reshape(6,30);pp=np.clip(p,1e-6,1-1e-6)
 cnt=(ref[e]>0).sum(axis=(1,2));us=np.divide(ref[e].sum(axis=(1,2)),cnt,out=np.zeros((6,30)),where=cnt>0)
 for a in [0,2,4]:
  b=a+1
  for name,x in [('mu',mu),('u',u),('U_static',us)]:
   zz=np.log(np.maximum(x[[a,b]],1e-9));rho=np.corrcoef(zz)[0,1];res=zz[1]-zz[1].mean()-np.dot(zz[0]-zz[0].mean(),zz[1]-zz[1].mean())/np.dot(zz[0]-zz[0].mean(),zz[0]-zz[0].mean())*(zz[0]-zz[0].mean())
   mask=(x[a]>0)&(x[b]>0)
   pairs.append(dict(env=e,pair=a//2,field=name,rho_all=rho,rho_positive=np.corrcoef(np.log(x[[a,b]][:,mask]))[0,1] if mask.sum()>2 else np.nan,relative_affine_residual=np.linalg.norm(res)/max(1e-300,np.linalg.norm(zz[1]-zz[1].mean()))))
 for s in range(6):
  for j in range(4):
   y=tar[e,s,j].astype(float);h=y>0;n=int(h.sum());occ=np.sum(h[None]*np.log(pp[:,None,:])+(~h[None])*np.log1p(-pp[:,None,:]),axis=(1,2))
   fix=[];cor=[]
   for k in range(6):
    pred=np.tile(mu[k],(10,1));z=np.log(y[h]);x=np.log(np.maximum(pred[h],1e-9));diff=z-x;rss=max(float(np.sum((diff-diff.mean())**2)),1e-12);fix.append(-.5*n*np.log(rss/n) if n>=4 else 0.)
   fixed=occ+np.array(fix)
   orig=old[(old.environment_index==e)&(old.source_index==s)&(old.target_index==j)].sort_values('candidate_index')
   v=orig.marked_ll.to_numpy()
   rec.append(dict(env=e,source=s,target=j,fixed_slope_rank=rank(fixed,s),old_M_rank=rank(v,s),B0_rank=rank(occ,s),fixed_pair_mark=float(fix[s]-fix[s^1])))
pd.DataFrame(rec).to_csv(O/'posthoc_fixed_slope_diagnostic.csv',index=False);pd.DataFrame(pairs).to_csv(O/'source_pair_geometry.csv',index=False)
print('FIXED SLOPE ONLY (not a result):');print(pd.DataFrame(rec).groupby('env').agg(rank=('fixed_slope_rank','mean'),top1=('fixed_slope_rank',lambda x:(x==1).mean()),delta=('fixed_pair_mark','mean')).to_string())
print('PAIR GEOMETRY');print(pd.DataFrame(pairs).round(5).to_string(index=False))
