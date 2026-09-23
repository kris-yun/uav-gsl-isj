import os, glob, json, itertools
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

def seqscore(P,dC,Q):
    return np.log(np.clip(1-dC[None,:,:]*np.abs(P[None,:,:]-Q),1e-300,None)).sum(axis=(1,2))

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
    P=np.stack(P); C=np.stack(C)
    dC=np.vstack([C[0],np.diff(C,axis=0)])
    if (dC<-1e-12).any(): raise RuntimeError("confidence decreased")
    dC=np.maximum(dC,0)

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
    for ui,(man,pv) in enumerate(zip(mans,pivs)):
        Q[:,ui,:]=pv.loc[owner_ids(man,ixs,iys)].to_numpy(float)

    aligned=seqscore(P,dC,Q)
    fixed=seqscore(P,dC,np.repeat(Q[:,-1:,:],5,axis=1))
    full=finals.native_score.to_numpy(float)
    ra,rf,rn=rank_desc(aligned,ti),rank_desc(fixed,ti),rank_desc(full,ti)

    null=[]
    for pr in itertools.permutations(range(5)):
        null.append(rank_desc(seqscore(P,dC,Q[:,pr,:]),ti))
    null=np.asarray(null,float)
    pval=float(np.mean(null<=ra+1e-12))
    rho=float(pd.Series(aligned).rank().corr(pd.Series(-finals.truth_dist).rank()))

    return dict(run=os.path.basename(run),house=os.path.basename(run).split("_")[0],
        n=len(finals),common_support=len(cells),truth_candidate=str(finals.iloc[ti].candidate_id),
        truth_dist=float(finals.iloc[ti].truth_dist),native_full_truth_rank=rn,
        fixed_final_operator_sequential_truth_rank=rf,time_aligned_operator_truth_rank=ra,
        time_aligned_spearman_vs_neg_truth_distance=rho,time_aligned_score_std=float(np.std(aligned)),
        exact_operator_permutation_p=pval,perm_rank_median=float(np.median(null)),
        perm_rank_q05=float(np.quantile(null,.05)),perm_rank_q95=float(np.quantile(null,.95)),
        beats_fixed=bool(ra<rf),beats_native_full=bool(ra<rn),perm_pass=bool(pval<=.05))

out=pd.DataFrame([process(r) for r in sorted(glob.glob(BASE+"/House*_seed*_off_off"))])
out.to_csv("TEMPORAL_OPERATOR_ALIGNMENT_PREAUDIT_R2.csv",index=False)
print(out.to_string(index=False))
