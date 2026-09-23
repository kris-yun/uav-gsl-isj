# Candidate M5 — Generative Lagrangian Filament World Model

Date: 2026-09-23  
Branch: `research/generative-lagrangian-filament-world-model-v1`  
Status: **KEEP — second-tier main-thesis candidate pending direct data probe**

## 1. Mother idea

The candidate transfers recent **generative physics over particle trajectories** into PMFS-style gas-source localization.

The scientific shift is:

> learn a source-conditioned stochastic world model over **filament trajectories**, not over a static plume image.

PMFS already describes gas as moving filaments/particles. Instead of keeping their motion as a hand-designed random walk, learn a physically constrained distribution over their Lagrangian dynamics.

Working name:

**Generative Lagrangian Filament World Model (GLF-WM)**

## 2. Remote-field parent ideas

### P1 — PhysCtrl, NeurIPS 2025
Wang et al., *PhysCtrl: Generative Physics for Controllable and Physics-Grounded Video Generation*, NeurIPS 2025.

Key transferable idea:
- represent physical dynamics as 3-D point trajectories;
- learn a generative distribution over physically plausible trajectories;
- condition on physical parameters and applied forces;
- impose interaction/physics constraints during training.

This is from generative video/physics, not GSL.

### P2 — Lagrangian generative turbulence
Modern generative turbulence models synthesize stochastic Lagrangian particle trajectories rather than only Eulerian fields.

Transfer:
- intermittency and trajectory statistics are first-class objects;
- stochastic path distribution matters, not merely mean velocity.

### P3 — Lagrangian flow-map learning, NeurIPS 2025
Recent flow-map work identifies Lagrangian training formulations as a stable way to learn continuous flow maps.

This is relevant to efficient trajectory propagation, but is not itself a GSL novelty.

## 3. PMFS-native interface

Native PMFS:

[
X_{k+1}^{(j)}
=
X_k^{(j)}
+
Delta t
[
w(X_k^{(j)})+epsilon_k^{(j)}
]
]

for filament (j), plus source births and obstacle handling.

GLF-WM replaces only the unresolved filament transition law:

[
X_{k+1}^{(j)}
sim
P_	heta(
cdot
mid
X_k^{(j)},
w,
O,
s,
	ext{local plume state}
).
]

Source candidate (s) determines filament injection.

Wind (w) is physical drift/force.

Obstacle geometry (O) determines admissible motion/boundary interaction.

The generated particle cloud is converted back into PMFS-compatible concentration/hit maps.

Thus the PMFS outer shell remains:
- candidate source;
- source probability map;
- candidate forward field;
- closed-loop localization.

## 4. Why this is not just “learn the PMFS simulator”

The main hypothesis is:

> PMFS's Gaussian random-walk filament motion is too restrictive to represent intermittent, obstacle-induced, multimodal plume transport; a conditional generative trajectory model can learn the unresolved **distribution of Lagrangian transport paths** while retaining wind and boundary physics.

The model must predict:
- multimodal trajectory futures;
- recirculation;
- obstacle deflection;
- spatially varying stochastic dispersion;
- plume intermittency.

If it only predicts the mean next particle position, this candidate collapses into an ordinary neural surrogate and should be demoted.

## 5. Physical decomposition

Preferred form:

[
dX_t
=
w(X_t,t),dt
+
b_{m wall}(X_t,O),dt
+
r_	heta(X_t,mathcal N_t,s,w,O,t),dt
+
Sigma_	heta^{1/2}dW_t.
]

where:

- (w): known/measured wind reference drift;
- (b_{m wall}): obstacle / no-through-wall mechanism;
- (r_	heta): learned unresolved turbulent drift;
- (Sigma_	heta): learned stochastic dispersion;
- (mathcal N_t): optional local particle-neighborhood state.

Wind must not be merely concatenated as a feature if the final architecture supports reference-drift integration.

## 6. Particle-to-PMFS map

Generated filaments are not the final inference object.

For measurement cell (x), derive concentration / hit probability from the generated particle ensemble using the same or a calibrated PMFS/GADEN sensor kernel:

[
H_s(x)
=
mathcal K(
{X_t^{(j)},sigma_t^{(j)}}_{j}
).
]

Then source inference continues on the PMFS candidate map.

## 7. Why this may be easier than M3 dense-field OFM

GADEN core directly exposes:

- `RunningSimulation::GetFilaments()`;
- `SampleWind()`;
- source position;
- obstacle/environment configuration.

Therefore M5 supervision can use native particle states directly.

