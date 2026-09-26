#!/usr/bin/env python3
import numpy as np
from analyze_dependence_layers_d0 import preserve_marginals,preserve_time_snapshots,es_u,es_v

rng=np.random.default_rng(123)
K,T,Q=8,10,30
B=rng.integers(0,2,size=(K,T,Q),dtype=np.int8)

C1=preserve_marginals(B,np.random.default_rng(1))
assert np.array_equal(C1.sum(0),B.sum(0))
assert np.isin(C1,[0,1]).all()
X1=C1.sum(2)
assert np.all((X1>=0)&(X1<=30))
assert np.allclose(X1,np.rint(X1))

C2=preserve_time_snapshots(B,np.random.default_rng(2))
assert np.array_equal(C2.sum(0),B.sum(0))
assert np.array_equal(np.sort(C2.sum(2),axis=0),np.sort(B.sum(2),axis=0))
assert np.isin(C2,[0,1]).all()

# A hand-built temporal pairing example: per-time count marginals identical,
# but paired trajectories differ.
X=np.array([[0,0],[0,0],[2,2],[2,2],[0,0],[0,0],[2,2],[2,2]],float)
Y=np.array([[0,2],[0,2],[2,0],[2,0],[0,2],[0,2],[2,0],[2,0]],float)
assert np.array_equal(np.sort(X,axis=0),np.sort(Y,axis=0))
q=np.array([0,0],float)
assert np.isfinite(es_u(X,q)) and np.isfinite(es_v(X,q))
print("SELF_TEST_PASS")
