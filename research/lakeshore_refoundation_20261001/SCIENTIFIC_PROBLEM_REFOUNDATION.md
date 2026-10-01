# Complex Lakeshore Gas Leakage — Scientific Problem Refoundation

Date: 2026-10-01
Status: conceptual refoundation after supervisor feedback; no experiment authorized yet.

## 1. Scenario first

The target scene is a lakeshore / waterfront industrial or facility area with:

- an unknown gas leak source s* = (x_s, y_s, z_s), possibly with an unknown release rate q(t);
- terrain, shoreline, buildings, vegetation and obstacles E(x);
- a time-varying meteorological field M_t including wind, thermal and turbulence variables;
- a hidden gas plume concentration field C(x,t);
- a team of UAVs at positions p_i(t), each observing only local gas / wind / pose information.

The scientific task is no longer only "find s*".

It is to infer and track the coupled state

    X_t = {source, plume state, meteorological forcing, uncertainty}

and use X_t to deploy multiple UAVs dynamically.

## 2. Required outputs

The system must output quantities that can be used by the next stage:

### Source outputs
- source location posterior P(s | O_1:t);
- estimated source position s_hat;
- optional source-strength estimate q_hat(t);
- localization uncertainty / credible source region.

### Current plume-state outputs
- concentration field or compact concentration representation;
- plume centroid mu_C(t);
- plume principal spread / covariance Sigma_C(t);
- centerline / dominant transport direction;
- effective plume region Omega_theta(t) = {x : C(x,t) >= theta};
- plume boundary partial Omega_theta(t);
- patch / connected-component state for intermittent plume structure;
- plume advection velocity v_C(t).

### Forecast outputs
For a short horizon tau:
- C_hat(x,t+tau);
- Omega_hat_theta(t+tau);
- centroid / boundary / front forecast;
- uncertainty of the forecast.

### Swarm-deployment outputs
- target sampling density rho_t(x);
- key monitoring points / roles;
- UAV-to-role allocation;
- safe trajectories under collision, energy and no-fly constraints.

## 3. Meteorological drivers

The primary physical drivers to model are:

1. 3-D wind speed and direction — dominant advection direction and travel rate;
2. vertical and horizontal wind shear — height-dependent transport;
3. turbulence intensity / eddy diffusivity — plume width, patchiness and mixing;
4. atmospheric stability / vertical temperature structure — vertical mixing / buoyancy;
5. lake-land thermal contrast — lake-breeze onset, front and wind-direction change;
6. boundary-layer height — vertical mixing envelope;
7. local roughness / obstacles / shoreline geometry — wakes, channeling and recirculation.

Ambient temperature, humidity and pressure may also enter the sensor / gas-response model,
but they should not be conflated with the core transport state unless the data show a load-bearing effect.

## 4. Three scientific questions

### Q1 — Source–plume joint observability under sparse mobile sensing

How can sparse, local, moving UAV observations distinguish:

- where the source is,
- what the current plume state is,
- and which changes are caused by meteorological transport rather than by source location?

This is a coupled inverse problem. Source location is a static / slow latent variable;
plume morphology is dynamic; meteorology is an exogenous driver.

### Q2 — Meteorology-conditioned plume evolution and short-horizon forecasting

How can the system forecast plume center, shape, boundary and concentration changes
under changing lake-breeze / wind / turbulence conditions without reconstructing a
computationally prohibitive dense 3-D CFD field online?

The desired state is compact, task-sufficient and physically interpretable.

### Q3 — Multi-UAV cooperative tracking of a deforming plume

How should multiple UAVs re-deploy as the plume center, boundary and forecast front move?

The objective is not simply "all robots move toward the source".
The team must jointly maintain source localization and plume situational awareness.

## 5. Main thesis

Proposed scientific thesis:

> Complex lakeshore gas localization should be formulated as a
> meteorology-driven source–plume world-state estimation problem, in which
> a compact persistent plume state is jointly inferred with the source and
> then used as the common information state for multi-UAV dynamic monitoring.

This replaces the old thesis:

> improve the PMFS source score.

PMFS remains:
- an important baseline;
- a possible source-posterior output interface;
- a component to compare against.

It is no longer the conceptual center of the dissertation.

## 6. Evidence boundary from previous experiments

Previous project evidence must constrain, not dictate, the new design:

- learned dense / monolithic plume models did not generalize reliably;
- deterministic 3-D physics already explained much predictable short-step transport;
- 3-D transport carried strong false-source discrimination but did not automatically restore truth evidence;
- Gaussian support did not solve source-evidence mismatch by itself;
- therefore the next method should not be another unconstrained field predictor or another PMFS score patch.

The new method must explicitly separate:
- static source state;
- dynamic plume state;
- meteorological forcing;
- observation model;
- multi-UAV action / sensing policy.
