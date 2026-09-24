#!/usr/bin/env python3
"""Regression test for CESS D1A uniform-macro intervention evaluation."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("d1a",HERE/"analyze_cess_d1a.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

# Four micro sources, two held-out realizations each.
N=4; R=2
labels=np.array([0,0,0,1],dtype=int)
true_s=np.repeat(np.arange(N),R)

rows=[]
for s in true_s:
    p=np.full(N,.08)
    p[s]=.74
    p[(s+1)%N]+=.02
    p/=p.sum()
    rows.append(p)
post=np.stack(rows)

got=m.macro_ei_only(post,true_s,labels)

# Independent calculation under p(M)=1/2 and uniform micro within M.
sizes=np.array([3,1])
score=np.zeros((len(post),2))
score[:,0]=post[:,:3].sum(axis=1)/3.0
score[:,1]=post[:,3]
score/=score.sum(axis=1,keepdims=True)
tg=labels[true_s]
lt=np.log(score[np.arange(len(score)),tg]).reshape(N,R).mean(axis=1)
expected=np.log(2.0)+0.5*(lt[:3].mean()+lt[3:].mean())
wrong_micro_uniform=np.log(2.0)+lt.mean()

assert np.isclose(got,expected,rtol=0,atol=1e-12),(got,expected)
assert not np.isclose(got,wrong_micro_uniform,rtol=0,atol=1e-6)
print("CESS D1A weighting self-test: PASS")
