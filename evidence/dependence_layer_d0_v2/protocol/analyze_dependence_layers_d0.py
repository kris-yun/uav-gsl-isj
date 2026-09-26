#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd

N_SURR=500
SEED=2026092603

def rank_average(v):
    return pd.Series(np.asarray(v,float)).rank(method="average",ascending=True).to_numpy(float)

def es_u(ref,y):
    ref=np.asarray(ref,float); y=np.asarray(y,float); K=len(ref)
    a=np.linalg.norm(ref-y[None,:],axis=1).mean()
    d=np.linalg.norm(ref[:,None,:]-ref[None,:,:],axis=2)
    b=d.sum()/(K*(K-1))
    return float(a-0.5*b)

def es_v(ref,y):
    ref=np.asarray(ref,float); y=np.asarray(y,float); K=len(ref)
    a=np.linalg.norm(ref-y[None,:],axis=1).mean()
    d=np.linalg.norm(ref[:,None,:]-ref[None,:,:],axis=2)
    return float(a-0.5*d.mean())

def locate(root,sid,rep,seed):
    ps=[
      root/sid/f"rep_{rep:02d}_seed_{seed}"/"pooled.npy",
      root/"compact_data"/sid/f"rep_{rep:02d}_seed_{seed}"/"pooled.npy",
    ]
    for p in ps:
        if p.is_file(): return p
    raise FileNotFoundError(f"missing pooled array: sid={sid}, rep={rep}, seed={seed}")

def metrics(scores,true_idx):
    ranks=[]; ties=0
    for row,ti in zip(scores,true_idx):
        r=rank_average(row); ranks.append(float(r[ti]))
        m=np.min(row)
        ties += int(np.sum(np.isclose(row,m,rtol=0,atol=1e-14))>1)
    ranks=np.asarray(ranks,float)
    return {
      "n_targets":int(len(ranks)),
      "mean_true_rank":float(ranks.mean()),
      "median_true_rank":float(np.median(ranks)),
      "mrr":float(np.mean(1.0/ranks)),
      "unique_top1_fraction":float(np.mean(ranks==1.0)),
      "top3_fraction":float(np.mean(ranks<=3.0)),
      "score_tie_target_fraction":float(ties/len(ranks)),
      "true_ranks":ranks.tolist(),
    }

def preserve_marginals(B,rng):
    # B K,T,Q binary; independently permute replicate labels for every t,q.
    B=np.asarray(B,np.int8); K,T,Q=B.shape
    out=np.empty_like(B)
    for t in range(T):
        for q in range(Q):
            p=rng.permutation(K)
            out[:,t,q]=B[p,t,q]
    assert np.array_equal(out.sum(axis=0),B.sum(axis=0))
    assert np.isin(out,[0,1]).all()
    return out

def preserve_time_snapshots(B,rng):
    # At each t, permute whole Q-dimensional snapshots as a unit.
    B=np.asarray(B,np.int8); K,T,Q=B.shape
    out=np.empty_like(B)
    for t in range(T):
        p=rng.permutation(K)
        out[:,t,:]=B[p,t,:]
    assert np.array_equal(out.sum(axis=0),B.sum(axis=0))
    raw_counts=np.sort(B.sum(axis=2),axis=0)
    out_counts=np.sort(out.sum(axis=2),axis=0)
    assert np.array_equal(raw_counts,out_counts)
    assert np.isin(out,[0,1]).all()
    return out

def score_fold(B,source_ids,train,test,control=None,rng=None):
    # B S,R,T,Q
    S=len(source_ids); K=len(train)
    refs=[]; phat=[]
    for s in range(S):
        b=B[s,train,:,:]
        phat.append(b.mean(axis=0))
        if control=="C1":
            b=preserve_marginals(b,rng)
        elif control=="C2":
            b=preserve_time_snapshots(b,rng)
        elif control not in (None,"RAW"):
            raise ValueError(control)
        refs.append(b.sum(axis=2).astype(float))
    refs=np.asarray(refs)      # S,K,T
    phat=np.asarray(phat)      # S,T,Q

    ys=[]; ybin=[]; true=[]
    for s in range(S):
        for r in test:
            ybin.append(B[s,r,:,:].astype(float))
            ys.append(B[s,r,:,:].sum(axis=1).astype(float))
            true.append(s)
    ys=np.asarray(ys); ybin=np.asarray(ybin); true=np.asarray(true,int)

    eu=np.zeros((len(ys),S))
    ev=np.zeros_like(eu)
    mb=np.zeros_like(eu)
    cm=np.zeros_like(eu)
    mean_count=phat.sum(axis=2)  # S,T
    for n,(y,yb) in enumerate(zip(ys,ybin)):
        for s in range(S):
            eu[n,s]=es_u(refs[s],y)
            ev[n,s]=es_v(refs[s],y)
            mb[n,s]=np.mean((yb-phat[s])**2)
            cm[n,s]=np.linalg.norm(y-mean_count[s])
    return {
      "ES_U":metrics(eu,true),
      "ES_V_diagnostic":metrics(ev,true),
      "MARGINAL_BRIER":metrics(mb,true),
      "COUNT_MEAN":metrics(cm,true),
    }

