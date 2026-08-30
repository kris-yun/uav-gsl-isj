#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, math, struct, time
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ROOT=Path('/mnt/data/h01_offline_assets/extracted/H01_SOURCE_INFORMATION_AUDIT_FINAL_20260829')
PRED=ROOT/'remote_full8/PF_DEI_H01_SOURCE_INFORMATION_AUDIT_20260829/predictive8'
SUPPORT=ROOT/'artifacts_pf_dei_v3/source_region_3d_support_manifest.csv'
SCHED=ROOT/'artifacts_pf_dei_v3/maponly_trajectories/maponly/H01/reserved'
A0=Path('/mnt/data/h01_offline_assets/a0gate/PF_DEI_H01_SOURCE_UPDATE_A0_GATE_20260829/h01_source_update_a0_replay.json')
OUT=Path('/mnt/data/h01_temporal_gate'); THR=0.1; MAGIC=b'PFV3STR1'; PRIM=8; INPUT=11

def read_multistream(path):
    raw=Path(path).read_bytes(); off=8
    assert raw[:8]==MAGIC
    count=struct.unpack_from('<I',raw,off)[0]; off+=4
    lengths=struct.unpack_from(f'<{count}I',raw,off); off+=4*count
    flat=np.frombuffer(raw,dtype='<f4',offset=off); arr=[]; start=0
    for n in lengths: arr.append(flat[start:start+n].astype(np.float64,copy=True)); start+=n
    return arr

def forward_sensor_batch(x,dt=0.2):
    x=np.asarray(x,dtype=np.float64); delay=2; alpha=math.exp(-dt/1.2)
    state=np.zeros(x.shape[:-1],dtype=np.float64); out=np.empty_like(x)
    for t in range(x.shape[-1]):
        inp=x[...,t-delay] if t>=delay else 0.0
        state=alpha*state+(1-alpha)*inp; out[...,t]=state
    return out

def carrier_rows():
    groups={}
    with SUPPORT.open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['house']=='H01': groups.setdefault(r['carrier_id'],[]).append(r)
    rows=[]
    for cid,rr in groups.items():
        first=rr[0]; rows.append((int(first['carrier_index']),cid,len(rr)/626.0,
            np.mean([float(r['pmfs_x']) for r in rr]),np.mean([float(r['pmfs_y']) for r in rr])))
    rows.sort(); assert [x[0] for x in rows]==list(range(210)); return rows

def schedule_blocks(seed):
    with (SCHED/f'trajectory_seed_{seed}.csv').open(newline='') as f: rr=list(csv.DictReader(f))
    t=np.array([float(r['t_sim_s']) for r in rr]); moving=np.array([int(r['is_moving']) for r in rr])
    blocks=[]; i=0; stop=0
    while i<len(rr):
        if moving[i]==0:
            j=i
            while j<len(rr) and moving[j]==0:j+=1
            stop+=1
            for s in range(i,j-9,10): blocks.append((s,s+10,stop,float(t[s+9])))
            i=j
        else:i+=1
    return t,blocks

def load_update_times():
    j=json.loads(A0.read_text()); by={u:[] for u in range(1,6)}
    for r in j['cases']:
        if r['mode']=='pfdei_full': by[int(r['source_update_id'])].append(float(r['source_update_sim_time_s']))
    for u in by: by[u]=sorted(by[u])
    return by,{u:float(np.median(v)) for u,v in by.items()}

def coverage_indices(rows,count=32):
    xy=np.array([[r[3],r[4]] for r in rows]); z=(xy-xy.min(0))/np.maximum(np.ptp(xy,axis=0),1e-12)
    tie=[hashlib.sha256(f'PFDEI-V3-RESERVED|H01|{r[1]}'.encode()).digest() for r in rows]
    sel=[min(range(len(rows)),key=lambda i:tie[i])]; rem=set(range(len(rows)))-set(sel)
    while len(sel)<count:
        def key(i):return (-min(float(np.sum((z[i]-z[j])**2)) for j in sel),tie[i])
        q=min(rem,key=key);sel.append(q);rem.remove(q)
    return sel

