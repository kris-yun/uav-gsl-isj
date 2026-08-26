#!/usr/bin/env python3
"""Observation-conditioned physical-source quotient prototype for CG-PC-CTT V3.

Research diagnostic only. Frozen Gate V2 is unchanged.

Input NPZ:
  phi[N,S,M,D] or phi[S,M,D]
  candidate_xy[S,2]
Optional --feature-index selects the causal observation support H_e.

The statistic never treats candidate IDs at identical coordinates as different
physical sources. It builds a local geometry graph on unique coordinates and
marks an edge resolved only when source-pair separation is replicated across
transport members on the actually selected observation support.
"""
from __future__ import annotations
import argparse,csv,json
from itertools import product,combinations
from pathlib import Path
import numpy as np
from scipy.spatial import Delaunay

P_MAX=0.01
RIDGE_REL=1e-3
EPS=1e-9


def load_feature_index(path: Path|None,D:int):
    if path is None: return np.arange(D,dtype=int)
    if path.suffix=='.npy': a=np.load(path)
    elif path.suffix=='.npz':
        d=np.load(path); key='feature_index' if 'feature_index' in d.files else d.files[0]; a=d[key]
    else: a=np.loadtxt(path,dtype=int,ndmin=1)
    a=np.asarray(a,dtype=int).reshape(-1)
    if a.size<1 or np.any(a<0) or np.any(a>=D) or len(np.unique(a))!=len(a):
        raise ValueError('invalid feature index')
    return np.sort(a)


def coordinate_quotient(x,xy,decimals=7):
    groups={}
    for i,(a,b) in enumerate(xy):
        key=(round(float(a),decimals),round(float(b),decimals))
        groups.setdefault(key,[]).append(i)
    keys=list(groups)
    qxy=np.asarray(keys,float)
    qx=np.stack([x[np.asarray(groups[k],int)].mean(axis=0) for k in keys])
    drift=0.0
    for inds in groups.values():
        if len(inds)>1:
            ref=x[inds[0]]
            for j in inds[1:]: drift=max(drift,float(np.max(np.abs(ref-x[j]))))
    return qx,qxy,groups,drift


def noise_whitener(x):
    S,M,D=x.shape; ss=np.zeros(D,float); n=0
    for m in range(M):
        for h in range(m+1,M):
            d=x[:,m]-x[:,h]
            ss += np.sum(0.5*d*d,axis=0); n += S
    v=ss/max(n,1)
    ridge=max(EPS,RIDGE_REL*max(float(v.mean()),EPS))
    return 1.0/np.sqrt(v+ridge),ridge


def geometry_edges(xy):
    if len(xy)<3: raise ValueError('need >=3 physical source coordinates')
    tri=Delaunay(xy)
    e=set()
    for simplex in tri.simplices:
        for i,j in combinations(map(int,simplex),2): e.add((min(i,j),max(i,j)))
    return sorted(e)


def pair_stat(x,w,i,j,patterns):
    M=x.shape[1]
    d=(x[i]-x[j])*w[None,:]
    selfsum=float(np.sum(d*d)); totals=patterns@d
    q=(np.sum(totals*totals,axis=1)-selfsum)/float(M*(M-1))
    obs=float(q[-1]); p=float(np.mean(q>=obs-1e-12))
    loo=[]
    for r in range(M):
        dd=np.delete(d,r,axis=0); mm=M-1
        tot=dd.sum(axis=0); ss=float(np.sum(dd*dd))
        loo.append((float(tot@tot)-ss)/float(mm*(mm-1)))
    loo_min=float(min(loo))
    return {'pair_cross_strength':obs,
            'pair_alpha_cf':float(np.sqrt(max(obs,0.0))),
            'pair_p_signflip':p,
            'loo_min_cross_strength':loo_min,
            'resolved':bool(obs>0 and p<=P_MAX and loo_min>0)}


