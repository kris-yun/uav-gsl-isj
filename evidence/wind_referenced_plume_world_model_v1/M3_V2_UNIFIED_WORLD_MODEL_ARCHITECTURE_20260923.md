# M3 v2 — Wind-Referenced Physics-Constrained Stochastic Plume World Model

Date: 2026-09-23  
Branch: \`research/wind-referenced-plume-world-model-v1\`  
Status: **current preferred architecture, pending W0.5 generation benchmark**

## 1. One scientific narrative

The paper should not read as “OFM + Curly-FM + PCFM.”

The unified scientific statement is:

> **A source hypothesis should predict a physically admissible distribution over stochastic plume worlds, not a single nominal hit map.**

Native PMFS:
\[
s \longrightarrow h_s(x).
\]

Proposed:
\[
s \longrightarrow
\mathcal P_\theta
\big(
\rho(\cdot,t)
\mid
s,w,O
\big)
\longrightarrow
p(y\mid s,x,t).
\]

Here:
- \(s\): source candidate;
- \(w(x,t)\): wind vector field;
- \(O(x)\): obstacle geometry;
- \(\rho(x,t)\): stochastic filament/gas density field;
- \(y\): robot gas hit/concentration observation.

The PMFS outer shell remains:
- candidate-source space;
- source probability map;
- source comparison;
- closed-loop mobile sensing.

The forward representation becomes a stochastic physics world model.

---

## 2. Main innovation — Operator-Flow Plume World Model

Parent: **Stochastic Process Learning via Operator Flow Matching**, NeurIPS 2025.

### Why it is the main module

The latent plume is a random field, not a deterministic image.

We model:

\[
\rho_s(\cdot,\cdot)
\sim
\mathcal P_\theta
(
\rho
\mid
q_s,w,O
),
\]

where \(q_s\) is a source-injection field for candidate \(s\).

Function-space modeling matters because the mobile robot observes only arbitrary sparse points:

\[
\{
(x_i,t_i,y_i)
\}_{i=1}^m.
\]

A stochastic operator can represent and query the joint field distribution at those points without tying the model to one fixed sensor grid.

### Physics-anchored base distribution

Do not start from an unrelated Gaussian image prior.

Use the PMFS/GADEN-low-fidelity process as the base/reference family:

\[
\rho^0_s
\sim
\mathcal P_{\rm PMFS}
(\rho\mid s,w,O).
\]

Then learn a conditional function-space transport:

\[
\boxed{
\rho^{HF}_s
=
T_\theta
(
\rho^0_s;
s,w,O,\xi
)
}
\]

that maps low-fidelity stochastic plume realizations toward the higher-fidelity GADEN plume distribution.

This makes PMFS the physical prior rather than discarding it.

---

## 3. Auxiliary innovation A — Wind-Referenced Non-Gradient Transport

Parent: **Curly Flow Matching for Learning Non-gradient Field Dynamics**, NeurIPS 2025.

### Physical problem

Indoor plume transport is not well described by a zero-drift / least-action generative path.

Obstacles and CFD wind create:
- recirculation;
- shear;
- vortical transport;
- curved/non-gradient trajectories.

### Transfer

Use known wind-driven transport as a non-zero reference process.

At physical time \(t\), the mean filament density obeys approximately

\[
\boxed{
\partial_t \rho
=
-\nabla\cdot(w\rho)
+
\nabla\cdot(D\nabla\rho)
+
q_s
-
\lambda\rho
+
r_\theta
}
\]

where:
- the first terms are known/reference transport;
- \(r_\theta\) represents unresolved turbulent/stochastic residual dynamics.

The model should learn deviations **around** wind physics, not rediscover the downwind direction from data.

### Critical notation discipline

Do not conflate:
- physical plume time \(t\);
- flow-matching generative time \(\tau\).

The world model learns a distribution over physical trajectories \(\rho(x,t)\).

The Curly-FM-inspired component determines how physical-time plume states/particle distributions are coupled/reference-drifted.

The OFM generative coordinate \(\tau\) remains an auxiliary sampling/training coordinate.

If only static plume fields are available and no reliable physical-time snapshots can be exported, this auxiliary is **HOLD**, not force-fitted.

---

## 4. Auxiliary innovation B — Hard Physics Projection During Generation

Parent: **Physics-Constrained Flow Matching: Sampling Generative Models with Hard Constraints**, NeurIPS 2025.

### Why this is different from PINN

PINN/PINO typically adds physics residuals as soft training penalties.

PCFM-style sampling projects/intervenes along the generative trajectory so final samples satisfy explicit constraints.

For generated plume state \(u\), define constraint residuals

\[
h(u;s,w,O)=0.
\]

The generator follows its learned flow while physics correction projects toward the constraint manifold.

### Candidate hard constraints

#### C1 — obstacle exclusion

For occupied cell \(i\),

\[
\rho_i=0.
\]

This can be exact.

#### C2 — wall no-through-flow

At solid boundaries:

\[
n\cdot
(
w\rho-D\nabla\rho
)=0.
\]

Use only where the GADEN/PMFS wall model is compatible with this approximation.

#### C3 — source support

Source injection is confined to the candidate source region:

\[
q(x)=0
\quad
x\notin S_s.
\]

#### C4 — global transport balance

For suitable snapshots/control volumes:

\[
\frac{d}{dt}
\int_\Omega\rho\,dx
=
Q_s
-
\int_{\partial\Omega}
(w\rho-D\nabla\rho)\cdot n\,dS
-
L.
\]

Do not enforce this until release/outflow/loss semantics are verified against GADEN.

### Inequality constraints

Nonnegativity is better enforced by parametrization:

\[
\rho=\operatorname{softplus}(z)
\]

rather than pretending it is an equality constraint.

---

## 5. Why this is not the 2024/2026 neural-GSL work

Existing learned GSL lines include:
- physics-guided NN source inversion;
- a publicly listed 2026 IROS physics-informed neural operator for turbulent gas-source localization.

Those make generic claims such as:
- source-conditioned learned dispersion;
- physics-informed surrogate;
- neural operator acceleration.

M3 only survives if experiments demonstrate the stronger distinction:

\[
\boxed{
\text{distribution over plume functions}
\neq
\text{one deterministic surrogate field}
}
\]

and the distributional component improves source identity on independent stochastic plume realizations.

Required comparison:

1. Native PMFS;
2. deterministic learned residual/operator;
3. stochastic world model;
4. stochastic world model + hard physics.

If 2 ≈ 3 in truth-source rank, the generative main claim fails.

---

## 6. Observation model

Do not force the physical PDE onto PMFS's heuristic source score.

Generate a physical latent field first.

At robot location \(x_t\), derive the observation law using a sensor model:

\[
p(y_t\mid\rho,x_t,\theta_{sensor}).
\]

For hit/miss:

\[
P(Y_t=1\mid\rho,x_t)
=
g_{\rm hit}(\rho(x_t)).
\]

Then source evidence is

\[
p(Y_{1:t}\mid s)
=
\int
p(Y_{1:t}\mid\rho)
\,d\mathcal P_\theta(\rho\mid s,w,O).
\]

This cleanly separates:
- plume physics;
- sensor response;
- source belief.

---

## 7. Why filament density is the right latent field

PMFS itself simulates stochastic filaments.

The empirical filament population converges conceptually toward an advection-diffusion/Fokker–Planck density.

Thus \(\rho\) is a bridge between:
- PMFS particle simulation;
- CFD/GADEN concentration;
- neural function-space world modeling.

It is more physically defensible than directly generating the final PMFS compatibility score.

---

## 8. Data-generation insight from GADEN-RT

MAPIRlab \`gaden_core\` exposes:

\`\`\`cpp
float Simulation::SampleConcentration(const Vector3& point) const;
Vector3 Simulation::SampleWind(const Vector3& point) const;
\`\`\`

and \`RunningSimulation\` defaults to:

\`\`\`cpp
bool saveResults = false;
\`\`\`

The GADEN documentation states that when result saving/compression is disabled, running simulation remains relatively cheap even at high filament counts.

The source object has a directly mutable:

\`\`\`cpp
Vector3 sourcePosition;
\`\`\`

Therefore a training dataset need not consist of massive saved GADEN files.

A practical generator can:

1. load one House environment/wind configuration once;
2. change source position;
3. run \`RunningSimulation\`;
4. sample a 2-D grid at robot sensor height at selected physical times;
5. save only those slices;
6. repeat for a small source design.

This makes W0.5 substantially more plausible.

---

## 9. W0.5 minimal generation benchmark

Do not train yet.

One House only, preferably House02.

### Source design

Use:
- existing true source;
- one new source in a different room/geometry region.

No truth-based choice for algorithm performance.

### Runtime

For each source:
- 60 s physical simulation first;
- two stochastic seeds if seed control is available;
- sample field every 5 s after warmup;
- begin with a coarse 2-D grid at sensor height.

Record:
- total wall time;
- time spent in simulation;
- time spent sampling concentration grid;
- peak RAM;
- output size.

### Decision

PASS if enough multi-source fields can be generated at practical cost to build a small 4–8-source-per-House pilot.

If grid sampling dominates runtime:
- coarsen training grid;
- sample random function points for OFM instead of dense grids;
- do not enable GADEN \`preCalculateConcentrations\` by default because upstream labels it much slower/larger.

---

## 10. First scientific falsification after W0.5

Before flow matching:

### F1 — source-conditioned residual structure

For each high-fidelity GADEN slice and low-fidelity PMFS realization:

\[
R_s(x,t)
=
\rho^{GADEN}_s(x,t)
-
\rho^{PMFS}_s(x,t).
\]

Test source-blind:
- residual spatial autocorrelation;
- cross-seed reproducibility;
- wind-aligned structure;
- obstacle-edge structure;
- low-dimensional energy;
- source-position interpolation.

Destructive null:
- spatially permute residual values;
- rotate/shuffle wind fields.

If real residuals are not more predictable than nulls, a learned residual world model is poorly motivated.

---

## 11. Module decision hierarchy

### Main
**Stochastic operator-flow plume world model**

Must beat deterministic learned forward models on source identity.

### Auxiliary A
**Wind-referenced non-gradient transport**

Only promoted if time-resolved GADEN fields show a measurable advantage over zero/straight generative coupling.

### Auxiliary B
**Hard physics-constrained generation**

Only promoted if it improves:
- held-out physical constraint satisfaction;
- cross-source/House generalization;
- source rank.

No auxiliary gets a paper contribution slot merely because it can be implemented.

---

## 12. Current status

Main candidate:
\`KEEP\`

Aux A, wind-referenced non-gradient dynamics:
\`KEEP / DATA-CONDITIONAL\`

Aux B, hard physics projection:
\`KEEP\`

Immediate next gate:
\`W0.5 GADEN MULTI-SOURCE GENERATION COST BENCHMARK\`
