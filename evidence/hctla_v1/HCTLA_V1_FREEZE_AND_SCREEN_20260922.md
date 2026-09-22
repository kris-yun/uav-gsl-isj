# HCTLA V1 — Hypothesis-Conditioned Transport-Law Alignment

Date: 2026-09-22  
Status: **DISCOVERY POSITIVE / FROZEN BEFORE CURRENT INDEPENDENT-PLUME RESULTS ARE READ**  
Branch: `research/hctla-v1-freeze-20260922`  
Parent fallback commit: `90e03e9e4fee6ac837a6699174e6a13f25a4dbf6`

## 0. Separation from the active HCMC experiment

This branch does not change HCMC V1, its independent-plume runner, its seeds, its realizations, or its verdict rules.

HCTLA V1 is frozen now, while the current independent-plume HCMC experiment has not yet returned its six unblinded HCMC endpoint results. This preserves the option to evaluate HCTLA on the same pre-generated independent plume cases later without defining HCTLA from those truth-revealed results.

No HCTLA result in this file is an independent performance estimate. All reported numbers below come from the old frozen House01/02/03 × seed0/1 discovery archive.

---

## 1. Remote-domain mother ideas

### A. CaStLe — Causal Space-Time Stencil Learning

Nichol et al., 2025, *Journal of Geophysical Research: Machine Learning and Computation*:

**Space-Time Causal Discovery in Earth System Science: A Local Stencil Learning Approach**  
DOI: `10.1029/2024JH000546`  
Code: https://github.com/jjakenichol/CaStLe

CaStLe's key scientific idea is that local space-time dependency regularities can be learned from spatial replicates and used to recover global dynamics in high-dimensional physical fields. The paper explicitly includes transient geophysical plume phenomena.

### B. PITA — Physics-informed Temporal Alignment

Zhu et al., ICML 2025:

**Physics-informed Temporal Alignment for Auto-regressive PDE Foundation Models**  
PMLR 267, 2025  
Code: https://github.com/SCAILab-USTC/PITA

PITA aligns **data-discovered physical dynamics across time**, rather than requiring a known PDE law or comparing only raw predicted states.

### Transfer to source inference

The combined source-inference hypothesis is:

> A physically compatible source hypothesis should reproduce the observation's **time-indexed local effective transport operator trajectory**, not merely a pointwise plume field.

For every PMFS source-update transition (k\rightarrow k+1), HCTLA independently estimates a lightweight local stencil map from the measured hit-probability field and from every candidate-conditioned simulated hit-probability field.

The scientific object is therefore not the concentration state itself, but the sequence

[
\beta^{(m)}_1,\ldots,\beta^{(m)}_4
]

versus

[
\beta^{(s)}_1,\ldots,\beta^{(s)}_4,
]

where each (eta_k) is a locally fitted effective transport-stencil coefficient vector for one source-update transition.

The underlying advection-diffusion physics need not differ by source. The source determines which parts of the geometry/flow field are excited and therefore which **effective local transport signature over the observed support** is produced. The claim must therefore use "effective transport-operator/stencil trajectory", not "the source changes the governing PDE".

---

## 2. Frozen HCTLA V1 definition

### Candidate scope

For each case:

1. take the authoritative final-leaf candidate IDs from the final source update;
2. retain only final-leaf IDs whose same candidate identity exists in all five source updates;
3. invalid/nonpersistent final leaves receive zero HCTLA density.

This persistence restriction is source-blind. A separate uniform-persistence control is required because persistence itself could otherwise create a geometric prior.

### Spatial support

Use only grid cells that satisfy:

- present in every source update;
- measured confidence (>10^{-6}) in every update.

No truth or source coordinate enters this support construction.

### Frozen stencil

For each valid center cell use the cardinal five-point stencil:

[
(i,j), (i+1,j), (i-1,j), (i,j+1), (i,j-1).
]

No diagonal terms in HCTLA V1.

### Per-transition normalization

For every measured/candidate field and every source update independently:

- subtract spatial mean over common support;
- divide by spatial standard deviation over common support.

This makes the fitted local operator primarily characterize spatial transition structure rather than absolute amplitude.

### Per-transition local operator