def build_cache():
    rows=carrier_rows(); cids=[r[1] for r in rows]; blocks={tr:schedule_blocks(4001+tr)[1] for tr in range(5)}
    nb=max(map(len,blocks.values())); bm=np.full((5,210,8,nb),np.nan,np.float32); bc=np.zeros(5,np.int32); t0=time.time()
    for ci,cid in enumerate(cids):
        streams=[read_multistream(PRED/f'member_{m:02d}/{cid}.bin') for m in range(8)]
        for tr in range(5):
            y=forward_sensor_batch(np.stack([streams[m][tr] for m in range(8)]));bc[tr]=len(blocks[tr])
            for bi,(s,e,_,_) in enumerate(blocks[tr]):bm[tr,ci,:,bi]=y[:,s:e].mean(1).astype(np.float32)
        if (ci+1)%50==0:print(f'CACHE {ci+1}/210 wall={time.time()-t0:.1f}',flush=True)
    np.savez_compressed(OUT/'block_cache.npz',block_means=bm,block_counts=bc)
    meta={'carrier_ids':cids,'prior':[r[2] for r in rows],'xy':[[r[3],r[4]] for r in rows],
          'block_ends':{str(k):[b[3] for b in v] for k,v in blocks.items()}}
    (OUT/'block_cache_meta.json').write_text(json.dumps(meta)); return bm,bc,meta

def load_cache():
    if not (OUT/'block_cache.npz').exists():return build_cache()
    z=np.load(OUT/'block_cache.npz');return z['block_means'],z['block_counts'],json.loads((OUT/'block_cache_meta.json').read_text())

def primitives(obs,pred4):
    o=np.log1p(np.maximum(obs,0)/THR);pl=np.log1p(np.maximum(pred4,0)/THR);pm=pl.mean(0);ps=pl.std(0);res=o-pm
    oh=(obs>THR).astype(np.float32);ph=(pred4>THR).mean(0).astype(np.float32)
    return np.stack([o,pm,ps,res,np.abs(res),oh,ph,oh-ph],1).astype(np.float32)

def sequence_features(prim,order=None):
    q=prim if order is None else prim[np.asarray(order,dtype=np.int64)]
    return np.column_stack([q,np.r_[0,np.diff(q[:,3])],np.r_[0,np.diff(q[:,0])],np.r_[0,np.diff(q[:,1])]]).astype(np.float32)

class CausalBlock(nn.Module):
    def __init__(self,w,d):super().__init__();self.pad=2*d;self.conv=nn.Conv1d(w,w,3,dilation=d);self.norm=nn.LayerNorm(w)
    def forward(self,x):return x+F.gelu(self.norm(self.conv(F.pad(x.transpose(1,2),(self.pad,0))).transpose(1,2)))
class TemporalNRE(nn.Module):
    def __init__(self,w=32):
        super().__init__();self.enc=nn.Sequential(nn.Linear(INPUT,w),nn.GELU());self.blocks=nn.ModuleList([CausalBlock(w,d) for d in (1,2,4,8,16,32)]);self.head=nn.Sequential(nn.Linear(2*w,32),nn.GELU(),nn.Linear(32,1))
    def forward(self,x,mask):
        h=self.enc(x)
        for b in self.blocks:h=b(h)
        ww=mask[...,None].to(h.dtype);L=mask.sum(1);mean=(h*ww).sum(1)/L[:,None];final=h[torch.arange(len(h)),L-1]
        return self.head(torch.cat([mean,final],1)).squeeze(1)

def pad_batch(seq):
    L=max(map(len,seq));x=np.zeros((len(seq),L,INPUT),np.float32);m=np.zeros((len(seq),L),bool)
    for i,a in enumerate(seq):x[i,:len(a)]=a;m[i,:len(a)]=1
    return torch.from_numpy(x),torch.from_numpy(m)

class Data:
    def __init__(self):
        self.bm,self.bc,self.meta=load_cache();self.cids=self.meta['carrier_ids'];self.prior=np.array(self.meta['prior']);self.xy=np.array(self.meta['xy']);self.bytime,self.med=load_update_times();self.ends={int(k):np.array(v) for k,v in self.meta['block_ends'].items()}
    def nblocks(self,tr,cut):return int(np.searchsorted(self.ends[tr],cut+1e-12,'right'))
    def prim(self,tr,true,om,cand,cut):
        n=self.nblocks(tr,cut);return primitives(self.bm[tr,true,om,:n],self.bm[tr,cand,0:4,:n])
    def feat(self,tr,true,om,cand,cut,order=None):return sequence_features(self.prim(tr,true,om,cand,cut),order)

