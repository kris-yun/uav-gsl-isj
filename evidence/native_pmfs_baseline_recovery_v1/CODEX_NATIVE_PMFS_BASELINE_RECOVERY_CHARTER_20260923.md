# CODEX CHARTER — Native PMFS Baseline Recovery on VGR

**Date:** 2026-09-23  
**Branch:** `research/native-pmfs-baseline-recovery-v1`  
**Priority:** P0 — block all new innovation screening until this audit is complete.

## 0. Why this task exists

The authoritative R2/VGR runs currently called "Native PMFS" were not executed with the same forward-model contract as the MAPIRlab PMFS example configuration.

The most important discovered deviation is:

- MAPIRlab official `humble` PMFS example: `useWindGroundTruth = True`
- our frozen R2 runner: `useWindGroundTruth:=false`

Therefore the R2 candidate-source forward maps were generated through a VGR/GMRF estimated-wind path, while the official PMFS simulation example drives the candidate filament simulator from the GADEN ground-truth wind service.

The R2 runner also changed several PMFS transport / hit-map parameters. Consequently the six R2 runs must be called **VGR-adapted PMFS baseline** until this recovery task establishes parity.

This is a baseline-recovery task, not a new-method task. Do not turn any bug or parameter mismatch found here into a claimed innovation.

---

## 1. Canonical source of truth

### 1.1 User's local archive

The user's downloaded official package is located at:

`D:\ZYC\A-gas\ASCi\GasSourceLocalization-humble.zip`

If Codex is running on the user's Windows machine and this path is accessible, use this archive as the first reference.

Do **not** modify the archive in place. Extract it to a temporary/reference directory.

Record:

- SHA256 of the ZIP;
- extracted top-level directory;
- SHA256 of every PMFS file used for parity;
- Git/branch information if embedded.

### 1.2 Upstream reference

If the Windows archive is unavailable from the execution environment, use the public upstream only as a read-only reference:

- repository: `MAPIRlab/GasSourceLocalization`
- branch: `humble`

A key parity anchor already verified:

`Environment_config/PMFS/launch/main_simbot_launch.py`

Git blob SHA:

`ad0159dc9a7d9395f050a7d50b6a1f7a0c8bf9db`

The local uploaded archive and upstream `humble` copy of this file matched this blob SHA during the audit.

Do not silently substitute another branch, tag, fork, or current default branch.

### 1.3 External dependency warning

`GMRF-wind` is a separately installed dependency in the MAPIRlab README; it is not version-pinned inside the GasSourceLocalization ZIP.

Therefore:

- record the exact GMRF binary/source provenance used by every recovery run;
- do not assume a locally installed GMRF version is the version implicitly used by the original PMFS experiments;
- for the official-ground-truth-wind PMFS parity path, GMRF must **not** be allowed to affect the PMFS candidate-source forward simulator.

---

## 2. Preserve all existing evidence

Do not delete, rewrite, or relabel old raw data in place.

The current R2 results remain valid as evidence for the configuration that generated them, but their baseline name must be treated as:

`VGR-adapted PMFS (GMRF-wind forward)`

not as proven author-native PMFS.

Keep all old hashes and manifests immutable.

Create all recovery outputs under a new namespace, for example:

`evidence/native_pmfs_baseline_recovery_v1/`

and new run roots. Never overwrite the authoritative R2 archive.

---

## 3. First deliverable: exact parameter/provenance diff

Generate:

`evidence/native_pmfs_baseline_recovery_v1/OFFICIAL_VS_R2_PARAMETER_DIFF_20260923.tsv`

and a human-readable MD report.

At minimum compare:

| parameter | MAPIRlab official humble example | frozen R2 |
|---|---:|---:|
| useWindGroundTruth | true | false |
| stepsSourceUpdate | 3 | 10 |
| maxRegionSize | 5 | 5 |
| sourceDiscriminationPower | 0.3 | 1.0 |
| refineFraction | 0.1 | 0.25 |
| deltaTime | 0.1 | 0.2 |
| noiseSTDev | 0.5 | 0.5 |
| iterationsToRecord | 200 | 200 |
| maxWarmupIterations | 500 | 3 |
| minWarmupIterations | official PMFSLib default 200 unless explicitly overridden | 1 |
| blurSigmaX/Y | 1.5 / 1.5 | 0 / 0 |
| hitPriorProbability | 0.3 | 0.1 |
| maxUpdatesPerStop | 5 | 8 |
| kernelSigma | 1.5 | 0.5 |
| kernelStretchConstant | 1.5 | 1.5 |
| confidenceMeasurementWeight | 1.0 | 0.5 |
| confidenceSigmaSpatial | 1.0 | 0.5 |

