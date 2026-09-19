# Candidate M1-C — Non-Intrusive Missing-Physics Correction for PMFS Transport Models

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: CANDIDATE / OFFLINE FALSIFICATION ONLY

## 0. Scientific thesis

The main failure in model-based turbulent GSL is not always weak inference; it can be a **structured model–reality gap** in the source-conditioned transport/sensor forward law.

Therefore, instead of replacing PMFS with an end-to-end network, reuse the trusted physical prior and learn only the missing structured correction needed to make candidate-conditioned responses physically consistent with observations.

## 1. Remote-field provenance

### Primary 2026 top-journal anchor
Nature Communications 2026:
Hao Wang, Qinghe Wang, Caiyou Yuan, Kailiang Wu,
*Learning missing physics from legacy simulators with alternating neural integrators*.

Core transferable idea:
- trusted prior is informative but incomplete;
- do not discard it for a black-box surrogate;
- alternate/reuse the callable prior and a learned corrector for the structured discrepancy;
- the prior can be non-differentiable / legacy / compiled;
- the correction targets the model–reality gap rather than pretending to discover a new fundamental law.

### Independent 2025/2026 support
- ICML 2025: *A Generalizable Physics-Enhanced State Space Model for Long-Term Dynamics Forecasting in Complex Environments*.
  Decomposes known and unknown dynamics and regularizes latent states against known physics.
- NeurIPS 2025: *Stable Port-Hamiltonian Neural Networks*.
  Strong physical inductive bias improves sparse-data dynamics learning and extrapolation.
- Nature Communications 2026: *Learning turbulent flows with generative models for super resolution and sparse flow reconstruction*.
  Demonstrates that naive L2 / standard physical surrogates can oversmooth turbulence and that targeted learned correction/generative components can restore missing high-frequency structure at low inference cost.

## 2. Existing project evidence directly matching the premise

### Exact source-conditioned physical responses retain source identity
evidence/cstar_m1_exact_counterfactual_transfer_20260909.json:
- H01: 4/4 true source rank-1.
- H02: 4/4.
- H03: 4/4.
- total: 12/12 rank-1 even when each target is scored only against candidate traces from the opposite wind.
- later calibration audit correctly withdraws the confidence gate, but the ranking result remains 12/12.

Interpretation:
> the source-conditioned physical response family contains strong source information when the forward response is sufficiently faithful.

### Approximate deployed model can erase physically observed support
evidence/cstar_m1_phic_support_failure_audit_20260910_r2.json:
- selected truth-region candidate rows: 1,584.
- exported positive events: 299.
- nonzero exposure rows for that candidate: 0.
- all 299 positive events have all three model members at zero exposure.
- first conflict: t = 45.5969597 s, measured concentration = 0.113416292 ppm above the fixed 0.1 ppm threshold, while every model member predicts zero.
- other candidates in the same export do have nonzero exposure, so this is not a globally dead simulator.

Frozen verdict: MODEL_ZERO_WITH_OBSERVED_HITS.

This is unusually direct evidence of a structured candidate-dependent model discrepancy.

### Source inspection identifies concrete structural mismatch opportunities
Current forward scoring / integration audits document:
- FOPDT sensor state can be reinitialized inside scoring rather than chronologically persisted;
- context exposure and source exposure are not always passed through identical sensor history;
- local/estimated transport approximations can create zero or physically wrong exposure;
- source discretization, transport mismatch, sensor memory and event alignment remain distinct possible discrepancy components.

## 3. Why this is different from PINN / neural operator / ordinary surrogate GSL

The main object is not a replacement forward network.

For candidate source s:

Prior: F_prior(s, history, transport_context) -> predicted response.

Correction: C_theta(F_prior state, observable context) -> structured residual / missing-physics update.

Corrected response: F_corr = Compose(F_prior, C_theta).

Source posterior: P(s | Y) proportional to likelihood(Y | F_corr(s)) times prior(s).

The scientific claim is:
> preserve the physically useful source-conditioned structure of PMFS while correcting only the specific parts of the transport/sensor operator that are unsupported by data.

Theory-name-removal test:
- if the callable prior is removed, this becomes a generic neural forward model and the missing-physics claim disappears;
- if the corrector is removed, the documented model-zero-with-hit conflict remains.

## 4. GSL collision screen

Existing collisions:
- 2024 physics-guided neural network GSL already learns a source-conditioned gas-dispersion surrogate and solves the inverse problem.
- reduced-order adjoint / DMD methods already accelerate source-term estimation.
- older atmospheric source inversion includes plume-bias correction.

Therefore the contribution cannot be:
- physics-guided NN for GSL;
- use a surrogate instead of CFD;
- add a residual to concentrations.