def deterministic_perm(n,key):return np.random.default_rng(int.from_bytes(hashlib.sha256(key.encode()).digest()[:8],'big')).permutation(n)

def make_pairs(data,rng,batch,split,seedkey):
    a=[];b=[];ap=[];bp=[]
    for k in range(batch):
        tr=int(rng.integers(0,3)) if split=='train' else 3;om=int(rng.integers(4,6)) if split=='train' else 6
        true=int(rng.integers(210));neg=int(rng.integers(209));neg+=int(neg>=true);u=int(rng.integers(1,6));cut=float(data.bytime[u][int(rng.integers(10))]) if split=='train' else data.med[u]
        pa=data.prim(tr,true,om,true,cut);pb=data.prim(tr,true,om,neg,cut);perm=deterministic_perm(len(pa),f'{seedkey}|{split}|{tr}|{om}|{true}|{neg}|{u}|{k}')
        a.append(sequence_features(pa));b.append(sequence_features(pb));ap.append(sequence_features(pa,perm));bp.append(sequence_features(pb,perm))
    return a,b,ap,bp

def loss_fn(model,batch):
    a,b,ap,bp=batch; n=len(a)
    x,m=pad_batch(a+b+ap+bp); logits=model(x,m); la,lb,lap,lbp=torch.split(logits,n)
    bce=.5*(F.binary_cross_entropy_with_logits(la,torch.ones_like(la))+F.binary_cross_entropy_with_logits(lb,torch.zeros_like(lb)))
    order=F.softplus(-((la-lb)-(lap-lbp))).mean();return bce+order,bce,order

def train_one(data,seed,steps=300):
    torch.set_num_threads(4);torch.manual_seed(seed);model=TemporalNRE();opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-4);rng=np.random.default_rng(seed);vrng=np.random.default_rng(99000+seed);val=make_pairs(data,vrng,96,'val',seed);best=None;hist=[]
    for step in range(1,steps+1):
        model.train();lo,bc,od=loss_fn(model,make_pairs(data,rng,24,'train',seed+17*step));opt.zero_grad();lo.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
        if step==1 or step%50==0:
            model.eval()
            with torch.no_grad():vl,vb,vo=loss_fn(model,val)
            row={'step':step,'train_total':float(lo.detach()),'val_total':float(vl),'val_bce':float(vb),'val_order':float(vo)};hist.append(row);print('TRAIN',seed,row,flush=True)
            if best is None or float(vl)<best[0]:
                best=(float(vl),step,{k:v.detach().cpu().clone() for k,v in model.state_dict().items()})
                torch.save({'seed':seed,'best_step':best[1],'state_dict':best[2],'contract':'CTT_CAUSAL_TEMPORAL_FORWARD_RESIDUAL_NRE_V1'},OUT/f'model_{seed}.pt')
                (OUT/f'train_{seed}.json').write_text(json.dumps({'seed':seed,'best_step':best[1],'best_val':best[0],'history':hist},indent=2))
    model.load_state_dict(best[2]);return model

def get_models(data):
    out=[]
    for seed in (1701,1702,1703):
        p=OUT/f'model_{seed}.pt'
        if p.exists():ck=torch.load(p,map_location='cpu',weights_only=False);m=TemporalNRE();m.load_state_dict(ck['state_dict']);m.eval();out.append(m)
        else:out.append(train_one(data,seed))
    return out

def score_all(models,data,true,tr,om,cut,permute=False):
    n=data.nblocks(tr,cut);order=deterministic_perm(n,f'TEST|{tr}|{cut:.9f}|{n}') if permute else None;seq=[data.feat(tr,true,om,c,cut,order) for c in range(210)];x,m=pad_batch(seq)
    with torch.no_grad():return np.mean(np.stack([q(x,m).numpy() for q in models]),0)

