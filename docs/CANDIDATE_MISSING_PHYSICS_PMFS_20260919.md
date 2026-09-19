# Candidate — Learned Missing Physics for PMFS/GSL

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: CANDIDATE / OFFLINE FALSIFICATION ONLY

## 0. One-sentence thesis

PMFS should not replace its physically meaningful but imperfect forward model with a black-box estimator; it should **reuse the prior and learn only the structured missing transport/sensor physics that corrupt source evidence**, while preserving source-discriminative intermittency and explicit uncertainty under shift.

## 1. Main remote-field paradigm

### Learned missing physics / gray-box reuse-and-correct

Primary 2026 anchor:
- Nature Communications 2026 — Hao Wang et al., *Learning missing physics from legacy simulators with alternating neural integrators*.
  - formalizes the model–reality gap as structured discrepancy caused by unresolved physics / structural incompleteness;
  - introduces a non-intrusive prior–corrector framework around callable frozen simulators;
  - uses operator-splitting composition rather than replacing the prior;
  - demonstrates recovery of missing coupling and effective subgrid correction in turbulence;
  - shows parameter-shift correction and real-data prior drift correction.

Independent 2025 anchors:
- NeurIPS 2025 — Wei et al., *INC: An Indirect Neural Corrector for Auto-Regressive Hybrid PDE Solvers*.
  - hybrid coarse solver + learned correction;
  - direct state correction can amplify autoregressive errors;
  - integrating correction into governing dynamics provides stronger stability properties;
  - tested through 3-D turbulence.
- NeurIPS 2025 — Yue et al., *DeltaPhi: Physical States Residual Learning for Neural Operators in Data-Limited PDE Solving*.
  - reframes direct PDE input-output prediction as learning residuals between related physical states.
- NeurIPS 2025 — Ilersich & Nair, *Learning Stochastic Multiscale Models*.
  - explicitly models resolved macrostate plus latent unresolved microscale dynamics.

The transfer is the **paradigm**, not any specific ANI/INC architecture:
> keep a trusted coarse physical prior and learn the unresolved discrepancy that matters for the downstream scientific task.

## 2. Why the project demands this paradigm

The project contains unusually direct evidence that the failure is often forward-model structural error rather than simply posterior arithmetic.

### Exact physics premise
Controlled exact candidate-specific forward responses rank the evaluator-only true source first across the frozen source×wind×House microbank.

Interpretation:
- source identity can survive transport changes when the candidate-conditioned physical response is sufficiently faithful.

### Deployable provider failure
The estimated transport provider can generate response shapes/amplitudes that are worse than a null response.

H01 SA-fast example:
- observed positive interval is late and sparse;
- estimated-provider log1p response MSE for the actual SA candidate ≈ 0.0073375;
- a zero/null response MSE on the same observations ≈ 0.0008061;
- predicted response develops a too-large, too-long tail.

H01 same-provider diagnostic:
- actual SA is ranked closer to the SB/null-like response than to the SA approximate response;
- actual SB is correctly represented by the near-zero SB response.

Thus the discrepancy is **candidate dependent**. A global calibration or candidate-independent nuisance removal cannot fix it.

### Explicit support contradiction
The PHIC support audit records:
- 299 observed positive events;
- selected candidate surrogate nonzero exposure rows = 0;
- verdict = MODEL_ZERO_WITH_OBSERVED_HITS.

So a candidate likelihood can fail because the surrogate omits physically realized support.

### Transport-provider error
Prequential local-wind audits show the GMRF predictor loses to last-local temporal persistence in every tested House/regime, despite beating zero wind.

Interpretation:
- the project already owns an informative physical prior;
- the weak link is a structured, context-dependent model–reality gap;
- replacing the entire inference chain is not the first scientific response.

## 3. Critical novelty boundary

Direct collision already exists in turbulent odor localization:
- Journal of Turbulence 2025 — Piro et al., *Many wrong models approach to localise an odour source in turbulence with static sensors*.
  - blends/ranks multiple inevitably imperfect stochastic odor models in Bayesian source localization.

