#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-bank",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    bank=pd.read_csv(a.source_bank,sep="\t")
    cells={(int(r.pmfs_i),int(r.pmfs_j)):idx for idx,r in bank.iterrows()}
    imin,imax=int(bank.pmfs_i.min()),int(bank.pmfs_i.max())
    jmin,jmax=int(bank.pmfs_j.min()),int(bank.pmfs_j.max())
    cand=[]
    for i0 in range(imin,imax+1):
      for i1 in range(i0,imax+1):
        w=i1-i0+1
        for j0 in range(jmin,jmax+1):
          for j1 in range(j0,jmax+1):
            h=j1-j0+1; n=w*h
            ok=all((i,j) in cells for i in range(i0,i1+1) for j in range(j0,j1+1))
            if ok:
              cand.append((n,-abs(w-h),-i0,-j0,-i1,-j1,i0,i1,j0,j1))
    if not cand: raise RuntimeError("no complete rectangle")
    best=max(cand)
    i0,i1,j0,j1=best[-4:]
    idx=[k for k,r in bank.iterrows()
         if i0<=int(r.pmfs_i)<=i1 and j0<=int(r.pmfs_j)<=j1]
    panel=bank.loc[idx].copy()
    if (i0,i1,j0,j1)!=(1,24,12,18) or len(panel)!=168:
      raise RuntimeError(f"frozen rectangle drift: {(i0,i1,j0,j1)}, n={len(panel)}")
    panel.insert(0,"source_bank_row",panel.index.astype(int))
    panel.insert(0,"panel_index",range(len(panel)))
    cols=["panel_index","source_bank_row","source_id","pmfs_i","pmfs_j","x_m","y_m","z_m"]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    panel[cols].to_csv(a.out,sep="\t",index=False)
    print(f"panel={len(panel)} rectangle=i{i0}..{i1},j{j0}..{j1}")
if __name__=="__main__":
    main()
