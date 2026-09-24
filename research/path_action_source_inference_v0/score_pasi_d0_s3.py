#!/usr/bin/env python3
"""Fresh S3 confirmation scorer for source-conditioned stochastic path action.

Scientific contract is frozen in:
01_idea/PATH_ACTION_SOURCE_INFERENCE_FREEZE_20260924.md
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd


def pooled_probe(cube, points):
    vals=[]
    for p in points:
        vals.append(cube[:, int(p["native_x0"]):int(p["native_x1_exclusive"]),
                         int(p["native_y0"]):int(p["native_y1_exclusive"])].mean(axis=(1,2)))
    return np.stack(vals,axis=1).astype(np.float64)


def rank(scores, truth_idx):
    order=np.argsort(scores,kind="stable")
    return int(np.where(order==truth_idx)[0][0]+1), order


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--source-bank",type=Path,required=True)
    ap.add_argument("--prediction-root",type=Path,required=True)
    ap.add_argument("--target-e",type=Path,required=True)
    ap.add_argument("--target-f",type=Path,required=True)
    ap.add_argument("--truth-source-id",default="pmfs_3_12")
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()

    c=json.loads(a.contract.read_text())
    bank=pd.read_csv(a.source_bank,sep="\t")
    ids=bank.source_id.tolist()
    ti=ids.index(a.truth_source_id)

    x=np.empty((len(ids),2,10,30),dtype=np.float64)
    for si,seed in enumerate(c["prediction_seeds"]):
        d=a.prediction_root/f"seed_{seed}"
        for i,src in enumerate(ids):
            x[i,si]=np.load(d/f"{src}.npy",allow_pickle=False).reshape(10,30)

    mu=x.mean(axis=1)
    vlocal=((x[:,0]-x[:,1])**2)/2.0
    vfloor=vlocal.mean(axis=0)
    v=vlocal+vfloor[None,:,:]+1e-12

    targets={
        "E": pooled_probe(np.load(a.target_e,allow_pickle=False),c["probe_points"]),
        "F": pooled_probe(np.load(a.target_f,allow_pickle=False),c["probe_points"]),
    }

    result={}
    for label,y in targets.items():
        resid=(mu-y[None,:,:])**2

        raw=resid.sum(axis=(1,2))
        hom=(resid/(vfloor[None,:,:]+1e-12)).sum(axis=(1,2))
        het=(resid/v).sum(axis=(1,2))
        action=(resid/v+np.log(v)).sum(axis=(1,2))

        rr,_=rank(raw,ti)
        hr,_=rank(hom,ti)
        er,_=rank(het,ti)
        ar,order=rank(action,ti)
        result[label]={
            "raw_rank":rr,
            "homoscedastic_rank":hr,
            "heteroscedastic_residual_only_rank":er,
            "path_action_rank":ar,
            "truth_path_action_score":float(action[ti]),
            "top10_path_action":[
                {
                    "source_id":ids[int(j)],
                    "score":float(action[int(j)]),
                }
                for j in order[:10]
            ]
        }

    action_sum=sum(result[k]["path_action_rank"] for k in ("E","F"))
    raw_sum=sum(result[k]["raw_rank"] for k in ("E","F"))
    hom_sum=sum(result[k]["homoscedastic_rank"] for k in ("E","F"))
    het_sum=sum(result[k]["heteroscedastic_residual_only_rank"] for k in ("E","F"))

    preds={
        "both_action_rank_le_3": all(result[k]["path_action_rank"]<=3 for k in ("E","F")),
        "action_sum_le_raw": action_sum<=raw_sum,
        "action_sum_le_homoscedastic": action_sum<=hom_sum,
        "logdet_load_bearing_or_both_rank1": (
            action_sum<het_sum or
            all(result[k]["path_action_rank"]==1 for k in ("E","F"))
        ),
    }
    passed=all(preds.values())

    out={
        "decision":"PASI_D0_PASS_FRESH_S3_PATH_ACTION_SIGNAL" if passed
                   else "PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE",
        "truth_source_id":a.truth_source_id,
        "source_count":len(ids),
        "prediction_seeds":c["prediction_seeds"],
        "variance_contract":{
            "local":"(C-D)^2/2 per source/time/probe",
            "global_floor":"mean local variance over all 630 sources",
            "floor_multiplier":1.0
        },
        "targets":result,
        "rank_sums":{
            "raw":raw_sum,
            "homoscedastic":hom_sum,
            "heteroscedastic_residual_only":het_sum,
            "path_action":action_sum
        },
        "pass_predicates":preds,
        "scope":"Fresh S3 House02/W2 offline confirmation only."
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
    raise SystemExit(0 if passed else 10)

if __name__=="__main__":
    main()
