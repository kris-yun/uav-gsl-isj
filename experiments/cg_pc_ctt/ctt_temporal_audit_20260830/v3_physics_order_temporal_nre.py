#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
sys.path.insert(0,'/mnt/data/h01_temporal_gate')
import train_eval_ctt_temporal_nre as v1
import v2_energy_temporal_nre as v2

OUT=Path('/mnt/data/h01_temporal_gate/v3'); OUT.mkdir(exist_ok=True)
INPUT=v1.INPUT
PRED_MEMBERS=(0,1,2); TRAIN_OBS=(4,5); VAL_OBS=6; TEST_OBS=3
TRAIN_TRAJ=(0,1,2); VAL_TRAJ=3; TEST_TRAJ=4
SEEDS=(1701,1702,1703); STEPS=300
FRESH_COUNT=64

class PhysicsOrderTemporalNRE(nn.Module):
    """Frozen energy anchor + causal temporal residual."""
    def __init__(self,w=32):
        super().__init__()
        self.enc=nn.Sequential(nn.Linear(INPUT,w),nn.GELU())
        self.blocks=nn.ModuleList([v1.CausalBlock(w,d) for d in (1,2,4,8,16,32)])
        self.temporal=nn.Sequential(nn.Linear(2*w,32),nn.GELU(),nn.Linear(32,1))
    def forward(self,x,mask,energy_z):
        h=self.enc(x)
        for b in self.blocks: h=b(h)
        ww=mask[...,None].to(h.dtype); L=mask.sum(1)
        mean=(h*ww).sum(1)/L[:,None]
        final=h[torch.arange(len(h)),L-1]
        return energy_z + self.temporal(torch.cat([mean,final],1)).squeeze(1)

def energy_all(data,tr,true,om,cut):
    n=data.nblocks(tr,cut)
    obs=data.bm[tr,true,om,:n].astype(float)
    pred=data.bm[tr][:,list(PRED_MEMBERS),:n].astype(float)
    M=len(PRED_MEMBERS)
    first=np.linalg.norm(pred-obs[None,None,:],axis=2).mean(1)
    pair=np.zeros(210)
    for i in range(M):
        for j in range(M): pair += np.linalg.norm(pred[:,i]-pred[:,j],axis=1)
    e=(first-.5*pair/(M*M))/math.sqrt(n)
    evidence=-e
    z=(evidence-evidence.mean())/max(evidence.std(),1e-8)
    return e,z

def prim(data,tr,true,om,cand,cut):
    n=data.nblocks(tr,cut)
    return v1.primitives(data.bm[tr,true,om,:n], data.bm[tr,cand,list(PRED_MEMBERS),:n])

def pad(seq): return v1.pad_batch(seq)
def perm(n,key): return v1.deterministic_perm(n,key)

def make_pairs(data,rng,batch,split,seedkey):
    A=[];B=[];AP=[];BP=[];EA=[];EB=[]
    for k in range(batch):
        if split=='train':
            tr=int(rng.choice(TRAIN_TRAJ)); om=int(rng.choice(TRAIN_OBS))
        else:
            tr=VAL_TRAJ; om=VAL_OBS
        true=int(rng.integers(210)); neg=int(rng.integers(209)); neg+=int(neg>=true)
        u=int(rng.integers(1,6))
        cut=float(data.bytime[u][int(rng.integers(10))]) if split=='train' else data.med[u]
        _,ez=energy_all(data,tr,true,om,cut)
        pa=prim(data,tr,true,om,true,cut); pb=prim(data,tr,true,om,neg,cut)
        q=perm(len(pa),f'V3|{seedkey}|{split}|{tr}|{om}|{true}|{neg}|{u}|{k}')
        A.append(v1.sequence_features(pa)); B.append(v1.sequence_features(pb))
        AP.append(v1.sequence_features(pa,q)); BP.append(v1.sequence_features(pb,q))
        EA.append(ez[true]); EB.append(ez[neg])
    return A,B,AP,BP,np.array(EA,np.float32),np.array(EB,np.float32)

def loss_fn(model,b):
    A,B,AP,BP,EA,EB=b; n=len(A)
    x,m=pad(A+B+AP+BP)
    ez=torch.from_numpy(np.r_[EA,EB,EA,EB])
    z=model(x,m,ez); la,lb,lap,lbp=torch.split(z,n)
    bce=.5*(F.binary_cross_entropy_with_logits(la,torch.ones_like(la))+
            F.binary_cross_entropy_with_logits(lb,torch.zeros_like(lb)))
    order=F.softplus(-((la-lb)-(lap-lbp))).mean()
    de=torch.from_numpy(EA-EB).to(la.dtype)
    w=torch.abs(de)
    signed=torch.sign(de)*(la-lb)
    phys=(w*F.softplus(-signed)).sum()/torch.clamp(w.sum(),min=1e-8)
    return bce+order+phys,bce,order,phys

