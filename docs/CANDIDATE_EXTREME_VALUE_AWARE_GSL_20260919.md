# Candidate M1 — Extreme-Value-Aware Source Inference

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: ACTIVE COMPETING CANDIDATE / OFFLINE FALSIFICATION ONLY

## 0. Main thesis

Turbulent source evidence is not uniformly distributed over the observation stream. A small fraction of intermittent tail events can carry disproportionate source identity, while ordinary empirical-risk, reconstruction, and predictive objectives are dominated by blank/common regimes.

The proposed transfer is from modern rare-event learning and Extreme Value Theory (EVT), not from classical hand-crafted whiff features.

## 1. Remote-field lineage

Primary 2026 anchors:
- Nature Communications 2026 — Chang & Sapsis, *Extreme Event Aware (η-) Learning*.
  - statistical regularization using an observable that characterizes extreme regimes;
  - designed to avoid models fitting common/quiescent behavior while remaining uncertain or wrong in rare regimes.
- UAI 2026 — Hasan et al., *Learning Max-Stable Representations that Extrapolate*.
  - extends max-stability into learned representations and explicitly covers infinite-dimensional observations/time series.
- ICLR 2026 — *EVEREST: A Transformer for Probabilistic Rare-Event Anomaly Detection with Evidential and Tail-Aware Uncertainty*.
  - EVT tail head is training-time only; deployment remains lightweight.
- NeurIPS 2025 — *Deciphering the Extremes: A Novel Approach for Pathological Long-tailed Recognition in Scientific Discovery*.

Scientific origin:
- Extreme Value Theory;
- peaks-over-threshold / tail laws;
- max-stability;
- rare-event statistical learning.

## 2. GSL collision boundary

Already known in turbulent odor literature:
- whiffs/blanks and intermittency are informative;
- timing vs intensity importance changes with plume sparsity;
- pairing timing and intensity can outperform individual cues.

Therefore NOT novel:
- thresholding odor into hits;
- average whiff/blank duration;
- intermittency factor;
- saying that rare whiffs matter.

Potentially novel:
- using modern EVT-aware representation/statistical regularization so a learned source-probability model preserves and extrapolates tail evidence under sparse rare events and cross-environment shift.

## 3. Existing-data tests

### 3.1 Whole-window held-wind source identity

12 controlled histories:
H01/H02/H03 × {SA,SB} × {fast,slow}.

Fixed 10 s windows, fast-wind source prototypes, slow-wind held transport, 120–240 s.

Accuracy:
- predictive-bulk summaries: 50/72 = 0.694;
- classical odor timing/intensity summaries: 51/72 = 0.708;
- tail/extreme summaries: 53/72 = 0.736;
- predictive+tail: 53/72 = 0.736;
- classical+tail: 53/72 = 0.736.

Tail observables give a small but repeatable edge over the classical feature set in this limited proxy.

### 3.2 Sparsity stratification

Sparse windows (<5% threshold occupancy):
- classical timing/intensity: 32/51 = 0.627;
- tail: 33/51 = 0.647.

Dense windows:
- classical: 16/18 = 0.889;
- tail: 17/18 = 0.944.

The advantage is not restricted to one sparsity bucket, but the sample is too small for a performance claim.

### 3.3 H01 destructive predictive test

At H01 late horizon, generic predictive compression can erase source identity.
A fixed η-tail branch restores 2/2 held-wind identity in the previous premise test.

This supports the need for rare-event preservation but does not establish EVT as sufficient by itself.

### 3.4 EVT-law / max-stable proxy

A source-blind tail-law fingerprint was tested using:
- q90/q95/q99/max;
- Hill-type tail index proxy;
- mean block maxima at multiple block sizes.

Result is mixed:
- H01 180/240 s retains 2/2 held-wind identity;
- H02 180 s fails because one source is effectively unsupported in one transport realization;
- H03 240 s remains 1/2.

Critical conclusion:
> an EVT fingerprint cannot create source identity when physical support is absent and is not uniformly transport-invariant.

Therefore the candidate must not claim a universal source-specific tail law.

## 4. Candidate architecture if M1 survives

### M1 — η/EVT-aware representation and source evidence
- lightweight temporal encoder;
- tail observable head / statistical regularizer;
- source logits constrained to retain physically meaningful exceedance/onset/tail information;
- training-time EVT branch may be removed at inference where possible.

### Potential M2 — event-aware temporal structure
Remote anchor:
- ICLR 2026 — *From Observations to Events: Event-Aware World Models for Reinforcement Learning*.
Transfer only the event representation principle:
continuous sensory stream -> learned event boundaries -> event prediction/embedding.

Reason:
EVT magnitude statistics alone ignore event order and duration, while project CTT evidence shows temporal ordering/first-passage structure can carry source identity.

Hard novelty boundary:
must exceed fixed hit/whiff segmentation; otherwise this collapses to old odor features.

### Potential M3 — structured shift-aware source region
Remote anchors:
- ICLR 2025 Wasserstein-regularized conformal prediction under general distribution shift;
- ICML 2025 optimal-transport conformal prediction;
- ICML 2025 volume-optimal structured prediction sets.

Role:
tail-aware models can still be overconfident under House/simulator/real-tunnel shift.
Return a calibrated spatial source region alongside the PMFS-style probability map.

## 5. Current score

Paradigm/source-theory strength: 10/10
2025/2026 provenance: 10/10
Direct fit to turbulent intermittency: 10/10
Collision risk with classical whiff literature: 6/10
Existing-data support: 8/10
Lightweight potential: 9/10
Cross-dataset definability: 10/10