Also include every other PMFS-relevant parameter found in the two launch/runtime manifests. Do not cherry-pick only the known differences.

Classify each parameter into exactly one category:

1. **official PMFS algorithm/forward parameter**;
2. **VGR environment adapter**;
3. **measurement/sensor protocol**;
4. **budget/evaluation protocol**;
5. **research instrumentation only**.

The recovery runner must restore category (1) from the official package. Categories (2–5) may remain VGR-specific only when required, and every retained deviation must be justified in the report.

---

## 4. Wind-path recovery — highest priority

### 4.1 Required official semantic path

For the Native-PMFS recovery arm, PMFS must be compiled with GADEN support and must execute:

`useWindGroundTruth = true`

so that `PMFSLib::EstimateWind()` takes the ground-truth/GADEN service branch and the candidate filament simulator receives those wind vectors.

The current PMFS source uses the GADEN wind service client:

`/wind_value`

Validate service type and response before launching PMFS.

### 4.2 Do not trust labels; assert runtime behavior

Add runtime evidence proving which branch was taken.

Every run must emit into the manifest/report:

- `useWindGroundTruth` requested value;
- whether PMFS was compiled with `USE_GADEN`;
- service name and type;
- number of successful wind queries;
- number of fallback/failure queries;
- min/median/max magnitude of the wind field actually passed into `simulateSourceInPosition`;
- SHA256 of the algorithm binary and launch file.

If practical, add an explicit log line such as:

`NATIVE_RECOVERY_WIND_PATH=GADEN_GROUND_TRUTH`

Do not rely only on a launch argument string.

### 4.3 Wind parity audit

At every source update, export the wind field PMFS actually uses.

Create:

`WIND_GROUND_TRUTH_PARITY_<HOUSE>_seed<SEED>.csv`

For a frozen set of cells including the robot/source-update cells, record:

- x, y;
- service-returned u, v;
- PMFS internal u, v;
- magnitude and angular difference.

Primary gate:

- internal PMFS field and service-returned field must agree to numerical tolerance;
- no hidden GMRF rescaling may appear in this arm.

Do not use source truth in this gate.

---

## 5. Do not "fix" wind direction by guessing

The official GADEN `simulated_anemometer` converts the flow/downwind vector to an **upwind** anemometer direction before publishing. Current GMRF-W source expects an upwind anemometer direction and converts it back to downwind internally.

Therefore a 180-degree patch must **not** be added merely because an R2 diagnostic showed reversed vectors.

First establish the exact VGR bridge publication semantics from its source and runtime topic.

For the Native recovery arm this issue should be bypassed by the direct ground-truth wind service path.

Document the VGR/GMRF direction issue separately as an adapter audit. Do not mix it into Native-PMFS recovery until proven.

---

## 6. Implement a clean recovery runner

Do not edit `reference/run_meaci_case_20260824.sh` in place.

Create a new runner, suggested path:

`reference/run_native_pmfs_recovery_20260923.sh`

Requirements:

- retain House01/02/03 VGR data selection;
- retain the 300 s evaluation budget unless a short smoke test is explicitly marked as such;
- retain source and start positions;
- retain deterministic seed bookkeeping;
- use a fresh run root;
- restore official category-(1) PMFS parameters;
- set `useWindGroundTruth:=true`;
- expose no experimental PFDI/TNQC/TADM module in the primary Native arm;
- retain instrumentation only if it provably does not alter the algorithm state;
- record all launch args into a machine-readable manifest.

The runner must fail closed if the ground-truth wind service is unavailable. Do **not** silently fall back to GMRF.

---

## 7. Recovery must be staged — no six-run rerun first

### Stage R0 — static/source-level smoke test

House01 seed0 only.

Goal: prove that the official wind branch and official PMFS parameters are actually active.

No source-rank conclusion yet.

Pass only if wind parity and runtime provenance are clean.

### Stage R1 — frozen candidate-forward replay

Using the same observation snapshot and same source-candidate geometry, compare three predeclared arms:

A. **R2 adapted forward** — current frozen behavior;  
B. **wind-only recovery** — ground-truth wind, otherwise keep R2 PMFS forward parameters;  
C. **full Native forward recovery** — ground-truth wind + official PMFS forward/hit-map parameters.

