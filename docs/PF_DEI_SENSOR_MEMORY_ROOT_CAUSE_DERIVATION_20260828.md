# PF-DEI sensor-memory root-cause derivation

Date: 2026-08-28

Status: **MECHANISM DERIVATION / NO LOCALIZATION-PERFORMANCE CLAIM**

## 1. Forward operator is now closed

The independent PF-DEI closure established the native chain

`S -> Z_c -> C_t -> R_t -> M_t -> Y_b`

with the historical sensor configuration:

- sample cadence: 0.2 s;
- gain 1, baseline 0;
- `tau_rise = tau_recovery = 1.2 s`;
- dead time 0.4 s;
- noise 0, drift 0;
- sensor state persistent across movement, stops and source-update contexts;
- PMFS block decision: ten consumed measured-ppm samples averaged and compared with `thresholdGas = 0.1 ppm`.

Therefore random measurement noise cannot explain the historical seed-dependent reversals under this frozen configuration.

## 2. A stronger failure mechanism than frequency compression

Earlier references implicitly treated a stop/context observation as locally generated from the current location and current transport state.  That assumption is false when the sensor state persists.

The correct native observation state is

`R_t = G(R_{t-1}, C_{<=t})`

and therefore

`M_t = H(R_t)`.

Consequently, two runs can have the same current physical concentration suffix and different measured suffixes solely because their pre-suffix trajectory/exposure histories differ.

This mechanism is called:

**trajectory-dependent observation aliasing**

Chinese: **轨迹依赖观测混叠**.

It means a spatially assigned PMFS HIT can encode gas encountered at an earlier location/time rather than only the current stop.

## 3. The closure parity case already falsifies locality

The synthetic end-to-end parity case contains an evaluation block whose ten native physical-concentration samples are all exactly zero.  The preceding block/position has large physical exposure.  With native run-persistent sensor state, the zero-input evaluation block has a measured mean of about 6.29 ppm and is a PMFS HIT.  Resetting the sensor at the evaluation boundary changes the first sample by about 10.07 ppm; with a clean zero state and the same zero physical-concentration suffix, the block would be NOTHING.

Thus the following locality model is false:

`p(Y_b | current physical concentration block)`.

The failure is deterministic under the frozen historical configuration because sensor noise is zero.

## 4. Closed-form inherited-state lower bound

Because `tau_rise = tau_recovery = tau`, gain is positive, baseline/noise are zero and physical concentration is non-negative, the native first-order sensor is a positive linear system with delay.  The homogeneous contribution of a previous measured state `m_prev` to a future sample after elapsed time `t` is

`m_prev * exp(-t/tau)`.

The delayed physical input contributes non-negatively, so the homogeneous term is a lower bound on the inherited-state contribution.

Let:

- `g` = elapsed time from the previous stop's last consumed sample to the next stop's first consumed sample;
- `dt = 0.2 s`;
- `B = 10` consumed samples;
- `tau = 1.2 s`.

Then the inherited-state-only lower bound on the next first block mean is

`LB = m_prev * exp(-g/tau) * A_B`

with

`A_B = (1/B) * sum_{k=0}^{B-1} exp(-k*dt/tau)`.

For the frozen configuration,

`A_B ~= 0.5283569`.

At zero inter-stop gap, any previous sensor state above

`0.1 / A_B ~= 0.1893 ppm`

is by itself sufficient to force a nominally zero-input next block above the PMFS 0.1 ppm HIT threshold.

Movement reduces this inherited contribution exponentially, but the median historical inter-stop gap is of the same order as the 1.2 s sensor time constant, so carry-over cannot be assumed negligible.

## 5. Truth-blind historical lower-bound result from the closure manifest

Using only `observed_block_manifest.csv`, measured ppm, timestamps and the source-proven sensor parameters, the lower-bound diagnostic gives:

- 514 reconstructed physical stops;
- 484 inter-stop transitions;
- 102/484 transitions (21.1%) where inherited sensor state alone is sufficient to force the next first block HIT under a counterfactual zero physical-gas suffix;
- all 102 of those transitions are indeed archived HITs, as required by positivity.

House breakdown:

- House01: 0/161 (0%);
- House02: 37/163 (22.7%);
- House03: 65/160 (40.6%).

This is not a localization-performance metric and does not use source truth.  It proves that spatially local interpretation of a substantial fraction of H02/H03 first-block HITs is physically invalid under the native sensor dynamics.

The pattern is also qualitatively consistent with the historical observation that H01 was easier for the prior source-evidence mechanisms while H02/H03 were much less stable, but no causal claim about localization performance is made from that coincidence alone.

Executable diagnostic:

`experiments/cg_pc_ctt/pf_dei_sensor_memory_bound.py`

## 6. A second structural correction: contexts are not conditionally independent

Once `R_t` persists across context boundaries, the previous factorization

`p(Y_1:C | S) = product_c p(Y_c | S)`

is generally false.

It becomes valid only after conditioning on each context's incoming sensor state:

`p(Y_1:C | S) = integral product_c p(Y_c, R_c_out | S, Z_c, R_c_in) p(Z_c|context_c) dZ dR`

with the hard state-link constraint

`R_c_in = R_{c-1}_out`.

Therefore a normative PF-DEI method must not independently score/reset contexts and then simply sum their source evidence.  It must preserve the complete run-prefix sensor state, either explicitly in a state-space likelihood/particle method or implicitly through a run-level simulation-based inference model.

This is a deeper correction than replacing occupancy by physical concentration.

## 7. Frozen mechanism ladder after forward closure

### F1 — sensor-history locality

Already positive in the closure synthetic case:

`SENSOR_HISTORY_LOCALITY_FALSIFIED = YES`.

### F2 — ideal versus native sensor source inference

Use exactly the same candidate-source physical GADEN traces and transport draws.

- A1: ideal observation operator, measured concentration equals physical concentration, while preserving the exact sample/block schedule;
- A2: native run-persistent sensor operator.

Use the same inference engine and the same truth-blind source candidates in A1/A2.

If A1 is predictive across contexts/runs but A2 is not, sensor-history aliasing is a dominant remaining blocker.

### F3 — finite transport versus physics-randomized transport

Only after the native sensor is correctly represented.  If A2 remains inadequate, broaden `Z` using source-independent physics ranges/configuration rather than development localization outcomes.

If adequacy is restored only after broadening `Z`, record finite transport-family insufficiency.

## 8. Consequence for the final PF-DEI inference engine

A candidate neural/SBI model must consume a **run prefix**, not isolated context snapshots.

A suitable likelihood-free target is a candidate-conditioned neural ratio estimator:

`r(D,S,kappa) = p(D | S,kappa) / p(D | kappa)`

where `D` is the complete measured-ppm sequence/prefix with timestamps, poses, wind and block/context markers, and `kappa` denotes observable run context.

Training examples are generated entirely by the closed native forward operator:

1. sample source candidate `S ~ q0`;
2. sample source-independent transport nuisance sequence `Z_1:C`;
3. generate physical concentration on the full trajectory;
4. propagate one coherent run-persistent native sensor state;
5. emit measured ppm and exact PMFS block membership;
6. pair the generated run prefix with its source as a positive pair and with an independently sampled same-context candidate source as a negative pair.

Under balanced joint-vs-product classification, the optimal logit estimates

`log p(D|S,kappa) - log p(D|kappa)`

and the discrete source posterior is

`q(S|D,kappa) proportional q0(S|kappa) * exp(f_psi(D,S,kappa))`.

No independence assumption over the ten within-block samples or over contexts is required.

This architecture remains a candidate until the matched F2/F3 mechanism tests are completed.
