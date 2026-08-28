# PF-DEI sensor-aware physical generative chain — normative freeze

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Status: **FORWARD-OPERATOR CLOSURE ONLY / NO NEW LIKELIHOOD / NO C++ / NO PERFORMANCE CLAIM**

This document supersedes the occupancy-to-Bernoulli PF-DEI likelihood as a normative method.

## 1. Established failure evidence

The following negative results are frozen and must not be reinterpreted after later experiments:

- V5 passive cumulative ledger: 30 runs / 150 contexts, 0/30 runs with ACCEPT.
- V6-A removes hard source components and still gives 0/30 continuous predictive pass.
- V6-A source-transfer-only pass: H01 1/10, H02 0/10, H03 2/10.
- V6-A absolute adequacy: 0/30.

Therefore:

> M1 is non-degenerate, but source validity is unproven.  Frequency-only source evidence is not cross-context stable or absolutely adequate.

## 2. O2 observation-operator verdict is now fixed

Repository source establishes that the old CTT quantity and the PMFS observation are different physical variables.

### CTT side

At each simulator timestep, a free cell receives at most one count when one or more simulated filaments occupy that cell.  Multiple filaments in the same timestep do not increase that count.  The final field divides counts by the number of timesteps.

Thus CTT `occupancyWords` / hit frequency is an **any-filament cell-occupancy event**, not a gas concentration in ppm.

### PMFS side

A StopAndMeasure block collects a fixed number of measured gas samples.  PMFS averages those measured concentrations and calls the completed block `GAS HIT` only when the mean exceeds `thresholdGas`.

Therefore the following identities are forbidden:

`filament occupancy bit == measured concentration`

`filament occupancy frequency == probability that a 10-sample mean exceeds thresholdGas`

No empirical occupancy-to-ppm, occupancy-to-HIT, logistic, isotonic, affine, lookup-table, House-specific, or seed-specific mapping may be fitted from the development outcomes.

## 3. Normative physical chain

PF-DEI now uses the following scientific object:

`S -> Z_c -> C_t -> R_t -> M_t -> Y_b`

where:

- `S`: global source location, invariant across a run;
- `Z_c`: context-specific transport realization / nuisance state;
- `C_t`: physical gas concentration at the robot sensor location and time under candidate source and transport;
- `R_t`: persistent internal gas-sensor state;
- `M_t`: measured gas concentration delivered to PMFS;
- `Y_b`: PMFS completed-block event produced from the exact consumed measured samples.

The observation rule is the native one:

`Y_b = 1[ mean_{i in consumed block b} M_i > thresholdGas ]`.

The exact transition for `R_t` is **not** frozen as a hand-written first-order equation in this document.  It must be recovered from the authoritative GADEN/sensor implementation and configuration.  Dead time, asymmetric rise/recovery, noise and state persistence must follow the native simulator exactly.

## 4. Persistent sensor state is not a context nuisance reset

`Z_c` may change between source-update contexts.

The sensor state must not be independently reinitialized for each context.  If the native sensor keeps memory across movement and StopAndMeasure cycles, PF-DEI forward simulations must keep the same coherent state trajectory.

Required metadata:

- `sensor_state_scope = run_persistent`;
- `context_state_reset = false`.

A per-context sensor reset is a scientific contract violation even if it improves localization.

## 5. Observed-data contract

Historical development archives contain `sensor_trace.csv` for the 30 OFF runs according to the independent audit.

Only causally observed fields may be used.  In particular:

- `measured_gas_ppm`: allowed;
- timestamps: allowed;
- robot pose: allowed;
- measured/estimated wind available to the runtime: allowed;
- `true_gas_ppm`: forbidden for inference, tuning, block reconstruction, adequacy decisions or method selection;
- true source and localization error: forbidden until the frozen performance stage.

The dedicated `continuous_measurement_samples_file` is not required if `sensor_trace.csv` can be proven to contain the exact measured values delivered to `/PID/Sensor_reading`.

## 6. Exact block-consumption mapping

