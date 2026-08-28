# PF-DEI exact sensor deconvolution — mechanism derivation

Date: 2026-08-28

Status: **TRUTH-BLIND MECHANISM DIAGNOSTIC / NOT A LOCALIZATION CLAIM**

## 1. Why this diagnostic exists

The forward operator is now closed and the sensor-memory lower-bound audit is independently reproduced:

- 484 inter-stop transitions;
- 102/484 transitions where previous measured state alone can keep the next block mean above 0.1 ppm under zero current input;
- H01 0/161, H02 37/163, H03 65/160;
- median gap 1.2 s, equal to sensor tau = 1.2 s.

This proves that the PMFS block event is not a local function of the current block concentration.  It does **not** prove that every qualifying event is a false physical hit or that sensor memory is the only localization failure.

The next diagnostic should therefore quantify the actual decision changes induced by the native sensor on the same historical physical concentration sequence, without opening source truth or localization error.

## 2. A stronger fact: the frozen native sensor is algebraically invertible

The source-proven archived configuration is:

- regular sample cadence `dt = 0.2 s`;
- dead time `L = 0.4 s`;
- `tau_rise = tau_recovery = tau = 1.2 s`;
- gain = 1;
- baseline = 0;
- additive sensor noise = 0;
- drift = 0;
- saturation is not active in the closure parity data;
- initial state/input = 0;
- state is run-persistent.

The native manifest freezes the state transition

`z[k] = exp(-dt/tau) z[k-1] + (1-exp(-dt/tau)) u_delayed[k]`.

Let

`alpha = exp(-dt/tau)`.

Because rise and recovery constants are equal, the transition is branch-independent.  Because noise and drift are zero and gain is one, measured ppm equals the dynamic state inside the unsaturated range.

Therefore

`u_delayed[k] = (M[k] - alpha M[k-1]) / (1-alpha)`.

The native delay history uses causal piecewise-linear sampled-input interpolation.  Here

`L/dt = 0.4/0.2 = 2`

exactly, so on the sample grid

`u_delayed[k] = C[k-2]`.

Hence

`C[k-2] = (M[k] - alpha M[k-1]) / (1-alpha)`.

This is an exact diagnostic inverse for the frozen archived configuration.  It is not claimed as a generic inverse for noisy/asymmetric/saturated sensors.

## 3. Closure-evidence parity already validates the inverse

Applying the equation to the 50-sample synthetic closure trace recovers the native GADEN physical concentration samples with numerical error at floating precision (approximately 1e-14 ppm in the independent derivation).

This means the observed historical measured trace contains an almost lossless delayed representation of the physical concentration sequence under the frozen zero-noise model.  Sensor memory therefore does not fundamentally destroy information when the complete continuous measured sequence and the correct sensor dynamics are retained.  It **moves and mixes information across time**.

This distinction is central:

> the primary failure mechanism is not merely that the sensor has memory; it is that a memoryless/local inference model attributes a history-dependent measured event to the current spatial stop/context.

Call this **sensor-state misattribution / trajectory-dependent observation aliasing**.

## 4. Consequence for context factorization

The old factorization

`p(Y_1:C | S) = product_c p(Y_c | S)`

is not physically valid because sensor state crosses context boundaries.

Conditionally valid structure is

`p(Y_c, R_out,c | S, Z_c, R_in,c)`

with

`R_in,c = R_out,c-1`.

A correct run-level model may either:

1. propagate/marginalize the persistent sensor state in the forward model; or
2. when the exact inverse is valid, canonicalize the measured trace back to physical concentration before transport/source inference.

The inverse diagnostic is scientifically useful because it separates sensor-state misattribution from transport-family insufficiency before training a large SBI model.

## 5. Six-decimal historical serialization does not invalidate the test

Historical `sensor_trace.csv` prints measured ppm to six decimal places.  Let each printed measurement have at most half-quantum error

`q/2 = 0.5e-6 ppm`.

For the frozen inverse, the worst-case induced physical-sample error is bounded by

`eps_C <= (q/2) * (1+alpha)/(1-alpha)`.

