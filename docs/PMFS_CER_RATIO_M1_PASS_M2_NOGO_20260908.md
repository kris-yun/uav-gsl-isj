# PMFS contrastive causal-event evidence: seed12 House123 result

Status: **M1_DEVELOPMENT_PASS_M2_NO_GO_NO_MULTISEED**.

The campaign used one exposed development seed (12), three Houses, three
nested arms, a 240 s horizon, corrected House-specific geometry and audited
wind/GADEN bindings.  All nine arms reached the intended horizon.  The tested
binary SHA-256 was:

`62df6d257bda7123dea67c3142b877fc3b8a8d8550012c18bfd3f456925ee533`.

## Failure-derived mechanism

The preceding event-likelihood version failed because it treated an absolute
filament visit frequency as the calibrated probability of a delayed FOPDT
sensor block crossing `0.1 ppm`.  A separate 252-case forward screen confirmed
the diagnosis: the source-conditioned physical/FOPDT model beat a source-free
context on NLL and Brier in 3/3 Houses, but lost to short-horizon persistence in
3/3 Houses.

The repaired M1 does not replace the reliable shared temporal prediction.
For completed sensing intervention `a_i`, prior observed block `y_(i-1)`, source
candidate `s`, and source-agnostic context response `c`, it uses the fixed unit
odds-ratio update

`logit p_i(s) = logit p_persist(y_i | y_(i-1)) + logit p_sim(y_i | do(s),do(a_i)) - logit p_context(y_i | do(a_i))`.

The context is the deterministic, candidate-permutation-invariant mean response
over the first-level candidate set.  A candidate whose simulated response is
indistinguishable from context contributes no source-specific shift.  Each
completed `StopAndMeasure` block enters once; spatial PMFS propagation is not
recounted as independent evidence.  The unit coefficient was fixed before the
closed loop.  On the 252-case cross-House predictive screen it improved both
NLL and Brier over persistence in 3/3 Houses without House-specific fitting.

This is best described as contrastive interventional evidence with systematic/
target-responsive decomposition.  It is stronger than the previous absolute
likelihood but the present experiment does not by itself prove a new general
causal-identifiability theorem.

M2 used the same M1 equation but marginalized likelihood over three reproducible
native transport members.  No planner weight or House-specific switch changed.

## Closed-loop results

Positive values are improvements over the nested comparator.

| House | A0 final (m) | M1R final (m) | M1M2R final (m) | M1 final gain (m) | M1 AUC gain (m s) | M2 final gain (m) | M2 AUC gain (m s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| H01 | 4.1162 | 2.8511 | 7.6934 | +1.2651 | +50.6324 | -4.8423 | -530.6679 |
| H02 | 3.4827 | 1.4710 | 1.7492 | +2.0117 | +103.4767 | -0.2781 | -0.5358 |
| H03 | 7.6468 | 8.7102 | 6.0879 | -1.0634 | +14.3007 | +2.6223 | +145.4383 |

### M1 gate

- final error improved in 2/3 Houses;
- distance-error AUC improved in 3/3 Houses;
- mean final improvement: `+0.7378 m`;
- mean AUC improvement: `+56.1366 m s`;
- verdict: **PASS** for the exposed House123 seed12 development gate.

The causal chain is real: the new event evidence changes the posterior and the
unchanged PMFS controller produces different trajectories.  This is not yet an
independent multiseed confirmation or universal cross-dataset claim.

### M2 gate

- final error improved in 1/3 Houses;
- distance-error AUC improved in 1/3 Houses;
- mean final improvement: `-0.8327 m`;
- mean AUC improvement: `-128.5885 m s`;
- verdict: **NO-GO; do not expand this M2 to more seeds**.

M2 is not uniformly useless: it gives a large H03 gain.  Its failure pattern
shows that uniform Monte-Carlo marginalization is not a transport-regime model.
It can let one high-likelihood random member dominate candidate evidence in H01,
while H03 needs alternate transport support.  More replicas would reduce Monte-
Carlo noise but would not identify when structural transport alternatives are
required.

## Next M2 requirement

Keep the now-passing M1 frozen.  Replace uniform random-member marginalization
with an explicit persistent transport-regime posterior or a preregistered robust
member-consensus score.  Before another full closed loop, the new M2 must expose
per-member source/context log ratios and pass a replay gate showing that its
aggregation improves calibration without letting a single member dominate.
House-specific activation, planner rescue tuning and extra seeds are not
authorized by this result.

### Immediate M2 failure probe

One additional H01-only probe corrected a plausible decomposition error: the
source-agnostic context was recomputed separately inside each transport member
before marginalization, preventing regime-wide response scale from becoming
source evidence.  The probe used binary SHA-256
`4a9b22384f48fcf6217ea3264402e6de09181314b0e2656e5e2b6892739b9131`.

It did not repair M2.  H01 final error remained `7.6934 m` (increment versus
M1R `-4.8423 m`) and AUC was `1805.7092 m s` (increment `-523.8846 m s`).
The run therefore stopped at H01; H02/H03 and further seeds were not launched.
This falsifies context pooling as the main M2 failure.  The three members are
Monte-Carlo realizations around one fixed estimated wind field, not distinct
structural transport regimes.  The next M2 must change the physical member
definition (for example, persistent measured-wind regimes with an explicit
online regime posterior), and pass an offline predictive-ratio gate before any
additional closed loop.

## Evidence

- Formal gate: `evidence/cstar_cer_ratio_house123_seed12_20260908/CSTAR_CER_RATIO_HOUSE123_SEED12_GATE.json`
- Nine raw run folders: `evidence/cstar_cer_ratio_house123_seed12_20260908/H0*_seed12_*`
- Predictive screen: `evidence/cstar_sensor_hit_screen_20260908/SENSOR_HIT_GATE.json`
- Frozen screen producer: `experiments/ctpi_cstar/screen_sensor_hit_probability.py`
- Closed-loop evaluator: `tools/cstar_evaluate_cer_house123.py`
- H01 member-context negative probe: `evidence/cstar_cer_ratio_memberctx_h01_seed12_20260908`
