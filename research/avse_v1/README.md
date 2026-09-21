# AVSE V1 — Anytime-Valid Source Elimination

Date: 2026-09-21  
Branch: `research/anytime-valid-source-elimination-v1`  
Status: **MAIN-INNOVATION CANDIDATE / OFFLINE FALSIFICATION ONLY**

## 1. Closure of the previous TPSD simplex-weight rescue

TPSD V1 is already frozen as `NO_GO_ON_NATIVE_300S_ENDPOINT`.

The proposed nonnegative, sum-to-one weight optimization over temporal/candidate evidence channels is therefore **not admissible as a rescue test on the same six R2 cases**. Optimizing convex weights against those endpoints would be post-hoc tuning of a frozen negative screen. Any apparent gain would not count as independent evidence.

Scientific consequence: TPSD remains closed. Do not spend the main-innovation slot on a better fusion rule for the same weak ingredients.

## 2. New mother idea

### Main thesis

**Turbulent gas-source localization should be formulated as sequential falsification of source hypotheses under dependent evidence, rather than repeated multiplication of heuristic compatibility scores.**

For each candidate source (s), maintain an anytime-valid evidence process that asks whether the observed sequence is still statistically compatible with (s).

A distinct physical sensor event may contribute evidence once. Map propagation, resampling, repeated candidate-cell updates, or repeated processing of the same observation may redistribute state but may not manufacture additional evidential mass.

False candidates are progressively rejected; surviving candidates define the source map.

## 3. Remote-field scientific roots

Primary modern roots:

- NeurIPS 2025 — Kilian, Cortinovis & Caron, *Anytime-valid, Bayes-assisted, Prediction-Powered Inference*.
- JRSS Series B 2026 — Koning & van Meer, *Anytime validity is free: inducing sequential tests*.
- JRSS Series B 2026 — Choe & Ramdas, *Combining evidence across filtrations*.

Transferred principle:

> evidence accumulated under continuous monitoring must remain valid under adaptive stopping and dependent information flows.

This is not ordinary confidence calibration and not another posterior-temperature rule.

## 4. Why it matches the project failure

Existing project evidence repeatedly shows that sharper internal confidence can coexist with worse true-source localization.

Relevant frozen observations include:

- TNQC V5: six-case integrity pass, but 6/6 false-confident collapse and essentially zero pooled endpoint gain.
- TPSD V1: ordinary cumulative temporal likelihood is slightly negative on the native 300-s endpoint; generic inhibition can improve true-source rank while degrading the actual endpoint.
- Active-deconfounding V1: all six required gates fail because false-source alternatives can remain observationally indistinguishable.
- MIPO V1: deliberate motion creates measurable modulation, but not reliable source-direction information.

These failures are consistent with an evidence-accounting problem: compatibility transformations can repeatedly sharpen a map without establishing new source-specific information.

They do **not** yet prove that AVSE improves localization.

## 5. GSL realization

At each distinct sensor event (k):

1. For every live source candidate (s), compute a causal candidate-conditioned residual/score from information available at that event.
2. Convert that event score into a valid bounded betting/evidence increment using a calibration rule fixed without endpoint truth tuning.
3. Update one source-specific evidence process (E_s(k)).
4. Reject/downweight a candidate only when accumulated evidence against it crosses a predeclared threshold.
5. Spatial propagation may move/expand candidate support but cannot multiply the event evidence again.

Output remains a PMFS-compatible source-location map.

## 6. Hard novelty boundary

Not claimed as new:

- sequential probability ratio testing;
- Bayesian source posteriors;
- confidence sequences/e-values themselves;
- ordinary likelihood accumulation;
- source-hypothesis pruning.

Targeted novelty hypothesis:

**event-unique anytime-valid elimination of physics-based gas-source hypotheses under correlated turbulent observations, integrated with a PMFS-style spatial source map.**

Current targeted searches found no direct GSL/OSL implementation of e-process / anytime-valid source-hypothesis elimination. This remains a search result, not an exhaustive novelty proof.

## 7. Cheapest decisive offline gate

Use only the frozen VGR/GADEN R2 House01/02/03 seed0/1 six-case traces and the native 300-s top-5% ExpectedValue endpoint.

No 2/5/10-min substitute metric.

Comparators:

- native PMFS;
- ordinary cumulative event likelihood;
- bounded/clipped cumulative score;
- terminal fixed-horizon candidate test;
- AVSE sequential evidence.

Required controls:

- **duplicate-event control:** replaying the same physical event must not create additional evidence;
- **propagation-only control:** PMFS propagation without a new observation must not change evidence wealth;
- **support/erasure control:** no source claim when the observation contains no candidate-specific physical support;
- **wrong-candidate calibration control:** calibration cannot use final source truth from the evaluation case.

Promotion bar before any ROS/closed-loop work:

- pooled 300-s endpoint improvement >= 2% over native;
- at least 4/6 cases non-worse;
- no new false-confident collapse;
- improvement must exceed the terminal-test and clipped-cumulative controls;
- result must survive leave-one-House-out or equivalent truth-independent calibration.

## 8. Current decision

**AVSE = GO FOR CHEAP OFFLINE FALSIFICATION ONLY.**

It is not yet authorized for closed loop.

It currently ranks above another TPSD fusion rescue because it changes the semantics of evidence rather than tuning the weighting of already-failed evidence channels.
