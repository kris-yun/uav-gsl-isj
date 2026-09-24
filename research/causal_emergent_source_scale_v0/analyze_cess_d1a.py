#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import logsumexp
from scipy.sparse import csr_matrix

ALPHA=.5
LEVELS=(168,126,84,63,42,28,21,14,10,7,5,3,2)
BOOTSTRAPS=2000
BOOT_SEED=2026109001
RANDOM_PARTITIONS=250
RANDOM_SEED=2026109002
EPS=1e-300

def load_data(panel,data_root):
    out=[]
    for i,r in panel.iterrows():
        sid=r.source_id; arr=[]
        for rep in range(1,17):
            seed=2026105000+16*i+rep
            f=data_root/sid/f"rep_{rep:02d}_seed_{seed}"/"pooled.npy"
            if not f.exists(): raise FileNotFoundError(str(f))
            x=np.load(f,allow_pickle=False)
            if x.shape!=(10,30) or not np.isfinite(x).all() or (x<0).any():
                raise ValueError(f"invalid {f}")
            arr.append((x>0).astype(np.float64))
        out.append(np.stack(arr))
    return np.stack(out)

def train_micro(B,tr,te):
    N=B.shape[0]; R=len(te)
    k=B[:,tr].sum(axis=1)
    p=(k+ALPHA)/(len(tr)+2*ALPHA)
    Y=B[:,te].reshape(-1,300)
    lp=np.log(p.reshape(N,-1)); lq=np.log((1-p).reshape(N,-1))
    ll=Y@lp.T+(1-Y)@lq.T
    logpost=ll-logsumexp(ll,axis=1,keepdims=True)
    post=np.exp(logpost)
    true_s=np.repeat(np.arange(N),R)
    micro_true=logpost[np.arange(len(true_s)),true_s].reshape(N,R)
    micro_ei=float(np.log(N)+micro_true.mean())
    return p,post,true_s,micro_true,micro_ei

def macro_eval(post,true_s,micro_true,micro_ei,labels,rng):
    N,R=micro_true.shape
    groups=np.unique(labels); M=len(groups)
    sizes=np.array([np.sum(labels==g) for g in groups],dtype=int)
    data=1.0/sizes[labels]
    G=csr_matrix((data,(np.arange(N),labels)),shape=(N,M))
    score=np.asarray(G.T.dot(post.T).T)
    score/=score.sum(axis=1,keepdims=True)
    true_g=labels[true_s]
    macro_true=np.log(score[np.arange(len(score)),true_g]+EPS).reshape(N,R)
    w=1.0/(M*sizes[labels])
    if not np.isclose(w.sum(),1.0): raise RuntimeError("macro intervention weights do not sum to 1")
    macro_ei=float(np.log(M)+(macro_true.mean(axis=1)*w).sum())
    delta=macro_ei-micro_ei

    idx=rng.integers(0,R,size=(BOOTSTRAPS,N,R))
    src=np.arange(N)[None,:,None]
    mm=micro_true[src,idx].mean(axis=2)
    ma=macro_true[src,idx].mean(axis=2)
    micro_b=np.log(N)+mm.mean(axis=1)
    macro_b=np.log(M)+(ma*w[None,:]).sum(axis=1)
    db=macro_b-micro_b
    q=np.quantile(db,[.025,.5,.975])
    return {
        "M":M,"EI_lower_nats":macro_ei,"delta_EI_nats":delta,
        "eta_lower":float(macro_ei/np.log(M)),
        "sizes":sizes,
        "bootstrap_q025":float(q[0]),"bootstrap_q50":float(q[1]),"bootstrap_q975":float(q[2]),
    }

def macro_ei_only(post,true_s,labels):
    N=post.shape[1]; R=len(true_s)//N
    groups=np.unique(labels); M=len(groups)
    sizes=np.array([np.sum(labels==g) for g in groups],dtype=int)
    data=1.0/sizes[labels]
    G=csr_matrix((data,(np.arange(N),labels)),shape=(N,M))
    score=np.asarray(G.T.dot(post.T).T)
    score/=score.sum(axis=1,keepdims=True)
    tg=labels[true_s]
    lt=np.log(score[np.arange(len(score)),tg]+EPS).reshape(N,R)
    w=1.0/(M*sizes[labels])
    return float(np.log(M)+(lt.mean(axis=1)*w).sum())