For transitions (k=1,ldots,4), fit

[
z_{k+1}(i,j)
=
\beta_{0,k}
+
\sum_{r\in\mathcal S_5}\beta_{r,k}z_k(r)
+
\epsilon,
]

using all eligible spatial centers as replicates.

Frozen regression:

- ridge coefficient: **alpha = 1.0**;
- intercept included;
- five stencil coefficients plus intercept;
- no House-specific parameters;
- no truth-dependent weighting.

### Candidate score

For source hypothesis (s):

[
C(s)
=
\frac{1}{4}
\sum_{k=1}^{4}
\cos\!\left(
\beta^{(m)}_k,
\beta^{(s)}_k
\right).
]

The temporal correspondence (k\leftrightarrow k) is part of the method.

No MSE-fit penalty is included in frozen HCTLA V1.

### Posterior construction

- convert valid candidate scores to average percentile ranks;
- invalid final leaves receive density 0;
- every final free cell inherits its final leaf's density;
- normalize to a source posterior.

For future authoritative evaluation, the final 300-s top-5% ExpectedValue endpoint must be computed by the same linked-native C++ evaluator used in the HCMC validation. The discovery numbers below use the rapid Python ceil/stable-tie clone and are not authoritative endpoint numbers.

---

## 3. Discovery result

Frozen six old discovery cases:

| case | Native m | HCTLA V1 m |
|---|---:|---:|
| House01 seed0 | 5.5273 | 4.0297 |
| House01 seed1 | 4.0016 | 4.3724 |
| House02 seed0 | 4.1070 | 2.7636 |
| House02 seed1 | 3.7007 | 2.6617 |
| House03 seed0 | 7.7821 | 2.3248 |
| House03 seed1 | 8.2116 | 3.2731 |

Aggregate:

- Native mean: **5.5551 m**
- HCTLA V1 mean: **3.2376 m**
- pooled reduction: **41.72%**
- improved/non-worse: **5/6**

This is weaker than HCMC discovery performance but materially stronger than the current HCDG fallback.

---

## 4. Critical destructive controls

### A. Uniform persistent-candidate support control

Give every final leaf that persists through all five updates equal positive density and all other final leaves zero density.

Result:

- mean endpoint: **6.4103 m**
- pooled change vs Native: **-15.39%**
- improved: **2/6**

Therefore the HCTLA result is not explained simply by selecting persistent candidates.

### B. Final-leaf score permutation

Freeze the exact HCTLA score distribution and valid/invalid candidate set but permute scores among valid final leaves.

300 repetitions:

- null mean: **4.4012 m**
- null 5–95%: **3.2983–5.3847 m**
- null as good as/better than real HCTLA: **10/300 = 3.33%**

### C. Spatial destruction

Within every candidate and every source-update snapshot independently, shuffle simulated hit probabilities over the same common support. This preserves snapshot marginal distributions and candidate/update identity but destroys local spatial stencil organization.

30 repetitions:

- null mean: **4.0950 m**
- null 5–95%: **3.5169–4.6140 m**
- null as good as/better than real HCTLA: **0/30**

### D. Temporal-order destruction

Within each case, permute the five candidate simulated source-update snapshots before fitting transition-wise stencil trajectories. Keep measured update order unchanged.

30 repetitions:

- null mean: **3.9689 m**
- null 5–95%: **3.3230–4.5778 m**
- null as good as/better than real HCTLA: **2/30 = 6.67%**

Therefore the matched temporal transition order is load-bearing for the frozen transition-wise score.

---

## 5. Important falsification that preceded V1

An earlier prototype fitted one **single aggregate stencil** over all four transitions.

It looked excellent superficially:

- about **43.49%** pooled reduction;
- **6/6** improved.

But temporal-order permutation made it **better** in most repetitions:

- **25/30** permuted orders were as good as/better than the real order.

That prototype is rejected as a causal/dynamical mechanism.

HCTLA V1 was retained only because transition-wise temporal alignment survives the time-order destruction test substantially better.

---

## 6. Cross-seed source-blind reproducibility

Spearman correlation of candidate HCTLA V1 scores on identical valid candidate IDs between seed0 and seed1:

