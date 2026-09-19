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


## 15. Same-route exact-vs-estimated evidence audit

A cleaner H01 SA-fast same-route comparison was performed using:
- observed measured history;
- exact candidate-forward GADEN inputs for SA and SB on the identical 1200-step route;
- exact frozen FOPDT replay;
- estimated-transport provider responses for SA and SB on that same observed route.

Route audit:
- H01 SA-fast and H01 SB-fast candidate-forward assets have identical timestamps and zero pose discrepancy.

Observed SA-fast:
- 16 sensor samples >0.1 ppm;
- first hit ~228.8 s;
- peak ~0.414 ppm;
- integrated response ~1.405 ppm·s.

Exact candidate responses:
- exact SA reproduces the observed sensor history to serialization-level precision;
- exact SA log1p MSE ~4.3e-31;
- exact SB log1p MSE ~8.09e-4;
- correct rank = SA.

Estimated provider:
- estimated SA log1p MSE ~7.34e-3;
- estimated SA has 44 >0.1 ppm samples, peak ~1.276 ppm and integrated response ~5.398 ppm·s;
- estimated SB is identically zero, MSE ~8.06e-4;
- wrong rank = SB.

This is a direct source-ranking reversal caused by the approximate forward provider while the exact physical response on the same route identifies the source correctly.

This is currently the strongest project-specific premise for M1.

## 16. Why generic residual regression is insufficient

Error decomposition for estimated SA:
- ~4.2% of squared log error occurs on the 16 observed hit samples;
- ~95.8% occurs on observed blank samples because the approximate provider produces an excessive late tail.

A global regression objective is therefore encouraged to minimize the dominant blank error and can obtain a deceptively low MSE by collapsing toward zero, which is exactly the wrong behavior for source identity.

A fixed four-statistic event-distance proxy (hit fraction, normalized first-arrival, log peak, log integrated exposure) was also tested and still preferred the wrong blank SB candidate because amplitude/tail mismatch remained too large.

Conclusion:
- merely changing the scoring metric to “event features” is not enough;
- M1 must actually correct the candidate response;
- M2 must constrain the correction so that rare source-support structure is preserved while spurious tail mass is removed.

This strengthens the M1+M2 coupling and eliminates an easy feature-engineering substitute.


## 17. Loop-7 collision sharpening: correction-based source localization exists in a distant modality

A 2025 underwater-acoustics screen found two close remote-domain precedents:

- JASA 2025, Miao et al., *Correction physics-informed neural network-aided matched field processing technique for underwater passive source range estimation*.
  - a physics propagation model generates source replicas;
  - a small measured-data correction network repairs environmental replica mismatch;
  - corrected replicas improve source ranging and generalization to unseen environments.

- CISS 2025, Kari et al., *Mismatch-Robust Underwater Acoustic Localization Using A Differentiable Modular Forward Model*.
  - adapts a learned forward propagation model at inference under environmental mismatch;
  - uses physics-inspired modularity in the forward model.

Interpretation for novelty:
- “correct an imperfect forward model to improve source localization” is **not globally novel**.
- This does not kill the GSL transfer; it actually supplies a strong distant-domain precedent for the transfer mechanism.
- But the GSL novelty must rely on the turbulent-gas-specific structure:
  1. source-conditioned correction of a PMFS-compatible transport/sensor response;
  2. correction judged by source evidence, not only field/replica fit;
  3. event/intermittency-aware constraints because blank-dominated regression can erase source evidence;
  4. cross-simulator / real-plume validation.

The claim must never be “first correction-based source localization”.

## 18. Scalar-correction falsification

A scalar amplitude sweep was applied to the wrong estimated SA response in H01 SA-fast.

- estimated SA baseline log1p MSE: ~0.0073375.
- estimated SB/null MSE: ~0.0008061.
- the global-MSE-optimal SA scale is ~0.067.
- this lowers SA MSE to ~0.0007404 and barely restores the SA-vs-SB MSE rank.
- however it removes **all** >0.1 ppm hits (predicted hit count 0) and peak falls below threshold (~0.0855 ppm).

By contrast:
- peak-matching scale ~0.325 retains 27 hits but MSE ~0.00149, still worse than the blank SB candidate;
- integrated-exposure-matching scale ~0.260 retains 26 hits but MSE ~0.00118, also worse than SB.

Thus no single scalar objective simultaneously restores:
- source rank under ordinary response fit;
- hit topology;
- amplitude/tail statistics.

Consequence:
> the missing physics is not reducible to a simple gain calibration. A useful correction must be time/context structured, while M2 must prevent the MSE-optimal blank collapse.

This is a positive necessity test for the M1+M2 composition.


## 19. Public-data feasibility correction

The validation ladder was re-audited against 2026 public dataset documentation.

