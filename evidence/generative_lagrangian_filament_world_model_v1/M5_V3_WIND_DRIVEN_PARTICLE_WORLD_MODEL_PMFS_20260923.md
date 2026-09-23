# M5 V3 — Wind-Driven Particle World Model for PMFS

Date: 2026-09-23  
Branch: \`research/generative-lagrangian-filament-world-model-v1\`  
Status: **CURRENT TOP CONCEPTUAL MAIN-INNOVATION CANDIDATE — empirical L1/L2 pending**

## 1. Main paper-level idea

Working name:

**Wind-Driven Particle World Model for PMFS (WP-PMFS)**

The main scientific shift is:

> replace PMFS's hand-coded low-fidelity filament transition with a **source-agnostic Lagrangian particle world model** that uses known gas physics as an explicit predictor and learns only the unresolved high-fidelity correction.

The PMFS outer shell remains recognizable:

- candidate source space;
- source probability map;
- candidate-source forward simulation;
- closed-loop mobile sensing.

The internal forward engine changes from:

\[
\text{hand-coded 2-D random walk}
\]

to:

\[
\text{physics predictor}
+
\text{learned particle-world corrector}.
\]

---

## 2. 2026 remote-field mother idea — WorldParticle

Wang et al., *WorldParticle: Unified World Simulation of Lagrangian Particle Dynamics via Transformer*, SIGGRAPH Asia 2026 (conditionally accepted).

Core architecture:

1. shared Lagrangian particle representation;
2. explicit predictor advances particles using **known external forces**;
3. learned corrector predicts residual position/velocity updates;
4. particle tokenizer encodes:
   - particle-particle interaction;
   - particle-boundary interaction;
   - topology-guided interaction;
5. hierarchical super-token encoder/decoder;
6. generalization to unseen:
   - physical parameters;
   - boundary configurations;
   - initial conditions;
   - external-force configurations.

This is the primary 2026 mother idea.

The transfer is not to claim WorldParticle itself as ours.

The transfer is:

> **known physics should advance the particle first; learning should correct only the unresolved dynamics.**

---

## 3. Supporting remote-field lineage

### PhysCtrl — NeurIPS 2025

Generative physical dynamics represented as 3-D point trajectories and conditioned on physical parameters/forces.

Useful if the gas residual proves multimodal/stochastic.

### Synthetic Lagrangian Turbulence — Nature Machine Intelligence 2024

Diffusion models reproduce non-Gaussian/intermittent turbulent particle trajectory statistics.

Useful only if L1 proves a simple Gaussian corrector inadequate.

### DeepLag — NeurIPS 2024

Lagrangian particle dynamics can expose hidden fluid evolution efficiently and interpretably.

---

## 4. Exact PMFS limitation being replaced

Native PMFS:

\[
v_t=w_{2D}(X_t)+\epsilon_t
\]

\[
X_{t+\Delta}=X_t+\Delta v_t.
\]

with:
- 2-D wind;
- isotropic Gaussian perturbation;
- no buoyancy;
- no filament age/sigma state;
- obstacle path stops before a blocked cell.

Its own source notes that wall deflection would be preferable to stopping.

This is the forward-model object M5 replaces.

---

## 5. High-fidelity physical target

GADEN uses:

### Advection

\[
X^*
=
X_t+W_{3D}(X_t)\Delta t.
\]

### Buoyancy

A known gas-property / concentration-dependent vertical terminal velocity:

\[
X^{**}_z
=
X^*_z
+
v_{\rm buoyancy}\Delta t.
\]

### Stochastic displacement

Gaussian velocity perturbations in x/y/z.

### Boundary interaction

Obstacle crossing triggers recursive tangential rejection/projection rather than simply stopping.

### Filament growth

\[
\sigma_{t+\Delta}
=
\sigma_t
+
\frac{\gamma}{2\sigma_t}\Delta t.
\]

Thus the high-fidelity transition is a natural training teacher for the world-model correction.

---

## 6. Gas-specific prediction–correction architecture

### 6.1 State

Per filament:

\[
p_t=
(X_t,\sigma_t,\text{gas type}).
\]

Environment:

\[
E=(W,O).
\]

### 6.2 Explicit physical predictor

Compute all known/simple physics before learning:

\[
\tilde X_{t+\Delta}
=
X_t
+
W(X_t)\Delta t
+
v_{\rm buoyancy}(p_t)\Delta t.
\]

Analytic filament growth:

\[
\tilde\sigma_{t+\Delta}
=
\sigma_t
+
\frac{\gamma}{2\sigma_t}\Delta t.
\]

Optionally include the cheap Native-PMFS collision handling as the low-fidelity boundary predictor for the first ablation.

### 6.3 Learned corrector

Predict only:

\[
\Delta X_{\rm corr}
=
C_\theta(
p_t,
\tilde X_{t+\Delta},
W,
O,
\text{boundary context}
).
\]

Final:

\[
\boxed{
X_{t+\Delta}
=
\tilde X_{t+\Delta}
+
\Delta X_{\rm corr}
}
\]

or a conditional distribution over \(\Delta X_{\rm corr}\) if L1 demonstrates stochastic multimodality.

---

## 7. Important gas-specific departure from WorldParticle

Do **not** copy all WorldParticle branches mechanically.

GADEN filaments do not physically interact with one another in the current simulator.

Therefore initial gas corrector should emphasize:

- particle-boundary interaction;
- local wind/geometry interaction;
- optional global environment context.

Do not add particle-particle attention merely because WorldParticle has it.

### Particle-particle branch rule

Only introduce shared/global particle interaction if independent evidence shows:
- correlated residual transport;
- shared turbulent structures;
- real/high-fidelity data where filament independence is inadequate.

This pruning is part of the gas-specific derivation.

---

## 8. Boundary representation

Candidate options, ordered from simplest:

### A. Local SDF features
- wall distance;
- nearest-wall normal/direction;
- outlet state.

### B. Boundary tokens
Sample nearby occupied/boundary cells as particles/tokens.

This is closer to WorldParticle's particle-boundary branch.

### C. Exact constraint projection
After learned correction, project any invalid crossing using the known occupancy geometry.

Preferred final implementation should **never allow a generated filament to pass through a wall**.

---

## 9. Stochastic/generative corrector is conditional, not mandatory

M5 V3 separates the **world-model idea** from the **generative necessity**.

### If L1 says Gaussian sufficient

Use:

\[
\Delta X_{\rm corr}
\sim
\mathcal N(
\mu_\theta(z),
\Sigma_\theta(z)
).
\]

The main idea remains a physics-anchored particle world model.

### If L1 shows constraint-induced multimodality/non-Gaussianity

Upgrade only the corrector to:
- diffusion;
- flow matching;
- mixture density;
- other compact generative residual.

Do not use a generative model unless the data demands it.

This avoids overengineering.

---

## 10. Source-agnostic transport — core second innovation

The transport model never receives source ID/location after a filament is born.

Learn:

\[
P_\theta(
p_{t+\Delta}
\mid
p_t,W,O
).
\]

Candidate source \(s\) affects only birth:

\[
p_{birth}\sim Q_s.
\]

For a PMFS candidate region:

1. sample/inject filament births from that candidate region;
2. roll the same frozen world model;
3. convert generated filament cloud to candidate concentration/hit map.

Therefore one learned environment model evaluates **all PMFS candidates**, including source positions absent from training.

---

## 11. Why this addresses the dataset bottleneck

Field models learn:

\[
(S,W,O)\to C
\]

and need many source positions.

WP-PMFS learns:

\[
(X_t,\sigma_t,W,O)
\to
P(X_{t+\Delta}).
\]

One 1000-s GADEN realization contains many filaments and many transition observations.

Thus:
- few source positions can provide large local transport supervision;
- unseen source generalization follows from source-independent transport.

This is a structural data-efficiency advantage.

---

## 12. PMFS candidate-map reconstruction

For each generated filament:

- position;
- sigma/age.

Use the same physical concentration kernel / sensor conversion to construct:

\[
C_s(x)
\]

or PMFS-compatible:

\[
h_s(x).
\]

Do not let the learned model output source probability directly.

The PMFS probability-map inference layer remains visible and auditable.

---

## 13. First implementation hierarchy

### V3-A — deterministic residual corrector
Tiny boundary-aware MLP/operator.

Purpose:
- establish source-rank signal.

### V3-B — heteroscedastic stochastic corrector
Only if residual variance is context dependent.

### V3-C — generative corrector
Only if L1 proves non-Gaussian/multimodal residual structure.

This hierarchy prevents a sophisticated architecture from hiding a weak mechanism.

---

## 14. Hard falsification gates

### L1 — trajectory structure
Already specified in:
\`L1_GENERATIVE_NECESSITY_HARD_GATE_20260923.md\`.

### L2 — unseen-source counterfactual rollout

Train transport on current source realization.

Generate one new source in the same House.

Without retraining:

- inject at unseen source;
- roll transport world model;
- compare field/hit map to new GADEN realization.

Compare:
1. Native PMFS;
2. explicit physical correction;
3. learned world-model correction.

### L3 — PMFS candidate source rank

Freeze transport model.

For the PMFS candidate bank:
- generate candidate hit maps;
- use unchanged Native PMFS source update initially.

Hard endpoint:

**truth-containing candidate rank**.

### L4 — independent plume realization

Repeat with second stochastic realization.

### L5 — destructive physics nulls

- shuffle wind;
- shuffle boundary context;
- replace real SDF/normals with permuted geometry;
- use wrong source-injection location.

Gain must follow physical structure.

---

## 15. Key comparisons required for publication

### Against Native PMFS
Does the world model fix source-relevant forward mismatch?

### Against explicit GADEN-inspired hand correction
Could a simple wall-deflection/buoyancy patch explain the gain?

### Against generic field surrogate
Is source-agnostic Lagrangian modeling more data-efficient than a source-conditioned field network?

### Against deterministic corrector
Is stochastic/generative modeling actually necessary?

---

## 16. Novelty boundary

Do not claim:
- first particle simulator;
- first learned particle dynamics;
- first Lagrangian fluid network;
- first WorldParticle application in general;
- first generative trajectory model.

Current GSL novelty hypothesis:

> **a source-agnostic, wind-driven Lagrangian particle world model used as the candidate forward engine of PMFS, with explicit gas-physics prediction and learned high-fidelity residual correction, enabling counterfactual replay of arbitrary candidate sources.**

No direct GSL collision has been found so far.

---

## 17. Why V3 meets the requested “big idea” standard

The mother idea is a 2026 **particle world simulator**, not a new score.

The PMFS-specific reinterpretation is:

### Old PMFS
For every source candidate:
- run a hand-designed random filament simulator.

### V3
For every source candidate:
- perform an intervention on filament birth;
- roll one shared learned physical world model.

Wind is an explicit dynamical force.

Obstacles are explicit constraints/boundary tokens.

The learned component has a physically defined responsibility.

---

## 18. Current verdict

Scientific-theme strength: **very high**.  
Remote-field recency: **very high — SIGGRAPH Asia 2026**.  
PMFS identity preservation: **exceptionally high**.  
Data efficiency: **high in principle**.  
Direct GSL collision risk: **currently low**.  
Main empirical risk: **a simple explicit/heteroscedastic corrector may already be sufficient**.

Status:

\`TOP CONCEPTUAL CANDIDATE — RUN L1/L2 BEFORE FULL MODEL IMPLEMENTATION\`.
