#!/usr/bin/env python3
import numpy as np
from completeness_gate import GateConfig,compute_gate,no_update_posterior

def make_case(signal=3.0,noise=0.2,collapse=False,seed=0,S=4,M=8,D=12):
    rng=np.random.default_rng(seed)
    basis=np.zeros((S,D))
    basis[0,0]=1.; basis[1,1]=1.; basis[2,2]=1.; basis[3,:3]=-1.
    if collapse: basis[:,2]*=1e-4
    return signal*basis[:,None,:] + noise*rng.normal(size=(S,M,D))

def cfg(seed=20260827,semantics='exchangeable_realizations',nperm=199):
    return GateConfig(gamma_min=0.05,p_max=0.01,rank_k=3,n_folds=4,n_permutations=nperm,permutation_seed=seed,member_semantics=semantics)

good=compute_gate(make_case(signal=3.0),cfg(1, nperm=499))
weak=compute_gate(make_case(signal=0.01),cfg(2, nperm=499))
null=compute_gate(make_case(signal=0.0),cfg(3, nperm=499))
collapsed=compute_gate(make_case(signal=3.0,collapse=True),cfg(4, nperm=499))

assert good.accepted,good
assert good.alpha_cf>0 and good.gamma_cf>=0.05 and good.p_perm<=0.01,good
assert not weak.accepted,weak
assert not null.accepted,null
assert not collapsed.accepted,collapsed

# Fixed nuisance support points may be screened descriptively, but V2 forbids
# treating the permutation p-value as inferential evidence.
fixed=compute_gate(make_case(signal=3.0),cfg(5,'fixed_nuisance_design',199))
assert not fixed.accepted and not fixed.inferential_valid,fixed

# Regression: a finite-M pure null must not systematically become accepted.
false_accept=0
for seed in range(20):
    r=compute_gate(make_case(signal=0.0,seed=seed),cfg(1000+seed,nperm=99))
    false_accept += int(r.accepted)
assert false_accept==0,false_accept

# Regression: independently permuting member order inside each source cannot
# manufacture source information from a null realization.
rng=np.random.default_rng(77)
x=make_case(signal=0.0,seed=77)
for s in range(x.shape[0]):
    x[s]=x[s,rng.permutation(x.shape[1])]
member_perm_null=compute_gate(x,cfg(78,nperm=199))
assert not member_perm_null.accepted,member_perm_null

q=np.array([0.1,0.2,0.3,0.4])
assert np.array_equal(q,no_update_posterior(q))

print('SELFTEST PASS V2')
for name,r in [('good',good),('weak',weak),('null',null),('collapsed',collapsed),('fixed_design',fixed),('member_perm_null',member_perm_null)]:
    print(name,r)
print('null_false_accept_20=',false_accept)
