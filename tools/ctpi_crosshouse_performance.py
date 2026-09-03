#!/usr/bin/env python3
"""Confirmatory 36-run CTPI evaluator (3 Houses x 3 fresh seeds x 4 arms).

The confirmatory paired test is an exact sign-flip randomization test on the
continuous lower-is-better metric difference. With 9 paired House/seed units,
all 2^9 sign assignments are enumerated; no asymptotic distribution is used.
"""
from __future__ import annotations
import argparse,csv,itertools,json,math
from pathlib import Path
import numpy as np

GT={'H01':(-0.40,-2.90),'H02':(0.0,-1.0),'H03':(-0.45,1.90)}
ARMS=('A0','F00','F10','F11')
COMPS=(('A0','F00','M1_F00_vs_A0'),('F00','F10','M3_F10_vs_F00'),('F10','F11','M2_DOWNSTREAM_F11_vs_F10'))
TOL=1e-12

def read(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def auc(t,e): return float(np.sum(0.5*(e[1:]+e[:-1])*np.diff(t)))

def run_metrics(path,house,horizon=240.0):
    gx,gy=GT[house]; t=[]; e=[]
    for r in read(path):
        try:
            if r.get('estimate_available','true').lower() not in ('true','1'):continue
            tt=float(r['sim_time']); x=float(r['estimate_x']); y=float(r['estimate_y'])
        except Exception:continue
        if all(map(math.isfinite,(tt,x,y))) and -TOL <= tt <= horizon+TOL:
            t.append(min(max(tt,0.0),horizon)); e.append(math.hypot(x-gx,y-gy))
    if not t:raise RuntimeError(f'NO_ESTIMATE:{path}')
    order=np.argsort(t); t=np.asarray(t)[order]; e=np.asarray(e)[order]
    unique_t=[]; unique_e=[]
    for tt,ee in zip(t,e):
        if unique_t and abs(tt-unique_t[-1])<=TOL: unique_e[-1]=float(ee)
        else: unique_t.append(float(tt)); unique_e.append(float(ee))
    t=np.asarray(unique_t); e=np.asarray(unique_e)
    ta=np.concatenate([[0.],t,[horizon]]); ea=np.concatenate([[e[0]],e,[e[-1]]])
    hit=np.flatnonzero(e<=2.0)
    return {'final_error_m':float(e[-1]),'error_auc_m_s':auc(ta,ea),'time_to_2m_s':float(t[hit[0]]) if hit.size else horizon}

def pair_summary(pairs):
    improvement=np.asarray([r['left']-r['right'] for r in pairs],dtype=float)
    w=int(np.sum(improvement>TOL)); l=int(np.sum(improvement<-TOL)); ties=len(pairs)-w-l
    observed=float(np.mean(improvement)); ge=0; total=0
    for signs in itertools.product((-1.0,1.0),repeat=len(improvement)):
        statistic=float(np.mean(improvement*np.asarray(signs)))
        ge += int(statistic >= observed-TOL); total += 1
    return {'wins':w,'losses':l,'ties':ties,'mean_improvement':observed,'exact_signflip_p_one_sided':ge/total,'permutation_count':total}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run-root',type=Path,required=True); ap.add_argument('--seeds',default='3,4,5'); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); seeds=[int(x) for x in a.seeds.split(',')]
    if seeds!=[3,4,5]: raise RuntimeError('CTPI_FORMAL_SEEDS_MUST_BE_3_4_5')
    records=[]
    for h in GT:
        for s in seeds:
            for arm in ARMS:
                records.append({'house':h,'seed':s,'arm':arm,**run_metrics(a.run_root/f'{h}_seed{s}_{arm}'/'source_estimate_trace.csv',h)})
    comparisons={}; gates={}
    for left,right,label in COMPS:
        c={}; per_house={}
        for metric in ('final_error_m','error_auc_m_s','time_to_2m_s'):
            pairs=[]
            for h in GT:
                for seed in seeds:
                    lv=next(r for r in records if r['house']==h and r['seed']==seed and r['arm']==left)[metric]
                    rv=next(r for r in records if r['house']==h and r['seed']==seed and r['arm']==right)[metric]
                    pairs.append({'house':h,'seed':seed,'left':lv,'right':rv})
            c[metric]={'left_mean':float(np.mean([r['left'] for r in pairs])),'right_mean':float(np.mean([r['right'] for r in pairs])),'paired':pair_summary(pairs)}
            per_house[metric]={}
            for h in GT:
                hp=[r for r in pairs if r['house']==h]
                per_house[metric][h]={'left_mean':float(np.mean([r['left'] for r in hp])),'right_mean':float(np.mean([r['right'] for r in hp])),'paired':pair_summary(hp)}
        c['per_house']=per_house; comparisons[label]=c
        eligible=[]
        for metric in ('error_auc_m_s','time_to_2m_s'):
            x=c[metric]
            no_stable_reverse=all(not (c['per_house'][metric][h]['right_mean']>c['per_house'][metric][h]['left_mean']+TOL and c['per_house'][metric][h]['paired']['losses']==3) for h in GT)
            eligible.append(x['right_mean']<x['left_mean']-TOL and x['paired']['exact_signflip_p_one_sided']<=0.05 and no_stable_reverse)
        final_ok=not any(c['per_house']['final_error_m'][h]['paired']['losses']==3 and c['per_house']['final_error_m'][h]['right_mean']>c['per_house']['final_error_m'][h]['left_mean']+TOL for h in GT)
        gates[label]={'temporal_metric_confirmed':any(eligible),'final_error_no_house_3of3_stable_reverse':final_ok,'pass':any(eligible) and final_ok}
    passed=all(v['pass'] for v in gates.values())
    report={'contract':'CTPI_CROSSHOUSE_36RUN_CONFIRM_V1','houses':list(GT),'seeds':seeds,'arms':list(ARMS),'run_count':len(records),'records':records,'comparisons':comparisons,'gates':gates,'pass':passed,'formal_three_module_closed_loop_confirmed':passed,'verdict':'CTPI_CROSSHOUSE_36RUN_CONFIRM=PASS' if passed else 'CTPI_CROSSHOUSE_36RUN_CONFIRM=NO_GO'}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(report['verdict']); return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
