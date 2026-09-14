# Project Evidence Ledger

Date: 2026-09-14

Purpose: one place to distinguish confirmed evidence from promising development results, unresolved hypotheses, and rejected routes.

---

## A. Baseline / simulator contract

### Main-V8 forward contract — CONFIRMED

- `main_v8` is the authoritative forward contract.
- `dataset_v1` is excluded/frozen for authoritative forward claims.
- Exact delayed/stateful FOPDT parity has been repeatedly checked in later causal/dual-view audits.

### Historical simulator failure — RESOLVED ENGINEERING ISSUE

Earlier `rc=-11` failures were traced to `RunningSimulation::StepTowards()` recursion / zero-progress behavior near obstacle corners, causing invalid indexing / stack overflow. This was not an RMFE formula failure.

---

## B. RMFE / candidate-field ranking

### mini8 — ACTIVATION CHAIN VALID, PERFORMANCE UNSTABLE

Two OFF/ON seed pairs showed one improvement and one degradation. No stale/future factor was observed.

### H02 full32x2 — NO-GO

- OFF final error: about 3.2146 m.
- ON final error: about 3.5065 m.
- 0/2 seed improvement.

Failure attribution:

- primary: fixed-amplitude scale mismatch;
- secondary: some transport/response-shape mismatch;
- no stable lag-bias explanation.

Representative evidence:

- source-near `kcover30` had `A_hat` far above frozen `A=1`;
- wrong candidate `kcover22` ranked above the candidate nearest the true source.

**Status:** REJECTED AS MAIN INNOVATION.

---

## C. SCTT / ordered temporal transport

Full C0–C4 × seed0/1 downstream evaluation:

- C2 PCA mean error about 1.959 m (best in that screen).
- C3 SCTT about 3.157 m vs Classic about 2.425 m.
- C4 shuffle outperformed ordered SCTT.

**Status:** NO-GO. Temporal ordering / shared trajectory by itself cannot be claimed as the causal source-identification mechanism.

---

## D. Historical M1 / M1R / M2

### Event-level / contrastive M1R — DEVELOPMENT POSITIVE, NOT CONFIRMATION

Historical House123 seed12 development results included:

- final error improvement in 2/3 Houses;
- AUC improvement in 3/3 Houses.

However, later code audit found important theory–implementation mismatches:

- `cer_ratio_m1` did not strictly implement one physical StopAndMeasure = one factor;
- the historical persistence term was not a full sequential persistent FOPDT latent sensor state;
- saved artifacts were insufficient for a clean exact historical replay of all per-candidate components.

Therefore the historical result remains useful evidence that source/context contrast can change performance, but it is **not** a clean causal-identification or cross-dataset result.

### Old M2 member averaging — NO-GO

Cross-House final/AUC performance was unstable and frequently worse. Member agreement did not protect against common systematic model error.

**Status:** REJECTED AS CURRENT SECOND MODULE.

---

## E. Counterfactual source-intervention line

### Exact controlled microbank — POSITIVE PREMISE

Using exact candidate-specific GADEN response plus exact FOPDT in a 2-source × 2-wind × 3-House microbank:

- 12/12 controlled cases ranked the evaluator-only true source first under the frozen cross-wind rule.

Scientific meaning:

> source identity can survive a controlled transport change when candidate-specific physical responses are sufficiently accurate.

It does **not** prove online full-map deployability.

### Deployable estimated transport provider — FAILED

The local-wind continuum provider produced poor temporal-shape correlation and near-continuous exposure where GADEN plume support was sparse/intermittent.

Later physical/causal provider audits still did not produce a stable full-map online source-identity mechanism.

**Status:** COUNTERFACTUAL PREMISE RETAINED; DEPLOYABLE PROVIDER MAIN LINE FROZEN.

---

## F. Single-stream transformations after M1

The project tested or audited several variants including Rank-2, DPISC, LMBT, CTAER, CFIR, CCDE, SCSP and related single-stream / source-vs-transport transforms.

The important project-level conclusion is not the individual score of each variant. It is the repeated pattern:

> source-related physical effects can exist without the observation stream uniquely identifying source location.

The latest single-channel causal review therefore demoted 'keep transforming the same single-UAV concentration sequence' as the main research path.

**Status:** FROZEN / REJECTED AS THE DEFAULT MAIN LINE.

---

## G. ME-ACI / STRI / R-GAF historical line

Earlier small screens showed improvements and motivated mechanisms such as early-evidence control and reversible assimilation.

However, the later frozen multiseed qualification concluded:

`V11_MULTISEED_QUALIFICATION_NO_GO`

with at least one catastrophic regression.

Therefore:

