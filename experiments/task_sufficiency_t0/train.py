"""Frozen tiny CPU feasibility probe; all preprocessing fitted within realization fold."""
import json,hashlib
from pathlib import Path
import numpy as np,pandas as pd,torch
from torch import nn
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.metrics import roc_auc_score,accuracy_score
torch.set_num_threads(2)
ROOT=Path(__file__).resolve().parents[2];O=ROOT/'evidence/task_sufficiency_t0_20261003'
def save(n,x):(O/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
class Net(nn.Module):
 def __init__(self,d):
  super().__init__();self.enc=nn.Sequential(nn.Linear(d,48),nn.Tanh(),nn.Linear(48,8));self.src=nn.Linear(8,2);self.pred=nn.Linear(14,4);self.dec=nn.Linear(8,d)
 def forward(self,x,p):
  z=self.enc(x);return z,self.src(z),self.pred(torch.cat([z,p],1)),self.dec(z)
def main():
 runs=json.loads((O/'RUNS.json').read_text()); rows=[]; arrays={}
 for case in sorted({r['context'] for r in runs}):
  rr=[r for r in runs if r['context']==case]; X=[];P=[];Y=[];F=[];G=[];R=[];T=[];UID=[]
  for r in rr:
   df=pd.read_csv(O/(r['run_id']+'.observations.csv'));assert len(df)==301
   v=df[['x','y','z','u','v','w']].values; gas=df.concentration.values; hit=(gas>=.001).astype(float)
   obs=np.column_stack([v,np.log1p(gas),hit,(df.time.values-100)/600])
   for k in range(20,286,5):
    X.append(obs[k-19:k+1].ravel());P.append(v[[k+5,k+15],:3].ravel());Y.append(0 if r['source_id'].endswith('_1') else 1);F.append(hit[[k+5,k+15]]);G.append(np.log1p(gas[[k+5,k+15]]));R.append(r['replicate']);T.append(df.time.iloc[k]);UID.append(r['run_id'])
  X=np.array(X);P=np.array(P);Y=np.array(Y);F=np.array(F);G=np.array(G);R=np.array(R);T=np.array(T);UID=np.array(UID)
  arrays[case]=dict(history=X,future_xyz=P,source=Y,future_hit=F,future_log_concentration=G,replicate=R,end_time=T,run_id=UID)
  np.savez_compressed(O/(case.replace('/','_')+'.tensor.npz'),**arrays[case])
  for fold in range(1,5):
   tr=R!=fold;te=~tr; xs=StandardScaler().fit(X[tr]);ps=StandardScaler().fit(P[tr]);xx=xs.transform(X).astype('float32');pp=ps.transform(P).astype('float32')
   for modelseed in [61003,61004,61005]:
    for arm in ['raw','statistics','generic','source_only','joint']:
     if arm in ['raw','statistics'] and modelseed!=61003:continue
     if arm=='raw':z=xx
     elif arm=='statistics':
      a=xx.reshape(-1,20,9);z=np.concatenate([a.mean(1),a.std(1),a[:,-1],a[:,-1]-a[:,0]],1)
     else:
      torch.manual_seed(modelseed);net=Net(X.shape[1]);opt=torch.optim.Adam(net.parameters(),lr=.003)
      xt=torch.tensor(xx[tr]);pt=torch.tensor(pp[tr]);yt=torch.tensor(Y[tr],dtype=torch.long);ft=torch.tensor(F[tr],dtype=torch.float32);gt=torch.tensor(G[tr],dtype=torch.float32)
      # Order identical per source/replicate; aligned-time conditional variance does not use test data.
      for epoch in range(160):
       zt,st,pr,re=net(xt,pt)
       if arm=='generic':loss=((re-xt)**2).mean()+.01*(zt**2).mean()
       elif arm=='source_only':loss=nn.functional.cross_entropy(st,yt)+.01*(zt**2).mean()
       else:
        nuisance=torch.stack([zt[yt==s].reshape(3,-1,8).var(0,unbiased=False).mean() for s in [0,1]]).mean()
        loss=nn.functional.cross_entropy(st,yt)+nn.functional.binary_cross_entropy_with_logits(pr[:,:2],ft)+.1*((pr[:,2:]-gt)**2).mean()+.01*(zt**2).mean()+.1*nuisance
       opt.zero_grad();loss.backward();opt.step()
      with torch.no_grad():z=net.enc(torch.tensor(xx)).numpy()
      name=f'{case.replace("/","_")}_{fold}_{arm}_{modelseed}'
      torch.save({'state_dict':net.state_dict(),'history_mean':xs.mean_,'history_scale':xs.scale_,'future_mean':ps.mean_,'future_scale':ps.scale_},O/(name+'.pt'))
     zs=StandardScaler().fit(z[tr]);zz=zs.transform(z)
     source=LogisticRegression(C=1,max_iter=2000).fit(zz[tr],Y[tr]);prob=source.predict_proba(zz[te])[:,1]
     feature=np.column_stack([zz,pp]); fp=[];gp=[];gs=[]
     for h in range(2):
      if len(np.unique(F[tr,h]))==1:hp=np.full(te.sum(),(F[tr,h].sum()+1)/(tr.sum()+2))
      else:hp=LogisticRegression(C=1,max_iter=2000).fit(feature[tr],F[tr,h]).predict_proba(feature[te])[:,1]
      pred=Ridge(alpha=1).fit(feature[tr],G[tr,h]);mu=pred.predict(feature[te]); sigma=max(float(np.std(G[tr,h]-pred.predict(feature[tr]))),.01)
      fp.append(hp);gp.append(mu);gs.append(sigma)
     fp=np.column_stack(fp);gp=np.column_stack(gp);clip=np.clip(fp,1e-6,1-1e-6)
     nuisance=[];stability=[];unseen_stability=[]
     for s in [0,1]:
      early=tr&(Y==s)&(T<=300);late=tr&(Y==s)&(T>=440)
      nprobe=LogisticRegression(C=1,max_iter=2000).fit(zz[early],R[early]);nuisance.append(accuracy_score(R[late],nprobe.predict(zz[late])))
      ss=zz[tr&(Y==s)].reshape(3,-1,zz.shape[1]);stability.append(float(np.mean(np.var(ss,axis=0))))
      unseen_stability.append(float(np.mean((zz[te&(Y==s)]-ss.mean(axis=0))**2)))
     rec=dict(case=case,fold=fold,arm=arm,modelseed=modelseed,source_probe_accuracy=float(accuracy_score(Y[te],prob>=.5)),nuisance_probe_accuracy=float(np.mean(nuisance)),nuisance_chance=1/3,cross_seed_conditional_variance=float(np.mean(stability)),heldout_latent_prototype_mse=float(np.mean(unseen_stability)),latent_dim=int(z.shape[1]))
     for h,j in enumerate([10,30]):
      rec[f'brier_{j}']=float(np.mean((fp[:,h]-F[te,h])**2));rec[f'hit_nll_{j}']=float(np.mean(-F[te,h]*np.log(clip[:,h])-(1-F[te,h])*np.log(1-clip[:,h])))
      rec[f'log_concentration_nll_{j}']=float(np.mean(.5*np.log(2*np.pi*gs[h]**2)+.5*((G[te,h]-gp[:,h])/gs[h])**2))
     rows.append(rec)
     for i,(uid,t,y,p) in enumerate(zip(UID[te],T[te],Y[te],prob)):
      predictions.append(dict(case=case,fold=fold,arm=arm,modelseed=modelseed,run_id=uid,time=t,source=int(y),prob_source1=float(p),hit10=float(F[te][i,0]),hit30=float(F[te][i,1]),prob_hit10=float(fp[i,0]),prob_hit30=float(fp[i,1]),log_conc10=float(G[te][i,0]),log_conc30=float(G[te][i,1]),pred_log_conc10=float(gp[i,0]),pred_log_conc30=float(gp[i,1])))
     print(case,fold,arm,modelseed,round(rec['source_probe_accuracy'],3),flush=True)
 pd.DataFrame(rows).to_csv(O/'FOLD_METRICS.csv',index=False);pd.DataFrame(predictions).to_csv(O/'OOF_PREDICTIONS.csv',index=False)
 finalize()
def finalize():
 p=pd.read_csv(O/'OOF_PREDICTIONS.csv');f=pd.read_csv(O/'FOLD_METRICS.csv');out=[]
 for (case,arm),v in p.groupby(['case','arm']):
  # First ensemble predetermined initialization seeds; then equal-weight complete realization means.
  q=v.groupby(['run_id','time','source']).prob_source1.mean().reset_index();r=q.groupby(['run_id','source']).prob_source1.mean().reset_index(); y=r.source.values; prob=r.prob_source1.values
  correct=np.where(y==1,prob,1-prob);rank=np.where(correct>.5,1,np.where(correct<.5,2,1.5));fold=f[(f.case==case)&(f.arm==arm)]
  rec=dict(case=case,arm=arm,realizations=len(r),mean_source_rank=float(rank.mean()),realization_accuracy=float(accuracy_score(y,prob>=.5)),realization_auc=float(roc_auc_score(y,prob)))
  for col in ['source_probe_accuracy','nuisance_probe_accuracy','cross_seed_conditional_variance','heldout_latent_prototype_mse','brier_10','brier_30','hit_nll_10','hit_nll_30','log_concentration_nll_10','log_concentration_nll_30']:rec[col]=float(fold[col].mean())
  out.append(rec)
 result=pd.DataFrame(out);result.to_csv(O/'CASE_METRICS.csv',index=False);a=result[result.arm=='raw'].set_index('case');d=result[result.arm=='joint'].set_index('case');c=result[result.arm=='source_only'].set_index('case');b=result[result.arm=='generic'].set_index('case')
 rank=a.mean_source_rank-d.mean_source_rank;auc=d.realization_auc-a.realization_auc
 gates={'source_rank_noninferior_cases':int((rank>=0).sum()),'median_rank_improvement':float(rank.median()),'median_auc_gain':float(auc.median()),'prediction_brier_improves':bool(d[['brier_10','brier_30']].values.mean()<c[['brier_10','brier_30']].values.mean()),'prediction_nll_improves':bool(d[['hit_nll_10','hit_nll_30']].values.mean()<c[['hit_nll_10','hit_nll_30']].values.mean()),'nuisance_reduced_vs_generic':bool(d.nuisance_probe_accuracy.mean()<b.nuisance_probe_accuracy.mean()),'source_probe_strong':bool(d.source_probe_accuracy.mean()>=.75)}
 go=gates['source_rank_noninferior_cases']>=3 and (gates['median_rank_improvement']>0 or gates['median_auc_gain']>=.05) and all(gates[k] for k in ['prediction_brier_improves','prediction_nll_improves','nuisance_reduced_vs_generic','source_probe_strong'])
 save('FINAL_DECISION.json',dict(decision='T0_GO' if go else 'T0_FAIL_TASK_SUFFICIENCY_MAINLINE',gates=gates,scope='feasibility of this frozen lightweight estimator and source-blind route only; FAIL does not prove impossibility of all task-sufficient representations',new_simulations=0,closed_loop=False,next_dataset_generated=False))
if __name__=='__main__':
 predictions=[];main()
