# CODEX TASK — PF-DEI exact deconvolution and matched ideal/native replay

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Preconditions:

- `PF_DEI_FORWARD_OPERATOR_CLOSED`;
- independently reproduced sensor-memory audit: 484 transitions, 102 lower-bound qualifying, H01/H02/H03 = 0/37/65.

Read first:

- `docs/CG_PC_CTT_PF_DEI_SENSOR_GENERATIVE_CHAIN_FREEZE_20260828.md`
- `docs/PF_DEI_SENSOR_MEMORY_ROOT_CAUSE_DERIVATION_20260828.md`
- `docs/PF_DEI_EXACT_SENSOR_DECONVOLUTION_DERIVATION_20260828.md`

Reference code:

- `experiments/cg_pc_ctt/pf_dei_inverse_sensor_reference.py`
- `experiments/cg_pc_ctt/selftest_pf_dei_inverse_sensor_reference.py`

This task supersedes the earlier instruction to evaluate the same native historical sequence directly under both ideal and native forward models.  A matched A1 observed arm must first be obtained by the exact truth-blind inverse of the source-proven deterministic sensor.

No C++, Active Probe, source truth, localization error or 60-arm performance experiment is allowed.

## Stage 0 — provenance freeze

Merge or preserve the forward-closure work and audit work before analysis.

Record exact:

- forward-closure commit/report/evidence hash;
- sensor-memory-audit commit/report/evidence hash;
- native GADEN shared-library/source hashes;
- native sensor source/config hashes;
- deployed overlay source/config hash for every new simulation launched in this task.

Historical `/dev/shm` overlay loss remains a reproducibility limitation; do not pretend it is recovered.

## Stage 1 — selftest and closure-evidence inverse parity

Run:

```bash
python3 experiments/cg_pc_ctt/selftest_pf_dei_inverse_sensor_reference.py
```

Then apply `invert_frozen_sensor(...)` to the 50-sample synthetic parity trace from the forward-closure evidence.

Mandatory:

- delay steps = 2;
- recovered physical sample count = 48 of the 50 interval samples (final two have no future delayed observation inside the interval);
- max absolute error against the synthetic native-GADEN physical concentration <= 1e-10 ppm;
- no parameter is fitted from this parity result.

If this fails, stop:

`STOP_PF_DEI_SENSOR_INVERSE_NOT_PARITY`

## Stage 2 — reconstruct historical physical input from measured data only

For each of the 30 archived OFF runs, load the complete run-level `sensor_trace.csv`.

Allowed input columns:

- timestamp;
- `measured_gas_ppm`;
- pose/runtime boundary fields needed to map exact PMFS blocks.

Forbidden:

- `true_gas_ppm`;
- true source;
- final localization error;
- ON/OFF improvement or any performance label.

Explicitly drop forbidden columns before constructing the analysis object even if they coexist in the CSV.

Verify before inversion:

- dynamic sensor configuration matches the frozen source/config hash;
- zero noise/drift, gain 1, baseline 0;
- symmetric tau 1.2 s;
- dead time 0.4 s;
- regular cadence 0.2 s within provenance tolerance;
- no active saturation.

If a run violates an invertibility precondition, do not approximate. Mark it invalid for this diagnostic and report the exact reason.

Apply the inverse to the complete measured stream.  Preserve:

- reconstructed physical sample value;
- physical sample timestamp;
- source measured indices used for inversion;
- serialization-error bound;
- recoverability mask.

Required artifact:

`artifacts/pf_dei_deconvolution/recovered_physical_trace_<house>_seed<seed>.csv`

No truth/performance columns.

## Stage 3 — round-trip validation

Feed each reconstructed physical trace through the exact frozen sensor recurrence using the same initial state and timing.

Because historical `sensor_trace.csv` is serialized to six decimal places, use a tolerance derived from serialization, never tuned from House/seed outcomes.

The source-proven six-decimal inverse physical error bound is

`eps_C = 0.5e-6 * (1+alpha)/(1-alpha)`

with `alpha=exp(-0.2/1.2)`, approximately `6.014e-6 ppm`.

Report round-trip measured reconstruction error and require it to be consistent with the serialization contract.

Do not continue if large residuals indicate a mismatch in cadence, sensor state, reset semantics or file provenance.

## Stage 4 — exact historical ideal-vs-native block counterfactual

Use the already validated exact 10-sample block-consumption manifest.

For every completed PMFS block whose physical samples are fully recoverable:

- `native_mean` = archived/recomputed mean of the actual measured ppm samples;
- `native_hit` = `native_mean > thresholdGas`;
- `ideal_mean` = mean of reconstructed physical ppm at the **same sample timestamps**;
- `ideal_hit` = `ideal_mean > thresholdGas`.

