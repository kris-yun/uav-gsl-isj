#!/usr/bin/env python3
"""Deterministic connected Ward hierarchy for the frozen 168-cell D1A panel."""
from __future__ import annotations
import argparse,heapq,json
from pathlib import Path
import numpy as np
import pandas as pd

TARGET_M=(168,126,84,63,42,28,21,14,10,7,5,3,2)

def cost(A,B):
    d=A["centroid"]-B["centroid"]
    return float((A["n"]*B["n"]/(A["n"]+B["n"]))*np.dot(d,d))

def snap(active,C,n):
    out=np.empty(n,dtype=int)
    ordered=sorted(active,key=lambda c:min(C[c]["members"]))
    for g,c in enumerate(ordered):
        for i in C[c]["members"]: out[i]=g
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--out-json",type=Path,required=True)
    ap.add_argument("--merge-log",type=Path,required=True)
    a=ap.parse_args()
    p=pd.read_csv(a.panel,sep="\t")
    n=len(p)
    if n!=168: raise ValueError(f"expected 168, got {n}")
    grid={(int(r.pmfs_i),int(r.pmfs_j)):i for i,r in p.iterrows()}
    if len(grid)!=n: raise ValueError("duplicate PMFS cells")
    C={}
    for i,r in p.iterrows():
        neigh=set()
        for q in ((r.pmfs_i+1,r.pmfs_j),(r.pmfs_i-1,r.pmfs_j),
                  (r.pmfs_i,r.pmfs_j+1),(r.pmfs_i,r.pmfs_j-1)):
            j=grid.get((int(q[0]),int(q[1])))
            if j is not None: neigh.add(j)
        C[i]={"n":1,"centroid":np.array([float(r.x_m),float(r.y_m)]),
              "members":{i},"neighbors":neigh,"version":0}
    seen={0}; stack=[0]
    while stack:
        i=stack.pop()
        for j in C[i]["neighbors"]:
            if j not in seen: seen.add(j); stack.append(j)
    if len(seen)!=n: raise ValueError("panel is not four-neighbor connected")

    active=set(range(n)); heap=[]
    def push(a,b):
        if a not in active or b not in active or a==b: return
        ka,kb=min(C[a]["members"]),min(C[b]["members"])
        if ka>kb: a,b=b,a; ka,kb=kb,ka
        heapq.heappush(heap,(cost(C[a],C[b]),ka,kb,a,b,C[a]["version"],C[b]["version"]))
    for i in range(n):
        for j in C[i]["neighbors"]:
            if i<j: push(i,j)

    target=set(TARGET_M); out={n:snap(active,C,n).tolist()}; log=[]; nid=n
    while len(active)>2:
        while heap:
            co,_,_,a0,b0,va,vb=heapq.heappop(heap)
            if (a0 in active and b0 in active and C[a0]["version"]==va and
                C[b0]["version"]==vb and b0 in C[a0]["neighbors"]):
                break
        else: raise RuntimeError("heap exhausted")
        A,B=C[a0],C[b0]
        members=A["members"]|B["members"]; nn=A["n"]+B["n"]
        cen=(A["n"]*A["centroid"]+B["n"]*B["centroid"])/nn
        neigh=(A["neighbors"]|B["neighbors"])-{a0,b0}
        active.remove(a0);active.remove(b0)
        c=nid;nid+=1
        C[c]={"n":nn,"centroid":cen,"members":members,"neighbors":set(),"version":0}
        valid=[]
        for u in neigh:
            if u not in active: continue
            C[u]["neighbors"].discard(a0);C[u]["neighbors"].discard(b0)
            C[u]["neighbors"].add(c);C[u]["version"]+=1;valid.append(u)
        C[c]["neighbors"]=set(valid);active.add(c)
        for u in valid: push(c,u)
        log.append({"after_M":len(active),"new_size":nn,"ward_cost":co,
                    "new_min_panel_row":min(members)})
        if len(active) in target: out[len(active)]=snap(active,C,n).tolist()
    missing=sorted(target-set(out))
    if missing: raise RuntimeError(f"missing hierarchy levels {missing}")
    payload={"method":"four-neighbor connected Ward","target_M":list(TARGET_M),
             "panel_source_ids":p.source_id.tolist(),
             "labels_by_M":{str(k):v for k,v in sorted(out.items(),reverse=True)}}
    a.out_json.parent.mkdir(parents=True,exist_ok=True)
    a.out_json.write_text(json.dumps(payload,indent=2)+"\n")
    pd.DataFrame(log).to_csv(a.merge_log,sep="\t",index=False)
    print("levels",sorted(out,reverse=True))
if __name__=="__main__":
    main()
