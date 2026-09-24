#!/usr/bin/env python3
"""Deterministic four-neighbor connectivity-constrained Ward hierarchy.

No plume observations are used. The hierarchy depends only on the frozen
equal-area PMFS source-cell geometry.
"""
from __future__ import annotations
import argparse, heapq, json
from pathlib import Path
import numpy as np
import pandas as pd

TARGET_M=(630,420,315,210,158,126,90,63,45,30,21,15,10,6,4,3,2)

def ward_cost(a,b):
    na,nb=a["n"],b["n"]
    d=a["centroid"]-b["centroid"]
    return float((na*nb/(na+nb))*np.dot(d,d))

def canonical_pair(a,b,clusters):
    ka=min(clusters[a]["members"])
    kb=min(clusters[b]["members"])
    return (a,b) if ka<kb else (b,a)

def snapshot(active, clusters, n_sources):
    labs=np.empty(n_sources,dtype=int)
    ordered=sorted(active,key=lambda c:min(clusters[c]["members"]))
    for g,c in enumerate(ordered):
        for i in clusters[c]["members"]:
            labs[i]=g
    return labs

def build(bank):
    n=len(bank)
    if n!=630:
        raise ValueError(f"expected 630 source cells, got {n}")
    grid={(int(r.pmfs_i),int(r.pmfs_j)):i for i,r in bank.iterrows()}

    # verify one connected four-neighbor component
    seen={0}; stack=[0]
    while stack:
        i=stack.pop()
        r=bank.iloc[i]
        for q in ((r.pmfs_i+1,r.pmfs_j),(r.pmfs_i-1,r.pmfs_j),
                  (r.pmfs_i,r.pmfs_j+1),(r.pmfs_i,r.pmfs_j-1)):
            j=grid.get((int(q[0]),int(q[1])))
            if j is not None and j not in seen:
                seen.add(j); stack.append(j)
    if len(seen)!=n:
        raise ValueError(f"source-bank four-neighbor graph disconnected: {len(seen)}/{n}")

    clusters={}
    for i,r in bank.iterrows():
        neigh=set()
        for q in ((r.pmfs_i+1,r.pmfs_j),(r.pmfs_i-1,r.pmfs_j),
                  (r.pmfs_i,r.pmfs_j+1),(r.pmfs_i,r.pmfs_j-1)):
            j=grid.get((int(q[0]),int(q[1])))
            if j is not None: neigh.add(j)
        clusters[i]={
            "active":True,"version":0,"n":1,
            "centroid":np.array([float(r.x_m),float(r.y_m)]),
            "members":{i},"neighbors":neigh
        }

    active=set(range(n)); heap=[]
    def push(a,b):
        if a==b or a not in active or b not in active: return
        a,b=canonical_pair(a,b,clusters)
        ca,cb=clusters[a],clusters[b]
        heapq.heappush(heap,(ward_cost(ca,cb),
                             min(ca["members"]),min(cb["members"]),
                             a,b,ca["version"],cb["version"]))
    for a in range(n):
        for b in clusters[a]["neighbors"]:
            if a<b: push(a,b)

    targets=set(TARGET_M)
    out={n:snapshot(active,clusters,n).tolist()}
    next_id=n
    merge_log=[]

    while len(active)>2:
        while heap:
            cost,_,_,a,b,va,vb=heapq.heappop(heap)
            if (a in active and b in active and
                clusters[a]["version"]==va and clusters[b]["version"]==vb and
                b in clusters[a]["neighbors"]):
                break
        else:
            raise RuntimeError("heap exhausted before hierarchy completed")

        A,B=clusters[a],clusters[b]
        new_members=A["members"]|B["members"]
        nn=A["n"]+B["n"]
        cen=(A["n"]*A["centroid"]+B["n"]*B["centroid"])/nn
        neigh=(A["neighbors"]|B["neighbors"])-{a,b}
        c=next_id; next_id+=1
        clusters[c]={
            "active":True,"version":0,"n":nn,"centroid":cen,
            "members":new_members,"neighbors":set()
        }

        # retire a,b first
        active.remove(a); active.remove(b)
        clusters[a]["active"]=False; clusters[b]["active"]=False

        valid_neigh=[]
        for u in neigh:
            if u not in active: continue
            clusters[u]["neighbors"].discard(a)
            clusters[u]["neighbors"].discard(b)
            clusters[u]["neighbors"].add(c)
            # u's centroid/size did not change, so existing heap edges from u
            # to its unchanged neighbors remain valid. Bumping u.version here
            # would incorrectly invalidate those candidates without re-pushing
            # them, distorting the constrained-Ward merge order.
            valid_neigh.append(u)
        clusters[c]["neighbors"]=set(valid_neigh)
        active.add(c)

        merge_log.append({
            "after_M":len(active),
            "left_min_row":min(A["members"]),
            "right_min_row":min(B["members"]),
            "new_min_row":min(new_members),
            "new_size":nn,
            "ward_cost":cost
        })

        for u in valid_neigh: push(c,u)

        if len(active) in targets:
            out[len(active)]=snapshot(active,clusters,n).tolist()

    missing=sorted(targets-set(out))
    if missing:
        raise RuntimeError(f"missing requested hierarchy levels: {missing}")
    return out, merge_log

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-bank",type=Path,required=True)
    ap.add_argument("--out-json",type=Path,required=True)
    ap.add_argument("--merge-log",type=Path,required=True)
    a=ap.parse_args()
    bank=pd.read_csv(a.source_bank,sep="\t")
    hierarchy,log=build(bank)
    a.out_json.parent.mkdir(parents=True,exist_ok=True)
    payload={
        "method":"four-neighbor connectivity-constrained Ward",
        "target_M":list(TARGET_M),
        "source_count":len(bank),
        "source_order":bank.source_id.tolist(),
        "labels_by_M":{str(k):v for k,v in sorted(hierarchy.items(),reverse=True)}
    }
    a.out_json.write_text(json.dumps(payload,indent=2)+"\n")
    pd.DataFrame(log).to_csv(a.merge_log,sep="\t",index=False)
    print("built hierarchy:",sorted(hierarchy,reverse=True))

if __name__=="__main__":
    main()
