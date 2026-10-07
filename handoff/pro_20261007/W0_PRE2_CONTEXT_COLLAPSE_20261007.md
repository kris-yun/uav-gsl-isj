# W0-PRE2 — context collapse and transport-hypothesis screen using existing 64 runs

Date: 2026-10-07

## Why this analysis was run

W0-PRE showed that changing the natural wind context can alter plume footprints more than within-wind realization noise. That result did not yet answer whether the **source evidence itself** is stable across transport contexts.

This analysis uses the same frozen 64 R0C/R0D/P0 runs and adds **no new GADEN simulation**.

Question:

> If source 0 and source 1 are discriminable inside one wind context, does that source evidence transfer to another wind context? If it does not, is it better to collapse all contexts into one average template, or preserve multiple transport hypotheses?

This is an exploratory mechanism screen, not a final paper claim.

---

## Test 1 — full-footprint source discrimination

For every House × gas:
- each wind has 2 equal-height sources × 4 realizations;
- use the full 2D concentration-footprint trajectory from 100–700 s;
- source classification is nearest source template;
- two frozen distances:
  - normalized-footprint mean JSD (shape-only);
  - symmetric relative L2 (absolute footprint).

### A. Same-wind leave-one-realization-out

Source discrimination is nearly perfect when the transport context is held fixed:

- absolute footprint: **64/64 correct**
- normalized shape JSD: **63/64 correct**

### B. Train in one wind, test in the other

When a source template learned in one wind is transferred directly to the other wind:

- absolute footprint: **46/64 correct = 71.9%**
- normalized shape JSD: **36/64 correct = 56.3%**

Thus source evidence that is almost perfectly separable within a wind context can collapse toward chance under a wind-context shift.

This is a much more direct source-inference result than the earlier vertical-spread sentinel.

---

## Test 2 — average-context collapse vs preserving transport hypotheses

Three leave-one-run-out source classifiers were compared:

1. **oracle_same_wind**:
   source template uses only the true wind context.
2. **pooled_mean**:
   all wind contexts for the same source are averaged into one template.
3. **min_wind_template**:
   each source keeps a separate template for each wind context; the source score uses the best matching transport hypothesis.

### Full 2D footprint

Absolute-footprint distance:

- oracle same wind: **64/64 = 100%**
- pooled mean: **56/64 = 87.5%**
- multi-hypothesis: **64/64 = 100%**

Paired comparison:
- multi-hypothesis fixed 8 pooled-mean errors;
- harmed 0 previously correct cases;
- exact paired sign/McNemar-style two-sided p ≈ **0.0078**.

Shape-only JSD:

- oracle same wind: **63/64 = 98.4%**
- pooled mean: **55/64 = 85.9%**
- multi-hypothesis: **63/64 = 98.4%**

### Sparse source-blind virtual route

To move away from full-field oracle observations, a deterministic 31-step normalized serpentine route was mapped to each House using geometry support only. At each time step only one footprint cell was sampled.

For log-concentration RMS distance:

- oracle same wind: **64/64 = 100%**
- pooled mean: **54/64 = 84.4%**
- multi-hypothesis: **62/64 = 96.9%**

Paired comparison:
- multi-hypothesis fixed 10 pooled-mean errors;
- harmed 2 cases;
- two-sided exact paired p ≈ **0.0386**.

This route was designed after the first W0 screen, so it is exploratory and cannot be treated as preregistered confirmation.

### Route robustness check

Four generic source-blind normalized routes were tested:

- horizontal serpentine;
- vertical serpentine;
- diagonal zig-zag;
- central cross.

Across all four routes and both concentration distances, preserving multiple wind-conditioned source templates outperformed a single pooled template:

- pooled: **70.3%–92.2%**
- multi-hypothesis: **82.8%–100%**
- oracle same-wind: **85.9%–100%**

The multi-hypothesis score remained close to the oracle same-wind upper bound.

---