def random_partition(rng,sizes,N):
    perm=rng.permutation(N); lab=np.empty(N,dtype=int); st=0
    for g,sz in enumerate(sizes):
        lab[perm[st:st+sz]]=g; st+=sz
    return lab

def connected(labels,panel):
    grid={(int(r.pmfs_i),int(r.pmfs_j)):i for i,r in panel.iterrows()}
    for g in np.unique(labels):
        cells=set(np.where(labels==g)[0]); seen={next(iter(cells))}; stack=list(seen)
        while stack:
            i=stack.pop(); r=panel.iloc[i]
            for q in ((r.pmfs_i+1,r.pmfs_j),(r.pmfs_i-1,r.pmfs_j),
                      (r.pmfs_i,r.pmfs_j+1),(r.pmfs_i,r.pmfs_j-1)):
                j=grid.get((int(q[0]),int(q[1])))
                if j in cells and j not in seen: seen.add(j); stack.append(j)
        if seen!=cells: return False
    return True

def physical_stats(labels,panel):
    vals=[]
    for g in np.unique(labels):
        idx=np.where(labels==g)[0]
        xy=panel.iloc[idx][["x_m","y_m"]].to_numpy(float)
        if len(xy)==1: diam=0.0
        else:
            d=xy[:,None,:]-xy[None,:,:]
            diam=float(np.sqrt((d*d).sum(axis=2)).max())
        vals.append((len(idx),len(idx)*.09,diam))
    a=np.asarray(vals,float)
    return {
      "cells_median":float(np.median(a[:,0])),"cells_q90":float(np.quantile(a[:,0],.9)),
      "area_m2_median":float(np.median(a[:,1])),
      "diameter_m_median":float(np.median(a[:,2])),"diameter_m_q90":float(np.quantile(a[:,2],.9)),
      "diameter_m_max":float(a[:,2].max())}

def micro_spatial_metrics(post,true_s,panel):
    xy=panel[["x_m","y_m"]].to_numpy(float)
    dist=np.sqrt(((xy[:,None,:]-xy[None,:,:])**2).sum(axis=2))
    order=np.argsort(-post,axis=1)
    ranks=np.empty(len(true_s),int)
    for k,s in enumerate(true_s): ranks[k]=int(np.where(order[k]==s)[0][0]+1)
    mapidx=order[:,0]; err=dist[true_s,mapidx]
    m05=np.array([post[k,dist[s]<=.5].sum() for k,s in enumerate(true_s)])
    m10=np.array([post[k,dist[s]<=1.0].sum() for k,s in enumerate(true_s)])
    return {"top1":float(np.mean(ranks==1)),"top3":float(np.mean(ranks<=3)),
            "map_error_median":float(np.median(err)),"map_error_q90":float(np.quantile(err,.9)),
            "mass_within_0p5m_mean":float(m05.mean()),"mass_within_1m_mean":float(m10.mean())}

