#!/usr/bin/env python3
"""OSDR-inspired within-stop dynamical marker for sparse GSL observations.

One PMFS StopAndMeasure stop contains repeated concentration measurements. This
module converts those causally available samples into a fixed 4-D outcome Y:
  log1p concentration mean, log1p concentration sd, hit fraction, temporal slope.

It adds no learned parameter and uses the existing PMFS gas threshold.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np


def marker(concentration,time,threshold):
    c=np.maximum(np.asarray(concentration,dtype=float),0.0)
    t=np.asarray(time,dtype=float)
    if c.ndim!=1 or t.shape!=c.shape or len(c)<2 or not np.all(np.isfinite(c)) or not np.all(np.isfinite(t)):
        raise ValueError('need >=2 finite concentration/time samples')
    if np.any(np.diff(t)<=0): raise ValueError('time must increase within stop')
    u=np.log1p(c); tc=t-t.mean(); den=float(tc@tc)
    slope=0.0 if den<=1e-15 else float(tc@(u-u.mean())/den)
    return np.asarray([float(u.mean()),float(u.std(ddof=0)),float(np.mean(c>threshold)),slope],dtype=float)


def load_rows(path):
    with path.open(newline='') as f: return list(csv.DictReader(f))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('events_csv',type=Path)
    ap.add_argument('--samples-per-stop',type=int,default=8)
    ap.add_argument('--out-csv',type=Path,required=True); ap.add_argument('--out-json',type=Path,required=True)
    a=ap.parse_args(); rr=load_rows(a.events_csv)
    required=('concentration','threshold','sim_time','x','y')
    if not rr or any(k not in rr[0] for k in required): raise ValueError(f'events CSV needs {required}')
    L=a.samples_per_stop
    if L<2: raise ValueError('samples-per-stop must be >=2')
    # Preferred: explicit stop_id. Fallback: consecutive fixed blocks, matching
    # the frozen PMFS maxUpdatesPerStop contract when called with L=8.
    groups=[]
    if 'stop_id' in rr[0]:
        by={}
        for r in rr: by.setdefault(r['stop_id'],[]).append(r)
        groups=[(k,by[k]) for k in sorted(by,key=lambda z:(len(z),z))]
    else:
        if len(rr)%L!=0: raise ValueError('row count not divisible by samples-per-stop and no stop_id exists')
        groups=[(str(i//L),rr[i:i+L]) for i in range(0,len(rr),L)]
    out=[]
    for stop_id,g in groups:
        if len(g)!=L: raise ValueError(f'stop {stop_id}: expected exactly {L} samples, got {len(g)}')
        c=np.asarray([float(r['concentration']) for r in g]); t=np.asarray([float(r['sim_time']) for r in g]); th=np.asarray([float(r['threshold']) for r in g])
        if np.max(np.abs(th-th[0]))>1e-12: raise ValueError(f'stop {stop_id}: threshold drift')
        x=np.asarray([float(r['x']) for r in g]); y=np.asarray([float(r['y']) for r in g])
        # StopAndMeasure must be spatially stationary up to numerical jitter.
        if np.max(np.hypot(x-x[0],y-y[0]))>1e-5: raise ValueError(f'stop {stop_id}: position changed within stop')
        v=marker(c,t,float(th[0]))
        out.append({'stop_id':stop_id,'x':float(x.mean()),'y':float(y.mean()),'t_start':float(t[0]),'t_end':float(t[-1]),
                    'y_logc_mean':v[0],'y_logc_sd':v[1],'y_hit_fraction':v[2],'y_logc_slope':v[3]})
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    meta={'contract':'CG_PC_CTT_OSDR_BLOCK_MARKER_V1','samples_per_stop':L,'stops':len(out),
          'y_feature_name':['logc_mean','logc_sd','hit_fraction','logc_slope'],
          'scientific_boundary':'Temporal-marker design inspired by OSDR principle; no biological OSDR equation is transferred.'}
    a.out_json.write_text(json.dumps(meta,indent=2),encoding='utf-8'); print(json.dumps(meta,indent=2))

if __name__=='__main__': main()
