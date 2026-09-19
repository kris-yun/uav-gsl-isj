#!/usr/bin/env python3
"""
Offline proxy screen for remote-paradigm candidate selection.

Uses only the existing 12 controlled measured histories:
H01/H02/H03 x {SA,SB} x {fast,slow}.

This is NOT a model-training or paper-performance script. It reproduces
mechanism-level screens used to reject/promote candidate ideas before any
new closed-loop experiment.

Run from repository root:
    python experiments/remote_paradigm/screen_representation_proxies.py
"""
from __future__ import annotations

import json, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "evidence" / "cstar_current_runtime_assets240_20260907" / "realizations"
HOUSES = ("H01","H02","H03")
SOURCES = ("SA","SB")
WINDS = ("fast","slow")


def load_trace(house, source, wind):
    p = DATA / f"{house}_{source}_{wind}" / "measured_history.jsonl"
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return np.asarray([max(0.0, float(r["gas_ppm"])) for r in rows], dtype=float)


def rms(a,b):
    n=min(len(a),len(b))
    if n==0: return float("nan")
    d=np.asarray(a[:n])-np.asarray(b[:n])
    return float(np.sqrt(np.mean(d*d)))


def moving_average(x,k):
    x=np.asarray(x,float)
    if len(x)==0:return x
    c=np.cumsum(np.r_[0.0,x])
    out=np.empty_like(x)
    for i in range(len(x)):
        j=max(0,i-k+1)
        out[i]=(c[i+1]-c[j])/(i-j+1)
    return out


def contrast_ratio(traces, house, horizon_s=240.0, transform="raw"):
    n=int(round(horizon_s/0.2))
    def tx(x):
        x=x[:n]
        if transform=="log": return np.log1p(x)
        if transform=="hit": return (x>0.1).astype(float)
        return x
    af=tx(traces[(house,"SA","fast")]); a_s=tx(traces[(house,"SA","slow")])
    bf=tx(traces[(house,"SB","fast")]); b_s=tx(traces[(house,"SB","slow")])
    src=0.5*(rms(af,bf)+rms(a_s,b_s))
    wind=0.5*(rms(af,a_s)+rms(bf,b_s))
    return {"source":src,"wind":wind,"wind_source_ratio":wind/(src+1e-12)}


def factorial_proxy(traces,house,horizon_s=180.0):
    n=int(round(horizon_s/0.2))
    af=np.log1p(traces[(house,"SA","fast")][:n])
    a_s=np.log1p(traces[(house,"SA","slow")][:n])
    bf=np.log1p(traces[(house,"SB","fast")][:n])
    b_s=np.log1p(traces[(house,"SB","slow")][:n])
    mean_a=(af+a_s)/2; mean_b=(bf+b_s)/2
    src=(mean_a-mean_b)/2
    interaction=(af-a_s-bf+b_s)/4
    ns=float(np.sqrt(np.mean(src*src)))
    ni=float(np.sqrt(np.mean(interaction*interaction)))
    return {"source_rms":ns,"interaction_rms":ni,"source_interaction_ratio":ns/(ni+1e-12)}


def vector_stats(x):
    x=np.asarray(x,float)
    if len(x)==0:return np.zeros(9)
    m=float(x.mean()); sd=float(x.std())
    q=np.quantile(x,[.5,.9,.99])
    dx=np.diff(x)
    return np.asarray([m,sd,*q,float(x.max()),float(x.min()),
                       float(np.sqrt(np.mean(dx*dx))) if len(dx) else 0.0,
                       float(np.mean(x>math.log1p(.1)))],float)


def normalized(v):
    v=np.asarray(v,float)
    n=float(np.linalg.norm(v))
    return v/(n if n>1e-12 else 1.0)


def eta_state(raw,horizon_s):
    raw=np.asarray(raw,float)
    if len(raw)==0:return np.zeros(7)
    q95,q99=np.quantile(raw,[.95,.99])
    topn=max(1,int(.01*len(raw)))
    top=float(np.mean(np.sort(raw)[-topn:]))
    idx=np.flatnonzero(raw>.1)
    fp=(float(idx[0])*0.2/horizon_s) if len(idx) else 1.0
    return normalized([
        math.log1p(q95),math.log1p(q99),math.log1p(float(raw.max(initial=0))),
        math.log1p(top),float(np.mean(raw>.01)),float(np.mean(raw>.1)),fp
    ])


