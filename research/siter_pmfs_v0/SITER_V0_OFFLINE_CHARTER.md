# SITER-PMFS v0 — offline scientific charter

Date: 2026-10-01
State: FINAL DESIGN BEFORE SIX-CASE SITER SCORING

## Scientific question

Can we obtain cross-House source-ranking gain by keeping PMFS as the stable generalist anchor and learning only a sparse wind-conditioned contradiction factor?

The experiment is not another plume predictor.

## Data

Use the authoritative six-case 300 s VGR/TNQC archive:

- H01 seed0/1
- H02 seed0/1
- H03 seed0/1

Use existing context-bank artifacts only:
- candidate manifests / final active leaves;
- measured_hit_probability.csv;
- candidate_support_alignment.csv or exact candidate hit maps;
- estimated_wind.csv;
- source_update_timing.csv;
- source_posterior.csv;
- map/occupancy metadata;
- evaluator-only source truth.

No new GADEN is required for v0.

## Representation

For every candidate and source update compute a fixed feature dictionary from:

1. PMFS candidate evidence;
2. measured-vs-simulated residual structure;
3. candidate-centered local wind coordinates;
4. map/flow reachability diagnostics that do not use source truth.

Absolute House ID, seed ID, source coordinates and truth distance are forbidden features.

All feature formulas and normalization rules must be frozen before the first outer held-out-House truth is evaluated.

## Model family

Primary v0 model is a sparse non-negative contradiction model:

    C(s) = sum alpha_k c_k(s)
    alpha_k >= 0
    sum alpha_k = 1

Final score:

    l_new(s) = l_PMFS(s) - C(s)

or an algebraically equivalent exp(-C) posterior penalty.

The transport head is not allowed to add positive evidence.

A generic MLP may be run only as a descriptive overfitting control and cannot become the v0 method.

## Fitting

Outer folds:
1. train H01+H02, test H03;
2. train H01+H03, test H02;
3. train H02+H03, test H01.

Within each outer training set:
- use only training-House truth for pairwise candidate supervision;
- choose sparsity/regularization by leave-one-run/source-update validation inside the two training Houses;
- freeze all weights and preprocessing;
- then evaluate held-out House once.

Candidate imbalance must be handled by per-update balanced pairwise ranking or equal update weights, not by duplicating the truth candidate.

## Primary endpoint

For each of the six held-out runs:
- terminal truth-owner leaf midrank;
- truth-vs-best-wrong margin;
- top-5% PMFS expected-location error using the existing validated evaluator.

Compare SITER against Native PMFS on the exact same fixed trajectory/candidate bank.

## GO gate

All are required:

- terminal truth rank improves in >=4/6 runs;
- pooled median truth-rank improvement > 0;
- no run worsens by >10 active-leaf rank positions;
- final top-5% expected-location error improves in >=4/6 runs;
- pooled mean endpoint error improves by >=5%;
- no false-confident collapse created by the SITER posterior;
- H01, H02 and H03 each have at least one improving seed.

Decision labels:

- rank passes but endpoint error does not: SITER_V0_HOLD_RANK_ONLY
- endpoint improves but transfer/rank gates fail: SITER_V0_HOLD_NONTRANSFERABLE
- all gates pass: SITER_V0_CROSS_HOUSE_SIGNAL
- otherwise: SITER_V0_NO_GO_STOP

## Required ablations

Source-blind/frozen before outer truth:
- PMFS only;
- PMFS + invariant/generalist specialist features only;
- PMFS + flow channel only;
- full SITER;
- unconstrained signed linear fusion, diagnostic only.

The full method must outperform or be safer than signed fusion to support the one-sided falsification thesis.

## STOP boundary

After six-case fixed-trajectory evaluation: STOP.

No closed loop unless SITER_V0_CROSS_HOUSE_SIGNAL.
No H03 can be used for development after it has served as held-out fold.
No feature redesign after outer-fold truth is opened.
