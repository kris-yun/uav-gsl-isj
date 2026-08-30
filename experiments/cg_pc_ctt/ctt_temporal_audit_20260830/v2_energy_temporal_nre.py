#!/usr/bin/env python3
from __future__ import annotations
import json, math, hashlib, sys, time
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
sys.path.insert(0,'/mnt/data/h01_temporal_gate')
import train_eval_ctt_temporal_nre as v1

OUT=Path('/mnt/data/h01_temporal_gate/v2');OUT.mkdir(exist_ok=True)
INPUT=v1.INPUT
PRED_MEMBERS=(0,1,2); TRAIN_OBS=(4,5); VAL_OBS=6; TEST_OBS=3
TRAIN_TRAJ=(0,1,2); VAL_TRAJ=3; TEST_TRAJ=4
SEEDS=(1701,1702,1703); STEPS=300

class EnergyTemporalNRE(nn.Module):
    def __init__(self,w=32):
        super().__init__();self.enc=nn.Sequential(nn.Linear(INPUT,w),nn.GELU());self.blocks=nn.ModuleList([v1.CausalBlock(w,d) for d in (1,2,4,8,16,32)]);self.temporal=nn.Sequential(nn.Linear(2*w,32),nn.GELU(),nn.Linear(32,1))
        # softplus^{-1}(1), positive physics coefficient learned on simulation train/val only.
        self.raw_alpha=nn.Parameter(torch.tensor(math.log(math.e-1.0),dtype=torch.float32))
    def forward(self,x,mask,energy_z):
        h=self.enc(x)
        for b in self.blocks:h=b(h)
        ww=mask[...,None].to(h.dtype);L=mask.sum(1);mean=(h*ww).sum(1)/L[:,None];final=h[torch.arange(len(h)),L-1]
        return F.softplus(self.raw_alpha)*energy_z + self.temporal(torch.cat([mean,final],1)).squeeze(1)

def pred_slice(data,tr,cand,n):return data.bm[tr,cand,list(PRED_MEMBERS),:n].astype(float)
def energy_all(data,tr,true,om,cut):
    n=data.nblocks(tr,cut);obs=data.bm[tr,true,om,:n].astype(float);pred=data.bm[tr][:,list(PRED_MEMBERS),:n].astype(float);M=len(PRED_MEMBERS)
    first=np.linalg.norm(pred-obs[None,None,:],axis=2).mean(1);pair=np.zeros(210)
    for i in range(M):
        for j in range(M):pair+=np.linalg.norm(pred[:,i]-pred[:,j],axis=1)
    e=(first-.5*pair/(M*M))/math.sqrt(n); evidence=-e
    return e,(evidence-evidence.mean())/max(evidence.std(),1e-8)

def prim(data,tr,true,om,cand,cut):
    n=data.nblocks(tr,cut);return v1.primitives(data.bm[tr,true,om,:n],data.bm[tr,cand,list(PRED_MEMBERS),:n])
def feat(data,tr,true,om,cand,cut,order=None):return v1.sequence_features(prim(data,tr,true,om,cand,cut),order)

def pad(seq):return v1.pad_batch(seq)
def perm(n,key):return v1.deterministic_perm(n,key)

def make_pairs(data,rng,batch,split,seedkey):
    A=[];B=[];AP=[];BP=[];EA=[];EB=[]
    for k in range(batch):
        if split=='train':tr=int(rng.choice(TRAIN_TRAJ));om=int(rng.choice(TRAIN_OBS))
        else:tr=VAL_TRAJ;om=VAL_OBS
        true=int(rng.integers(210));neg=int(rng.integers(209));neg+=int(neg>=true);u=int(rng.integers(1,6));cut=float(data.bytime[u][int(rng.integers(10))]) if split=='train' else data.med[u]
        _,ez=energy_all(data,tr,true,om,cut);pa=prim(data,tr,true,om,true,cut);pb=prim(data,tr,true,om,neg,cut);q=perm(len(pa),f'V2|{seedkey}|{split}|{tr}|{om}|{true}|{neg}|{u}|{k}')
        A.append(v1.sequence_features(pa));B.append(v1.sequence_features(pb));AP.append(v1.sequence_features(pa,q));BP.append(v1.sequence_features(pb,q));EA.append(ez[true]);EB.append(ez[neg])
    return A,B,AP,BP,np.array(EA,np.float32),np.array(EB,np.float32)

def loss_fn(model,b):
    A,B,AP,BP,EA,EB=b;n=len(A);x,m=pad(A+B+AP+BP);ez=torch.from_numpy(np.r_[EA,EB,EA,EB]);z=model(x,m,ez);la,lb,lap,lbp=torch.split(z,n)
    bce=.5*(F.binary_cross_entropy_with_logits(la,torch.ones_like(la))+F.binary_cross_entropy_with_logits(lb,torch.zeros_like(lb)));order=F.softplus(-((la-lb)-(lap-lbp))).mean();return bce+order,bce,order

