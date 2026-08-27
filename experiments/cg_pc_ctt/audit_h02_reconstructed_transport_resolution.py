#!/usr/bin/env python3
"""Truth-free batch audit of reconstructed H02 CTT transport-side local resolution.
This is model-side diagnostics only, not current-observation evidence and not a release gate.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
from v3_math import coordinate_quotient,nuisance_metric,delaunay_neighbors,tangent_information_for_source,pair_cross_stat

TIMESTEPS=200.0

def one(path:Path):
    d=np.load(path,allow_pickle=False)
    first=np.asarray(d['first_hit'],dtype=np.float64)
    xy=np.asarray(d['candidate_xy'],dtype=np.float64)
    phi=first/TIMESTEPS
    qphi,qxy,groups,drift=coordinate_quotient(phi,xy)
    metric=nuisance_metric(qphi)
    nb,edges=delaunay_neighbors(qxy)
    tang=[tangent_information_for_source(qphi,qxy,i,jj,metric) for i,jj in enumerate(nb)]
    lmin=np.asarray([r['lambda_min'] for r in tang]);gamma=np.asarray([r['gamma_xy'] for r in tang]);cond=np.asarray([r['geometry_condition'] for r in tang])
    pair=np.asarray([pair_cross_stat(qphi,i,j,metric,exact_signflip=False)['pair_cross_strength'] for i,j in edges])
    return {'case_id':str(np.asarray(d['case_id']).item()),'cluster_id':str(np.asarray(d['cluster_id']).item()),
      'source_count':int(len(qxy)),'feature_count':int(qphi.shape[2]),'member_count':int(qphi.shape[1]),
      'coordinate_alias_max_field_drift':float(drift),'nuisance_rank':int(metric.numerical_rank),
      'lambda_min_positive_fraction':float(np.mean(lmin>0)),'gamma_xy_median':float(np.median(gamma)),'gamma_xy_q05':float(np.quantile(gamma,.05)),
      'geometry_condition_median':float(np.median(cond[np.isfinite(cond)])) if np.isfinite(cond).any() else math.inf,
      'geometry_condition_max':float(np.max(cond[np.isfinite(cond)])) if np.isfinite(cond).any() else math.inf,
      'delaunay_edges':int(len(edges)),'pair_cross_positive_fraction':float(np.mean(pair>0))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tensor_dir',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    files=sorted(p for p in a.tensor_dir.glob('h02_ctx_*.npz'))
    if not files:raise SystemExit('no H02 tensor NPZ files')
    rows=[one(p) for p in files];cluster={}
    for r in rows:cluster.setdefault(r['cluster_id'],[]).append(r)
    payload={'contract':'H02_RECONSTRUCTED_TRANSPORT_RESOLUTION_AUDIT_V1','truth_used':False,'diagnostic_only':True,
      'representation':'normalized first-arrival-time field on full free-space support; NOT observation-conditioned H_e',
      'cases':len(rows),'clusters':len(cluster),'case_results':rows,
      'summary':{'lambda_min_positive_fraction_median':float(np.median([r['lambda_min_positive_fraction'] for r in rows])),
                 'gamma_xy_median_of_case_medians':float(np.median([r['gamma_xy_median'] for r in rows])),
                 'pair_cross_positive_fraction_median':float(np.median([r['pair_cross_positive_fraction'] for r in rows]))},
      'binding_note':'This audit asks whether the reconstructed forward family has local 2-D source structure. It cannot substitute for actual-observation resolution, adequacy, source margin, or closed-loop evidence.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in payload.items() if k!='case_results'},indent=2))
if __name__=='__main__':main()
