# Candidate — Rare-Event Rate-Function Source Inference for Turbulent GSL

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: ACTIVE PRIMARY CANDIDATE / OFFLINE FALSIFICATION ONLY

## 0. One-sentence thesis

In turbulent GSL, source identity is often carried disproportionately by the statistics of **rare, high-information plume excursions**, so source evidence should be built from a candidate's rare-event rate structure rather than from average concentration compatibility or generic temporal encoding.

## 1. Mother scientific idea

### Large-deviation / rare-event statistical mechanics

The scientific object is not “a tail feature”. It is the **rate at which unlikely concentration/exposure events occur** under a source-conditioned transport process.

For a block observable A_tau (e.g. block-averaged concentration or another predeclared source-relevant observable), the large-deviation form is

P(A_tau ≈ a | s) ~ exp[-tau I_s(a)]

where I_s(a) is a source-conditioned rate function.

The proposed GSL translation is:

source candidate s
  -> stochastic turbulent transport
  -> distribution of block observables / exceedances
  -> empirical or learned rate object I_s
  -> source evidence by compatibility of observed rate structure with I_s
  -> PMFS-compatible source probability map.

Important: the current existing-data experiment estimates only **finite-horizon empirical rate proxies**. A full asymptotic large-deviation claim is not yet authorized.

## 2. Recent remote-domain provenance

Primary recent anchors:

1. Nature Communications 2026 — Chang & Sapsis, *Extreme Event Aware (η-) Learning*.
   - learns models constrained by statistics of an observable indicating extremeness;
   - explicitly targets rare regimes that ordinary data-driven learning under-represents;
   - theoretical justification uses optimal-transport arguments.

2. Nature Communications 2026 — Feng et al., *Breaking through safety performance stagnation in autonomous vehicles with dense learning*.
   - formalizes the “curse of rarity” and shows that learning should concentrate on informative rare/near-critical data rather than treating all common samples equally.

3. Physical Review E 2026 — Werner & Hartmann, *Numerical estimation of limiting large-deviation rate functions*.
   - rate functions remain the central rare-event object; emphasizes biased/rare-event sampling and rate-function estimation.

Foundational physical match:
- passive-scalar turbulence has heavy tails/intermittency and has been analyzed with instanton/large-deviation formalisms.
- this is a real physical match to gas transport, not a metaphor imported from unrelated classification.

## 3. Project phenomenon this candidate explains

Repeated project evidence shows:

- H02 has no usable source signal at early horizons, so ordinary inference cannot manufacture source identity.
- H01 source-defining evidence appears late/intermittently; generic predictive smoothing can erase it.
- native first-passage/timing carries information that coarse HIT compression can destroy.
- exact candidate-specific physical response can preserve source identity while approximate/global representations mix source and transport.
- probability maps can become sharp even when source identity is wrong.

This motivates a failure-first question:

> Is the part of the plume that discriminates source hypotheses concentrated in rare exposure statistics rather than in the bulk distribution?

## 4. Existing-data empirical rate proxy

For each trace, non-overlapping block means were formed at fixed block scales (2 s, 5 s, 10 s).

At predeclared physical concentration thresholds

[0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3] ppm,

a finite-horizon exceedance-rate proxy was computed:

I_hat_tau(c) = -(1/tau) log P_hat(block_mean >= c).

The vector over thresholds is treated as an empirical source-rate fingerprint.

No source labels are used to define the thresholds.

## 5. Existing-data result A — rate structure vs ordinary tail summaries

Cross-wind comparison over the existing controlled 2-source factorial histories:

### H01
- 120–240 s, 5 s blocks:
  - rate ratio (wind/source distance) ≈ 0.131, held-wind identity 2/2.
  - ordinary tail-stat ratio ≈ 0.098, also 2/2.
- 150–240 s, 5 s blocks:
  - rate ratio ≈ 0.019, 2/2.
- 180–240 s, 5 s blocks:
  - rate ratio ≈ 0.040, 2/2.

### H02
- 120–240 s:
  - rate ratio ≈ 0.18–0.20 across 2–10 s block scales, 2/2 identity.
- 150–240 s:
  - same result: 2/2 and source-dominant.
- 180–240 s:
  - rate ratio ≈ 0.91–1.0 and only 1/2 identity.

This late H02 failure is valuable: the rate object does **not** hallucinate source identity when the late interval itself is physically non-identifying.

### H03
- 120–240 s:
  - rate ratio ≈ 0.34–0.45 and 2/2 identity across 2–10 s blocks.
  - simple tail summaries fail badly (0/2 over the same long interval).
- 150–240 s:
  - rate ratio ≈ 0.38–0.52 and 2/2.
  - simple tail summaries remain 0/2.
- 180–240 s:
  - rate retains 2/2 across block scales.

This is the strongest current mechanism-specific positive result:
> the **shape of the exceedance-rate curve** preserves cross-wind source identity in H03 where ordinary tail-amplitude summaries do not.

## 6. Existing-data result B — cumulative held-wind source discrimination

A source-blind two-source evaluator was used only to compare representations.

For each House and horizon 60/120/180/240 s:
- fast-wind rate vectors are treated as frozen source references;
- slow-wind trace is matched to the nearer reference.

Across all 24 held-wind decisions:

- finite-horizon rate vector: 19/24 correct = 79.2%;
- raw summary statistics: 18/24 = 75.0%;
- ordinary tail summaries: 16/24 = 66.7%.

Approximate Brier-like score under the same fixed distance-to-probability mapping:
- rate: 0.102;
- raw: 0.122;
- tail: 0.136.