def energy(data,true,tr,om,cut):
    n=data.nblocks(tr,cut);obs=data.bm[tr,true,om,:n].astype(float);pred=data.bm[tr,:,0:4,:n].astype(float);first=np.linalg.norm(pred-obs[None,None,:],axis=2).mean(1);pair=np.zeros(210)
    for i in range(4):
        for j in range(4):pair+=np.linalg.norm(pred[:,i]-pred[:,j],axis=1)
    return (first-.5*pair/16)/math.sqrt(n)
def rank_desc(x,i):return 1+int(np.sum(x>x[i]+1e-12*(1+abs(float(x[i])))))
def rank_asc(x,i):return 1+int(np.sum(x<x[i]-1e-12*(1+abs(float(x[i])))))

def selftest(data,models):
    n=data.nblocks(4,data.med[3]);obs=data.bm[4,0,7,:n];pred=data.bm[4,0,0:4,:n];e=float(np.max(np.abs(primitives(obs,pred)-primitives(obs,pred[[2,0,3,1]]))));f=sequence_features(primitives(obs,pred));x,m=pad_batch([f]);base=[]
    with torch.no_grad():base=[float(q(x,m)) for q in models]
    x2,m2=pad_batch([f.copy()]);
    with torch.no_grad():ext=[float(q(x2,m2)) for q in models]
    ce=max(abs(a-b) for a,b in zip(base,ext));o={'member_permutation_max_abs_feature_error':e,'deterministic_prefix_score_error':ce,'pass':e<=1e-7 and ce<=1e-7};(OUT/'selftest.json').write_text(json.dumps(o,indent=2));print('SELFTEST',o,flush=True);assert o['pass']

def evaluate(data,models):
    rows0=carrier_rows();coverage=coverage_indices(rows0,32);rows=[];tr=4;om=7
    for u in range(1,6):
        for ti,cut in enumerate(data.bytime[u]):
            for true in coverage:
                s=score_all(models,data,true,tr,om,cut,False);sp=score_all(models,data,true,tr,om,cut,True);en=energy(data,true,tr,om,cut);r=rank_desc(s,true);rp=rank_desc(sp,true);re=rank_asc(en,true);lp=np.log(np.maximum(data.prior,1e-300))+s;rpost=rank_desc(lp,true)
                rows.append([u,ti,cut,data.nblocks(tr,cut),true,r,rp,re,rpost])
            print(f'EVAL u={u} timing={ti+1}/10',flush=True)
    import pandas as pd
    df=pd.DataFrame(rows,columns=['update','timing_index','cut_time_s','blocks','true_index','network_rank','perm_rank','energy_rank','posterior_rank'])
    for pref in ('network','perm','energy','posterior'):
        df[pref+'_norm_rank']=(df[pref+'_rank']-1)/209;df[pref+'_top5']=(df[pref+'_rank']<=5).astype(int);df[pref+'_top10']=(df[pref+'_rank']<=10).astype(int)
    df.to_csv(OUT/'test_cases.csv',index=False)
    def agg(g):
        o={'cases':len(g)}
        for p in ('network','perm','energy','posterior'):
            o[p+'_top5']=float(g[p+'_top5'].mean());o[p+'_top10']=float(g[p+'_top10'].mean());o[p+'_median_rank']=float(g[p+'_rank'].median());o[p+'_mean_norm_rank']=float(g[p+'_norm_rank'].mean())
        return o
    overall=agg(df);by={str(u):agg(g) for u,g in df.groupby('update')};wins=int((df.network_rank<df.perm_rank).sum());loss=int((df.network_rank>df.perm_rank).sum());ties=len(df)-wins-loss;n=wins+loss
    from math import comb
    p=min(1.0,2*sum(comb(n,i) for i in range(min(wins,loss)+1))/(2**n)) if n else 1
    summary={'contract':'CTT_CAUSAL_TEMPORAL_FORWARD_RESIDUAL_NRE_H01_GATE_V1','test':'trajectory4005_member7','coverage_sources':32,'timings_per_update':10,'overall':overall,'by_update':by,'time_permute':{'wins':wins,'losses':loss,'ties':ties,'sign_p':p},'posterior':'geometry_prior * exp(mean_three_seed_NRE_logit), rebuilt from fixed prior each cumulative prefix','no_post_outcome_tuning':True};(OUT/'test_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    d=Data();ms=get_models(d);selftest(d,ms);evaluate(d,ms)