def train(data,seed):
    torch.set_num_threads(4); torch.manual_seed(seed)
    model=PhysicsOrderTemporalNRE(); opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-4)
    rng=np.random.default_rng(seed+20260830); vrng=np.random.default_rng(seed+99000)
    val=make_pairs(data,vrng,96,'val',seed); best=None; hist=[]
    for step in range(1,STEPS+1):
        model.train(); lo,bc,od,ph=loss_fn(model,make_pairs(data,rng,24,'train',seed+step*31))
        opt.zero_grad(); lo.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),5); opt.step()
        if step==1 or step%50==0:
            model.eval()
            with torch.no_grad(): vl,vb,vo,vp=loss_fn(model,val)
            row={'step':step,'val_total':float(vl),'val_bce':float(vb),'val_order':float(vo),'val_physics':float(vp)}
            hist.append(row); print('V3TRAIN',seed,row,flush=True)
            if best is None or float(vl)<best[0]:
                best=(float(vl),step,{k:v.detach().cpu().clone() for k,v in model.state_dict().items()})
                torch.save({'seed':seed,'best_step':step,'state_dict':best[2],
                            'contract':'CTT_PHYSICS_ORDER_CONSISTENT_CAUSAL_TEMPORAL_NRE_V3'},OUT/f'model_{seed}.pt')
                (OUT/f'train_{seed}.json').write_text(json.dumps({'best_step':step,'best_val':best[0],'history':hist},indent=2))
    model.load_state_dict(best[2]); model.eval(); return model

def get_models(data):
    out=[]
    for s in SEEDS:
        p=OUT/f'model_{s}.pt'
        if p.exists():
            ck=torch.load(p,map_location='cpu',weights_only=False); q=PhysicsOrderTemporalNRE(); q.load_state_dict(ck['state_dict']); q.eval(); out.append(q)
        else: out.append(train(data,s))
    return out

def fresh_sources(data):
    rows=v1.carrier_rows(); used=set(v1.coverage_indices(rows,32))
    rem=[i for i in range(210) if i not in used]
    rem.sort(key=lambda i:hashlib.sha256(f'CTT-V3-FRESH-SOURCE|H01|{data.cids[i]}'.encode()).digest())
    return rem[:FRESH_COUNT]

def write_pretest_contract(data):
    fs=fresh_sources(data); ids=[data.cids[i] for i in fs]
    digest=hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest()
    code=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    contract={
      'contract':'CTT_PHYSICS_ORDER_CONSISTENT_CAUSAL_TEMPORAL_NRE_V3_PRETEST',
      'method':{
        'fixed_physics_coefficient':1.0,'predictor_members':list(PRED_MEMBERS),
        'loss':'balanced_BCE + time_order_contrast + gap_weighted_physics_order_consistency',
        'physics_consistency':'abs(delta_energy_z)*softplus(-sign(delta_energy_z)*delta_logit), normalized by total abs gap',
        'steps':STEPS,'model_seeds':list(SEEDS),'train_obs_members':list(TRAIN_OBS),'val_obs_member':VAL_OBS,
        'fresh_test_obs_member':TEST_OBS,'train_trajectories':[4001,4002,4003],
        'val_trajectory':4004,'fresh_test_trajectory':4005,
      },
      'fresh_source_count':len(fs),'fresh_source_indices':fs,'fresh_source_ids':ids,'fresh_source_list_sha256':digest,
      'fresh_source_exclusion':'excludes all 32 source carriers whose member3/member7 held-test ranks were previously opened in V1/V2 coverage evaluation',
      'first_gate_timing':'median of the ten frozen actual H01 PMFS source-update times for each update 1..5',
      'stress_timing':'all ten actual historical H01 update times only if median gate passes',
      'gates_reused_from_v2':{
        'time':'wins>losses; two-sided sign p<=0.01; chronological Top10 >= TIME-PERMUTE Top10 + 0.05',
        'physics':'network Top5 >= energy Top5 - 0.05; network Top10 >= energy Top10; network mean normalized rank <= energy mean normalized rank',
        'online':'every update network median normalized rank <=0.25; update1 network mean normalized rank <= energy + 0.05',
        'posterior':'overall posterior mean normalized rank <= network +0.05; no update posterior mean normalized rank > network +0.10',
      },
      'posterior':'q_t(s) proportional geometry_prior(s)*exp(f_theta(s,D_1:t)); rebuilt from fixed geometry prior, never cumulative-posterior multiplied',
      'code_sha256':code,'no_post_test_changes':True
    }
    (OUT/'PRETEST_CONTRACT.json').write_text(json.dumps(contract,indent=2))
    return contract

def score_all(ms,data,true,cut,permuted=False):
    tr=TEST_TRAJ; om=TEST_OBS; n=data.nblocks(tr,cut)
    order=perm(n,f'V3TEST|traj={tr}|member={om}|cut={cut:.9f}|n={n}') if permuted else None
    _,ez=energy_all(data,tr,true,om,cut)
    seq=[]
    for c in range(210):
        p=prim(data,tr,true,om,c,cut); seq.append(v1.sequence_features(p,order))
    x,m=pad(seq); te=torch.from_numpy(ez.astype(np.float32))
    with torch.no_grad(): return np.mean(np.stack([q(x,m,te).numpy() for q in ms]),0)

