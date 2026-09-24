#!/usr/bin/env python3
"""R0 stochastic benchmark stability analysis.

This script does NOT score source-localization methods. It asks whether the
stochastic plume statistics themselves are reproducible enough to support
future source-conditioned-distribution research.
"""
from __future__ import annotations
import argparse,json,math
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd

KS=(2,4,8,12,16)
EPS=1e-12

def pair_rel(a,b):
    return float(np.linalg.norm(a-b)/(np.linalg.norm((a+b)/2.0)+EPS))

def pair_cos(a,b):
    na=np.linalg.norm(a); nb=np.linalg.norm(b)
    return float(np.dot(a,b)/(na*nb+EPS))

def source_summary(arr):
    # arr [n,10,30]
    flat=arr.reshape(arr.shape[0],-1)
    rel=[]; cos=[]
    for i,j in combinations(range(len(flat)),2):
        rel.append(pair_rel(flat[i],flat[j]))
        cos.append(pair_cos(flat[i],flat[j]))
    mass_t=arr.sum(axis=2)
    total=arr.sum(axis=(1,2))
    zfrac=(arr<=0).mean(axis=(1,2))
    first=[]
    for mt in mass_t:
        nz=np.where(mt>0)[0]
        first.append(int(nz[0]) if len(nz) else 10)
    rel=np.asarray(rel,float); cos=np.asarray(cos,float)
    return {
        "n":int(arr.shape[0]),
        "median_pairwise_rel_l2":float(np.median(rel)),
        "q90_pairwise_rel_l2":float(np.quantile(rel,0.90)),
        "median_pairwise_cosine":float(np.median(cos)),
        "q10_pairwise_cosine":float(np.quantile(cos,0.10)),
        "median_total_mass":float(np.median(total)),
        "q10_total_mass":float(np.quantile(total,0.10)),
        "q90_total_mass":float(np.quantile(total,0.90)),
        "median_zero_fraction":float(np.median(zfrac)),
        "median_first_arrival_index":float(np.median(first)),
    }, rel, cos, total, zfrac, first

def spearman(a,b):
    a=pd.Series(a,dtype=float).rank(method="average")
    b=pd.Series(b,dtype=float).rank(method="average")
    return float(a.corr(b))

def tertiles(vals):
    r=pd.Series(vals,dtype=float).rank(method="first")
    return pd.qcut(r,3,labels=[0,1,2]).astype(int).to_numpy()