### TURB-Smoke — strong mechanistic cross-simulator test
Scientific Data 2026 provides:
- DNS of fully resolved 3-D Navier–Stokes turbulence;
- five distinct point sources;
- multiple mean-wind strengths;
- source-resolved Lagrangian particle trajectories;
- source-resolved 3-D concentration fields and 2-D concentration products.

Use:
- define a frozen coarse prior (e.g. reduced puff/advection model) before test evaluation;
- sample DNS along synthetic robot trajectories;
- test whether the learned discrepancy transfers across wind and source while preserving source rank.

Status: SUITABLE.

### ICASSP 2025 GSL Challenge — preferred real localization benchmark
The challenge is explicitly built around:
- real wind-tunnel gas-source localization;
- high-resolution 3-D gas and wind measurements;
- controlled train/validation data.

Use:
- preferred real-data source-localization benchmark, subject to actual dataset access/license and exact split semantics.

Status: SUITABLE IN PRINCIPLE; ACCESS/SPLIT DETAILS MUST BE AUDITED BEFORE FREEZE.

### Red:Vapor 2026 — useful but NOT a multi-source-location localization benchmark
Scientific Data 2026 documents:
- 39 wind-tunnel runs;
- 8 dense raster scans;
- 22 fly-through trajectories;
- multiple sensors and four obstacle/landscape setups.
However, the synthetic source is the same physical outlet in all experiments; its location on the turntable remains fixed (although the turntable/setup orientation changes).

Therefore:
- do not claim Red:Vapor as an independent multi-source-position localization benchmark;
- use it for real-plume response correction, sensor-dynamics transfer, obstacle/geometry shift, and route/fly-through robustness;
- source-location ranking across multiple ground-truth source positions requires another real dataset such as the ICASSP challenge.

This correction prevents overstating cross-dataset localization validation.


## 20. Correction placement audit: discrepancy is upstream and sign-changing

The exact candidate-forward concentration input was compared directly with the estimated-provider concentration **before** the frozen FOPDT sensor law.

H01 SA-fast:
- exact raw candidate exposure:
  - 94 nonzero samples;
  - 19 samples >0.1 ppm;
  - first >0.1 ppm at ~186.4 s;
  - peak ~0.747 ppm;
  - integrated exposure ~1.406 ppm·s.
- estimated-provider raw exposure:
  - 128 nonzero samples;
  - 35 samples >0.1 ppm;
  - first >0.1 ppm only at ~228.6 s;
  - peak ~2.002 ppm;
  - integrated exposure ~5.429 ppm·s.

The discrepancy is not a constant gain and not even one-signed in time:
- 180–210 s: exact exposure mass ~0.224 vs estimated ~0.025 ppm·s — **missing support** dominates.
- 210–228 s: exact ~0.050 vs estimated ~0.006 — still missing support.
- 228–240 s: exact ~0.937 vs estimated ~4.944 — **spurious tail mass** dominates.

Across the full trace the discrepancy contains both:
- positive missing exact mass;
- negative/excess estimated mass.

Scientific consequence:
> the correction must alter the transport-response dynamics, not merely rescale the final sensor output.

This makes the NeurIPS 2025 INC distinction between direct state correction and indirect/physics-level correction directly relevant.

Current preferred placement:
1. correct the candidate exposure/transport trace upstream;
2. then pass the corrected exposure through the frozen exact FOPDT sensor model;
3. score source likelihood afterward.

This keeps the already-audited sensor physics fixed and assigns the learned component only to the unresolved transport discrepancy.


## 21. Provenance verification — top-level anchors confirmed

Web verification on 2026-09-19 confirmed:

- **Nature Communications 2026** — Hao Wang, Qinghe Wang, Caiyou Yuan et al., *Learning missing physics from legacy simulators with alternating neural integrators*, published 23 June 2026, DOI 10.1038/s41467-026-74002-2.
  - explicitly frames the scientific problem as a model–reality gap caused by unresolved physics / structural incompleteness;
  - provides a non-intrusive reuse-and-correct framework around a fixed callable prior;
  - includes effective subgrid correction in turbulence.
- **NeurIPS 2025 Main Conference** — Hao Wei et al., *INC: An Indirect Neural Corrector for Auto-Regressive Hybrid PDE Solvers*.
  - correction is inserted into governing dynamics rather than appended only to outputs;
  - evaluated through 3-D turbulence.
- **NeurIPS 2025 Main Conference** — Xihang Yue et al., *DeltaPhi: Physical States Residual Learning for Neural Operators in Data-Limited PDE Solving*.
- **NeurIPS 2025 Main Conference** — Andrew F. Ilersich & Prasanth Nair, *Learning Stochastic Multiscale Models*.

This gives the M1 paradigm one 2026 high-level journal anchor plus several independent 2025 top-conference SciML lineages.

