# Frozen experiment specification

## Data

Use only the already generated R0 benchmark:

- House02
- W2 = `3,5-1_slow`
- 18 frozen source identities
- 16 independent R0 realizations per source
- each `pooled.npy` has shape `10 x 30`

Canonical VM data root:
`/home/zyc/r0_stochastic_benchmark_20260924`

Canonical review archive if preferred:
`/home/zyc/R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz`

Seed matrix:
`research/stochastic_benchmark_refoundation/R0_SEED_MATRIX_18x16.tsv`

No legacy C/D realization enters this experiment.

## Source-blind representation

For one realization with pooled concentration matrix C in R^(10x30), define

`B(t,q) = 1[C(t,q) > 0]`

and the 10-dimensional encounter-count trajectory

`x_t = sum_q B(t,q)`,  t=1..10.

Thus each realization becomes x in {0,...,30}^10.

This is deliberately low-dimensional and uses the R0-supported encounter
object. No concentration amplitude, threshold tuning, covariance fitting,
history length or learned representation is introduced.

## Reference / target splits

Primary cross-fit:
- A: reference replicates 1..8, targets 9..16
- B: reference replicates 9..16, targets 1..8

Robustness cross-fit:
- C: odd replicates reference, even replicates target
- D: even replicates reference, odd replicates target

Each arm uses K=8 reference realizations for every candidate source.

## M0 — deterministic mean prototype

For candidate s:

`mu_s = mean_i x_{s,i}`

Target score:

`D_mean(s,y) = ||y - mu_s||_2`

Lower is better.

This is the deterministic/source-mean comparator.

## M1 — empirical branching distribution

Let reference realizations be X_s={x_s1,...,x_s8}.

Use the multivariate Energy Score:

`ES_s(y) = mean_i ||x_si-y||_2
           - 0.5 * mean_{i,j} ||x_si-x_sj||_2`

Lower is better.

No distribution family is fitted.

## N1 — exact mean-preserving residual reassignment null

For each candidate source:

`r_si = x_si - mu_s`.

The eight residual vectors have exactly zero empirical mean.

For each null repetition, draw a derangement pi of the 18 source IDs and define:

`X_null_s = {mu_s + r_{pi(s),i}}`.

Therefore every candidate keeps **exactly the same 10-D mean mu_s**, while the
source-specific residual/branching geometry is reassigned to another source.

This is the key destructive control.

Run exactly 500 null derangements with RNG seed `2026092602`.

For every null, score all targets under all 18 candidates using the same Energy
Score. Do not generate or tune anything from source ranks.

## Metrics

For each directed split and each method:
- overall top-1 accuracy;
- overall top-3 accuracy;
- mean true-source rank;
- median true-source rank;
- mean reciprocal rank (MRR);
- per-source mean true-source rank.

For each directed split, report:
- M1 minus M0 top-1;
- M0 minus M1 mean-rank improvement.

For the pooled primary A+B targets, report null fractions:
- fraction of N1 nulls with mean true-source rank <= actual M1;
- fraction of N1 nulls with top-1 accuracy >= actual M1.

Repeat the same null audit for robustness C+D as a secondary diagnostic.

## Decision

Exactly one label.

### `STOCHASTIC_BRANCHING_D0_SIGNAL`
All must hold:
1. In both primary directions A and B, M1 mean true-source rank is strictly
   better (lower) than M0.
2. Pooled primary M1 top-1 is not lower than pooled M0 top-1.
3. Pooled primary residual-reassignment null fraction for mean rank <= 0.05.
4. In pooled robustness C+D, M1 mean true-source rank is better than M0.
5. Pooled robustness M1 top-1 is not lower than M0.

Interpretation:
source-specific branching geometry contains development-set source information
beyond the preserved mean. This authorizes a NEW fresh confirmation design,
not a main-innovation claim and not closed loop.

### `STOCHASTIC_BRANCHING_D0_STRONG_SIGNAL`
All SIGNAL conditions hold, and:
- pooled primary null fraction for top-1 <= 0.05;
- pooled robustness residual-null fraction for mean rank <= 0.05.

Interpretation is still development only.

### `STOCHASTIC_BRANCHING_D0_MEAN_ONLY`
M1 may differ from M0, but source-specific residual reassignment is not
distinguishable at the frozen 0.05 gate, or the improvement does not survive
the robustness split.

Interpretation:
the useful stochastic object is primarily the source mean/encounter profile or
generic dispersion, not source-specific branching. Do not build the mainline
around stochastic branching.

### `STOCHASTIC_BRANCHING_D0_NULL_OR_ADVERSE`
M1 is directionally adverse or fails to improve mean rank in either primary
direction.

Interpretation:
stop stochastic-branching world-model mainline.

### `STOCHASTIC_BRANCHING_D0_HOLD_DATA_CONTRACT`
Only for missing/corrupt R0 files, hash/schema mismatch, or failure to reproduce
the frozen 18x16 structure.

## Governance

- R0 data are OPEN and previously inspected; this is explicitly development.
- No hyperparameter may be changed after results are seen.
- No extra source, seed, House or wind may be added to rescue D0.
- No neural model.
- No GADEN run.
- No PMFS run.
- No closed loop.
