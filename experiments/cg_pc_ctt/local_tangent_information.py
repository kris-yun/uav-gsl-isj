#!/usr/bin/env python3
"""Observation-conditioned 2-D local source-information diagnostic for CG-PC-CTT V3.

The physical source parameter is (x,y), so local source identifiability is a
2-D inverse-problem property. This script delegates all mathematics to
`v3_math.py` and does not alter frozen Gate V2.

Input NPZ:
  phi[N,S,M,D] or phi[S,M,D]
  candidate_xy[S,2]
Optional --feature-index selects only causally available observation support.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np

from v3_math import coordinate_quotient, nuisance_metric, delaunay_neighbors, tangent_information_for_source


def load_feature_index(path: Path|None, D: int):
    if path is None:
        return np.arange(D,dtype=int)
    if path.suffix=='.npy':
        a=np.load(path)
    elif path.suffix=='.npz':
        z=np.load(path)
        key='feature_index' if 'feature_index' in z.files else z.files[0]
        a=z[key]
    else:
        a=np.loadtxt(path,dtype=int,ndmin=1)
    a=np.asarray(a,dtype=int).reshape(-1)
    if a.size<1 or np.any(a<0) or np.any(a>=D) or len(np.unique(a))!=len(a):
        raise ValueError('invalid feature index')
    return np.sort(a)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('npz',type=Path)
    ap.add_argument('--feature-index',type=Path,default=None)
    ap.add_argument('--out-csv',type=Path,required=True)
    ap.add_argument('--out-json',type=Path,required=True)
    a=ap.parse_args()

    d=np.load(a.npz,allow_pickle=True)
    phi=np.asarray(d['phi'],dtype=np.float64)
    if phi.ndim==3: phi=phi[None,...]
    if phi.ndim!=4: raise ValueError(f'phi must be [N,S,M,D] or [S,M,D], got {phi.shape}')
    xy=np.asarray(d['candidate_xy'],dtype=np.float64)
    N,S,M,D=phi.shape
    if xy.shape!=(S,2): raise ValueError(f'candidate_xy must be [{S},2], got {xy.shape}')
    fi=load_feature_index(a.feature_index,D)

    all_rows=[]; summaries=[]
    for n in range(N):
        qphi,qxy,groups,alias_drift=coordinate_quotient(phi[n][:,:,fi],xy)
        metric=nuisance_metric(qphi)
        neighbours,_=delaunay_neighbors(qxy)
        rows=[]
        for i,nb in enumerate(neighbours):
            r=tangent_information_for_source(qphi,qxy,i,nb,metric)
            row={
                'context_index':n,
                'physical_source_idx':i,
                'x':float(qxy[i,0]),
                'y':float(qxy[i,1]),
                'lambda_max':r['lambda_max'],
                'lambda_min':r['lambda_min'],
                'gamma_xy':r['gamma_xy'],
                'neighbor_count':int(len(nb)),
                'geometry_rank':r['geometry_rank'],
                'geometry_condition':r['geometry_condition'],
                'nuisance_numerical_rank':metric.numerical_rank,
            }
            rows.append(row); all_rows.append(row)
        lam=np.asarray([r['lambda_min'] for r in rows],float)
        gam=np.asarray([r['gamma_xy'] for r in rows],float)
        cond=np.asarray([r['geometry_condition'] for r in rows],float)
        summaries.append({
            'context_index':n,
            'feature_count':int(len(fi)),
            'candidate_id_count':S,
            'physical_source_count':len(qxy),
            'max_alias_field_drift':float(alias_drift),
            'lambda_min_positive_fraction':float(np.mean(lam>0)),
            'gamma_xy_median':float(np.median(gam)),
            'gamma_xy_q05_q95':[float(x) for x in np.quantile(gam,[.05,.95])],
            'geometry_condition_median':float(np.median(cond[np.isfinite(cond)])) if np.any(np.isfinite(cond)) else None,
            'geometry_condition_max':float(np.max(cond[np.isfinite(cond)])) if np.any(np.isfinite(cond)) else None,
            'nuisance_covariance_rank':metric.numerical_rank,
            'nuisance_covariance_dimension':int(metric.covariance.shape[0]),
            'nuisance_pinv_tolerance':metric.tolerance,
        })

    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(all_rows[0].keys())); w.writeheader(); w.writerows(all_rows)
    out={
        'contract':'CG_PC_CTT_LOCAL_TANGENT_INFORMATION_V2_FULL_COVARIANCE',
        'diagnostic_only':True,
        'source_dimension':2,
        'nuisance_metric':'full_pair_difference_covariance_moore_penrose_precision',
        'feature_index_count':int(len(fi)),
        'contexts':summaries,
        'binding_note':('V3 local source information is computed only on the selected observation support. '
                        'The full-covariance pseudoinverse prevents exact duplicated feature encodings from '
                        'creating artificial information. No threshold here retunes frozen Gate V2.'),
    }
    a.out_json.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
