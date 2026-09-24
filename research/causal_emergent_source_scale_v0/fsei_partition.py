#!/usr/bin/env python3
"""FSEI connected information-fidelity partition candidate.

This module contains no target-dependent logic.

Given source-by-realization binary encounter arrays and source grid geometry,
it constructs a connected hard partition using the pre-data FSEI merge rule:

    accept merge iff estimated encounter fidelity cost
    < first-order finite-sample estimation-regret reduction.

The output is a candidate partition for reference-only evaluation.
It is NOT itself a scientific confirmation test.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple
import heapq
import math
import numpy as np
import pandas as pd

EPS = 1e-12


def bernoulli_kl(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Elementwise KL(Bern(p)||Bern(q)) in nats."""
    p=np.clip(np.asarray(p,float),EPS,1-EPS)
    q=np.clip(np.asarray(q,float),EPS,1-EPS)
    return p*np.log(p/q)+(1-p)*np.log((1-p)/(1-q))


@dataclass
class Group:
    gid: int
    members: Set[int]
    size: int
    profile: np.ndarray
    neighbors: Set[int]
    version: int = 0


def source_profiles(binary: np.ndarray, alpha: float=0.5) -> np.ndarray:
    """Jeffreys-smoothed source encounter marginals.

    binary shape: [N, n, T, P].
    returns [N, Q=T*P].
    """
    x=np.asarray(binary,float)
    if x.ndim!=4:
        raise ValueError(f"expected [N,n,T,P], got {x.shape}")
    if not np.all((x==0)|(x==1)):
        raise ValueError("binary array must contain only 0/1")
    n=x.shape[1]
    k=x.sum(axis=1).reshape(x.shape[0],-1)
    return (k+alpha)/(n+2*alpha)


def four_neighbor_graph(panel: pd.DataFrame) -> List[Set[int]]:
    """Build four-neighbor PMFS adjacency for panel row order."""
    grid={}
    for i,r in panel.reset_index(drop=True).iterrows():
        key=(int(r.pmfs_i),int(r.pmfs_j))
        if key in grid:
            raise ValueError(f"duplicate grid cell {key}")
        grid[key]=i
    out=[set() for _ in range(len(panel))]
    for (ii,jj),i in grid.items():
        for key in ((ii+1,jj),(ii-1,jj),(ii,jj+1),(ii,jj-1)):
            j=grid.get(key)
            if j is not None:
                out[i].add(j)
    if out:
        seen={0}; stack=[0]
        while stack:
            i=stack.pop()
            for j in out[i]:
                if j not in seen:
                    seen.add(j); stack.append(j)
        if len(seen)!=len(out):
            raise ValueError("source panel is not four-neighbor connected")
    return out


def merge_fidelity_cost(a: Group, b: Group, n_sources: int) -> float:
    """Incremental full-vector marginal fidelity cost in nats/source.

    For two current macro groups A,B with source-averaged Bernoulli profiles,
    the increase in the plug-in estimate of

        sum_q I(S; H_q | M) / N

    from merging A and B is the weighted Bernoulli Jensen-Shannon cost.
    """
    na=float(a.size); nb=float(b.size)
    pc=(na*a.profile+nb*b.profile)/(na+nb)
    cost=(na*bernoulli_kl(a.profile,pc).sum()
          +nb*bernoulli_kl(b.profile,pc).sum())/float(n_sources)
    return float(cost)


def complexity_benefit(n_train: int, n_sources: int, q_dim: int) -> float:
    """First-order nats/source benefit for removing one Q-parameter macro block."""
    if n_train<=0 or n_sources<=0 or q_dim<=0:
        raise ValueError("positive n_train, n_sources, q_dim required")
    return float(q_dim/(2.0*n_train*n_sources))


def _compact_labels(groups: Dict[int,Group], n_sources: int) -> np.ndarray:
    ordered=sorted(groups.values(),key=lambda g:min(g.members))
    out=np.empty(n_sources,dtype=int)
    for k,g in enumerate(ordered):
        for s in g.members:
            out[s]=k
    return out


