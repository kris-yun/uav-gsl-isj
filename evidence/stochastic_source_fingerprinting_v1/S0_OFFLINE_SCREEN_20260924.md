# Stochastic Source Fingerprinting v1 — S0 Offline Screen

Date: 2026-09-24  
Branch: `research/stochastic-source-fingerprinting-v1`  
Parent evidence: Bi-Green Gate 1A independent review `02eadd90cba01c418ac6bacec8888ca3e1df13d0`

## Status

**SSF_V1_S0_HOLD_SOURCE_CONDITIONED_VARIABILITY_REQUIRED**

This is a candidate mainline, not a frozen main innovation and not yet authorized for Codex/VM expansion.

## Scientific failure mechanism inherited from Gate 1A

The exact GADEN source-to-sensor oracle localized S2_W2_A at rank 1 but S2_W2_B at rank 7 under an independent plume realization, even though the wrong top candidates remained close to the true source.

The new scientific question is therefore:

> How can source identity be detected and attributed when the observed plume is one stochastic realization of a source-conditioned random process?

The target is not another deterministic plume predictor. The target is to separate a **source-conditioned forced fingerprint** from **internal plume variability**.

## Far-domain mother theory

### Climate detection and attribution / fingerprinting

Climate optimal fingerprinting separates externally forced response patterns from internal climate variability by weighting residuals using a covariance/precision structure estimated from climate-model simulations.

Primary current anchors:

1. Haoran Li and Yan Li, **Regularized Fingerprinting with Linearly Optimal Weight Matrix in Detection and Attribution of Climate Change**, *Journal of Climate*, 2026, DOI: `10.1175/JCLI-D-25-0740.1`.
   - peer-reviewed;
   - online 2026-09-16;
   - explicitly estimates covariance of internal climate variability from climate simulations;
   - derives a linearly optimal regularized weight matrix.

2. Yan Li, Tianying Wang, Jun Yan, Xuebin Zhang, **Improved Optimal Fingerprinting Based on Estimating Equations Reaffirms Anthropogenic Effect on Global Warming**, *Journal of Climate*, 2025, DOI: `10.1175/JCLI-D-24-0193.1`.
   - peer-reviewed;
   - errors-in-variables fingerprinting;
   - shared covariance / internal variability;
   - reproducible R implementation in the `dacc` package.

3. Haoran Li and Yan Li, **Adaptable Fingerprinting with Nonlinear Shrinkage for Climate Change Detection and Attribution under Variance Heterogeneity**, arXiv:2608.12496, 2026.
   - preprint only; not a peer-reviewed anchor;
   - relevant because it explicitly introduces variability inflation / variance heterogeneity and residual consistency checks.

The plain Mahalanobis distance or covariance whitening is **not** claimed as novelty.

## GSL-specific translation

For arbitrary source candidate (s) and plume realization (r):

[
z_s^{(r)} = \phi(c_s^{(r)}), \qquad \phi(c)=\log(1+c).
]

Decompose:

[
z_s^{(r)} = \mu_s + \epsilon_s^{(r)},
]

where:

- (mu_s) is the candidate source fingerprint;
- (epsilon_s^{(r)}) is internal stochastic plume variability.

With two independent simulation seeds C,D:

[
\Delta_s=z_s^{(C)}-z_s^{(D)}.
]

A first shared internal-variability covariance is estimated only from training sources:

[
\widehat\Sigma_{iv} \propto \operatorname{Cov}(\Delta_s).
]

The candidate score is the precision-weighted mismatch:

[
d_{iv}(s;y)=
(\phi(y)-\widehat\mu_s)^T
\widehat W_{iv}
(\phi(y)-\widehat\mu_s).
]

The final method, if it survives later gates, must convert these scores back into a PMFS-style source probability map.

## Frozen data used

Review package:

`BIGREEN_GATE1A_REVIEW_20260924.tar.gz`

SHA-256:

`9f2c4e93c3833b00dd82d3f53a21e2286f23afdf3e5087328fc094cada1ba2be`

Data:

- 630 arbitrary House02 free source locations;
- prediction seed C = 2026092401;
- prediction seed D = 2026092402;
- 300 observations/source = 10 time slices x 30 frozen pooled probes;
- S2_W2_A/B remain independent target realizations.

No new GADEN simulation was used in S0.

## S0-A: interleaved source-held-out covariance transfer

Four folds are defined only from PMFS source coordinates:

[
f=(i \bmod 2, j \bmod 2)
]

with fold sizes 153/159/156/162.

For every held-out fold:

- none of its source C-D differences is used to estimate the covariance;
- the precision matrix is fitted from the other ~75% of arbitrary sources;
- the held-out C realization retrieves the same source in the D bank and vice versa.

### Baseline: log1p Euclidean

C -> D:

- top-1: **48.41%**
- top-3: **73.17%**
- top-10: **93.02%**
- median rank: **2**
- mean rank: **3.346**

D -> C:

- top-1: **49.37%**
- top-3: **73.97%**
- top-10: **93.65%**
- median rank: **2**
- mean rank: **3.313**

### Ledoit-Wolf internal-variability whitening

C -> D:

- top-1: **59.68%**
- top-3: **86.83%**
- top-10: **97.46%**
- median rank: **1**
- mean rank: **2.208**

D -> C:

- top-1: **60.32%**
- top-3: **86.03%**
- top-10: **97.94%**
- median rank: **1**
- mean rank: **2.143**

OAS shrinkage independently reproduces essentially the same result.

### Paired source bootstrap

Using source identity as the bootstrap unit and averaging both directions:

