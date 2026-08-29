#!/usr/bin/env python3
"""Frozen paired OFF/FULL aggregator for PF-DEI development or confirmation."""
from __future__ import annotations
import argparse, json, math
from math import comb
from pathlib import Path
import numpy as np

BOOT=10000
BOOT_SEED=20260829

def sign_p(k:int,n:int)->float:
    return sum(comb(n,i) for i in range(k,n+1))/float(2**n) if n else 1.0

def csv_list(text:str)->list[str]:
    return [x for x in text.split(',') if x!='']

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--houses',default='House01,House02,House03')
    ap.add_argument('--seeds',default='0,1,2,3,4,5,6,7,8,9')
    ap.add_argument('--phase',choices=['development','confirmatory'],required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    houses=csv_list(a.houses); seeds=[int(s) for s in csv_list(a.seeds)]
    rows=[]
    for p in sorted(a.root.rglob('case_result.json')):
        d=json.loads(p.read_text()); d['_path']=str(p); rows.append(d)
    keyed={}; errors=[]
    for r in rows:
        try: key=(str(r['house']),int(r['seed']),str(r['arm']))
        except Exception: errors.append(f"BAD_SCHEMA:{r.get('_path')}"); continue
        if key in keyed: errors.append(f'DUPLICATE:{key}')
        keyed[key]=r
    pairs=[]
    for h in houses:
        for s in seeds:
            off=keyed.get((h,s,'off')); on=keyed.get((h,s,'on'))
            if off is None or on is None:
                errors.append(f'MISSING_PAIR:{h}:seed{s}'); continue
            if not bool(off.get('valid')) or not bool(on.get('valid')):
                errors.append(f'INVALID_PAIR:{h}:seed{s}'); continue
            eo=float(off['primary_error_m']); en=float(on['primary_error_m'])
            if not (math.isfinite(eo) and math.isfinite(en) and eo>=0 and en>=0):
                errors.append(f'BAD_ERROR:{h}:seed{s}'); continue
            pairs.append({'house':h,'seed':s,'off':eo,'on':en,'improved':en<eo,
                          'delta':eo-en,'rel':(eo-en)/max(eo,1e-12),
                          'collapse':bool(off.get('false_confident_collapse',False) or on.get('false_confident_collapse',False)),
                          'first_release_s':on.get('first_release_s')})
    expected=len(houses)*len(seeds); n=len(pairs); complete=(n==expected and not errors)
    if n:
        off=np.asarray([p['off'] for p in pairs]); on=np.asarray([p['on'] for p in pairs])
        pooled=float((off.sum()-on.sum())/max(off.sum(),1e-12)); k=sum(p['improved'] for p in pairs); sp=sign_p(k,n)
    else:
        pooled=float('nan'); k=0; sp=1.0
    per_house={}
    for h in houses:
        pp=[p for p in pairs if p['house']==h]
        if pp:
            x=np.asarray([p['off'] for p in pp]); y=np.asarray([p['on'] for p in pp])
            per_house[h]={'n':len(pp),'off_mean':float(x.mean()),'on_mean':float(y.mean()),
                          'pooled_reduction':float((x.sum()-y.sum())/max(x.sum(),1e-12)),
                          'improved_pairs':sum(p['improved'] for p in pp)}
        else: per_house[h]={'n':0}
    rng=np.random.default_rng(BOOT_SEED); boots=[]
    if n:
        off=np.asarray([p['off'] for p in pairs]); on=np.asarray([p['on'] for p in pairs])
        for _ in range(BOOT):
            idx=rng.integers(0,n,n); x=off[idx]; y=on[idx]; boots.append((x.sum()-y.sum())/max(x.sum(),1e-12))
    ci=[float(np.quantile(boots,.025)),float(np.quantile(boots,.975))] if boots else [None,None]
    target_improved=20 if expected==30 else math.ceil((2.0/3.0)*expected)
    no_house_bad=all(v.get('n')==len(seeds) and v.get('pooled_reduction',-1.0)>=-0.05 for v in per_house.values())
    no_collapse=not any(p['collapse'] for p in pairs)
    criteria={'complete_expected_pairs':complete,'pooled_reduction_ge_0p10':bool(n and pooled>=0.10),
              'improved_pairs_ge_target':bool(k>=target_improved),'paired_sign_p_le_0p05':bool(sp<=0.05),
              'no_house_degradation_gt_5pct':no_house_bad,'no_false_confident_collapse':no_collapse}
    go=all(criteria.values())
    out={'contract':'PF_DEI_PAIRED_CLOSED_LOOP_V1','phase':a.phase,'houses':houses,'seeds':seeds,
         'expected_pairs':expected,'pairs':n,'target_improved_pairs':target_improved,'improved_pairs':k,
         'sign_test_one_sided_p':sp,'pooled_reduction':None if not n else pooled,'pooled_bootstrap_95ci':ci,
         'per_house':per_house,'criteria':criteria,'errors':errors,
         'verdict':f"PF_DEI_{a.phase.upper()}_{'GO' if go else 'NO_GO'}"}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
