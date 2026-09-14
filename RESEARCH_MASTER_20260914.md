# UAV-GSL-ISJ — Research Master

Date: 2026-09-14

Branch: `project/research-master-20260914`
Latest evidence head: `1be4363959fcf7909e935568bb74d0a0dbd4328b`

This branch is the **research-control branch**. It does not authorize algorithm or simulator changes. It keeps one authoritative view of the scientific question, evidence, rejected routes, candidate theory, and the next falsification gate.

## Read in this order

1. `docs/LATEST_DECISION_AFTER_ACTIVE_OBSERVABILITY_NOGO_20260914.md`
2. `docs/PROJECT_SCIENTIFIC_QUESTION_AND_CORE_IDEA_20260914.md`
3. `docs/PROJECT_EVIDENCE_LEDGER_20260914.md`
4. `docs/BIG_SCIENCE_THEORY_MAP_20260914.md`
5. `docs/NEXT_STAGE_PHYSICAL_SUPPORT_AUDIT_20260914.md`
6. `docs/PROJECT_RESEARCH_STATE_20260914.json`

## Current one-sentence scientific problem

> In finite-horizon turbulent gas transport with slow sensor dynamics, **which source hypotheses can physically influence the robot-accessible sensing domain strongly enough to be identifiable at all, before any Bayesian inference or active-search policy is allowed to claim source information?**

The dominant unresolved problem is now **finite-horizon sensing support / source identifiability under the physical observation operator**.

## Current main-innovation status

```text
VALIDATED_MAIN_INNOVATION = NONE
PRIMARY_CANDIDATE = NONE_PENDING_PHYSICAL_SUPPORT_AUDIT
CAUSAL_LOCALIZATION_CLAIM = NOT_AUTHORIZED
CROSS_DATASET_CLAIM = NOT_AUTHORIZED
```

The project should not invent another posterior correction until the physical-support layer is resolved.

## Why the project arrived here

Repeated evidence now shows:

```text
more sophisticated processing of the same weak observation stream
    -> can change rankings
    -> does not stably recover full source identity
```

The latest active-observability experiment was precommitted and source-blind at route-generation time. It tested 12 map-only routes using only `W_fast + W_slow` and did not open `W_altfast` after the design gate failed.

For the best route `AO_00`:

```text
W_fast: rank=3, sigma3/sigma1=0.000609, Q_energy<=6.8e-8
W_slow: rank=2, sigma3/sigma1=4.42e-17, Q_energy<=1.78e-16
zero-exposure sources: S_k01, S_k22
```

No route passed. The best route was SHA-256 identical to the old route. Therefore **persistent-excitation route design is NO-GO in its current form within the frozen 12-route budget**.

The 5 s dual-receiver time mismatch is also no longer a candidate mechanism. Geometry-only forensic analysis supports motion-revisit confounding: median revisit time is about 4.04 s while median wind-advection times are about 104–475 s.

## Current status labels

### CONFIRMED

- `main_v8` remains the authoritative forward contract; `dataset_v1` is excluded.
- RMFE full32x2 H02 is NO-GO and exposed amplitude/ranking failure.
- SCTT downstream is NO-GO and shuffle contradicted the claimed temporal mechanism.
- Historical M1R has development-screen gains but is not a clean causal or cross-domain proof.
- Old M2 transport-member averaging is NO-GO.
- Exact counterfactual microbank tests show source effects can survive controlled transport changes when exact candidate-specific responses are available; this did not yield a deployable full-map provider.
- LMBT / CTAER / CFIR / Rank-2 / DPISC / CCDE / SCSP and related single-stream transforms do not establish stable full-support source identity.
- House02 can physically support a 2 m dual-UAV formation after native occupancy parity correction.
- Same-frame dual-receiver data integrity is PASS.
- Fixed signed two-point difference / second-order structure is NO-GO as a main algorithmic innovation.
- The 5 s mismatch is compatible with motion-revisit confounding and is not authorized as a plume-lag mechanism.
- Source-blind map-only persistent-excitation route redesign is NO-GO in the frozen 12-route budget.
- In design winds, some source/transport combinations produce effectively zero exposure over all tested admissible routes.

### CURRENTLY TESTING

Only one upstream question is active:

**finite-horizon physical support** — whether source/transport combinations fail because the raw plume never reaches accessible sensing space, slow FOPDT removes usable contrast, admissible trajectories miss existing support, or inference still fails after support is adequate.

### DEMOTED / REJECTED AS CURRENT MAIN INNOVATION

- fixed-A RMFE ranking;
- SCTT as causal temporal module;
- global transport-invariant representation;
- old M2 member averaging;
- TSBIE transport-member reweighting;
- local-wind continuum causal provider;
- simple causal posterior repair on the same single-UAV gas stream;
- signed simultaneous two-point difference / second-order structure;
- ordinary multi-robot fusion / Product-of-Experts as novelty;
- `Transport-Robust Persistent-Excitation Sensing` in its current map-only route-search form;
- `Collective Multi-Trajectory Informativity` is locked and cannot be promoted because its primary premise did not pass;
- ME-ACI V11 as established cross-domain positive evidence.

## Big-science theory map after the latest NO-GO

### Diagnostic mother theory now most relevant: finite-time transport support / domain of dependence

The current failure resembles a **transport-support problem**: some sources do not contribute non-negligible signal inside the admissible sensing domain within the finite horizon.

Forward–adjoint duality and sensor **domains of dependence** are a strong physical language for diagnosing this. However, a 2026 AIAA SciTech paper already applies multi-sensor domains of dependence to turbulent scalar source localization. Therefore this theory is useful for diagnosis but **cannot be claimed as our novelty by itself**.

### Lagrangian transport / coherent structures — secondary physics candidate, not authorized module

Lagrangian coherent structures and transport barriers describe which material regions communicate over finite time. They may later help explain or design access to plume-support regions, but they are not authorized until the physical-support audit proves that route coverage, rather than raw transport or sensor bandwidth, is the dominant bottleneck.

### Persistent excitation / OED — retained as background theory, not active innovation

The theory remains scientifically relevant, but the current implementation failed because the physical source-support modes were nearly absent. It should not be rescued by enlarging route search after seeing the failure.

## Immediate next decision

Run only:

`docs/NEXT_STAGE_PHYSICAL_SUPPORT_AUDIT_20260914.md`

The audit must separate four failure layers:

1. `RAW_TRANSPORT_SUPPORT_FAILURE`
2. `SENSOR_BANDWIDTH_FAILURE`
3. `TRAJECTORY_COVERAGE_FAILURE`
4. `SUPPORT_ADEQUATE_INFERENCE_REMAINS`

Only after this classification may a new big-science theory be promoted into a candidate module.

## Paper-level claim boundary today

The project **does not yet have a validated cross-dataset main innovation**.

The strongest defensible scientific narrative is now:

1. multiple increasingly sophisticated inference-layer repairs fail when the physical observation operator does not expose all source hypotheses;
2. fixed dual-receiver structure and map-only observability design also fail under the current finite-horizon experiment;
3. the unresolved bottleneck is therefore upstream: finite-time transport support, sensor bandwidth, or route access;
4. the next main innovation must arise from the physically verified bottleneck, not from another post-hoc score.

If the physical-support audit shows raw plume support itself is absent, algorithm development on the current 150 s House02 experiment should stop. If raw support exists but FOPDT erases it, the next research variable is sensor modality/response time. If usable support exists but routes miss it, transport-guided measurement design can reopen. Only if support is adequate and identity still collapses should inference innovation resume.