## Interpretation

### Positive mechanism signal

**W0-PRE2_CONTEXT_COLLAPSE_SIGNAL = POSITIVE_EXPLORATORY**

The existing data support a clear mechanism:

> Source evidence is highly transport-context dependent. Collapsing different wind contexts into one averaged source representation can erase discriminative structure, while retaining separate transport hypotheses can recover much of the lost source information.

This argues against searching for one universal wind-invariant plume/source fingerprint.

It supports a source-inference formulation in which transport state is an explicit nuisance/latent variable:

p(y | s, O_w) = Σ_m p(y | s, m) p(m | O_w)

or its continuous analogue:

p(y | s, O_w) = ∫ p(y | s, U) p(U | O_w) dU.

However, this equation is a **method family**, not yet a novel contribution.

---

## Critical prior-art warning

A 2025 Journal of Turbulence paper,
**“Many wrong models approach to localise an odour source in turbulence with static sensors”**
(Piro, Heinonen, Cencini, Biferale; DOI 10.1080/14685248.2025.2492711)
already proposes ranking and blending multiple approximate transport models inside a Bayesian odor-source-localization algorithm.

Therefore:

**Generic “use multiple plume models / blend multiple wrong models” is NOT available as our main innovation.**

It should become a strong conceptual/source-inference baseline.

Our candidate novelty must be narrower and tied to the lakeshore/UAV problem, e.g.:
- inferring 3D transport hypotheses from sparse UAV/ground meteorology;
- identifying which spatial/structural wind uncertainties matter for source posterior;
- allocating limited wind reconstruction/assimilation capacity according to expected source-posterior distortion;
- mobile UAV source inference in real-site lakeshore geometry.

---

## Newly identified confound in H02

The previous W0-PRE result suggested that the WC→WD effect was source-dependent in H02.

A deeper geometry check shows an important alternative explanation.

H02 source coordinates:
- source0 x = **−3.743 m**
- source1 x = **−2.243 m**

Domain x-min:
- **−5.393 m**

Thus under the leftward WC transport, simple x-direction clearance to the domain boundary is approximately:
- source0: **1.65 m**
- source1: **3.15 m**

The average WC plume displacement was:
- G10: source0 **0.48 m**, source1 **2.36 m**
- G13: source0 **1.05 m**, source1 **2.43 m**

A large fraction of WC footprint mass also reaches the leftmost footprint bins.

Therefore the source-dependent WC effect may partly reflect **finite-domain / outflow support**, not only internal geometry.

This is scientifically useful because it reveals a missing benchmark/source-selection contract:

> Equal local obstacle clearance at the source is not enough. Source locations must also have adequate transport-path / downwind-domain support under the forcing cases used for causal mechanism tests.

Do not claim the H02 source dependence as “geometry-conditioned wind sensitivity” until the boundary-support confound is controlled.

---

## Consequence for the next causal experiment

The decisive W0 experiment should be updated.

Before wind perturbations:
1. choose a base source / wind case using only the unperturbed baseline;
2. require low edge-loss / adequate downwind support;
3. freeze source, gas, geometry, RNG and route;
4. only then create matched-global-error perturbations.

The future method must also be compared against:
- PMFS / probabilistic forward-simulation GSL;
- a simple Bayesian/source-term inversion baseline;
- a **many-wrong-models / transport-ensemble blending baseline**.

The candidate contribution cannot be “multiple models” alone.

---

## Decision

Existing data are now sufficient to justify **one small causal GADEN experiment**, but not a new learned model and not a full FSR build.

Next scientific gate:

**W0C_MATCHED_TRANSPORT_ERROR_TO_SOURCE_POSTERIOR**

Question:
> when global wind-field error is matched, do different spatial/structural transport errors produce reproducibly different source-posterior damage after boundary-support confounds are controlled?

If NO: stop task-oriented transport sensitivity.
If YES: proceed to method design and FSR lakeshore confirmation.
