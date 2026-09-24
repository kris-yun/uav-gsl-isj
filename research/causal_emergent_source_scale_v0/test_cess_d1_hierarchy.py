#!/usr/bin/env python3
"""Regression test for connectivity-constrained Ward merge ordering."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location(
    "cess_ward", HERE/"build_connected_ward_hierarchy.py"
)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def synthetic_bank():
    # Exactly 630 connected cells so production build() invariants are tested.
    rows=[]
    k=0
    for i in range(21):
        for j in range(30):
            rows.append({
                "source_id":f"s{k:03d}",
                "pmfs_i":i,"pmfs_j":j,
                "x_m":0.3*i,"y_m":0.3*j,"z_m":0.2,
            })
            k+=1
    return pd.DataFrame(rows)

def naive_prefix(bank,n_steps=120):
    n=len(bank)
    grid={(int(r.pmfs_i),int(r.pmfs_j)):i for i,r in bank.iterrows()}
    clusters={}
    for i,r in bank.iterrows():
        neigh=set()
        for q in ((r.pmfs_i+1,r.pmfs_j),(r.pmfs_i-1,r.pmfs_j),
                  (r.pmfs_i,r.pmfs_j+1),(r.pmfs_i,r.pmfs_j-1)):
            j=grid.get((int(q[0]),int(q[1])))
            if j is not None: neigh.add(j)
        clusters[i]={
            "n":1,
            "centroid":np.array([float(r.x_m),float(r.y_m)]),
            "members":{i},
            "neighbors":neigh,
        }
    active=set(range(n))
    next_id=n
    out=[]
    for _ in range(n_steps):
        candidates=[]
        for a in active:
            for b in clusters[a]["neighbors"]:
                if b not in active or a==b: continue
                aa,bb=mod.canonical_pair(a,b,clusters)
                if aa!=a: continue
                A,B=clusters[aa],clusters[bb]
                candidates.append((
                    mod.ward_cost(A,B),
                    min(A["members"]),min(B["members"]),
                    aa,bb
                ))
        if not candidates:
            raise AssertionError("naive hierarchy exhausted")
        cost,_,_,a,b=min(candidates)
        A,B=clusters[a],clusters[b]
        members=A["members"]|B["members"]
        nn=A["n"]+B["n"]
        cen=(A["n"]*A["centroid"]+B["n"]*B["centroid"])/nn
        neigh=(A["neighbors"]|B["neighbors"])-{a,b}
        c=next_id; next_id+=1

        active.remove(a); active.remove(b)
        valid=[u for u in neigh if u in active]
        for u in valid:
            clusters[u]["neighbors"].discard(a)
            clusters[u]["neighbors"].discard(b)
            clusters[u]["neighbors"].add(c)
        clusters[c]={
            "n":nn,"centroid":cen,"members":members,
            "neighbors":set(valid)
        }
        active.add(c)
        out.append((
            min(A["members"]),min(B["members"]),nn,float(cost)
        ))
    return out

def main():
    bank=synthetic_bank()
    _,log=mod.build(bank)
    ref=naive_prefix(bank,120)
    got=[(
        int(x["left_min_row"]),int(x["right_min_row"]),
        int(x["new_size"]),float(x["ward_cost"])
    ) for x in log[:120]]
    assert len(got)==len(ref)
    for i,(a,b) in enumerate(zip(got,ref)):
        assert a[:3]==b[:3],(i,a,b)
        assert np.isclose(a[3],b[3],rtol=0,atol=1e-12),(i,a,b)
    print("CESS D1 hierarchy self-test: PASS")

if __name__=="__main__":
    main()
