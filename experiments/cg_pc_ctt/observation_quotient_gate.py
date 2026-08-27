#!/usr/bin/env python3
"""Observation-conditioned physical-source quotient prototype for CG-PC-CTT V3.

Frozen Gate V2 is unchanged. This script asks a different question:
which local physical source alternatives are replicably separable on the
observation support actually available now?

Input NPZ:
  phi[N,S,M,D] or phi[S,M,D]
  candidate_xy[S,2]
Optional --feature-index selects the causal observation support H_e.

All core mathematics comes from `v3_math.py`.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np

from v3_math import coordinate_quotient, nuisance_metric, delaunay_neighbors, pair_cross_stat


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
        if not r['resolved_proto']: union(i,j)
    g={}
    for i in range(n): g.setdefault(find(i),[]).append(i)
    return list(g.values())


def component_diameter(xy,inds):
    if len(inds)<2:return 0.0
    a=xy[np.asarray(inds,int)]; d2=((a[:,None]-a[None,:])**2).sum(2)
    return float(np.sqrt(d2.max()))


def evaluate_context(x,xy):
    qx,qxy,groups,drift=coordinate_quotient(x,xy)
    metric=nuisance_metric(qx)
    _,edges=delaunay_neighbors(qxy)
    edge_rows=[pair_cross_stat(qx,i,j,metric,exact_signflip=True) for i,j in edges]
    comps=unresolved_components(len(qxy),edges,edge_rows)
    sizes=np.asarray([len(c) for c in comps],int)
    diam=np.asarray([component_diameter(qxy,c) for c in comps],float)
    summary={
        'physical_source_count':int(len(qxy)),
        'candidate_id_count':int(len(xy)),
        'max_alias_field_drift':float(drift),
        'geometry_edge_mode':'delaunay_unique_coordinates',
        'geometry_edges':int(len(edges)),
        'resolved_edge_fraction':float(np.mean([r['resolved_proto'] for r in edge_rows])),
        'component_count':int(len(comps)),
        'resolution_fraction':float(len(comps)/len(qxy)),
        'max_component_size':int(sizes.max()),
        'median_component_size':float(np.median(sizes)),
        'max_component_diameter':float(diam.max()),
        'nuisance_covariance_rank':metric.numerical_rank,
        'nuisance_covariance_dimension':int(metric.covariance.shape[0]),
        'nuisance_pinv_tolerance':metric.tolerance,
        'components':[list(map(int,c)) for c in comps],
        'physical_xy':qxy.tolist(),
    }
    return summary,edges,edge_rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('npz',type=Path)
    ap.add_argument('--feature-index',type=Path,default=None)
    ap.add_argument('--out-json',type=Path,required=True)
    ap.add_argument('--out-csv',type=Path,required=True)
    a=ap.parse_args()

    d=np.load(a.npz,allow_pickle=True); phi=np.asarray(d['phi'],float)
    if phi.ndim==3: phi=phi[None,...]
    if phi.ndim!=4: raise ValueError(f'phi must be [N,S,M,D], got {phi.shape}')
    xy=np.asarray(d['candidate_xy'],float); N,S,M,D=phi.shape
    if xy.shape!=(S,2): raise ValueError('candidate_xy mismatch')
    if M>16: raise ValueError('exact sign-flip prototype requires M<=16')
    fi=load_feature_index(a.feature_index,D)

    all_rows=[]; summaries=[]
    for n in range(N):
        summary,edges,er=evaluate_context(phi[n][:,:,fi],xy)
        summary['context_index']=n; summary['feature_count']=int(len(fi)); summaries.append(summary)
        qxy=np.asarray(summary['physical_xy'],float)
        for edge_id,((i,j),r) in enumerate(zip(edges,er)):
            all_rows.append({
                'context_index':n,'edge_id':edge_id,'i':i,'j':j,
                'xi':qxy[i,0],'yi':qxy[i,1],'xj':qxy[j,0],'yj':qxy[j,1],
                **r,
            })

    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='',encoding='utf-8') as f:
        ww=csv.DictWriter(f,fieldnames=list(all_rows[0].keys())); ww.writeheader(); ww.writerows(all_rows)
    out={
        'contract':'CG_PC_CTT_OBSERVATION_QUOTIENT_V2_FULL_COVARIANCE_PROTO',
        'diagnostic_only':True,
        'nuisance_metric':'full_pair_difference_covariance_moore_penrose_precision',
        'feature_count':int(len(fi)),
        'contexts':summaries,
        'binding_note':('Current physical-source resolution is defined from observation-conditioned local '
                        'replicated separability on unique coordinates. Unresolved connected components '
                        'represent currently unsupported point precision. This does not alter frozen Gate V2.'),
    }
    a.out_json.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))

if __name__=='__main__': main()
