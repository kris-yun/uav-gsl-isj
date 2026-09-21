# CODEX — DRPE V1 fastest closed-loop pilot

You are implementing a **new method** on top of exact R2. TNQC stays frozen
HOLD.

Branch:

`research/dendritic-resonant-plume-v1`

Base scientific execution commit:

`b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`

Read first:

1. `research/drpe_v1/README.md`
2. `evidence/drpe_v1/OFFLINE_SCREEN_20260921.md`
3. `docs/DRPE_V1_CLOSED_LOOP_PILOT_20260921.md`
4. `research/drpe_v1/drpe_core.py`

## Hard rules

Do not modify TNQC V5.

Do not change:

- 0.1 ppm gas threshold;
- 0.2 s sampling interval;
- periods 1/5/20 s;
- decay_cycles=2;
- ridge alpha=1;
- posterior beta=2;
- score clip=3;
- R2 300-s terminal contract;
- PMFS native likelihood;
- source-update cadence;
- linked-native ExpectedValue endpoint.

Do not add:

- fractional memory;
- adaptive threshold;
- refractory logic;
- branch pruning;
- TNQC;
- predictive-coding residuals;
- another gate.

Those were screened and rejected.

## Phase 1 — reproduce the Python reference

Use the final TNQC R2 evidence archive already available on the VM.

Implement a standalone reproducer that recreates:

- native pooled = 5.555060292 m;
- exponential-onset pooled = 5.524817071 m;
- DRPE onset pooled = 5.502544743 m.

The six DRPE endpoint targets are:

- H01/s0 5.441234760444091
- H01/s1 3.956581812699798
- H02/s0 4.034832886109734
- H02/s1 3.689225685746103
- H03/s0 7.747248202094789
- H03/s1 8.146145112097257

Use the linked-native endpoint for final parity.

If these cannot be reproduced from the repository specification, STOP. Do
not reinterpret the method.

## Phase 2 — freeze the three held-out-House readouts

Before any new seed is run:

- H01 model: train only H02 s0/s1 + H03 s0/s1.
- H02 model: train only H01 s0/s1 + H03 s0/s1.
- H03 model: train only H01 s0/s1 + H02 s0/s1.

Target for training candidates:

`-EuclideanDistance(candidate_center, training_source_truth)`.

Use StandardScaler + Ridge(alpha=1).

Export each model as a plain JSON bundle containing:

- feature order/version;
- scaler mean;
- scaler scale;
- coefficients;
- intercept;
- training cases;
- training source truths;
- SHA256 of training sensor/pose/wind/candidate inputs;
- all frozen DRPE constants.

Commit the three model bundles BEFORE running seed2/3.

After that commit, no retraining is allowed.

## Phase 3 — implement online DRPE

Keep the R2 runtime lifecycle unchanged.

At each 0.2-s gas sample:

```
hit_t = concentration_t > 0.1
onset_t = hit_t && !hit_{t-1}
```

Only `onset_t` drives the resonators.

For P in {1,5,20}:

```
r = exp(-dt/(2*P))
omega = 2*pi*dt/P
z_t = r * exp(j*omega) * z_{t-1} + onset_t
norm_t = r * norm_{t-1} + 1
m_t = abs(z_t)/norm_t
```

Store the 5-Hz pose, wind and three branch envelopes for the current run.

At each native PMFS source update, for each active terminal source leaf:

- compute the exact feature ordering defined by `drpe_core.py`;
- standardize with the frozen held-out-House bundle;
- apply ridge readout;
- z-normalize the scores across the active leaf bank;
- factor = `exp(2 * clip(zscore,-3,3))`;
- multiply the native source posterior cells represented by that leaf;
- normalize the source posterior;
- recompute planner-visible source variance/expected quantities from the
  fused posterior.

Do not change the native candidate simulations.

## Phase 4 — SHADOW parity before closed loop

Run DRPE in SHADOW/replay mode on the existing six development traces.

The online/C++ implementation must reproduce the six reference DRPE endpoints
within 0.011 m linked-native tolerance.

Also export per-candidate scores and compare with the Python reference.

If any case fails, STOP. Fix implementation only; do not alter equations or
constants.

Commit the implementation + SHADOW evidence.

## Phase 5 — independent fastest closed-loop pilot

New test cases only:

- House01 seed2
- House01 seed3
- House02 seed2
- House02 seed3
- House03 seed2
- House03 seed3

Each case has two arms:

- native PMFS
- DRPE FUSED

Total 12 runs.

Ordering:

- seed2: native then DRPE
- seed3: DRPE then native

Use fresh run roots and ROS domains.

Do not use seed0/1 in the pilot verdict.

For every arm preserve:

- terminal RESULT IS;
- Search_t;
- linked-native top-5% endpoint;
- runtime manifest;
- code/binary/launch/model-bundle SHA256;
- sensor/pose/wind traces;
- source-update timing;
- final source posterior.

## Phase 6 — frozen pilot gate

Calculate paired DRPE-vs-native errors over the six new cases.

Promotion requires ALL:

- 12/12 integrity-valid;
- >=4/6 cases improve;
- pooled DRPE error < pooled native;
- pooled reduction >=1.0%;
- no individual case degrades >5%.

Report the result even if it fails.

If HOLD:

- stop;
- do not tune DRPE on seed2/3;
- do not add rejected modules.

If GO:

- stop and upload the complete evidence;
- do not immediately run a larger matrix until reviewed.

## Required final report

Return:

1. implementation commit SHA;
2. three model-bundle SHA256 values;
3. six SHADOW parity errors;
4. 12 terminal RESULT IS lines;
5. six native linked-native errors;
6. six DRPE linked-native errors;
7. six paired improvement percentages;
8. pooled native / DRPE / reduction;
9. improved count;
10. worst degradation;
11. integrity summary;
12. GO/HOLD;
13. complete evidence paths;
14. final Git branch/commit.

Push only to this research branch or a child result branch. Never modify the
V5 release/tag.
