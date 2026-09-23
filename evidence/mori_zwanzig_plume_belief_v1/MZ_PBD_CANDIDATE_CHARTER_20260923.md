# Candidate Main Innovation — Mori–Zwanzig Plume Belief Dynamics (MZ-PBD) v1

Date: 2026-09-23  
Branch: \`research/mori-zwanzig-plume-belief-v1\`  
Status: **CANDIDATE / DEVELOPMENT ONLY — NO ADVANCE CLAIM**

## 0. Why this candidate exists

M4-v3 D0 did **not** fail because wind was ignored.

On the frozen House02 development holdout:

- predicted wind-response amplitude reached about 0.58–0.64 of the real GADEN intervention;
- relative wind/source response and centroid-displacement magnitude gates passed;
- removing characteristic advection reduced predicted wind-response norm to about 0.107–0.111 of the full model;
- nevertheless, wind-delta cosine remained only about 0.34–0.38 in all four comparisons;
- one field-MSE comparison also lost to the frozen monolithic baseline.

Therefore M4-v3 learned a meaningful **coarse wind-driven transport effect**, but the high-dimensional spatial response geometry was wrong.

This pattern motivates a reduced-order interpretation:

> The observed 2-D concentration field is not a sufficient Markov state for the underlying filamentary, stochastic, 3-D turbulent plume dynamics.

The missing physics should not be represented by another arbitrary deterministic spatial layer.

---

## 1. Main scientific principle

Use the Mori–Zwanzig (MZ) projection formalism as the organizing principle for plume dynamics.

Let the inaccessible full plume state be \(X_t\), containing for example:
- filament positions and ages;
- unresolved turbulent velocity fluctuations;
- vertical structure;
- wake / recirculation state;
- stochastic dispersion variables.

Let the deployable resolved observable be

\[
Y_t=P(X_t),
\]

where \(Y_t\) contains only information available to the localization stack, such as:
- coarse concentration / hit-probability representation;
- occupancy;
- estimated wind field or wind belief;
- recent observations.

The exact projected reduced dynamics are represented conceptually as

\[
\dot Y_t
=
\underbrace{M(Y_t,W_t,O,Q_s)}_{\text{Markov / resolved term}}
+
\underbrace{\int_0^t K(t-\tau;\,Y_\tau,W_\tau,O)\,d\tau}_{\text{memory term}}
+
\underbrace{\eta_t}_{\text{orthogonal / unresolved dynamics}}.
\]

This is the scientific main idea.

### Interpretation for gas-source localization

- source hypothesis \(s\) enters through the forcing \(Q_s\);
- current wind/geometry drive the resolved coarse transport term;
- wind/plume history enters through a finite-memory closure;
- unresolved turbulent/filament variability becomes a conditional stochastic term;
- PMFS consumes the resulting predictive observation distribution as a source likelihood.

The key shift is:

> do not predict one deterministic plume field from a source candidate; predict a **history-conditioned distribution of observations** under that candidate.

---

## 2. Relationship to M4-v3

M4-v3 is not discarded as useless.

It is demoted from “complete main model” to the **Markov coarse-transport component** of the MZ decomposition.

Its D0 result is evidence for this narrower role:
- characteristic transport materially drives the wind response;
- coarse displacement scale is plausible;
- but a Markov concentration-only state is insufficient for the full spatial response.

No M4-v3 failure threshold is changed or reinterpreted.

---

## 3. 2025–2026 scientific anchors

### 3.1 Memory is not an engineering trick

**Buitrago Ruiz et al., ICLR 2025, _On the Benefits of Memory for Modeling Time-Dependent PDEs_.**

Motivated by Mori–Zwanzig, the work shows theoretically that memory can be arbitrarily better than Markov reduced models and proposes MemNO. The empirical advantage is especially strong for low-resolution/noisy PDE observations and high-frequency fluid dynamics.

Relevance to this project:
our state is a low-dimensional / spatially reduced observation of a higher-dimensional turbulent system.

### 3.2 Direct turbulent-transport evidence

**de Wit et al., PNAS 2026, _Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows_, DOI 10.1073/pnas.2525390123.**

The work uses MZ plus time-delay embedding to learn turbulent Lagrangian reduced dynamics and explicitly separates present/history-dependent resolved dynamics from unresolved orthogonal dynamics.

Relevance:
pollutant/gas filaments are Lagrangian transported objects; the paper directly supports the proposition that reduced turbulent transport needs memory and unresolved dynamics.

### 3.3 2026 turbulent transport with explicit finite memory

**Freitas et al., 2026 preprint, _Learning turbulent transport via Mori–Zwanzig graph neural networks_, arXiv:2606.14918.**

The model represents turbulent tracer dynamics using current and delayed states and reports that memory is essential for intermittent statistics.

This is close prior art for turbulent transport, therefore MZ itself is **not** the novelty.

### 3.4 Stochastic closure for unresolved scales

**Dong, Chen & Wu, JCP 2025, _Data-driven stochastic closure modeling via conditional diffusion model and neural operator_, DOI 10.1016/j.jcp.2025.114005.**

The paper argues that deterministic local closures fail when unresolved dynamics are nonlinear, non-local and non-Markovian; it uses a conditional diffusion model + neural operator as a stochastic closure.

### 3.5 Deterministic coarse component + stochastic small-scale component

**Fotiadis et al., ICML 2025, _Adaptive Flow Matching for Resolving Small-Scale Physics_.**

The method first encodes deterministic/coarse components and then uses flow matching to add stochastic small-scale physics.

This separation strongly matches the M4-v3 D0 failure:
coarse transport is partly correct, but small-scale/spatial response geometry is not.

### 3.6 Hard physical constraints on generative correction

**Utkarsh et al., NeurIPS 2025, _Physics-Constrained Flow Matching_, DOI 10.52202/085713-5354.**

This provides a route to enforce conservation/boundary constraints during generative correction instead of relying only on soft penalties.

---

## 4. Prior-art boundary

Forbidden novelty claims:

- first Mori–Zwanzig model for turbulence;
- first memory model for PDEs;
- first diffusion/flow-matching model for physics;
- first neural operator for GSL;
- first stochastic plume model.

Target novelty, if evidence supports it:

> **A Mori–Zwanzig reduced plume-belief model for probabilistic gas-source localization that decomposes source-conditioned plume prediction into resolved characteristic transport, finite-memory closure, and constrained stochastic orthogonal dynamics, and uses the resulting predictive distribution directly in source-candidate Bayesian ranking.**

A targeted search on 2026-09-23 found no direct use of Mori–Zwanzig / generalized-Langevin reduced plume dynamics for gas-source localization. This is a provisional novelty observation, not an exhaustive patent/literature clearance.

---

## 5. Architecture roles

### Main framework — MZ-PBD

The MZ decomposition itself is the main innovation.

### Resolved Markov term

Use the already developed source-agnostic characteristic transport as a coarse resolved component.

It is not allowed to regain the status of a complete plume model.

### Auxiliary innovation A — finite-memory closure

Learn

\[
m_t=\mathcal K_\theta(Y_{t-h:t},W_{t-h:t},O)
\]

using a lightweight causal state-space / memory operator.

Hard rules:
- causal only;
- no future wind;
- same parameters for every source candidate;
- source enters only through resolved forcing/state;
- memory length frozen before confirmatory data.

Ablation:
set the memory term to zero.

### Auxiliary innovation B — constrained stochastic orthogonal dynamics

Model unresolved residual physics conditionally:

\[
\eta_t \sim p_\phi(\eta \mid Y_{t-h:t},W_{t-h:t},O).
\]

Candidate implementation:
- low-rank conditional flow matching or diffusion in a residual basis;
- not a full-field image generator per PMFS candidate.

The residual is projected so that it cannot trivially overwrite already-resolved large-scale transport.

Development constraint:
- zero global mass correction;
- zero first-moment correction (centroid) unless later physical analysis demonstrates that the resolved-state projection itself requires first-moment memory.

The purpose is to alter internal plume geometry/intermittency, not to secretly move the plume or rescale total concentration.

Ablation:
set stochastic orthogonal dynamics to zero / posterior mean.

---

## 6. Why this is stronger than “M4 + correction network”

A generic correction network would be post-hoc.

MZ-PBD makes a falsifiable physical claim:

> once unresolved degrees of freedom are projected out, the reduced plume dynamics must contain memory and unresolved stochastic dynamics in addition to the resolved Markov transport.

Therefore the new modules correspond to terms in a reduced-dynamics equation, not arbitrary architecture blocks.

The M4-v3 failure itself becomes a diagnostic predicted by the theory:
a Markov coarse model may capture bulk advection while failing intermittent/high-frequency response geometry.

---

## 7. Development protocol — House02 only

House02 is permanently development-only.

Do not reinterpret M4-v3 D0 as evidence for MZ-PBD.

Use the raw pre-existing House02 GADEN time series to answer only:

> Does adding finite memory and stochastic orthogonal closure correct the specific response-geometry failure without overwriting the coarse transport signal?

### D1 — memory necessity test

Compare:
1. frozen/coarse Markov term;
2. Markov + finite-memory closure.

Primary development endpoint:
- W1→W2 intervention delta cosine as a function of prediction horizon.

Secondary:
- response amplitude;
- centroid vector;
- source-intervention delta;
- field error;
- temporal autocorrelation of residuals.

A useful MZ signal requires:
- residuals of the Markov model exhibit statistically meaningful temporal correlation;
- memory term reduces that residual autocorrelation;
- memory improves intervention geometry without destroying coarse transport.

If Markov residuals are effectively memoryless:
**STOP MZ memory line.**

### D2 — stochastic orthogonal-dynamics test

Only if D1 supports non-Markovian residuals.

Compare deterministic residual closure vs stochastic closure.

Do not use single-sample MSE as primary.

Use:
- predictive log likelihood / CRPS on held-out time blocks;
- ensemble calibration / coverage;
- intermittency statistics;
- spatial spectrum / high-frequency energy;
- distribution of hit/non-hit durations at fixed probes;
- source-candidate marginalized likelihood.

If stochastic closure improves images but not observation likelihood or source rank:
**NO-GO FOR GSL MAIN METHOD.**

---

## 8. Inverse-localization endpoint

The model should output

\[
p(y_{1:T}\mid s,\;W_{1:T},O,\mathcal H_0)
\]

or a tractable approximation.

PMFS source probability then updates using the marginalized likelihood rather than a deterministic field residual.

Primary scientific endpoint remains:

\[
\boxed{\text{truth-containing source-candidate rank}}
\]

under the same observation budget.

Required comparisons:
- Native PMFS;
- matched monolithic deterministic model;
- M4-v3 Markov coarse term;
- MZ-PBD without memory;
- MZ-PBD without stochastic orthogonal dynamics;
- full MZ-PBD.

---

## 9. Fresh confirmation

House01/House03 are not generated/opened until the complete D1/D2 architecture, memory horizon, residual basis, likelihood, candidate bank and thresholds are frozen.

Minimum confirmation:
- two unseen Houses;
- two source interventions;
- two physical wind interventions;
- two independent plume realizations;
- estimated-wind and oracle-wind tracks reported separately.

House02 remains development-only.

---

## 10. Real-world constraint

A full-field diffusion model executed independently for hundreds of source candidates is not acceptable for UAV deployment.

Therefore stochastic orthogonal dynamics must be:
- low-dimensional;
- amortized across source candidates where possible;
- or used to produce a compact predictive likelihood rather than expensive full-field samples.

Deployment fails if source update latency materially changes the PMFS search budget.

The real-flight evidence ladder remains:
GADEN confirmation -> estimated-wind W0 -> hardware-in-loop -> stationary physical plume -> controlled UAV flight -> autonomous GSL.

---

## 11. Current decision

### M4-v3
**STOP remains unchanged.**

### Generic “M4 + corrective auxiliary network”
**REJECT as insufficiently scientific.**

### MZ-PBD
**PROMOTE TO SCREENING CANDIDATE.**

Reason:
it directly explains the observed M4-v3 failure through a rigorous reduced-order dynamics principle and naturally yields one main scientific idea plus two separately ablatable auxiliary mechanisms.

No model training is authorized yet from this memo alone. The next action is a source-blind residual-memory audit on the already-open House02 development trajectories.
