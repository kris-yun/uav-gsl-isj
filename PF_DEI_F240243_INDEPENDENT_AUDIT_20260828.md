# PF-DEI f240243 independent audit (2026-08-28)

## Verdict

The observation-operator gate is the strongest improvement in this revision, but the current `pf_dei_phase_marginal_reference.py` is not yet a valid source likelihood for the archived experiment.

The source evidence resolves the operator classification as **O2**, not O1:

- CTT/PMFS forward simulation increments a cell when at least one simulated filament occupies it during a simulation step.
- Runtime PMFS first passes GADEN concentration through a causal dynamic gas-sensor model, averages ten measured samples, and declares HIT only when that average exceeds the gas threshold.

Thus a CTT occupancy bit and a runtime PMFS HIT are different random variables.

## Archive inventory established during this audit

- Dedicated `continuous_measurement_samples_file`: 0/30 OFF runs.
- Runtime `sensor_trace.csv`: 30/30 OFF runs.
- Each `sensor_trace.csv` contains 0.2 s ordered `measured_gas_ppm` and `true_gas_ppm` columns.
- The VGR runtime source writes `measured_gas_ppm` and publishes the same value on `/PID/Sensor_reading` in the same simulation tick.
- Scientific reconstruction must read only the causally observed `measured_gas_ppm`; `true_gas_ppm` is forbidden.

Therefore a high-resolution observed stream probably can be reconstructed, but exact membership of the ten samples consumed by each completed StopAndMeasure block must be matched by simulation timestamps and action-log boundaries.

## Problems remaining in the frozen reference

1. `block_hit_probability()` integrates binary occupancy inside an interval and converts the occupied fraction into one Jeffreys-smoothed Bernoulli probability. It preserves block order, but it is not a full concentration/sensor sequence likelihood.
2. Treating roughly 80 within-stop samples as 80 independent observations would be pseudo-replication. The actual asymmetric sensor has dead time, rise/recovery constants, and persistent state, so adjacent samples are strongly dependent.
3. Sensor state is not context-independent. It evolves continuously across the run and carries information from earlier locations into the current stop. A context-wise reset or independent sensor nuisance marginalization is physically wrong.
4. The archived CTT occupancy record has no concentration units and cannot be passed through the actual sensor FOPDT/asymmetric observation operator without an additional physical concentration model.
5. The truth-blind 20/30 threshold is an actionability gate only. Passing it cannot establish 20/30 localization improvement or a 10% pooled error gain.

The synthetic science selftest passes, but it tests internal algebra under constructed compatible data; it cannot validate the missing observation semantics.

## Required method upgrade

Keep the paper name PF-DEI, but use the complete causal observation chain:

`global source S -> context transport Z_c -> true concentration C_t -> persistent sensor state R_t -> measured samples M_t -> block decision Y_b`.

A minimal physical model is:

`C_t = F(S, Z_c, position_t, wind_t)`

`R_t = a_t R_(t-1) + (1-a_t) C_(t-delay) + process/noise terms`

`M_t = R_t + measurement noise`

`Y_b = 1[(1/10) sum_(t in block b) M_t > thresholdGas]`.

The source is global, transport is context-specific, and sensor state is a trajectory-level causal state rather than an independent per-context nuisance.

The preferred source likelihood should score the observed measured-concentration sequence under this model. The binary block likelihood is a matched coarse ablation. Semi-Markov remains a source-independent dynamic null only.

## Fast decision path

1. Freeze the 30 authoritative `sensor_trace.csv` files and exact block/sample alignment using only measured values and timestamps.
2. Do not run the existing occupancy-to-Bernoulli PF-DEI score as the final diagnostic; O1 is false.
3. Determine whether the truth-free builder can emit source-conditioned concentration traces in physical units and then pass them through the exact frozen sensor model.
4. If it cannot, classify the finite CTT occupancy family as insufficient for PF-DEI and proceed directly to physics-randomized GADEN simulation-based inference. Do not introduce an empirically fitted occupancy-to-concentration transform.
5. Validate dynamic predictive transfer truth-blind, then freeze. Only after that inspect localization and require pooled improvement >=10%, >=20/30 improved development runs, no House pooled regression worse than 5%, and no false-confident collapse.
6. A final publication claim still requires untouched held-out seeds after method development; the reused seeds 0..9 are development evidence.

## Reproducibility

- Audited branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`
- Audited HEAD: `f2402436b70d1179a3ab0ef698dfa73df73a22a4`
- `PF_DEI_PHASE_MARGINAL_REFERENCE_SELFTEST PASS` reproduced in an isolated VM copy.