def fit_fsei_partition(
    binary_train: np.ndarray,
    panel: pd.DataFrame,
    alpha: float=0.5,
) -> dict:
    """Fit the parameter-free connected FSEI partition.

    binary_train: [N,n,T,P]
    panel: N rows containing pmfs_i, pmfs_j

    Stopping rule is fixed from theory:
        min connected merge fidelity cost < Q/(2*n*N)

    Returns labels plus a complete merge audit trail.
    """
    x=np.asarray(binary_train,float)
    N,n,T,P=x.shape
    if len(panel)!=N:
        raise ValueError("panel/data source count mismatch")
    Q=T*P
    prof=source_profiles(x,alpha=alpha)
    graph=four_neighbor_graph(panel)

    groups: Dict[int,Group]={}
    active=set(range(N))
    for i in range(N):
        groups[i]=Group(i,{i},1,prof[i].copy(),set(graph[i]),0)

    heap=[]
    def push(a:int,b:int):
        if a not in active or b not in active or a==b:
            return
        if b not in groups[a].neighbors:
            return
        ga,gb=groups[a],groups[b]
        ka,kb=min(ga.members),min(gb.members)
        if ka>kb:
            a,b=b,a; ga,gb=gb,ga; ka,kb=kb,ka
        c=merge_fidelity_cost(ga,gb,N)
        heapq.heappush(heap,(c,ka,kb,a,b,ga.version,gb.version))

    for i in range(N):
        for j in graph[i]:
            if i<j:
                push(i,j)

    threshold=complexity_benefit(n,N,Q)
    merges=[]
    next_gid=N

    while heap:
        cost,_,_,a,b,va,vb=heapq.heappop(heap)
        if a not in active or b not in active:
            continue
        A,B=groups[a],groups[b]
        if A.version!=va or B.version!=vb or b not in A.neighbors:
            continue
        if not cost < threshold:
            break

        members=A.members|B.members
        size=A.size+B.size
        profile=(A.size*A.profile+B.size*B.profile)/size
        neigh=(A.neighbors|B.neighbors)-{a,b}

        active.remove(a); active.remove(b)
        g=next_gid; next_gid+=1
        groups[g]=Group(g,members,size,profile,set(),0)

        valid=[]
        for u in sorted(neigh):
            if u not in active:
                continue
            groups[u].neighbors.discard(a)
            groups[u].neighbors.discard(b)
            groups[u].neighbors.add(g)
            groups[u].version+=1
            valid.append(u)
        groups[g].neighbors=set(valid)
        active.add(g)

        merges.append({
            "after_K":len(active),
            "merge_cost_nats_per_source":float(cost),
            "complexity_benefit_nats_per_source":float(threshold),
            "size_a":A.size,
            "size_b":B.size,
            "size_new":size,
            "min_source_row":min(members),
        })
        for u in valid:
            push(g,u)

    final={g:groups[g] for g in active}
    labels=_compact_labels(final,N)
    sizes=np.bincount(labels)

    return {
        "labels":labels,
        "K":int(len(sizes)),
        "sizes":sizes,
        "threshold_nats_per_source":float(threshold),
        "n_train":int(n),
        "Q":int(Q),
        "N":int(N),
        "alpha":float(alpha),
        "merges":merges,
        "stopped_because":"next_merge_cost_ge_theory_benefit" if heap else "no_edges",
    }


def honest_micro_lift(
    macro_posterior: np.ndarray,
    labels: np.ndarray,
    micro_prior: np.ndarray | None=None,
) -> np.ndarray:
    """Lift macro posterior back to the original micro support without spikes."""
    labels=np.asarray(labels,int)
    q=np.asarray(macro_posterior,float)
    N=len(labels); K=int(labels.max()+1)
    if q.shape[-1]!=K:
        raise ValueError("macro posterior K mismatch")
    if micro_prior is None:
        pi=np.full(N,1.0/N)
    else:
        pi=np.asarray(micro_prior,float)
        if pi.shape!=(N,) or np.any(pi<0) or not np.isclose(pi.sum(),1):
            raise ValueError("invalid micro prior")
    mass=np.array([pi[labels==k].sum() for k in range(K)])
    if np.any(mass<=0):
        raise ValueError("empty/zero-prior macro")
    out=np.empty(q.shape[:-1]+(N,),float)
    for s in range(N):
        out[...,s]=q[...,labels[s]]*pi[s]/mass[labels[s]]
    if not np.allclose(out.sum(axis=-1),1.0,rtol=1e-9,atol=1e-12):
        raise RuntimeError("lift does not conserve probability")
    return out


def partition_geometry(labels: np.ndarray, panel: pd.DataFrame) -> pd.DataFrame:
    """Diagnostic size/area/diameter table for an equal-area 0.30m PMFS panel."""
    labels=np.asarray(labels,int)
    rows=[]
    for k in np.unique(labels):
        idx=np.where(labels==k)[0]
        xy=panel.iloc[idx][["x_m","y_m"]].to_numpy(float)
        if len(xy)==1:
            diam=0.0
        else:
            d=xy[:,None,:]-xy[None,:,:]
            diam=float(np.sqrt((d*d).sum(axis=2)).max())
        rows.append({
            "macro":int(k),
            "cells":int(len(idx)),
            "area_m2":float(len(idx)*0.09),
            "diameter_m":diam,
        })
    return pd.DataFrame(rows)