With `dt=0.2`, `tau=1.2`, this is approximately

`6.014e-6 ppm`.

This bound is determined before examining House/seed outcomes.  A counterfactual ideal block whose reconstructed mean lies within this bound of `thresholdGas` must be marked `AMBIGUOUS_SERIALIZATION_MARGIN`, not forced to HIT/NOTHING.

## 6. Immediate truth-blind historical counterfactual

For each of the 30 archived OFF runs:

1. read only timestamp and `measured_gas_ppm` from the complete run-level `sensor_trace.csv`;
2. apply the exact inverse to obtain reconstructed physical sample input `C_hat(t)` for every recoverable sample;
3. re-run the frozen forward recurrence on `C_hat` and verify measured-trace reconstruction within the source-proven serialization bound;
4. map the exact ten consumed samples for every PMFS block;
5. compute the counterfactual ideal-sensor block mean from `C_hat` at those sample times;
6. compare ideal HIT/NOTHING to archived native HIT/NOTHING.

Required categories:

- `NATIVE_HIT_IDEAL_NOTHING`: sensor dynamics changes the block from ideal NOTHING to native HIT;
- `NATIVE_NOTHING_IDEAL_HIT`: sensor dynamics changes the block from ideal HIT to native NOTHING;
- `SAME_HIT`;
- `SAME_NOTHING`;
- `AMBIGUOUS_SERIALIZATION_MARGIN`;
- `UNRECOVERABLE_END_OF_RUN` for samples whose future delayed observation is unavailable.

These labels are observation-operator counterfactuals.  They are **not** statements about true-source correctness or localization error.

## 7. Correct matched A1/A2 source-evidence design

A subtle but important correction to the earlier SBI task:

It is not scientifically clean to feed the same native historical measured sequence to both an ideal-sensor forward model and a native-sensor forward model.  The historical data were generated by the native sensor.

The exact inverse now supplies the missing matched observation arm:

### A1 — ideal sensor

Observed sequence:

`D_ideal = C_hat(t)`

Candidate prediction:

native GADEN physical concentration `C_s,z(t)` on the same historical poses/timestamps.

### A2 — native persistent sensor

Observed sequence:

`D_native = measured_gas_ppm(t)`

Candidate prediction:

exact native sensor applied continuously to the **same** candidate physical trace `C_s,z(t)`.

Thus A1/A2 differ only by the known sensor operator and are matched on trajectory, source candidates, transport draws and physical forward simulation.

No true H01/H02/H03 source is needed.

## 8. Theoretical expectation under a correct full-sequence inference engine

For the frozen deterministic, unsaturated, zero-noise sensor, the A2 sequence is almost an invertible transform of A1 except for dead-time boundary samples.

Therefore a sufficiently correct run-level inference engine should retain nearly the same source information in A1 and A2.

If A1 is strong but A2 is weak, the interpretation is **not** automatically “the sensor destroyed source information.”  It is more likely that the inference representation failed to model/invert the known persistent sensor operator.

This refines the mechanism labels:

- old block/frequency proxy fails, A1 and correctly modelled A2 recover -> `LOCAL_OBSERVATION_ALIASING_DOMINANT`;
- A1 recovers, A2 only recovers after explicit inverse/state modelling -> `SENSOR_STATE_MISATTRIBUTION_DOMINANT`;
- A1 and correct A2 both fail -> `TRANSPORT_FAMILY_OR_SOURCE_FORWARD_INSUFFICIENT`;
- broader physics-randomized GADEN nuisance is required -> `FINITE_TRANSPORT_FAMILY_INSUFFICIENT`.

## 9. What this does not authorize

Do not use deconvolved physical concentration as hidden truth.  It is a deterministic transform of allowed measured data under a source-proven archived sensor model.

Do not inspect true source or localization error during this mechanism stage.

Do not change `thresholdGas`, sensor tau/dead time, House-specific thresholds or transport ranges from these results.

Do not run C++ or the 60-arm matrix until a native-sensor-aware source model passes the truth-blind mechanism/adequacy stage.