def summarize_split(panel, arrays, left_reps, right_reps, name):
    left=[]; right=[]
    for sid in panel.source_id:
        arr=arrays[sid]
        l,_r1,_c1,_t1,_z1,_f1=source_summary(arr[np.array(left_reps)-1])
        r,_r2,_c2,_t2,_z2,_f2=source_summary(arr[np.array(right_reps)-1])
        left.append(l); right.append(r)
    lv=[x["median_pairwise_rel_l2"] for x in left]
    rv=[x["median_pairwise_rel_l2"] for x in right]
    lm=[x["median_total_mass"] for x in left]
    rm=[x["median_total_mass"] for x in right]
    la=tertiles(lv); ra=tertiles(rv)
    return {
        "split":name,
        "variability_spearman":spearman(lv,rv),
        "mass_spearman":spearman(lm,rm),
        "variability_tertile_agreement":float(np.mean(la==ra)),
        "left_variability_median":float(np.median(lv)),
        "right_variability_median":float(np.median(rv)),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--seed-matrix",type=Path,required=True)
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    a=ap.parse_args()

    panel=pd.read_csv(a.panel,sep="\t")
    seeds=pd.read_csv(a.seed_matrix,sep="\t")
    assert len(panel)==18 and panel.source_id.nunique()==18
    assert len(seeds)==288 and seeds.rng_seed.nunique()==288
    assert set(seeds.source_id)==set(panel.source_id)

    arrays={}
    realization_rows=[]
    complete=True
    for _,p in panel.sort_values("panel_index").iterrows():
        sid=p.source_id
        ss=seeds[seeds.source_id==sid].sort_values("replicate")
        if list(ss.replicate)!=list(range(1,17)):
            raise RuntimeError(f"replicates not 1..16 for {sid}")
        aa=[]
        for _,sr in ss.iterrows():
            f=a.data_root/sid/f"rep_{int(sr.replicate):02d}_seed_{int(sr.rng_seed)}"/"pooled.npy"
            if not f.exists():
                print("MISSING",f)
                complete=False
                continue
            x=np.load(f,allow_pickle=False)
            if x.shape!=(10,30) or not np.isfinite(x).all() or (x<0).any():
                raise RuntimeError(f"invalid pooled array: {f}")
            aa.append(x.astype(np.float64))
            mass_t=x.sum(axis=1)
            nz=np.where(mass_t>0)[0]
            realization_rows.append({
                "panel_index":int(p.panel_index),
                "source_id":sid,
                "replicate":int(sr.replicate),
                "rng_seed":int(sr.rng_seed),
                "total_mass":float(x.sum()),
                "zero_fraction":float((x<=0).mean()),
                "first_arrival_index":int(nz[0]) if len(nz) else 10,
                "path_l2_norm":float(np.linalg.norm(x)),
            })
        if len(aa)==16:
            arrays[sid]=np.stack(aa,axis=0)

    a.out_dir.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(realization_rows).to_csv(a.out_dir/"R0_REALIZATION_STATS.tsv",sep="\t",index=False)

    if not complete or len(arrays)!=18:
        result={
            "decision":"R0_INFRA_STOP_INCOMPLETE_18X16",
            "complete":False,
            "expected_sources":18,
            "expected_realizations":288,
            "found_sources":len(arrays),
            "found_realizations":len(realization_rows),
        }
        (a.out_dir/"R0_RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
        raise SystemExit(30)

    pair_rows=[]
    k_rows=[]
    source_rows=[]
    for _,p in panel.sort_values("panel_index").iterrows():
        sid=p.source_id
        arr=arrays[sid]
        full,rel,cos,total,zf,fa=source_summary(arr)
        # pairwise audit rows
        for i,j in combinations(range(16),2):
            pair_rows.append({
                "panel_index":int(p.panel_index),
                "source_id":sid,
                "replicate_i":i+1,
                "replicate_j":j+1,
                "pairwise_rel_l2":pair_rel(arr[i].reshape(-1),arr[j].reshape(-1)),
                "pairwise_cosine":pair_cos(arr[i].reshape(-1),arr[j].reshape(-1)),
            })
        # nested K convergence
        for k in KS:
            s,*_=source_summary(arr[:k])
            k_rows.append({
                "panel_index":int(p.panel_index),
                "source_id":sid,
                "K":k,
                **s,
            })
        source_rows.append({
            "panel_index":int(p.panel_index),
            "source_id":sid,
            "x_m":float(p.x_m),"y_m":float(p.y_m),"z_m":float(p.z_m),
            "legacy_cd_variability_stratum":p.legacy_cd_variability_stratum,
            "legacy_cd_mass_stratum":p.legacy_cd_mass_stratum,
            "legacy_cd_rel_l2":float(p.legacy_cd_rel_l2),
            **full,
        })

    pair_df=pd.DataFrame(pair_rows)
    kdf=pd.DataFrame(k_rows)
    sdf=pd.DataFrame(source_rows)

    # Stable R0 strata are defined only after all 16 calibration realizations.
    sdf["r0_variability_stratum"]=pd.qcut(
        sdf["median_pairwise_rel_l2"].rank(method="first"),
        3,labels=["low","mid","high"]
    ).astype(str)

    pair_df.to_csv(a.out_dir/"R0_PAIRWISE_STATS.tsv",sep="\t",index=False)
    kdf.to_csv(a.out_dir/"R0_K_CONVERGENCE.tsv",sep="\t",index=False)
    sdf.to_csv(a.out_dir/"R0_SOURCE_SUMMARY.tsv",sep="\t",index=False)

    splits=[
        summarize_split(panel,arrays,list(range(1,9)),list(range(9,17)),"first8_vs_last8"),
        summarize_split(panel,arrays,list(range(1,17,2)),list(range(2,17,2)),"odd8_vs_even8"),
    ]
    split_df=pd.DataFrame(splits)
    split_df.to_csv(a.out_dir/"R0_SPLIT_REPRO.tsv",sep="\t",index=False)

    def kchange(k):
        vals=[]
        for sid in panel.source_id:
            v16=float(kdf[(kdf.source_id==sid)&(kdf.K==16)].median_pairwise_rel_l2.iloc[0])
            vk=float(kdf[(kdf.source_id==sid)&(kdf.K==k)].median_pairwise_rel_l2.iloc[0])
            vals.append(abs(vk-v16)/(abs(v16)+EPS))
        return {
            "median":float(np.median(vals)),
            "q75":float(np.quantile(vals,0.75)),
            "max":float(np.max(vals)),
        }

    c8=kchange(8); c12=kchange(12)
    min_rho=float(split_df.variability_spearman.min())
    min_agree=float(split_df.variability_tertile_agreement.min())
    min_mass_rho=float(split_df.mass_spearman.min())
    legacy_rho=spearman(sdf.legacy_cd_rel_l2,sdf.median_pairwise_rel_l2)

    pass_pred={
        "complete_18x16":True,
        "both_split_variability_spearman_ge_0_70":min_rho>=0.70,
        "both_split_tertile_agreement_ge_0_50":min_agree>=0.50,
        "K8_to_K16_median_change_le_0_25":c8["median"]<=0.25,
        "K8_to_K16_q75_change_le_0_40":c8["q75"]<=0.40,
        "K12_to_K16_median_change_le_0_15":c12["median"]<=0.15,
        "K12_to_K16_q75_change_le_0_25":c12["q75"]<=0.25,
    }
    hold_pred={
        "complete_18x16":True,
        "both_split_variability_spearman_ge_0_40":min_rho>=0.40,
        "K12_to_K16_median_change_le_0_25":c12["median"]<=0.25,
        "K12_to_K16_q75_change_le_0_40":c12["q75"]<=0.40,
    }

    if all(pass_pred.values()):
        decision="R0_PASS_STOCHASTIC_BENCHMARK_USABLE"
        rc=0
    elif all(hold_pred.values()):
        decision="R0_HOLD_MORE_REALIZATIONS_REQUIRED"
        rc=10
    else:
        decision="R0_STOP_PER_SOURCE_DISTRIBUTION_MAINLINE_UNSTABLE"
        rc=20

    result={
        "decision":decision,
        "panel_sources":18,
        "new_realizations_per_source":16,
        "total_new_realizations":288,
        "legacy_cd_used_for_r0_estimation":False,
        "legacy_cd_vs_r0_variability_spearman":legacy_rho,
        "split_reproducibility":splits,
        "min_variability_split_spearman":min_rho,
        "min_mass_split_spearman_diagnostic":min_mass_rho,
        "min_variability_tertile_agreement":min_agree,
        "K8_to_K16_relative_change":c8,
        "K12_to_K16_relative_change":c12,
        "pass_predicates":pass_pred,
        "hold_predicates":hold_pred,
        "interpretation":{
            "PASS":"16-realization source stochastic summaries are reproducible enough to support a new source-conditioned stochastic benchmark.",
            "HOLD":"Statistics are partially stabilizing but 16 realizations are not yet enough; increase K before theory selection.",
            "STOP":"Per-source stochastic descriptors remain too unstable under the frozen observation operator; do not build the next mainline on per-source path distributions."
        }
    }
    (a.out_dir/"R0_RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    raise SystemExit(rc)

if __name__=="__main__":
    main()
