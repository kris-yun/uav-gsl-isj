# Candidate — Hybrid Missing-Physics Correction for Turbulent GSL

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: ACTIVE PRIMARY CANDIDATE / OFFLINE FALSIFICATION ONLY

## 0. One-sentence thesis

Turbulent GSL should not replace PMFS's physical forward model with a black-box estimator; it should treat the deployed transport model as a **trusted but structurally incomplete simulator** and learn only the missing physics that causes candidate source responses to disagree with real/high-fidelity plume observations.

## 1. Main remote-domain paradigm

### Hybrid mechanistic–data-driven modeling / non-intrusive missing-physics correction

Primary 2026 anchor:
- Nature Communications 2026 — Wang et al., *Learning missing physics from legacy simulators with alternating neural integrators*.

The key scientific idea is the model–reality gap:
- a mechanistic prior is informative and executable;
- its errors are structured because some physics is unresolved or simplified;
- replacing the prior wastes physical knowledge;
- blindly trusting the prior creates systematic downstream inference error;
- therefore alternate/reuse the prior with a learned correction targeted only at the structured discrepancy.

The load-bearing object is not “a neural network”. It is a **prior evolution operator plus a learned discrepancy/correction operator**.

Supporting recent anchors:
- Nature Communications 2025 — *Bridging known and unknown dynamics by transformer-based machine-learning inference from sparse observations*.
- ICLR 2025 — *Model-Agnostic Knowledge Guided Correction for Improved Neural Surrogate Rollout*.

## 2. Why this maps directly to the project

The current project already contains a clean prior-vs-reference contradiction.

### High-fidelity candidate-conditioned forward responses preserve source identity

CSTAR_M1_EXACT_COUNTERFACTUAL_TRANSFER V1/V2:
- H01: 4/4 true source rank-1;
- H02: 4/4;
- H03: 4/4;
- total: 12/12 rank-1 under the two-source controlled bank.

The later V2 audit correctly withdrew the old confidence calibration, but the ranking fact remains.

### Deployable simplified provider destroys the response family

CSTAR_M1_TEMPORAL_PROVIDER_ALIGNMENT_DIAGNOSTIC_V1:
- mean log-shape correlation with GADEN reference: H01 0.234, H02 0.183, H03 0.159;
- the provider predicts nonzero exposure through most of the mission while the filament reference is sparse/intermittent.

This is structural model discrepancy, not ordinary white noise: sparse filament transport is being replaced by an almost-continuous response family.

### Same-provider H01 diagnostic shows direct localization consequence

For H01 SA-fast:
- approximate-provider true-SA log1p MSE: 0.0073375;
- null/SB response MSE: 0.0008061;
- ordinary ranking therefore prefers SB although SA is the actual source.

For H01 SB-fast, SB remains correctly preferred.

This asymmetry matters: the discrepancy is candidate-dependent, so a global nuisance subtraction or scalar posterior tempering cannot repair it.

## 3. New structured-discrepancy diagnostic

The stored H01 SA-fast approximate-provider sensor trace was compared against the frozen observed history.

Observed event:
- >0.1 ppm approximately 229.0–232.0 s;
- peak 0.414 ppm around 230.2 s.

Approximate provider:
- >0.1 ppm approximately 229.8–238.4 s;
- peak 1.276 ppm around 234.6 s.

Residual structure:
- lag-1 residual autocorrelation ≈ 0.995;
- lag-5 ≈ 0.882;
- lag-10 ≈ 0.633.

Evaluator-only low-dimensional correction probe:
- raw log1p MSE = 0.0073375;
- amplitude-only oracle fit -> 0.0007236 (~90.1% reduction);
- joint shift+scale oracle fit -> 0.0002111 (~97.1% reduction).

This probe is NOT deployable and uses the target observation to fit the correction. Its only purpose is mechanism diagnosis: a very small correction family can explain a large fraction of the observed provider error, so “learn the missing correction” is a falsifiable and lightweight premise rather than a call for a new full plume model.

## 4. Proposed 1+2 architecture

