# AVSE V1 — Anytime-Valid Source Elimination

Date: 2026-09-21  
Branch: `research/anytime-valid-source-elimination-v1`  
Status: **DEMOTED / INTERNAL COLLISION FOUND**

## 1. Previous line is closed

TPSD V1 is frozen as `NO_GO_ON_NATIVE_300S_ENDPOINT`.

A nonnegative, sum-to-one optimization of its temporal/evidence-channel weights on the same six R2 endpoint cases is not an admissible rescue experiment: it would optimize against a frozen negative evaluation set. TPSD remains closed.

## 2. Main thesis

**Turbulent gas-source localization should be formulated as sequential falsification of source hypotheses under dependent evidence, rather than repeated multiplication of heuristic compatibility scores.**

For each source hypothesis (s), maintain an anytime-valid sequential test/evidence process asking whether the observed history is still compatible with (s).

A distinct physical observation may create evidence once. Map propagation, resampling, cell expansion, repeated source updates, or repeated processing of that observation may redistribute state but may not create additional evidential mass.

False source hypotheses are progressively rejected/downweighted; surviving hypotheses define the spatial source map.

## 3. Preferred V1 route: induce a sequential test from a strong terminal source test

The preferred first realization is **not** to invent another arbitrary betting score.

Use the recent induced-sequential-test result:

- start from a predeclared valid fixed-horizon source-consistency test;
- sequentialize that test so its current value represents its conditional terminal rejection behavior;
- preserve the terminal test at the fixed horizon while gaining anytime-valid stopping semantics.

For this project the natural terminal object to investigate first is the already-positive nuisance-robust source-identity statistic (the affine/quotient spatial consistency signal), **not** the failed TNQC posterior tilt itself.

This is a materially different scientific object from “multiply another likelihood into PMFS”.

## 4. Modern remote-field roots

- NeurIPS 2025 — Kilian, Cortinovis & Caron, *Anytime-valid, Bayes-assisted, Prediction-Powered Inference*.
- JRSS Series B 2026 — Koning & van Meer, *Anytime validity is free: inducing sequential tests*.
- JRSS Series B 2026 — Choe & Ramdas, *Combining evidence across filtrations*.

Transferred principle:

> continuously monitored evidence needs a sequential validity law; repeated computational reuse of one observation is not new evidence.

The cross-filtration result is especially relevant if gas, wind, spatial-support, or event-level evidence streams are later combined, because validity of a process in one information filtration does not automatically survive naïve fusion into a richer filtration.

## 5. Why the project now points at evidence semantics

The strongest current internal premise is not “there is no source signal”.

The frozen 240-s controlled VGR audit already reports:

- 12/12 correct affine/quotient source identity at full support;
- both disjoint checkerboard support halves independently recover the correct source in 12/12;
- 100 independent positive-scale perturbation runs retain 100% affine accuracy;
- 100 independent background-offset perturbation runs retain 100% affine accuracy;
- far-from-source support still retains 11/12 affine accuracy.

Yet the authoritative TNQC V5 300-s localization gate produces essentially zero pooled improvement and 6/6 false-confident-collapse cases.

Therefore a plausible bottleneck is:

**source-discriminative information exists, but its conversion into recursively sharpened posterior mass is scientifically wrong or poorly calibrated.**

This is a premise for AVSE, not proof that AVSE will improve endpoint localization.

## 6. GSL realization

At each distinct physical sensor event (k):

1. Update the source-consistency state using only information newly revealed at event (k).
2. For each live candidate (s), update its induced sequential test / e-process.
3. Reject or attenuate (s) only according to a predeclared anytime-valid rule.
4. Do not re-count the event when PMFS later propagates, repartitions, or revisits the same derived map quantity.
5. Keep unsupported candidates unresolved rather than forcing posterior concentration.

Output remains a PMFS-compatible source-location map.

## 7. Hard novelty boundary

Not new by itself:

- SPRT / sequential testing;
- e-values, e-processes, test martingales;
- Bayesian source posteriors;
- source-hypothesis pruning;
- ordinary cumulative likelihood;
- confidence calibration.

Targeted GSL novelty hypothesis:

**induced anytime-valid sequential falsification of physics-based gas-source hypotheses with event-unique evidence accounting, coupled to a PMFS spatial source map under turbulent dependent observations.**

A targeted 2025/2026 search has not found a direct GSL/OSL implementation of this construction. Recent GSL does contain “sequential inference”, so the novelty claim must remain specifically about anytime-valid source falsification/evidence accounting rather than the word “sequential”.

## 8. Cheap falsification ladder

### Gate A — controlled 240-s mechanism asset

Use H01/H02/H03 × SA/SB × fast/slow only as a mechanism screen.

Require:

- correct candidate elimination when source identity becomes physically supported;
- abstention before support;
- invariance to duplicated/replayed observations at the evidence-accounting level;
- no evidence change from propagation-only steps;
- no degradation relative to the terminal affine test at 240 s;
- destructive controls showing the result is not just cumulative amplitude or sample count.

This gate does **not** establish full localization.

### Gate B — authoritative native 300-s R2 endpoint

Use House01/02/03 × seed0/1 and the original
`ExpectedValue(sourceProbability,0.05)` endpoint.

Comparators:

- native PMFS;
- ordinary cumulative event likelihood;
- bounded/clipped cumulative score;
- fixed-horizon source test;
- AVSE sequentialized test.

Promotion bar before closed loop:

- pooled endpoint improvement >= 2%;
- at least 4/6 cases non-worse;
- no new false-confident collapse;
- improvement beyond fixed-horizon/clipped controls;
- truth-independent calibration / leave-one-House-out where calibration is required.

No 2/5/10-minute substitute endpoint.

## 9. Internal collision audit and decision

A repository-wide collision search found that the project already contains:

- `OPGSL/CP_Stopping.hpp`: an explicit Hoeffding-supermartingale **E-Process Stopping Rule** with anytime-valid inference;
- `OPGSLScientificV31`: a time-uniform prequential source-model skill verifier.

The old e-process is used primarily for convergence/stopping rather than candidate-wise source elimination, so the exact proposed construction is not identical.

However, this is still too close to an already-used project idea to support the clean new main thesis now required.

**AVSE = DEMOTED / DO NOT PROMOTE AS THE NEW MAIN INNOVATION.**

Candidate-wise induced sequential source tests may remain a future auxiliary mechanism, but the project should continue searching for a different mother idea.
