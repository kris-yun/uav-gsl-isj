#!/usr/bin/env python3
"""Freeze gamma/alpha thresholds from DEVELOPMENT data only.

Inputs:
  gate CSV: context_id,gamma,alpha
  margin CSV: context_id,margin  (one or multiple hard-negative atoms/context)

Selection rule is fixed:
  1) coverage >= min_coverage (default .20)
  2) minimize false-pass rate: PASS atoms with margin<=0
  3) maximize PASS median margin
  4) maximize coverage

Threshold candidates are empirical deciles plus zero, computed only from dev.
Outputs a full grid CSV and a frozen JSON threshold file.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd


def args():
    p=argparse.ArgumentParser()
    p.add_argument('--gate', required=True)
    p.add_argument('--margin', required=True)
    p.add_argument('--context-col', default='context_id')
    p.add_argument('--margin-col', default='margin')
    p.add_argument('--grid-output', required=True)
    p.add_argument('--frozen-output', required=True)
    p.add_argument('--min-coverage', type=float, default=0.20)
    return p.parse_args()


def candidates(x):
    q=np.linspace(0,0.9,10)
    vals=np.quantile(np.asarray(x,float),q)
    return sorted(set([0.0]+[float(v) for v in vals if np.isfinite(v)]))


def main():
    a=args()
    g=pd.read_csv(a.gate)
    m=pd.read_csv(a.margin)
    for c in [a.context_col,'gamma','alpha']:
        if c not in g: raise ValueError(f'missing {c} in gate CSV')
    for c in [a.context_col,a.margin_col]:
        if c not in m: raise ValueError(f'missing {c} in margin CSV')
    d=m.merge(g[[a.context_col,'gamma','alpha']],on=a.context_col,how='inner',validate='many_to_one')
    if len(d)==0: raise ValueError('no merged dev atoms')
    gs=candidates(d.gamma); al=candidates(d.alpha)
    rows=[]
    for gt in gs:
        for at in al:
            passed=(d.gamma>=gt)&(d.alpha>=at)
            cov=float(passed.mean())
            if passed.any():
                pm=d.loc[passed,a.margin_col].to_numpy(float)
                fpr=float(np.mean(pm<=0))
                med=float(np.median(pm)); mean=float(np.mean(pm))
            else:
                fpr=1.0; med=float('-inf'); mean=float('nan')
            fail=d.loc[~passed,a.margin_col].to_numpy(float)
            rows.append(dict(gamma_threshold=gt,alpha_threshold=at,coverage=cov,false_pass_rate=fpr,
                             pass_margin_median=med,pass_margin_mean=mean,
                             fail_margin_median=float(np.median(fail)) if len(fail) else np.nan,
                             n_pass=int(passed.sum()),n_total=int(len(d))))
    grid=pd.DataFrame(rows)
    eligible=grid[grid.coverage>=a.min_coverage].copy()
    if len(eligible)==0: raise RuntimeError('no threshold pair satisfies min coverage')
    eligible=eligible.sort_values(['false_pass_rate','pass_margin_median','coverage'],ascending=[True,False,False])
    best=eligible.iloc[0]
    frozen={
        'gamma_threshold':float(best.gamma_threshold),
        'alpha_threshold':float(best.alpha_threshold),
        'development_coverage':float(best.coverage),
        'development_false_pass_rate':float(best.false_pass_rate),
        'development_pass_margin_median':float(best.pass_margin_median),
        'development_pass_margin_mean':float(best.pass_margin_mean),
        'selection_rule':'coverage>=min; min false-pass; max pass median margin; max coverage',
        'min_coverage':a.min_coverage,
        'n_dev_atoms':int(len(d)),
        'WARNING':'FROZEN AFTER DEVELOPMENT. DO NOT CHANGE AFTER HELD-OUT/H02 RESULTS.'
    }
    Path(a.grid_output).parent.mkdir(parents=True,exist_ok=True)
    grid.to_csv(a.grid_output,index=False)
    Path(a.frozen_output).write_text(json.dumps(frozen,indent=2),encoding='utf-8')
    print(json.dumps(frozen,indent=2))

if __name__=='__main__':
    main()