Therefore this candidate **cannot** claim novelty as:
- “handle model mismatch”;
- “use several wrong models”;
- “marginalize model uncertainty”;
- “combine physics and ML”.

The surviving novelty must be narrower and stronger:

> **learn a source-conditioned, physically structured correction to a frozen PMFS/transport prior, and prove that the correction restores source-discriminative evidence rather than merely reducing forward MSE.**

This differs from many-wrong-model blending because it learns missing physics relative to the executable prior rather than selecting/weighting fixed approximate models.

## 4. Main innovation M1

### Source-Conditioned Missing-Physics Correction

Let the frozen prior produce a candidate response
[
	ilde y_s = mathcal P(s, h_t),
]
where (h_t) contains the allowed pose/wind/sensor history.

Learn only a correction
[
Delta_	heta(s,	ilde y_s,h_t)
]
and construct a corrected candidate response
[
hat y_s = mathcal C(	ilde y_s,Delta_	heta).
]

The exact coupling operator (mathcal C) is not frozen yet.
Candidate implementations to compare:
1. additive residual;
2. multiplicative/log residual;
3. alternating prior–corrector composition inspired by ANI;
4. indirect/parameterized physical correction inspired by INC where the prior exposes suitable state variables.

Key rule:
- the corrector is candidate-conditioned;
- it cannot be a single global response calibration;
- source truth is training/evaluation supervision only and is not available online.

PMFS-compatible source likelihood is then evaluated from corrected candidate responses and normalized into the same source-location probability map.

## 5. M1 falsification: MSE is not enough

A simple existing-data affine correction exposes a crucial failure mode.

H01:
- fitting a generic log-affine correction to SA reduces SA forward MSE from ~0.00734 to ~0.000710;
- but applying that same correction to SB worsens its already-correct response.
- fitting on the near-zero SB response learns essentially a zero predictor; when transferred to SA it reduces SA MSE to ~0.000804 simply by collapsing toward blank observations.

Therefore:
[
oxed{	ext{lower forward MSE} 
otRightarrow 	ext{better source evidence}.}
]

Any M1 that only optimizes response MSE is invalid.

Mandatory M1 metrics:
- true-candidate rank / pairwise source margin;
- support overlap;
- first-arrival/onset error;
- hit/blank calibration;
- burst/tail statistics;
- posterior proper score;
- wrong-candidate destructive control.

## 6. Discrepancy anatomy from existing H01 provider

For H01 SA-fast:
- observed hit samples >0.1 ppm: 16;
- predicted hit samples: 44;
- overlap: 12;
- observed first hit: ~228.8 s;
- predicted first hit: ~229.6 s;
- log1p MSE: ~0.0073375.

Only ~4.2% of squared log error occurs on the 16 observed hit samples; ~95.8% occurs on blank samples because the predicted response has a large late tail.

Scientific implication:
- ordinary global MSE is dominated by blank-region discrepancy and can reward a collapse-to-zero solution;
- the correction must preserve event topology/intermittency, not only average fit.

This creates a concrete necessity for M2.

## 7. Auxiliary innovation M2 — Extreme-Event-Aware Intermittency Correction

Primary remote anchor:
- Nature Communications 2026 — Chang & Sapsis, *Extreme Event Aware (η-) Learning*.

Transfer:
- rare/extreme observable -> plume whiff / onset / burst / upper-tail exposure;
- quiescent regime -> long blank intervals;
- η-aware training -> correction constrained by predeclared event statistics in addition to average response error.

Candidate fixed observables:
- first arrival above the existing physical gas floor;
- exceedance fraction;
- q95/q99/top-tail mass;
- burst duration / blank duration;
- hit-support overlap.

The point is not to invent arbitrary odor features.
The point is to stop the missing-physics corrector from winning by predicting the dominant blank state while erasing the rare events that actually identify source.

M2 is killed if a trained M1 already preserves these statistics and η-style constraints give no held-condition source-rank increment.

## 8. Auxiliary innovation M3 — Structured Shift-Aware Source Regions

