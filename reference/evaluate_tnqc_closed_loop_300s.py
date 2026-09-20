#!/usr/bin/env python3
"""Evaluate full-budget TNQC closed-loop OFF versus FUSED matrix."""
from __future__ import annotations

import argparse, csv, json, math, re
from pathlib import Path

CASES=[("House01",0,-0.40,-2.90),("House01",1,-0.40,-2.90),
       ("House02",0,0.0,-1.0),("House02",1,0.0,-1.0),
       ("House03",0,-0.45,1.90),("House03",1,-0.45,1.90)]


def rows(p):
    with p.open(newline="",encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def final_update(run,budget=300.0):
    rr=rows(run/"context_bank"/"source_update_timing.csv")
    z=[(float(r["sim_time"]),int(r["source_update_id"])) for r in rr
       if float(r["sim_time"])<=budget+1e-9]
    if not z: raise ValueError(f"no source update <= {budget}: {run}")
    return max(z,key=lambda x:(x[0],x[1]))


def result_line(run):
    pat=re.compile(r"RESULT IS: Success=([^,]+), Search_t=([0-9.eE+-]+), Error=([0-9.eE+-]+)")
    out=None
    for line in (run/"launch.log").read_text(encoding="utf-8",errors="replace").splitlines():
        m=pat.search(line)
        if m:
            out={"success":m.group(1).strip(),"search_t":float(m.group(2)),"reported_error_m":float(m.group(3))}
    if out is None: raise ValueError(f"missing RESULT IS: {run}")
    return out


def metrics(run,tx,ty):
    t,u=final_update(run)
    p=run/"context_bank"/f"source_update_{u:04d}"/"source_posterior.csv"
    rr=[(int(r["cell_index"]),float(r["x"]),float(r["y"]),max(float(r["source_probability"]),0.0))
        for r in rows(p)]
    total=sum(q for _,_,_,q in rr)
    rr=[(i,x,y,q/total) for i,x,y,q in rr]
    mx=sum(x*q for _,x,_,q in rr); my=sum(y*q for _,_,y,q in rr)
    ranked=sorted(rr,key=lambda z:(-z[3],z[0]))
    n=max(1,math.ceil(0.05*len(ranked))); top=ranked[:n]; sm=sum(q for *_,q in top)
    x5=sum(x*q for _,x,_,q in top)/sm; y5=sum(y*q for _,_,y,q in top)/sm
    mode=max(rr,key=lambda z:(z[3],-z[0]))
    var=sum(q*((x-mx)**2+(y-my)**2) for _,x,y,q in rr)
    result=result_line(run)
    full_budget=295.0<=result["search_t"]<=330.0
    reported_match=abs(result["reported_error_m"]-math.hypot(x5-tx,y5-ty))<=0.02
    return {"selected_update_id":u,"selected_update_sim_time":t,
            "pmfs_top5_x":x5,"pmfs_top5_y":y5,
            "pmfs_top5_error_m":math.hypot(x5-tx,y5-ty),
            "map_x":mode[1],"map_y":mode[2],
            "map_error_m":math.hypot(mode[1]-tx,mode[2]-ty),
            "mean_x":mx,"mean_y":my,"mean_error_m":math.hypot(mx-tx,my-ty),
            "variance_m2":var,"result_line":result,
            "full_budget_audit_pass":full_budget,
            "reported_error_rounding_audit_pass":reported_match}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-root",type=Path,required=True)
    ap.add_argument("--determinism-root",type=Path)
    ap.add_argument("--json-out",type=Path)
    args=ap.parse_args()
    cases=[]; det_all=True
    for house,seed,tx,ty in CASES:
        off=args.run_root/f"{house}_seed{seed}_off_off"
        fused=args.run_root/f"{house}_seed{seed}_off_off_tnqc_fused"
        om=metrics(off,tx,ty); fm=metrics(fused,tx,ty)
        dpath=(args.determinism_root or args.run_root)/f"{house}_seed{seed}_off_off_tnqc_shadow"/"tnqc_shadow_determinism.json"
        if not dpath.exists():
            det=False
        else:
            det=bool(json.loads(dpath.read_text(encoding="utf-8")).get("pass",False))
        det_all &= det
        gain=(om["pmfs_top5_error_m"]-fm["pmfs_top5_error_m"])/max(abs(om["pmfs_top5_error_m"]),1e-12)
        cases.append({"house":house,"seed":seed,"truth":[tx,ty],"off":om,"fused":fm,
                      "improvement_fraction":gain,"shadow_determinism_pass":det})

    valid=det_all and all(c["off"]["full_budget_audit_pass"] and c["fused"]["full_budget_audit_pass"]
                          and c["off"]["reported_error_rounding_audit_pass"]
                          and c["fused"]["reported_error_rounding_audit_pass"] for c in cases)
    no=sum(c["off"]["pmfs_top5_error_m"] for c in cases)/6
    nf=sum(c["fused"]["pmfs_top5_error_m"] for c in cases)/6
    pooled=(no-nf)/max(abs(no),1e-12)
    improved=sum(c["fused"]["pmfs_top5_error_m"]<c["off"]["pmfs_top5_error_m"] for c in cases)
    worst=max((c["fused"]["pmfs_top5_error_m"]-c["off"]["pmfs_top5_error_m"])/max(abs(c["off"]["pmfs_top5_error_m"]),1e-12)
              for c in cases)
    collapse=[f'{c["house"]}_seed{c["seed"]}' for c in cases
              if c["fused"]["variance_m2"]<1.0 and c["fused"]["pmfs_top5_error_m"]>2.0]
    passed=valid and pooled>=0.10 and improved>=4 and worst<=0.25 and not collapse
    payload={"contract":"TNQC_CLOSED_LOOP_300S_MATRIX_V1","cases":cases,
             "pooled_off_error_m":no,"pooled_fused_error_m":nf,
             "pooled_improvement_fraction":pooled,"improved_pairs":improved,
             "worst_pair_degradation_fraction":worst,
             "false_confident_collapse_cases":collapse,
             "all_shadow_determinism_pass":det_all,"valid":valid,
             "development_gate_pass":passed,
             "verdict":"TNQC_CLOSED_LOOP_300S_PASS" if passed else "TNQC_CLOSED_LOOP_300S_FAIL"}
    text=json.dumps(payload,indent=2,sort_keys=True); print(text)
    out=args.json_out or args.run_root/"tnqc_closed_loop_300s_evaluation.json"
    out.write_text(text+"\n",encoding="utf-8")
    if not valid: raise SystemExit(5)


if __name__=="__main__":
    main()
