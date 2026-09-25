# 02 — EXPERIMENT SPECIFICATION

## 1. Scientific contrast

Let `X[s,r,t,p]` denote the frozen R0 observable.

Partition time into 5 contiguous blocks, each 2 time slices.

For fold f, fit block-wise unsupervised transforms only on the 12 reference realizations/source.

For realization r, obtain:

`z[s,r] ∈ R^10`

by concatenating 2 pooled-reference PCA scores per block.

### FULL

The 5 blocks in z come from the same realization r.

This preserves cross-block realization dependence.

### SHUFFLED

Within each source s and reference fold, keep block 0 attached to realization r.

For blocks 1..4, reassign block scores across the same 12 realization IDs using independent derangements.

This preserves every block's empirical marginal sample set exactly but destroys the original block-to-block realization correspondence.

## 2. Why block PCA is frozen this way

The goal is not to discover a powerful representation.

We need a low-dimensional, ordinary model so source-specific full covariance is estimable from 12 reference realizations.

PCA is:

- unsupervised;
- fit on pooled reference only;
- separate per block;
- identical for FULL and null.

Do not use source-supervised LDA, neural encoders, truth coordinates, or test-fitting.

## 3. Gaussian working likelihood

For each source s:

FULL:
- fit mean `μ_s`
- fit OAS covariance `Σ_s`
- evaluate heldout z using MVN log density.

SHUFFLED replicate m:
- make shuffled reference z
- fit its own `μ_s^(m), Σ_s^(m)`
- evaluate the same heldout z.

Uniform prior across sources.

Posterior:

`p(s|z) = softmax(loglik_s(z))`

## 4. Null integrity checks

For every source/fold/shuffle verify:

- each block retains exactly the same multiset of reference block scores as FULL;
- per-block means match to numerical tolerance;
- per-block variances match to numerical tolerance;
- source IDs unchanged;
- eval data unchanged;
- at least 95% of non-anchor block realization pairings differ from FULL;
- the concatenated cross-block covariance differs unless data themselves contain no cross-block covariance.

If null construction changes block marginals, invalidate that shuffle.

## 5. Shuffling implementation

Primary:

- 200 shuffle replicates.
- global seed list frozen in config.
- generate a derangement for each non-anchor block.
- deterministic seed derivation:
  `seed = base_seed + 100000*fold + 1000*shuffle + 10*source + block`

A derangement means `perm[i] != i` for all i.

Do not keep regenerating until a desired result appears.

## 6. CV folds

Frozen eval sets by realization index:

- F0 = [0,4,8,12]
- F1 = [1,5,9,13]
- F2 = [2,6,10,14]
- F3 = [3,7,11,15]

Reference = complement.

Each source follows the exact same index scheme.

## 7. Required controls

Also compute two descriptive controls, not used to rescue the Gate:

### DIAG-COV

FULL z, but force every source covariance to diagonal.

Purpose: see whether any FULL gain is specifically carried by dependence/covariance, not just numerical mean differences.

### BLOCK-PRODUCT

Fit a separate 2D Gaussian per block and sum log-likelihoods across blocks.

Purpose: explicit conditional-independence working baseline.

These are descriptive only. Primary Gate remains FULL vs SHUFFLED.

## 8. No hyperparameter search

Frozen:

- 5 blocks
- 2 PCs/block
- OAS
- uniform prior
- 200 null shuffles
- four folds above

No tuning after seeing results.

## 9. Failure modes to record

- singular/unstable covariance despite OAS
- zero-variance block
- source with degenerate support
- posterior underflow (use log-sum-exp)
- null marginal mismatch
- source dominated by one realization
- missing source coordinates
- input-shape mismatch