## 22. Cross-House positive premise: exact physics survives transport shift

The frozen exact counterfactual transfer audit is stronger than a same-wind replay:

- target source/wind is scored **only with candidate traces from the opposite wind**;
- same-source same-wind trace is forbidden;
- true source ranks first in **12/12 cases**:
  - H01: 4/4;
  - H02: 4/4;
  - H03: 4/4.

The calibrated confidence gate was correctly withdrawn later, but the ranking fact remains.

Interpretation:
> transport change by itself does not destroy source identity when the candidate-conditioned physical response family is faithful enough.

Combined with the H01 estimated-provider rank reversal, this isolates the scientific target more sharply:
> the key failure is not merely “different wind”; it is **structural error in the deployable candidate forward response**.

## 23. Candidate-conditioning necessity test

A source-independent fast↔slow correction was tested using the existing exact measured histories on the identical source-blind route.

Protocol:
- learn the complete log-response wind residual on source SA and add it to the opposite-wind response of source SB;
- repeat with SB-trained residual applied to SA;
- test both fast→slow and slow→fast directions;
- no localization metric is used to fit the correction.

Results:
- only 2 of 12 cross-source transfers give even a tiny MSE improvement;
- the other 10 worsen;
- catastrophic examples include:
  - H01 SA-trained slow→fast correction applied to SB: error ×~446;
  - H02 SB-trained slow→fast correction applied to SA: error ×~5262;
  - H02 SB-trained fast→slow correction applied to SA: error ×~3992;
  - H03 all four source-independent transfers worsen.

Conclusion:
> a transport correction learned independently of source/candidate is empirically invalid.

This directly supports the M1 requirement that the learned discrepancy be **candidate-conditioned**, not a global wind calibration or context-only adaptation.

## 24. Lightweight-corrector feasibility: discrepancy is structured, not white noise

For H01 SA-fast upstream exposure, define

[
d_t = y_t^{exact} - y_t^{estimated}.
]

Existing-data analysis gives:
- RMS discrepancy ≈ 0.150 ppm;
- lag-1 autocorrelation ≈ 0.954;
- lag-2 ≈ 0.890;
- lag-5 ≈ 0.674;
- only 3 sign changes across the 1200-sample trace;
- low-frequency spectral energy fraction:
  - first 20 Fourier bins ≈ 52.6%;
  - first 50 ≈ 85.1%;
  - first 100 ≈ 95.2%.

This matters for the lightweight requirement:
> the missing-physics signal is temporally organized enough that a compact temporal corrector is plausible; the evidence does not look like unlearnable white stochastic error.

At the same time, the SA and SB correction residuals have essentially zero cross-source correlation (~0.004), again ruling out a single global discrepancy trace.

## 25. Meta-context alternative challenged and demoted

A separate 2025 top-venue paradigm was screened:

- ICLR 2025 — *Neural Context Flows for Meta-Learning of Dynamical Systems*;
- NeurIPS 2025 — *MaNGO — Adaptable Graph Network Simulators via Meta-Learning*;
- NeurIPS 2025 — *Dynamics-Aligned Latent Imagination in Contextual World Models for Zero-Shot Generalization*.

Candidate thesis:
> infer a latent transport/environment context and adapt one shared source model to the new context.

The cross-source residual transfer test above is a direct negative control for its simplest physical premise:
- the same wind/context change does **not** induce a source-independent response correction;
- discrepancy is strongly source×transport dependent.

A context-adaptive model could still condition jointly on source, but once that interaction is made explicit it converges conceptually toward the current **candidate-conditioned missing-physics** M1 rather than remaining a distinct context-only paradigm.

Decision:
- latent-context/meta-adaptation is not promoted above M1;
- retain only as a possible implementation tool for rapid adaptation of the candidate-conditioned corrector.

## 26. Updated confidence boundary

Current positive support for M1 now comes from three independent kinds of evidence:

1. **remote SciML theory/paradigm** — verified Nature Communications 2026 + NeurIPS 2025 hybrid-correction work;
2. **cross-House exact-physics premise** — opposite-wind exact candidate responses give 12/12 correct two-source ranks across H01–H03;
3. **deployable-provider failure anatomy** — H01 estimated transport reverses source rank, with structured, sign-changing and candidate-dependent discrepancy.

What remains missing:
- the estimated-provider rank-reversal evidence itself is currently H01-specific;
- no trained learned corrector has yet passed a held-House / held-wind source-margin gate;
- therefore M1 remains **ACTIVE PRIMARY CANDIDATE / NOT VALIDATED MAIN INNOVATION**.


## 27. M2 necessity strengthened: η-aware objective separates useful correction from blank collapse

A fixed scalar-correction family was evaluated on the H01 SA-fast **estimated sensor response** against the observed sensor history. This is not proposed as the final corrector; it is a mechanism test asking whether rare-event/intermittency statistics discriminate physically useful corrections that ordinary MSE cannot.

