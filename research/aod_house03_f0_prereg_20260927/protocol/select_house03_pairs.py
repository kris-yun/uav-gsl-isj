#!/usr/bin/env python3
import argparse, hashlib, math
from pathlib import Path
import pandas as pd, numpy as np

SALT="AOD_H03_F1_20260927"
ANCHORS=[
 ("pmfs_24_13","pmfs_24_14"),
 ("pmfs_1_4","pmfs_2_4"),
 ("pmfs_44_26","pmfs_43_26"),
]
def canon(a,b): return tuple(sorted((str(a),str(b))))
def h(a,b): return hashlib.sha256((SALT+"|"+canon(a,b)[0]+"|"+canon(a,b)[1]).encode()).hexdigest()

ap=argparse.ArgumentParser()
ap.add_argument("--source-bank",type=Path,required=True)
ap.add_argument("--out",type=Path,required=True)
a=ap.parse_args()
df=pd.read_csv(a.source_bank,sep=None,engine="python")
req={"source_id","pmfs_i","pmfs_j","x_m","y_m","z_m","clearance_m"}
miss=req-set(df.columns)
if miss: raise SystemExit(f"missing columns: {sorted(miss)}")
if "house" in df.columns: df=df[df.house.astype(str)=="House03"].copy()
if "free" in df.columns: df=df[df.free.astype(bool)].copy()
df=df[(np.isclose(df.z_m.astype(float),0.20,atol=1e-9)) &
      (df.clearance_m.astype(float)>=0.30)].copy()
by={str(r.source_id):r for _,r in df.iterrows()}
pairs=[]
ids=sorted(by)
for ii,a0 in enumerate(ids):
  ra=by[a0]
  for b0 in ids[ii+1:]:
    rb=by[b0]
    di=abs(int(ra.pmfs_i)-int(rb.pmfs_i)); dj=abs(int(ra.pmfs_j)-int(rb.pmfs_j))
    if (di,dj) not in [(1,0),(0,1)]: continue
    d=math.hypot(float(ra.x_m)-float(rb.x_m),float(ra.y_m)-float(rb.y_m))
    if abs(d-0.30)>1e-6: continue
    cx=(float(ra.x_m)+float(rb.x_m))/2
    cy=(float(ra.y_m)+float(rb.y_m))/2
    pairs.append(dict(a=a0,b=b0,cx=cx,cy=cy,d=d,tie=h(a0,b0)))

avail={(canon(p["a"],p["b"])):(p) for p in pairs}
chosen=[]
used=set()
for A,B in ANCHORS:
    key=canon(A,B)
    if key not in avail: raise SystemExit(f"anchor absent/ineligible: {key}")
    p=avail[key].copy(); chosen.append(p); used.update(key)

while len(chosen)<6:
    cands=[]
    for p in pairs:
        key=canon(p["a"],p["b"])
        if key[0] in used or key[1] in used: continue
        mind=min(math.hypot(p["cx"]-q["cx"],p["cy"]-q["cy"]) for q in chosen)
        cands.append((mind,p["tie"],p))
    if not cands: raise SystemExit("not enough eligible disjoint pairs")
    cands.sort(key=lambda x:(-x[0],x[1]))
    p=cands[0][2].copy()
    chosen.append(p); used.update(canon(p["a"],p["b"]))

# output source rows
rows=[]
for pi,p in enumerate(chosen,1):
    for role,sid in zip(["anchor","partner"],canon(p["a"],p["b"])):
        r=by[sid]
        rows.append(dict(pair_id=pi,role=role,source_id=sid,
                         pmfs_i=int(r.pmfs_i),pmfs_j=int(r.pmfs_j),
                         x_m=float(r.x_m),y_m=float(r.y_m),z_m=float(r.z_m),
                         clearance_m=float(r.clearance_m),
                         pair_center_x=p["cx"],pair_center_y=p["cy"],
                         pair_distance_m=p["d"],selection_tie=p["tie"]))
out=pd.DataFrame(rows)
cent=np.array([[chosen[i]["cx"],chosen[i]["cy"]] for i in range(6)])
D=np.sqrt(((cent[:,None,:]-cent[None,:,:])**2).sum(2))
np.fill_diagonal(D,np.inf)
minsep=float(D.min())
if minsep<1.50-1e-9: raise SystemExit(f"min pair-center separation {minsep:.6f}<1.50m")
a.out.parent.mkdir(parents=True,exist_ok=True)
out.to_csv(a.out,sep="\t",index=False)
print("PAIRS",6,"SOURCES",12,"MIN_PAIR_CENTER_SEP_M",minsep)
