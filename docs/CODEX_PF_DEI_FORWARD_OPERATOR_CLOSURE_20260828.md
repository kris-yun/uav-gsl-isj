# CODEX TASK — PF-DEI sensor-aware forward-operator closure

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Normative science contract:

`docs/CG_PC_CTT_PF_DEI_SENSOR_GENERATIVE_CHAIN_FREEZE_20260828.md`

Validation helpers:

- `experiments/cg_pc_ctt/pf_dei_observation_contract.py`
- `experiments/cg_pc_ctt/selftest_pf_dei_observation_contract.py`

This task supersedes all occupancy-to-Bernoulli PF-DEI replay tasks.

## Objective

Close the exact physical observation chain used by PMFS before any new PF-DEI likelihood or SBI model is allowed:

`source -> transport -> physical concentration -> persistent sensor state -> measured concentration -> consumed 10-sample mean -> HIT/NOTHING`.

Do not implement C++, Active Probe, source posterior updates or a 60-arm matrix in this task.

Do not use H01/H02/H03 development source truth or localization error.

## Stage 0 — sync and freeze provenance

1. Pull the branch and record the exact HEAD.
2. Run:

```bash
cd /home/zyc/uav-gsl-isj
python3 experiments/cg_pc_ctt/selftest_pf_dei_observation_contract.py
python3 experiments/cg_pc_ctt/selftest_v4_final_reference.py
```

Run any still-present V5/V6-A regression tests as archival checks, but do not restore deleted/superseded code from another branch.

3. Record the frozen V6-A negative result without recomputing thresholds:

- 30 runs / 150 contexts;
- 0/30 continuous predictive pass;
- H01/H02/H03 transfer pass = 1/10, 0/10, 2/10;
- absolute pass = 0/30.

## Stage 1 — prove O2 from source and freeze it

Read the exact branch source and document line-level provenance for both sides.

### CTT prediction side

Prove that the existing CTT trace marks a cell occupied at a timestep when one or more simulated filaments occupy it, and that multiple filaments in that timestep do not produce a physical concentration value.

### PMFS observation side

Prove that StopAndMeasure:

1. receives measured gas sensor samples;
2. consumes the configured measurement block after settling;
3. averages measured concentration;
4. compares that average to `thresholdGas`;
5. produces `GAS HIT/NOTHING`.

Write:

`OBSERVATION_OPERATOR_CLASS = O2`

Do not leave O1/O2 unresolved after this source proof.

## Stage 2 — inventory and reconstruct the real measured samples

Archive root:

`/home/zyc/CG_PC_CTT_V3_ORR_MULTI30_20260827`

Inventory all 30 OFF development runs.

The independent audit reports:

- dedicated `continuous_measurement_samples_file`: 0/30;
- `sensor_trace.csv`: 30/30.

Verify this yourself and report exact counts.

### Allowed fields

Use only fields that were actually observable by the algorithm/runtime, especially:

- timestamp;
- `measured_gas_ppm`;
- pose;
- causally available wind if required for context metadata.

### Forbidden fields

Do not read or use:

- `true_gas_ppm`;
- true source;
- final localization error;
- ON/OFF improvement;
- any post-run performance label.

If a parser must read a row containing forbidden columns, explicitly drop those columns before constructing any in-memory analysis object and record that behavior.

### Exact consumed-sample mapping

Do NOT group every ten consecutive `sensor_trace.csv` rows.

Recover from runtime/source provenance exactly which sensor samples were delivered to StopAndMeasure after settling and consumed in each completed block.

For every completed block, preserve:

- block id;
- consumed sample indices;
- all ten measured ppm values;
- all ten timestamps;
- block mean;
- threshold;
- archived `GAS HIT/NOTHING` event.

Mandatory parity:

`recomputed mean > thresholdGas == archived block event`

for **100% of completed blocks across all 30 runs**.

Any mismatch is a STOP until provenance is fixed. Do not add tolerance to the binary decision.

Required artifact:

`artifacts/pf_dei_forward/observed_block_manifest.csv`

with no truth/performance columns.

## Stage 3 — recover the authoritative sensor dynamics

Locate the exact GADEN sensor implementation and launch/config used by these runs, whether inside this repository, a ROS workspace dependency, or the frozen VM build provenance.

Document with code/config hashes:

