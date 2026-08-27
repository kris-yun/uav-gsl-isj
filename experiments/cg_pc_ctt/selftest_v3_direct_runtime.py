#!/usr/bin/env python3
import numpy as np
from v3_direct_runtime_reference import observation_resolved_posterior

rng=np.random.default_rng(20260827)
rect=np.asarray([[0,0,1,1],[1,0,1,1],[0,1,1,1],[1,1,1,1]],dtype=int)
base=np.asarray([
 [.10,.15,.20,.25,.30,.40,.45,.50],
 [.20,.25,.30,.35,.45,.55,.60,.65],
 [.40,.35,.30,.25,.20,.15,.10,.05],
 [.60,.55,.50,.45,.40,.35,.30,.25],
])
P=np.clip(base[:,None,:]+rng.normal(0,.02,(4,8,8)),.01,.99)
y=np.asarray([0,0,1,0,1,1,1,1],dtype=int)
block=np.arange(8)
prior=np.ones(4)

q,meta=observation_resolved_posterior(P,y,block,rect,prior)
assert meta['released'] and np.isclose(q.sum(),1.0) and np.isfinite(q).all()
assert meta['resolution']['resolution_cells']==4

# Exact local twin: evidence is forbidden from splitting the unresolved cell.
T=P.copy(); T[1]=T[0]
q,meta=observation_resolved_posterior(T,y,block,rect,prior)
assert meta['released']
assert meta['resolution']['resolution_cells']==3
assert np.isclose(q[0],q[1],rtol=0,atol=1e-12)

# Same physical predictive family but non-identifying parity fold -> abstain.
y_bad=np.asarray([0,1,0,1,0,1,0,1],dtype=int)  # even all 0, odd all 1
q,meta=observation_resolved_posterior(P,y_bad,block,rect,prior)
assert q is None and not meta['released'] and meta['reason']=='NON_IDENTIFYING_FOLD'

# Same-window native posterior is not an input: changing only fixed prior changes
# only the declared base measure, never the predictive evidence computation.
prior2=np.asarray([1.,2.,1.,2.])
q2,meta2=observation_resolved_posterior(P,y,block,rect,prior2)
assert meta2['same_window_native_posterior_used'] is False
assert meta2['source_truth_used'] is False
assert meta2['proximal_bridge_required'] is False
assert np.isclose(q2.sum(),1.0)

print('CG_PC_CTT_V3_DIRECT_RUNTIME_SELFTEST PASS')