Remaining novelty room:
- non-intrusive correction of the **existing PMFS source-conditioned transport/sensor operator**;
- explicit decomposition of transport discrepancy, sensor-memory discrepancy, and source-support discrepancy;
- correction learned across environments but applied candidate-wise before probability-map updating;
- lightweight reuse-and-correct architecture that preserves the PMFS map output and frozen physical prior.

Status after collision screen: CONDITIONAL SURVIVOR.

## 5. Smallest viable architecture

M1 main: **Prior–Corrector Transport Response**

At each source-update block:
1. PMFS / compact physical prior produces candidate-conditioned exposure-response sequence.
2. lightweight residual corrector consumes only observable context and prior response.
3. corrected response is passed through the same persistent sensor law.
4. event likelihood updates the source probability map.

No 3-D plume reconstruction is required.

## 6. Possible auxiliary innovations if M1 survives

### Auxiliary A — Extreme-event-aware correction
Nature Communications 2026 η-learning.

Reason:
- the discrepancy is often concentrated at intermittent positive events that a mean-squared residual learner could ignore.
- η-style observable-statistic constraints can force the corrector to preserve hit/onset/tail statistics.

### Auxiliary B — Shift-aware structured calibration
ICLR/ICML 2025 conformal-under-shift / structured conformal regions.

Reason:
- a corrected forward model can still be wrong in an unseen House/simulator;
- probability-map confidence should expand/abstain under unsupported shift.

## 7. Offline falsification gates before implementation

Kill M1-C if:
1. discrepancy errors are effectively random rather than reproducible/structured across source/context;
2. a source-independent scalar recalibration fixes the same support failures;
3. corrected prior cannot improve true-source held-transport likelihood without also improving decoys equally;
4. correction must use evaluator-only full CFD fields or future wind;
5. the learned corrector is heavier than simply replacing the forward model;
6. public datasets do not provide enough paired observation/prior information to train or evaluate correction.

## 8. Current evidence score

Strengths:
- strongest direct project-mechanism match among current M1 candidates.
- primary source is a 2026 Nature Communications scientific-computing paper.
- preserves existing PMFS architecture and source probability map.
- naturally lightweight if the prior is callable and the correction small.
- exact physical response 12/12 result gives a concrete upper-mechanism target.

Risks:
- physics-guided/source-surrogate GSL collision is real.
- novelty depends on **non-intrusive missing-physics correction of an existing source-conditioned operator**, not generic hybrid ML.
- transfer to public real datasets is harder because the baseline prior must be runnable or approximated for every dataset.

## 9. Current verdict

M1-C = STRONG MECHANISM-FIT CANDIDATE, lower novelty margin than the PRL delay-invariant candidate.

Next:
- quantify whether the observed forward discrepancy is low-dimensional / structured enough to learn;
- compare source-independent calibration vs candidate-dependent correction;
- search 2025/2026 hybrid-inverse literature for direct source-estimation collisions.

## 10. Simple global-calibration diagnostic

A deliberately favorable evaluator-only diagnostic was run on the existing H01-SA-fast estimated-transport traces.

Inputs:
- observed H01-SA-fast measured gas history;
- approximate estimated-transport candidate sensor traces for SA and SB on the same route;
- fit a single affine calibration y = a * y_model + b on the first 180 s using the true SA candidate only;
- test both candidates on the held final 60 s.

This is not deployable and is intentionally biased in favor of the simple-calibration hypothesis.

Fit:
- a = 0.05497
- b = 0.000931 ppm

Held final 60 s:
- raw SA MSE = 0.05927
- raw SB-zero-trace MSE = 0.004032
- affine-calibrated SA MSE = 0.003722
- affine-calibrated SB MSE = 0.003995

Observed tail:
- mean = 0.02021 ppm
- 16 samples exceed 0.1 ppm
- maximum = 0.4141 ppm

Interpretation:
- a source-independent affine calibration can shrink the gross amplitude error enough to reverse SA vs SB in this one evaluator-only case, but only by collapsing the modeled amplitude by ~18x.
- it does not reconstruct event timing/support; the SB trace remains a constant offset because its physical prior is identically zero.
- the resulting SA-vs-SB tail MSE margin is very small despite using the true candidate to fit the calibration.
- therefore this diagnostic does not support a claim that scalar recalibration solves the forward mismatch.

Combined with MODEL_ZERO_WITH_OBSERVED_HITS:
> the important missing object is candidate- and history-dependent support/timing, not only a global concentration scale.

Caveat:
- this is one H01 route and an evaluator-only fit, so it establishes a mechanism warning, not a general PASS.

## 11. Updated M1-C decision

M1-C survives the simple-calibration kill test provisionally.

However, novelty remains the major risk:
- if the corrector is only a residual MLP, reject;
- a viable contribution must expose a physically interpretable correction state (transport support, timing/memory, or unresolved closure) and demonstrate that it repairs candidate evidence before posterior updating.

Status: STRONG MECHANISM-FIT / NOVELTY-AT-RISK.
