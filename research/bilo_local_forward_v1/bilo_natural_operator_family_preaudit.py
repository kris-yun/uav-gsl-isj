import os, glob, json, math
import numpy as np
import pandas as pd

BASE = os.environ.get("R2_NATIVE_BASE", "/mnt/data/r2_partial_id/extracted/tnqc_r2_six_offline_20260921_authoritative/native")
NULL_REPS = 500
SEED = 20260923

def truth_rank_desc(scores, ti, atol=1e-12):
    s=np.asarray(scores,float); v=s[ti]
    gt=np.sum(s>v+atol); eq=np.sum(np.abs(s-v)<=atol)
    return float(gt+(eq+1)/2.0)

def logmeanexp_rows(A):
    m=A.max(axis=1)
    return m+np.log(np.exp(A-m[:,None]).mean(axis=1))

def native_scores_matrix(P,C,Q):
    return np.log(np.clip(1.0-C[None,:]*np.abs(P[None,:]-Q),1e-300,None)).sum(axis=1)

def owner_ids(man, ixs, iys):
    oi=man.origin_i.to_numpy(int); oj=man.origin_j.to_numpy(int)
    si=man.size_i.to_numpy(int); sj=man.size_j.to_numpy(int)
    area=si*sj; ids=man.candidate_id.astype(str).to_numpy()
    out=[]
    for ix,iy in zip(ixs,iys):
        mask=(oi<=ix)&(ix<oi+si)&(oj<=iy)&(iy<oj+sj)
        inds=np.flatnonzero(mask)
        if not len(inds): raise RuntimeError(f"no owner for {ix},{iy}")
        out.append(ids[inds[np.argmin(area[inds])]])
    return out

def pivot_q(path, common):
    a=pd.read_csv(os.path.join(path,"candidate_support_alignment.csv"),
                  usecols=["candidate_id","cell_index","simulated_hit_probability"])
    a=a[a.cell_index.isin(common)]
    p=a.pivot(index="candidate_id",columns="cell_index",values="simulated_hit_probability").reindex(columns=common)
    if p.isna().any().any(): raise RuntimeError("missing common support")
    return p

def process(run):
    rng=np.random.default_rng(SEED+sum(map(ord,os.path.basename(run))))
    ev=json.load(open(os.path.join(run,"tnqc_fixed_trajectory_evaluation.json")))
    truth=np.asarray(ev["truth"],float)
    uds=[u for u in sorted(glob.glob(run+"/context_bank/source_update_[0-9][0-9][0-9][0-9]")) if os.path.isdir(u)]
    ms=[]; ss=[]
    for u in uds:
        m=pd.read_csv(os.path.join(u,"measured_hit_probability.csv"),
                      usecols=["cell_index","probability","confidence"])
        m=m[m.confidence>0].copy(); ms.append(m); ss.append(set(m.cell_index.astype(int)))
    common=sorted(set.intersection(*ss))
    mf=ms[-1].set_index("cell_index").loc[common]
    P=mf.probability.to_numpy(float); C=mf.confidence.to_numpy(float)

    mans=[pd.read_csv(os.path.join(u,"candidate_manifest.csv")) for u in uds]
    pivs=[pivot_q(u,common) for u in uds]
    leaf_ids=ev.get("tnqc_gate_scope_audit",{}).get("final_leaf_candidate_ids") or list(ev["final_leaf_hypothesis_measure_cells"])
    finals=mans[-1][mans[-1].candidate_id.astype(str).isin(set(map(str,leaf_ids)))].copy().reset_index(drop=True)
    finals["truth_dist"]=np.hypot(finals.native_source_x-truth[0], finals.native_source_y-truth[1])
    ti=int(finals.truth_dist.to_numpy().argmin())

    meta=ev["endpoint_evaluator"]["grid_metadata"]
    ox=float(meta["origin_x"]); oy=float(meta["origin_y"]); cs=float(meta["cell_size"])
    ixs=np.floor((finals.native_source_x.to_numpy(float)-ox)/cs).astype(int)
    iys=np.floor((finals.native_source_y.to_numpy(float)-oy)/cs).astype(int)

    L=np.empty((len(finals),5),float)
    for ui,(man,piv) in enumerate(zip(mans,pivs)):
        ids=owner_ids(man,ixs,iys)
        L[:,ui]=native_scores_matrix(P,C,piv.loc[ids].to_numpy(float))

    curr=L[:,4]; marginal=logmeanexp_rows(L); profile=L.max(axis=1)
    col_evidence=[]
    for ui in range(5):
        a=L[:,ui]; mm=a.max()
        col_evidence.append(float(mm+np.log(np.exp(a-mm).mean())))
    shared_ui=int(np.argmax(col_evidence)); shared=L[:,shared_ui]

    rcur=truth_rank_desc(curr,ti); rsh=truth_rank_desc(shared,ti)
    rma=truth_rank_desc(marginal,ti); rpr=truth_rank_desc(profile,ti)
    rfull=truth_rank_desc(finals.native_score.to_numpy(float),ti)

    null=[]
    for _ in range(NULL_REPS):
        N=L.copy()
        for ui in range(4):
            N[:,ui]=L[rng.permutation(len(L)),ui]
        null.append(truth_rank_desc(logmeanexp_rows(N),ti))
    null=np.asarray(null,float)
    frac=float(np.mean(null<=rma+1e-12))
    rho=float(pd.Series(marginal).rank().corr(pd.Series(-finals.truth_dist.to_numpy(float)).rank()))

    return dict(
        run=os.path.basename(run), house=os.path.basename(run).split("_")[0],
        n=len(finals), common_support=len(common),
        truth_candidate=str(finals.iloc[ti].candidate_id), truth_dist=float(finals.iloc[ti].truth_dist),
        native_full_truth_rank=rfull, current_common_truth_rank=rcur,
        shared_operator_index=shared_ui+1, shared_truth_rank=rsh,
        marginal_truth_rank=rma, profile_truth_rank=rpr,
        marginal_score_std=float(np.std(marginal)),
        marginal_spearman_vs_neg_truth_distance=rho,
        null_fraction_as_good_or_better=frac, null_rank_median=float(np.median(null)),
        null_q05=float(np.quantile(null,.05)), null_q95=float(np.quantile(null,.95)),
        marginal_beats_current=bool(rma<rcur), marginal_beats_shared=bool(rma<rsh),
        null_pass=bool(frac<=.05)
    )

rows=[process(r) for r in sorted(glob.glob(BASE+"/House*_seed*_off_off"))]
out=pd.DataFrame(rows)
out.to_csv("BILO_NATURAL_OPERATOR_FAMILY_PREAUDIT_R2.csv",index=False)
print(out.to_string(index=False))
