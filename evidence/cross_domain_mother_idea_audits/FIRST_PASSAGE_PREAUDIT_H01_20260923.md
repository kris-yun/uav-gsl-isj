# Mother-idea audit pre-screen — transport age / first-passage structure

Date: 2026-09-23
Branch: `research/cross-domain-mother-idea-audits-20260923`

Status: **GLOBAL-SUMMARY PROXY NO-GO; CELL-LEVEL FIRST-PASSAGE TEST STILL OPEN**

This is not a method definition and does not create a new localization score.

## 1. Motivation after the multi-expert review

The verified standalone H01 replay established candidate-internal dynamics without perturbing the ROS closed loop.

A key conceptual correction is that, within one PMFS source update, candidates share the same wind/geometry transport dynamics. The source hypothesis changes the injection location. Therefore the scientifically natural source-dependent object is not a distinct transfer operator but the **passage/reachability structure produced by different injections under the common transport dynamics**.

The candidate internal step is interpreted as **transport age**, not robot time.

This motivates first-passage / transition-path quantities rather than real-time temporal alignment.

## 2. Cheap global-summary proxy tested first

Before requesting a new cell-level derived table, the existing `step_summary.csv` was used for a deliberately cheap falsification.

For each of 152 H01_R2026092201 evaluated candidates, available dynamic summaries include:
- filament centroid vs transport age;
- covariance;
- active filament count;
- number of occupied cells at each internal step.

The measured field centroid over Free cells with confidence > 1e-6 was approximately:
- probability × confidence centroid: (-5.2743, -3.1599)
- probability-only centroid: (-5.2273, -3.1667)

Truth source used only for evaluation:
- (-0.4, -2.9)

Candidate source coordinates come from the already verified replay parity table.

## 3. Result

No simple global transport-summary quantity is strongly source-specific.

Spearman association with negative source distance:

- minimum filament-centroid distance to measured centroid: **0.116**
- average filament-centroid distance: **0.134**
- final filament-centroid distance: **0.147**
- maximum covariance trace/spread: **0.216**
- integrated occupied-cell count: **-0.066**
- late occupied-cell count: **0.080**
- Native score: **0.109**
- source-point distance to measured centroid geometry baseline: **0.180**

The nearest-truth candidate's percentile under the dynamic centroid-distance proxies is only about **0.52–0.55**, i.e. essentially non-discriminative.

Therefore:

> merely exposing global plume centroid/spread evolution does not create useful source identity.

This proxy is rejected.

## 4. Why this does not yet reject first-passage / transition-path theory

First-passage theory is fundamentally **target-specific**. It asks whether particles injected from candidate source (s) reach particular cells/regions, with what probability and at what transport age.

Global centroid/covariance intentionally discard the target-specific path structure.

The verified replay package contains the required lower-level data:
- per-step occupied-cell events;
- filament positions;
- from/to cell transitions.

Therefore the actual necessary mechanism can still be tested without changing Native PMFS.

## 5. Required next derived table

Create source-blind from the already verified H01 replay:

For every `candidate_id × free_cell`:
- ever_hit;
- first_hit_internal_step;
- first_hit_internal_time_s;
- last_hit_internal_step;
- occupied_step_count;
- fraction_of_200_steps_occupied;
- optional number of distinct occupancy episodes.

If filament identities can be reconstructed from the binary trace without ambiguity, additionally:
- filament-level first-arrival count;
- conditional first-arrival mean/quantiles.

Do not use truth while creating the table.

## 6. Actual kill test to run after table exists

Compare two representations using direct candidate truth identity, not top-5% endpoint:

### Static control
Only the final 200-step occupancy frequency already present in Native hitMap.

### Passage representation
Use first-arrival / transport-age structure.

Required positive evidence:
1. nearest-truth candidate rank improves materially over static control;
2. passage score has stronger relation to candidate truth distance than static hitMap;
3. a control that preserves final per-cell occupancy frequency but destroys first-arrival order removes the advantage;
4. constant/near-constant measured fields remain mathematically defined.

Fail any of 1–3 -> close the first-passage route.

Only if H01 mechanism pre-screen passes should the deterministic replay be expanded and the test repeated on old + independent plume cases, then CStar source × transport intervention.

## 7. External mother-theory anchors

Recent external literature identified with scite:
- 2025 SIAM J. Applied Mathematics, *Mean First Passage Times for Transport Equations*, DOI `10.1137/24M1647667`.
- 2026 J. Chemical Physics, *A continuous-space analytical framework for committor functions from molecular dynamics*, DOI `10.1063/5.0337005`.
- 2026 *Reactive Flux Matching: Mechanism Discovery and Adaptive Sampling of Rare Events*, arXiv `2606.06295`.
- 2025 JFM, *Transport and mixing in control volumes through the lens of probability*, DOI `10.1017/jfm.2025.10631`.

Public reference implementations/ecosystems include `deeptime-ml/deeptime` and `LuzieH/pytpt`.

No method is promoted from these references.