def unresolved_components(n,edges,edge_rows):
    parent=list(range(n))
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]; a=parent[a]
        return a
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    for (i,j),r in zip(edges,edge_rows):
        if not r['resolved']: union(i,j)
    g={}
    for i in range(n): g.setdefault(find(i),[]).append(i)
    return list(g.values())


def component_diameter(xy,inds):
    if len(inds)<2:return 0.0
    a=xy[np.asarray(inds,int)]; d2=((a[:,None]-a[None,:])**2).sum(2)
    return float(np.sqrt(d2.max()))


def evaluate_context(x,xy,patterns):
    qx,qxy,groups,drift=coordinate_quotient(x,xy)
    w,ridge=noise_whitener(qx); edges=geometry_edges(qxy)
    edge_rows=[pair_stat(qx,w,i,j,patterns) for i,j in edges]
    comps=unresolved_components(len(qxy),edges,edge_rows)
    sizes=np.asarray([len(c) for c in comps],int)
    diam=np.asarray([component_diameter(qxy,c) for c in comps],float)
    summary={'physical_source_count':int(len(qxy)),
             'candidate_id_count':int(len(xy)),
             'max_alias_field_drift':float(drift),
             'geometry_edge_mode':'delaunay_unique_coordinates',
             'geometry_edges':int(len(edges)),
             'resolved_edge_fraction':float(np.mean([r['resolved'] for r in edge_rows])),
             'component_count':int(len(comps)),
             'resolution_fraction':float(len(comps)/len(qxy)),
             'max_component_size':int(sizes.max()),
             'median_component_size':float(np.median(sizes)),
             'max_component_diameter':float(diam.max()),
             'ridge':float(ridge),
             'components':[list(map(int,c)) for c in comps],
             'physical_xy':qxy.tolist()}
    return summary,edges,edge_rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('npz',type=Path); ap.add_argument('--feature-index',type=Path,default=None)
    ap.add_argument('--out-json',type=Path,required=True); ap.add_argument('--out-csv',type=Path,required=True)
    a=ap.parse_args()
    d=np.load(a.npz,allow_pickle=True); phi=np.asarray(d['phi'],float)
    if phi.ndim==3: phi=phi[None]
    if phi.ndim!=4: raise ValueError(f'phi must be [N,S,M,D], got {phi.shape}')
    xy=np.asarray(d['candidate_xy'],float); N,S,M,D=phi.shape
    if xy.shape!=(S,2): raise ValueError('candidate_xy mismatch')
    if M>16: raise ValueError('exact sign-flip prototype requires M<=16')
    fi=load_feature_index(a.feature_index,D)
    pats=np.asarray([(1.0,)+tail for tail in product((-1.0,1.0),repeat=M-1)],float)
    all_rows=[]; summaries=[]
    for n in range(N):
        summary,edges,er=evaluate_context(phi[n][:,:,fi],xy,pats)
        summary['context_index']=n; summary['feature_count']=int(len(fi)); summaries.append(summary)
        qxy=np.asarray(summary['physical_xy'],float)
        for edge_id,((i,j),r) in enumerate(zip(edges,er)):
            all_rows.append({'context_index':n,'edge_id':edge_id,'i':i,'j':j,
                'xi':qxy[i,0],'yi':qxy[i,1],'xj':qxy[j,0],'yj':qxy[j,1],**r})
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='') as f:
        ww=csv.DictWriter(f,fieldnames=list(all_rows[0].keys())); ww.writeheader(); ww.writerows(all_rows)
    out={'contract':'CG_PC_CTT_OBSERVATION_QUOTIENT_GATE_V3_PROTO',
         'diagnostic_only':True,'p_max':P_MAX,'ridge_rel':RIDGE_REL,
         'feature_count':int(len(fi)),'contexts':summaries,
         'binding_note':('Current physical-source resolution is defined from observation-conditioned local '
                         'replicated separability. This does not alter frozen Gate V2.')}
    a.out_json.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))

if __name__=='__main__': main()