It does not require storing dense concentration grids at every time.

This may drastically reduce:
- storage;
- field sampling cost;
- output dimensionality.

## 8. Direct GSL prior-art boundary

Already known:
- hand-designed filament/particle plume models are standard in olfactory search;
- neural networks have been used to predict concentration fields;
- generative networks have been used for 3-D plume reconstruction from sensing;
- PINN/PINO gas forward models exist.

Do NOT claim:
- first particle plume model;
- first neural gas-dispersion model;
- first generative gas plume model in general.

Current novelty hypothesis is narrower:

> source-conditioned **generative Lagrangian filament dynamics** integrated as the candidate forward world model in PMFS-style source localization.

A final literature audit is mandatory.

## 9. Minimal data gate — L0

Before training:

For one GADEN source realization, export filament states at fixed times:

- filament ID if persistent/available;
- position;
- sigma/radius;
- source birth time or age if available;
- local wind;
- obstacle relation.

Determine whether trajectories can be associated across time.

### Critical fork

If GADEN filament IDs / ordering permit tracking:

train path transitions directly.

If not:

learn set-to-set / empirical transition distributions rather than inventing correspondence.

Do not fake particle identity.

## 10. Tiny falsification — L1 transition residual

Use existing GADEN filament trajectories.

Compute the native PMFS/GADEN-style baseline prediction:

[
hat X_{t+Delta}^{0}
=
X_t+Delta t,w(X_t).
]

Residual:

[
R_t
=
X_{t+Delta}-hat X_{t+Delta}^{0}.
]

Before any neural model test:

- conditional mean structure;
- conditional covariance;
- multimodality;
- obstacle dependence;
- wind-direction dependence;
- spatial heteroscedasticity;
- temporal correlation.

Destructive null:
shuffle residuals across positions/wind/obstacle context.

If real residuals are not more structured than nulls, kill M5.

## 11. L2 tiny generative transition model

Only if L1 is positive.

Fit a minimal conditional stochastic model for one-step filament transitions.

Compare against:
1. native Gaussian random walk;
2. heteroscedastic Gaussian residual;
3. genuinely generative/multimodal residual model.

Metrics:
- held-out transition NLL;
- Wasserstein/energy distance;
- recirculation-region path statistics;
- downstream hit-map error.

Hard downstream gate:

**truth-containing source-candidate rank** after replacing Native PMFS transition generation in frozen replay.

If the generative model improves trajectory fit but not source identity, kill as main.

## 12. L3 stochastic necessity

The generative/multimodal model must beat a simpler heteroscedastic Gaussian residual.

Otherwise “generative world model” is unnecessary.

## 13. Cross-source / cross-House test

Train without the held-out source / environment.

Required:
- source-conditioned generalization;
- cross-House transfer or adaptation;
- no House-specific truth tuning.

## 14. Destructive nulls

- wind shuffle;
- obstacle/context shuffle;
- source label shuffle;
- residual spatial permutation;
- destroy filament temporal ordering.

The source-rank gain must disappear under relevant nulls.

## 15. Comparison to M3 and M4

### M3 — stochastic field world model
Object learned:
- random Eulerian plume field.

Best when:
- joint field uncertainty is the central missing representation.

### M4 — causal compositional world model
Object learned:
- reusable causal mechanisms / interventions.

Best when:
- unseen source×wind×House combinations are the central challenge.

### M5 — generative Lagrangian filament world model
Object learned:
- stochastic particle/filament trajectory law.

Best when:
- unresolved transport dynamics are strongly structured at the particle level.

Do not merge until each mechanism has independent evidence.

## 16. Kill conditions

NO-GO as main if:

1. no reliable filament trajectory correspondence/data;
2. residual dynamics are essentially Gaussian/unstructured;
3. a simple heteroscedastic random walk performs as well;
4. trajectory gains do not improve source rank;
5. direct prior art already uses equivalent learned generative filament dynamics for GSL;
6. gains require truth-tuned House-specific parameters;
7. the method degenerates into a deterministic next-position network.

## 17. Current verdict

Mother-idea strength: **high**.  
Physical fit to PMFS: **exceptionally high**.  
Direct novelty risk: **moderate** because particle learning is established outside GSL.  
Data feasibility: **potentially better than M3 because GADEN exposes filaments directly**.  
Scientific-theme strength relative to M4: **lower**, unless L1 reveals strong non-Gaussian transport structure that materially affects source identity.

Status:

`KEEP — SECOND-TIER MAIN CANDIDATE / STRONG POSSIBLE AUXILIARY`.
