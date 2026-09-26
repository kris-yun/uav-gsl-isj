#!/usr/bin/env python3
# Minimal deterministic algebra check for the Energy Score and exact
# mean-preserving residual reassignment contract. This is not scientific data.
import numpy as np
from analyze_branching_d0 import energy_score
rng=np.random.default_rng(7)
S,K,D=4,8,10
X=rng.normal(size=(S,K,D))
mu=X.mean(1)
res=X-mu[:,None,:]
assert np.max(np.abs(res.mean(1))) < 1e-12
p=np.array([1,0,3,2])
null=np.stack([mu[s][None,:]+res[p[s]] for s in range(S)])
assert np.max(np.abs(null.mean(1)-mu)) < 1e-12
y=X[0,0]
a=energy_score(X[0],y)
b=energy_score(X[0],y)
assert a==b
print("SELF_TEST_PASS")
