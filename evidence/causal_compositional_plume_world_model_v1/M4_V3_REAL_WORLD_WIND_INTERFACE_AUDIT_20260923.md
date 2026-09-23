# M4-v3 Real-World Wind-Interface Audit — Historical House02 Closed Loop

Date: 2026-09-23  
Branch: `research/m4-v3-interventional-evolution-propagator`  
Status: **INPUT-CONTRACT WARNING — DO NOT USE HISTORICAL GMRF FIELD AS A VERIFIED DEPLOYMENT INPUT**

## Scope

This audit uses the previously preserved native House02 PMFS closed-loop artifacts from:

`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

It does not modify M4-v3 and does not evaluate the M4-v3 plume model.

Purpose:

> Check whether the existing PMFS/GMRF wind-estimation artifacts can be treated as a deployment-compatible wind field for M4-v3.

## Historical run contract

House02 seed0/seed1 both used:
- `useWindGroundTruth: false`;
- PMFS reduced grid `27 x 39`, cell size `0.3000000119 m`;
- local anemometer topic routed to GMRF-wind;
- 5 source-probability updates over 300 s.

The GMRF export contains 631 cells per source update.

## Magnitude audit

Local wind traces are in m/s and contain 1500 samples over 300 s.

| Run | local wind mean | local wind p95 | GMRF mean at update 1 | GMRF mean at update 5 | GMRF max at update 5 |
|---|---:|---:|---:|---:|---:|
| House02 seed0 | 0.14853 | 0.46437 | 5.36e-5 | 8.45e-4 | 0.02491 |
| House02 seed1 | 0.13104 | 0.43975 | 5.84e-5 | 6.85e-4 | 0.02133 |

At the GMRF cell nearest the robot at each source update, the estimated speed was zero for most updates. When nonzero, the estimated/local-wind ratio was approximately 0.0002–0.0024.

This is a material attenuation relative to the local anemometer signal.

## Unit check

The upstream GMRF-wind 2.0 source does not define a hidden unit conversion:
- the sensor callback reads `msg->wind_speed` as m/s;
- `insertObservation_GMRF` converts that m/s magnitude directly to Cartesian `wind_x/wind_y`;
- the service returns the internal Cartesian means directly.

Therefore the several-order magnitude difference should not be dismissed as a simple documented unit conversion.

## Version / parameter-contract warning

The historical launch-parameter snapshots contain:

- `GMRF_lambdaObs: 1.0`
- `GMRF_lambdaObsLoss: 0.0`
- `GMRF_lambdaPrior_reg: 0.5`
- `GMRF_lambdaPrior_mass_conservation: 10.0`
- `GMRF_lambdaPrior_obstacles: 1.0`

The inspected upstream GMRF-wind 2.0 node (revision header 20/08/2026) declares a different active interface:

- `GMRF_lambdaPrior_advection`
- `GMRF_lambdaPrior_mass_conservation`
- `GMRF_lambdaPrior_diffusion`
- `GMRF_lambdaPrior_obstacles`
- `observation_var_wind_speed`
- `observation_var_wind_direction`

The old `GMRF_lambdaObs`, `GMRF_lambdaObsLoss`, and `GMRF_lambdaPrior_reg` names are not part of the inspected node's declared parameter interface.

This is sufficient to mark the historical estimated-wind artifact as **configuration-compatibility unverified**. It is not sufficient to prove that parameter mismatch caused the attenuation, because the exact historical GMRF binary/source hash was not preserved in this audit.

## Consequence for M4-v3

Do **not**:
- train M4-v3 to compensate for these historical attenuated fields;
- introduce an empirical wind-speed gain;
- treat the historical GMRF field as the final UAV deployment input;
- interpret a failure under this field as a failure of the interventional transport hypothesis.

## Required deployment wind-estimator gate W0

Before any estimated-wind M4-v3 confirmation:

1. freeze the exact GMRF-wind source commit/binary hash;
2. dump the node's actually declared/resolved parameters at runtime;
3. verify every requested launch parameter is declared and consumed;
4. inject known synthetic wind observations into a source-blind map;
5. verify estimates at observed cells retain the measurement vector within a predeclared tolerance;
6. verify service output is m/s by direct source/binary contract;
7. only then use the estimated field as M4-v3 input.

A suggested source-blind sanity boundary is:

[
0.5 le
rac{|hat W(x_{obs})|}{|W_{meas}(x_{obs})|}
le 1.5
]

at observed cells after estimator convergence, unless the GMRF model explicitly documents a different posterior behavior. The exact final W0 threshold must be frozen before new target-House plume outcomes are inspected.

## Scientific interpretation

M4-v3 should be evaluated as two nested questions:

1. **Transport-model question:**  
   Does the source-agnostic characteristic propagator work when the wind driver is known?

2. **Deployment-observation question:**  
   Does the same frozen propagator remain useful when wind is inferred from sparse real measurements?

The second question should ultimately marginalize or otherwise account for uncertainty in `p(W | anemometer, map)`; it should not silently replace the first question or alter the transport mechanism after holdout inspection.

## Current decision

- M4-v3 structural mechanism contract: unchanged, PASS.
- House02 D0: still blocked only by the exact canonical W2 dynamic sequence.
- Historical House02 GMRF export: useful as a warning/regression fixture, **not a verified deployment wind field**.
- No change to the M4-v3 architecture is authorized from this audit.
