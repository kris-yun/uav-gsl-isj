#!/usr/bin/env python3
"""Scale-free reversible outer posterior for frozen bridge candidate scores.

Each accepted event supplies one score per candidate (higher is better). To
avoid tuning a score temperature or mixing coefficient:
  1) convert candidate scores within each event to normal ranks z_e(s);
  2) split accepted events by accepted-event parity;
  3) aggregate z_e within each fold and divide by sqrt(n_fold);
  4) rank-normalize each fold aggregate again;
  5) combine folds g=(z_even+z_odd)/sqrt(2);
  6) q(s) proportional to q0(s)*exp(g(s)).

Gate-FAIL events are permanently excluded, so exact ABSTAIN cannot later be
undone by cumulative rescoring. Release requires at least one accepted event in
both folds. This is a candidate online contract derived from the empirically
positive V11 fixed-prior reversible rank architecture; it remains frozen only
if the offline bridge gate passes.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
from statistics import NormalDist
import numpy as np
ND=NormalDist()


def normal_ranks(scores):
    x=np.asarray(scores,float); n=len(x)
    order=np.argsort(-x,kind="mergesort")
    rank=np.empty(n,int); rank[order]=np.arange(1,n+1)
    # best score -> large positive z
    p=1.0-(rank-.5)/n
    return np.asarray([ND.inv_cdf(float(v)) for v in p])

def posterior(events,q0=None):
    accepted=[e for e in events if e["accepted"]]
    if not accepted: return None,{"released":False,"reason":"NO_ACCEPTED_EVENTS"}
    ids=accepted[0]["candidate_id"]; S=len(ids)
    for e in accepted:
        if list(e["candidate_id"])!=list(ids): raise ValueError("candidate order drift")
    folds=[[],[]]
    for k,e in enumerate(accepted): folds[k%2].append(normal_ranks(e["score"]))
    if not folds[0] or not folds[1]: return None,{"released":False,"reason":"NEED_BOTH_FOLDS","accepted_events":len(accepted)}
    zf=[]; nf=[]
    for f in folds:
        A=np.sum(np.stack(f),axis=0)/math.sqrt(len(f)); zf.append(normal_ranks(A)); nf.append(len(f))
    g=(zf[0]+zf[1])/math.sqrt(2.0)
    prior=np.ones(S)/S if q0 is None else np.asarray(q0,float)
    if prior.shape!=(S,) or np.any(prior<0) or prior.sum()<=0: raise ValueError("invalid q0")
    prior=prior/prior.sum(); logq=np.log(np.maximum(prior,1e-300))+g; logq-=logq.max(); q=np.exp(logq); q/=q.sum()
    return q,{"released":True,"accepted_events":len(accepted),"fold_counts":nf,"max_g":float(g.max()),"min_g":float(g.min())}

def load_events(path):
    # CSV: event_id,candidate_id,score,accepted. Every event must contain all candidates.
    with path.open(newline="") as f: rr=list(csv.DictReader(f))
    by={}
    for r in rr:
        eid=r["event_id"]; by.setdefault(eid,[]).append(r)
    out=[]
    for eid in sorted(by,key=lambda z:(len(z),z)):
        r=by[eid]; accepted={x["accepted"].lower() in {"1","true","yes"} for x in r}
        if len(accepted)!=1: raise ValueError(f"event {eid}: accepted flag differs by candidate")
        out.append({"event_id":eid,"candidate_id":[x["candidate_id"] for x in r],"score":np.asarray([float(x["score"]) for x in r]),"accepted":accepted.pop()})
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("scores_csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); ev=load_events(a.scores_csv); q,meta=posterior(ev)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    payload={"contract":"CG_PC_CTT_REVERSIBLE_RANK_POSTERIOR_V1","meta":meta,"posterior":None if q is None else q.tolist()}
    a.out.write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(json.dumps(payload,indent=2))
if __name__=="__main__": main()
