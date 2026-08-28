#!/usr/bin/env python3
"""External truth evaluator for one CG-PC-CTT closed-loop arm.

The online method must never import this file. It reads a final posterior CSV
with columns x,y,source_probability and writes the standard case_result.json
consumed by aggregate_multiseed.py.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path


def read(path):
    with path.open(newline="",encoding="utf-8-sig") as f: return list(csv.DictReader(f))

def metrics(path,tx,ty):
    rr=read(path); xyz=[(float(r["x"]),float(r["y"]),max(float(r["source_probability"]),0.0)) for r in rr]
    z=sum(p for _,_,p in xyz)
    if not xyz or z<=0: raise ValueError("invalid posterior")
    xyz=[(x,y,p/z) for x,y,p in xyz]
    n=max(1,math.ceil(.05*len(xyz))); top=sorted(xyz,key=lambda q:q[2],reverse=True)[:n]; m=sum(p for _,_,p in top)
    x=sum(a*p for a,_,p in top)/m; y=sum(b*p for _,b,p in top)/m
    mx=sum(a*p for a,_,p in xyz); my=sum(b*p for _,b,p in xyz)
    var=sum(p*((a-mx)**2+(b-my)**2) for a,b,p in xyz)
    return {"primary_error_m":math.hypot(x-tx,y-ty),"top5_x":x,"top5_y":y,"variance_m2":var,"cell_count":len(xyz)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--posterior-csv",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--house",required=True); ap.add_argument("--seed",type=int,required=True); ap.add_argument("--arm",choices=["off","on"],required=True)
    ap.add_argument("--truth-x",type=float,required=True); ap.add_argument("--truth-y",type=float,required=True); ap.add_argument("--first-release-s",type=float,default=None); ap.add_argument("--binary-sha256",default=None); a=ap.parse_args()
    m=metrics(a.posterior_csv,a.truth_x,a.truth_y)
    collapse=bool(m["variance_m2"]<1.0 and m["primary_error_m"]>2.0)
    out={"contract":"CG_PC_CTT_CASE_RESULT_V1","house":a.house,"seed":a.seed,"arm":a.arm,"valid":True,"primary_metric":"PMFS_ExpectedValue_top_5_percent","primary_error_m":m["primary_error_m"],"variance_m2":m["variance_m2"],"false_confident_collapse":collapse,"first_release_s":a.first_release_s,"binary_sha256":a.binary_sha256,"posterior_csv":str(a.posterior_csv),"truth_eval_only":[a.truth_x,a.truth_y]}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2),encoding="utf-8"); print(json.dumps(out,indent=2))
if __name__=="__main__": main()
