import os
from pathlib import Path
import numpy as np,pandas as pd,json,hashlib
R=Path(os.environ['ME_REVIEW_ROOT']); O=Path(os.environ['ME_AUDIT_OUT']);O.mkdir(exist_ok=True)
bank=pd.read_csv(R/'forward/candidate_mark_bank.csv');tar=np.load(R/'protocol/JTD_E2_FRESH_TARGET_10x30.npy');ref=np.load(R/'protocol/JTD_E2_REFERENCE_12x10x30.npy');old=pd.read_csv(R/'evaluation/CANDIDATE_SCORES_ALL.csv')
print('shapes',tar.shape,ref.shape)

def profile(y,z):
 y=np.asarray(y,dtype=np.float64);z=np.asarray(z,dtype=np.float64)
 m=y>0;n=m.sum()
 if n<4:return dict(ll=0.,n=int(n),rho=0.,slope=0.,den=0.,syy=0.,r2=0.,zeros=int((z[m]<=0).sum()))
 x=np.log(np.maximum(z[m],1e-9));v=np.log(y[m]);xc=x-x.mean();yc=v-v.mean();den=xc@xc;syy=yc@yc;dot=xc@yc
 b=max(0.,dot/den) if den>1e-12 else 0.;res=yc-b*xc; rss=max(float(res@res),1e-12)
 return dict(ll=-.5*n*np.log(rss/n),n=int(n),rho=float(dot/np.sqrt(den*syy)) if den*syy>0 else 0.,slope=float(b),den=float(den),syy=float(syy),r2=float(max(0,dot)**2/(den*syy)) if den>1e-12 and syy>0 else 0.,zeros=int((z[m]<=0).sum()))

def rank(a,i): return int(1+(a>a[i]).sum())
rows=[]; diag=[];bankstat=[];debugdiff=0.
for e in range(3):
 be=bank[bank.environment_index==e].sort_values(['source_index','probe_rank'])
 p=be.presence_prob.to_numpy().reshape(6,30); u=be.multiplicity_mean_unconditional.to_numpy().reshape(6,30);mu=be.multiplicity_mean_conditional.to_numpy().reshape(6,30)
 pp=np.clip(p,1e-6,1-1e-6)
 counts=(ref[e]>0).sum(axis=1);UU=np.divide(ref[e].sum(axis=1),counts,out=np.zeros((6,10,30)),where=counts>0)
 sc=(ref[e]>0).sum(axis=(1,2));Ustat=np.divide(ref[e].sum(axis=(1,2)),sc,out=np.zeros((6,30)),where=sc>0)
 for k in range(6):
  bankstat.append(dict(env=e,source=k,p_zero=int((p[k]==0).sum()),p_below_floor=int((p[k]<1e-6).sum()),p_above_ceiling=int((p[k]>1-1e-6).sum()),mu_min=float(mu[k].min()),mu_median_pos=float(np.median(mu[k][mu[k]>0])),mu_max=float(mu[k].max()),mu_nearone=int(((mu[k]>0)&(mu[k]<1.1)).sum()),u_max=float(u[k].max())))
 for s in range(6):
  for j in range(4):
   y=tar[e,s,j];h=y>0
   occ=np.sum(h[None,:,:]*np.log(pp[:,None,:])+(~h[None,:,:])*np.log1p(-pp[:,None,:]),axis=(1,2))
   pm=[profile(y,np.tile(mu[k],(10,1))) for k in range(6)]
   pu=[profile(y,UU[k]) for k in range(6)]
   ps=[profile(y,np.tile(Ustat[k],(10,1))) for k in range(6)]
   # Diagnostic variants: same target / score, no tuning; NOT method confirmation
   p_unc=[profile(y,np.tile(u[k],(10,1))) for k in range(6)]
   marks=np.array([z['ll'] for z in pm]);um=np.array([z['ll'] for z in pu]);us=np.array([z['ll'] for z in ps]);uu=np.array([z['ll'] for z in p_unc])
   mse=[]
   for k in range(6):
    est=np.tile(np.maximum(u[k],1e-9),(10,1));scale=max(0.,np.sum(y*est)/np.sum(est*est));mse.append(np.sum((y-scale*est)**2))
   scores={'B0':occ,'M':occ+marks,'U':occ+um,'B2':-np.array(mse),'posthoc_U_static':occ+us,'posthoc_M_unconditional_sameprofile':occ+uu,'posthoc_mark_only':marks}
   o=old[(old.environment_index==e)&(old.source_index==s)&(old.target_index==j)].sort_values('candidate_index')
   debugdiff=max(debugdiff,float(abs(occ-o.occurrence_ll.to_numpy()).max()),float(abs(marks-o.conditional_mark_ll.to_numpy()).max()),float(abs(um-o.upper_mark_ll.to_numpy()).max()),float(abs(np.array(mse)-o.scaled_value_SSE.to_numpy()).max()))
   for name,a in scores.items():
    rows.append(dict(env=e,source=s,target=j,method=name,rank=rank(a,s),unique_top1=bool(a[s]==a.max() and np.sum(a==a.max())==1),top1=int(np.argmax(a)),score_true=float(a[s]),pair_margin=float(a[s]-a[s^1])))
   for k in range(6):
    for name,z in [('M',pm[k]),('U',pu[k]),('U_static',ps[k]),('u_log',p_unc[k])]:
     diag.append(dict(env=e,source=s,target=j,candidate=k,template=name,**z))
print('max original difference',debugdiff)
df=pd.DataFrame(rows); dd=pd.DataFrame(diag); bs=pd.DataFrame(bankstat)
df.to_csv(O/'diagnostic_scores.csv',index=False);dd.to_csv(O/'profile_diagnostics.csv',index=False);bs.to_csv(O/'bank_diagnostics.csv',index=False)
print(df.groupby(['env','method']).agg(rank=('rank','mean'),top1=('unique_top1','mean'),pair_margin=('pair_margin','mean')).round(6).to_string())
print('bank:');print(bs.to_string(index=False))
print('profile all candidate:');print(dd.groupby(['env','template']).agg(n=('n','median'),r2=('r2','median'),rho=('rho','median'),zero_slope=('slope',lambda x:(x==0).mean()),zero_template=('zeros','mean')).to_string())
print('profile true only:');print(dd[dd.source==dd.candidate].groupby(['env','template']).agg(n=('n','median'),r2=('r2','median'),rho=('rho','median'),zero_slope=('slope',lambda x:(x==0).mean()),zero_template=('zeros','mean')).to_string())
