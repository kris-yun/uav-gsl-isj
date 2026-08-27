#!/usr/bin/env python3
"""Full-covariance local physical source-pair audit for CG-PC-CTT V3.

This is the V3 counterpart of the historical `local_pair_audit.py`.
It uses the shared `v3_math.py` nuisance covariance and physical-coordinate
quotient. It is diagnostic-only and does not retune frozen Gate V2.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from v3_math import coordinate_quotient, nuisance_metric, delaunay_neighbors, pair_cross_stat


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('npz',type=Path)
    ap.add_argument('--out-csv',type=Path,required=True); ap.add_argument('--out-json',type=Path,required=True)
    a=ap.parse_args()
    d=np.load(a.npz,allow_pickle=True); phi=np.asarray(d['phi'],float)
    if phi.ndim==3: phi=phi[None]
    if phi.ndim!=4: raise ValueError(f'phi must be [N,S,M,D] or [S,M,D], got {phi.shape}')
    xy=np.asarray(d['candidate_xy'],float); N,S,M,D=phi.shape
    if xy.shape!=(S,2): raise ValueError('candidate_xy mismatch')
    rows=[]; summaries=[]
    for n in range(N):
        qphi,qxy,groups,drift=coordinate_quotient(phi[n],xy)
        metric=nuisance_metric(qphi); _,edges=delaunay_neighbors(qxy)
        er=[]
        for edge_id,(i,j) in enumerate(edges):
            r=pair_cross_stat(qphi,i,j,metric,exact_signflip=True)
            dist=float(np.linalg.norm(qxy[i]-qxy[j]))
            row={'context_index':n,'edge_id':edge_id,'i':i,'j':j,'distance':dist,
                 'xi':float(qxy[i,0]),'yi':float(qxy[i,1]),'xj':float(qxy[j,0]),'yj':float(qxy[j,1]),**r}
            rows.append(row); er.append(row)
        p=np.asarray([r['pair_p_signflip'] for r in er],float)
        aalpha=np.asarray([r['pair_alpha_cf'] for r in er],float)
        summaries.append({
            'context_index':n,'candidate_id_count':S,'physical_source_count':len(qxy),
            'duplicate_id_count':int(S-len(qxy)),'max_alias_field_drift':float(drift),
            'delaunay_edges':len(edges),'resolved_offline_proto_fraction':float(np.mean([r['resolved_proto'] for r in er])),
            'pair_p_le_0p01_fraction':float(np.mean(p<=0.01)),
            'pair_p_gt_0p05_fraction':float(np.mean(p>0.05)),
            'pair_alpha_median':float(np.median(aalpha)),
            'nuisance_rank':metric.numerical_rank,'nuisance_dimension':int(metric.covariance.shape[0]),
        })
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    out={'contract':'CG_PC_CTT_V3_LOCAL_PAIR_AUDIT_FULL_COVARIANCE','diagnostic_only':True,
         'online_signflip_authorized':False,'contexts':summaries,
         'binding_note':'Exact sign-flip p-values are offline diagnostics only; repeated online use requires an anytime-valid sequential contract.'}
    a.out_json.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))

if __name__=='__main__': main()
