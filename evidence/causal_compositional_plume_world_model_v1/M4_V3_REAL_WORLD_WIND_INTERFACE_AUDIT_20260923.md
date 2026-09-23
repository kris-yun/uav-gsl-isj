# M4-v3 Real-World Wind-Interface Audit — Historical House02 Closed Loop

Date: 2026-09-23  
Branch: `research/m4-v3-interventional-evolution-propagator`  
Status: **HISTORICAL INTERFACE INVALID FOR DEPLOYMENT — MAGNITUDE AND DIRECTION CONTRACTS BOTH FAIL**

## Scope

This audit uses the preserved native House02 PMFS closed-loop artifacts from:

`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

It does not modify M4-v3 and does not evaluate M4-v3 plume prediction.

Purpose:

> Determine whether the historical PMFS/GMRF wind path can be reused as the deployment-compatible wind input for M4-v3.

## Historical run contract

House02 seed0/seed1 both used:
- `useWindGroundTruth: false`;
- PMFS reduced grid `27 x 39`, cell size `0.3000000119 m`;
- `/Anemometer/WindSensor_reading` routed to PMFS and GMRF-wind;
- five source-probability updates over 300 s.

The GMRF export contains 631 free cells per source update.

## 1. Magnitude audit

Local wind traces are in m/s and contain 1500 samples over 300 s.

| Run | local wind mean | local wind p95 | GMRF mean at update 1 | GMRF mean at update 5 | GMRF max at update 5 |
|---|---:|---:|---:|---:|---:|
| House02 seed0 | 0.14853 | 0.46437 | 5.36e-5 | 8.45e-4 | 0.02491 |
| House02 seed1 | 0.13104 | 0.43975 | 5.84e-5 | 6.85e-4 | 0.02133 |

At the GMRF cell nearest the robot at each source update, the estimated speed was zero for most updates. When nonzero, the estimated/local-wind ratio was approximately 0.0002–0.0024.

This is a material attenuation relative to the local anemometer signal.

### Unit check

The inspected upstream GMRF-wind 2.0 source does not define a hidden unit conversion:
- the sensor callback reads `msg->wind_speed` as m/s;
- `insertObservation_GMRF` converts that m/s magnitude directly to Cartesian `wind_x/wind_y`;
- `WindEstimation` returns the internal Cartesian means directly.

Therefore the several-order magnitude difference cannot be dismissed as a documented unit conversion.

## 2. Direction-semantics audit — CONFIRMED CONTRACT CONFLICT

This audit found a direct semantic incompatibility in the historical simulation path.

### Historical VGR publisher semantics

The preserved House02 wind trace contains:
- `wind_u`;
- `wind_v`;
- `wind_direction_rad`.

Across all 1500 seed0 rows,

[
wind\_direction\_rad \approx \operatorname{atan2}(wind_v,wind_u)
]

with maximum wrapped numerical discrepancy only about `1.8e-4 rad`.

The VGR simulator source used by this project publishes:

- `Anemometer.header.frame_id = "map"`;
- `wind_speed = ||(u,v)||`;
- `wind_direction = atan2(v,u)`.

The GADEN/OpenFOAM `u,v` vector is the **downwind flow vector**.

Therefore the historical `/Anemometer/WindSensor_reading` message is a **map-frame downwind direction**.

### PMFS interpretation

The PMFS `Algorithm::windCallback` treats `msg->wind_direction` directly as `downWind_direction`, transforms its frame, and does not add π.

For the historical map-frame VGR message, this is consistent.

### GMRF-wind 2.0 subscriber interpretation

The inspected GMRF-wind 2.0 `sensorCallback` explicitly documents the incoming message as an **upwind** anemometer direction. It transforms that orientation into map frame and then computes:

[
downwind = upwind + \pi.
]

Applied to the historical VGR message, which was already downwind, this introduces an unnecessary approximately 180° reversal.

This is not a statistical interpretation. It is a direct interface-contract conflict.

It explains why the historical nonzero GMRF vectors near the robot were observed roughly opposite to the local `wind_u/v` direction (previous audit: about 144°–174° discrepancies, with additional estimator/model effects).

## 3. Parameter-contract warning

The historical launch snapshots contain:

- `GMRF_lambdaObs: 1.0`
- `GMRF_lambdaObsLoss: 0.0`
- `GMRF_lambdaPrior_reg: 0.5`
- `GMRF_lambdaPrior_mass_conservation: 10.0`
- `GMRF_lambdaPrior_obstacles: 1.0`

The inspected upstream GMRF-wind 2.0 node (revision header 20/08/2026) declares:

- `GMRF_lambdaPrior_advection`
- `GMRF_lambdaPrior_mass_conservation`
- `GMRF_lambdaPrior_diffusion`
- `GMRF_lambdaPrior_obstacles`
- `observation_var_wind_speed`
- `observation_var_wind_direction`

The historical `GMRF_lambdaObs`, `GMRF_lambdaObsLoss`, and `GMRF_lambdaPrior_reg` names are not part of the inspected active interface.

This is a second reason not to reuse the historical GMRF field as a deployment input. It does not by itself prove which parameter caused the magnitude attenuation because the exact historical GMRF source/binary hash was not preserved here.

## 4. Canonical M4-v3 wind contract

M4-v3 must not consume an ambiguous meteorological/anemometer angle.

The internal transport input is frozen conceptually as:

[
oxed{W_{map}^{down}(x,t)=(u(x,t),v(x,t))}
]

that is:
- Cartesian;
- map-frame;
- **downwind / flow-toward direction**;
- m/s.

All sensor- or vendor-specific conventions are converted exactly once at an adapter boundary.

### Simulation

GADEN/VGR `u,v` can be passed directly after spatial/time alignment.

### Physical anemometer

If the physical device reports the standard **upwind/from-direction**, the hardware adapter must:
1. interpret the vendor's handedness and zero-axis convention;
2. transform from sensor frame to map frame using TF;
3. reverse from upwind to downwind exactly once;
4. emit canonical Cartesian `(u,v)`.

No downstream component may repeat the reversal.

## 5. GMRF integration rule for M4-v3

For future M4-v3 validation, prefer an explicit canonical adapter followed by GMRF's `AddWindObservation` service rather than relying on the ambiguous raw-anemometer subscriber path.

Reason:
- the GMRF core `insertObservation_GMRF` documents its supplied direction as already **DownWind in the map reference system**;
- `AddWindObservation` passes the supplied speed/direction directly to that core routine;
- this gives one auditable conversion boundary.

This is an interface-cleanup requirement, not part of the M4-v3 scientific novelty.

## 6. Required deployment wind-estimator gate W0

Before any estimated-wind M4-v3 confirmation:

1. freeze exact GMRF-wind source commit and binary hash;
2. record all actually declared/resolved parameters;
3. reject unknown/obsolete requested parameters;
4. define one canonical map-frame downwind vector convention;
5. inject known synthetic canonical vectors at source-blind locations;
6. query `WindEstimation` after convergence at those same locations;
7. require positive vector alignment and reasonable magnitude retention;
8. run +x, -x, +y, -y cases so a π flip or axis swap cannot hide;
9. only then connect the estimated field to M4-v3.

Development-only W0 sanity boundaries to freeze before target-House outcomes:

[
\cos(\hat W,W_{in}) > 0.95
]

and

[
0.5 \le
\frac{\|\hat W(x_{obs})\|}{\|W_{in}(x_{obs})\|}
\le 1.5
]

at directly observed cells after estimator convergence.

The final threshold can be revised only before new target-House plume outcomes are inspected and with an estimator-model justification.

## 7. Consequence for M4-v3

Do **not**:
- train M4-v3 to compensate for historical attenuated or reversed GMRF fields;
- introduce an empirical wind-speed gain;
- let the main transport model learn a hidden π correction;
- treat historical GMRF fields as real-world evidence;
- interpret failure under this invalid interface as failure of the M4-v3 transport hypothesis.

M4-v3 remains two nested scientific questions:

1. **Transport mechanism:** does the source-agnostic characteristic propagator work with a correctly defined wind driver?
2. **Deployment observation:** does the same frozen propagator remain useful when that wind driver is estimated from sparse real measurements?

Uncertainty in the second stage should eventually be represented as `p(W | anemometer, map)`, not hidden inside source-conditioned transport weights.

## Current decision

- M4-v3 structural mechanism contract: unchanged, PASS.
- House02 D0: still blocked only by the exact canonical W2 dynamic sequence.
- Historical House02 GMRF field: **invalid as a verified deployment fixture** because both direction semantics and parameter compatibility are compromised.
- W0 becomes mandatory before any estimated-wind comparison.
- No change to the M4-v3 transport architecture is authorized from this audit.
