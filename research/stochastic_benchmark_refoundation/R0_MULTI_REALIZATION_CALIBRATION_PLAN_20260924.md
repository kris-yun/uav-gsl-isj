# Stochastic Benchmark Refoundation Plan — R0

Date: 2026-09-24

Status: **BENCHMARK REPAIR BEFORE NEXT MAIN-INNOVATION SEARCH**

This is not a new innovation. It repairs the evaluation layer that recent fresh failures exposed.

## 1. Objective

Characterize stochastic plume variability well enough that future scientific mechanisms are tested against a stable distributional benchmark rather than accidental two-seed realization structure.

Retain the existing 630-source C/D bank.

## 2. R0 calibration panel

Select a deterministic, target-blind panel of **12–24 source cells** spanning:
- low / median / high observed plume mass;
- low / median / high C/D discrepancy;
- different source-to-probe geometries;
- distance from previously used S1/S2/S3.

Freeze source selection before generating new data.

For each calibration source generate at least **16 independent W2 realizations** under the exact frozen House02/GADEN contract.

R0 is benchmark calibration, not a source-ranking experiment, so the >=143 arbitrary-candidate rule is not violated. Future method evaluation still uses the full 630 bank.

## 3. R0 measurements

For every source report:
1. pairwise relative-L2 distribution;
2. cosine distribution;
3. total plume-mass distribution over time;
4. zero/non-detection fraction;
5. first-arrival distribution;
6. concentration quantiles;
7. intermittency / heavy-tail diagnostics;
8. stability as realization count K grows.

Evaluate K = 2,4,8,12,16.

Key question:

> Does the classification of source stochasticity remain stable across disjoint seed subsets and as K grows?

## 4. R0 decision

### PASS
Advance only if by K=16 source-level stochastic summaries and low/median/high strata are materially stable across disjoint seed subsets.

### HOLD
If convergence is visible but insufficient, increase realization count before algorithm search.

### STOP for per-source distribution mainlines
If even multi-realization data do not yield stable source-conditioned stochastic descriptors with the current observation operator, do not build a main innovation around per-source path distributions.

## 5. Redesign future scientific gates

Future candidates must report three separate questions.

### A. Source-basin identifiability
- MAP spatial error;
- truth rank;
- top-k radius;
- probability mass within fixed radius when available.

### B. Realization robustness
Performance distribution across multiple fresh target realizations, not one seed.

### C. Cross-source robustness
At minimum test pre-selected low-, median-, and high-stochasticity source strata.

No candidate should be promoted from one source and two target seeds.

## 6. Data separation

From now on use disjoint:
- calibration seeds/sources;
- method-development seeds/sources;
- locked validation seeds/sources;
- one-time final test seeds/sources.

Do not keep recycling S1/S2/S3 as discovery evidence for every new theory.

## 7. Only after R0: choose the next mother theory

R0 should tell us which stochastic object is real:
- encounter/intermittency statistics;
- path ensemble;
- heavy-tail/mixture structure;
- rare-event action;
- source-conditioned distributional geometry;
- or something else.

Do not crown another theory before this empirical object is stable.

## 8. Resource rationale

A previous 300 s GADEN realization cost roughly ~1.9 s wall time on the VM.

- 12 sources ×16 = 192 runs
- 24 sources ×16 = 384 runs

This is far cheaper than repeatedly creating and falsifying entire mainlines.

## 9. New gate order

1. benchmark/statistical adequacy
2. mother-theory candidate
3. no-training proxy
4. fresh **multi-realization** validation
5. cross-source strata
6. cross-wind / cross-House
7. second-order model
8. PMFS closed loop
9. real flight
