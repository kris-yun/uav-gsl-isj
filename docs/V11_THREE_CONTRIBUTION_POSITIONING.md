# ME-ACI V11 — three-contribution paper positioning

## Decision

Do **not** modify the frozen V11 online inference path after its held-out qualification pass.
For the paper, the strongest structure is one integrated main method with three separable technical contributions rather than V11 plus two newly tuned online modules.

The frozen runtime method remains ME-ACI V11.  This document only decomposes its scientific contribution and defines offline ablations; it does not change `Simulations.cpp`, the planner, the nuisance family, the cadence, or the evaluator.

## Contribution 1 — amplitude-conditioned inverse-transport source abduction

### Problem

PMFS is a forward simulator-based source estimator.  Under intermittent turbulent transport and model mismatch, a source candidate can receive a poor absolute forward fit even when its source-relative transport geometry is plausible.

### V11 construction

Treat each candidate source location as a candidate physical cause and the observed gas hit/miss sequence as downstream effects.  For each candidate and each frozen transport-nuisance member, use a source-relative wind-frame transport propensity and condition on the observed total hit count.  Conditioning removes an unknown additive release/sensor intercept from the binary event ordering problem.

The two temporal fold scores are subsequently mapped to candidate-relative normal ranks.  Therefore the released quantity is a **conditional inverse-transport score** and the final distribution is a **generalized/decision posterior**, not an exact Bayesian belief posterior.

### 2026 theory lineage

- Andreou, Chen & Bollt, *Assimilative causal inference*, Nature Communications 17, 1854 (2026), DOI `10.1038/s41467-026-68568-0`: strong far-domain lineage for tracing candidate causes backward from observed effects in intermittent dynamical systems.
- Wu et al., *Adaptive Nonparametric Perturbations of Parametric Models with Generalized Bayes*, JMLR 27(123), 2026: supports robust generalized updating when the scientific/parametric model may be misspecified.

No theorem from either paper is claimed to transfer directly.  V11's conditional hit-count construction, plume geometry, finite candidate source set and rank aggregation are GSL-specific.

## Contribution 2 — spatiotemporally replicated identifiability before evidence release

### Problem

A single plume encounter can be spatially coherent but causally non-identifying.  Likewise, a score that appears only in one temporal realization can be transport noise rather than source evidence.

### V11 construction

Evidence is released only when:

1. the even temporal fold contains both hits and misses;
2. the odd temporal fold contains both hits and misses;
3. hits have occurred in at least two distinct occupied sensing cells.

This is not a performance gate.  It uses no source truth, source distance, posterior entropy, final error or tuned House-specific threshold.

### 2026 theory lineage

Park, Balakrishnan & Wasserman, *Robust universal inference for misspecified models*, Biometrika 113(2), 2026, DOI `10.1093/biomet/asaf070`, develops split-sample tests of **relative fit** under model misspecification.  V11 does not inherit its confidence-set theorem, because plume events are dependent and the V11 normal-rank score is not their test statistic.  The transferable design principle is narrower: separated data views and relative agreement are safer than trusting one absolute misspecified-model score.

### Offline ablation already available

In held-out H02/seed825201:

- update 1: 32 retained events, both temporal folds have 2 hits / 16 events, but all hits occupy one sensing cell;
- update 2: 56 retained events, both temporal folds still have 2 hits / 28 events, and hits still occupy one sensing cell;
- V11 therefore abstains with `single_hit_site_no_spatial_replication`.

A truth-external offline forced-score ablation using the same frozen 201 physical candidate coordinates removes only the spatial replication rule.  At both early updates the forced top candidate is approximately **4.79 m** from the true source.  Thus the spatial replication rule prevents an early, spatially non-identifying commitment in this held-out trajectory.

This is development evidence for the contribution, not a new qualification result; the truth is used only by the offline evaluator after the counterfactual score is produced.

## Contribution 3 — fixed-prior reversible cumulative generalized posterior

### Problem

V10 solved first evidence release but not later falsification.  Once an accepted posterior was injected, accepted evidence was cleared.  A later all-miss block could be non-identifying by itself and the previous accepted posterior was then copied forward unchanged.

### V11 construction

Retain the complete accepted evidence history and rescore the whole history after every later update.  Since the cumulative score already contains old evidence, rebuild from the fixed geometry prior every time:

`q_t(s) ∝ q_0(s) exp(g_t(s))`.

Do **not** multiply the cumulative score by `q_{t-1}`, which would count retained observations twice.

The important principle is defeasibility: later observations are allowed to demote an earlier source basin.

### 2026 theory lineage

- Fong & Yiu, *Asymptotics for a class of parametric martingale posteriors*, Biometrika 113(2), 2026, DOI `10.1093/biomet/asag007`: recent predictive/sequential-posterior theory emphasizing one-step-ahead predictive structure and a posterior view not tied to a conventional prior-likelihood construction.
- Wu et al., JMLR 2026: generalized-Bayes lineage under model misspecification.

Again, V11 does not inherit their asymptotic or coverage theorems.  The transfer is the sequential/predictive and misspecification-aware design principle.

### Same-seed offline mechanism ablation

H02/seed824201 provides a direct V10 -> V11 mechanism comparison.

- V10 final ME-ACI error: **3.6017416 m**.
- V11 final ME-ACI error: **2.5407062 m**.
- V10 update-3 injected posterior -> update-4 resident posterior: maximum probability-vector difference **0.0**.
- V11 update-3 -> update-4 released posterior: maximum absolute probability change approximately **0.01739**, L1 change approximately **0.46730**.
- The 24 newly acquired update-4 events are exactly equal between V10 and V11 for position, hit flag, concentration and wind direction in the archived evidence.
- nearest-truth candidate rank improves from V10 `76/201` to V11 `68/201`.

The V11 run is still 12.19% worse than native PMFS on this already-inspected development seed, so this ablation must **not** be presented as universal accuracy success.  It establishes the structural claim: future evidence is no longer mechanically blocked from changing the accepted source state, and the former catastrophic V10 failure is substantially reduced.

## Why not add two more online modules now

Two 2025 ideas were screened as possible extra modules:

1. Online conformal prediction / risk control (ICML 2025 and NeurIPS 2025) to calibrate a set-valued source region.
2. Conformal Information Pursuit (NeurIPS 2025) to couple uncertainty-set reduction to active measurement planning.

They are scientifically attractive but should **not** be inserted into frozen V11 before the larger independent-seed experiment:

- V11 decision-posterior probabilities are deliberately not probability-calibrated; conformalization would require a separate calibration protocol and enough independent calibration trajectories.
- only three current held-out House/seed pairs exist, so a formal conformal source region would be extremely coarse and potentially uninformative;
- planner coupling would create a different treatment because the frozen qualification used `posterior_guidance_weight=0`, requiring a new preregistered planner study.

These are better positioned as a future fourth module / future work unless the larger seed bank first establishes V11 statistical generalization.

## Recommended paper contribution list

Use one method name and three contributions:

1. **Conditional inverse-transport source abduction** under intermittent plume observations and unknown amplitude.
2. **Spatiotemporally replicated identifiability** using disjoint temporal views plus multi-site hit replication before source evidence release.
3. **Reversible cumulative generalized inference** that rebuilds from a fixed geometry prior so later observations can falsify an earlier source basin without double-counting history.

This is stronger and cleaner than claiming three unrelated modules.  The three pieces solve three different failure modes and are individually ablatable, while together forming one coherent ME-ACI V11 inference framework.

## Claim boundary

Current held-out status supports an **online source-inference** claim, not a universal planner-improvement claim.  Keep the planner unchanged for the next independent-seed study.