Primary 2025 remote anchors:
- ICLR 2025 — Wasserstein-Regularized Conformal Prediction under General Distribution Shift.
- ICML 2025 — Optimal transport-based conformal prediction.
- ICML 2025 — Volume Optimality in Conformal Prediction with Structured Prediction Sets.

Project role:
- learned missing physics will itself have a validity domain;
- House/simulator/sensor shift can change discrepancy structure;
- existing project evidence already shows sharp posterior confidence can be wrong.

M3 does not replace the PMFS source probability map.
It adds a calibrated spatial source region / abstention rule derived from the map.

M3 is killed if:
- nominal coverage fails on held environment shifts; or
- valid coverage requires nearly the whole map.

## 9. Current 1+2 architecture

### M1 MAIN
**Source-Conditioned Learned Missing Physics**
- frozen coarse PMFS/transport prior;
- lightweight candidate-conditioned corrector;
- corrected candidate evidence drives source probability map.

### M2 AUX
**Extreme-Event-Aware Intermittency Preservation**
- event/tail-aware correction objective;
- protects sparse source-identifying structure from blank-dominated regression.

### M3 AUX
**Shift-Aware Structured Source Calibration**
- calibrated spatial source region / abstention under unseen environment shift.

## 10. Lightweight contract

The method is not allowed to become a second CFD solver.

Preferred deployment form:
- reuse existing prior outputs already computed by PMFS or a cheap candidate provider;
- small temporal residual corrector;
- correct only response/event statistics needed by source likelihood, not a full 3-D plume;
- one shared corrector with candidate coordinates/context as conditioning;
- M2 is a loss/statistics head, not a second network;
- M3 is post-hoc calibration.

## 11. Public-data transfer contract

### VGR/GADEN
- prior: existing PMFS/coarse candidate response model;
- reference: GADEN/recorded sensor histories;
- target: correct candidate sensor evidence.

### Independent DNS turbulent plume
- prior must be frozen before target evaluation, e.g. a deliberately coarse advection-diffusion/puff or reduced stochastic model;
- reference: DNS-sampled trajectories;
- target: learn the discrepancy without retuning the prior per test case.

### Real wind tunnel
- prior: same class of coarse transport/sensor model using available measured wind;
- train/calibration split only;
- held source/wind/trajectory conditions test whether learned discrepancy transfers.

A separate prior invented after seeing each test dataset is forbidden.

## 12. Current collision status

Nearby but not identical:
- 2025 many-wrong-model odor localization: model ensemble/blending, not learned source-conditioned discrepancy.
- 2025 source-term ML enriched with simplified plume physics: feature fusion/direct regression.
- 2026 explainable adaptive PINN source inversion preprint: learns correction factors inside a Gaussian-plume/PINN inversion, a meaningful adjacent collision but not yet a peer-reviewed top-venue equivalent and not robotic PMFS.
- direct PINN, neural surrogate, transformer source inversion: replace/approximate the forward/inverse map rather than non-intrusively correcting a frozen deployed prior.

Novelty remains plausible, not established.

## 13. Hard GO gates

M1 premise GO requires all:
1. corrected true-candidate response improves held-context source rank/margin, not only MSE;
2. wrong-candidate correction does not obtain the same gain;
3. improvement survives source/wind/House holdout;
4. zero/support contradictions are reduced rather than smoothed away;
5. a matched black-box residual baseline and many-wrong-model ensemble comparator are included.

M2 GO additionally requires:
1. tail/event constraints improve held source evidence beyond M1 alone;
2. destructive event permutation or tail-statistic removal removes that increment.

M3 GO requires:
1. calibrated held-shift coverage with useful region size.

## 14. Current verdict

This candidate is currently stronger than the JEPA/predictive-representation line because:
- it directly matches the project’s strongest positive premise: exact forward physics preserves source identity;
- it directly targets the strongest negative premise: deployable approximate physics corrupts candidate evidence;
- it has independent 2025/2026 high-level SciML support in turbulence and hybrid solvers;
- it preserves the PMFS probability-map semantics instead of replacing the problem.

Status: ACTIVE PRIMARY CANDIDATE / OFFLINE FALSIFICATION ONLY.
