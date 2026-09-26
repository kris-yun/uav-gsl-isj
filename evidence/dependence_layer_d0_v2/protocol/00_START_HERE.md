# DEPENDENCE-LAYER D0 V2 — mean-field / instantaneous-joint / cross-time-joint decomposition

Date: 2026-09-26

Status: **OPEN development analysis only**.

This supersedes the unexecuted `STOCHASTIC_BRANCHING_D0_20260926` scientific
gate. The old package is retained as history but must not be executed as the
world-model licensing test.

No new plume simulation.
No PMFS closed loop.
No neural network.
No new source/wind/House.
No result-driven model choice.

## Why V2 exists

Independent review identified two valid confounds in V1:

1. preserving only the 10-dimensional mean encounter-count trajectory does not
   preserve the complete 10x30 source-specific mean encounter field
   `p_s(t,q)`;
2. cross-source residual reassignment can leave the physical count support
   `{0,...,30}` and is not a clean physical/exchangeable branching null.

V2 removes both confounds by using **within-source replicate permutations only**.

The question is now:

> After preserving all source-specific binary encounter marginals, which
> additional dependence layer, if any, changes source identification on the
> existing 18-source R0 development panel?

The three nested information layers are:

L0. complete binary mean encounter field `p_s(t,q)`;
L1. each-time spatial snapshot/count distribution;
L2. cross-time realization pairing of count trajectories.

A positive L2 result is NOT yet a stochastic-world-model claim. It only
licenses fresh confirmation of cross-time dependence as a candidate scientific
object.