def neighbor_diagnostic(B,panel):
    P=B.mean(axis=1).reshape(len(panel),-1)
    xy=panel[["x_m","y_m"]].to_numpy(float)
    near=[]; far=[]
    for i in range(len(panel)):
      for j in range(i+1,len(panel)):
        d=float(np.linalg.norm(xy[i]-xy[j])); den=np.linalg.norm(P[i])*np.linalg.norm(P[j])
        c=float(P[i]@P[j]/den) if den>0 else np.nan
        if abs(d-.3)<1e-6: near.append(c)
        if d>=3.0: far.append(c)
    return {"neighbor_0p3m_cosine_median":float(np.nanmedian(near)),
            "far_ge_3m_cosine_median":float(np.nanmedian(far)),
            "neighbor_pairs":len(near),"far_pairs":len(far)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--hierarchy-json",type=Path,required=True)
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    a=ap.parse_args()
    panel=pd.read_csv(a.panel,sep="\t")
    if len(panel)!=168: raise ValueError("expected 168-source D1A panel")
    H=json.loads(a.hierarchy_json.read_text())
    labels_by={int(k):np.asarray(v,int) for k,v in H["labels_by_M"].items()}
    if set(labels_by)!=set(LEVELS): raise ValueError("hierarchy levels mismatch")
    for M,lab in labels_by.items():
        if len(np.unique(lab))!=M or not connected(lab,panel): raise ValueError(f"bad hierarchy M={M}")
    B=load_data(panel,a.data_root)
    splits=[("A_train1_8_test9_16",list(range(8)),list(range(8,16))),
            ("B_train9_16_test1_8",list(range(8,16)),list(range(8)))]
    cache={}; rows=[]; microdiag={}
    for si,(name,tr,te) in enumerate(splits):
        p,post,true_s,mtrue,mei=train_micro(B,tr,te)
        cache[name]=(post,true_s,mtrue,mei)
        microdiag[name]={"EI_lower_nats":mei,**micro_spatial_metrics(post,true_s,panel)}
        brng=np.random.default_rng(BOOT_SEED+si)
        for M in LEVELS:
            lab=labels_by[M]
            if M==168:
                row={"split":name,"M":168,"EI_lower_nats":mei,"delta_EI_nats":0.0,
                     "eta_lower":float(mei/np.log(168)),"bootstrap_q025":0.0,
                     "bootstrap_q50":0.0,"bootstrap_q975":0.0,"random_percentile":np.nan,
                     **physical_stats(lab,panel)}
            else:
                e=macro_eval(post,true_s,mtrue,mei,lab,brng)
                row={"split":name,**{k:v for k,v in e.items() if k!="sizes"},
                     "random_percentile":np.nan,**physical_stats(lab,panel)}
            rows.append(row)
    df=pd.DataFrame(rows)

    for M in LEVELS[1:]:
        lab=labels_by[M]
        sizes=np.array([np.sum(lab==g) for g in np.unique(lab)],int)
        rrng=np.random.default_rng(RANDOM_SEED+M)
        arrays={name:[] for name,_,_ in splits}
        for _ in range(RANDOM_PARTITIONS):
            rl=random_partition(rrng,sizes,168)
            for name,_,_ in splits:
                post,true_s,_,_=cache[name]
                arrays[name].append(macro_ei_only(post,true_s,rl))
        for name,_,_ in splits:
            arr=np.asarray(arrays[name]); spatial=float(df[(df.split==name)&(df.M==M)].EI_lower_nats.iloc[0])
            pct=float((np.sum(arr<spatial)+.5*np.sum(arr==spatial))/len(arr))
            mask=(df.split==name)&(df.M==M)
            df.loc[mask,"random_percentile"]=pct
            df.loc[mask,"random_EI_mean"]=float(arr.mean())
            df.loc[mask,"random_EI_q95"]=float(np.quantile(arr,.95))

    good={}
    for M in LEVELS[1:]:
        z=df[df.M==M]
        good[M]=bool(len(z)==2 and (z.delta_EI_nats>0).all() and
                     (z.bootstrap_q025>0).all() and (z.random_percentile>.95).all())
    bands=[]; cur=[]
    for M in LEVELS[1:]:
        if good[M]: cur.append(M)
        else:
            if len(cur)>=2: bands.append(cur)
            cur=[]
    if len(cur)>=2: bands.append(cur)
    peak={}
    for name,_,_ in splits:
        z=df[df.split==name]
        peak[name]=int(z.loc[z.EI_lower_nats.idxmax(),"M"])
    pos={M:i for i,M in enumerate(LEVELS)}
    peak_adj=abs(pos[peak[splits[0][0]]]-pos[peak[splits[1][0]]])<=1
    peak_band=any(peak[splits[0][0]] in b and peak[splits[1][0]] in b for b in bands)
    peak_ok=bool(peak_adj or peak_band)
    decision="CESS_D1A_PASS_EMERGENT_SOURCE_SCALE" if (bands and peak_ok) else "CESS_D1A_FAIL_STOP_CAUSAL_EMERGENT_SCALE_MAINLINE"
    rc=0 if decision.startswith("CESS_D1A_PASS") else 20

    a.out_dir.mkdir(parents=True,exist_ok=True)
    df.to_csv(a.out_dir/"CESS_D1A_LEVELS.tsv",sep="\t",index=False)
    result={"decision":decision,"sources":168,"fresh_realizations_per_source":16,
            "total_new_realizations":2688,"supported_scale_bands":bands,
            "peak_M_by_split":peak,"peak_reproducible":peak_ok,
            "micro_diagnostics":microdiag,"encounter_redundancy_diagnostic":neighbor_diagnostic(B,panel),
            "metric":"corrected intervention-weighted held-out raw EI lower bound",
            "bootstrap":"2000 source-stratified realization bootstraps",
            "random_controls_per_M":250,"scope":"House02/W2 dense-region D1A only"}
    (a.out_dir/"CESS_D1A_RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    raise SystemExit(rc)
if __name__=="__main__": main()
