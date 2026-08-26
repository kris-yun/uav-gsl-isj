#!/usr/bin/env python3
"""Development-only alpha calibration. Test rows are never used for selection."""
import argparse,json
import numpy as np
from completeness_gate import GateConfig,compute_gate

def main():
    p=argparse.ArgumentParser(); p.add_argument('--npz',required=True); p.add_argument('--gamma-min',type=float,default=0.05); p.add_argument('--min-coverage',type=float,default=0.20); p.add_argument('--quantiles',type=int,default=41); a=p.parse_args()
    d=np.load(a.npz,allow_pickle=True); phi=np.asarray(d['phi'],float); margin=np.asarray(d['margin'],float); split=np.asarray(d['split']).astype(str); dev=split=='dev'
    if not np.any(dev): raise ValueError("No split=='dev' rows")
    if not np.all(np.isfinite(margin[dev])): raise ValueError('Development margin contains NaN/Inf')
    vals=[]
    for i in np.flatnonzero(dev):
        r=compute_gate(phi[i],GateConfig(gamma_min=0.0,alpha_min=0.0)); vals.append((i,r.gamma,r.alpha))
    idx=np.array([v[0] for v in vals],int); gam=np.array([v[1] for v in vals]); alp=np.array([v[2] for v in vals]); mar=margin[idx]
    base=gam>=a.gamma_min; pool=alp[base]
    if len(pool)<5: raise RuntimeError('Too few dev contexts pass gamma to calibrate alpha')
    best=None
    for th in np.unique(np.quantile(pool,np.linspace(0,0.95,a.quantiles))):
        acc=base & (alp>=th); cov=float(acc.mean())
        if cov<a.min_coverage or acc.sum()<3: continue
        q25=float(np.quantile(mar[acc],0.25)); mean=float(mar[acc].mean()); key=(q25,mean,cov)
        if best is None or key>best[0]: best=(key,float(th),int(acc.sum()))
    if best is None: raise RuntimeError('No alpha threshold satisfies minimum coverage')
    print(json.dumps({'alpha_min_frozen':best[1],'gamma_min_frozen':a.gamma_min,'dev_accepted':best[2],'dev_total':int(dev.sum()),'dev_coverage':best[0][2],'dev_margin_q25':best[0][0],'dev_mean_margin':best[0][1],'NOTE':'Freeze thresholds before held-out evaluation; no retuning.'},indent=2))
if __name__=='__main__': main()
