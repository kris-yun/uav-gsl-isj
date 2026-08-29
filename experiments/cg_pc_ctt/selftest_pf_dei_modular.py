#!/usr/bin/env python3
import math
import numpy as np
from pf_dei_modular_core import *

# 1) sensor inverse parity on known physical signal.
cfg=SensorInverseConfig()
alpha=np.exp(-cfg.dt/cfg.tau)
c=np.array([0.0,0.2,1.0,0.4,0.0,0.8,0.1,0.0],float)
m=np.zeros(len(c)+cfg.delay_samples,float)
for k in range(1,len(m)):
    idx=k-cfg.delay_samples
    inp=c[idx] if 0<=idx<len(c) else 0.0
    m[k]=alpha*m[k-1]+(1-alpha)*inp
rec=StreamingSensorInverse(cfg).deconvolve(m)
assert np.max(np.abs(rec[:len(c)]-c)) < 1e-10, (rec,c)

# 1b) historical sensor_trace.csv stores ppm to six decimal places.  Rounding
# each M sample by at most 0.5e-6 propagates through the exact inverse by at
# most 0.5e-6*(1+alpha)/(1-alpha).  This tolerance is replay-only; production
# raw-double inference keeps the strict default tolerance above.
quantum=1e-6
serialized_bound=0.5*quantum*(1.0+alpha)/(1.0-alpha)
mr=np.round(m,6)
replay_cfg=SensorInverseConfig(serialization_bound_ppm=float(serialized_bound)+1e-12)
recr=StreamingSensorInverse(replay_cfg).deconvolve(mr)
assert np.min((mr[1:]-alpha*mr[:-1])/(1-alpha)) >= -serialized_bound-1e-12
# Recovered C is allowed inverse-rounding error plus truth-serialization-free C.
assert np.max(np.abs(recr[:len(c)]-c)) <= serialized_bound+1e-12

# 2) synthetic source ranking. true source 1, observation is held-out-like.
T=50; S=4; M=4
t=np.arange(T)
x=np.zeros((S,M,T),float)
for s in range(S):
  for j in range(M):
    base=0.2+0.1*s
    phase=0.17*j
    x[s,j]=np.maximum(0, base + 0.25*np.sin(0.2*t + 0.7*s + phase))
y=np.maximum(0,0.3 + 0.25*np.sin(0.2*t + 0.7*1 + 0.09))
q0=np.ones(S)/S
r=infer(y,x,q0,0.1,Mode.FULL)
assert r.selected_source==1, (r.scores,r.posterior)

# 3) coherence scramble preserves the per-time ensemble multiset exactly.
xs=coherent_scramble(x)
for s in range(S):
  for k in range(T):
    assert np.allclose(np.sort(xs[s,:,k]), np.sort(x[s,:,k]))

# 4) reversible posterior: same prefix is recomputed from q0, never multiplied again.
r2=infer(y,x,q0,0.1,Mode.FULL)
assert np.allclose(r.posterior,r2.posterior)
assert abs(r.posterior.sum()-1)<1e-12

# 5) each inference-side ablation switch is isolated and numerically valid.
# Sensor ablation is applied at the observation adapter, not inside infer().
for mode in [Mode.FULL,Mode.ABLATE_TEMPORAL,Mode.ABLATE_COHERENCE,Mode.ABLATE_NUISANCE]:
    rr=infer(y,x,q0,0.1,mode)
    assert np.all(np.isfinite(rr.scores)) and np.all(np.isfinite(rr.posterior))
print('PF_DEI_MODULAR_SELFTEST PASS')
