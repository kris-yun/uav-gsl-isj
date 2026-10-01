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

For PMFS cell prism V_i, compute the filament probability mass inside that prism:

q_(i,k,t) = Integral over V_i of Normal(x; mu_(k,t), Sigma_(k,t)) dx.

Combine filament support without introducing a release-rate calibration:

h_(i,t) = 1 - Product_k [1 - q_(i,k,t)]

and simulated hit probability:

Hhat_i = mean_t h_(i,t).

Use the same frozen PMFS likelihood to score candidates. Do not introduce a learned scorer.

## Software controls before truth scoring

All must pass:

1. Tiny-covariance limit approaches the R1 hard point-hit support.
2. Gaussian cell masses stay in [0,1].
3. Occupied geometry cannot receive legal observation mass.
4. Candidate/source draws, center trajectories and CFD queries match R1.
5. Measured map and likelihood code are unchanged.
6. Every covariance parameter is provenance-derived before truth ranks are read.
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
