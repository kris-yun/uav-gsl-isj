#!/usr/bin/env python3
"""Freeze a geometry-only connected 160-source CESS D1A panel.

No plume observations, C/D scores, source truths, or R0 statistics are used.
The panel is a connected, globally spanning graph skeleton with a one-hop
thickening so adjacent 0.30 m microstates remain represented.
"""
from __future__ import annotations
import argparse, hashlib
from collections import deque
from pathlib import Path
import numpy as np
import pandas as pd

N_BANK=630
N_PANEL=160
N_ANCHORS=8

def adjacency(bank):
    grid={(int(r.pmfs_i),int(r.pmfs_j)):i for i,r in bank.iterrows()}
    adj=[[] for _ in range(len(bank))]
    for i,r in bank.iterrows():
        for q in ((r.pmfs_i+1,r.pmfs_j),(r.pmfs_i-1,r.pmfs_j),
                  (r.pmfs_i,r.pmfs_j+1),(r.pmfs_i,r.pmfs_j-1)):
            j=grid.get((int(q[0]),int(q[1])))
            if j is not None: adj[i].append(j)
        adj[i].sort()
    return adj

def bfs_dist(adj,s):
    d=np.full(len(adj),-1,dtype=int); d[s]=0
    q=deque([s])
    while q:
        u=q.popleft()
        for v in adj[u]:
            if d[v]<0:
                d[v]=d[u]+1; q.append(v)
    if (d<0).any(): raise ValueError("source-bank graph is disconnected")
    return d

def shortest_path(adj,s,t):
    parent={s:None}; q=deque([s])
    while q:
        u=q.popleft()
        if u==t: break
        for v in adj[u]:
            if v not in parent:
                parent[v]=u; q.append(v)
    if t not in parent: raise ValueError("no path")
    out=[]; u=t
    while u is not None:
        out.append(u); u=parent[u]
    return out[::-1]

def select(bank):
    if len(bank)!=N_BANK or bank.source_id.nunique()!=N_BANK:
        raise ValueError("expected frozen 630-source Gate1A bank")
    adj=adjacency(bank)
    xy=bank[["x_m","y_m"]].to_numpy(float)

    # Graph center: minimum eccentricity, then minimum total graph distance,
    # then smallest original source-bank row.
    center_keys=[]
    all_dist=[]
    for s in range(N_BANK):
        d=bfs_dist(adj,s); all_dist.append(d)
        center_keys.append((int(d.max()),int(d.sum()),s))
    center=min(range(N_BANK),key=lambda s:center_keys[s])
    dcenter=all_dist[center]

    # Geometry-only Euclidean farthest-point anchors.
    anchors=[center]
    mind=np.linalg.norm(xy-xy[center],axis=1)
    while len(anchors)<N_ANCHORS:
        mx=float(mind.max())
        cand=np.where(np.isclose(mind,mx,rtol=0,atol=1e-12))[0]
        a=int(cand.min())
        anchors.append(a)
        mind=np.minimum(mind,np.linalg.norm(xy-xy[a],axis=1))

    # Deterministic shortest-path skeleton from graph center to all anchors.
    skeleton=set()
    for a in anchors:
        skeleton.update(shortest_path(adj,center,a))

    selected=set(skeleton)
    additions=[]
    expansion_centers=list(anchors)

    # One-hop thickening. Prefer boundary cells that close/fill the largest
    # number of selected-neighbor contacts; within that class use farthest
    # point spacing relative to anchors + prior additions.
    while len(selected)<N_PANEL:
        boundary={v for u in selected for v in adj[u] if v not in selected}
        if not boundary: raise RuntimeError("panel expansion exhausted")
        conn={v:sum(w in selected for w in adj[v]) for v in boundary}
        max_conn=max(conn.values())
        cand=sorted(v for v in boundary if conn[v]==max_conn)
        sep=[]
        for v in cand:
            sep.append(min(float(np.linalg.norm(xy[v]-xy[a]))
                           for a in expansion_centers))
        mx=max(sep)
        pick=min(v for v,z in zip(cand,sep)
                 if np.isclose(z,mx,rtol=0,atol=1e-12))
        selected.add(pick)
        additions.append(pick)
        expansion_centers.append(pick)

    if len(selected)!=N_PANEL: raise AssertionError("panel size drift")

    # Connected induced subgraph check.
    start=min(selected); seen={start}; q=deque([start])
    while q:
        u=q.popleft()
        for v in adj[u]:
            if v in selected and v not in seen:
                seen.add(v); q.append(v)
    if seen!=selected: raise AssertionError("D1A panel is not connected")

    sel=sorted(selected)
    rows=[]
    anchor_set=set(anchors); sk=set(skeleton)
    for pi,i in enumerate(sel):
        r=bank.iloc[i]
        role=("anchor" if i in anchor_set else
              "connector" if i in sk else "one_hop_expansion")
        rows.append({
            "panel_index":pi,
            "source_bank_row":i,
            "source_id":r.source_id,
            "pmfs_i":int(r.pmfs_i),"pmfs_j":int(r.pmfs_j),
            "x_m":float(r.x_m),"y_m":float(r.y_m),"z_m":float(r.z_m),
            "selection_role":role,
            "graph_distance_from_center":int(dcenter[i]),
            "selected_degree_4n":sum(v in selected for v in adj[i]),
        })
    return pd.DataFrame(rows),{
        "center_source_bank_row":center,
        "center_source_id":str(bank.iloc[center].source_id),
        "anchor_source_bank_rows":anchors,
        "anchor_source_ids":[str(bank.iloc[i].source_id) for i in anchors],
        "skeleton_cells":len(skeleton),
        "panel_cells":len(selected),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-bank",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    bank=pd.read_csv(a.source_bank,sep="\t")
    out,meta=select(bank)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    text=out.to_csv(sep="\t",index=False,float_format="%.12f")
    a.out.write_text(text)
    print(meta)
    print("panel_sha256",hashlib.sha256(text.encode()).hexdigest())

if __name__=="__main__":
    main()
