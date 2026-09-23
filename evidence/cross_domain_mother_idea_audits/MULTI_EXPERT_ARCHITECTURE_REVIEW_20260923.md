# Multi-expert review after HCMC/HCCE/MZ failures

Date: 2026-09-23
Status: **architecture-level research decision; no new method is promoted or named**

## 1. What is being preserved

The project should preserve the useful classical PMFS chassis:

- occupancy / free-space map;
- source-hypothesis grid / quadtree;
- a spatial probability map over possible source locations;
- Native planner / trajectory framework as the baseline;
- the existing candidate simulator as a forward-model primitive when useful.

The project is **not** constrained to preserve PMFS's existing evidence semantics or pointwise Bayesian-style update.

The acceptable design space is therefore:

> keep the classical probability-map framework, but replace one or more core inference modules by a genuinely different cross-domain scientific mechanism, provided the transferred mechanism survives source-specific falsification.

This is analogous to using a classical tracking framework/library while replacing its core representation/update/association modules with new scientific ideas.

## 2. Failure-driven requirements for any replacement

Any future main mechanism must explicitly address the failures already observed:

1. HCMC: static realization-specific descriptors can look excellent and fail on a new stochastic plume.
2. HCCE: a strong temporal signature can encode transport regime rather than source identity.
3. HCTLA: some ideas require data that the accepted artifacts do not contain.
4. HCDG / ACIA / IDG: positive endpoint gains are insufficient when null separation/source identity is weak.
5. MZ proxy: adding temporal history is not evidence for a source-specific memory kernel.
6. Geometry shortcuts: endpoint centroids can improve for reasons unrelated to gas-source evidence.
7. Low-information states: the method must remain mathematically defined and avoid false-confidence collapse.

Therefore the next main innovation should not merely be another descriptor of the final static candidate hitMap.

## 3. Expert-panel perspectives

### A. Gas-source-localization / robotics perspective

Keep PMFS as the spatial belief chassis because:
- it gives a natural source map;
- it integrates with the existing planner;
- it is a fair classical baseline;
- it makes ablation and closed-loop comparison straightforward.

But replace the **source evidence generator / belief update**, not just add a small multiplier.

### B. Turbulent-transport / statistical-physics perspective

The scientifically richest new information recovered by standalone replay is the ordered 200 x 0.2 s source-conditioned transport process that PMFS previously collapsed into one occupancy-frequency map.

Therefore future main ideas should preferentially operate **before temporal averaging**, on:
- particle/cell transitions;
- first-passage/reachability;
- reactive flux;
- coherent transport;
- stochastic path ensembles.

### C. Molecular-physics / rare-event perspective

The most source-specific remote-domain concept currently identified is **Transition Path Theory / committor / reactive flux**.

Why it fits the failure mechanism:
- it does not require one plume realization to match another;
- it asks whether stochastic transport from a candidate source can *reach the observed sensor-support regions*;
- source identity is represented as source-to-observation reachability / reactive flux under the current transport field;
- transport changes are handled by changing the operator, rather than pretending the source signature is invariant;
- low-information conditions naturally yield broad/weak reachability evidence instead of an undefined structure function.

Recent anchors:
- 2026 Reactive Flux Matching: mechanism discovery from reactive trajectory ensembles;
- 2026 committor-function work in molecular dynamics;
- public TPT implementations exist (PyTPT, augmented TPT, FEM committor solvers).

**Decision:** highest-priority mother-theory audit once replay dynamics are available for enough cases. Do not call it a localization method yet.

### D. Developmental / single-cell biology perspective

A second genuinely different idea is **unbalanced transport of probability mass** (Wasserstein-Fisher-Rao / unbalanced optimal transport).

Recent anchor:
- ICLR 2026 WFR-FM, motivated by single-cell population dynamics with simultaneous displacement and birth/death of mass.

Why it matches the PMFS probability-map chassis:
- PMFS already represents belief as nonnegative spatial mass;
- classical pointwise reweighting can prematurely collapse probability;
- an unbalanced transport update can move belief through source space while also creating/removing mass according to evidence;
- map geometry can enter the transport cost;
- weak/contradictory evidence need not irreversibly zero out a hypothesis.

But this is **not source evidence by itself**.

**Decision:** promising replacement for the belief-update layer, not yet the main physical source-evidence mechanism. It should be tested only after a source-specific evidence mechanism exists.

