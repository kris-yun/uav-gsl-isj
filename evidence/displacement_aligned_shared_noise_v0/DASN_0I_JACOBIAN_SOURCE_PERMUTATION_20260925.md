# DASN 0I — Source-Permuted Jacobian Specificity Control

Date: 2026-09-25

Status: **LOCAL JACOBIAN HAS SIGNAL, BUT SPECIFICITY IS NOT YET ROBUST ENOUGH**

## Null

Keep every learned Jacobian numerically unchanged, including its singular scales and conditioning, but randomly reassign source labels.

The same source permutation is used for odd/even views, preserving a generic paired 2D sensitivity structure while destroying the match between a source's plume residual and its own local source-response derivative.

300 source permutations are used per 8/8 direction.

## Direction A

- true local-J T_J = 0.24425 m^2;
- permuted-J null mean = 0.09332 m^2;
- null median = 0.08270 m^2;
- null q2.5/q97.5 = -0.07365 / 0.47243 m^2;
- exceedance = 13/300.

The true local J is stronger than most random source Jacobians, but the null has a wide upper tail.

## Direction B

- true local-J T_J = 0.50227 m^2;
- permuted-J null mean = 0.10892 m^2;
- null median = 0.11116 m^2;
- null q2.5/q97.5 = -0.21037 / 0.42953 m^2;
- exceedance = 1/300.

## Interpretation

A source's correct local sensitivity appears to matter, especially in the reverse realization split.

However, generic source-sensitivity subspaces themselves can induce positive paired pseudo-displacement because the underlying plume residual is shared across views.

Therefore the source-permutation control does not yet justify a source-specific displacement-aligned mechanism.

Next mini-step: **DASN-0J neighboring-source Jacobian mismatch control**, which preserves local spatial similarity and is a stricter specificity test.