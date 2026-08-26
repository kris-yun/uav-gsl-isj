#!/usr/bin/env python3
"""Runtime-only evaluator for a frozen sieve-GMM proximal bridge h(R,S).

Important causal boundary: Z is an instrument used during bridge fitting and is
NOT an input to h at runtime. Runtime inputs are source-independent R and the
queried candidate source coordinate S. This matches the stronger V15 bridge
form E[g(Z,S)(Y-h(R,S))]=0.

Frozen model NPZ schema:
  beta[P,Y]
  rs_mean[Dr+Ds]
  rs_std[Dr+Ds]
  h_basis_scale[P]
  r_dim scalar
  s_dim scalar
Optional metadata strings are ignored by prediction.
"""
from __future__ import annotations
import argparse,csv
from pathlib import Path
import numpy as np


def as2(x):
    x=np.asarray(x,dtype=np.float64); return x[:,None] if x.ndim==1 else x

def poly2(x):
    x=as2(x); n,d=x.shape; cols=[np.ones((n,1)),x,x*x]
    if d>1: cols += [x[:,i:i+1]*x[:,j:j+1] for i in range(d) for j in range(i+1,d)]
    return np.concatenate(cols,axis=1)

class FrozenBridge:
    def __init__(self,path):
        d=np.load(path,allow_pickle=False)
        self.beta=np.asarray(d["beta"],float); self.mean=np.asarray(d["rs_mean"],float); self.std=np.asarray(d["rs_std"],float); self.scale=np.asarray(d["h_basis_scale"],float)
        self.r_dim=int(np.asarray(d["r_dim"]).reshape(-1)[0]); self.s_dim=int(np.asarray(d["s_dim"]).reshape(-1)[0])
        if len(self.mean)!=self.r_dim+self.s_dim or len(self.std)!=len(self.mean): raise ValueError("model dimension mismatch")
        if np.any(self.std<=0) or np.any(self.scale<=0): raise ValueError("invalid frozen scales")
    def predict(self,R,S):
        R,S=as2(R),as2(S)
        if len(R)!=len(S): raise ValueError("R/S row mismatch")
        if R.shape[1]!=self.r_dim or S.shape[1]!=self.s_dim: raise ValueError("R/S dimension mismatch")
        x=np.concatenate([R,S],axis=1); h=poly2((x-self.mean)/self.std)/self.scale
        if h.shape[1]!=self.beta.shape[0]: raise ValueError("basis/beta mismatch")
        return h@self.beta
    def candidate_scores(self,r_one,S_candidates,y_one):
        S=as2(S_candidates); r=np.asarray(r_one,float).reshape(1,-1); y=np.asarray(y_one,float).reshape(1,-1)
        R=np.repeat(r,len(S),axis=0); pred=self.predict(R,S)
        if pred.shape[1]!=y.shape[1]: raise ValueError("Y dimension mismatch")
        err=np.mean((pred-y)**2,axis=1)
        return -err,pred

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--model",type=Path,required=True); ap.add_argument("--input",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args()
    x=np.load(a.input,allow_pickle=False); r=np.asarray(x["r"],float).reshape(-1); s=np.asarray(x["candidate_s"],float); y=np.asarray(x["y"],float).reshape(-1); ids=np.asarray(x["candidate_id"]).astype(str) if "candidate_id" in x else np.asarray([str(i) for i in range(len(s))])
    b=FrozenBridge(a.model); score,pred=b.candidate_scores(r,s,y)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("w",newline="") as f:
        w=csv.writer(f); w.writerow(["candidate_id","score","s0","s1"]+[f"pred_{j}" for j in range(pred.shape[1])])
        for i in range(len(s)): w.writerow([ids[i],float(score[i]),*list(s[i]),*list(pred[i])])
if __name__=="__main__": main()
