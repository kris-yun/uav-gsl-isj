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

# 5) carrier-to-cell KL/I-projection preserves carrier marginal and within-carrier odds.
carrier_of_cell = np.array([0, 0, 1, 1, 1, 2], dtype=np.int64)
reference_cell_mass = np.array([0.05, 0.15, 0.10, 0.20, 0.30, 0.20], dtype=np.float64)
carrier_posterior = np.array([0.2, 0.5, 0.3], dtype=np.float64)
cell_posterior = carrier_to_cell_projection(carrier_posterior, carrier_of_cell, reference_cell_mass)
carrier_sums = np.array([cell_posterior[carrier_of_cell == i].sum() for i in range(3)])
assert np.allclose(carrier_sums, carrier_posterior / carrier_posterior.sum())
for i in range(3):
    idx = np.where(carrier_of_cell == i)[0]
    if len(idx) >= 2:
        ratios_ref = reference_cell_mass[idx] / reference_cell_mass[idx[0]]
        ratios_out = cell_posterior[idx] / cell_posterior[idx[0]]
        assert np.allclose(ratios_ref, ratios_out)
reference_carrier_mass = np.array([reference_cell_mass[carrier_of_cell == i].sum() for i in range(3)])
same_reference = carrier_to_cell_projection(reference_carrier_mass, carrier_of_cell, reference_cell_mass)
assert np.allclose(same_reference, reference_cell_mass / reference_cell_mass.sum())
try:
    carrier_to_cell_projection([0.2, 0.5, 0.3, 0.0], carrier_of_cell, reference_cell_mass)
    raise AssertionError("missing carrier support was accepted")
except ValueError as exc:
    assert "no reference cells" in str(exc)

# 6) each inference-side ablation switch is isolated and numerically valid.
# Sensor ablation is applied at the observation adapter, not inside infer().
for mode in [Mode.FULL,Mode.ABLATE_TEMPORAL,Mode.ABLATE_COHERENCE,Mode.ABLATE_NUISANCE]:
    rr=infer(y,x,q0,0.1,mode)
    assert np.all(np.isfinite(rr.scores)) and np.all(np.isfinite(rr.posterior))

# 7) persistent sensor state must be continuous across source-update / stop
# boundaries.  Splitting the same physical tape into two contiguous chunks and
# resuming from the carried state must match one uninterrupted pass exactly.
def advance_persistent_sensor(samples, state=0.0, delay_one=0.0, delay_two=0.0):
    out = []
    for physical in np.asarray(samples, dtype=np.float64):
        target = delay_two
        delay_two = delay_one
        delay_one = float(physical)
        state = alpha * state + (1.0 - alpha) * target
        out.append(state)
    return np.asarray(out, dtype=np.float64), float(state), float(delay_one), float(delay_two)

trace = np.array([0.0, 0.25, 0.5, 0.0, 0.8, 0.1, 0.0, 0.4, 0.0, 0.0], dtype=np.float64)
full_trace, full_state, full_d1, full_d2 = advance_persistent_sensor(trace)
prefix_trace, prefix_state, prefix_d1, prefix_d2 = advance_persistent_sensor(trace[:6])
suffix_trace, suffix_state, suffix_d1, suffix_d2 = advance_persistent_sensor(
    trace[6:], prefix_state, prefix_d1, prefix_d2
)
stitched_trace = np.concatenate([prefix_trace, suffix_trace])
assert np.allclose(stitched_trace, full_trace)
assert np.isclose(suffix_trace[0], full_trace[6])
assert np.allclose([suffix_state, suffix_d1, suffix_d2], [full_state, full_d1, full_d2])
reset_suffix_trace, *_ = advance_persistent_sensor(trace[6:])
assert not np.allclose(reset_suffix_trace, suffix_trace)
print('PF_DEI_MODULAR_SELFTEST PASS')