If `abs(ideal_mean-thresholdGas)` is within the source-proven serialization uncertainty bound, classify the ideal decision as `AMBIGUOUS_SERIALIZATION_MARGIN`.

Otherwise classify exactly one of:

- `NATIVE_HIT_IDEAL_NOTHING`;
- `NATIVE_NOTHING_IDEAL_HIT`;
- `SAME_HIT`;
- `SAME_NOTHING`.

If future delayed measurements needed to recover a sample lie beyond the run trace, classify `UNRECOVERABLE_END_OF_RUN`; never extrapolate.

Required outputs:

- `artifacts/pf_dei_deconvolution/block_counterfactual.csv`;
- `artifacts/pf_dei_deconvolution/block_counterfactual_summary.json`;
- counts by House and seed;
- counts restricted to the first block after an inter-stop transition;
- relation to stop gap and previous measured state.

This stage is truth-blind.  Do not call `NATIVE_HIT_IDEAL_NOTHING` a false positive; it means only that the native sensor dynamics changed the decision relative to an ideal instantaneous sensor on the same reconstructed physical input.

## Stage 5 — matched candidate-source A1/A2 forward dataset

Only after Stages 1–4 pass, generate candidate-source forward traces on the exact historical poses/timestamps using the closed native GADEN physical concentration path.

For every source candidate and frozen transport draw, generate one coherent physical trace across the complete run timeline.

Create matched arms from the **same physical trace**:

### A1 ideal observation arm

Observed:

`D_ideal = reconstructed physical concentration from historical measured ppm`.

Candidate prediction:

`C_candidate,transport(t)` directly from native GADEN physical forward.

### A2 native observation arm

Observed:

`D_native = historical measured_gas_ppm(t)`.

Candidate prediction:

exact run-persistent native sensor applied to the same `C_candidate,transport(t)`.

The A1/A2 candidate grids, transport draws, poses, timestamps, wind/runtime context and inference engine must be identical.

Do not reset sensor state at stop/context boundaries.

## Stage 6 — inference qualification on synthetic matched draws before historical source evidence

Before using the 30 historical runs for source ranking, qualify the selected inference engine on synthetic draws where the source is chosen by the experimenter.

Important theoretical expectation:

under the frozen zero-noise unsaturated sensor, A2 is almost an invertible transform of A1 except for dead-time boundary samples.  Therefore a correct full-sequence inference engine should not show a large intrinsic source-information loss in A2.

If A1 synthetic source recovery is good but A2 is poor, first diagnose representation/inference failure to model the known sensor operator; do **not** immediately conclude the physical sensor destroyed information.

Preferred diagnostic implementation order:

1. exact deconvolved A1 sequence;
2. native A2 sequence with explicit persistent-state-aware simulation;
3. same modest run-prefix inference architecture/protocol for both arms.

If a neural ratio estimator is used, freeze architecture/hyperparameters before historical evaluation and use same-context negative sources so House/trajectory identity cannot become a shortcut.

## Stage 7 — truth-blind historical source-evidence comparison

Evaluate A1 and A2 on the 30 historical OFF trajectories without true source/error.

Report:

- cross-prefix source-ranking stability;
- held-out-prefix predictive adequacy;
- source-independent absolute adequacy/model-criticism statistic;
- A1/A2 disagreement in source ranking/evidence;
- results by House and seed, but no House-specific thresholds.

Interpretation:

### `SENSOR_STATE_MISATTRIBUTION_DOMINANT`

Use only if:

- the historical block counterfactual shows substantial native/ideal decision changes;
- A1 source evidence becomes cross-prefix/absolute adequate;
- A2 becomes similarly adequate when the full persistent sensor operator is modelled, while the old local/frequency representation remains inadequate.

This means the principal failure was spatial/context misattribution of a history-dependent observation, not intrinsic loss of source information by the sensor.

### `TRANSPORT_FAMILY_OR_SOURCE_FORWARD_INSUFFICIENT`

If A1 and correctly modelled A2 both remain inadequate, the sensor-locality error is real but does not explain the source-evidence failure. Proceed to source-independent physics-randomized GADEN transport expansion.

### `SBI_INFERENCE_NOT_QUALIFIED`

If synthetic A1/A2 are identifiable but the inference engine cannot recover/calibrate them.

### `MIXED_SENSOR_TRANSPORT`

If correcting sensor state produces material but incomplete adequacy recovery and broader transport is still required.

No localization performance is opened in this task.

## Stage 8 — performance remains separate

Only after a native-sensor-aware source model is truth-blind adequate may a separately frozen development task open source truth/localization error and test:

- pooled expected-location error improvement >=10%;
- >=20/30 paired improvements;
- no House pooled degradation >5%;
- zero new false-confident collapses;
- all runtime/parity contracts.

No C++ or 60-arm run before that separate authorization.
