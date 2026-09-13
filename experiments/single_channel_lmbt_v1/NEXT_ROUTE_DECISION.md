# Next-route decision: where a defensible causal contribution can still come from

## Decision

Keep exact sensor-lag correction as mandatory observation preprocessing. Retire LMBT mean backward transport as a main mechanism. Do not try another posterior-only, covariance-only, or passive backward-trajectory module on the same trace.

Under the present restrictions—one gas channel, no source shutoff, no source-response library, no second receiver, and no deployable full-flow field—a purely passive causal source-localization claim is not identified by the available observations. More optimization cannot create the missing intervention or independent information.

## The remaining causal route

The scientifically distinct route is **Coded Receptor Intervention (CRI)**: impose a known, weak, time-varying intake pattern at the sensor inlet while the UAV continues flying and the leak continues normally.

In plain language, the leak is never touched. A pump or valve at the detector alternates the intake according to a known code. Because the code is chosen by us and is independent of the plume, the measured component synchronized with that code reveals the detector's current gas intake; the unsynchronized slow component estimates sensor carryover. This turns sensor memory from an unknown nuisance into an experimentally separable state.

A minimal state model is

\[
x_{k+1}=a x_k+b\,u_k c_k+\epsilon_k,\qquad y_k=x_k+\eta_k,
\]

where `c_k` is ambient gas at the flying sensor, `x_k` is the detector's internal memory, and `u_k` is the known intake code. The intervention is on the receptor path `u_k -> x_{k+1}`; it does not intervene on the factory leak or assume knowledge of the gas source.

The second-order innovation would be a joint module:

1. design a short hardware-feasible intake code under pump/valve and sampling-rate limits;
2. estimate current intake and carryover from the coded response;
3. attach the demodulated current-intake event to the correct UAV pose;
4. feed the corrected one-channel evidence to the same PMFS support and planner.

This is a measurement-algorithm co-design contribution. It should not be described as a generic causal regularizer.

## Why this is a distant-field transfer rather than a name change

- Robotic olfaction work treats active airflow and sensor timing/hysteresis as part of the inference system rather than as fixed noise.
- Coded sensing in computational imaging designs a known temporal excitation under hardware constraints so that latent signal components become identifiable.
- Lock-in measurement and system identification recover the response synchronized with a controlled excitation while rejecting uncorrelated drift.

The transferable principle is **create an exogenous temporal tag at the receptor, then use that tag to identify the observation dynamics**. CRI adapts that principle to a moving one-channel gas detector with an uncontrolled, continuously emitting source.

## Fair comparison with classic PMFS

The acquisition protocol must be separated from the estimator comparison. A defensible experiment includes:

| Arm | Acquisition | Estimator | Purpose |
|---|---|---|---|
| A0 | ordinary intake | classic PMFS | historical benchmark |
| A1 | coded intake | classic PMFS without demodulation | controls for extra hardware/data collection |
| A2 | coded intake | PMFS with lag correction only | isolates timing correction |
| A3 | coded intake | CRI-demodulated PMFS | tests the proposed mechanism |

All coded-stream arms receive exactly the same raw one-channel measurements and trajectory. The new method must beat A1 and A2; beating only A0 would not distinguish the algorithm from the changed acquisition.

## Gate before implementation

CRI is viable only if the detector exposes a controllable intake pump/valve, or a small external inlet modulator can be mounted without changing the sensing chemistry. The switching period must be faster than plume-scale variation but slow enough for a measurable detector response. These are device facts, not tunable algorithm choices.

If no such intake control exists, the causal main-innovation route should be closed. The honest paper direction would then be sensor-memory-aware observation correction plus robust noncausal source localization, and it would need a different main contribution.

## Smallest decisive next experiment

Before any flight or multiseed run, replay the same H03 seed11 concentration history through the frozen first-order sensor model with a preregistered binary intake code. Compare A1/A2/A3 on recovery of the known instantaneous concentration and pose assignment. Only if CRI beats both matched controls should it enter a single H03 closed-loop run.

This simulated gate tests the observation-identifiability premise. It cannot validate the real device until the intake actuator and timing interface are confirmed.