- top-1 improvement: **+11.11 percentage points**
  - 95% bootstrap CI approximately **[+8.10, +14.21] pp**
- top-3 improvement: **+12.86 pp**
  - 95% CI approximately **[+10.40, +15.32] pp**
- top-10 improvement: **+4.37 pp**
  - 95% CI approximately **[+2.86, +5.95] pp**

20,000 paired bootstrap replicates; no replicate produced a non-positive top-1/top-3 delta in this run.

This is the first strong post-Bi-Green signal that holds over all 630 arbitrary source identities rather than only S1/S2.

## S0-B: independent S2 target check with truth fold excluded

The truth source belongs to held-out parity fold 2. Its C-D difference is not used to estimate the precision matrix.

With the shared log1p + Ledoit-Wolf internal-variability precision:

- S2_W2_A truth rank: **1**
- S2_W2_B truth rank: **3**

For comparison, log1p Euclidean gives:

- A: rank **1**
- B: rank **5**

This repairs the previously problematic B realization without using B to fit the covariance.

## Mechanism audit

On the truth-excluded covariance fit:

- the top 10 internal-variability eigenmodes explain about **55.2%** of covariance variance;
- top 50 explain about **83.1%**;
- top 100 explain about **92.0%**.

For the true-source residual:

- S2_W2_A places about **35.3%** of raw residual energy in the top 50 high-variance noise modes;
- S2_W2_B places about **78.0%** there.

After precision weighting, those same top 50 modes contribute only:

- A: about **3.3%** of weighted mismatch;
- B: about **18.8%**.

Thus B's realization error is disproportionately aligned with empirically high-variance plume directions, and precision weighting suppresses those nuisance directions. This directly supports the proposed detection-attribution mechanism.

## S0-C: strict contiguous-region holdout — critical limitation

The interleaved split is not sufficient for claiming spatial transfer.

A stricter four-quadrant holdout was therefore run. Each test quadrant is a contiguous source region and its C-D differences are completely excluded from covariance estimation.

### Shared full 300-D covariance

This **does not transfer**:

Baseline log1p top-3:

- C -> D: 73.17%
- D -> C: 73.97%

Shared full whitening top-3:

- C -> D: **74.29%**
- D -> C: **75.24%**

Top-1 slightly decreases.

Therefore the impressive interleaved result cannot justify a global shared-covariance mainline by itself.

### Why

Internal variability is strongly nonstationary over source position.

Across the four contiguous source quadrants, pairwise Ledoit-Wolf covariance matrices have relative Frobenius differences of roughly **1.23–1.56**. Their leading 10-dimensional noise eigenspaces have mean principal angles roughly **67–79 degrees**.

So one House-wide covariance is physically wrong.

### Transferable low-dimensional component

If only the **10x10 temporal internal-variability covariance** is learned by pooling across probes/sources, contiguous-region transfer becomes modest but statistically positive at top-3:

C -> D:

- baseline top-3 73.17%
- temporal-whitened top-3 **77.62%**

D -> C:

- baseline top-3 73.97%
- temporal-whitened top-3 **76.98%**

Paired two-direction top-3 improvement:

- **+3.73 pp**
- 95% bootstrap CI approximately **[+1.51, +6.03] pp**

Top-1 does not improve reliably.

This suggests that a transferable internal-variability structure exists, but the full spatial covariance must be source/transport conditioned.

## Heterogeneity evidence

The source-level C-D log-noise energy varies strongly:

- 5th percentile ~0.060
- median ~0.631
- 95th percentile ~1.735
- max ~5.517

A source-conditioned variability magnitude is spatially smooth under interleaved out-of-source prediction; simple geometry-only kNN diagnostics obtain high cross-fold predictability. This is **diagnostic evidence only**, not a proposed final algorithm.

A scalar variance-inflation patch was tested. It produced at most marginal additional retrieval gains and was not robust enough to freeze as the solution.

## Prior-art boundary

Searches over GSL / robotic olfaction found:

- variance maps and concentration fluctuation statistics;
- Gaussian-process covariance for gas distribution mapping;
- probabilistic PDE/factor-graph uncertainty;
- Bayesian/source posterior approaches;
- a 2026 deep probabilistic GSL preprint using physical dependency-guided sequential inference.

No retrieved work in the screen implemented the specific climate-detection-and-attribution construction:

> estimate source-realization internal variability from independent plume simulations, construct a regularized precision fingerprint, and use it to suppress stochastic plume modes in arbitrary-candidate PMFS source ranking.

This is a preliminary novelty screen, not a proof of absence.

## Decision

**SSF_V1_S0_HOLD_SOURCE_CONDITIONED_VARIABILITY_REQUIRED**

What is supported:

1. The new scientific problem is real: source identity must be separated from realization-level stochastic plume variability.
2. Climate detection-attribution fingerprinting is a legitimate far-domain mother theory, with current 2025/2026 peer-reviewed anchors.
3. Internal-variability precision weighting has a strong 630-source interleaved held-out signal and repairs S2_B from log rank 5 to rank 3.
4. The improvement has a directly verified mechanism: B residual energy lies heavily in high-variance plume modes.
5. A source-independent full covariance does **not** transfer to a contiguous unseen source region.

Therefore:

- do **not** send Codex to closed loop;
- do **not** claim plain covariance whitening / Mahalanobis distance as innovation;
- do **not** freeze Stochastic Source Fingerprinting as the main innovation yet.

The next knife must derive and validate a **source/transport-conditioned internal-variability model** that preserves the climate fingerprinting idea while transferring across contiguous unseen source regions.

If that mechanism cannot exceed baseline under the contiguous-region gate without target-driven tuning, STOP this mainline.
