#!/usr/bin/env python3
"""SVD is a strong *ordinary* comparator; no neural method trained here.

Uses saved native 2D hit maps. Does NOT measure concentration or UAV accuracy.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from o24_parity import saved_runs_in_package, logistic


def rank_corr(a,b):
    def ranks(x):
        order=np.argsort(x,kind='mergesort');r=np.empty(len(x),dtype=float);r[order]=np.arange(len(x));return r
    aa=ranks(a);bb=ranks(b);aa-=aa.mean();bb-=bb.mean()
    return float((aa@bb)/(np.linalg.norm(aa)*np.linalg.norm(bb)))


def inspect_bank(run, update=1, ranks=(1,2,4,8,16,32,64)):
    cs=[c for c in run.meta if int(c['update'])==update]
    ms=[m for m in run.posterior if int(m['update'])==update]
    nx=1+max(int(m['col']) for m in ms)
    idx=np.array([int(m['row'])*nx+int(m['col']) for m in ms])
    a=np.array([float(m['hit_confidence']) for m in ms]);mask=a>0
    measured=logistic(np.array([float(m['hit_log_odds']) for m in ms]))[mask]
    aw=a[mask]
    P=np.stack([np.frombuffer(run.response_bytes,dtype='<f4',count=int(c['count']),offset=int(c['offset_bytes']))[idx[mask]] for c in cs]).astype(float)
    native=np.array([float(c['score']) for c in cs]);scores=np.prod(1-.2*aw[None,:]*np.abs(P-measured[None,:]),axis=1)
    assert np.max(np.abs(scores-native))<1e-10
    # Fit exactly the same candidate bank. These results are in-bank morphology
    # diagnostics, NOT held-out generalization/performance numbers.
    results=[]
    for mode in ['uncentered_POD','centered_POD','confidence_weighted_centered_POD']:
        mu=np.zeros((1,P.shape[1])) if mode=='uncentered_POD' else P.mean(axis=0,keepdims=True)
        scale=np.sqrt(aw) if mode=='confidence_weighted_centered_POD' else np.ones(P.shape[1])
        X=(P-mu)*scale
        u,s,vt=np.linalg.svd(X,full_matrices=False)
        for r in ranks:
            r=min(int(r),min(X.shape))
            recon=(u[:,:r]*s[:r])@vt[:r,:]/scale+mu
            # SVD doesn't preserve [0,1]; record this and clip only as a
            # deliberately disclosed ablation, not native semantics.
            clipped=((recon<0)|(recon>1)).sum()
            recon=np.clip(recon,0,1)
            approx=np.prod(1-.2*aw[None,:]*np.abs(recon-measured),axis=1)
            lerr=np.log(approx)-np.log(scores)
            rmse=float(np.sqrt(np.mean(lerr**2)))
            results.append({'role':run.role,'update':update,'method':mode,'rank':r,
              'candidate_count':len(cs),'informative_receptor_cells':int(mask.sum()),
              'logscore_rmse':rmse,'mean_absolute_relative_hit_error':float(np.mean(np.abs(recon-P))),
              'candidate_rank_spearman':rank_corr(approx,scores),
              'best_candidate_preserved':bool(np.argmax(scores)==np.argmax(approx)),
              'out_of_range_before_clip':int(clipped),
              'data_leakage_controls':'no source truth or real ppm used; fitted+tested same candidate bank; not held-out'} )
    return {'case':run.role,'update':update,'results':results,'status':'MODEL_COMPRESSION_DIAGNOSTIC_ONLY'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--zip',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();runs=saved_runs_in_package(args.zip,True)
    report=[inspect_bank(r) for r in runs if r.role in ('O24G_A2_ISO_R03','O24G_B2_R01')]
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps([{'role':t['case'],'ranks':[(x['method'],x['rank'],round(x['logscore_rmse'],3),x['best_candidate_preserved']) for x in t['results'] if x['rank'] in (1,8,32)]} for t in report],ensure_ascii=False))
