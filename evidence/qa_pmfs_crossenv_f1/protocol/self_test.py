#!/usr/bin/env python3
import numpy as np
from qa_pmfs_core import marginal_preserving_probit_loglik, independent_loglik

h=np.array([0,1,1,0],dtype=np.int8)
p=np.array([0.1,0.25,0.6,0.8],dtype=float)
assert abs(marginal_preserving_probit_loglik(h,p,0.0)-independent_loglik(h,p))<1e-12

# Marginal property is analytic:
# sqrt(rho) Z + sqrt(1-rho) eps ~ N(0,1), hence
# P(H=1)=Phi(Phi^-1(p))=p.
print("QA_PMFS_SELFTEST_PASS")