### M1 MAIN — Non-Intrusive Missing-Physics Corrector

Let the frozen/deployable PMFS transport provider produce a candidate-conditioned prior response y_prior^s(t). Learn a small correction operator C_phi that evolves alongside the prior. The precise alternating/composition law must preserve the non-intrusive prior-corrector principle; a plain arbitrary additive output bias is a baseline, not the proposed mechanism.

Pipeline:
source candidate -> prior transport response -> learned missing-physics correction -> persistent sensor dynamics -> event likelihood -> PMFS-compatible source probability map.

Scientific thesis: cross-environment GSL fails primarily when the forward model is structurally incomplete; correcting the forward physics should precede changing the Bayesian posterior.

### M2 AUX — Continuous-Time Correction State

Primary 2026 anchors:
- ICLR 2026 — *Stochastic Optimal Control for Continuous-Time fMRI Representation Learning*.
- ICLR 2026 — *DeNOTS: Stable Deep Neural ODEs for Time Series*.

Project-specific reason:
- CTT already proved that native 0.2 s first-passage phase contains source information;
- compressing 80 native samples into eight HIT blocks destroys that information;
- the H01 provider discrepancy itself contains multi-second phase/tail error.

Transfer: learn the discrepancy as a continuous-time latent correction process rather than a blockwise/static correction. This is not route control or OED.

Hard gate: the continuous-time correction must beat an architecture-matched discrete/block correction while preserving native first-passage destructive controls.

### M3 AUX — Extreme-Event-Aware η-Regularization

Primary anchor:
- Nature Communications 2026 — Chang & Sapsis, *Extreme Event Aware (η-) Learning*.

Project-specific reason:
- gas traces are dominated by long quiescent intervals;
- source-defining evidence can appear in rare short whiffs;
- generic predictive/smoothing proxies previously erased H01 source identity.

Transfer: constrain the correction model with statistics of a physically predeclared extremeness observable η so that training does not minimize bulk error by washing out rare source-informative excursions.

Candidate η observables:
- threshold-exceedance probability;
- first-arrival/onset time;
- burst duration / top-tail exposure;
- native first-passage phase statistics.

η is an auxiliary training constraint; it is not itself the source score.

## 5. Why these three modules are non-redundant

M1: the physical prior is structurally incomplete.
M2: the correction must preserve continuous-time phase/order because coarse aggregation destroys source information.
M3: training must not ignore rare intermittent events because ordinary losses are dominated by zeros/quiescent periods.

Chain: incomplete transport model -> continuous-time discrepancy correction -> extreme-event-aware training -> corrected candidate likelihood -> source probability map.

## 6. Collision screen

Direct 2025/2026 GSL search found PINN inversion, generic neural inversion, Mamba/SSM backtracking, RL/random-search localization, neuromorphic/event-based gas localization, and molecular-communication source inversion.

Current search did NOT find a GSL/OSL method whose main contribution is non-intrusive reuse-and-correct of an existing PMFS/GADEN-style candidate forward provider by learning structured missing physics, with continuous-time and extreme-event-aware correction.

Collision boundary:
- “physics-informed NN” is not novel;
- “residual network on PMFS” is not sufficient;
- novelty must reside in the scientific model-discrepancy formulation and prior-corrector composition, with M2/M3 shown load-bearing by matched ablations.

## 7. Lightweight contract

- keep the existing PMFS physical/provider step;
- correction network sees only residual state/context;
- no 3-D plume decoder;
- no large transformer/foundation model;
- continuous-time correction dimension must be small;
- η-regularization adds no deployment network;
- final map update reuses PMFS likelihood/posterior interface.

Target: one small correction model, not three separate backbones.

## 8. Existing-data falsification gates before any closed loop

Gate A — structured discrepancy: premise PASS on H01 SA; residual is highly autocorrelated and a simple oracle correction removes >97% of log-MSE. Still required on more cases.

Gate B — correction transfer: train correction without target source/wind and test held source/wind. Must improve response NLL/Brier, first-passage timing and true-source rank. If correction only fits each case independently, M1 fails.

