# Codex execution contract — CSTAR causal three-module implementation

Date: 2026-09-06
Branch: `g3-cstar-causal-redesign-20260906`
Base: `2387668ec6345d273a8d630af069d65af710850f`
Read first: `docs/CTPI_CSTAR_CAUSAL_THREE_MODULE_THEORY_20260906.md`.

This contract authorizes **offline/reference implementation and falsification only**. It does not authorize new House/GADEN campaigns or production replacement of the current runtime scientific path.

## 1. Non-negotiable scientific identity

Implement exactly three load-bearing modules:

- M1 `PICR`: perturbation-invariant causal source representation;
- M2 `CPO`: bank-free source/route-conditioned first-passage + committor observation operator;
- M3 `PHS`: prospective route sweeps scored by posterior-weighted pairwise Bhattacharyya source confusion.

Do not rename standard Bayes marginalization as causality. Do not reintroduce peak-SSE M1, a site-specific predictive bank, source-carrier centroids, expected-observation fake lookahead, `20x` posterior modulation, House-specific thresholds or planner weights.

## 2. First command / reference math

Before model work:

```bash
cd experiments/ctpi_cstar
python selftest_cstar_reference.py
```

Expected exact terminal line:

`CSTAR_REFERENCE_SELFTEST PASS`

The functions in `cstar_reference.py` are the mathematical oracle for:

- hazard -> first-passage distribution;
- first-passage -> committor;
- categorical Bhattacharyya coefficient;
- PHS route-resolution score and deterministic distance/index tie-break.

Future C++ must have parity tests against this reference.

## 3. Current-code alignment audit to perform before editing

Write `evidence/ctpi_cstar/code_alignment.json` containing exact source line/function identities and hashes for:

1. `CPIR.cpp::recordCPIRRawSample` and `applyCPIRPosterior`;
2. `CTPIOnlineCoreV2.hpp::{Transport,Fopdt,ObservationStream}`;
3. `CTPI.cpp::evaluateCTPIActionInformation`;
4. `MovingStatePMFS.cpp::chooseGoalAndMove` and `calculateMutualInformationGas`;
5. wind ingress / geometry adapters;
6. source-candidate representation used by Classic PMFS `resultsFirstLevel` and how a cell/region posterior can be mapped to those source weights without source truth.

Record, do not silently reinterpret:

- `distanceFromRobot` is a propagated navigation-distance field; it is not a stored path trajectory.
- Current CTPI M3 does not expose a complete future Nav2 path.
- If the runtime cannot obtain a real planned path without architectural work, the first PHS implementation must use a legally defined fixed endpoint+dwell horizon. Do **not** invent straight-line routes through obstacles.

## 4. Phase M1 — PICR offline implementation

Create:

```text
experiments/ctpi_cstar/m1_picr/
  build_intervention_pairs.py
  dataset_contract.json
  model.py
  train.py
  evaluate_causal_gate.py
  destructive_controls.py
  README.md
```

### 4.1 Data contract

Use only existing spent/frozen assets first. Each training/evaluation example must carry separate metadata fields:

- source location/region label (offline training/evaluator only);
- House/geometry identity (for split/audit only; never an encoder input);
- transport realization/wind context;
- source-strength/release context if available or physically generated under an explicitly valid forward rule;
- sensor context;
- ordered stamped `(pose,gas,wind)` frames.

No callback-order reconstruction. No future frame. No held-out-House runtime bank feature.

### 4.2 Pair builders

Produce explicit pair tables before training:

- `same_source_transport_intervention`;
- `same_source_amplitude_intervention`;
- `same_source_sensor_intervention` where available;
- `different_source_matched_context`;
- leave-one-House-out split.

If a requested intervention cannot be generated from existing evidence without an unverified assumption, mark that intervention `UNAVAILABLE` rather than synthesizing it silently.

### 4.3 Model contract

The initial research model must have separable named outputs:

```python
PICR.forward(history, geometry, candidates) -> {
    "source_logits": [N_candidate],
    "source_representation": [...],
    "nuisance_representation": [...],
    "amplitude_state": [...],
}
```

Required structure:

- response branch: gas + audited sensor temporal state;
- context/internal-auxiliary branch: wind + executed pose + geometry/time;
- causal temporal mask: no future attention;
- candidate-conditioned scorer supporting arbitrary free cells/regions, not a fixed House class head;
- no House/member/true-source coordinate as input.

A local/sparse attention rule may be introduced only with an explicit source-independent physical support definition and a destructive ablation. Do not tune its radius/window on closed-loop localization outcomes.

