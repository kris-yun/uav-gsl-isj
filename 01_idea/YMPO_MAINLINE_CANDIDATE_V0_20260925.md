# YMPO v0 — Young-Measure Plume Operator

Date: 2026-09-25

Status: **D0_ADVANCE_MAINLINE_CANDIDATE / NO NEW SIMULATION AUTHORIZED**

## 1. Main scientific object

Classical plume/world-model approaches assign a point value or a small parametric uncertainty object to each spatial query:

  x -> c(x)   or   x -> (mean(x), variance(x)).

YMPO instead represents turbulent plume transport by a spatial field of local probability measures:

  x -> nu_x,

where nu_x is the local concentration law under repeated turbulent realizations / short-time sampling.

For source s and environment E, the forward object is a measure-valued operator

  G_E^YM : s -> {nu_{s,E,x}}_x.

The inverse PMFS task remains a normalized posterior over the original source cells.

## 2. Mother theory

The main far-domain inspiration is Young-measure / measure-valued descriptions of stochastic transport and turbulent PDEs.

A direct 2026 theoretical anchor is:

F. Butori, F. Flandoli, E. Luongo, Y. Tahraoui,
'Background Vlasov equations and Young measures for passive scalar and vector advection equations under special stochastic scaling limits',
Probability Theory and Related Fields, 2026, DOI 10.1007/s00440-026-01471-3.

The paper shows that non-trivial Young measures can retain fluctuation/oscillation information beyond the deterministic diffusive limit for passive scalar/vector stochastic transport.

This is a mother-theory analogy, not a claim that GADEN satisfies the paper's special scaling-limit assumptions.

## 3. Why this is not ordinary mean+variance gas mapping

Gas distribution mapping already contains mature mean maps, variance maps, Gaussian process mixtures, Kernel DM+V and GMRF uncertainty maps.

YMPO is only distinct if the full local distribution shape beyond mean/variance is load-bearing for source inference.

D1R directly tests that condition.

## 4. D1R same-source fresh-realization evidence

Using the identical 6-fit / 2-train-only-calibration / 8-fresh protocol with ordinary shrinkage LDA:

- per-probe mean log-concentration only: fresh proper score -3.215 / -3.387 bit;
- per-probe mean+std+hit/intermittency: -2.129 / -2.177 bit;
- per-probe empirical-distribution summary (mean,std,q25,q50,q75,max,hit): -2.006 / -2.040 bit.

Thus replacing a point-valued mean field with local distribution statistics recovers more than one bit/target of fresh source information.

Mean, width and zero mass are complementary; no one statistic alone explains the gain.

## 5. Temporal-order quotient evidence

Source information does not require the exact order of the ten short-time samples:

- full ordered 10x30 log-ppm and
- independently sorted ten amplitudes at every probe

have essentially identical fresh pairwise / posterior performance.

Therefore the stable object is much closer to a local empirical measure than a short path trajectory.

## 6. Global-histogram negative control

Pooling all 30 probes into one global empirical concentration distribution collapses fresh performance to roughly -4.75 / -5.00 bit and top1 about 26%.

Therefore the object is not a single concentration histogram.

It is a **spatial field of local measures**.

## 7. Generic measure-method negative controls

Using the same D1R contract:

- RBF kernel mean embedding + LDA: about -2.79 / -2.77 bit;
- discrete zero+amplitude histogram + LDA: about -2.74 / -2.66 bit;
- direct Wasserstein template posterior: about -3.77 / -3.81 bit;
- direct Hellinger/Bhattacharyya histogram posterior: about -3.72 / -3.63 bit;
- quantile-function functional PCA + LDA: about -2.24 / -2.37 bit.

All lose to the simple empirical-distribution summary.

Therefore YMPO is not advanced because a generic measure metric/network sounds sophisticated.

## 8. Whole-source transfer D0

Checkerboard hold out 84 source classes completely.

Representation/metric and source-coordinate KRR are trained only on the other 84 sources. Candidate prototypes are predicted for all 168 source cells. Evaluation uses the opposite fresh realization half from the unseen source classes.

### Point-valued mean field

Fresh log2 scores across the four source-holdout x realization-direction scenarios:

- -4.450;
- -4.178;
- -4.203;
- -4.311.

### Full ordered raw 10x30 field

- -4.389;
- -4.605;
- -4.253;
- -4.644.

### Ordinary mean+std distribution map

- -4.387;
- -4.680;
- -4.151;
- -4.605.

### Quantile measure field

- **-4.025**;
- **-3.668**;
- **-3.718**;
- **-3.692**.

The quantile measure field wins in all four scenarios, including over the higher-dimensional 300-D ordered raw representation and over the ordinary mean+std map.

Top1 improves from roughly 17-22% for the mean field to roughly 28-32%; median rank improves from about 4 to 2.

## 9. Sample-count saturation

Using the empirical-distribution summary with the first k registered snapshots:

- k=3: -2.566 / -2.641 bit;
- k=5: -2.204 / -2.328;
- k=7: -2.066 / -2.103;
- k=10: -2.006 / -2.040.

Most of the within-environment benefit is already present by roughly 5-7 registered samples.

These counts are not yet converted into physical seconds.

## 10. D0 decision

**D0_ADVANCE_YMPO_MAINLINE_CANDIDATE**

Reason:

> a spatial field of local concentration distributions preserves fresh and unseen-source localization information that is systematically lost by point-valued mean fields, full ordered raw fields under source-context interpolation, and ordinary mean+variance maps.

This advances the scientific object, not yet a final neural architecture.

## 11. Next required gate

No closed loop and no large data bank.

The next gate must test whether the measure-valued advantage survives a genuinely different physical wind operator and is not unique to House02/W2.

Before acquisition freeze:
- exact representation (strong ordinary quantile baseline);
- point-valued / mean+variance / ordered-field baselines;
- same candidate source support;
- proper source-posterior endpoint;
- local stochastic-distinguishability preservation;
- small physical-wind data budget.