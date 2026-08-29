# PF-DEI single-source methodological derivation — Assimilative Causal Inference (ACI)

Date: 2026-08-29
Status: NON-NORMATIVE DERIVATION / DO NOT INTERRUPT CURRENT H01 INFORMATION AUDIT

## 1. Single methodological source

Use one explicit distant-field methodological source:

Andreou, M., Chen, N. & Bollt, E. **Assimilative causal inference.** Nature Communications 17, 1854 (2026). Published 22 January 2026. DOI: 10.1038/s41467-026-68568-0.

ACI was developed for complex stochastic dynamical systems, with emphasis on time-evolving causal relationships, intermittency, turbulence and climate/geophysical applications. Its central idea is to formulate causal inference as an inverse problem: use a governing dynamical model and Bayesian data assimilation to trace hidden causes backward from observed effects, rather than estimating only forward influence.

No other distant-field paper is treated as the conceptual origin of the method in this derivation.

## 2. Mapping ACI to robotic gas-source localization

ACI abstraction:

- hidden/potential cause: dynamical variable or state whose uncertainty is to be reduced;
- observed effect: partial stochastic time series;
- governing model: stochastic dynamical system;
- inference: forecast -> assimilation/analysis -> posterior uncertainty reduction.

GSL mapping:

- target cause `S`: persistent planar source carrier region;
- latent source placement `U`: unresolved 3-D placement inside carrier;
- latent transport state `Z_t`: plume transport realization/state;
- physical concentration `C_t` at robot pose;
- persistent sensor state `R_t`;
- observed effect `M_t`: measured ppm available causally to PMFS;
- governing model: native GADEN + parity-proven persistent sensor model.

Causal generative graph:

`S -> U -> Z_t -> C_t -> R_t -> M_t`, with trajectory/wind/environment as observed conditioning variables.

The localization task is therefore an inverse-causal assimilation problem: infer the persistent source cause from the dynamically generated measured effects.

## 3. State-space formulation

Let `K_t` denote source-independent known context up to time t: robot pose, timestamps, wind, map/geometry and sensing markers.

Static variables:

- `S ~ q0(S)`;
- `U ~ p(U | S, geometry)`.

Dynamic latent variables:

`Z_{t+1} ~ p_Z(Z_{t+1} | Z_t, S, U, K_t)`

`C_t = G(S,U,Z_t,K_t)`

`R_{t+1} ~ p_R(R_{t+1} | R_t,C_t,K_t)`

`M_t ~ p_M(M_t | R_t,K_t)`.

For the frozen simulator benchmark, the transition/observation laws are represented by native seeded GADEN and the parity-proven sensor implementation rather than an invented analytic surrogate.

## 4. Forecast-analysis recursion

Define latent nuisance state `Xi_t = (U,Z_t,R_t)`.

Forecast before assimilating the new observation:

`p_t^F(S,Xi_t) = integral p(Xi_t | Xi_{t-1},S,K_t) p_{t-1}^A(S,Xi_{t-1}) dXi_{t-1}`.

Analysis after observing measured ppm `M_t`:

`p_t^A(S,Xi_t) proportional p(M_t | Xi_t,K_t) p_t^F(S,Xi_t)`.

Source posterior:

`q_t(S) = integral p_t^A(S,Xi_t) dXi_t`.

This is the key temporal contract: the posterior at t is not a product of independent contexts. Transport and sensor state are propagated in chronology and each observation is assimilated only after the forecast state at that time has been formed.

## 5. Explicit assimilative causal evidence

ACI's causal interpretation is uncertainty reduction in a potential cause induced by observations of its effects. Adapt this directly to the source variable.

Forecast source distribution:

`q_t^F(S) = integral p_t^F(S,Xi_t) dXi_t`.

Analysis source distribution:

`q_t^A(S) = q_t(S)`.

Define instantaneous assimilative source-causal information:

`I_t = D_KL(q_t^A(S) || q_t^F(S))`.

`I_t >= 0` quantifies how much the newly observed gas effect changes information about the hidden source cause. It is a diagnostic/information quantity, not an empirical accept/reject gate.

For candidate-wise interpretation define the predictive log-evidence increment:

