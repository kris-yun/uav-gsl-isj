#!/usr/bin/env python3
"""Check D1A connected-Ward merge order against a naive reference."""
from __future__ import annotations
import subprocess,sys,tempfile
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
BUILDER=HERE/"build_cess_d1a_hierarchy.py"

def panel():
    rows=[]; k=0
    for i in range(1,25):
        for j in range(12,19):
            rows.append(dict(panel_index=k,source_bank_row=k,source_id=f"s{k:03d}",
                             pmfs_i=i,pmfs_j=j,x_m=.3*i,y_m=.3*j,z_m=.2))
            k+=1
    return pd.DataFrame(rows)

def ward(A,B):
    d=A["c"]-B["c"]
    return float((A["n"]*B["n"]/(A["n"]+B["n"]))*np.dot(d,d))

def naive_prefix(p,steps=120):
    n=len(p); grid={(int(r.pmfs_i),int(r.pmfs_j)):i for i,r in p.iterrows()}
    C={}
    for i,r in p.iterrows():
        nb=set()
        for q in ((r.pmfs_i+1,r.pmfs_j),(r.pmfs_i-1,r.pmfs_j),
                  (r.pmfs_i,r.pmfs_j+1),(r.pmfs_i,r.pmfs_j-1)):
            j=grid.get((int(q[0]),int(q[1])))
            if j is not None: nb.add(j)
        C[i]={"n":1,"c":np.array([float(r.x_m),float(r.y_m)]),
              "m":{i},"nb":nb}
    active=set(range(n)); nid=n; out=[]
    for _ in range(steps):
        cand=[]
        for a in active:
            for b in C[a]["nb"]:
                if b not in active or a==b: continue
                ka,kb=min(C[a]["m"]),min(C[b]["m"])
                aa,bb=a,b
                if ka>kb: aa,bb=b,a; ka,kb=kb,ka
                if aa!=a: continue
                cand.append((ward(C[aa],C[bb]),ka,kb,aa,bb))
        co,_,_,a,b=min(cand)
        A,B=C[a],C[b]; mem=A["m"]|B["m"]; nn=A["n"]+B["n"]
        cen=(A["n"]*A["c"]+B["n"]*B["c"])/nn
        nb=(A["nb"]|B["nb"])-{a,b}
        active.remove(a); active.remove(b)
        valid=[u for u in nb if u in active]
        c=nid; nid+=1
        for u in valid:
            C[u]["nb"].discard(a); C[u]["nb"].discard(b); C[u]["nb"].add(c)
        C[c]={"n":nn,"c":cen,"m":mem,"nb":set(valid)}
        active.add(c)
        out.append((nn,float(co),min(mem)))
    return out

def main():
    p=panel()
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); pf=td/"panel.tsv"; jf=td/"h.json"; lf=td/"m.tsv"
        p.to_csv(pf,sep="\t",index=False)
        subprocess.run([sys.executable,str(BUILDER),"--panel",str(pf),
                        "--out-json",str(jf),"--merge-log",str(lf)],check=True,
                       stdout=subprocess.DEVNULL)
        got=pd.read_csv(lf,sep="\t").head(120)
    ref=naive_prefix(p,120)
    for i,(r,e) in enumerate(zip(got.itertuples(index=False),ref)):
        nn,co,mn=e
        assert int(r.new_size)==nn,(i,r,e)
        assert int(r.new_min_panel_row)==mn,(i,r,e)
        assert np.isclose(float(r.ward_cost),co,rtol=0,atol=1e-12),(i,r,e)
    print("CESS D1A hierarchy self-test: PASS")

if __name__=="__main__":
    main()
