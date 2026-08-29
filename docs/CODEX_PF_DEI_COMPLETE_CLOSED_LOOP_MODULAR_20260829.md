# CODEX — PF-DEI COMPLETE MODULAR CLOSED-LOOP CONTRACT

Date: 2026-08-29
Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`
Status: END-TO-END IMPLEMENTATION / QUALIFICATION CONTRACT

This is the single execution entrypoint after the currently running H01 source-information audit finishes. It supersedes any instruction that stops at offline qualification. The goal is a complete path from existing-bank falsification through native ROS2 closed-loop OFF/FULL experiments, with module boundaries frozen before outcomes so later ablations are valid.

Do not launch shared/LOHO neural training from this contract. The current branch is testing a training-free physically closed backend first. A neural amortizer is a separate future backend only if the physical-information audit says physics is informative but this frozen direct backend is insufficient.

## 0. Preserve and finish the current audit

Do not kill the already-running H01 audit. Preserve its logs/hashes and finish:

1. quick strict reserved 4->3 LOMO result;
2. full reserved-observation vs eight training-nuisance-member source-information audit;
3. the existing-bank coherence/order audit when the required cross-bank payload is present.

Do not start neural training while these run.

The audit answers three distinct questions and must report them separately:

- source separability from the physically closed predictive ensemble;
- extra information from chronological increments/order;
- extra information from retaining one nuisance member as one coherent trajectory.

Do not merge these into one PASS string.

## 1. Sync exact branch and record provenance

Pull the latest branch without rebasing away existing evidence. Record:

- git HEAD;
- dirty status;
- Python version / NumPy;
- compiler and build flags;
- ROS2 distro;
- GADEN source/binary/overlay hashes;
- current physical-bank manifest/hashes;
- current train/reserved member manifests.

Run:

```bash
python3 experiments/cg_pc_ctt/selftest_pf_dei_modular.py
```

Expected:

`PF_DEI_MODULAR_SELFTEST PASS`

Compile a minimal C++17 selftest that includes:

- `PFDEIModularRuntime.hpp`;
- `PFDEIPredictiveProvider.hpp`;
- `PFDEIEngine.hpp`.

The C++ test must reproduce the Python synthetic selected source, sensor inverse and all module switches. Do not edit formulas to make parity pass.

## 2. Hard runtime closure A — raw observation tap

The qualified sequence semantics use measured ppm at the native sensor sampling cadence, nominally 0.2 s, before the PMFS 10-sample/block mean threshold decision.

Trace the actual ROS/GADEN measurement path and identify the exact callback/topic/location at which the raw `measured_gas_ppm` sample is available before `StopAndMeasure` averaging. Record file:line, ROS topic/message field and observed cadence.

Add an isolated PF-DEI observation tap that appends

`PFDEIEngine::RawSample{measuredPpm, time, pose xyz, measured/available wind xy}`

to the PF-DEI engine. The tap must be read-only with respect to native PMFS: it must not alter the averaging, HIT/NOTHING map, state machine, planner or stopping logic.

Hard checks:

- timestamps strictly increase;
- PF-DEI raw sample count matches the sensor trace for an OFF smoke run;
- values match the authoritative `measured_gas_ppm`, never `true_gas_ppm`;
- pose/wind attached to each sample are causal values available at that timestamp.

If the deployed ROS path exposes only completed block averages and no raw measurement can be tapped, STOP with `PFDEI_RAW_SEQUENCE_NOT_CLOSED`. Do not silently use a block-average sequence after auditing/training at 0.2-s resolution. A block-resolution method would require a new pre-outcome offline qualification.

## 3. Hard runtime closure B — trajectory-independent physical predictive provider

The completed historical tensor bank is sufficient for offline tests only if it is sampled along historical trajectories. An adaptive ON run can visit different poses, therefore closed-loop inference requires a provider that can answer the physical concentration of every candidate/member at arbitrary causally visited pose/time.

Implement a production class satisfying `PFDEIPredictiveProvider.hpp`, preferably `GadenFieldPredictiveProvider`.

### 3.1 First reuse existing native assets

Audit the completed V3 bank/build outputs before regenerating anything. Determine whether the 7404 candidate/member realizations retain native GADEN field outputs / frame-query-readable state sufficient to query `(x,y,z,t)` independently of the historical robot trajectory.

If yes, index those immutable fields by:

- House/environment;
- stable carrier ID;
- training nuisance member ID;
- physical time / field frame.

Use only the eight frozen training/predictive members at runtime. The four reserved members remain qualification-only.

### 3.2 If current payload is trajectory-only

Do not fake interpolation from historical trajectory samples. Reuse the already-frozen source placement quantiles, GADEN transport seeds, geometry, source configuration and native GADEN physics to create one reusable **trajectory-independent field bank per House**, not one bank per experimental run.

This regeneration is allowed only because it produces the required immutable deployment asset and uses no localization outcomes. Do not change placement quantiles, transport seeds, Q, wind/config or simulator equations.

### 3.3 Provider parity gate

For each House, compare provider queries against the already materialized historical physical tensor at at least 1,000 deterministic `(source,member,time,pose)` points spread over source/member/time support.

Require:

- source/member IDs exact;
- physical time alignment exact;
- max ppm mismatch within the native frame-query/serialization tolerance established by the earlier forward closure;
- zero truth/performance fields in provider input;
- provider hash and field-bank hashes frozen.

Failure => `PFDEI_RUNTIME_PROVIDER_NOT_CLOSED`; STOP before ON experiments.

## 4. Hard runtime closure C — observation/provider time origin

Audit source-age / plume-phase semantics explicitly. The provider time origin must correspond to the same GADEN release-age semantics used to generate qualification observations. Do not choose a phase by looking at gas values or localization error.

If run start and simulator-field age are deterministically aligned by the benchmark launch contract, freeze that alignment. If physical source age is genuinely latent, STOP production integration and create a source-independent pre-outcome phase nuisance contract; do not search phase from outcomes.

Record the final alignment in the run manifest.

## 5. Python/C++ parity on real historical prefixes

Before modifying `sourceProbability`, export deterministic parity snapshots from existing OFF trajectories containing only:

- raw measured ppm prefix;
- deconvolved/aligned physical observation prefix;
- sample context/time/pose/wind;
- candidate/member physical prediction tensor returned by the runtime provider;
- source IDs/member IDs;
- geometry prior;
- reference `thresholdGas`;
- mode.

For at least three Houses x two runs x four chronological prefixes, compare Python `pf_dei_modular_core.py` with C++ `PFDEIEngine` for:

- candidate scores;
- Gaussian midrank evidence;
- candidate source mass;
- selected source;
- each ablation mode.

Require selected source exact and max source-mass absolute difference <= `1e-10` unless a tighter already-proven serialization tolerance applies. Failure is an implementation bug, not a reason to change the scientific formula.

## 6. Integrate modular PF-DEI into PMFS

Keep the new runtime isolated. Do not re-enter the historical PC-ACI/V4/V5 monolith.

### 6.1 Add explicit modes

Extend PMFS parameter validation/configuration with exactly:

- `pfdei_shadow`;
- `pfdei_full`;
- `pfdei_ablate_sensor`;
- `pfdei_ablate_temporal`;
- `pfdei_ablate_coherence`;
- `pfdei_ablate_nuisance`.

`off` remains untouched Classic PMFS.

### 6.2 Engine ownership

Add one PF-DEI engine/provider object owned by the PMFS/Simulations adapter. The raw sample tap appends to this engine continuously. Do not reconstruct history from HIT/NOTHING blocks.

### 6.3 Source-update ordering

At the existing source-update cadence:

1. allow the native PMFS update path to execute exactly as OFF so planner-side/native diagnostics remain available;
2. run PF-DEI inference from the full causal raw-sample prefix and frozen predictive provider;
3. in `pfdei_shadow`, log the PF-DEI source mass and return without modifying `sourceProbability`;
4. in FULL/ablation arms, map carrier mass to the exact carrier free-cell partition and replace **only** the PMFS `sourceProbability` channel used downstream;
5. normalize and verify finite nonnegative total mass = 1;
6. do not blend with same-window native PMFS posterior, use a temperature, KL blend, Active Probe or outcome-driven ACCEPT gate.

On structural failure (`INSUFFICIENT_PREFIX`, provider failure, nonfinite input, source-support mismatch), leave the native source grid unchanged for that update and log the structural reason. This is fail-safe behavior, not an evidence-quality gate.

### 6.4 Region-to-grid mapping

For candidate carrier `s` with exact 2-D free-cell set `F_s`:

`p(f)=q(s)/|F_s|` for `f in F_s`.

Use the existing persistent carrier manifest as the authoritative partition. Never treat the stored carrier centroid as an exact point source. Verify every free source cell receives exactly one carrier contribution and all prior-support cells are covered.

### 6.5 Reversible update semantics

The direct backend recomputes

`q_t(s) proportional q0(s) exp(z_t(s))`

from the geometry prior and the complete current prefix at every source update. Do not recursively multiply by the previous PF-DEI source mass. This prevents repeated counting of the same historical evidence.

Call this a `source belief/mass` in logs and manuscripts; the Gaussian-rank adapter is not yet a calibrated physical likelihood.

## 7. Freeze module boundaries for later ablation

Use the same names everywhere in code, experiment logs and manuscript:

- `B0`: physically closed region-valued source / native 3-D predictive generator. Common base; not removed in primary ablation.
- `M1`: exact persistent-sensor canonicalization `M -> C`.
- `M2`: physical nuisance-distribution marginalization over the predictive member ensemble.
- `M3`: preservation of cross-time nuisance-member trajectory coherence.
- `M4`: ordered adjacent temporal-increment evidence.
- `A0`: reversible source-mass / PMFS-grid adapter. Integration operator; not claimed as an independent innovation module and not removed in primary ablation.

No ablation is implemented by editing formulas after FULL results. The runtime switch must select one of the already-frozen code paths:

| Arm | Only changed scientific module |
|---|---|
| `pfdei_full` | B0 + M1 + M2 + M3 + M4 + A0 |
| `pfdei_ablate_sensor` | remove M1 only |
| `pfdei_ablate_nuisance` | remove M2 only: replace the member distribution by its arithmetic-mean trajectory |
| `pfdei_ablate_coherence` | remove M3 only: preserve every source/time member multiset but destroy cross-time member identity |
| `pfdei_ablate_temporal` | remove M4 only: remove adjacent `diff(log1p(C/threshold))` channel |

The B0 geometry/source-region base, provider, raw observations, prior, planner, source-update cadence, stopping rule and A0 adapter are identical across these arms.

## 8. Shadow side-effect smoke

Build one isolated PF-DEI binary. Before any ON experiment, run `off` and `pfdei_shadow` for one infrastructure seed in each House with matched native RNG.

Require:

- raw PMFS HIT/NOTHING sequence identical;
- sourceProbability used by planner identical at every update;
- robot trajectory/waypoints identical;
- stopping time/status identical;
- native GADEN random stream/hash contract identical;
- PF-DEI shadow source-mass log exists;
- no source truth/error is read by runtime.

Also record PF-DEI inference latency and provider query latency. Target total PF-DEI source-update wall time <=10% of the native source-update interval. If not, optimize caching/batching/I/O only; do not change semantics.

Any side effect in shadow => STOP and fix integration.

## 9. Activate scientific backend using only truth-blind audit results

Do this before viewing FULL localization outcomes.

- If held-out physical source separability is near null: `PFDEI_PHYSICAL_INFORMATION_NO_GO`; do not run ON and do not rescue with a new network.
- If source separability is strong but chronological/coherence controls show no added information: freeze a level-only direct backend **before** FULL outcomes and remove unsupported M3/M4 claims. Do not keep unsupported modules for storytelling.
- If source separability, ordered increments and coherent-member controls all show positive held-out value: freeze `pfdei_full` exactly as specified in `PFDEIModularRuntime.hpp`.

Write `PFDEI_FULL_FREEZE.json` with git SHA, binary SHA, provider/field hashes, source/member manifests, module modes and exact decision branch. After this file is written, no formula/threshold/member change is allowed during the development matrix.

## 10. Development closed-loop matrix

Create/freeze a one-case runner compatible with `closed_loop/pf_dei/run_pfdei_pair_matrix.sh`. It must write:

```json
{
  "house": "House01",
  "seed": 0,
  "arm": "off or on",
  "valid": true,
  "primary_error_m": 0.0,
  "first_release_s": null,
  "false_confident_collapse": false
}
```

The evaluator may use source truth only after each run to compute the external endpoint; runtime PF-DEI must never receive it.

Launch development:

```bash
PHASE=development \
SEEDS_CSV=0,1,2,3,4,5,6,7,8,9 \
CASE_RUNNER=/absolute/path/to/frozen_pfdei_case_runner.sh \
closed_loop/pf_dei/run_pfdei_pair_matrix.sh
```

This is H01/H02/H03 x 10 seeds x OFF/FULL = 30 matched pairs / 60 arms.

Frozen GO criteria:

- 30/30 valid matched pairs;
- pooled primary-error reduction >=10%;
- >=20/30 paired runs improve;
- one-sided paired sign test p<=0.05;
- no House pooled mean degrades >5%;
- zero new false-confident collapses.

If NO-GO, STOP. Do not tune using the matrix.

## 11. Module-removal ablation matrix

Only if development FULL is GO, run M1/M2/M3/M4 ablations on the same development seed set. Do **not** rerun the 30 expensive FULL arms. Reuse their frozen `case_result.json` metadata via `FULL_RESULT_ROOT`:

```bash
FULL_RESULT_ROOT=/absolute/path/to/development_full_root \
CASE_RUNNER=/absolute/path/to/frozen_pfdei_case_runner.sh \
closed_loop/pf_dei/run_pfdei_modular_ablation_matrix.sh
```

This runs only the four removal arms = 3 Houses x 10 seeds x 4 = 120 arms, and pairs them with the already-frozen FULL results.

Aggregate with `aggregate_pfdei_ablation.py`. Treat ablation output as descriptive causal/mechanistic support for the frozen method. **Never** change FULL because one ablation looks better; doing so would turn the ablation set into a development/tuning set.

For the paper, report for each removal:

- paired FULL-vs-ablation error delta;
- number of pairs where FULL is better;
- pooled error increase when the module is removed;
- per-House deltas;
- one-sided sign test as descriptive support.

A claimed module must have corresponding offline mechanism evidence and a non-harmful/positive closed-loop ablation pattern; otherwise remove or weaken that module claim in the manuscript, not in the already-frozen confirmatory code.

## 12. Confirmatory unseen-seed matrix

The confirmatory FULL implementation is the exact frozen development implementation. Ablation results cannot trigger code changes before confirmation.

Run:

```bash
PHASE=confirmatory \
SEEDS_CSV=10,11,12,13,14,15,16,17,18,19 \
CASE_RUNNER=/absolute/path/to/frozen_pfdei_case_runner.sh \
closed_loop/pf_dei/run_pfdei_pair_matrix.sh
```

Again 30 matched pairs / 60 arms, OFF/FULL only, same criteria.

Any source, binary, provider, source/member manifest, observation cadence, formula, prior, planner or threshold hash drift from `PFDEI_FULL_FREEZE.json` invalidates confirmation.

## 13. Real-world/deployment contract

The final deployment story is **new environment = prepare/query physics, not retrain source inference**.

For a new environment, allowed before localization outcomes:

- source-independent 2-D/3-D map/geometry preparation;
- source-independent wind/config preparation;
- source-independent sensor calibration;
- generation/indexing of a trajectory-independent predictive physical field bank under the same frozen nuisance policy.

Forbidden:

- source-label neural retraining/fine-tuning;
- localization-error-based thresholds/blends;
- House-specific weights;
- using real source truth to tune Q/source strength.

Current benchmark Q=10 is a controlled condition. Before real experiments, either control/calibrate physical release strength to the benchmark regime, or freeze a source-independent Q-nuisance extension before seeing localization outcomes.

## 14. Required final return package

Do not report only a one-line PASS. Return one immutable package containing:

1. current H01 audit results and hashes;
2. raw-observation tap source location/cadence proof;
3. provider design, field-bank provenance and 1,000-point parity report;
4. Python/C++ real-prefix parity report;
5. shadow side-effect parity report;
6. `PFDEI_FULL_FREEZE.json`;
7. exact source/binary/provider/member hashes;
8. development `PAIR_VERDICT.json` and all 30 matched pairs;
9. if development GO, ablation `ABLATION_SUMMARY.json`;
10. confirmatory `PAIR_VERDICT.json` if authorized by development GO;
11. runtime latency/memory metrics;
12. a compact status table marking each item CONFIRMED / FAILED / NOT RUN.

Do not continue to another method after a failure without stopping and reporting the exact failed boundary.
