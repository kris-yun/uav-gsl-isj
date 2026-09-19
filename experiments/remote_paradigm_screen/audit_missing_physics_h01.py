#!/usr/bin/env python3
"""Fixed offline premise audit for learned-missing-physics candidate.

Compares, on the same frozen H01 SA-fast route:
1) observed sensor history,
2) exact GADEN candidate-forward traces replayed through frozen FOPDT,
3) estimated-transport provider candidate responses.

No fitting, threshold tuning, posterior update, or planner is performed.
"""
from __future__ import annotations
import json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REF_ASSETS=ROOT/"evidence/cstar_current_runtime_assets240_20260907/realizations"
EXACT=ROOT/"evidence/cstar_m1_candidate_forward_20260909_r2"
EST_SA=ROOT/"evidence/cstar_m1_estimated_transport_h01_screen_240s_SA_trace_v3_20260910.json"
EST_ALL=ROOT/"evidence/cstar_m1_estimated_transport_h01_screen_240s_20260910.json"

def read_jsonl(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def fopdt(times, exposure, tau=1.2, dead=0.4):
    hist=[(0.0,0.0)]; y=0.0; prev=0.0; out=[]
    for t,u in zip(times,exposure):
        dt=t-prev; hist.append((t,u)); q=t-dead; delayed=0.0
        if q>0:
            while len(hist)>2 and hist[1][0]<q: hist.pop(0)
            if q>=hist[-1][0]: delayed=hist[-1][1]
            else:
                for (tl,ul),(tr,ur) in zip(hist,hist[1:]):
                    if q<=tr:
                        r=(q-tl)/(tr-tl); delayed=ul+r*(ur-ul); break
        a=math.exp(-dt/tau); y=a*y+(1-a)*delayed; out.append(y); prev=t
    return out

def log_mse(a,b):
    return sum((math.log1p(max(0,x))-math.log1p(max(0,y)))**2 for x,y in zip(a,b))/len(a)

def event(a):
    idx=[i for i,x in enumerate(a) if x>0.1]
    return dict(hit_count=len(idx), first_hit_s=(0.2*idx[0] if idx else None),
                peak=max(a), integrated_ppm_s=0.2*sum(a))

def main():
    obs_rows=read_jsonl(REF_ASSETS/"H01_SA_fast/measured_history.jsonl")
    a_rows=read_jsonl(EXACT/"H01_SA_fast/candidate_forward_input.jsonl")
    b_rows=read_jsonl(EXACT/"H01_SB_fast/candidate_forward_input.jsonl")
    assert [r["stamp_ns"] for r in a_rows]==[r["stamp_ns"] for r in b_rows]
    assert max(math.dist(x["pose_xy"],y["pose_xy"]) for x,y in zip(a_rows,b_rows))==0.0

    obs=[r["gas_ppm"] for r in obs_rows]
    times=[r["t_sim_s"] for r in a_rows]
    exact_a=fopdt(times,[r["candidate_forward_input_ppm"] for r in a_rows])
    exact_b=fopdt(times,[r["candidate_forward_input_ppm"] for r in b_rows])
    est_a=json.loads(EST_SA.read_text())["candidates"][0]["sensor_ppm"]
    est_j=json.loads(EST_ALL.read_text())
    est_b=next(c["sensor_ppm"] for c in est_j["candidates"] if c["candidate"]=="SB")

    def block(a,b):
        ma,mb=log_mse(obs,a),log_mse(obs,b)
        return {"SA":{"log1p_mse":ma,"event":event(a)},
                "SB":{"log1p_mse":mb,"event":event(b)},
                "rank1":"SA" if ma<mb else "SB"}

    report={"contract":"MISSING_PHYSICS_H01_SAME_ROUTE_V1",
            "observed":event(obs),"exact":block(exact_a,exact_b),
            "estimated":block(est_a,est_b)}

    hit=[x>0.1 for x in obs]; e_hit=e_blank=e_all=0.0
    for y,p,h in zip(obs,est_a,hit):
        e=(math.log1p(max(0,y))-math.log1p(max(0,p)))**2
        e_all+=e
        if h:e_hit+=e
        else:e_blank+=e
    report["estimated_SA_error_fraction"]={"observed_hit":e_hit/e_all,
                                           "observed_blank":e_blank/e_all}
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
