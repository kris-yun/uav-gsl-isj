# Mori–Zwanzig v1 — Gate M0 Dense-History Freeze

Date: 2026-09-24  
Status: **FROZEN BEFORE DENSE W2 GENERATION**

## Goal

Test one mechanism only:

> Does finite-memory reduced dynamics contain source-discriminative information that survives independent turbulent plume realizations and is absent from an otherwise matched Markov reduced model?

This is a physical/mechanistic gate, not the final learned method.

## A. Frozen environment

- House: House02 only for M0 development.
- wind: W2 = `3,5-1_slow`;
- occupancy: same frozen House02 OccupancyGrid3D used by Bi-Green Gate 1A;
- GADEN binary and simulator parameters: same frozen C0.5/Gate-1A contract;
- parent source bank: the exact 630 free PMFS support cells from the independently reviewed Gate 1A bank;
- M0 source subset: **180** candidates selected deterministically from the 630 bank by geometry-only farthest-point sampling, with the exact S2 truth support forced into the set; no plume value or rank is read during selection;
- source z: 0.20 m;
- probes: same 30 source-blind geometry probes;
- probe operator: exact 2x2 average pooling followed by the frozen 30 pooled-grid samples.

Historical HCMC W1 plume/wind traces are excluded from every M0 score.

## B0. Frozen source-subset construction

M0 does not choose 180 candidates by plume behavior. The selector must:

1. read only the 630-source geometry bank;
2. choose the source nearest the geometric centroid as the first farthest-point anchor;
3. iteratively add the point with maximum Euclidean distance to the current selected set, with source_id lexical tie-break;
4. reserve one slot for exact truth `pmfs_3_34`; if it is already selected, continue FPS until 180 unique sources are present; otherwise select 179 by FPS then append `pmfs_3_34`;
5. sort the final source table by source_id only for storage, while retaining an `fps_order` column.

The selector may not read any concentration, score or target rank.

## B. Dense observations

For every source in the frozen 180-source M0 subset generate **three independent W2 realizations**:

- seed R1 = `2026092403`;
- seed R2 = `2026092404`;
- seed R3 = `2026092405`.

Save dense compact probe histories at the native frozen result cadence (0.5 s wherever the verified GADEN output exists).

Do not retain full spatial cubes after compact extraction.

Each compact history must include:

- ordered simulation times;
- 30 pooled probe concentrations;
- source id and xyz;
- RNG seed;
- wind/hash provenance;
- simulator/extractor hashes.

## C. Three-fold cross-realization evaluation

For each held-out seed (R_h):

- reference seeds = the other two seeds;
- held-out target histories = all 180 sources under (R_h);
- candidate models = all 180 source identities, fitted only from their two reference realizations.

Thus each fold evaluates 180 held-out targets against 180 candidate source models.

No held-out realization may be used for model-order or regularization selection.

## D. Matched reduced-state representation

Before fitting source-conditioned dynamics, construct one **global reference-only PCA** using all reference histories from the current fold.

PCA is source-label blind.

Retain the minimum number of components explaining >=95% of reference variance, with:
- minimum 3 components;
- maximum 10 components.

The raw 0.5 s histories are retained, but M0 dynamics are fit on a fixed **2.0 s cadence** (every fourth sample). This lets the frozen memory-order grid test roughly 4–32 s of history without excessive parameter count.

Standardization/PCA parameters are fitted on reference realizations only and then frozen for that fold.

This representation is shared by Markov and memory arms.

## E. Arm 0 — Markov baseline

For each candidate source (s), fit the same ridge-regularized first-order reduced dynamics:

[
z_{t+1}=b_s+A_{s,1}z_t+epsilon_t.
]

No candidate-specific architecture or hyperparameter.

## F. Arm 1 — finite-memory MZ diagnostic

For each candidate source (s), fit:

[
z_{t+1}=b_s+sum_{ell=1}^{L}A_{s,ell}z_{t+1-ell}+epsilon_t,
]

using the exact same fitting code and ridge penalty family as Arm 0.

This is a **finite-memory diagnostic approximation** to an MZ/GLE memory term, not the final innovation.

## G. Hyperparameter selection without target leakage

Global hyperparameters are selected separately inside each held-out fold, using only the two reference seeds.

Candidate grid:

- memory order (L in {2,4,8,16,32});
- ridge (lambda in {10^{-6},10^{-4},10^{-2},1,100}).

Selection procedure:

1. fit on R_ref1 and evaluate one-step prediction on R_ref2 across all 180 M0 sources;
2. fit on R_ref2 and evaluate on R_ref1;
3. average normalized one-step error across all source identities;
4. select one global pair ((L^*,lambda^*)), tie-breaking toward smaller L then larger regularization.

The Markov arm selects its one global (lambda_0^*) using the same reference-seed swap procedure after (L^*) is frozen, and its validation error is measured over the same warm-up interval used by the memory arm.

After selection, refit each candidate model on both reference realizations.

No target rank is inspected during selection.

## H. Candidate score on held-out histories

For a held-out target history, every candidate source model receives the same observed target history as input.

Score by normalized one-step innovation energy after a fixed warm-up of (L^*) samples. Both arms use this same scoring interval; the Markov arm does not gain extra early samples:

[
E_s=
\frac{\sum_t \|z_{t+1}-\hat z_{t+1}^{(s)}\|_2^2}
{\sum_t \|z_{t+1}\|_2^2+10^{-12}}.
]

Lower is better.

Compute true-source rank among all 180 candidate models.

No source-specific amplitude fit, time shift, offset correction, threshold or post-hoc calibration.

## I. Primary gate metrics

Aggregate over all (180\times3=540) held-out source-realization tests.

Report for both Markov and memory arms:

- top-1 source retrieval rate;
- top-3 rate;
- top-10 rate;
- median truth rank;
- mean log truth rank;
- median source-position error of rank-1 candidate;
- held-out one-step normalized prediction error.

Also report the subset of cases where the Markov truth rank >3, but this is secondary and cannot determine PASS alone.

## J. Frozen PASS criteria

M0 PASS requires **all** of the following:

1. **Nontrivial memory:** selected (L^*>1) in all three held-out folds.
2. **Predictive value:** finite-memory median held-out one-step error improves by >=10% relative to Markov in every fold.
3. **Source value:** finite-memory top-3 retrieval rate improves by >=10 percentage points over Markov when pooled over the 540 held-out tests.
4. **Rank value:** finite-memory mean log truth rank improves by >=20% over Markov.
5. **Consistency:** finite-memory improves truth rank in >50% of tests and worsens it in <25% of tests.
6. **No fold collapse:** none of the three folds has lower top-10 retrieval rate than the Markov arm.

If any condition fails:

`MZ_M0_FAIL_STOP_MEMORY_MAINLINE`

If all conditions pass:

`MZ_M0_PASS_MEMORY_IS_LOAD_BEARING`

No threshold may be changed after seeing M0 results.

## K. Interpretation discipline

A lower trajectory-prediction error alone is **not** evidence for the main innovation.

M0 only passes if memory also improves **source identity retrieval** across independent realizations.

If M0 passes, the next stage is not “use a bigger RNN.” It is to derive an MZ source collective variable / memory-kernel objective and test unseen-source generalization before any PMFS closed loop.