def train(data,seed):
    torch.set_num_threads(4);torch.manual_seed(seed);model=EnergyTemporalNRE();opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-4);rng=np.random.default_rng(seed+20260830);vrng=np.random.default_rng(seed+99000);val=make_pairs(data,vrng,96,'val',seed);best=None;hist=[]
    for step in range(1,STEPS+1):
        model.train();lo,bc,od=loss_fn(model,make_pairs(data,rng,24,'train',seed+step*31));opt.zero_grad();lo.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
        if step==1 or step%50==0:
            model.eval();
            with torch.no_grad():vl,vb,vo=loss_fn(model,val)
            alpha=float(F.softplus(model.raw_alpha));row={'step':step,'val_total':float(vl),'val_bce':float(vb),'val_order':float(vo),'physics_alpha':alpha};hist.append(row);print('V2TRAIN',seed,row,flush=True)
            if best is None or float(vl)<best[0]:
                best=(float(vl),step,{k:v.detach().cpu().clone() for k,v in model.state_dict().items()},alpha)
                torch.save({'seed':seed,'best_step':step,'state_dict':best[2],'contract':'CTT_ENERGY_PLUS_CAUSAL_TEMPORAL_NRE_V2'},OUT/f'model_{seed}.pt');(OUT/f'train_{seed}.json').write_text(json.dumps({'best_step':step,'best_val':best[0],'physics_alpha':alpha,'history':hist},indent=2))
    model.load_state_dict(best[2]);return model

def models(data):
    out=[]
    for s in SEEDS:
        p=OUT/f'model_{s}.pt'
        if not p.exists():out.append(train(data,s))
        else:ck=torch.load(p,map_location='cpu',weights_only=False);q=EnergyTemporalNRE();q.load_state_dict(ck['state_dict']);q.eval();out.append(q)
    return out

def score_all(ms,data,true,cut,permuted=False):
    tr=TEST_TRAJ;om=TEST_OBS;n=data.nblocks(tr,cut);order=perm(n,f'V2TEST|traj={tr}|member={om}|cut={cut:.9f}|n={n}') if permuted else None;_,ez=energy_all(data,tr,true,om,cut);seq=[feat(data,tr,true,om,c,cut,order) for c in range(210)];x,m=pad(seq);te=torch.from_numpy(ez.astype(np.float32))
    with torch.no_grad():return np.mean(np.stack([q(x,m,te).numpy() for q in ms]),0)

def raw_energy(data,true,cut):return energy_all(data,TEST_TRAJ,true,TEST_OBS,cut)[0]

def evaluate(data,ms,timing_mode='median'):
    cov=v1.coverage_indices(v1.carrier_rows(),32);rows=[]
    timing={u:([data.med[u]] if timing_mode=='median' else data.bytime[u]) for u in range(1,6)}
    for u in range(1,6):
        for ti,cut in enumerate(timing[u]):
            for true in cov:
                s=score_all(ms,data,true,cut,False);sp=score_all(ms,data,true,cut,True);e=raw_energy(data,true,cut);r=v1.rank_desc(s,true);rp=v1.rank_desc(sp,true);re=v1.rank_asc(e,true);post=v1.rank_desc(np.log(np.maximum(data.prior,1e-300))+s,true)
                rows.append([u,ti,cut,data.nblocks(TEST_TRAJ,cut),true,r,rp,re,post])
            print('V2EVAL',timing_mode,u,ti+1,len(timing[u]),flush=True)
    import pandas as pd
    df=pd.DataFrame(rows,columns=['update','timing_index','cut_time_s','blocks','true','network','perm','energy','post'])
    for q in ('network','perm','energy','post'):df[q+'_norm']=(df[q]-1)/209
    def agg(g):
        return {q:{'top5':float((g[q]<=5).mean()),'top10':float((g[q]<=10).mean()),'median_rank':float(g[q].median()),'mean_norm_rank':float(g[q+'_norm'].mean())} for q in ('network','perm','energy','post')}
    overall=agg(df);by={str(u):agg(g) for u,g in df.groupby('update')};wins=int((df.network<df.perm).sum());loss=int((df.network>df.perm).sum());ties=len(df)-wins-loss;n=wins+loss
    from math import comb
    p=min(1.0,2*sum(comb(n,i) for i in range(min(wins,loss)+1))/(2**n)) if n else 1
    summary={'contract':'CTT_ENERGY_PLUS_CAUSAL_TEMPORAL_NRE_V2_H01_GATE','timing_mode':timing_mode,'test':'trajectory4005_member3_FRESH_OBSERVATION_HOLDOUT','predictor_members':list(PRED_MEMBERS),'overall':overall,'by_update':by,'time_permute':{'wins':wins,'losses':loss,'ties':ties,'sign_p':p}}
    df.to_csv(OUT/f'{timing_mode}_cases.csv',index=False);(OUT/f'{timing_mode}_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));return summary

def selftest(data,ms):
    cut=data.med[3];n=data.nblocks(TEST_TRAJ,cut);obs=data.bm[TEST_TRAJ,0,TEST_OBS,:n];p=data.bm[TEST_TRAJ,0,list(PRED_MEMBERS),:n];a=v1.primitives(obs,p);b=v1.primitives(obs,p[[2,0,1]]);err=float(np.max(np.abs(a-b)));assert err<1e-7
    o={'predictor_member_permutation_max_abs':err,'fresh_test_member':TEST_OBS,'test_member_not_in_predictors':TEST_OBS not in PRED_MEMBERS,'pass':True};(OUT/'selftest.json').write_text(json.dumps(o,indent=2));print('V2SELFTEST',o)

if __name__=='__main__':
    d=v1.Data();ms=models(d);selftest(d,ms);evaluate(d,ms,'median')
