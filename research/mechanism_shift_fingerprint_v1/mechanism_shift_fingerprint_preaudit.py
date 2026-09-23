import os, glob, json, math, itertools
import numpy as np
import pandas as pd

BASE=os.environ.get("R2_NATIVE_BASE","/mnt/data/r2_partial_id/extracted/tnqc_r2_six_offline_20260921_authoritative/native")

def rank_desc(s,ti,atol=1e-12):
    s=np.asarray(s,float); v=s[ti]
    return float(np.sum(s>v+atol)+(np.sum(np.abs(s-v)<=atol)+1)/2)

def owner_ids(man,ixs,iys):
    oi=man.origin_i.to_numpy(int); oj=man.origin_j.to_numpy(int)
    si=man.size_i.to_numpy(int); sj=man.size_j.to_numpy(int)
    area=si*sj; ids=man.candidate_id.astype(str).to_numpy(); out=[]
    for ix,iy in zip(ixs,iys):
        ii=np.flatnonzero((oi<=ix)&(ix<oi+si)&(oj<=iy)&(iy<oj+sj))
        out.append(ids[ii[np.argmin(area[ii])]])
    return out

def pivot(path,cells):
    a=pd.read_csv(path+"/candidate_support_alignment.csv",
                  usecols=["candidate_id","cell_index","simulated_hit_probability"])
    a=a[a.cell_index.isin(cells)]
    p=a.pivot(index="candidate_id",columns="cell_index",values="simulated_hit_probability").reindex(columns=cells)
    if p.isna().any().any(): raise RuntimeError("missing support")
    return p

def weighted_cosine_rows(Q,A,w):
    q=(Q*np.sqrt(w)[None,None,:]).reshape(Q.shape[0],-1)
    a=(A*np.sqrt(w)[None,:]).reshape(-1)
    return (q@a)/np.maximum(np.linalg.norm(q,axis=1)*np.linalg.norm(a),1e-300)

def process(run):
    ev=json.load(open(run+"/tnqc_fixed_trajectory_evaluation.json"))
    truth=np.asarray(ev["truth"],float)
    uds=[u for u in sorted(glob.glob(run+"/context_bank/source_update_[0-9][0-9][0-9][0-9]")) if os.path.isdir(u)]
    meas=[]; support=[]
    for u in uds:
        m=pd.read_csv(u+"/measured_hit_probability.csv",usecols=["cell_index","probability","confidence"])
        m=m[m.confidence>0]; meas.append(m); support.append(set(m.cell_index.astype(int)))
    cells=sorted(set.intersection(*support))
    P=[]; C=[]
    for m in meas:
        z=m.set_index("cell_index").loc[cells]
        P.append(z.probability.to_numpy(float)); C.append(z.confidence.to_numpy(float))
    P=np.stack(P); C=np.stack(C); w=C.mean(axis=0); w/=w.sum()

    mans=[pd.read_csv(u+"/candidate_manifest.csv") for u in uds]
    pivs=[pivot(u,cells) for u in uds]
    leaves=set(map(str,ev["tnqc_gate_scope_audit"]["final_leaf_candidate_ids"]))
    finals=mans[-1][mans[-1].candidate_id.astype(str).isin(leaves)].copy().reset_index(drop=True)
    finals["truth_dist"]=np.hypot(finals.native_source_x-truth[0],finals.native_source_y-truth[1])
    ti=int(finals.truth_dist.to_numpy().argmin())

    meta=ev["endpoint_evaluator"]["grid_metadata"]
    ox,oy,cs=float(meta["origin_x"]),float(meta["origin_y"]),float(meta["cell_size"])
    ixs=np.floor((finals.native_source_x.to_numpy(float)-ox)/cs).astype(int)
    iys=np.floor((finals.native_source_y.to_numpy(float)-oy)/cs).astype(int)

    Q=np.empty((len(finals),5,len(cells)))
    for u,(man,pv) in enumerate(zip(mans,pivs)):
        Q[:,u,:]=pv.loc[owner_ids(man,ixs,iys)].to_numpy(float)

    A=P-P.mean(axis=0,keepdims=True)
    B=Q-Q.mean(axis=1,keepdims=True)
    mech=weighted_cosine_rows(B,A,w)

    qm=Q.mean(axis=1)*np.sqrt(w)[None,:]
    pm=P.mean(axis=0)*np.sqrt(w)
    static=(qm@pm)/np.maximum(np.linalg.norm(qm,axis=1)*np.linalg.norm(pm),1e-300)

    curr=np.log(np.clip(1-C[-1][None,:]*np.abs(P[-1][None,:]-Q[:,-1,:]),1e-300,None)).sum(axis=1)
    rme,rst,rcu=rank_desc(mech,ti),rank_desc(static,ti),rank_desc(curr,ti)

    null=[]
    for pr in itertools.permutations(range(5)):
        null.append(rank_desc(weighted_cosine_rows(B[:,pr,:],A,w),ti))
    null=np.asarray(null,float)
    pval=float(np.mean(null<=rme+1e-12))
    rho=float(pd.Series(mech).rank().corr(pd.Series(-finals.truth_dist).rank()))

    return dict(run=os.path.basename(run),house=os.path.basename(run).split("_")[0],
        n=len(finals),common_support=len(cells),truth_candidate=str(finals.iloc[ti].candidate_id),
        truth_dist=float(finals.iloc[ti].truth_dist),current_common_truth_rank=rcu,
        static_mean_truth_rank=rst,mechanism_fingerprint_truth_rank=rme,
        mechanism_spearman_vs_neg_truth_distance=rho,mechanism_score_std=float(np.std(mech)),
        exact_permutation_p=pval,perm_rank_median=float(np.median(null)),
        perm_rank_q05=float(np.quantile(null,.05)),perm_rank_q95=float(np.quantile(null,.95)),
        beats_current=bool(rme<rcu),beats_static_mean=bool(rme<rst),perm_pass=bool(pval<=.05))

out=pd.DataFrame([process(r) for r in sorted(glob.glob(BASE+"/House*_seed*_off_off"))])
out.to_csv("MECHANISM_SHIFT_FINGERPRINT_PREAUDIT_R2.csv",index=False)
print(out.to_string(index=False))
