#!/usr/bin/env python3
"""Regression tests for V3 resolution-cell posterior projection."""
import numpy as np
from v3_quotient_rank_posterior import posterior

ids=["a","b","c","d"]
q0=np.array([.1,.2,.3,.4])

ev=[
 {"candidate_id":ids,"score":np.array([9.,-9.,2.,0.]),"accepted":True,"component_id":np.array([0,0,1,2])},
 {"candidate_id":ids,"score":np.array([-8.,8.,1.,0.]),"accepted":True,"component_id":np.array([0,0,1,2])},
]
q,meta=posterior(ev,np.array([0,0,1,2]),q0)
assert np.isclose(q[0]/q[1],q0[0]/q0[1],rtol=1e-12)
assert meta["current_resolution_cells"]==3

q_all,_=posterior(ev,np.array([0,0,0,0]),q0)
assert np.allclose(q_all,q0,rtol=1e-12,atol=1e-12)

q_split,_=posterior(ev,np.array([0,1,2,3]),q0)
assert np.isclose(q_split[0]/q_split[1],q0[0]/q0[1],rtol=1e-12)

ev2=ev+[
 {"candidate_id":ids,"score":np.array([8.,-8.,0.,0.]),"accepted":True,"component_id":np.array([0,1,2,3])},
 {"candidate_id":ids,"score":np.array([7.,-7.,0.,0.]),"accepted":True,"component_id":np.array([0,1,2,3])},
]
q_split2,_=posterior(ev2,np.array([0,1,2,3]),q0)
assert q_split2[0]/q_split2[1] > q0[0]/q0[1]

q_merge,_=posterior(ev2,np.array([0,0,1,2]),q0)
assert np.isclose(q_merge[0]/q_merge[1],q0[0]/q0[1],rtol=1e-12)

print("CG_PC_CTT_V3_QUOTIENT_POSTERIOR_SELFTEST PASS")
