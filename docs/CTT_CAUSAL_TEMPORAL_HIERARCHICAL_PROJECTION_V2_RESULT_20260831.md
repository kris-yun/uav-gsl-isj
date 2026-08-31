# CTT causal-temporal hierarchical projection V2 result

## Terminal state

`CTT_CAUSAL_TEMPORAL_HIERARCHICAL_PROJECTION_V2_NO_GO`

This is a frozen fixed-trajectory development result, not a closed-loop or
held-out claim.  Runtime integration and the requested paired 300 s pilot are
not authorised by the preregistered V2 Gate.

## Integrity

- scientific preregistration commit: `5832cfe7b60a62302699cbb80637b26d9735d269`
- final execution freeze commit: `685475ba943fb2f5f1719b5e56aff53b951f79f2`
- evaluator SHA-256: `29171c4fb64e9388ac01aa9dd0a049ffd8d3723d7c034ee15ea97703cfae37d3`
- run-freeze SHA-256: `3b78f3aba0cc0e381b9f8ff42065cef80f0abc41d138fccf79bea8eb25d8d3ef`
- frozen Stage-1 semantic posterior SHA-256:
  `95d68bf4078fa6117a0555acfad78f827a5c51f4b69d2a55869c5dca16f65032`
- all 150 native PMFS posteriors and 30 truth-bearing case results matched
  their byte hashes preserved in the V1 summary.
- identity reconstruction, carrier marginal, within-carrier conditional,
  total mass, fail-closed, row-permutation and native endpoint parity
  invariants all passed.
- no GADEN run and no neural training were performed.

R1 terminated before aggregation because the final-endpoint parity accumulator
was incorrectly included in the next run's projection-invariant loop.  The R1
INVALID artifact was retained.  The failure category was fixed with a direct
cross-run regression test, a new evaluator commit and a new run-freeze before
R2 was run.  No scientific formula, threshold, arm or Gate changed.

## Primary result

For the canonical PMFS endpoint over H01/H02/H03 seeds 0--9:

| Scope | PMFS mean error | V2 mean error | Pooled improvement | Improved pairs |
|---|---:|---:|---:|---:|
| all 30 | 5.1823 m | 2.6074 m | 49.6864% | 27/30 |
| H01 | 5.0013 m | 4.1013 m | 17.9962% | 8/10 |
| H02 | 3.2229 m | 1.5622 m | 51.5283% | 9/10 |
| H03 | 7.3228 m | 2.1588 m | 70.5195% | 10/10 |

The reverse and symmetric exact-tie endpoints retained 48.3801% and 49.0036%
pooled improvement respectively, each with 27/30 improved pairs.  Both the
unrestricted and equal-free-cell-count-stratified source-label permutation
nulls gave empirical upper-tail `p = 1/257 = 0.00389105` in all three primary
tie endpoints.

These data establish a strong joint causal-temporal source-evidence signal on
the opened fixed trajectories.  They do not satisfy the complete safety and
mechanism Gate.

## Failed preregistered rules

Exactly two rules failed:

1. `catastrophes_every_tie_mode = false`.  H01 seed 3 remained a catastrophe:
   canonical PMFS error `2.6117 m` versus V2 `4.0996 m`.  Its full CTRE true
   carrier rank improved from native `206.5` to `46.0`, but the spatial mass of
   better-ranked wrong carriers moved the PMFS top-five-percent estimator away
   from the true source.  Thus better exact-carrier ordering was not sufficient
   for a safe metric-level update.
2. `full_no_worse_than_count_only = false`.  Canonically FULL was slightly
   better than COUNT_ONLY (`78.2223 m` versus `78.9942 m` total), but the result
   reversed under at least one frozen tie endpoint.  The stop-resolved temporal
   identity component therefore did not supply tie-robust incremental value
   beyond exchangeable reached/not-reached counts.

The three canonical regressions were H01 seed 0 (`5.8455 -> 6.1969 m`), H01
seed 3 (`2.6117 -> 4.0996 m`) and H02 seed 8 (`2.1607 -> 2.2836 m`).

## Evidence hashes

- `SUMMARY.json`: `36bd50881f19bb6119e28a8444908bed8e5058ed14151dd253ece65350107f98`
- `FINAL_PAIRS.csv`: `4ecf7caa8d0d14281e95b030ff3d3db74025e0c2b6327b0bb5dabfd72c161cb5`
- `UPDATES.csv`: `d56c9dec67a2cf196b8e43bda3c15831ba836c77169dae8098c3e7d716249d64`
- `VERDICT.txt`: `9a62ff3b9c3cea41fa76acbdfeec2ba9d8b502147f491bd42d709b70e188b015`

The evidence directory is
`CTT_CAUSAL_TEMPORAL_HIERARCHICAL_V2_EVIDENCE_20260831_R2`.