Gate C — prior necessity: compare prior only, correction-only black box, additive residual, and alternating prior-corrector. M1 requires the alternating form to win on held House/wind with lower or comparable parameter count.

Gate D — M2 timing: continuous-time corrector must beat a discrete/block corrector and lose its gain under time permutation / phase-label shuffle.

Gate E — M3 extreme events: η-regularization must improve rare-event timing/tail calibration and source ranking beyond the same corrector trained with ordinary loss.

## 9. Public-data path

1. VGR/GADEN: prior = current deployable PMFS/local transport provider; reference = held GADEN histories.
2. TURB-Smoke/DNS: prior = low-order/advection-diffusion or reduced plume model; reference = DNS trajectories/fields.
3. Real wind tunnel: prior = simulation/reduced physical model; reference = measured gas/wind trajectory.

The shared question is not whether one neural network transfers unchanged across all simulators. It is whether the same prior-corrector principle systematically improves source-conditioned physical likelihood across distinct model-reality gaps.

## 10. Hard kill conditions

Kill M1 if a direct recent GSL paper already applies non-intrusive missing-physics correction to candidate source likelihoods; residual corrections do not transfer; a correction-only black box matches the prior-corrector; gains are only scalar amplitude calibration; or better response fit does not improve source ranking.

Kill M2 if native timing adds no incremental source evidence after M1 correction.

Kill M3 if ordinary loss matches η-loss on rare-event and source-ranking gates.

## 11. Current verdict

M1 — Hybrid Missing-Physics Correction: STRONG ACTIVE PRIMARY CANDIDATE.
M2 — Continuous-Time Correction State: ACTIVE AUXILIARY CANDIDATE.
M3 — Extreme-Event-Aware η-Regularization: ACTIVE AUXILIARY CANDIDATE.

Relative to prior candidates:
- stronger project-mechanism match than JEPA;
- lower direct novelty collision than inverse diffusion/flow;
- unlike LDT, survives the theory-name-removal test because removing the missing-physics principle leaves only a generic residual network and loses the frozen-prior/structured-correction composition;
- unlike causal invariance, explicitly allows candidate-dependent transport discrepancy rather than assuming it can be removed globally.

No closed-loop run is authorized.

## 12. Loop-10: symbolic and temporal-correction screen

### 12.1 Symbolic residual discovery — useful, but not yet a separate contribution

Recent remote-domain anchors:
- Nature Computational Science 2026 — Yu, Ding & Li, *Discovering network dynamics with neural symbolic regression*.
- Nature Computational Science 2026 — Ruan et al., *Discovering physical laws with parallel symbolic enumeration*.
- Nature Communications 2025 — Hu et al., *Learning interpretable network dynamics via universal neural symbolic regression*.

Direct web collision search did not find symbolic-regression gas/odor source-localization work.

However, the 2026 ANI paper already includes post-hoc symbolic distillation/write-back of learned discrepancy in selected controlled systems. Therefore “ANI + symbolic distillation” would be too close to the source paper if counted as an independent auxiliary innovation without a GSL-specific mechanism gain.

Decision:
- retain symbolic residual discovery as a lightweight interpretability/compression option;
- DO NOT count it as M2/M3 yet.

### 12.2 Prefix-to-future phase/amplitude correction

The H01 SA-fast approximate-provider trace was used for a strictly diagnostic temporal split.

Fixed diagnostic:
- fit only on observed/predicted log-response from 226–232 s;
- choose a constant phase shift plus scalar amplitude from that prefix;
- apply the frozen correction to 232–240 s.

Prefix fit:
- learned phase shift: -4.2 s in the implemented sign convention, i.e. advance the delayed prior response by ~4.2 s;
- log-amplitude factor: 0.280.

Held future tail:
- uncorrected prior log-MSE: 0.20698;
- zero/null-response log-MSE: 0.000995;
- prefix-fitted corrected SA log-MSE: 0.000194;
- reduction versus prior: ~99.91%;
- crucially, the corrected true-SA response now beats the null/SB response on the held tail, whereas the uncorrected prior does not.

