#!/usr/bin/env python3
"""Small deterministic smoke test for fsei_partition.py."""
import numpy as np
import pandas as pd
from fsei_partition import fit_fsei_partition, honest_micro_lift

rng=np.random.default_rng(7)
# 4x4 source grid, 12 realizations, 2x3 observations.
rows=[]
for i in range(4):
  for j in range(4):
    rows.append({"pmfs_i":i,"pmfs_j":j,"x_m":.3*i,"y_m":.3*j})
panel=pd.DataFrame(rows)

# Neighboring columns share similar hit probabilities.
N=16;n=12;T=2;P=3
prob=np.empty((N,T,P))
for s,r in panel.iterrows():
    base=.15+.20*(int(r.pmfs_i)//2)+.05*int(r.pmfs_j)
    prob[s]=np.clip(base+rng.normal(0,.01,(T,P)),.02,.98)
x=rng.binomial(1,prob[:,None,:,:],size=(N,n,T,P))

fit=fit_fsei_partition(x,panel)
assert fit["labels"].shape==(N,)
assert 1<=fit["K"]<=N

K=fit["K"]
macro=np.full((5,K),1/K)
micro=honest_micro_lift(macro,fit["labels"])
assert micro.shape==(5,N)
assert np.allclose(micro.sum(axis=1),1)
print("OK",{"K":fit["K"],"merges":len(fit["merges"])})
