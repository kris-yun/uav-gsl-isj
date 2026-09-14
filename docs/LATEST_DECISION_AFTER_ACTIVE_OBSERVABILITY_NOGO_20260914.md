# Latest scientific decision after Active-Observability V1 NO-GO

Date: 2026-09-14
Evidence branch: `codex/dual-uav-two-point-premise-20260913`
Evidence head: `1be4363959fcf7909e935568bb74d0a0dbd4328b`

## Formal update

The previous primary candidate, **Transport-Robust Persistent-Excitation Sensing**, is no longer the active main-innovation candidate in its current form.

The precommitted 12-route development experiment returned:

```text
TIME_MISMATCH_FORENSIC = MOTION_REVISIT_CONFOUND_SUPPORTED
OBSERVABILITY_FIRST_ROUTE_PREMISE = NO_GO
FROZEN_ROUTE_STATUS = NONE_NO_DESIGN_CANDIDATE_PASS
W_altfast = UNOPENED
```

For the best route `AO_00`:

```text
W_fast: rank 3, sigma3/sigma1 = 0.000609, Q_energy <= 6.8e-8
W_slow: rank 2, sigma3/sigma1 = 4.42e-17, Q_energy <= 1.78e-16
zero-exposure sources in both design winds: S_k01, S_k22
```

No route among the frozen 12-route map-only candidate set passed the predeclared observability gates. The old route and best new candidate are SHA-256 identical. No held-wind evaluation was opened.

## What this DOES establish

1. The 5 s time-mismatch improvement is much more compatible with robot-motion revisit than plume advection. It is not authorized as a lag-based localization mechanism.
2. Merely redesigning route geometry inside the current 150 s House02 experiment did not restore source observability.
3. The dominant problem is now upstream of inference: some source/transport combinations provide effectively no physical exposure over admissible sensing trajectories.
4. Posterior repair, causal-score repair, signed differencing, and another route-ranking formula cannot create missing physical support.

## What this does NOT establish

- It does not prove that every imaginable House02 route is uninformative.
- It does not prove that gas-source localization is impossible in House02.
- It does not prove that longer horizon, faster sensors, a different sensing modality, or a different validation environment would fail.
- It does not validate a replacement main innovation.

## Updated scientific question

The next question is no longer `Which inference or route score is better?`

It is:

> **Within a finite sensing horizon, which source hypotheses have a physically non-negligible transport path into the robot-accessible sensing domain, and which hypotheses are outside the effective sensing support before inference even begins?**

This is a finite-horizon transport-support / sensing-support problem.

## Immediate diagnostic theory: domain of dependence, NOT novelty

A 2026 AIAA SciTech paper, *Scalar Source Localization Using Multi-Sensor Domains of Dependence in Turbulent Channel Flow*, uses forward-adjoint duality and adjoint scalar fields as sensor domains of dependence for turbulent source localization.

This makes `domain of dependence / adjoint sensitivity` a strong diagnostic language for the current failure, but it also creates a direct novelty collision. Therefore:

```text
DOMAIN_OF_DEPENDENCE = diagnostic mother theory
DOMAIN_OF_DEPENDENCE = NOT authorized as our main innovation
```

Reference:
https://pdxscholar.library.pdx.edu/mengin_fac/549/

## Decision tree after the next audit

For every source x wind pair, separate four possible failure layers:

1. `RAW_TRANSPORT_SUPPORT_FAILURE`
   - raw plume never reaches enough robot-accessible free space within the frozen horizon.
   - implication: change horizon/environment/transport opportunity; do not invent inference.

2. `SENSOR_BANDWIDTH_FAILURE`
   - raw plume reaches accessible space, but frozen sensor dynamics erase or delay usable contrast.
   - implication: sensing modality / response-time redesign is required.

3. `TRAJECTORY_COVERAGE_FAILURE`
   - usable support exists and survives sensor dynamics, but admissible trajectories systematically miss it.
   - implication: measurement-design research may reopen, but only with transport-support guidance.

4. `INFERENCE_FAILURE_AFTER_SUPPORT`
   - support, sensor response, and route coverage are adequate, but source identity still collapses.
   - implication: only then is another inference-layer mechanism scientifically justified.

## Current main-innovation status

```text
VALIDATED_MAIN_INNOVATION = NONE
PRIMARY_CANDIDATE = NONE_PENDING_PHYSICAL_SUPPORT_AUDIT
PERSISTENT_EXCITATION_ROUTE = DEMOTED_NO_GO_IN_CURRENT_FORM
SIGNED_TWO_POINT_STRUCTURE = NO_GO
CAUSAL_LOCALIZATION_CLAIM = NOT_AUTHORIZED
CROSS_DATASET_CLAIM = NOT_AUTHORIZED
```

Do not promote a new module until the physical-support audit identifies which layer is actually limiting the experiment.
