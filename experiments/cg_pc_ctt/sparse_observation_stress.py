#!/usr/bin/env python3
"""Sparse-observation stress test for the V3 observation quotient.

Diagnostic only. It never fits thresholds. For each fixed query-support size Q,
it samples deterministic feature subsets, evaluates the observation quotient,
and reports physical source resolution. The purpose is to expose whether the
current robot support carries enough local source information.
"""
from __future__ import annotations
import argparse,csv,json
from itertools import product
from pathlib import Path
import numpy as np
from observation_quotient_gate import evaluate_context

DEFAULT_Q=(1,2,4,8,16,32,64,128,256)
SEED=20260827


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('npz',type=Path); ap.add_argument('--repeats',type=int,default=5)
    ap.add_argument('--q',default=','.join(map(str,DEFAULT_Q)))
    ap.add_argument('--out-csv',type=Path,required=True); ap.add_argument('--out-json',type=Path,required=True)
    a=ap.parse_args()
    d=np.load(a.npz,allow_pickle=True); phi=np.asarray(d['phi'],float); xy=np.asarray(d['candidate_xy'],float)
    if phi.ndim==3: phi=phi[None]
    N,S,M,D=phi.shape
    if xy.shape!=(S,2): raise ValueError('candidate_xy mismatch')
    qvals=[int(x) for x in a.q.split(',') if int(x)>0]
    qvals=[q for q in qvals if q<=D]
    if D not in qvals: qvals.append(D)
    patterns=np.asarray([(1.0,)+tail for tail in product((-1.0,1.0),repeat=M-1)],float)
    rows=[]
    for q in qvals:
        reps=1 if q==D else a.repeats
        for rep in range(reps):
            rng=np.random.default_rng(SEED + q*1009 + rep*9176)
            idx=np.arange(D) if q==D else np.sort(rng.choice(D,size=q,replace=False))
            for n in range(N):
                s,_,_=evaluate_context(phi[n][:,:,idx],xy,patterns)
                rows.append({'q':q,'repeat':rep,'context_index':n,
                             'resolution_fraction':s['resolution_fraction'],
                             'resolved_edge_fraction':s['resolved_edge_fraction'],
                             'component_count':s['component_count'],
                             'physical_source_count':s['physical_source_count'],
                             'max_component_size':s['max_component_size'],
                             'max_component_diameter':s['max_component_diameter']})
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    summary={}
    for q in qvals:
        rr=[r for r in rows if r['q']==q]
        summary[str(q)]={
            'n_context_repeat':len(rr),
            'resolution_fraction_mean':float(np.mean([r['resolution_fraction'] for r in rr])),
            'resolution_fraction_q10_q90':[float(x) for x in np.quantile([r['resolution_fraction'] for r in rr],[.1,.9])],
            'resolved_edge_fraction_mean':float(np.mean([r['resolved_edge_fraction'] for r in rr])),
            'max_component_size_median':float(np.median([r['max_component_size'] for r in rr])),
            'max_component_diameter_median':float(np.median([r['max_component_diameter'] for r in rr]))}
    out={'contract':'CG_PC_CTT_SPARSE_OBSERVATION_STRESS_V1','diagnostic_only':True,
         'seed':SEED,'repeats':a.repeats,'feature_dim_full':D,'summary':summary,
         'binding_note':'No result from this diagnostic may be used to retune frozen Gate V2 or choose an H02-specific observation threshold.'}
    a.out_json.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))

if __name__=='__main__': main()
