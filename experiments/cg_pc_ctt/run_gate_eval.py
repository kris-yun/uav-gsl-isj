#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from completeness_gate import GateConfig,compute_gate

def opt(d,k,n,default):
    if k in d:
        x=np.asarray(d[k]);
        if len(x)!=n: raise ValueError(f"{k} length mismatch")
        return x
    return np.asarray([default]*n)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--npz',required=True); p.add_argument('--out',required=True)
    p.add_argument('--gamma-min',type=float,default=0.05)
    p.add_argument('--alpha-min',type=float,required=True)
    p.add_argument('--beta-min',type=float,default=None)
    p.add_argument('--ridge-rel',type=float,default=1e-3)
    a=p.parse_args(); d=np.load(a.npz,allow_pickle=True); phi=np.asarray(d['phi'],float)
    if phi.ndim!=4: raise ValueError(f"phi must be [N,S,M,D], got {phi.shape}")
    N=phi.shape[0]; context=opt(d,'context',N,''); split=opt(d,'split',N,''); house=opt(d,'house',N,''); margin=opt(d,'margin',N,np.nan).astype(float)
    cfg=GateConfig(a.gamma_min,a.alpha_min,a.beta_min,a.ridge_rel)
    rows=[]
    for i in range(N):
        g=compute_gate(phi[i],cfg)
        rows.append({'i':i,'context':context[i],'split':split[i],'house':house[i],**g.to_dict(),'margin':margin[i]})
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    accepted=np.array([r['accepted'] for r in rows],bool)
    s={'n':N,'coverage':float(accepted.mean()),'accepted':int(accepted.sum()),'rejected':int((~accepted).sum()),'gamma_min':a.gamma_min,'alpha_min':a.alpha_min,'beta_min':a.beta_min}
    if np.any(np.isfinite(margin)):
        for name,mask in [('accepted',accepted),('rejected',~accepted)]:
            z=margin[mask & np.isfinite(margin)]
            s[f'{name}_mean_margin']=float(z.mean()) if len(z) else None
            s[f'{name}_positive_margin_rate']=float(np.mean(z>0)) if len(z) else None
    print(json.dumps(s,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