This three-arm decomposition is diagnostic only. Do not choose an arm after seeing truth.

For each arm report:

- candidate count;
- truth-containing candidate rank;
- truth candidate score;
- top-5 candidate IDs/centers;
- endpoint/top-5 centroid only as secondary diagnostics;
- wind magnitude distribution;
- candidate-map hash / deterministic replay hash.

Truth is used only after all three scores are frozen.

### Stage R2 — one full 300 s closed-loop case

House01 seed0.

Use the clean Native recovery runner.

Required outputs:

- full manifest;
- raw sensor/wind traces;
- source-update context bank;
- final truth-source candidate rank;
- final endpoint error;
- exact binary/config hashes.

### Stage R3 — six-run recovery

Only after R0–R2 pass infrastructure/parity gates.

Run House01/02/03 × seed0/1 with the exact same frozen recovery contract.

No House-specific tuning.

---

## 8. Scientific gates

### 8.1 Baseline validity gate

A recovery run is valid only if:

- official-ground-truth wind path is proven at runtime;
- official PMFS algorithm/forward parameters are restored or every unavoidable deviation is explicitly justified;
- no GMRF-derived wind enters the Native candidate simulator;
- no truth coordinate is used to select parameters, cells, hyperparameters, or stopping conditions;
- seed and binary/config hashes are recorded.

### 8.2 Do not require performance improvement to call parity successful

The purpose is to recover a valid baseline, not to force PMFS to perform well.

If full Native recovery still gives poor truth-source rank, that is a scientifically important result.

If rank improves dramatically, then many old forward-map-dependent innovation screens must be rerun.

### 8.3 Source identity remains the primary scientific metric

For all comparisons:

**truth-source candidate rank is the hard gate.**

Endpoint/centroid improvements cannot substitute for source identity.

---

## 9. Old-result triage after recovery

When R3 completes, create:

`OLD_EVIDENCE_REVALIDATION_MATRIX_20260923.md`

Classify every previous line into:

- **A — independent of candidate forward wind semantics; remains valid**
- **B — partly dependent; needs spot-check**
- **C — directly depends on old candidate forward family; must rerun**
- **D — infrastructure-only / novelty-only; unaffected**

At minimum re-evaluate:

- spatial proper-score tests;
- static operator correction;
- first-passage/TPT candidate replay;
- distributional-forward tests;
- native discriminability / active-identifiability tests;
- any method whose pass/fail was decided by candidate truth rank using old `estimated_wind`.

Do not rerun everything blindly before this matrix exists.

---

## 10. Explicit non-goals

Codex must NOT:

- invent a new PMFS variant during baseline recovery;
- tune `noiseSTDev`, blur, sourceDiscriminationPower, GMRF lambdas, or likelihood using truth;
- claim the GMRF issue is an original-PMFS bug without evidence;
- delete the R2 archive;
- overwrite the official ZIP;
- silently use the latest upstream dependency instead of documenting/pinning it;
- combine Native recovery with PFDI/TNQC/ME-ACI;
- optimize endpoint while truth-source rank worsens.

---

## 11. Required GitHub checkpoints

Commit after each stage:

1. **audit** — archive/upstream fingerprints + full parameter diff;
2. **runner** — clean Native recovery runner and runtime assertions;
3. **R0/R1 evidence** — wind parity + candidate-forward three-arm result;
4. **R2 evidence** — one 300 s closed-loop result;
5. **R3 evidence** — six-run frozen result;
6. **triage** — old-evidence revalidation matrix.

Do not wait until the end to commit.

Suggested commit prefixes:

- `audit: ...`
- `baseline: ...`
- `evidence: ...`

---

## 12. Final decision report

Create:

`evidence/native_pmfs_baseline_recovery_v1/NATIVE_PMFS_BASELINE_RECOVERY_DECISION_20260923.md`

It must answer exactly:

1. Was the user's local `GasSourceLocalization-humble.zip` consistent with the official `humble` PMFS source?
2. Which R2 deviations came from our VGR adapter/runner rather than the original PMFS example?
3. Did the recovered ground-truth-wind path pass numerical parity?
4. How did truth-source rank change in A/B/C replay?
5. How did six recovered Native runs perform?
6. Which previous innovation conclusions remain valid and which must be rerun?
7. Is the fixed-forward-family/source-identifiability failure still present after a valid Native recovery?

Stop there. Do not start a new innovation module in this branch.