Mechanism-specific examples:
- H01 at 180 s: rate = 2/2 while raw and tail are 1/2.
- H03 at 240 s: rate = 2/2; ordinary tail = 0/2; raw = 2/2.
- H02 at 60/120 s: all methods remain unresolved, consistent with missing early physical support.

## 7. Negative control — marked temporal point-process auxiliary

A separate proxy extracted whiff events at 0.01/0.03/0.1 ppm and used:
- event counts/rates;
- first/last event time;
- duration;
- peak mark;
- event area;
- inter-arrival gap statistics.

Recent remote support for MTPPs exists at NeurIPS 2025 and ICLR 2026.

However, on the same 24 held-wind decisions:
- marked-event proxy = 18/24 = 75%;
- rate proxy = 19/24 = 79.2%;
- rate + point-process proxy = 19/24 = 79.2%.

Therefore a point-process module currently adds no independent evidence.

Decision:
- DO NOT count MTPP as an auxiliary innovation.
- temporal/event structure remains a possible implementation detail only if a later ablation shows incremental value.

## 8. Proposed 1+2 architecture

### M1 MAIN — Rare-Event Rate-Function Source Evidence

For candidate source s, learn or estimate a source-conditioned rare-event object over admissible transport contexts:

I_s(a; context)

or a finite-horizon surrogate.

Observed rare-event structure produces a source score such as

E_s = D(I_obs, I_s)

and the PMFS-compatible map is

P(s | Z) ∝ P_0(s) exp[-β E_s].

The scientific contribution is the replacement of bulk/mean compatibility by **rare-event-rate compatibility**.

### M2 AUX — Extreme-Event-Aware η-Regularization

Primary anchor:
- Nature Communications 2026, *Extreme Event Aware (η-) Learning*.

Role:
- rate functions are hard to learn because informative plume events are rare;
- enforce statistics of a physically chosen extremeness observable η during model training;
- reduce the tendency of a lightweight model to fit quiescent bulk behavior and ignore source-defining tails.

Possible η observables for screening:
- threshold-exceedance curve;
- top-tail block exposure;
- onset/first-arrival statistic;
- whiff duration/blank duration distribution.

M2 is not “append whiff features”; it is a **training constraint on the learned source-conditioned rate model**.

### M3 AUX — Distribution-Informed Online Spatial Calibration

Primary recent anchor:
- ICLR 2026, *Distribution-informed Online Conformal Prediction*.
Supporting 2025 work:
- ICLR/ICML conformal methods under distribution shift and structured prediction sets.

Role:
- convert sequential source scores into a calibrated spatial source region;
- allow the region to expand/abstain under House/simulator/real-sensor shift;
- do not claim that conformal localization itself is new.

Novelty target:
> online distribution-informed calibration of a sequential rare-event source-probability field under transport-regime shift.

## 9. Why this is different from existing whiff/intermittency GSL

Collision screen found:
- classical and recent olfactory navigation work already uses whiff/blank frequency, duration and intermittency;
- outdoor plume work predicts source distance from hand-designed odor statistics;
- 2026 biological work studies neural representation of intermittent odor stimuli.

Therefore the main claim cannot be:
> “intermittency matters” or “use whiff statistics”.

The surviving claim is narrower and stronger:
> construct source evidence from a **source-conditioned finite-horizon rare-event rate object**, and learn/calibrate that object with recent rare-event-aware statistical machinery.

The H03 result is important because the rate curve succeeds where ordinary tail summaries fail.

## 10. Lightweight contract

- no full 3-D plume reconstruction;
- no large foundation model;
- rate object is low-dimensional over a fixed observable grid;
- candidate-conditioned predictor may be a small MLP / spline / monotone head;
- η regularization is an auxiliary loss/statistical constraint;
- M3 is a small online calibration layer;
- runtime must remain compatible with PMFS source-map cadence.

## 11. Public-data compatibility

Required data:
- concentration time series or fields that can be sampled along trajectories;
- source location label;
- optional local wind/context;
- repeated contexts or multiple source realizations preferred.

Validation ladder:
1. VGR/GADEN — cross-house/cross-wind.
2. TURB-Smoke — DNS, five point sources, turbulent intermittency.
3. real wind-tunnel GSL challenge if source-position diversity is confirmed.
4. Red:Vapor for real-sensor/intermittency transfer, not by itself a multi-source benchmark.

## 12. Hard kill conditions

Kill M1 if:
1. a direct GSL paper already uses a source-conditioned large-deviation/rate-function inference map;
2. held-wind rate evidence loses its advantage on an independent source bank or extra seeds;
3. the rate curve is statistically indistinguishable from a simpler threshold-count vector after matched dimensionality;
4. gains disappear when block dependence is treated correctly;
5. no usable rare-event support is available within mission horizons on the public datasets.

Kill M2 if η-regularization does not improve held-context rate estimation beyond ordinary tail weighting.

Kill M3 if coverage can only be maintained by expanding to nearly the full map.

## 13. Current verdict

M1: ACTIVE PRIMARY CANDIDATE.
M2: ACTIVE AUXILIARY CANDIDATE.
M3: CONDITIONAL AUXILIARY CANDIDATE.

Current evidence level:
- stronger than JEPA after its matched predictive-vs-PCA null;
- stronger than Koopman/operator identity because cross-wind rate structure is more stable across Houses;
- stronger than rough-path signatures, which were transport-dominated;
- still provisional because current rate estimates use temporally correlated samples from a small controlled bank.

Next required step:
- audit block-dependence / effective sample size;
- test rate-vs-threshold-count equivalence;
- search direct 2025/2026 large-deviation/rare-event GSL collisions;
- test on independent evidence assets before any closed loop.