This is still one development case and is not a deployable PASS, but it is stronger than an all-data oracle fit because the correction parameters are frozen before the future tail is scored.

Interpretation:
> a large part of the candidate-dependent model discrepancy can be expressed as a low-dimensional **phase + amplitude correction**, and correcting it can reverse the wrong-source preference caused by the incomplete prior.

### 12.3 Probabilistic time-warping auxiliary collision

Remote anchor:
- ICLR 2026 — *Perturbed Dynamic Time Warping: A Probabilistic Framework and Generalized Variants*.

The idea is a natural match to the measured phase error, but direct collision search found:
- Sensors and Actuators B: Chemical 2026 — *Exploring pre-ignition source localization using a 3D network of semiconducting metal oxide gas sensors*, where a DTW separability score is already used for source-localization sensor selection.

Therefore:
- plain DTW/soft-DTW cannot be claimed as a new GSL auxiliary;
- if temporal registration is retained, its novelty must be inside the missing-physics correction operator, not “we use DTW for localization”.

### 12.4 Consequence for M2

The old M2 label “generic continuous-time correction” is too broad and is weakened by the historical CTT neural first-passage NO-GO.

The data now point to a narrower object:
> **adaptive phase–amplitude discrepancy state** inside the prior-corrector.

A future M2 must show:
1. phase/amplitude discrepancy is estimable from a past prefix;
2. the frozen correction improves future candidate likelihood/rank;
3. it beats static scalar calibration;
4. the effect survives more than H01 SA-fast;
5. it is not equivalent to a DTW similarity score.

Until those gates pass, M2 remains conditional.

## 13. Current candidate status after loop-10

M1 — Non-Intrusive Missing-Physics Correction:
**STRONG ACTIVE PRIMARY CANDIDATE.**

M2 — Adaptive Phase–Amplitude Discrepancy State:
**CONDITIONAL AUXILIARY CANDIDATE.**
The H01 prefix-to-future result is a strong premise, but cross-case replication is missing.

M3 — Extreme-Event-Aware η-Regularization:
**ACTIVE AUXILIARY CANDIDATE.**

Symbolic residual discovery:
**RESERVE LIGHTWEIGHT/INTERPRETABILITY TOOL, not counted as an innovation.**


## 14. Cross-House structural-mismatch expansion

The approximate temporal provider failure is not H01-only at the response-shape level.

Frozen evidence:
`evidence/cstar_m1_temporal_provider_alignment_20260909.json`

Across all 12 controlled source×wind cases:

### H01
- mean log-shape correlation: 0.234.
- approximate provider nonzero fraction minus GADEN nonzero fraction: mean +0.912.
- support inflation factors across the four cases: ~7.3×, 12.4×, 61.2×, 232×.

### H02
- mean log-shape correlation: 0.183.
- mean nonzero-support gap: +0.881.
- support inflation factors: ~5.3×, 7.2×, 63.2×, 94.8×.

### H03
- mean log-shape correlation: 0.159.
- mean nonzero-support gap: +0.497.
- support inflation factors: ~1.33×, 1.35×, 6.27×, 6.34×.

Thus the simplified provider systematically transforms sparse/intermittent physical support into a much denser response family in **all three Houses**, not only H01.

This does not yet prove that a learned correction improves source ranking in H02/H03, because stored deployable rank-reversal traces are available only for H01.
But it upgrades the M1 premise from:
> “one H01 bad fit”

to:
> “a repeated cross-House structural model-reality gap, with one directly demonstrated localization rank reversal.”

The cross-House exact counterfactual bank remains the complementary positive control:
- exact candidate-conditioned responses give true-source rank 1 in 12/12 cross-wind tests.

Therefore the central contrast is now present in every House:
- high-fidelity candidate-conditioned physics preserves source identity;
- the cheap deployable provider has strongly distorted temporal support/shape.

### Updated M1 evidence boundary

M1 premise: **CROSS-HOUSE PASS at structural-discrepancy level**.

M1 correction efficacy: **H01-only development evidence so far**.

No held-House learned-corrector claim is authorized.
