# Loop 7 — Venue Integrity Correction and JEPA Provenance Audit

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: literature integrity audit complete for current M1/M2/M3 line.

## 1. Important correction

The 2026 paper *Representation Learning for Spatiotemporal Physical Systems* is **not being counted as an ICLR 2026 main-conference paper**.

The arXiv/public manuscript explicitly states:
- Published at ICLR 2026 Workshop on AI & PDE.

It remains valuable as the most directly relevant physical-system transfer evidence:
- latent-space JEPA representations outperform pixel-level VideoMAE representations for downstream governing-parameter estimation on active matter, shear flow, and Rayleigh–Bénard convection;
- however, it cannot satisfy the “recent top main venue” requirement by itself.

## 2. M1 top-main-venue provenance repaired

The paradigm-level M1 source is therefore JEPA / latent predictive representation as a **broader 2025 top-conference family**, with the physics workshop used only as domain-transfer support.

Main-conference anchors:

### ICML 2025 — M3-JEPA
*Multimodal Alignment via Multi-gate MoE based on the Joint-Embedding Predictive Architecture*
- latent predictive alignment;
- separation of shared vs modality-specific information;
- generalization to unseen datasets/domains;
- computational efficiency.

### CVPR 2025 — AnySat
*One Earth Observation Model for Many Resolutions, Scales, and Modalities*
- JEPA-based self-supervision over heterogeneous sensors/resolutions;
- one model trained across multiple Earth-observation datasets;
- external-dataset transfer demonstrated.

### NeurIPS 2025 — seq-JEPA
*Autoregressive Predictive Learning of Invariant-Equivariant World Models*
- main-track predictive joint-embedding architecture;
- explicitly addresses the invariance/equivariance tradeoff in downstream adaptation.

### ICLR 2025 — D-JEPA
*Denoising with a Joint-Embedding Predictive Architecture*
- main-conference evidence that JEPA is an active paradigm extending beyond standard discriminative SSL.

Supporting physical transfer:
- ICLR 2026 Workshop on AI & PDE — *Representation Learning for Spatiotemporal Physical Systems*.

## 3. Consequence for current main claim

The paper narrative must **not** be:
> “ICLR 2026 proved JEPA is best for physical systems.”

The defensible narrative is:
> JEPA is a rapidly developing top-conference self-supervised paradigm in 2025; a dedicated 2026 physics study provides direct evidence that latent predictive objectives preserve governing-parameter information better than pixel reconstruction on several physical systems. We test whether that principle transfers to turbulent source inference.

This satisfies the user’s requirement better:
- paradigm source = multiple current top main venues;
- remote-physical support = latest dedicated physics work;
- GSL-specific mechanism = independently falsified with project data.

## 4. Direct GSL collision boundary tightened

A major 2026 adjacent collision is:
- Advanced Materials 2026 — *Receptor-Mimetic Stereo Olfaction for Simultaneous Odor Recognition and Spatial Localization (AROMA)*.
- AROMA converts plume onset/rise/amplitude dynamics into a learned latent representation and performs source localization.

Therefore these claims are **not novel**:
- “use plume dynamics rather than static concentration”;
- “learn a latent representation of olfactory time series”;
- “use a Transformer on spatiotemporal odor features”.

Surviving novelty boundary for M1:
1. source-blind predictive self-supervision before source probing;
2. latent future prediction rather than supervised latent fusion;
3. explicit destructive target-time control showing temporal prediction is load-bearing;
4. probability-map output rather than direct coordinate regression;
5. cross-simulator / cross-house representation transfer.

## 5. M2 provenance integrity

Primary:
- Nature Communications 2026 — Chang & Sapsis, *Extreme Event Aware (η-) Learning*.

This is a strong peer-reviewed journal anchor.
The transferred mechanism is statistical regularization by an observable that characterizes rare/extreme regimes.

Supporting fluid-physics context:
- Physical Review Fluids 2025 — *Universality of extreme events in turbulent flows*.
- Physical Review Fluids 2026 — latent-space control of extreme events in turbulent flows.

Important implementation correction:
- M2 should be η-style statistical regularization, not tail-feature concatenation.
- the naive concatenation proxy has already shown a negative H03 case.

## 6. M3 provenance integrity

Main-conference anchors:
- ICLR 2025 — *Wasserstein-Regularized Conformal Prediction under General Distribution Shift*.
- ICLR 2025 — *Error-quantified Conformal Inference for Time Series*.
- ICML 2025 — *Optimal transport-based conformal prediction*.
- ICML 2025 — *Volume Optimality in Conformal Prediction with Structured Prediction Sets*.

This is sufficient recent top-main-venue provenance for a spatially structured, shift-aware source region.

## 7. Current 1+2 after venue audit

M1 MAIN:
**Predictive latent physical representation / JEPA-class self-supervision**
- top-main-venue paradigm provenance: ICML/CVPR/NeurIPS/ICLR 2025;
- direct physical-transfer evidence: ICLR 2026 AI&PDE workshop;
- project destructive temporal-order test: PASS 3/3 Houses.

M2 AUX:
**Extreme-event-aware intermittency preservation**
- Nature Communications 2026;
- project rare-event rescue premise: positive but naive concatenation negative control retained.

M3 AUX:
**Structured shift-aware source region**
- ICLR/ICML 2025 main-conference conformal literature;
- directly addresses confident-wrong source maps and public-dataset shift.

## 8. Remaining issue

M1 remains the leader, but not frozen.
The stochastic-multiscale NeurIPS 2025 line remains the strongest competing M1 because it has a more direct turbulence interpretation and less adjacency collision than generic spatiotemporal latent representation.

Next loop:
- test whether stochastic multiscale coupling has an incremental observable beyond the predictive M1;
- search for 2025/2026 top-main-venue predictive-information / latent-dynamics work that could give M1 an even more distinctive scientific object than “JEPA”.