### 4.4 Training constraints

Primary task: proper source score/candidate contrast.

Causal constraints:

- same-source nuisance interventions -> stable `zS`;
- different-source matched-context pairs -> separable `zS`;
- `zS` nuisance leakage conditioned on source below frozen tolerance;
- `zN`/amplitude head carries enough nuisance information to prevent trivial all-zero collapse.

Prefer constrained/Lagrangian optimization with audit-visible dual variables over arbitrary hand sweeps of loss coefficients. Any development hyperparameters must be selected without using confirmatory House outcomes.

### 4.5 Mandatory M1 baselines

Evaluate on identical fixed trajectories:

1. current peak-SSE M1;
2. ordinary temporal encoder with identical parameter budget but no intervention constraints;
3. PICR;
4. PICR with intervention-pair relation shuffled;
5. PICR with source labels permuted (sanity/destructive control).

### 4.6 M1 gate

Do not proceed to runtime if any of these fail:

- source proper score / spatial source error not directionally better than current M1 on the predeclared development split;
- causal PICR does not beat the matched ordinary temporal encoder on nuisance invariance while retaining source separation;
- shuffled intervention relations leave the full gain unchanged;
- leave-one-House-out collapses;
- source-strength intervention recreates fixed-amplitude source-identity drift.

Write `evidence/ctpi_cstar/m1_picr_gate.json` with exact metrics and `PASS` or `NO_GO`.

## 5. Phase M2 — CPO offline implementation

Create:

```text
experiments/ctpi_cstar/m2_cpo/
  build_route_law_dataset.py
  physics_prior.py
  model.py
  train.py
  evaluate_committor_gate.py
  zero_shot_house_split.py
  README.md
```

### 5.1 Keep V2 physics as the prior

Do not rewrite `CTPIOnlineCoreV2::Transport/Fopdt` science during this phase. Build a Python/reference parity wrapper first. The physics provider must use the already-corrected navigation-height geometry and causally available wind rule.

A learned correction may target the discrepancy in encounter hazard / marked observation law, not secretly change source posterior.

### 5.2 Exact M2 output schema

For every source hypothesis `s` and legally defined route `tau`:

```python
CPORouteLaw = {
    "first_hit_prob": [H+1],  # T=1..H plus T>H
    "committor": [H],
    "logppm_mean": [H],
    "logppm_scale": [H],
    "valid": bool,
}
```

`sum(first_hit_prob)==1`; `committor` is monotone; final `committor[-1] == 1-first_hit_prob[-1]` within tolerance.

### 5.3 Training target

Use held-out high-fidelity transport outcomes / spent simulation assets as supervision. Existing predictive banks are allowed only as offline data sources/teachers. At deployment and leave-one-House-out evaluation, held-out-House bank content is forbidden.

Train a geometry/context-conditioned correction around the physics prior. Do not train a fixed source-ID classifier.

### 5.4 M2 baselines/gate

Compare:

1. legacy/current plume route-law provider;
2. uncorrected causal V2 physics prior;
3. CPO full provider;
4. source-shuffled and route-shuffled controls.

Primary predictive metrics: first-passage NLL/Brier + horizon-wise committor calibration. Secondary: marked log-ppm NLL/CRPS, tail encounter/non-encounter stratification.

CPO must improve the predeclared primary predictive metric over both the plume and uncorrected physics baseline on held-out transport data and retain directionally valid leave-one-House-out performance. Otherwise write `M2_CPO_NO_GO` and do not use it to rescue M3.

## 6. Phase M3 — PHS offline implementation

Create:

```text
experiments/ctpi_cstar/m3_phs/
  route_provider.py
  baseline_route_law.py
  phs.py
  selftest_cpp_parity_inputs.py
  evaluate_phs_gate.py
  destructive_controls.py
  README.md
```

### 6.1 Route identity

Preferred route: actual planner path sampled at 0.2 s plus dwell to a common fixed horizon.

Hard rule: current `distanceFromRobot` is insufficient to reconstruct the route. First audit whether the codebase/Nav2 wrapper can expose a planned path. If not, implement the first scientific PHS gate on offline legally known paths. For production, either expose the real planner path or freeze endpoint+dwell prediction; never use an invented line through obstacles.

### 6.2 Source-region marginalization

For a region-valued source candidate, use all free cells or a frozen deterministic quadrature/placement set with normalized weights. Every route-law provider and every compared M3 policy must share this marginalization. No centroid collapse.

### 6.3 PHS score

Use `cstar_reference.prospective_resolution_scores` exactly. No extra term.

