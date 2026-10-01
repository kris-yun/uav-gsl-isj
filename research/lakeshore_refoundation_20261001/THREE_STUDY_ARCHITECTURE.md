# Three-study architecture — source, plume, swarm

Date: 2026-10-01
Status: design candidate for supervisor discussion.

## Study 1 — Main paper
### Task-Sufficient Source–Plume World Model for Lakeshore Gas Localization

#### Problem
Sparse UAV measurements cannot directly observe the full plume, yet source location and
current plume morphology are coupled through meteorological transport.

#### Starting methods to improve

1. **Learning Task-Sufficient World Models**, ICML 2026:
   learn minimal, task-specific, sufficient hidden states instead of a huge generic latent state.

2. **PERSIST: Beyond Pixel Histories — World Models with Persistent 3D State**, ICML 2026:
   maintain a persistent hidden 3-D world rather than rebuilding the scene from a short observation history.

3. **Flow Equivariant World Models**, ICML 2026:
   hidden memory should evolve consistently with self-motion and external dynamics.

#### Scene-specific second innovation

Define a structured hidden state

    Z_t = { z_source, z_plume, z_meteo }

where:
- z_source is static / slowly varying;
- z_plume is persistent and dynamic;
- z_meteo is exogenous forcing.

Dynamics:

    z_plume(t+1) = F_theta(z_plume(t), z_meteo(t), E, q_t)
    y_i(t) = G_phi(z_plume(t), p_i(t), sensor_i)

Inference jointly estimates:

    p(s, z_plume(t) | O_1:t)

The latent state is not trained to reconstruct every CFD voxel.
It is optimized to preserve only quantities needed for:
- source localization;
- plume-shape estimation;
- short-term forecast;
- UAV deployment.

#### Main outputs
- source posterior;
- current plume compact state;
- plume uncertainty.

#### Role of PMFS
PMFS is a baseline and optional probability-map head, not the method being locally patched.

---

## Study 2 — Plume morphology and meteorology-conditioned forecasting
### Meteorology-Conditioned Compact Plume Operator

#### Problem
The supervisor explicitly asks for:
- shape;
- diffusion path;
- concentration change;
- morphology change;
- meteorological drivers;
- prediction output.

#### Starting methods to improve

1. **Gaussian Particle Operator (GPO)**, ICML 2026:
   compact, interpretable Gaussian basis with centers, anisotropic scales and weights;
   resolution-agnostic and suitable for irregular / 3-D domains.

2. **Origo: Neural Operator Splitting**, ICML 2026:
   decomposes PDE evolution into a global operator and sparse local constitutive mechanisms.

3. Optional geometry-generalization support:
   **Operator Learning with Domain Decomposition for Geometry Generalization**, ICLR 2026.

#### Scene-specific second innovation

Use a compact plume basis

    Z_plume(t) = {mu_k, Sigma_k, w_k}_{k=1..K}

but do NOT use it merely as a smoother for PMFS.

Split plume evolution into:

    global meteorological transport
    +
    local lakeshore / obstacle correction.

A practical decomposition is:

    Z_{t+1} =
      T_global(Z_t ; wind, stability, lake-breeze state)
      +
      R_local(Z_t ; shoreline, obstacles, roughness)

where the global branch captures advection / large-scale spreading and the local branch
captures wakes, channeling and recirculation around terrain / structures.

#### Forecasted quantities

- C_hat(x,t+tau);
- plume centroid;
- covariance / principal axes;
- effective threshold region;
- plume front / boundary;
- uncertainty.

The core scientific question is whether this compact state predicts the task-relevant plume
geometry across unseen meteorological conditions / geometries better than dense field surrogates.

---

## Study 3 — Multi-UAV dynamic plume tracking and monitoring
### Forecast-Guided Cooperative Plume State Tracking

#### Problem
As the plume deforms, a single UAV cannot simultaneously:
- preserve source information;
- observe the centerline;
- track plume boundaries;
- probe the forecast front;
- monitor meteorological uncertainty.

#### Starting methods to improve

1. **SniffySquad**, ACM TOSN 2026:
   patchiness-aware active sensing and collaborative role adaptation for multi-robot gas source localization.

2. Distribution-aware multi-UAV coverage / informative path planning:
   use modern distributed ergodic / information-targeted coverage as a coordination template.

#### Scene-specific second innovation

Roles are no longer only "source seeking".

At every update, construct a target sensing distribution

    rho_t(x) =
      w_s U_source(x)
      + w_b U_boundary(x)
      + w_f U_forecast_front(x)
      + w_m U_meteorology(x)

and dynamically assign UAVs to four functional regions:

- source/upwind sentinel;
- plume-center / centerline tracker;
- boundary / high-gradient tracker;
- forecast-front / uncertainty scout.

As the plume changes shape, rho_t changes and roles are reallocated.

#### Output and evaluation

Outputs:
- UAV role assignment;
- trajectories;
- real-time source / plume state.

Metrics:
- source localization error;
- plume boundary Hausdorff / IoU;
- centroid error;
- forecast error;
- uncertainty coverage;
- redundant sampling;
- mission time / energy;
- collision / safety violations.

This study can be the main closed-loop simulation + real-flight validation study.