Adjusted: 53/60 before novelty penalty refinement.

## 6. Kill conditions

Kill as M1 if:
1. learned EVT/η regularization adds nothing over classical timing+intensity features on held transport;
2. gains vanish after matched calibration for hit rate / source support;
3. performance comes only from a fixed high-concentration amplitude threshold;
4. a direct 2025/2026 GSL method already performs EVT/max-stable/tail-regularized source-map inference;
5. the same tail mechanism does not transfer to an independent DNS plume dataset.

## 7. Current decision

ACTIVE COMPETING CANDIDATE.
Not frozen.
The next required test is a learned-but-light tail-aware representation against:
- classical whiff/timing features;
- direct encoder;
- predictive/JEPAlike encoder;
using identical held-wind splits.


## 8. Auxiliary screening update — event-aware and rough-path candidates

### Event-aware segmentation: NO-GO as current M2

Recent remote anchor:
- ICLR 2026 — Peng et al., *From Observations to Events: Event-Aware World Models for Reinforcement Learning*.

A fixed proxy encoded:
- event count,
- ordered onset times,
- durations,
- peak/mass of the first events,
- event-centroid timing.

Matched 20 s held-wind test (36 decisions):
- aggregate classical features: 28/36;
- tail features: 28/36;
- event-order features: 25/36;
- tail + event: 27/36.

Time reversal changed event features as expected but did not expose a positive source-identification increment.
Decision:
> event-aware segmentation is not currently load-bearing and is rejected as M2. It risks collapsing back to classical whiff segmentation.

### Rough-path / path-signature representation: mathematically valid but no positive increment

Recent remote anchors:
- ICML 2025 — Lucchese et al., *Learning with Expected Signatures: Theory and Applications*.
- NeurIPS 2025 — *Scalable Signature Kernel Computations via Local Neumann Series Expansions*.
- ICLR 2026 — Piatti et al., *Random Controlled Differential Equations*.

A level-2/3 path signature of (normalized time, log-gas) was evaluated on the same 20 s windows.

Normal held-wind accuracy:
- tail: 28/36;
- signature: 27/36;
- tail + signature: 28/36.

Destructive time reversal:
- tail remains 28/36, as expected because it is order-free;
- signature falls 27/36 -> 20/36;
- tail + signature falls 28/36 -> 23/36.

Thus the signature correctly captures temporal order, but it provides **zero cases where signature corrects a tail error** in the current 36-decision set; it only introduces one extra error.

Decision:
> path signatures are useful as a destructive-control representation but are not promoted as an auxiliary innovation.

## 9. New leading M2 — censoring-aware survival evidence

Recent top-venue provenance:
- ICLR 2025 — Davidov et al., *Conformalized Survival Analysis for General Right-Censored Data*.
- ICML 2025 — Sesia & Svetnik, *Doubly Robust Conformalized Survival Analysis with Right-Censored Data*.
- AISTATS 2025 — Alberge et al., *Survival Models: Proper Scoring Rule and Stochastic Optimization with Competing Risks*.

Scientific mapping:
- informative plume/extreme event = time-to-event;
- no event before finite sensing horizon = right-censoring, not a negative event time.

Existing controlled-history chronology using the frozen 0.1 ppm floor:
- 120 s: H01/H02 both sources censored -> abstain; H03 distinguishes 2/2.
- 180 s: H01 still censored -> abstain; H02 and H03 distinguish 2/2 each.
- 240 s: H01/H02/H03 all distinguish 2/2, with censored vs observed or strongly separated arrival times.

This matches the physical-support audit exactly:
> source distinction should appear only when the finite horizon makes it observable.

Why it complements EVT M1:
- EVT explains how to retain information in observed rare/tail events.
- survival analysis supplies correct semantics when the rare event has **not yet occurred**.

## 10. Revised strongest 1+2 EVT architecture

### M1 MAIN — Extreme-Value-Aware Scientific Learning
Remote sources:
- Nature Communications 2026 η-learning;
- UAI 2026 max-stable representations;
- ICLR 2026 EVEREST;
- NeurIPS 2025 scientific long-tail recognition.

### M2 AUX — Censoring-Aware Survival Evidence
Remote sources:
- ICLR 2025 / ICML 2025 modern right-censored survival inference.

Role:
> distinguish “event not observed yet within T” from “source contradicted”.

### M3 AUX — Structured Shift-Aware Source Region
Remote sources:
- ICLR 2025 Wasserstein-regularized conformal prediction under shift;
- ICML 2025 optimal-transport conformal prediction;
- ICML 2025 volume-optimal structured prediction sets.

Role:
> convert the final PMFS-compatible probability map into a spatially calibrated region under House/simulator/real-sensor shift rather than trusting false sharpness.

This 1+2 now has three different remote scientific/statistical lineages:
- extreme-value / rare-event statistics,
- survival / censoring statistics,
- distribution-free conformal uncertainty.

All three address distinct project failures and can be lightweight.

## 11. Promotion status after current loop

EVT-aware M1 is now stronger than the JEPA alternative on current project evidence, but is **not frozen**.

Remaining hard gates:
1. show η/EVT-aware training gives an incremental benefit over classical whiff/timing features, not just hand-crafted tail statistics;
2. obtain multi-realization evidence so survival curves/hazards are estimable rather than single-realization proxies;
3. run direct collision search for EVT/max-stable source localization through 2026;
4. verify the same data interface on TURB-Smoke and Red:Vapor;
5. evaluate M3 only when an actual probability map from M1/M1+M2 exists.
