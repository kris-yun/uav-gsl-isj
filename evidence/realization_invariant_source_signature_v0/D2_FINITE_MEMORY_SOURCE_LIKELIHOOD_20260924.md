# D2 — Finite-Memory Source Likelihood

Date: 2026-09-24  
Branch: `research/realization-invariant-source-signature-v0`

Decision: **D2_ADVANCE_FINITE_MEMORY_SOURCE_LIKELIHOOD**

## Purpose

D1 showed that off-diagonal temporal stochastic structure is load-bearing for source ranking. D2 tests a sequential, finite-memory likelihood rather than a static full-covariance score.

This is still a data-only proxy. It is not yet the final Mori–Zwanzig source operator.

## Target-blind memory horizon

The memory horizon is determined only from the independent prediction-realization differences C-D.

For each lag h, compute the mean temporal correlation of per-time-L1 mass-fraction residuals across all sources/probes.

The first non-positive mean correlation occurs at lag 8, so the frozen rule retains lags 1..7.

This rule never reads S2_W2_A/B ranks.

## Rank curve

| Retained memory lags | A rank | B rank |
|---:|---:|---:|
| 0 | 1 | 7 |
| 1 | 1 | 4 |
| 2 | 1 | 5 |
| 3 | 1 | 3 |
| 4 | 1 | 2 |
| 5 | 1 | 2 |
| 6 | 1 | 2 |
| **7 (target-blind rule)** | **1** | **2** |
| 8 | 1 | 2 |
| 9 | 1 | 2 |

The B recovery therefore does not depend on choosing one single target-favorable lag. Once sufficient history is retained, the result plateaus at rank 2.

## Split robustness

Re-estimating memory using only:

- all candidates -> horizon 7 -> A/B = 1/2;
- even-index half -> horizon 8 -> A/B = 1/2;
- odd-index half -> horizon 7 -> A/B = 1/2;
- all candidates except truth -> horizon 7 -> A/B = 1/2.

## Scientific interpretation

The same source under independent stochastic plume realizations cannot be treated as a set of conditionally independent concentration snapshots.

A useful source statistic has two layers:

1. remove realization-dependent absolute plume mass by mapping each time slice to a spatial mass fraction;
2. retain the finite temporal memory of the remaining stochastic morphology in the source likelihood.

This is consistent with a Mori–Zwanzig interpretation:

- resolved object: source-conditioned observation coordinate;
- unresolved object: stochastic filament/plume degrees of freedom;
- projection consequence: history-dependent memory plus orthogonal noise.

## Current architecture candidate

The mainline candidate is now:

**Mori–Zwanzig Non-Markovian Source Inference (working name)**

The PMFS-style source probability map remains the final output, but the likelihood is no longer instantaneous/independent-time. It is computed from a realization-robust projected observation history with a finite memory model.

D0 mass-fraction normalization is not claimed as the main innovation. It is a necessary projection/nuisance-removal component discovered by the data.

## Prior-art boundary

Do not claim novelty for Langevin or generalized Langevin plume modeling: Lagrangian stochastic/GLE models already exist in gas/atmospheric dispersion.

The candidate novelty is the inverse-inference use of Mori–Zwanzig-style non-Markovian memory in arbitrary-source GSL / PMFS likelihood construction.

## Next required gate

Before any closed loop, D3 must falsify this mechanism outside the exact S2_W2_A/B pair.

Minimum D3:

- retain >=143 arbitrary candidate sources;
- add at least one different true source coordinate not used in D0-D2;
- use independent target/prediction plume seeds;
- preferably add another House after the second-source test;
- freeze mass-fraction projection and the target-blind first-zero memory-horizon rule;
- compare raw exact-forward, static D0 signature, diagonal-time model, and finite-memory D2 model.

Advance only if the memory model improves or preserves source rank on every independent target and does not depend on S2-specific tuning.