def pooled(parts,key):
    ranks=[]
    mrrs=[]
    top1_n=0; top3_n=0; ties_n=0; n=0
    for p in parts:
        r=np.asarray(p[key]["true_ranks"],float)
        ranks.extend(r.tolist()); n += len(r)
        top1_n += int(np.sum(r==1.0)); top3_n += int(np.sum(r<=3.0))
        # tie metric cannot be reconstructed target-wise from aggregate; average weighted
        ties_n += p[key]["score_tie_target_fraction"]*len(r)
    ranks=np.asarray(ranks,float)
    return {
      "n_targets":int(n),
      "mean_true_rank":float(ranks.mean()),
      "median_true_rank":float(np.median(ranks)),
      "mrr":float(np.mean(1.0/ranks)),
      "unique_top1_fraction":float(top1_n/n),
      "top3_fraction":float(top3_n/n),
      "score_tie_target_fraction":float(ties_n/n),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--seed-matrix",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)

    sm=pd.read_csv(a.seed_matrix,sep="\t")
    req={"panel_index","source_id","replicate","rng_seed"}
    if not req.issubset(sm.columns): raise SystemExit("seed matrix schema mismatch")
    if len(sm)!=288 or sm.source_id.nunique()!=18: raise SystemExit("not 18x16")
    if not (sm.groupby("source_id").replicate.nunique()==16).all(): raise SystemExit("replicate uniqueness fail")
    if not all(set(g.replicate.astype(int))==set(range(1,17)) for _,g in sm.groupby("source_id")):
        raise SystemExit("replicates must be exactly 1..16/source")
    if sm.rng_seed.nunique()!=288: raise SystemExit("RNG seeds not unique")

    order=(sm[["panel_index","source_id"]].drop_duplicates().sort_values("panel_index"))
    source_ids=order.source_id.astype(str).tolist()
    sidx={s:i for i,s in enumerate(source_ids)}
    B=np.zeros((18,16,10,30),np.int8)
    inv=[]
    for _,r in sm.iterrows():
        sid=str(r.source_id); rep=int(r.replicate); seed=int(r.rng_seed)
        p=locate(a.data_root,sid,rep,seed)
        z=np.load(p,allow_pickle=False)
        if z.shape!=(10,30) or not np.isfinite(z).all() or np.any(z<0):
            raise SystemExit(f"bad pooled array {p}")
        B[sidx[sid],rep-1]=(z>0).astype(np.int8)
        inv.append({"source_id":sid,"replicate":rep,"rng_seed":seed,"path":str(p)})
    pd.DataFrame(inv).to_csv(a.out_dir/"input_inventory.csv",index=False)

    splits={
      "A_first8_to_last8":(np.arange(0,8),np.arange(8,16)),
      "B_last8_to_first8":(np.arange(8,16),np.arange(0,8)),
      "C_odd_to_even":(np.arange(0,16,2),np.arange(1,16,2)),
      "D_even_to_odd":(np.arange(1,16,2),np.arange(0,16,2)),
    }
    primary=["A_first8_to_last8","B_last8_to_first8"]
    robust=["C_odd_to_even","D_even_to_odd"]

    raw={}
    for name,(tr,te) in splits.items():
        raw[name]=score_fold(B,source_ids,tr,te,control="RAW")

    raw_pool={
      "primary":pooled([raw[n] for n in primary],"ES_U"),
      "robust":pooled([raw[n] for n in robust],"ES_U"),
      "primary_marginal_brier":pooled([raw[n] for n in primary],"MARGINAL_BRIER"),
      "robust_marginal_brier":pooled([raw[n] for n in robust],"MARGINAL_BRIER"),
      "primary_count_mean":pooled([raw[n] for n in primary],"COUNT_MEAN"),
      "robust_count_mean":pooled([raw[n] for n in robust],"COUNT_MEAN"),
      "primary_ES_V_diagnostic":pooled([raw[n] for n in primary],"ES_V_diagnostic"),
      "robust_ES_V_diagnostic":pooled([raw[n] for n in robust],"ES_V_diagnostic"),
    }

    rng=np.random.default_rng(SEED)
    rows=[]
    # Independent surrogate randomizations for each split and source; target data never affect them.
    for b in range(N_SURR):
        row={"surrogate_id":b}
        all_ctrl={"C1":{},"C2":{}}
        for ctrl in ["C1","C2"]:
            for name,(tr,te) in splits.items():
                all_ctrl[ctrl][name]=score_fold(B,source_ids,tr,te,control=ctrl,rng=rng)
            for grp,names in [("primary",primary),("robust",robust)]:
                m=pooled([all_ctrl[ctrl][n] for n in names],"ES_U")
                for k,v in m.items():
                    row[f"{ctrl}_{grp}_{k}"]=v
            # directed mean ranks are needed for directionality gates
            for name in splits:
                row[f"{ctrl}_{name}_mean_true_rank"]=all_ctrl[ctrl][name]["ES_U"]["mean_true_rank"]
                row[f"{ctrl}_{name}_mrr"]=all_ctrl[ctrl][name]["ES_U"]["mrr"]
        rows.append(row)

    sur=pd.DataFrame(rows)
    sur.to_csv(a.out_dir/"within_source_surrogates_500.csv",index=False,float_format="%.17g")

    def frac_rank(ctrl,grp,raw_rank):
        return float(np.mean(sur[f"{ctrl}_{grp}_mean_true_rank"] <= raw_rank))
    def frac_top1(ctrl,grp,raw_top1):
        return float(np.mean(sur[f"{ctrl}_{grp}_unique_top1_fraction"] >= raw_top1))
    def med(ctrl,grp,field):
        return float(np.median(sur[f"{ctrl}_{grp}_{field}"]))

    fracs={}
    for ctrl in ["C1","C2"]:
        for grp in ["primary","robust"]:
            fracs[f"{ctrl}_{grp}_rank_as_good_or_better"]=frac_rank(ctrl,grp,raw_pool[grp]["mean_true_rank"])
            fracs[f"{ctrl}_{grp}_unique_top1_as_good_or_better"]=frac_top1(ctrl,grp,raw_pool[grp]["unique_top1_fraction"])

    # Directionality checks use surrogate median per directed split.
    A=raw["A_first8_to_last8"]["ES_U"]["mean_true_rank"]
    Bv=raw["B_last8_to_first8"]["ES_U"]["mean_true_rank"]
    medC2A=float(np.median(sur["C2_A_first8_to_last8_mean_true_rank"]))
    medC2B=float(np.median(sur["C2_B_last8_to_first8_mean_true_rank"]))
    medC1A=float(np.median(sur["C1_A_first8_to_last8_mean_true_rank"]))
    medC1B=float(np.median(sur["C1_B_last8_to_first8_mean_true_rank"]))

    cross_time=(
      A < medC2A and Bv < medC2B and
      fracs["C2_primary_rank_as_good_or_better"] <= 0.05 and
      raw_pool["primary"]["mean_true_rank"] < med("C1","primary","mean_true_rank") and
      raw_pool["robust"]["mean_true_rank"] < med("C2","robust","mean_true_rank") and
      fracs["C2_robust_rank_as_good_or_better"] <= 0.10 and
      raw_pool["primary"]["mrr"] >= med("C2","primary","mrr") and
      raw_pool["robust"]["mrr"] >= med("C2","robust","mrr")
    )

    instantaneous=(
      (not cross_time) and
      fracs["C1_primary_rank_as_good_or_better"] <= 0.05 and
      med("C2","primary","mean_true_rank") < med("C1","primary","mean_true_rank") and
      raw_pool["primary"]["mean_true_rank"] <= med("C2","primary","mean_true_rank")+0.25 and
      fracs["C1_robust_rank_as_good_or_better"] <= 0.10
    )

    # Mean-field only is the conservative default if complete-marginal destruction
    # does not separate from RAW.
    if cross_time:
        decision="DEPENDENCE_D0_CROSS_TIME_SIGNAL"
    elif instantaneous:
        decision="DEPENDENCE_D0_INSTANTANEOUS_JOINT_ONLY"
    elif fracs["C1_primary_rank_as_good_or_better"] > 0.05:
        decision="DEPENDENCE_D0_MEAN_FIELD_ONLY"
    else:
        decision="DEPENDENCE_D0_INCONSISTENT_HOLD"

    result={
      "contract":"DEPENDENCE_LAYER_D0_V2",
      "decision":decision,
      "source_count":18,
      "realizations_per_source":16,
      "representation":"binary pooled encounters B(t,q), plus 10D count trajectories for dependence score",
      "primary_score":"fair U-statistic Energy Score on 10D count trajectories",
      "diagnostic_score":"V-statistic empirical Energy Score",
      "full_mean_field_context":"300D marginal Brier loss",
      "surrogate_count":N_SURR,
      "surrogate_seed":SEED,
      "raw_directed":raw,
      "raw_pooled":raw_pool,
      "surrogate_fractions":fracs,
      "surrogate_medians":{
        f"{ctrl}_{grp}_{field}":med(ctrl,grp,field)
        for ctrl in ["C1","C2"] for grp in ["primary","robust"]
        for field in ["mean_true_rank","mrr","unique_top1_fraction"]
      },
      "directionality":{
        "RAW_A_mean_rank":A,"C2_A_median_mean_rank":medC2A,"C1_A_median_mean_rank":medC1A,
        "RAW_B_mean_rank":Bv,"C2_B_median_mean_rank":medC2B,"C1_B_median_mean_rank":medC1B,
      },
      "gates":{
        "cross_time":bool(cross_time),
        "instantaneous_joint_only":bool(instantaneous),
      },
      "interpretation_boundary":"OPEN development only; no network/world-model authorization."
    }
    (a.out_dir/"D0_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "decision":decision,
      "raw_pooled":raw_pool,
      "surrogate_fractions":fracs,
      "directionality":result["directionality"]
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
