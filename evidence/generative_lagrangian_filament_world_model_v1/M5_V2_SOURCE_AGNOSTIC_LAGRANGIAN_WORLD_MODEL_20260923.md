# M5 v2 — Source-Agnostic Generative Lagrangian Transport World Model

Date: 2026-09-23  
Branch: \`research/generative-lagrangian-filament-world-model-v1\`  
Status: **PROMOTED — PARALLEL LEAD WITH M6**

## 1. Key structural insight

The original M5 card described a source-conditioned generative filament simulator.

A stronger formulation is available:

> **learn the transport law independently of source identity.**

Once a filament is emitted, its motion depends on:
- current position;
- wind;
- obstacle/boundary geometry;
- filament age/sigma;
- gas physical properties;
- unresolved stochastic transport;

but not on the source label itself.

Therefore learn:

\[
\boxed{
P_\theta
(
X_{t+\Delta},\sigma_{t+\Delta}
\mid
X_t,\sigma_t,W,O,\text{gas physics}
)
}
\]

as a reusable **environment transport world model**.

Candidate source \(s\) enters only through the injection/birth mechanism:

\[
X_{t_{\rm birth}}
\sim
Q_s.
\]

Then roll the same learned transport model for every PMFS candidate.

## 2. Why this matters for data efficiency

Eulerian field surrogates typically learn:

\[
(S,W,O)\rightarrow C.
\]

They need plume labels spanning many source positions.

The Lagrangian model learns:

\[
(X_t,W,O)\rightarrow X_{t+\Delta}.
\]

A single plume realization contains thousands/millions of local transition samples at many spatial locations.

Thus:

> one or a few source realizations can provide large supervision for the **source-independent transport mechanism**.

This directly addresses the current project-data limitation of only one high-fidelity source position per House.

## 3. Counterfactual source reuse

For any unseen PMFS candidate source \(s'\):

1. instantiate new filament births at \(s'\);
2. use the same learned environment transport law;
3. generate a stochastic particle cloud;
4. map particles to PMFS-compatible hit probability;
5. score/update candidate source probability.

The new source does not require retraining the transport model.

This is a much stronger generalization mechanism than source-coordinate interpolation in a monolithic field network.

## 4. Remote-field mother ideas

### PhysCtrl — NeurIPS 2025
Generative physics over distributions of 3-D point trajectories conditioned on physics parameters and forces.

Transfer:
- particle trajectory is the generative object;
- wind acts like a force/reference drift;
- stochastic physical futures are generated rather than regressed to one mean.

### DeepLag — NeurIPS 2024
Lagrangian–Eulerian fluid prediction:
- expose hidden fluid dynamics through tracked particles;
- use Lagrangian motion as an interpretable dynamic representation.

M5 combines:
- DeepLag's Lagrangian physical representation;
- PhysCtrl's generative trajectory modeling;
- PMFS/GADEN filament physics.

## 5. Gas-specific second derivation

Do not ask the network to learn known advection from zero.

Use a wind-referenced residual:

\[
\Delta X_t
=
W(X_t)\Delta t
+
R_\theta(
X_t,\sigma_t,W,O,\xi
).
\]

Equivalently:

\[
X_{t+\Delta}
=
X_t+
W(X_t)\Delta t+
R_\theta(\cdot).
\]

The generative residual must model only:
- local turbulent deviation;
- 3-D buoyancy/effective vertical motion when relevant;
- obstacle-induced deflection/recirculation;
- heteroscedastic stochasticity.

Wind is therefore a **reference drift**, not a feature token.

## 6. Hard wall constraint

Do not allow generated trajectories to pass through obstacles.

Use one of:

1. GADEN-consistent geometric projection / StepTowards;
2. constrained generative trajectory projection;
3. no-through-wall manifold/constraint layer.

A soft obstacle loss alone is not sufficient for the final method if exact projection is practical.

## 7. PMFS shell

Retain:

- candidate source quadtree/regions;
- source-probability map;
- online measured hit map;
- movement logic initially unchanged.

Replace candidate forward simulation:

### Native PMFS
hand-coded 2-D filament random walk.

### M5-v2
source birth + learned source-agnostic stochastic 3-D/2.5-D transport world model.

This is a direct next-generation PMFS forward mechanism.

## 8. Why existing source coverage is less problematic

Current high-fidelity data:
- one source per House;
- two independent plume realizations.

For an Eulerian source-conditioned model this is inadequate.

For M5-v2 it may be sufficient for an **L1 local-transition test** because every realization yields many filament transitions.

New source positions are required only for:
- out-of-source rollout validation;
- downstream source-rank proof.

They are not required to estimate the local transport law itself.

## 9. L1 revised hard gate

### Training source
Use one GADEN realization.

### Held-out stochasticity
Use the second realization from the same source/House.

### Models

A. Native PMFS transition law.

B. Simple heteroscedastic Gaussian residual:
\[
R\sim\mathcal N(\mu_\phi(context),\Sigma_\phi(context)).
\]

C. Generative/multimodal trajectory residual inspired by PhysCtrl/flow/diffusion.

### Required result
C must beat B on held-out trajectory distribution metrics.

If B is enough, a full generative-physics model is unnecessary.

## 10. L2 unseen-source rollout gate

Generate **one new GADEN source position** in the same House.

Do not retrain.

For the unseen source:

- inject particles at the new source;
- roll A/B/C transport models;
- construct sensor-height hit/concentration field;
- compare to the new GADEN realization.

This is the central source-agnostic generalization test.

## 11. L3 PMFS source-identity gate

Use multiple candidate sources including the held-out true source.

Generate candidate hit maps from the frozen transport model.

Use the same PMFS inference/update rule initially.

Primary outcome:

**truth-containing source-candidate rank.**

The learned transport law must improve over Native PMFS.

## 12. Scientific kill conditions

M5-v2 is NO-GO as the main idea if:

1. held-out GADEN residuals are adequately Gaussian/Markov with a simple local model;
2. the generative model does not beat a simple heteroscedastic Gaussian;
3. source-agnostic rollout fails at an unseen source;
4. downstream source rank does not improve;
5. direct GSL prior art already uses learned generative Lagrangian filament dynamics;
6. the result is only a faster replica of known GADEN without better localization/generalization.

## 13. Current priority

M5 is promoted from second-tier to:

\`PARALLEL LEAD WITH M6\`

because it now has:
- a 2025 NeurIPS mother idea;
- exceptionally strong PMFS physical fit;
- a proven recoverable trajectory data interface;
- source-independent local supervision;
- natural unseen-source generalization by construction;
- no obvious direct GSL collision found so far.

The single biggest scientific risk remains:

> Is the high-fidelity local transport distribution complex enough that a generative trajectory model adds value over simpler stochastic dynamics?
