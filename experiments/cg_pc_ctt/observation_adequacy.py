#!/usr/bin/env python3
"""CLI for CG-PC-CTT V3 observation-adequacy diagnostics.

Input NPZ:
  prediction[N,S,M,E] or prediction[S,M,E]
  observed[N,E] or observed[E]
Optional:
  candidate_xy[S,2]
  context_id[N]

Alternative key `phi` is accepted for prediction.

No binary adequacy threshold is defined here.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from v3_adequacy import family_predictive_adequacy


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('npz',type=Path)
    ap.add_argument('--out-csv',type=Path,required=True)
    ap.add_argument('--out-json',type=Path,required=True)
    a=ap.parse_args()

    d=np.load(a.npz,allow_pickle=True)
    key='prediction' if 'prediction' in d.files else ('phi' if 'phi' in d.files else None)
    if key is None or 'observed' not in d.files:
        raise ValueError('NPZ requires prediction (or phi) and observed')
    P=np.asarray(d[key],dtype=np.float64)
    y=np.asarray(d['observed'],dtype=np.float64)
    if P.ndim==3: P=P[None]
    if y.ndim==1: y=y[None]
    if P.ndim!=4 or y.ndim!=2 or P.shape[0]!=y.shape[0] or P.shape[3]!=y.shape[1]:
        raise ValueError(f'shape mismatch prediction={P.shape} observed={y.shape}')
    N,S,M,E=P.shape
    xy=np.asarray(d['candidate_xy'],float) if 'candidate_xy' in d.files else None
    if xy is not None and xy.shape!=(S,2): raise ValueError('candidate_xy mismatch')
    cid=np.asarray(d['context_id']).astype(str) if 'context_id' in d.files else np.asarray([f'context_{i:04d}' for i in range(N)])

    rows=[]; summaries=[]
    for n in range(N):
        rr,s=family_predictive_adequacy(P[n],y[n])
        s['context_index']=n; s['context_id']=str(cid[n])
        summaries.append(s)
        for j,r in enumerate(rr):
            row={'context_index':n,'context_id':str(cid[n]),'candidate_idx':j,**r}
            if xy is not None:
                row['source_x']=float(xy[j,0]); row['source_y']=float(xy[j,1])
            rows.append(row)

    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    out={
        'contract':'CG_PC_CTT_V3_OBSERVATION_ADEQUACY_DIAGNOSTIC_V1',
        'diagnostic_only':True,
        'binary_gate_frozen':False,
        'shape':[N,S,M,E],
        'contexts':summaries,
        'binding_note':('Replicated source structure and observation adequacy are separate premises. '
                        'These scale-free scores require development calibration before any binary release threshold is claimed.')
    }
    a.out_json.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
