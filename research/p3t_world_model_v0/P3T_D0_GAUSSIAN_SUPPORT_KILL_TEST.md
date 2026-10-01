# P3T-D0 — Physically grounded 3-D Gaussian-support kill test

Date: 2026-10-01
State: PRE-REGISTERED DEVELOPMENT TEST
Execution: run only after R1P5 has completed and stopped.

## Scientific question

R1 restored xyz filament transport but retained a hard observation rule: a filament contributes a hit only when its point center occupies the original PMFS xy cell and the sensor's exact 3-D voxel layer.

R1 produced:
- identical Oracle-2D and Oracle-3D truth log scores in 4/4 cases;
- zero truth-template support at confident observation cells in both oracle arms;
- increased truth-tie plateaus in Oracle-3D.

GADEN/Gaden-RT instead represents each physical filament by a 3-D Gaussian distribution whose support grows under diffusion.

D0 asks:

If the exact same 3-D center trajectories are represented as physical Gaussian filaments rather than point hits, does 3-D transport begin to create positive evidence for the true source instead of only suppressing false sources?

This is a representation kill test. It is not world-model training.

## Frozen inputs

Exactly the same four historical R1 terminal cases, candidate leaves, measured hit/confidence maps, static CFD state0, occupancy, source heights, deterministic source draws and transport seeds as R1.

No H03.
No new GADEN.
No new plume realization.
No new trajectory.
No training.

## Arms

A — R1 Oracle-3D Point:
read frozen R1 output as the control.

B — Oracle-3D Gaussian:
use exactly the same emitted filament centers and center dynamics as R1 Oracle-3D.

The only scientific change is the filament representation / observation operator.

For filament k at time t:

X_(k,t) follows Normal(mu_(k,t), Sigma_(k,t))

where:
- mu_(k,t) is the exact R1 3-D filament-center trajectory;
- Sigma_(k,t) is derived from the historical GADEN/Gaden-RT diffusion configuration associated with the dataset;
- no covariance parameter may be fitted to source truth, rank, margin or R1 result.

If one physically supported covariance schedule cannot be recovered from existing configuration/provenance, D0 is INVALID/STOP. Do not tune sigma.

Important semantic correction:

A GADEN Gaussian filament is a continuous gas-concentration distribution, not a random point whose cell-membership probability should be combined with an invented union rule. D0 must therefore use the native physical concentration semantics.

For each frozen PMFS query location x_i and timestep t, compute only the on-demand concentration contributed by the Gaussian filaments:

C_i,t = Sum_k C_k(x_i ; mu_(k,t), Sigma_(k,t), filament_mass)

using the historical GADEN/Gaden-RT concentration equation and the provenance-recovered filament mass and diffusion schedule.

Convert concentration to a hit using exactly the same fixed gas-detection threshold that was used to define the measured PMFS hit/miss observations:

hit_i,t = 1 if C_i,t >= C_detection, else 0.

The simulated hit probability is the temporal hit frequency:

Hhat_i = mean_t hit_i,t.

No dense 3-D concentration volume is required: concentration is queried only at the frozen PMFS observation/grid locations, following the on-demand Gaden-RT principle.

Filament mass, diffusion parameters and C_detection must all come from frozen historical configuration or sensor provenance. None may be selected by looking at source rank or truth location. If a unique compatible set cannot be recovered, D0 is INVALID/STOP rather than calibrated after the fact.

For mechanism diagnostics only, also export continuous concentration support and the number of confident observation cells with nonzero Gaussian concentration. These diagnostics cannot replace the frozen hit-probability score.

Use the same frozen PMFS likelihood to score the resulting hit-probability maps. Do not introduce a learned scorer.

## Software controls before truth scoring

All must pass:

1. Tiny-covariance synthetic unit test recovers the expected point-support behavior under a controlled single-filament case; this is a software test, not a claim of exact equivalence to R1's discrete collision rule.
2. On-demand Gaussian concentration matches an independent implementation of the historical GADEN/Gaden-RT concentration equation.
3. Filament mass, diffusion schedule and gas-detection threshold are provenance-recovered before truth evaluation.
4. Occupied geometry and outside-volume handling follow the frozen R1 geometry contract; no source-specific repair is allowed.
5. Candidate/source draws, center trajectories and CFD queries match R1.
6. Measured map and PMFS likelihood code are unchanged.
7. Deterministic repeat is byte-identical or numerically identical under a frozen tolerance.

## Primary gate

A useful representation must create positive truth evidence. Merely suppressing another false source is insufficient.

P3T_D0_GAUSSIAN_SUPPORT_POSITIVE requires all:

- Gaussian truth log score is greater than Point truth log score in at least 3/4 cases.
- Truth rank improves in at least 3/4 cases.
- Median active-leaf truth-rank improvement is at least 10 positions.
- Truth-tie count decreases in at least 3/4 cases.
- Truth-vs-best-wrong source margin improves in at least 3/4 cases.
- No more than one case has worse truth rank.

If truth log score improves in fewer than 3/4:
P3T_D0_NO_POSITIVE_TRUTH_SUPPORT_STOP.

If truth support improves but the rank gate fails:
P3T_D0_HOLD_SUPPORT_NOT_DISCRIMINATIVE.

If physics/provenance/integrity fails:
P3T_D0_INVALID_STOP.

## Required diagnostics

Per case:
- Point vs Gaussian truth log score;
- Point vs Gaussian truth midrank and pessimistic rank;
- number of confident observation cells with nonzero truth support;
- truth-template total support;
- equal-score wrong-leaf count;
- truth-vs-best-wrong margin;
- source-map entropy;
- top-5 candidate IDs;
- runtime and memory.

Representation diagnostics:
- active Gaussian count over time;
- equivalent dense 3-D voxel count;
- storage/computation ratio;
- query cost at the frozen PMFS observation cells.

## Stop boundary

After D0 decision: STOP.

A positive D0 authorizes only D1: persistent 3-D Gaussian state across source updates / partial observations.

D0 does not authorize:
- neural world-model training;
- H03;
- confirmation;
- new GADEN plume generation;
- PMFS/ROS closed loop;
- real flight.
