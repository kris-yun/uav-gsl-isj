# R2C operational freeze, before any R2C discovery score

Scientific protocol commit: 7967491d57af26875ce07ed6aac093c28879410c.
No scientific thresholds or inputs changed. Primary 64 binary 10x30 tensors,
K=3, time t/9, spatial B/sqrt(30), prepended zero, sigma=1, dyadic_order=1.

## Public numerical conventions

Reference https://github.com/crispitagorico/sigkernel commit
40a583155ea8d2194af0e90dddab37e2659cfcfd. RBFKernel uses
exp(-squared_distance/sigma), hence exp(-squared_distance) here. The default
non-naive PDE recurrence uses second-order correction d^2/12, with each static
mixed increment repeated 2x2 and divided by 4. Numba float64, no fastmath,
serial fixed summation. The unmodified public pure-Torch solver supplies
independent synthetic parity; no dependency or ROS environment is modified.
Parity tolerances absolute/relative 1e-10; Gram PSD tolerance 1e-10*max(1,norm2).
Two full scientific repeats must have exactly identical exported bytes.

## Q Monte Carlo, frozen identifier convention

NumPy PCG64 via SeedSequence([2026093201, context_index, candidate_source_index,
target_replica, alternative_omission, channel]); context/source zero-based,
replica/omission 1..4. Channel 0: Q-target draws; channel 1 and 2: independent
Q-self pair draws. Each stream generates 4096x10 int64 draws uniformly in 0..2.
The first 2048 are primary; all 4096 audit convergence, never rescue primary.
Same-time complete snapshots selected together; no scalar-probe reshuffling.
Truth references omit target replica, alternative references omit designated
replica. Truth Q is independently keyed to each alternative-omission view;
therefore all 256 comparisons and 512 candidate evaluations are recalculated.

## Explicit truncated anatomy (descriptive only)

Use exact piecewise-linear Chen tensor signatures in the same augmented R31
coordinate path: level1, cumulative <=2, cumulative <=3, unweighted Euclidean
tensor inner products. This linear-coordinate feature map is distinct from the
primary RBF RKHS signature; no claim that truncation decomposes the RBF kernel.
Integrate the empirical snapshot-product Q law exactly by conditional Chen
recursion over three present-snapshot states, independently verified by full
enumeration on a fixed 27-path synthetic example. This is numerical integration
of Q, not a Markov model of the physical plume. Raw score uses the same fair-U
K=3 formula. Exact Q mean-signature norm gives independent-Q self expectation.
No target-based level selection or effect rescue is allowed.

At level1 the endpoint marginal is unchanged by Q. A nonzero RAW-U versus
empirical-Q residual can still occur due to finite-reference diagonal/self-term
differences. Export it as prescribed; do not call it cross-time information.
Positive primary residual by itself is neither calibrated likelihood nor PMFS
posterior, and failure of one Variogram score does not rule out every pairwise
model. Scientific result remains discovery-only.
