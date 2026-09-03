#!/usr/bin/env python3
"""Compute truth-used-after-run performance metrics for CTPI paired closed-loop arms."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import numpy as np

GT={'H01':(-0.40,-2.90),'H02':(0.0,-1.0),'H03':(-0.45,1.90)}
ARMS=('A0','F00','F10','F11')
TOL=1e-12

def read(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def metrics(path:Path,house:str,horizon=240.0):
    rows=read(path); t=[]; e=[]; gx,gy=GT[house]
    for r in rows:
        try:
            if r.get('estimate_available','true').lower() not in ('true','1'):continue
            tt=float(r['sim_time']); x=float(r['estimate_x']); y=float(r['estimate_y'])
        except Exception:continue
        if not all(map(math.isfinite,(tt,x,y))) or tt < -TOL or tt > horizon+TOL:continue
        t.append(min(max(tt,0.0),horizon));e.append(math.hypot(x-gx,y-gy))
    if not t:raise RuntimeError(f'NO_ESTIMATE:{path}')
    order=np.argsort(t); t=np.asarray(t)[order]; e=np.asarray(e)[order]
    ut=[];ue=[]
    for tt,ee in zip(t,e):
        if ut and abs(tt-ut[-1])<=TOL:ue[-1]=float(ee)
        else:ut.append(float(tt));ue.append(float(ee))
    t=np.asarray(ut);e=np.asarray(ue)
    ta=np.concatenate([[0.0],t,[horizon]]); ea=np.concatenate([[e[0]],e,[e[-1]]])
    auc=float(np.sum(0.5*(ea[1:]+ea[:-1])*np.diff(ta)))
    hit=np.flatnonzero(e<=2.0)
    time2=float(t[hit[0]]) if hit.size else horizon
    return {'final_error_m':float(e[-1]),'error_auc_m_s':auc,'time_to_2m_s':time2,'estimate_points':int(len(e))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run-root',type=Path,required=True); ap.add_argument('--house',choices=GT,required=True); ap.add_argument('--seeds',default='0,1,2'); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    seeds=[int(x) for x in args.seeds.split(',') if x!='']; records=[]
    for seed in seeds:
        for arm in ARMS:
            p=args.run_root/f'{args.house}_seed{seed}_{arm}'/'source_estimate_trace.csv'
            records.append({'house':args.house,'seed':seed,'arm':arm,**metrics(p,args.house)})
    comps={}
    for left,right,label in [('A0','F00','M1_F00_vs_A0'),('F00','F10','M3_F10_vs_F00'),('F10','F11','M2_DOWNSTREAM_F11_vs_F10')]:
        out={}
        for metric in ('final_error_m','error_auc_m_s','time_to_2m_s'):
            pairs=[]
            for seed in seeds:
                l=next(r for r in records if r['seed']==seed and r['arm']==left)[metric]; rr=next(r for r in records if r['seed']==seed and r['arm']==right)[metric]
                pairs.append({'seed':seed,'left':l,'right':rr,'improved':rr<l-TOL,'worsened':rr>l+TOL})
            out[metric]={'left_mean':float(np.mean([p['left'] for p in pairs])),'right_mean':float(np.mean([p['right'] for p in pairs])),'wins':sum(p['improved'] for p in pairs),'losses':sum(p['worsened'] for p in pairs),'pairs':pairs}
        comps[label]=out
    report={'contract':'CTPI_FASTTRACK_PERFORMANCE_V1','horizon_s':240.0,'records':records,'comparisons':comps,'screening_only':len(seeds)<9}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print('CTPI_FASTTRACK_PERFORMANCE=PASS')
if __name__=='__main__':main()