Observed event statistics:
- first >0.1 ppm: 228.8 s;
- hit fraction: 0.01333;
- q99: ~0.1399 ppm;
- peak: ~0.4141 ppm;
- top-1% mean: ~0.2811 ppm;
- integrated response: ~1.405 ppm·s.

Five fixed correction families were compared:

1. unscaled estimated response:
   - log1p MSE ~0.007338;
   - large tail/event-statistic mismatch.

2. MSE-optimal scalar (~0.06755):
   - log1p MSE improves to ~0.000740;
   - but **all >0.1 ppm hits disappear**;
   - peak falls to ~0.086 ppm;
   - this is a classic blank-dominated optimum.

3. peak-matching scalar (~0.32453):
   - preserves nonzero event topology much better;
   - MSE ~0.001491.

4. integral-matching scalar (~0.26030):
   - preserves event/top-tail structure best in this probe;
   - MSE ~0.001184;
   - first hit ~231.6 s, hit fraction ~0.0217, peak ~0.332 ppm, integral exactly matched.

5. null response:
   - MSE ~0.000806;
   - no events at all.

A predeclared composite η-distance over first-arrival, hit fraction, q99, peak, top-1% mean and integrated exposure gives:
- unscaled ~2.364;
- MSE-optimal ~1.153;
- peak-match ~0.281;
- integral-match ~0.122;
- null ~1.663.

Interpretation:
> ordinary forward MSE and event-preserving correction rank the candidate correction families differently.

This is exactly the mechanism needed for the 2026 η-learning transfer:
- M1 learns the structured missing-physics correction;
- M2 constrains that correction by rare/intermittency observables so it cannot win by collapsing to the dominant blank regime.

M2 is therefore no longer justified only by qualitative “whiff importance”; it has an explicit existing-data failure mode and a discriminating objective-level premise.

## 28. Primary M1 citation verified

The principal remote-domain source was rechecked against the Nature version of record:

- Wang, H., Wang, Q., Yuan, C. & Wu, K.
  *Learning missing physics from legacy simulators with alternating neural integrators*.
  **Nature Communications 17, 7877 (2026)**.
  Published 23 June 2026.
  DOI: **10.1038/s41467-026-74002-2**.

The article explicitly defines the target regime as a **model–reality gap** caused by unresolved physics or structural incompleteness, and explicitly positions ANI as a non-intrusive **reuse-and-correct** framework around a fixed callable prior. It also demonstrates effective subgrid correction in turbulence.

This is the strongest current paradigm-level provenance for M1.


## 29. M1+M2 composition capacity test — structured correction can beat the false candidate without erasing events

A deliberately tiny oracle family was used only as a representational-capacity test on H01 SA-fast:

[
hat y_t =
egin{cases}
a_1,	ilde y_t,&t<t_c,\
a_2,	ilde y_t,&tge t_c .
end{cases}
]

This is **not** a deployable fitted model and uses the observed target only to test whether a lightweight time-structured correction family can simultaneously:
1. restore the true-candidate response rank against the false SB/null candidate; and
2. preserve source-informative event statistics.

Baseline:
- false SB/null log1p MSE: ~0.0008061.
- uncorrected estimated SA MSE: ~0.0073375.

Grid-search mechanism results:

**Pure MSE optimum**
- (t_capprox231.5) s, (a_1approx0.775), (a_2approx0.05);
- MSE ~0.0004056, comfortably better than false SB;
- but only 8 hits survive, so it still under-represents the event structure.

**η-regularized optimum**
- (t_capprox232.0) s, (a_1approx0.775), (a_2approx0.125);
- MSE ~0.0005443, still better than false SB;
- 21 hits survive;
- peak ~0.372 ppm and integral ~1.347 ppm·s, both close to observation.

**Best event-feasible correction that still beats false SB**
- (t_capprox233.0) s, (a_1approx0.70), (a_2approx0.075);
- MSE ~0.0007908 < false-SB ~0.0008061;
- 14 hits vs observed 16;
- peak ~0.435 vs observed ~0.414 ppm;
- integrated response ~1.424 vs observed ~1.405 ppm·s;
- top-1% mean ~0.282 vs observed ~0.281 ppm.

Interpretation:
> a **very low-capacity, time-structured** corrector is already expressive enough to cross the source-ranking boundary without destroying the rare-event topology, whereas one global scalar cannot.

This is important for both novelty and lightweight design:
- M1 does not need to become a surrogate CFD model;
- M2 is not cosmetic: it selects among response corrections that may have similar/better average fit but very different source-event fidelity.

The final learned corrector must reproduce this behavior on held conditions without oracle tuning. If it cannot, the candidate is killed.