- House01: **rho = 0.445**, permutation upper-p ≈ **0.001**
- House02: **rho = 0.833**, permutation upper-p ≈ **0.001**
- House03: **rho = 0.954**, permutation upper-p ≈ **0.001**

This is a strong source-blind reproducibility signal on the discovery archive.

---

## 7. Stencil / regularization family robustness

The following family was checked as a robustness stress test, not as a model-selection exercise:

| stencil | ridge alpha | mean m | pooled reduction | improved |
|---|---:|---:|---:|---:|
| cardinal 5 | 0.1 | 3.4124 | 38.57% | 5/6 |
| cardinal 5 | 1.0 | 3.2376 | 41.72% | 5/6 |
| cardinal 5 | 10 | 3.8992 | 29.81% | 5/6 |
| Moore 3×3 | 0.1 | 3.0833 | 44.50% | 5/6 |
| Moore 3×3 | 1.0 | 3.3789 | 39.17% | 5/6 |
| Moore 3×3 | 10 | 3.8928 | 29.92% | 4/6 |

Do not switch HCTLA V1 to Moore-9/alpha-0.1 merely because it has the best discovery number. V1 remains cardinal-5, alpha=1.0.

A source-blind median-rank consensus across all six family members yields:

- mean ≈ **3.4852 m**
- pooled reduction ≈ **37.26%**
- improved **5/6**

Thus the signal is not confined to one exact stencil/ridge setting.

---

## 8. Adjacent GSL collision screen and claim boundary

Targeted current search found adjacent but not identical GSL work:

1. **Park et al., 2025, Visual Mamba-Inspired Directionally Gated State-Space Backtracking for Chemical Gas Source Localization** uses learned directional causal stencils / state-space backtracking for concentration sequences.
2. 2026 work also exists on physics-guided / sequential deep indoor GSL.

Therefore HCTLA must **not** claim:
- first use of causal stencils in gas source localization;
- first temporal/sequential model for GSL;
- first physics-guided source localization.

The narrower novelty hypothesis is:

> **source posterior construction by candidate-wise temporal alignment of data-discovered local effective transport-stencil trajectories between measured and source-conditioned simulated plume statistics.**

The current search found no direct implementation of that exact mechanism in GSL/OSL, but this is a targeted screen, not an exhaustive novelty proof.

---

## 9. Pre-registered independent-plume gate

Because HCTLA V1 is frozen before the active independent-plume HCMC results are read, the already-generated independent plume cases may later be used for an HCTLA holdout evaluation **only if HCTLA posterior generation is performed source-blind and frozen before loading truth**.

Required protocol:

1. use the same six independent plume cases and the same native trajectories/context banks;
2. do not modify any HCTLA V1 definition above;
3. generate HCTLA scores/posteriors without loading source truth;
4. hash and freeze all six HCTLA posterior files;
5. only then release truth;
6. evaluate Native and HCTLA with the linked-native C++ top-5% evaluator;
7. run the same pre-frozen controls:
   - 300 final-leaf score permutations;
   - 30 spatial shuffles;
   - 30 time-order permutations;
   - uniform persistent-candidate support control.

Proposed PASS gate, frozen now:

- pooled HCTLA reduction >= **10%**;
- >= **4/6** non-worse;
- no new false-confident collapse;
- real HCTLA better than mean leaf-permutation null;
- real HCTLA better than mean spatial-shuffle null;
- real HCTLA better than mean time-permutation null;
- all provenance/integrity/native-endpoint parity checks pass.

Otherwise:
- performance failure -> `HCTLA_V1_INDEPENDENT_OFFLINE_NO_GO`;
- provenance/source-blind freeze/parity failure -> `HCTLA_V1_INDEPENDENT_OFFLINE_HOLD`.

Do not run HCTLA closed-loop before this gate passes.

---

## 10. Current fallback interpretation

HCTLA is now a stronger fallback candidate than the first HCDG screen because:

- larger discovery effect;
- temporal-order destruction is informative;
- spatial destruction is informative;
- strong cross-seed candidate-score reproducibility;
- stencil/regularization family robustness;
- two recent external scientific anchors with public code.

It remains **secondary to the active HCMC/HCRC independent validation** until independent-plume evidence exists.
