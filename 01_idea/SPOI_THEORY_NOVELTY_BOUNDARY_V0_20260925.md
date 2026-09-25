# SPOI Theory and Novelty Boundary V0 — 2026-09-25

## Working name

**Sparse-Observation Stochastic Plume Operator Inversion (SPOI)**

## Mother theory

Park, Zhou, Kim & Barati Farimani, ICML 2026, *Generative Neural Operators through Diffusion Last Layer*.

DLL represents a conditional random field using an input-conditioned functional basis and a conditional coefficient distribution:

C(x,t) ~= mu_a(x,t) + sum_k xi_k phi_k(a)(x,t),

xi ~ p_theta(xi | a).

For GSL the operator input a is not an RNG seed. It is physical candidate context:

a_s = {source cell s, map/occupancy, wind field, release/sensor metadata}.

The intrinsic stochasticity is represented in the latent coefficient law rather than requiring an observed random forcing coordinate.

## GSL second-order adaptation

The forward stochastic model is:

p_theta(C | a_s).

A UAV does not observe the whole field. Let H_T be the observation operator induced by the robot's sampled locations/times.

y_T = H_T C + eta.

Source likelihood:

L_s(y_T) = E_{C ~ p_theta(C|a_s)} [ p_eta(y_T - H_T C) ].

PMFS posterior update:

P(S=s | y_T) proportional to P(S=s) L_s(y_T).

This preserves PMFS as a source-location probability map.

## Why the stochastic law is scientifically relevant

A deterministic surrogate approximates only a point/mean plume and treats realization variability as residual error.

D1R shows that this variability is source-dependent and reproducible as a statistical property. Under sparse observations, the shape of p(C|a_s), not only its mean, can change how candidate sources explain the same sensor evidence.

## Novelty exclusions

Not novel:
- neural operators;
- DLL itself;
- plume surrogates;
- probabilistic GSL;
- deep source posterior classifiers;
- heteroscedastic diagonal Gaussian field prediction;
- PMFS/Bayesian source maps.

Candidate novelty bundle:
1. source-conditioned correlated stochastic plume operator rather than deterministic plume surrogate;
2. sparse observation operator applied to the random function law;
3. explicit likelihood inversion over PMFS candidate sources;
4. transport context from wind + geometry, enabling candidate laws without candidate-specific real releases;
5. source-heldout and eventually cross-House/wind tests where stochastic structure must improve proper probabilistic source inference.

## Critical overlap with 2026 DGSE-S

DGSE-S learns inverse conditionals from sparse observations and uses diagonal Gaussian wind/concentration field uncertainty before outputting a source posterior.

SPOI must remain a forward generative observation model:

source/wind/map -> correlated plume distribution -> sparse observation likelihood -> Bayesian source posterior.

If implementation collapses into direct p(S|observations,map,wind) prediction, it loses the claimed distinction.

## Sim-to-real requirement

Offline simulation may teach the stochastic operator.

Real flight may use map, wind and a limited calibration layer, but the method is unacceptable if every new environment requires exhaustive repeated releases from every candidate source.

## Current status

HOLD pending an existing-asset transport-context D1. No new plume generation is authorized.