- maximize normalized pairwise source resolution;
- common future horizon is the cost budget;
- travel distance then deterministic coordinates/index only break ties;
- no `lambda`, posterior multiplier, exploration probability or learned action score.

### 6.4 M3 gate with baseline provider

To isolate M3, first use a frozen baseline route-law provider, not CPO. Compare on paired held-out outcome realizations:

- native PMFS action;
- explicit MAP/source-seeking exploit baseline;
- old current CTPI one-step EIG implementation;
- PHS.

Primary metric: predeclared temporal source-risk/localization-error AUC over the offline rollout. Report paired wins/losses and House stratification. Route-law/source pairing shuffle must remove the claimed advantage.

Do not proceed if PHS has no incremental value over F00-equivalent behavior under the baseline provider.

## 7. Full module-combination gate

Only after M1, M2 and M3 offline gates pass independently, build a shadow/offline composition with the exact arms:

- `A0` Classic PMFS;
- `F00` PICR + native PMFS information planner;
- `F10` PICR + PHS + baseline route-law provider;
- `F11` PICR + PHS + full CPO.

### 7.1 Clean M1->native-planner adapter

Do not use the current M1 MAP chase or posterior-guidance coefficient. Inspect how `calculateMutualInformationGas()` consumes `simulations.resultsFirstLevel[*].sourceProb`. Implement a deterministic mapping from PICR candidate posterior mass to the corresponding Classic PMFS source-hypothesis weights, preserving the native PMFS information calculation. Add a parity test: when PICR weights equal the native weights, the native action scores/goals must be unchanged within numerical tolerance.

This adapter is infrastructure, not M3.

### 7.2 Interpret increments exactly

- `F00-A0`: M1 downstream effect;
- `F10-F00`: M3 downstream effect;
- `F11-F10`: M2 downstream effect;
- `F11-A0`: complete CSTAR effect.

Each increment must be directionally beneficial before calling that module load-bearing. No post-hoc arm redefinition.

## 8. Production integration, only after offline GO

Do not edit the legacy scientific functions in place. Add versioned components first:

```text
ros2_package/src/gsl_server/algorithms/PMFS/CSTAR/
  CausalSourcePICR.hpp/.cpp
  CommittorCPO.hpp/.cpp
  ProspectiveSweepPHS.hpp/.cpp
  CSTARContracts.hpp
```

Add a new explicit mode, e.g. `pfdiMode=cstar_v1`, leaving legacy modes byte/numerically unchanged.

Required audit logs:

- each M1 posterior release and intervention-support diagnostics;
- each M2 `(source,route)` law hash + causal input cutoff time;
- each M3 pairwise confusion matrix, resolution score, feasible route identity and selected route;
- exact model/artifact hashes and runtime versions.

If neural M1/M2 runtime binding is needed, select the runtime mechanism only after offline GO based on what is reproducibly available on the VM. Do not alter the science merely to fit a preferred inference library.

## 9. Destructive controls that must survive into paper experiments

M1:
- source label permutation;
- nuisance intervention-pair shuffle;
- source-strength intervention;
- sensor-state reset/perturbation;
- transport/wind intervention;
- House-ID prohibition.

M2:
- source/route shuffle;
- physics-prior removal;
- learned-correction removal;
- held-out geometry/flow perturbation;
- tail event stratification.

M3:
- source-conditioned law shuffle;
- replace prospective route law by single-endpoint law;
- replace pairwise symmetric resolution by old one-step EIG;
- region-centroid ablation versus correct placement marginalization.

Full:
- A0/F00/F10/F11 frozen factorial;
- bank-assisted diagnostic versus true bank-free runtime when later authorized.

## 10. Repository/reporting deliverables for this cycle

Before requesting any new House experiment, commit:

1. all reference/offline code;
2. selftests and parity tests;
3. `evidence/ctpi_cstar/code_alignment.json`;
4. `evidence/ctpi_cstar/m1_picr_gate.json`;
5. `evidence/ctpi_cstar/m2_cpo_gate.json`;
6. `evidence/ctpi_cstar/m3_phs_gate.json`;
7. `docs/CTPI_CSTAR_OFFLINE_FALSIFICATION_RESULT_20260906.md`;
8. `docs/CTPI_CSTAR_RUNTIME_INTEGRATION_PLAN.md` only if all three gates survive;
9. a machine-readable manifest with SHA-256 provenance.

Negative results remain negative. If one module fails, diagnose that module; do not lower the gate or modify another module so that it carries the failed one.
