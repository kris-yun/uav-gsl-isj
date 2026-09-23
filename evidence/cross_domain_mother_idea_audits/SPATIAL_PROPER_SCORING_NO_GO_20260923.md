# Spatial proper-scoring / field-verification mother idea — six-run kill test

Date: 2026-09-23
Status: **NO-GO AS MAIN SOURCE-EVIDENCE MECHANISM**

## Mother idea

Remote field: multivariate probabilistic weather/climate forecast verification.

Recent anchor:
- Pic, Dombry, Naveau, Taillardat (2025), *Proper scoring rules for multivariate probabilistic forecasts based on aggregation and transformation*, ASCMO 11, 23–58, DOI 10.5194/ascmo-11-23-2025.

The transfer hypothesis is directly failure-informed:

> Native PMFS multiplies independent cellwise agreements. Spatial forecast verification shows that gridpoint-by-gridpoint comparison can incur a double penalty under small spatial displacement and can miss dependence-structure errors. Replacing the pointwise evidence semantics by patch/dependence-aware field scores might recover source identity under stochastic plume displacement.

No method name, posterior construction, or endpoint tuning is used in this screen.

## Frozen inputs

Six accepted independent-plume Native source-update banks:
- H01_R2026092201 / 2202
- H02_R2026092211 / 2212
- H03_R2026092221 / 2222

For each terminal source candidate, the screen uses exactly the exported observed-support table:
- measured hit probability;
- measured confidence;
- candidate simulated hit probability;
- grid coordinates.

Truth enters only after all candidate scores are computed, to identify the terminal candidate whose Native sampled source point is nearest the true source and evaluate its rank.

Terminal leaves are reconstructed from the quadtree rectangle containment relation and reproduce the previously audited counts:
- H01: 121 / 121
- H02: 144 / 135
- H03: 157 / 157

## Frozen score family

No parameter search was performed.

Controls / candidates:
1. Native candidate score.
2. Confidence-weighted pointwise absolute/squared error.
3. Non-overlapping 2x2 and 4x4 patch-aggregated squared error.
4. Overlapping 3x3 and 5x5 neighborhood-aggregated squared error.
5. Variogram-style dependence scores over grid-pair neighborhoods of Chebyshev radius 1 and 2, with confidence and inverse-distance weighting.

Lower loss is better except Native score, which is converted to a lower-is-better negative score.

## Truth-nearest ranks

| Run | Native | Patch 2x2 | Patch 4x4 | Variogram r=1 | Variogram r=2 |
|---|---:|---:|---:|---:|---:|
| H01_R2026092201 | 76/121 | 76/121 | 76/121 | **20.5/121** | **20.5/121** |
| H01_R2026092202 | 77.5/121 | 77.5/121 | 77.5/121 | 63.5/121 | 54.5/121 |
| H02_R2026092211 | 107.5/144 | 101.5/144 | 102.5/144 | 86.5/144 | 86.5/144 |
| H02_R2026092212 | 97/135 | 111/135 | 123/135 | 122.5/135 | 123.5/135 |
| H03_R2026092221 | 105/157 | 150/157 | 105/157 | **157/157** | **157/157** |
| H03_R2026092222 | 104/157 | 149/157 | 104/157 | 155/157 | 154/157 |

The H01 all-miss realization shows that dependence-aware scoring can materially reorder candidates, but that effect does not transfer across Houses or even reliably across the independent H01 realization.

## Direct source-distance association

Representative Spearman(score quality, -source distance):

- H01_R2026092201 variogram r=2: +0.278
- H01_R2026092202 variogram r=2: +0.451
- H02_R2026092211 variogram r=2: **-0.732**
- H02_R2026092212 variogram r=2: +0.044
- H03_R2026092221 variogram r=2: **-0.139**
- H03_R2026092222 variogram r=2: **-0.161**

Thus the dependence-aware field score is not a consistent source-distance ordering.

## Cross-realization candidate-score reproducibility

Spearman correlation on common terminal candidate IDs between the two independent realizations of each House:

| Score | H01 | H02 | H03 |
|---|---:|---:|---:|
| Native | +0.987 | +0.997 | +0.996 |
| Patch 2x2 | +0.987 | **-0.414** | +0.996 |
| Patch 4x4 | +0.987 | **-0.366** | +0.996 |
| Variogram r=1 | -0.193 | **-0.530** | +0.979 |
| Variogram r=2 | +0.276 | **-0.534** | +0.991 |

The H02 independent-realization inversion is decisive: the proposed spatial verification semantics are not recovering a stable source-conditioned compatibility ordering.

## Interpretation

The mother idea correctly diagnoses one weakness of Native PMFS: pointwise field comparison can be overly sensitive to spatial displacement and ignores spatial dependence.

However, this is not the dominant failure in the accepted independent-plume source-update banks.

The H02/H03 results show that the deeper problem is upstream:

> the candidate forward field itself often does not place the truth-nearest source hypothesis in a source-identifying relation to the measured field.

Changing only the field verification metric therefore cannot repair the source identity.

## Decision

**SPATIAL PROPER-SCORING / FIELD-VERIFICATION TRANSFER = NO-GO AS THE MAIN INNOVATION.**

Do not tune:
- patch size;
- variogram radius/order;
- confidence exponent;
- pair-distance weights;
- House-specific score mixtures

on these six runs.

The idea may remain useful later as:
- an auxiliary verification metric;
- a robustness diagnostic for a corrected forward model;
- a double-penalty-resistant ablation.

The next mother mechanism should act **upstream of the comparison rule**, on the PMFS forward-model discrepancy itself or on a genuinely different source-information channel.