- sampling cadence;
- dead time;
- rise/response dynamics;
- recovery dynamics;
- measurement noise model and RNG semantics;
- saturation/clipping if any;
- initialization;
- whether state persists during movement;
- whether state persists across StopAndMeasure blocks and source-update contexts.

Do not replace the native dynamics by the convenient recurrence from the audit text unless the source proves that exact recurrence.

Preferred engineering route: expose/share the native sensor transition code so the forward builder and simulator cannot drift.

Required report section:

`SENSOR_STATE_SCOPE = RUN_PERSISTENT` or a source-proven alternative.

If the native source actually resets state somewhere, report the exact reset boundary rather than assuming persistence.

## Stage 4 — determine how to generate physical concentration for candidate sources

The existing CTT occupancy trace is insufficient.

Search authoritative GADEN/source code for the function/path that produces the physical gas concentration supplied to the dynamic sensor at a pose and simulator time.

Classify one of:

### A — shared physical forward path exists

A truth-free builder can execute the same physical concentration logic for a candidate source/transport realization at requested sample poses/times.

Implement/reuse that path and preserve code/config hashes.

### B — only full GADEN execution is trustworthy

Build a streamed forward runner that launches the native GADEN simulation for a candidate source/transport realization and records the native physical/measured sensor trace along the requested trajectory/timestamps.

Do not approximate it with CTT occupancy.

### C — no auditable concentration path can be reproduced

Stop with:

`STOP_PF_DEI_FORWARD_OPERATOR_UNRESOLVED`

Do not fit occupancy-to-ppm from historical outcomes.

## Stage 5 — build one synthetic end-to-end parity case before scaling

Use a new controlled synthetic case with a source chosen by the experimenter; this is not H01/H02/H03 development truth.

Run the authoritative native simulator and the proposed PF-DEI forward path using matched:

- source;
- environment/map;
- transport seed/substream;
- sensor parameters;
- sensor RNG where deterministic replay is supported;
- robot pose/time schedule.

Verify as strongly as the implementation allows:

1. physical concentration trace parity;
2. persistent sensor-state behavior parity;
3. measured ppm parity under deterministic RNG, or frozen distributional parity if the native noise path cannot be bit-replayed;
4. exact 10-sample block mean parity;
5. exact HIT/NOTHING parity.

A parity failure blocks dataset generation.

## Stage 6 — stream a minimal truth-free candidate forward sample

Only after Stage 5 passes, materialize a very small diagnostic sample, e.g. one House, one nondevelopment synthetic run/context, a small candidate subset and all frozen transport realizations.

Normative payload must include physical and measured concentrations in physical units and run-persistent sensor-state provenance.

Validate using:

`validate_forward_payload(...)`

from `pf_dei_observation_contract.py`.

Do not yet generate the full training bank.

## Stage 7 — decision

Return exactly one verdict:

### `PF_DEI_FORWARD_OPERATOR_CLOSED`

Only if all are true:

- O2 is source-proven;
- 30/30 observed `sensor_trace.csv` inventory is understood;
- 100% block-consumption/HIT reconstruction passes;
- exact sensor dynamics/config and persistence semantics are identified;
- physical candidate-source concentration can be generated without occupancy conversion;
- synthetic end-to-end parity passes;
- a minimal sensor-aware forward payload passes the contract selftest.

### `STOP_PF_DEI_FORWARD_OPERATOR_UNRESOLVED`

Otherwise.

No intermediate result authorizes a source-likelihood or performance experiment.

## Stage 8 — prepare but do not execute the SBI handoff

If and only if the operator is closed, add a short design note for the next task describing how the exact forward simulator can generate training examples with:

- global source `S`;
- context-specific transport nuisance `Z_c`;
- coherent run-persistent sensor state;
- measured ppm/time/pose observations;
- random prefixes for sequential online inference.

Do not select a neural architecture based on localization performance in this task.

## Deliverables

Commit:

- source/config provenance report;
- `artifacts/pf_dei_forward/observed_block_manifest.csv`;
- observed reconstruction script(s);
- sensor-model provenance/hash manifest;
- physical concentration forward-path provenance;
- synthetic parity script/results;
- minimal valid forward payload or a precise stop report;
- `docs/PF_DEI_FORWARD_OPERATOR_CLOSURE_REPORT_20260828.md`.

The closure report must explicitly state that raw measured samples are correlated and were not treated as independent evidence.
