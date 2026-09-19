# Loop 7 — Top-Venue Provenance and Collision Audit

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: INTERNAL SCREENING

## Purpose

Re-check the current 1+2 candidate against the user's hard requirement:
- each innovation must have a 2025/2026 high-level remote-domain source;
- M1 must be paradigm-level and support the paper's main thesis;
- nearby GSL/OSL work must not already implement the same scientific mechanism.

## M1 — Predictive / Joint-Embedding Representation Learning

### Verified top-main-venue anchors

1. **ICML 2025 — M3-JEPA: Multimodal Alignment via Multi-gate MoE based on the Joint-Embedding Predictive Architecture**
   - PMLR 267, ICML 2025.
   - Uses JEPA latent-space prediction/alignment rather than original token-space reconstruction.
   - Reports unseen-domain generalization and computational efficiency.
   - URL: https://proceedings.mlr.press/v267/lei25b.html

2. **CVPR 2025 — AnySat: One Earth Observation Model for Many Resolutions, Scales, and Modalities**
   - CVPR 2025.
   - Uses JEPA for self-supervised learning over heterogeneous Earth-observation sensors, scales and resolutions.
   - Evaluates on multiple external environmental-monitoring datasets.
   - URL: https://openaccess.thecvf.com/content/CVPR2025/html/Astruc_AnySat_One_Earth_Observation_Model_for_Many_Resolutions_Scales_and_CVPR_2025_paper.html

### Physical-science-specific support — NOT top-main venue

3. **Representation Learning for Spatiotemporal Physical Systems**
   - Published at the **ICLR 2026 Workshop on AI & PDE**, not the ICLR main conference.
   - Shows latent predictive / JEPA-style representation can outperform pixel reconstruction for downstream physical-parameter estimation.
   - This paper is useful mechanistic support but MUST NOT be counted as satisfying the top-main-venue provenance gate.

### Corrected provenance decision

The M1 provenance gate is therefore supported by **ICML 2025 + CVPR 2025** at the paradigm level.
The physical-specific evidence is workshop-level and only supplementary.

M1 remains eligible, but its novelty thesis must be:
> predictive latent representation of turbulent plume histories for source-probability inference,
not simply “JEPA for physical systems.”

## M2 — Extreme-event-aware intermittency preservation

### Verified top-journal anchor

**Nature Communications 2026 — Chang & Sapsis, Extreme Event Aware (η-) Learning**
- Published 20 Aug 2026; Version of Record 17 Sep 2026.
- Introduces η-learning: constrain learning using statistics of an observable indicative of rare/extreme regimes.
- Theoretical support uses optimal-transport arguments.
- URL: https://www.nature.com/articles/s41467-026-76811-x

### GSL transfer boundary

The transferable object is:
- rare/extreme observable statistics -> turbulent plume intermittency / whiff-tail statistics.

The contribution cannot be “use whiff/intermittency features,” because turbulent-odor literature already uses those features.
The proposed novelty must be:
> use extreme-event-aware statistical constraints to prevent predictive representation learning from washing out rare source-informative plume events.

M2 passes the provenance gate.

## M3 — Distribution-informed online calibration

### Verified top-main-venue anchor

**ICLR 2026 — Distribution-informed Online Conformal Prediction**
- Published as a conference paper at ICLR 2026.
- Uses predictable structure in nonconformity-score distributions to construct tighter online prediction sets while retaining coverage guarantees even when distribution estimates are inaccurate.
- URL: https://proceedings.iclr.cc/paper_files/paper/2026/hash/5f8241131e6fd428aa49914da76b8ad0-Abstract-Conference.html

### Collision boundary

Generic “conformal prediction for localization/source detection” is already occupied in adjacent localization/source-detection literature.
Therefore M3 cannot be claimed as conformal localization itself.

The only defensible transfer is narrower:
> online distribution-informed calibration of a sequential spatial source-probability field whose reliability changes with plume regime/environment.

M3 passes provenance but remains conditional on an offline sequential-map replay.

## Direct 2025/2026 GSL/OSL collision screen

Nearby work found:
- 2026 odor diffusion-state classification using UMAP + K-means;
- 2026 Advanced Materials stereo olfaction using temporal plume disparities and a learned latent representation for recognition/localization;
- 2025 robotic OSL using LLM decision making;
- 2026 RL + extremum-seeking OSL;
- 2026 INFOCOM probabilistic random-search OSL.

Important collision:
**Advanced Materials 2026 — Receptor-Mimetic Stereo Olfaction for Simultaneous Odor Recognition and Spatial Localization**
already converts plume dynamics into a unified latent representation using a multi-task Transformer.

Therefore the M1 novelty CANNOT be:
- “learn a latent representation from plume dynamics,”
- “use a Transformer on temporal plume data,”
- “learn spatiotemporal features for source localization.”

The surviving novelty boundary is substantially narrower:
1. source-blind predictive latent objective rather than supervised localization representation;
2. explicit extreme-event-aware preservation of intermittent source evidence;
3. PMFS-compatible source probability map rather than direct coordinate regression/classification;
4. heterogeneous cross-environment / cross-simulator validation.

## Current gate

- M1 top-venue provenance: PASS, with corrected anchors.
- M1 GSL collision: CONDITIONAL PASS; generic latent-representation claim is occupied.
- M2 top-journal provenance: PASS.
- M2 GSL collision: CONDITIONAL PASS; whiff features themselves are old, η-learning constraint is the candidate novelty.
- M3 top-main-venue provenance: PASS.
- M3 collision: CONDITIONAL PASS; generic conformal localization is occupied.

No module is promoted to final innovation yet.
