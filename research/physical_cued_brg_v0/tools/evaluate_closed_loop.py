#!/usr/bin/env python3
"""Paired closed-loop scoring; no privileged information enters the network.
Input one JSON record per planned case/arm; runner failures remain failures.
Predeclare radius and budget in protocol, not by inspecting this summary.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np

def evaluate(records,arms,radius,baseline,replicates=10000,seed=2026092703):
    table={}
    for r in records:
        k=(r['case_id'],r['arm'])
        if k in table:raise ValueError('duplicate result')
        table[k]=r
    cases=sorted(set(k[0] for k in table))
    if any((c,a) not in table for c in cases for a in arms):raise ValueError('missing planned arm; do not score partial campaign')
    vals={};sources=[]
    for c in cases:
        base=table[c,baseline];sources.append(base['candidate_support_id']+'::'+base['source_id'])
        for a in arms:
            r=table[c,a]
            for k in ['source_id','plume_id','budget_s','initial_pose_id','observation_contract_id','candidate_support_id']:
                if r[k]!=base[k]:raise ValueError(f'unpaired context {k}')
    for a in arms:
        rows=[table[c,a] for c in cases];success=[];error=[]
        for r in rows:
            ok=r['status'] in {'completed','time_budget'}
            estimate=r.get('estimate_xy');truth=r['truth_xy']
            truth=np.asarray(truth,dtype=float)
            if truth.shape!=(2,) or not np.isfinite(truth).all():raise ValueError('invalid evaluator truth coordinates')
            if estimate is not None:
                estimate=np.asarray(estimate,dtype=float)
                if estimate.shape!=(2,) or not np.isfinite(estimate).all():raise ValueError('nonfinite estimate must be recorded as explicit failure, not hidden')
            err=float(np.linalg.norm(estimate-truth)) if ok and estimate is not None else float('inf')
            success.append(float(err<=radius));error.append(err)
        vals[a]=dict(success=np.array(success),errors=np.array(error))
    rng=np.random.default_rng(seed);groups=sorted(set(sources));idx={s:np.flatnonzero(np.array(sources)==s) for s in groups};out={}
    for a in arms:
        d=vals[a]['success']-vals[baseline]['success'];boots=[]
        # Fixed tested-source panel: source-weighted mean, within-source plume resampling.
        # Assumes one case per independent plume; multiple starts must be grouped
        # upstream as a single source/plume case before calling this evaluator.
        for _ in range(replicates):
            boots.append(np.mean([np.mean(d[rng.choice(i,len(i),replace=True)]) for i in idx.values()]))
        out[a]={'success_rate':float(np.mean([vals[a]['success'][i].mean() for i in idx.values()])),
                'paired_delta':float(np.mean([d[i].mean() for i in idx.values()])),
                'ci95_fixed_source_panel':np.quantile(boots,[.025,.975]).tolist(),
                'finite_mean_error_m':float(np.mean(vals[a]['errors'][np.isfinite(vals[a]['errors'])])) if np.isfinite(vals[a]['errors']).any() else None,
                'failures_no_estimate':int(np.isinf(vals[a]['errors']).sum()),'source_count':len(groups),'case_count':len(cases)}
    return {'comparison':out,'radius_m':radius,'new_scientific_decision':None,'interpretation':'success is geometric final-estimate accuracy under fixed budget; no claim from rank or posterior peak alone'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--jsonl',required=True);p.add_argument('--arms',nargs='+',required=True);p.add_argument('--radius-m',type=float,required=True);p.add_argument('--baseline',default='native_pmfs');p.add_argument('--out',required=True);a=p.parse_args()
 rows=[json.loads(s) for s in Path(a.jsonl).read_text().splitlines() if s.strip()]
 # Refuse ambiguous nesting; otherwise same source/plume would be pseudoreplicated.
 pairs=[(r['arm'],r['source_id'],r['plume_id']) for r in rows]
 if len(pairs)!=len(set(pairs)):raise ValueError('combine correlated starts per plume before evaluation')
 result=evaluate(rows,a.arms,a.radius_m,a.baseline);Path(a.out).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