- these mechanisms may remain historical failure-analysis tools;
- they are not established cross-domain positive evidence;
- they cannot be inserted into the current method without a newly demonstrated matching failure mechanism.

**Status:** DEMOTED / NOT CURRENT MAIN INNOVATION.

---

## H. Dual-UAV two-point structure line

### Geometry audit V1 — INITIAL STOP, LATER SUPERSEDED

The first frozen route appeared unable to support a 2 m formation. A parity audit then showed the custom occupancy parser matched the native semantics, but the historical `T_diag_A` route itself contained many blocked points and was not a deployable navigation route.

A whole-map House02 search subsequently found:

- occupancy parity: 3044/3044 agreement;
- 4958 / 6704 free center cells support a 2 m formation;
- largest feasible component about 49.42 m²;
- a 150 s / 750-point source-blind formation route passed native geometry validation.

Therefore House02 itself is not geometrically incapable of 2 m dual-UAV operation.

### Same-frame dual-receiver premise — TECHNICALLY VALID, SCIENTIFIC NO-GO

Data integrity:

- 12/12 audited caches;
- 9000 synchronized rows;
- 18000 same-frame gas queries;
- two independent persistent FOPDT channels;
- replay error = 0.

Primary signed increment:

- W_fast `sigma3/sigma1 = 0.001345`;
- W_slow `0.000683`;
- W_altfast `0.001384`.

All are far below the preregistered 0.05 premise threshold.

Held-wind source identity:

- S1 plus: 1/4;
- S1 minus: 2/4;
- Ordinary D2: 1/4;
- Signed increment: 2/4;
- squared structure: 2/4.

Destructive controls:

- receiver/position swap: 1/4;
- collapsed baseline: 1/4;
- 5 s time mismatch: **3/4**, better than correct simultaneous signed increment.

Scientific conclusion:

`STRUCTURAL_COMPLEMENTARITY_ONLY_NO_SOURCE_IDENTITY`

The simple two-point operator is rejected as the main algorithmic innovation.

### Important failure fingerprint

The route does not excite source interventions evenly:

- `S_truth`: roughly 470 exposed samples per wind;
- `S_k10`: roughly 171–291;
- `S_k01`: roughly 7–8;
- `S_k22`: roughly 0–20.

The third source mode is therefore physically present but extremely weak.

This is the strongest current evidence that **measurement design / source observability is the dominant bottleneck**.

---

## I. Current interpretation of the 5 s mismatch

The 5 s shift must not be promoted to a lag-based method.

A strong confound exists:

- dual-UAV baseline: 2 m;
- historical robot speed: about 0.35 m/s;
- `2 / 0.35 ≈ 5.71 s`.

Thus a 5 s shift may align one receiver with a spatial location recently visited by the other receiver rather than measure plume-advection time.

Historical local wind in R3B was also much slower than robot translation, making a 5 s plume-advection interpretation physically questionable.

**Status:** CURRENTLY TESTING — geometry/wind timescale audit only; no lag algorithm authorized.

---

# J. Current research-state summary

## CONFIRMED

1. The project has many negative results showing that more complex source evidence does not overcome missing source information.
2. Exact controlled forward responses can preserve source identity in a small counterfactual microbank.
3. Deployable approximations and ordinary trajectories often collapse source-identifying directions.
4. Dual-UAV simultaneous measurement is physically feasible in House02, but simple signed two-point structure does not solve source identity.
5. The latest route provides severely imbalanced physical exposure across source interventions.

## CURRENTLY TESTING

1. Whether 5 s mismatch is motion-revisit confounding.
2. Whether route/formation design based on persistent excitation / weakest source-mode observability can restore source identity with the **same inference rule**.

## PRIMARY CANDIDATE

**Transport-Robust Persistent-Excitation Sensing.**

## SECONDARY CANDIDATE

**Collective Multi-Trajectory Informativity** for dual UAVs, only if a single feasible trajectory cannot satisfy the excitation gate.

## REJECTED AS CURRENT MAIN INNOVATION

RMFE, SCTT, old M2, global invariant pooling, TSBIE, local-wind continuum provider, same-stream causal posterior repairs, fixed signed two-point structure, ordinary multi-robot fusion.

---

# K. What would constitute the first real GO from here?

A clean development GO requires all of the following without changing the source evaluator:

1. A source-blind route is selected using design winds only.
2. Each design wind satisfies the frozen source-observability gates.
3. The route is frozen before opening the held wind.
4. On the held wind, all four source identities are rank-1.
5. The same inference method fails or is materially weaker on the old route.
6. Generic OED / information-gain / classic GSL planning is compared so the novelty is not merely 'choose informative measurements'.

Only then should cross-environment confirmation and paper-level novelty claims begin.
