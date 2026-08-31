# CTT causal-temporal PMFS shadow preregistration

This Gate is the first direct comparison of the frozen two-module method with
Classic PMFS.  It is preregistered before reading the measured historical
source scores or localization errors.

The method has not been reduced to a generic confidence Gate.  Its two active
scientific operators are:

1. **Causal physical source operator (M1).**  For every candidate source, use
   the native GADEN response under `do(S=s)` and pass the complete chronology
   through the frozen persistent sensor.
2. **Temporal censored-reachability operator (M2).**  Each completed physical
   stop contributes one right-censored reached/not-reached event.  The eight
   frozen predictive nuisance members are marginalized inside that stop, and
   the resulting evidence is accumulated over completed stops.

Exact arrival phase remains a temporal-resolution ablation because its fresh
cross-wind test was not robust.  This does not remove time from the method:
physical-stop identity, event history, right censoring, sensor memory, update
time, and single consumption are all retained.

## Comparison

The 30 existing H01/H02/H03 seed0--9 PMFS-OFF trajectories are immutable.  At
each of their five real PMFS source-update times, CTRE consumes only
`measured_gas_ppm` and completed stops.  It forms

\[
q_{\mathrm{CTRE},t}(s) \propto q_0(s)
\prod_{b\le t}\left[p_{s,b}^{E_b}(1-p_{s,b})^{1-E_b}\right],
\qquad
p_{s,b}=\frac{\tfrac12+\sum_{m=1}^{8}E_{s,m,b}}{9}.
\]

The native PMFS posterior is not an input to CTRE because both channels have
already consumed the same observations.  Multiplication would double-count
evidence.  Native PMFS is therefore an immutable comparator, while CTRE is a
source-channel replacement from the source-independent geometry prior.

The run is split into two fail-closed stages. Stage 1 can read only the bank,
support geometry, pose, update timing, and `measured_gas_ppm`; it writes and
hashes all 150 FULL and control posteriors. Stage 2 reloads that exact hash
before it may read native PMFS posteriors or `truth_eval_only`. The primary
endpoint is the original PMFS
`ExpectedValue(sourceProbability, 0.05)` error.  Because a carrier assigns an
equal likelihood to all its cells, reverse-cell-order and tie-symmetrized
fractional boundaries are co-primary artifact guards. Sixteen fixed random
tie orders are also reported as sensitivity analysis. Canonical, reverse,
and symmetrized endpoints must all improve by at least 10%.

Two frozen ablations test whether the temporal module adds information rather
than merely counting hits: `COUNT_ONLY` discards physical-stop identity, while
`STOP_LABEL_PERMUTE` destroys the matching between observed and predicted
stops. FULL must have no larger pooled error than either control. Candidate
source-label permutations, including permutations stratified by carrier free
cell count, test whether M1's source-conditioned physics adds information
beyond static geometry.

## Hard decision

`CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_PASS_TO_RUNTIME` requires all 30 final pairs
and all 150 updates, exact native endpoint parity, cell/carrier mass and
online=batch invariants, at least 10% pooled improvement under all three
co-primary endpoint implementations, at least 20/30 improved pairs under all
three, no House worse than -5%, no catastrophic regression, no new
false-confident collapse, temporal-control superiority, and a source-label
permutation probability at most 0.01.

Any failed rule freezes
`CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_NO_GO`.  A PASS authorizes only immutable
runtime integration and the requested H01/H02/H03 seeds1--3 paired 300-second
closed-loop experiment; this fixed-trajectory Gate is not itself called a
closed-loop result.

The machine-readable contract is
`CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_PREREGISTRATION_20260831.json`.
