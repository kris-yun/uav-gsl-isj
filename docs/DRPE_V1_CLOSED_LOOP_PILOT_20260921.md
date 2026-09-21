# DRPE V1 fastest closed-loop pilot contract

Date: 2026-09-21

## 1. Scope

This is a **pilot**, not a final claim. DRPE has a 6/6 positive fixed-trajectory
development signal, but only ~0.95% pooled endpoint reduction. The closed-loop
test asks whether feedback through the planner amplifies, preserves or destroys
that signal.

No TNQC component is enabled.

## 2. Freeze before new truth

Before starting seed2/seed3, generate and commit three readout bundles:

- House01 model trained only on House02 seed0/1 + House03 seed0/1;
- House02 model trained only on House01 seed0/1 + House03 seed0/1;
- House03 model trained only on House01 seed0/1 + House02 seed0/1.

Each bundle must contain:

- feature mean/std;
- ridge coefficients/intercept;
- training case IDs and source truths;
- SHA256 of every training trace;
- constants: threshold=0.1, dt=0.2, periods=[1,5,20],
  decay_cycles=2, ridge_alpha=1, beta=2, clip=3.

After bundle hashes are committed, do not retrain from seed2/3.

## 3. Online module

At 5 Hz:

1. threshold measured concentration at 0.1 ppm;
2. emit a spike only on 0->1 whiff onset;
3. update the three fixed resonant states.

At each PMFS source update:

1. use terminal/current active source leaves;
2. compute the frozen 45-D candidate feature from stored pose/wind/resonant
   history;
3. apply the corresponding held-out-House scaler + ridge readout;
4. z-normalize scores across the active candidate bank;
5. multiply native source probability by
   `exp(2 * clip(z, -3, 3))`;
6. renormalize;
7. recompute the planner-visible source distribution/variance from the fused
   posterior.

Do not add adaptive thresholds, branch pruning, refractory logic, fractional
memory, TNQC or extra gates.

## 4. Shadow equivalence check

Before FUSED runs, replay the six development traces through the C++/ROS DRPE
implementation in SHADOW mode.

Required:

- candidate scores match the Python reference within a frozen numeric
  tolerance;
- fused posterior produced offline by C++ matches the reference;
- linked-native endpoint reproduces the six values in
  `evidence/drpe_v1/OFFLINE_SCREEN_20260921.md`.

If not, stop. Do not tune.

## 5. Fastest independent closed-loop test

Use NEW seeds:

- House01 seed2, seed3
- House02 seed2, seed3
- House03 seed2, seed3

For every case run exactly two arms under the same R2 environment:

- Native PMFS
- DRPE FUSED

Total: 12 x 300-s runs.

To reduce ordering bias:

- seed2: Native then DRPE;
- seed3: DRPE then Native.

Run sequentially unless the existing VM has already demonstrated that parallel
ROS domains do not alter timing/resource behavior.

Seeds0/1 are development data and must not enter this pilot verdict.

## 6. Endpoint and integrity

Every arm must have:

- terminal RESULT IS;
- Search_t approximately 300 s under R2;
- linked-native top-5% endpoint;
- runtime/binary/launch/readout SHA;
- no post-budget scientific update.

Record trajectory, sensor and wind traces for later mechanism analysis.

## 7. Pre-registered pilot decision

Because one native H01 repeat already showed ~0.062 m run-to-run endpoint
variation, tiny differences are not treated as proof.

Pilot promotion requires all of:

- 12/12 runs integrity-valid;
- DRPE improves at least 4/6 paired scenario/seed comparisons;
- pooled DRPE error < pooled native error;
- no individual degradation >5%;
- pooled reduction >=1.0%.

A stronger result (>=2% pooled) is preferred before spending effort on a larger
multi-seed publication matrix.

If the pilot fails any gate: **HOLD DRPE V1**. Do not tune these six new cases.

If it passes: freeze DRPE V1 and run a larger independent seed/realization
matrix before publication claims.

## 8. Why this is the fastest defensible route

A single 3-case run is too close to the measured native stochasticity floor.
The 6-case new-seed matrix costs only twelve 300-s arms and is the minimum
reasonable closed-loop check that preserves House coverage and averages some
runtime randomness.