def raw_energy(data,true,cut): return energy_all(data,TEST_TRAJ,true,TEST_OBS,cut)[0]

def aggregate(df):
    out={}
    for q in ('network','perm','energy','post'):
        out[q]={'top5':float((df[q]<=5).mean()),'top10':float((df[q]<=10).mean()),
                'median_rank':float(df[q].median()),'mean_norm_rank':float(((df[q]-1)/209).mean())}
    return out

def evaluate(data,ms,timing_mode='median'):
    import pandas as pd
    fs=fresh_sources(data); rows=[]
    timing={u:([data.med[u]] if timing_mode=='median' else data.bytime[u]) for u in range(1,6)}
    for u in range(1,6):
        for ti,cut in enumerate(timing[u]):
            for true in fs:
                s=score_all(ms,data,true,cut,False); sp=score_all(ms,data,true,cut,True); e=raw_energy(data,true,cut)
                r=v1.rank_desc(s,true); rp=v1.rank_desc(sp,true); re=v1.rank_asc(e,true)
                post=v1.rank_desc(np.log(np.maximum(data.prior,1e-300))+s,true)
                rows.append([u,ti,cut,data.nblocks(TEST_TRAJ,cut),true,r,rp,re,post])
            print('V3EVAL',timing_mode,u,ti+1,len(timing[u]),flush=True)
    df=pd.DataFrame(rows,columns=['update','timing_index','cut_time_s','blocks','true','network','perm','energy','post'])
    overall=aggregate(df); by={str(u):aggregate(g) for u,g in df.groupby('update')}
    wins=int((df.network<df.perm).sum()); losses=int((df.network>df.perm).sum()); ties=len(df)-wins-losses; n=wins+losses
    from math import comb
    p=min(1.0,2*sum(comb(n,i) for i in range(min(wins,losses)+1))/(2**n)) if n else 1.0
    t=overall['network']['top10']>=overall['perm']['top10']+0.05 and wins>losses and p<=0.01
    ph=overall['network']['top5']>=overall['energy']['top5']-0.05 and overall['network']['top10']>=overall['energy']['top10'] and overall['network']['mean_norm_rank']<=overall['energy']['mean_norm_rank']
    on=all(by[str(u)]['network']['median_rank']<=1+0.25*209 for u in range(1,6)) and by['1']['network']['mean_norm_rank']<=by['1']['energy']['mean_norm_rank']+0.05
    po=overall['post']['mean_norm_rank']<=overall['network']['mean_norm_rank']+0.05 and all(by[str(u)]['post']['mean_norm_rank']<=by[str(u)]['network']['mean_norm_rank']+0.10 for u in range(1,6))
    summary={'contract':'CTT_PHYSICS_ORDER_CONSISTENT_CAUSAL_TEMPORAL_NRE_V3_H01_GATE','timing_mode':timing_mode,
             'fresh_test':'trajectory4005_member3_on_fresh_source_subset','fresh_source_count':len(fs),
             'overall':overall,'by_update':by,'time_permute':{'wins':wins,'losses':losses,'ties':ties,'sign_p':p},
             'gates':{'time':bool(t),'physics_non_degradation':bool(ph),'online':bool(on),'posterior':bool(po)},
             'verdict':'PASS' if t and ph and on and po else 'NO_GO'}
    df.to_csv(OUT/f'{timing_mode}_cases.csv',index=False); (OUT/f'{timing_mode}_summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2),flush=True)
    return summary

def selftest(data,ms):
    cut=data.med[3]; n=data.nblocks(TEST_TRAJ,cut); obs=data.bm[TEST_TRAJ,0,TEST_OBS,:n]; p=data.bm[TEST_TRAJ,0,list(PRED_MEMBERS),:n]
    a=v1.primitives(obs,p); b=v1.primitives(obs,p[[2,0,1]])
    err=float(np.max(np.abs(a-b))); assert err<1e-7
    q=PhysicsOrderTemporalNRE()
    for par in q.temporal.parameters(): par.data.zero_()
    seq=[v1.sequence_features(a)]; x,m=pad(seq); ez=torch.tensor([0.731],dtype=torch.float32)
    with torch.no_grad(): ferr=abs(float(q(x,m,ez)[0])-0.731)
    assert ferr<1e-6
    o={'predictor_member_permutation_max_abs':err,'fixed_physics_anchor_error':ferr,'pass':True}; (OUT/'selftest.json').write_text(json.dumps(o,indent=2)); print('V3SELFTEST',o,flush=True)

if __name__=='__main__':
    d=v1.Data(); c=write_pretest_contract(d); print('V3PRETEST',c['fresh_source_list_sha256'],c['code_sha256'],flush=True)
    ms=get_models(d); selftest(d,ms)
    s=evaluate(d,ms,'median')
    if s['verdict']=='PASS': evaluate(d,ms,'stress')
