#!/usr/bin/env python3
"""Final H01 factorized neural first-passage M1 + source-evidence gate.

This is the final preregistered neural implementation of the CTT M2/M3
factorization, not a post-hoc score blend:

  p(F=never|x) = 1 - p_e(x)
  p(F=t|x)     = p_e(x) p_phi(t|F<never,x), t=0..79

Training uses two proper conditional likelihoods with fixed unit contribution:
  L = BCE(ever) + CE(phase | ever).
No localization/rank/posterior/planner signal is used by training or checkpoint
selection.  The phase loss is conditional on an event, matching the exact
placement/count factorization; it is not an outcome-tuned class weight.

Forward-context provenance is fixed: H01 predictive8 was generated with one
native --wind input across reserved trajectories, so trajectory-specific local
wind estimates are forbidden here. Inputs are source/query geometry plus causal
absolute-time/route context.

Fresh combination for final source-rank opening:
  train: trajectories 4001..4003, members 0..4
  validation/checkpoint: trajectory 4004, member 5
  final test: trajectory 4005, member 6
Member7 is not used by this version.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,random
from pathlib import Path
import numpy as np, torch
from torch import nn
from scipy.stats import binomtest
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('fw',HERE/'train_h01_neural_first_passage_fixedwind_gate.py');fw=importlib.util.module_from_spec(sp);sp.loader.exec_module(fw)
b=fw.b
TRAIN_TRAJ=(0,1,2);VAL_TRAJ=(3,);TEST_TRAJ=(4,);TRAIN_MEM=(0,1,2,3,4);VAL_MEM=(5,);TEST_MEM=(6,)
SEED=20260835;BATCH=2048;MAX_EPOCHS=50;PATIENCE=7;GEOM_DIM=10

def digest(s):return hashlib.sha256(s.encode()).digest()
def prepare(a):
 root=a.audit_root;cs=b.carrier_rows(root/'artifacts_pf_dei_v3/source_region_3d_support_manifest.csv');sch=[b.read_schedule(a.maponly_root/f'H01/reserved/trajectory_seed_{4001+i}.csv') for i in range(5)];dum=[np.zeros((len(x),3),np.float32) for x in sch];stops=[b.stop_records(sch[i],dum[i]) for i in range(5)];assert [len(x) for x in stops]==[10,10,10,9,10]
 bank=root/'remote_full8/PF_DEI_H01_SOURCE_INFORMATION_AUDIT_20260829/predictive8';lab=[[None]*5 for _ in cs]
 for ci,c in enumerate(cs):
  ss=[b.read_stream(bank/f'member_{m:02d}/{c["id"]}.bin') for m in range(7)]
  for tr in range(5):
   meas=b.sensor_batch(np.stack([ss[m][tr] for m in range(7)]));lab[ci][tr]=[b.first_passage(meas,st['idx']) for st in stops[tr]]
  if (ci+1)%50==0:print(f'PREPROCESS {ci+1}/210',flush=True)
 def make(trajs,mem):
  X=[];Y=[];C=[]
  for ci,c in enumerate(cs):
   for tr in trajs:
    for j,st in enumerate(stops[tr]):
     x=b.base_features(c,st)
     for m in mem:X.append(x);Y.append(int(lab[ci][tr][j][m]));C.append((ci,tr,j,m))
  return np.asarray(X,np.float32),np.asarray(Y,np.int64),C
 return cs,stops,bank,{'train':make(TRAIN_TRAJ,TRAIN_MEM),'val':make(VAL_TRAJ,VAL_MEM),'test':make(TEST_TRAJ,TEST_MEM)}

class Factorized(nn.Module):
 def __init__(self,d):
  super().__init__();self.enc=nn.Sequential(nn.Linear(d,128),nn.SiLU(),nn.Linear(128,128),nn.SiLU(),nn.Linear(128,128),nn.SiLU());self.surv=nn.Linear(128,1);self.phase=nn.Linear(128,80)
 def raw(self,x):h=self.enc(x);return self.surv(h).squeeze(1),self.phase(h)
 def probs(self,x):
  s,p=self.raw(x);pe=torch.sigmoid(s);ph=torch.softmax(p,1);return torch.cat([pe[:,None]*ph,(1-pe)[:,None]],1)
def factor_loss(m,x,y):
 s,p=m.raw(x);ev=(y<80).float();ls=nn.functional.binary_cross_entropy_with_logits(s,ev);mask=y<80
 lp=nn.functional.cross_entropy(p[mask],y[mask]) if bool(mask.any()) else p.sum()*0
 return ls+lp,ls,lp

def fit(D,out):
 X,Y,_=D['train'];XV,YV,_=D['val'];mean=X.mean(0);std=X.std(0);std[std<1e-6]=1;X=(X-mean)/std;XV=(XV-mean)/std
 torch.manual_seed(SEED);m=Factorized(X.shape[1]);opt=torch.optim.AdamW(m.parameters(),lr=2e-3,weight_decay=1e-5);g=torch.Generator().manual_seed(SEED);dl=torch.utils.data.DataLoader(torch.utils.data.TensorDataset(torch.from_numpy(X),torch.from_numpy(Y)),batch_size=BATCH,shuffle=True,generator=g);best=1e99;stale=0;hist=[]
 for ep in range(MAX_EPOCHS):
  m.train();tot=ts=tp=n=0
  for xb,yb in dl:
   l,ls,lp=factor_loss(m,xb,yb);opt.zero_grad(set_to_none=True);l.backward();opt.step();tot+=float(l.detach())*len(xb);ts+=float(ls.detach())*len(xb);tp+=float(lp.detach())*len(xb);n+=len(xb)
  m.eval()
  with torch.no_grad():vl,vs,vp=factor_loss(m,torch.from_numpy(XV),torch.from_numpy(YV))
  val=float(vl);hist.append({'epoch':ep,'train_total':tot/n,'train_survival':ts/n,'train_phase':tp/n,'val_total':val,'val_survival':float(vs),'val_phase':float(vp)});print('factor',ep,tot/n,ts/n,tp/n,val,float(vs),float(vp),flush=True)
  if val<best-1e-5:best=val;stale=0;torch.save({'state':m.state_dict(),'mean':torch.from_numpy(mean),'std':torch.from_numpy(std),'epoch':ep,'val_total':val},out/'factorized_best.pt')
  else:
   stale+=1
   if stale>=PATIENCE:break
 (out/'history.json').write_text(json.dumps(hist,indent=2)+'\n');ck=torch.load(out/'factorized_best.pt',weights_only=True);m.load_state_dict(ck['state']);return m,ck

def predict(m,ck,X):
 X=((X-ck['mean'].numpy())/ck['std'].numpy()).astype(np.float32);r=[];m.eval()
 with torch.no_grad():
  for s in range(0,len(X),BATCH):r.append(m.probs(torch.from_numpy(X[s:s+BATCH])).numpy())
 return np.concatenate(r)
def proper(P,Y):
 p=np.clip(P,1e-12,1);n=-np.log(p[np.arange(len(Y)),Y]);cdf=np.cumsum(P[:,:80],1);o=(Y[:,None]<=np.arange(80)[None,:]).astype(np.float32);return n,((cdf-o)**2).mean(1)
def rank(sc,t):x=sc[t];return float(1+np.count_nonzero(sc>x)+.5*(np.count_nonzero(sc==x)-1))
def sign(a,b):
 a=np.asarray(a);b=np.asarray(b);w=int((a<b).sum());l=int((a>b).sum());z=int((a==b).sum());n=w+l;return {'wins':w,'losses':l,'ties':z,'p':float(binomtest(w,n,.5,alternative='greater').pvalue) if n else 1.}
def summ(a):a=np.asarray(a);return {'mean_normalized_rank':float(((a-1)/209).mean()),'median_rank':float(np.median(a)),'top5':float((a<=5).mean()),'top10':float((a<=10).mean())}
def score(P,F):
 ii=np.arange(len(F));full=np.log(np.clip(P[:,ii,F],1e-12,1)).sum(1);pe=1-P[:,:,-1];ev=F<80;sv=np.where(ev[None,:],np.log(np.clip(pe,1e-12,1)),np.log(np.clip(1-pe,1e-12,1))).sum(1);ph=np.zeros_like(pe)
 for j in range(len(F)):
  if ev[j]:ph[:,j]=np.log(np.clip(P[:,j,F[j]]/np.clip(pe[:,j],1e-12,1),1e-12,1))
 return full,sv,ph.sum(1)
def perm_first(binary,key):
 q=[]
 for j,row in enumerate(binary):
  rng=np.random.default_rng(int.from_bytes(digest(f'CTT-FACT-FP-PERM|{key}|{j}')[:8],'big'));z=row[rng.permutation(80)];q.append(np.argmax(z) if z.any() else 80)
 return np.asarray(q,int)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--audit-root',type=Path,required=True);ap.add_argument('--maponly-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();
 if a.output.exists():raise SystemExit('REFUSE_OVERWRITE')
 a.output.mkdir(parents=True);random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED);torch.set_num_threads(4);cs,stops,bank,D=prepare(a);m,ck=fit(D,a.output);X,Y,C=D['test'];P=predict(m,ck,X);nll,br=proper(P,Y);P=P.reshape(210,10,81);norm=float(np.max(abs(P.sum(2)-1)))
 # final source-evidence opening on fresh trajectory4005/member6 combination
 B=[];F=[]
 for ci,c in enumerate(cs):
  phys=b.read_stream(bank/f'member_06/{c["id"]}.bin')[4][None,:];meas=b.sensor_batch(phys)[0];bb=np.stack([(meas[st['idx']]>b.TH) for st in stops[4]]);B.append(bb);F.append(np.array([np.argmax(z) if z.any() else 80 for z in bb],int))
 labperm=np.random.default_rng(SEED+99).permutation(210);rows=[]
 for truth in range(210):
  fu,sv,ph=score(P,F[truth]);fp=perm_first(B[truth],cs[truth]['id']);fup,_,_=score(P,fp);fulab=sv+ph[labperm];rows.append({'truth':truth,'carrier_id':cs[truth]['id'],'rank_full':rank(fu,truth),'rank_survival':rank(sv,truth),'rank_time_permute':rank(fup,truth),'rank_phase_label_shuffle':rank(fulab,truth)})
 with open(a.output/'source_cases.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 A={k:np.array([r[k] for r in rows]) for k in ('rank_full','rank_survival','rank_time_permute','rank_phase_label_shuffle')};S={k:summ(v) for k,v in A.items()};cmp={'full_vs_survival':sign(A['rank_full'],A['rank_survival']),'full_vs_time_permute':sign(A['rank_full'],A['rank_time_permute']),'full_vs_phase_label_shuffle':sign(A['rank_full'],A['rank_phase_label_shuffle'])};g={'first_passage_beats_survival':S['rank_full']['mean_normalized_rank']<S['rank_survival']['mean_normalized_rank'] and cmp['full_vs_survival']['p']<=.01,'top10_non_degrade_vs_survival':S['rank_full']['top10']>=S['rank_survival']['top10'],'time_load_bearing':S['rank_full']['mean_normalized_rank']<S['rank_time_permute']['mean_normalized_rank'] and cmp['full_vs_time_permute']['p']<=.01,'candidate_phase_load_bearing':S['rank_full']['mean_normalized_rank']<S['rank_phase_label_shuffle']['mean_normalized_rank'] and cmp['full_vs_phase_label_shuffle']['p']<=.01,'normalization':norm<1e-6};R={'contract':'CTT_H01_FACTORIZED_NEURAL_FIRST_PASSAGE_FINAL_GATE_V1','split':{'train_trajectories':[4001,4002,4003],'train_members':[0,1,2,3,4],'val_trajectory':4004,'val_member':5,'test_trajectory':4005,'test_member':6},'checkpoint':{'epoch':int(ck['epoch']),'val_factorized_loss':float(ck['val_total'])},'test_proper':{'nll':float(nll.mean()),'integrated_brier':float(br.mean()),'normalization_error':norm},'source_summary':S,'comparisons':cmp,'gate':g,'verdict':'CTT_H01_FACTORIZED_NEURAL_FIRST_PASSAGE_FINAL_PASS' if all(g.values()) else 'CTT_H01_FACTORIZED_NEURAL_FIRST_PASSAGE_FINAL_NO_GO'};(a.output/'summary.json').write_text(json.dumps(R,indent=2)+'\n');(a.output/'VERDICT.txt').write_text(R['verdict']+'\n');print(json.dumps(R,indent=2))
if __name__=='__main__':main()
