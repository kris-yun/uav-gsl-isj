#!/usr/bin/env python3
"""Descriptive paired ablation aggregator for a frozen PF-DEI full method.

Run only after the full development method is frozen. This script never selects
or retunes the method. Positive deltas mean removing one module made localization
worse on the same House/seed.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from math import comb

FULL="pfdei_full"
ABLATIONS=("pfdei_ablate_sensor","pfdei_ablate_temporal","pfdei_ablate_coherence","pfdei_ablate_nuisance")

def sign_p(k,n):
    return sum(comb(n,i) for i in range(k,n+1))/float(2**n) if n else 1.0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    rows=[]
    for p in sorted(a.root.rglob('case_result.json')):
        d=json.loads(p.read_text()); d['_path']=str(p); rows.append(d)
    keyed={}; errors=[]
    for r in rows:
        try:key=(str(r['house']),int(r['seed']),str(r['arm']))
        except Exception: errors.append(f"BAD_SCHEMA:{r.get('_path')}"); continue
        if key in keyed: errors.append(f"DUPLICATE:{key}")
        keyed[key]=r
    result={}; keys=sorted({(h,s) for h,s,arm in keyed if arm==FULL})
    for ab in ABLATIONS:
        pairs=[]
        for h,s in keys:
            f=keyed.get((h,s,FULL)); b=keyed.get((h,s,ab))
            if not f or not b or not bool(f.get('valid')) or not bool(b.get('valid')): continue
            ef=float(f['primary_error_m']); eb=float(b['primary_error_m'])
            if not (math.isfinite(ef) and math.isfinite(eb)): continue
            pairs.append({'house':h,'seed':s,'full':ef,'ablation':eb,'delta_m':eb-ef,'module_helped':ef<eb})
        n=len(pairs); k=sum(p['module_helped'] for p in pairs); full_sum=sum(p['full'] for p in pairs); ab_sum=sum(p['ablation'] for p in pairs)
        result[ab]={'pairs':n,'full_better_pairs':k,'one_sided_sign_p':sign_p(k,n),
                    'pooled_error_increase_when_removed':None if not n else (ab_sum-full_sum)/max(full_sum,1e-12),
                    'mean_delta_m':None if not n else sum(p['delta_m'] for p in pairs)/n,
                    'per_house':{h:{'n':sum(1 for p in pairs if p['house']==h),
                                    'mean_delta_m':(sum(p['delta_m'] for p in pairs if p['house']==h)/sum(1 for p in pairs if p['house']==h)) if any(p['house']==h for p in pairs) else None}
                                 for h in sorted({p['house'] for p in pairs})}}
    out={'contract':'PF_DEI_MODULAR_ABLATION_V1','full_arm':FULL,'ablations':result,'errors':errors,
         'interpretation':'descriptive paired module-removal analysis; never use this output to retune full method'}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
