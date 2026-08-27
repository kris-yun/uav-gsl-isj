#!/usr/bin/env python3
"""Regression tests for PMFS Bernoulli trajectory adequacy."""
import numpy as np
from v3_bernoulli_adequacy import candidate_log_trajectory_support, family_log_trajectory_support

M,E=8,24
y=np.array(([0,0,1,1,0,1]*4),dtype=float)
base=np.where(y==1,0.8,0.2)
offset=np.linspace(-0.05,0.05,M)[:,None]
P0=np.clip(base[None,:]+offset,0.01,0.99)
wrong=np.where(y==1,0.1,0.9)
P1=np.clip(wrong[None,:]+0.01*offset,0.01,0.99)
rows,s=family_log_trajectory_support(np.stack([P0,P1]),y)
assert s["best_candidate_idx"]==0
assert rows[0]["ensemble_log_trajectory_likelihood_per_event"] > rows[1]["ensemble_log_trajectory_likelihood_per_event"]

bad=candidate_log_trajectory_support(np.full((M,E),0.99),np.zeros(E))
assert bad["ensemble_log_trajectory_likelihood_per_event"] < -4.0

perm=np.roll(y,1)
shuf=candidate_log_trajectory_support(P0,perm)
assert shuf["ensemble_log_trajectory_likelihood_per_event"] < rows[0]["ensemble_log_trajectory_likelihood_per_event"]

print("CG_PC_CTT_V3_BERNOULLI_ADEQUACY_SELFTEST PASS")