The approximately 0.2-s sensor trace is **not** automatically split into consecutive groups of ten.

The authoritative runtime must determine exactly which ten measured samples were consumed after settling for every completed StopAndMeasure block.

A valid reconstruction must prove for every archived block:

1. exactly `measurement_block_samples` samples were consumed;
2. samples are time ordered and not reused;
3. settle/moving-state samples are not included;
4. recomputed block mean equals the algorithm input to floating precision where that value is archived;
5. `mean > thresholdGas` reproduces the archived `GAS HIT/NOTHING` event for every block.

Failure to achieve 100% block-decision reconstruction is a blocking provenance error, not a tunable tolerance.

## 7. The raw samples are correlated observations

If ten measured samples per block are recovered, they must not be treated as ten independent Bernoulli or Gaussian replicates.

Their dependence arises from at least:

- physical plume persistence/intermittency;
- native dynamic sensor memory;
- dead time and response/recovery dynamics;
- transport continuity;
- measurement noise structure.

The later inference model must condition on or marginalize this dependence through the forward simulator or an explicitly validated sequential model.

## 8. Predictive-side concentration contract

A normative PF-DEI predictive payload must contain physical concentrations generated by an authoritative GADEN forward path and measured concentrations generated by the authoritative sensor path.

Required conceptual fields:

- physical concentration trace in physical units;
- simulated measured concentration trace;
- source candidate identity;
- transport realization key/seed;
- sample timestamps matching the observation schedule;
- sensor model code hash;
- sensor parameter/config hash;
- persistent sensor-state provenance.

CTT occupancy may be retained as a diagnostic or matched ablation only.  It cannot be the main observation variable.

## 9. Two legal ways to close the forward operator

### Path A — shared native concentration/sensor implementation

If the repository/VM source exposes the same physical concentration query and sensor transition used by GADEN, extend a truth-free forward builder to evaluate candidate source/transport realizations at the actual sample poses/timestamps and pass them through exactly that sensor model.

Prefer shared source/library code over a reimplementation.

### Path B — full GADEN forward simulation

If no safe shared concentration query exists, run full GADEN forward simulations with the candidate source and frozen nuisance randomization, and record the native measured sensor output at the required trajectory/timestamps.

This is slower but scientifically valid.

### Forbidden path

Do not estimate physical concentration from CTT occupancy/frequency using an empirical conversion.

If neither Path A nor Path B can generate the native measured quantity with auditable provenance, stop:

`STOP_PF_DEI_FORWARD_OPERATOR_UNRESOLVED`

## 10. Synthetic parity is allowed; development truth is not

A controlled synthetic parity case may use a known source because that source is an input chosen by the experimenter.

Use such cases to verify:

- physical concentration parity;
- sensor-state evolution parity;
- measured ppm parity/distributional parity under controlled RNG;
- exact block HIT parity.

Do not use the true source of H01/H02/H03 seeds 0..9 to design or fit the forward operator.

## 11. Inference architecture is intentionally not frozen yet

Until the forward operator is closed, do not freeze a new source likelihood, neural ratio estimator, neural likelihood estimator, SBI network, event hazard, semi-Markov feature set or active planner.

After closure, compare candidate inference engines on the **same exact sensor-aware forward data**.  The preferred paper direction is physics-factorized simulation-based inference because it can marginalize context-specific transport and persistent sensor dynamics without pretending raw samples are independent.

## 12. Paper-level interpretation

The intended innovation remains one coherent ability:

**Physics-Factorized Dynamic Event Inference (PF-DEI)**

The defensible scientific claim is not Pearl/Rubin source causal-effect estimation.  It is a physics-factorized generative model that separates:

- global source;
- context-specific transport;
- persistent sensor dynamics;
- observed temporal measurements;

before source assimilation.

The 2026 cross-domain inspiration is conceptual: reconstruct/condition hidden dynamics before inferring the invariant scientific quantity, and use physics-based forward simulation when nuisance effects are too entangled for a tractable hand-written likelihood.
