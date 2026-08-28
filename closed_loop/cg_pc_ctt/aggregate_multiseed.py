#!/usr/bin/env python3
"""Preregistered multi-seed OFF/ON aggregator for CG-PC-CTT.

Reads case_result.json files recursively. Required schema:
{
  "house": "House01",
  "seed": 0,
  "arm": "off" | "on",
  "valid": true,
  "primary_error_m": 3.14,
  "first_release_s": null | 123.4,
  "false_confident_collapse": false
}

Primary paper endpoint: PMFS ExpectedValue(sourceProbability, 0.05) error.
Default confirmatory matrix is 3 Houses x 10 seeds = 30 matched pairs.

Frozen success criteria for the full 30-pair matrix:
  1) all 30 OFF/ON pairs valid;
  2) pooled relative error reduction >= 10%;
  3) one-sided paired sign test p <= 0.05 (20/30 improvements is sufficient);
  4) no House pooled mean degrades by more than 5%;
  5) zero false-confident-collapse flags.
These criteria are written before CG-PC-CTT multi-seed results exist.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

HOUSES=("House01","House02","House03")
EXPECTED_SEEDS=tuple(range(10))
BOOT=10000
SEED=20260827


def sign_p(k,n):
    from math import comb
    return sum(comb(n,i) for i in range(k,n+1))/float(2**n)


def load(root):
    rows=[]
    for p in sorted(root.rglob("case_result.json")):
        d=json.loads(p.read_text())
        d["_path"]=str(p); rows.append(d)
    return rows


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args()
    rows=load(a.root)
    keyed={}
    errors=[]
    for r in rows:
        try: key=(str(r["house"]),int(r["seed"]),str(r["arm"]))
        except Exception: errors.append(f"BAD_SCHEMA:{r.get('_path')}"); continue
        if key in keyed: errors.append(f"DUPLICATE:{key}")
        keyed[key]=r
    pairs=[]
    for h in HOUSES:
        for s in EXPECTED_SEEDS:
            off=keyed.get((h,s,"off")); on=keyed.get((h,s,"on"))
            if off is None or on is None:
                errors.append(f"MISSING_PAIR:{h}:seed{s}"); continue
            if not bool(off.get("valid")) or not bool(on.get("valid")):
                errors.append(f"INVALID_PAIR:{h}:seed{s}"); continue
            eo=float(off["primary_error_m"]); en=float(on["primary_error_m"])
            if not (math.isfinite(eo) and math.isfinite(en) and eo>=0 and en>=0):
                errors.append(f"BAD_ERROR:{h}:seed{s}"); continue
            pairs.append({"house":h,"seed":s,"off":eo,"on":en,"improved":en<eo,"delta":eo-en,"rel":(eo-en)/max(eo,1e-12),"collapse":bool(off.get("false_confident_collapse",False) or on.get("false_confident_collapse",False)),"first_release_s":on.get("first_release_s")})

    n=len(pairs); complete=(n==30 and not errors)
    if n:
        off=np.array([p["off"] for p in pairs]); on=np.array([p["on"] for p in pairs])
        pooled=(off.sum()-on.sum())/max(off.sum(),1e-12)
        k=sum(p["improved"] for p in pairs); sp=sign_p(k,n)
    else:
        pooled=float("nan"); k=0; sp=1.0

    per_house={}
    for h in HOUSES:
        pp=[p for p in pairs if p["house"]==h]
        if pp:
            x=np.array([p["off"] for p in pp]); y=np.array([p["on"] for p in pp])
            per_house[h]={"n":len(pp),"off_mean":float(x.mean()),"on_mean":float(y.mean()),"pooled_reduction":float((x.sum()-y.sum())/max(x.sum(),1e-12)),"improved_pairs":int(sum(p["improved"] for p in pp))}
        else: per_house[h]={"n":0}

    rng=np.random.default_rng(SEED); boots=[]
    if n:
        for _ in range(BOOT):
            idx=rng.integers(0,n,n); x=np.array([pairs[i]["off"] for i in idx]); y=np.array([pairs[i]["on"] for i in idx])
            boots.append((x.sum()-y.sum())/max(x.sum(),1e-12))
    ci=[float(np.quantile(boots,.025)),float(np.quantile(boots,.975))] if boots else [None,None]
    no_house_bad=all(v.get("n")==10 and v.get("pooled_reduction",-1)>=-0.05 for v in per_house.values())
    no_collapse=not any(p["collapse"] for p in pairs)
    criteria={"complete_30_pairs":complete,"pooled_reduction_ge_0p10":bool(n and pooled>=0.10),"paired_sign_p_le_0p05":bool(sp<=0.05),"no_house_degradation_gt_5pct":no_house_bad,"no_false_confident_collapse":no_collapse}
    go=all(criteria.values())
    out={"contract":"CG_PC_CTT_MULTI_SEED_CONFIRMATORY_V1","primary_metric":"PMFS_ExpectedValue_top_5_percent_error_m","pairs":n,"improved_pairs":k,"sign_test_one_sided_p":sp,"pooled_reduction":None if not n else float(pooled),"pooled_bootstrap_95ci":ci,"per_house":per_house,"criteria":criteria,"errors":errors,"verdict":"CG_PC_CTT_MULTI_SEED_GO" if go else "CG_PC_CTT_MULTI_SEED_NOT_GO"}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2),encoding="utf-8"); print(json.dumps(out,indent=2))
if __name__=="__main__": main()
