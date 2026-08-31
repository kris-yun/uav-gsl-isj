# CTT hierarchical projection V2 preregistration

V1 remains frozen as `CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_NO_GO`.  It produced a
large source-evidence signal but exposed an incomplete resolution interface:
a carrier posterior was spread uniformly over its native PMFS cells, creating
wide posteriors and exact top-five-percent ties.  This V2 is one parameter-free
interface repair.  It does not change the causal or temporal operators.

Let `x` be a free PMFS cell and `B(x)` its frozen carrier.  Let `p_N(x|D)` be
the independently maintained native PMFS shadow posterior and `q_T(B|D)` the
byte-frozen Stage-1 causal-temporal carrier posterior.  V2 is

\[
q_{V2}(x\mid D)
=q_T(B(x)\mid D)
\frac{p_N(x\mid D)}{\sum_{x'\in B(x)}p_N(x'\mid D)}.
\]

This is not a blend.  It completely replaces the native carrier marginal and
retains only native PMFS's within-carrier conditional geometry.  Equivalently,
it is the minimum-KL cell distribution with prescribed CTRE carrier masses.
The inherited PMFS conditional is baseline resolution support, not a third
innovation module.

If CTRE assigns positive mass to a carrier whose native mass is exactly zero,
the whole update must fail closed to native PMFS.  No epsilon, uniform fill,
renormalization, or outcome-dependent exception is permitted.

V2 must reproduce native PMFS under identity carrier marginals, conserve every
CTRE carrier mass, preserve within-carrier native conditionals, and remain
cell-row permutation invariant.  It is evaluated once on all 30 development
trajectories with canonical, reverse, symmetric, and sixteen fixed random tie
orders.  Every tie order must have zero catastrophes; all primary performance,
House, source-label-null, conditional-only, count-only, and stop-permutation
rules in the machine-readable contract must pass.

A PASS authorizes only one immutable runtime implementation and the requested
H01/H02/H03 seeds1--3 paired closed-loop pilot.  Because those seeds already
occurred in V1 development replay, they cannot be called final held-out proof.