### E. Computational-neuroscience perspective

Continuous attractor neural dynamics are a major theory of how the brain represents continuous spatial variables robustly.

2026 provides a public CANN toolkit.

Potential transfer:
- PMFS probability map becomes a continuous attractor field;
- local recurrent excitation preserves coherent hypotheses;
- global/long-range inhibition prevents diffuse false modes;
- external source evidence drives the field;
- multimodality and recovery after bad evidence may be better than pointwise multiplication.

However, this primarily solves **belief stability / integration**, not the stochastic-plume source-identity problem.

**Decision:** possible auxiliary module; not the first main innovation to test.

### F. Topological / distributed-sensing perspective

Cellular sheaf / sheaf-Laplacian methods provide a principled way to fuse heterogeneous local observations and quantify global incompatibility.

Potential transfer:
- gas, wind, local map and candidate evidence can be treated as local sections;
- only mutually compatible local evidence contributes strongly to the global source map;
- inconsistent regions become a source-blind observability/conflict diagnostic.

Again, this is a consistency layer, not yet a source-specific forward mechanism.

**Decision:** possible auxiliary reliability module.

## 4. Routes explicitly closed or deferred

Do not re-open without new evidence:
- HCMC / cross-scale slope matching;
- HCCE / causal emergence as source identity;
- current MZ static-hitMap memory proxy;
- direct time-irreversibility / entropy-production proxy from the CStar gas trace;
- simple large-deviation/SCGF path statistics that do not beat hit-rate-preserving temporal shuffles;
- simple Koopman/delay fingerprints that fail the source x transport identity gate.

These failures must remain in the permanent ledger.

## 5. Architecture recommended by the panel

The most coherent future paper architecture, **if the corresponding mechanisms pass**, is:

### Classical chassis
PMFS probability / quadtree source map and planner.

### Main scientific replacement
A source-specific **stochastic transport-to-observation mechanism**, with Transition Path Theory / committor / reactive flux currently the highest-priority mother theory.

This would replace static candidate similarity as the main source evidence.

### Possible update-layer innovation
Use unbalanced probability-mass transport (WFR/UOT-style dynamics) to evolve the source belief map rather than pointwise Bayes-like multiplication.

This would be a major update-rule change while preserving the PMFS map concept.

### Possible reliability / active layer
A source-blind consistency or observability layer (e.g. sheaf consistency, or later a carefully justified active-sensing mechanism).

No auxiliary module is promoted until the main source mechanism survives intervention tests.

## 6. First kill test for Transition Path Theory family

No localization posterior yet.

Using deterministic candidate replay, for each candidate source construct only transport quantities that precede the final time-average:

- first-arrival time to observed sensor-hit cells;
- probability/reachability of entering hit-support regions within 40 s;
- survival / non-arrival to persistent no-hit regions;
- reactive cell-to-cell flux into observed-hit sets.

Necessary source-specific phenomenon:

> candidates spatially near the true source must have systematically stronger / earlier source-to-hit reactive transport than wrong candidates, and this ordering must remain informative across independent stochastic plume realizations and source x transport intervention.

Immediate rejection if:
- truth-near candidate rank is not better than random / Native static score;
- temporal ordering adds nothing beyond final hitMap occupancy frequency;
- source identity fails under transport intervention;
- a trivial encounter-rate baseline explains the result.

Only after this passes may a source-localization score be designed.

## 7. Why this is not a "small PMFS patch"

A small patch would be:
- alter one weight;
- add a smoothing factor;
- change a Bayes likelihood;
- add one posterior multiplier.

The proposed research space is larger:

> PMFS remains the chassis and probability-map representation, while the **meaning of evidence and potentially the mathematics of belief evolution are replaced** by mechanisms imported from rare-event molecular dynamics / transport theory / biological population dynamics.

That is comparable to retaining a classical tracker framework while replacing its core appearance model, association model and update dynamics with new modules.

## 8. Current priority order

1. Finish deterministic replay extension beyond one H01 run.
2. Audit Transition Path Theory / reactive-flux necessary phenomenon.
3. If it fails, reject it before designing a localization method.
4. Next audit a genuinely different source mechanism.
5. Only after one source mechanism passes, test WFR/UOT as the probability-map update replacement.
6. Only then consider auxiliary consistency / active modules.