def predictive_eta_rep(raw,horizon_s=240,k=25,kind="combo"):
    n=min(len(raw),int(round(horizon_s/0.2)))
    raw=np.asarray(raw[:n],float)
    log=np.log1p(raw)
    pred=moving_average(log,k)
    p=normalized(vector_stats(pred))
    e=eta_state(raw,horizon_s)
    if kind=="pred": return p
    if kind=="eta": return e
    return np.r_[p,e]


def pair_identity(rep_af,rep_as,rep_bf,rep_bs):
    da_same=np.linalg.norm(rep_as-rep_af)
    da_cross=np.linalg.norm(rep_as-rep_bf)
    db_same=np.linalg.norm(rep_bs-rep_bf)
    db_cross=np.linalg.norm(rep_bs-rep_af)
    return int(da_same<da_cross)+int(db_same<db_cross)


def eta_rescue_screen(traces,house,horizon_s=240,k=25):
    reps={}
    for s in SOURCES:
        for w in WINDS:
            raw=traces[(house,s,w)]
            for kind in ("pred","eta","combo"):
                reps[(s,w,kind)]=predictive_eta_rep(raw,horizon_s,k,kind)
    out={}
    for kind in ("pred","eta","combo"):
        af=reps[("SA","fast",kind)]; a_s=reps[("SA","slow",kind)]
        bf=reps[("SB","fast",kind)]; b_s=reps[("SB","slow",kind)]
        src=.5*(np.linalg.norm(af-bf)+np.linalg.norm(a_s-b_s))
        wind=.5*(np.linalg.norm(af-a_s)+np.linalg.norm(bf-b_s))
        out[kind]={
            "held_wind_identity":pair_identity(af,a_s,bf,b_s),
            "source_distance":float(src),
            "wind_distance":float(wind),
            "wind_source_ratio":float(wind/(src+1e-12))
        }
    return out


def ar_feature(raw,horizon_s=240,p=3,lam=.01):
    n=min(len(raw),int(round(horizon_s/0.2)))
    y=np.log1p(np.asarray(raw[:n],float))
    if len(y)<=p: return np.zeros(p+2)
    X=[];Y=[]
    for t in range(p,len(y)):
        X.append([1.0,*y[t-p:t][::-1]])
        Y.append(y[t])
    X=np.asarray(X);Y=np.asarray(Y)
    reg=np.eye(p+1)*lam;reg[0,0]=0
    beta=np.linalg.solve(X.T@X+reg,X.T@Y)
    pred=X@beta
    mse=float(np.mean((Y-pred)**2))
    var=float(np.var(Y))
    return np.r_[beta,math.log1p(mse),1-mse/(var+1e-12)]


def ar_identity_screen(traces,house,horizon_s=240,p=3):
    R={(s,w):ar_feature(traces[(house,s,w)],horizon_s,p) for s in SOURCES for w in WINDS}
    af,a_s,bf,b_s=R[("SA","fast")],R[("SA","slow")],R[("SB","fast")],R[("SB","slow")]
    src=.5*(rms(af,bf)+rms(a_s,b_s))
    wind=.5*(rms(af,a_s)+rms(bf,b_s))
    return {"held_wind_identity":pair_identity(af,a_s,bf,b_s),
            "wind_source_ratio":wind/(src+1e-12)}


def main():
    traces={(h,s,w):load_trace(h,s,w) for h in HOUSES for s in SOURCES for w in WINDS}
    out={"contract":"REMOTE_PARADIGM_PROXY_SCREEN_V1","houses":{}}
    for h in HOUSES:
        out["houses"][h]={
            "factorial":{
                str(H):factorial_proxy(traces,h,H) for H in (60,120,180,240)
            },
            "raw_log_hit":{
                str(H):{m:contrast_ratio(traces,h,H,m) for m in ("raw","log","hit")}
                for H in (60,120,180,240)
            },
            "predictive_eta":{
                "180":eta_rescue_screen(traces,h,180,25),
                "240_k25":eta_rescue_screen(traces,h,240,25),
                "240_k50":eta_rescue_screen(traces,h,240,50),
            },
            "ar_dynamics":{
                str(H):{str(p):ar_identity_screen(traces,h,H,p) for p in (3,8,20)}
                for H in (120,180,240)
            }
        }
    outpath=ROOT/"evidence"/"remote_paradigm_loop_20260919"/"PROXY_SCREEN_V1.json"
    outpath.parent.mkdir(parents=True,exist_ok=True)
    outpath.write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(outpath)
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    main()
