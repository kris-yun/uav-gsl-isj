# M4-v3 Real-World Deployment Contract

Date: 2026-09-23  
Branch: `research/m4-v3-interventional-evolution-propagator`  
Status: **HARD DESIGN CONSTRAINT — SIMULATION PASS ALONE IS INSUFFICIENT**

## 1. Purpose

M4-v3 is intended for eventual UAV flight, not only GADEN benchmark performance.

Therefore any M4-v3 design that requires information unavailable on the flying robot is rejected even if it performs well with simulator oracle inputs.

The simulator is used to isolate mechanism and obtain controlled counterfactual interventions. It is a prerequisite, not the final validation domain.

---

## 2. Information available at deployment

The deployable M4-v3 interface is restricted to information that can be available online:

- robot/UAV pose;
- occupancy/topology map from the mapping stack;
- local gas sensor observations;
- local wind observations from the onboard/near-body anemometer;
- a dense wind **estimate/belief** obtained from the existing GMRF-wind pipeline or an equivalent estimator;
- elapsed time / measurement timestamps;
- frozen model parameters.

Forbidden deployment inputs:

- GADEN ground-truth wind service;
- complete CFD/GADEN wind sequence known in advance;
- true source coordinates;
- future wind;
- true concentration field;
- hidden simulator filament state;
- target-environment concentration labels used for online fitting.

---

## 3. Two separate forward-input modes

### 3.1 Oracle-wind mode — mechanism diagnostic only

Use full GADEN wind fields to answer:

> Does the proposed characteristic propagator represent the intended transport mechanism when the transport driver is known?

This isolates model-form error.

A pass in oracle mode **cannot** establish deployability.

### 3.2 Estimated-wind mode — deployment gate

Run the same frozen propagator from the wind field produced by the same estimation interface intended for flight.

For the current PMFS stack this means the GMRF-wind estimate generated from local wind measurements.

This answers:

> Does the transport/source factorization remain useful after realistic wind observation and interpolation error?

The primary simulation claim must report oracle and estimated-wind results separately.

If the gain exists only with oracle wind:
**NO-GO FOR THE UAV MAIN METHOD.**

---

## 4. Gas-sensor observation contract

The core transport model may evolve a concentration-like latent field, but final source scoring must not require an unrealistically perfect calibrated ppm sensor.

PMFS already operates through a gas-hit probability abstraction. M4-v3 should preserve a deployment-compatible observation layer:

[
	ext{transport state} ightarrow 	ext{predicted observation statistic}
ightarrow p(y_tmid s).
]

Allowed first implementation:
- the same threshold/hit abstraction as PMFS, using one pre-calibrated detection threshold fixed before each experiment campaign.

Possible later auxiliary module:
- calibration-robust ordinal/rank observation likelihood.

The latter is not part of the M4-v3 main claim and must not be added merely to rescue failed transport experiments.

---

## 5. UAV-specific nuisance factors

These are real-world gates, not optional discussion items.

### R1 — rotor/downwash interaction

Before autonomous localization trials, characterize gas and wind readings with:
- motors off;
- hover;
- representative forward/sideways flight speeds.

The test must establish whether sensor placement produces systematic concentration attenuation, delay, or wind-vector bias.

No post-hoc per-trial correction is allowed.

### R2 — gas-sensor dynamics

Measure the sensor step/impulse response sufficiently to estimate:
- effective response time;
- recovery time;
- usable sampling rate;
- saturation / floor behavior.

The localization observation model must use timestamps and may use a fixed causal sensor-response filter if that filter is calibrated before localization trials.

### R3 — wind-sensor validity near the airframe

Compare onboard wind measurements with a reference sensor over a predeclared operating envelope.

If rotor flow overwhelms ambient wind at the chosen sensor location, the flight configuration is invalid for this method and must be redesigned physically rather than corrected using source truth.

### R4 — pose/time synchronization

Gas, wind, and pose must share synchronized timestamps.

A concentration or wind observation is associated with the UAV pose at the measurement's effective sensing time, including any predeclared sensor lag correction.

---

## 6. Geometry / dimensionality boundary

The current House02 C0.5 bank is a fixed sensor-height 2-D slice and is **development data only**.

It cannot by itself validate UAV deployment.

Before confirmatory simulation:
- choose the actual flight-height policy;
- reproduce the sensor/anemometer height(s) used by the UAV;
- if altitude variation is material, M4-v3 must use a 3-D or explicitly layered transport representation;
- if flight altitude is intentionally fixed, the claim must be restricted to that 2.5-D operating regime.

A 2-D model is not allowed to silently make a general 3-D UAV claim.

---

## 7. Compute/online constraint

Candidate-source forward evaluation must fit inside the localization update cycle on the intended onboard or companion computer.

Freeze and report:
- candidate count;
- grid size;
- number of internal transport steps;
- source-update latency;
- peak memory;
- hardware.

The model fails deployment if its required latency forces a fundamentally different search behavior from the PMFS baseline.

---

## 8. Sim-to-real evaluation ladder

### Stage S0 — mechanism development
House02, already opened.
Purpose: debug characteristic transport and intervention response only.

### Stage S1 — untouched GADEN confirmation
House01/House03 after architecture freeze.
Run both:
- oracle wind;
- estimated wind from the deployment-compatible wind-estimation pipeline.

### Stage S2 — hardware-in-the-loop
Real UAV/robot computation, sensing timestamps, ROS communication and navigation;
gas/plume may still be simulated or replayed.

Purpose: expose timing, compute, synchronization and interface failures.

### Stage R0 — stationary physical plume
Real gas source, real sensors, fixed robot/UAV measurement poses.
No autonomous search.

Purpose: validate observation likelihood and wind-estimation interface without navigation confounding.

### Stage R1 — controlled UAV flight
Predeclared trajectories through the plume.

Purpose: verify sensing under rotor/downwash and motion.

### Stage R2 — autonomous source localization
Frozen algorithm and parameters.
Compare against Native PMFS using the same platform, sensor suite, source, environment and trial protocol.

Primary physical endpoint:
- final source-location error at the frozen time/termination horizon.

Secondary:
- success rate under a frozen source-radius threshold;
- time/path length to first valid declaration;
- number of gas/wind measurements;
- compute latency;
- failure modes.

---

## 9. Real-world anti-cheating rules

- no source coordinate is available to the algorithm;
- no trial-specific threshold tuning after inspecting the result;
- no wind ground truth used by M4-v3 if it is unavailable to Native PMFS in that physical trial;
- no discarded failed flight unless a predeclared hardware/safety exclusion is triggered;
- failed localization trials remain in the denominator;
- trial ordering should be randomized or blocked to reduce systematic plume/environment drift;
- source positions are predeclared independently of method output;
- environmental conditions and source release settings are logged.

---

## 10. Main-innovation success boundary

The M4-v3 main innovation is not considered established by:
- lower GADEN field MSE;
- oracle-wind source rank alone;
- one successful physical flight.

The intended evidence chain is:

[
	ext{mechanism}
ightarrow
	ext{held-out inverse rank}
ightarrow
	ext{estimated-wind robustness}
ightarrow
	ext{hardware/ROS viability}
ightarrow
	ext{real UAV localization}.
]

If explicit characteristic transport improves the first two stages but collapses under estimated wind, the scientific mechanism may remain interesting but it is **not suitable as the UAV-GSL main method**.
