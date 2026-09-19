# Auxiliary Candidate — Censoring-Aware Survival Evidence for Finite-Horizon GSL

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: ACTIVE AUXILIARY CANDIDATE / OFFLINE FALSIFICATION ONLY

## Scientific origin

Survival / time-to-event analysis treats an event that has not occurred by the end of observation as **right-censored**, not as an observed negative event time.

Recent top-venue anchors:
- ICLR 2025 — Davidov et al., *Conformalized Survival Analysis for General Right-Censored Data*.
- ICML 2025 — Sesia & Svetnik, *Doubly Robust Conformalized Survival Analysis with Right-Censored Data*.
- AISTATS 2025 — Alberge et al., *Survival Models: Proper Scoring Rule and Stochastic Optimization with Competing Risks*.

## GSL transfer

Event:
- first physically valid gas arrival / threshold crossing on an observed sensing path.

Observed event:
- gas arrival occurs within the finite sensing horizon.

Right-censored case:
- no arrival is observed by horizon T.
- This means only T_arrival > T on the observed path; it does **not** mean the source is false.

This directly addresses a recurrent project failure:
some source×transport combinations have no finite-horizon exposure, and posterior logic cannot manufacture missing physical support.

## Existing-data premise

Using the pre-existing 0.1 ppm physical threshold on the current-runtime controlled histories:

At T = 120 s:
- H01 SA/SB: both censored in fast and slow winds -> no source distinction; correct action is abstention.
- H02 SA/SB: both censored -> no source distinction; abstention.
- H03: SA observed (63.2/89.6 s fast/slow), SB censored -> held-wind identity 2/2.

At T = 180 s:
- H01: both censored -> abstention.
- H02: SA censored; SB arrival 153.8/154.8 s -> 2/2.
- H03: SA observed; SB censored -> 2/2.

At T = 240 s:
- H01: SA arrival 229.0/229.2 s; SB censored -> 2/2.
- H02: SA censored; SB arrival 153.8/154.8 s -> 2/2.
- H03: SA 63.2/89.6 s; SB 207.6/208.6 s -> 2/2.

The mechanism matches the project's physical-support chronology:
source identity emerges only when the finite-horizon observation makes the relevant event distinguishable.

## Novelty boundary

Not novel:
- treating hit/miss as Bayesian evidence;
- using a first-arrival time as a scalar feature;
- saying that nondetection is informative.

Potentially novel auxiliary:
- explicitly model finite-horizon non-arrivals as censored time-to-event evidence inside a source-probability inference system;
- couple observed extreme events (M1 EVT-aware evidence) with censored event-time semantics, so missing extremes are not misread as observed negative evidence.

Direct search did not find a 2025/2026 robotic turbulent GSL paper framed as right-censored survival inference.
Older GSL literature does update source likelihood from detection and nondetection, so the contribution must be the censoring semantics / modern survival loss, not nondetection per se.

## Why this is complementary to EVT-aware M1

EVT-aware learning is strongest when informative upper-tail events are observed.
Its blind spot is precisely the case where the event is absent within the finite horizon.

Survival analysis supplies the missing semantics:
- observed tail event -> use event magnitude/timing;
- no event by T -> use censored survival contribution;
- do not convert censoring into source impossibility.

## Lightweight implementation

No large second network is required.

Possible implementation:
- M1 temporal encoder / tail head outputs candidate-specific event hazard or survival score;
- M2 uses a censored survival loss / likelihood term:
  - observed event: log f_s(t)
  - censored event: log S_s(T)
- output remains the PMFS-compatible source probability map.

## Kill conditions

Kill M2 if:
1. censor-aware likelihood does not improve calibration/source rank over matched hit/miss and first-arrival baselines;
2. its apparent gain is entirely explained by a single fixed threshold;
3. the event process is not reproducible across transport realizations/public datasets;
4. a direct recent GSL method already uses the same right-censoring formulation.

## Current decision

ACTIVE AUXILIARY CANDIDATE.
Strong conceptual match to finite-horizon physical support.
Needs a multi-realization/public-dataset gate before paper-level promotion.
