#!/usr/bin/env python3
import numpy as np
from completeness_gate import GateConfig,compute_gate,no_update_posterior

def make_case(signal=3.0,noise=0.2,collapse=False,seed=0):
    rng=np.random.default_rng(seed); S,M,D=4,8,12; basis=np.zeros((S,D)); basis[0,0]=1; basis[1,1]=1; basis[2,2]=1; basis[3,:3]=-1
    if collapse: basis[:,2]*=1e-4
    return signal*basis[:,None,:]+noise*rng.normal(size=(S,M,D))

good=compute_gate(make_case(),GateConfig(gamma_min=0.05,alpha_min=1.0))
weak=compute_gate(make_case(signal=0.01,noise=0.2),GateConfig(gamma_min=0.05,alpha_min=1.0))
collapsed=compute_gate(make_case(collapse=True),GateConfig(gamma_min=0.05,alpha_min=1.0))
assert good.accepted,good
assert not weak.accepted,weak
assert not collapsed.accepted,collapsed
q=np.array([0.1,0.2,0.3,0.4]); assert np.array_equal(q,no_update_posterior(q))
print('SELFTEST PASS'); print('good',good); print('weak',weak); print('collapsed',collapsed)
