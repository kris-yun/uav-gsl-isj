# Biological kinetic-proofreading transfer — six-run necessary-phenomenon screen

Date: 2026-09-23  
Branch: `research/cross-domain-mother-idea-audits-20260923`  
Status: **NO-GO AS MAIN SOURCE-EVIDENCE MECHANISM**

## Purpose

Test the necessary phenomenon required by the previously proposed biological adaptive-discrimination / kinetic-proofreading transfer before designing any localization posterior.

The intended transfer was:

> a source hypothesis should accumulate repeated compatible evidence across causal StopAndMeasure blocks and only become strongly activated after multi-stage confirmation, analogous to nonequilibrium kinetic proofreading.

This screen asks only whether source-near PMFS candidates actually receive more persistent repeated confirmation than wrong candidates.

No endpoint error is optimized and no truth enters the score.

## Frozen inputs

Six accepted independent Native runs:

- H01_R2026092201
- H01_R2026092202
- H02_R2026092211
- H02_R2026092212
- H03_R2026092221
- H03_R2026092222

Each run contributes:

- the 88 StopAndMeasure blocks before source update 1, parsed from the launch log;
- exact block hit/miss using the Native 0.1 ppm threshold;
- block position from the state-machine start / last issued navigation goal;
- the exported source-update candidate support alignment;
- terminal quadtree leaves only for source-identity evaluation.

The block positions map to candidate-support grid cells with maximum nearest-cell error only about 0.036–0.087 m over the six runs.

## Source-blind block evidence

For each candidate s and measurement block t, use the exported candidate hit probability p_s(x_t) at the actual block position and the observed Native block hit h_t.

The per-block Bernoulli log evidence is:

`ell_t(s) = h_t log p_s + (1-h_t) log(1-p_s)`

with only numerical clipping at 1e-6.

A source-blind relative confirmation is declared when the candidate's block evidence is strictly above the candidate-ensemble median for that same block.

The following predeclared persistence diagnostics were evaluated:

- total above-median confirmation count;
- maximum consecutive confirmation run;
- number of K-consecutive confirmation chains for K = 2, 3, 4;
- ordinary cumulative block evidence as a non-proofreading control.

Source truth is used only after all scores are frozen to rank the terminal leaf nearest the true source.

## Result

Terminal-leaf truth-nearest ranks:

| run | terminal leaves | observed hit blocks / 88 | cumulative evidence rank | max-run rank | K=2 rank | K=3 rank | K=4 rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| H01_R2026092201 | 121 | 0 | 1 (69-way tie) | 1 (121-way tie) | 1 (121-way tie) | 1 (121-way tie) | 1 (121-way tie) |
| H01_R2026092202 | 121 | 2 | 27 (69-way tie) | 37 (85-way tie) | 37 (85-way tie) | 1 (121-way tie) | 1 (121-way tie) |
| H02_R2026092211 | 144 | 52 | 78 | 74 | 74 | 74 | 74 |
| H02_R2026092212 | 135 | 70 | 103 | 93 | 102 | 102 | 102 |
| H03_R2026092221 | 157 | 24 | 149 | 100 | 100 | 100 | 100 |
| H03_R2026092222 | 157 | 24 | 149 | 100 | 100 | 100 | 100 |

The H01 apparent rank-1 entries are degenerate ties, not localization success.

Candidate-score association with closeness to truth is also wrong-signed or negligible in the informative Houses:

- H02_R2026092211: roughly -0.84 Spearman for cumulative/persistence metrics;
- H02_R2026092212: roughly -0.36 to -0.69 depending persistence metric;
- H03 repeats: roughly -0.12 to -0.17 for persistence metrics.

## Time-order destruction control

H02_R2026092212 does contain a genuinely order-dependent confirmation streak for the truth-nearest candidate:

- real K=2/3/4 chain counts = 7 / 6 / 5;
- 100 source-blind block-order shuffles never matched those counts.

But the truth-nearest candidate is still only about rank 102/135 under those same K-chain scores.

This is the decisive distinction:

> temporal clustering exists, but the clustering is not source-identifying.

The mechanism therefore fails for the same scientific reason as prior temporal false leads: nontrivial time structure alone is insufficient if it does not select the correct source hypothesis.

H03 is even more direct: in both independent realizations, the truth-nearest terminal candidate receives zero above-median proofreading confirmations and remains about rank 100/157.

## Low-information behavior

H01_R2026092201 correctly collapses to broad abstention: all candidates tie on the proofreading activation metrics because all 88 Native blocks are misses.

That is mathematically safe, but it does not create source information.

## Decision

**BIOLOGICAL KINETIC-PROOFREADING TRANSFER = NO-GO AS THE MAIN SOURCE-EVIDENCE MECHANISM.**

Do not tune:

- K;
- reset/decrement rules;
- confirmation thresholds;
- House-specific parameters;
- hit threshold;
- block subsets

on these six runs to rescue the line.

The necessary phenomenon required by the architecture decision — source-near candidates survive repeated evidence more consistently across independent realizations — is absent.

The biological idea may remain conceptually useful for an auxiliary commitment/abstention gate after a genuinely source-identifying evidence mechanism exists, but it is not load-bearing here.