`Delta_t(s) = log p(M_t | M_{1:t-1}, S=s, K_{1:t}) - log p(M_t | M_{1:t-1}, K_{1:t})`.

Then the source posterior obeys the sequential evidence form

`q_t(s) proportional q_{t-1}(s) exp(Delta_t(s))`.

This makes the causal and temporal meanings explicit simultaneously: `Delta_t(s)` is evidence about a persistent candidate cause supplied by the next effect in chronological order.

## 6. Why temporal order is intrinsic, not a TCN naming trick

Temporal order does not come from calling a convolution "causal". It comes from the physical state recursion itself:

- plume state at t depends on its earlier transport history;
- sensor state at t depends on earlier concentration exposure;
- the forecast distribution at t depends on the previous analysis distribution;
- the next observation updates that forecast.

Therefore shuffling the measured sequence while keeping timestamps/trajectory fixed must change the assimilated source evidence. A time-shuffle negative control is mandatory for any final implementation.

## 7. Training-free implementation should be tested before neural amortization

The current V3 physical bank supplies coherent trajectories indexed by source carrier and joint nuisance member. If the ongoing model-free H01 audit shows strong source separability, the first implementation to test should be an ensemble assimilative source filter, not a new neural network.

Represent each nuisance member as a coherent whole-run particle attached to a source candidate. Maintain joint source/member weights through chronological observations and marginalize members to obtain `q_t(S)`.

The exact finite-ensemble observation/predictive density approximation must be calibrated using simulator-only held-out nuisance realizations before historical localization outcomes are opened. Do not introduce a temperature or bandwidth tuned from localization performance.

If a training-free assimilative filter is sufficiently discriminative and stable, it should be preferred because it requires no House-specific or real-room neural retraining.

## 8. Neural model, if required, is only an amortized assimilation operator

If the physical audit proves source information exists but a training-free finite-ensemble approximation is insufficient, a neural model may be used only to amortize the same assimilative quantity:

`Delta_psi(D_{1:t}, s, P_s) ~= predictive source log-evidence increment / cumulative ratio`.

The network is not the conceptual innovation. It must preserve:

- source-conditioned physics predictive ensemble;
- member-level temporal coherence;
- chronological causal prefix;
- one shared set of weights across environments;
- no House ID or source truth;
- new environment = new source-independent physics bank, not new neural retraining.

## 9. Proposed innovation statement

Working method name:

**Assimilative Causal Spatiotemporal Source Inference (ACSI)**

Chinese: **同化式因果时空源推断**.

Core contribution statement:

> Robotic gas-source localization is reformulated from local observation scoring into an assimilative inverse-causal problem. A persistent source region is treated as the hidden cause, while turbulent 3-D transport and run-persistent sensor dynamics generate a temporally ordered sequence of observable effects. A physics-based forecast-analysis recursion assimilates these effects online and marginalizes unresolved source placement and transport nuisance to recover source belief.

The novelty is not "TCN for GSL". The novelty is transferring the 2026 ACI paradigm of tracing hidden causes backward from observed effects through a stochastic dynamical model into robotic gas-source localization, with the specific source/transport/sensor factorization required by GSL.

## 10. Falsification contract implied by this derivation

Before claiming the innovation:

1. model-free physical source-information audit must beat a permutation/null baseline on held-out transport/placement realizations;
2. chronological order must outperform/order-sensitive relative to an outcome-independent shuffle control;
3. source/member permutation must preserve semantics;
4. removing the persistent sensor-state propagation must measurably alter the assimilation path where sensor memory is known to matter;
5. held-out-environment validation must use environment physics at inference but no environment-specific neural retraining if a neural amortizer is used;
6. final claim still requires frozen closed-loop OFF/ON localization improvement, not only source-ranking diagnostics.

## 11. Current decision rule

Do not activate a new model from this derivation while the H01 source-information audit is running.

- If held-out physics separability is strong: prioritize training-free ACSI / ensemble data assimilation.
- If physics separability is significant but insufficient: use one shared neural amortizer of ACSI evidence, not a House-specific source classifier.
- If held-out physics separability is near null: stop neural rescue and revisit the physical predictive family.
