# M6 Theory Audit — Why GeoPT Pretraining Is Physically Aligned with PMFS Filament Transport

Date: 2026-09-23  
Branch: \`research/geopt-physics-foundation-pmfs-v1\`

## Decision

\`PRETRAINING-TASK ALIGNMENT = POSITIVE\`

The argument for M6 is stronger than a superficial input-feature match.

GeoPT's self-supervised pretext task explicitly learns **geometry–velocity interaction along moving point trajectories**, which is structurally aligned with filament transport through obstacle-rich wind fields.

## 1. What GeoPT pretraining actually learns

GeoPT does not pretrain only on static shape reconstruction.

Its lifted pretraining samples:

- geometry \(G\);
- spatial query points \(x\), including volume and boundary points;
- synthetic per-point velocity:
  \[
  v\sim Uniform(B_C).
  \]

It evolves the point according to a geometry-constrained dynamics:

\[
\frac{dx_t}{dt}
=
v(x_t,t)\,1_G(x_t)
\]

and supervises the model to predict the trajectory of geometric features:

\[
h_G(x_{0:\tau}).
\]

Thus the pretraining signal asks:

> How does a moving point, driven by a velocity condition, interact with local geometry/boundaries over a trajectory?

This is the dynamics-lifted component that distinguishes GeoPT from static geometry pretraining.

## 2. Structural alignment to PMFS/GADEN

### GeoPT pretext object
- moving point;
- velocity/dynamics prompt;
- geometry/boundary;
- trajectory-conditioned geometry features.

### Gas filament object
- moving filament center;
- wind vector field;
- walls/obstacles/outlets;
- transport trajectory and subsequent concentration/hit field.

The mapping is not exact physics, but the representation problem is highly aligned:

\[
(point,\ velocity,\ geometry)
\quad\leftrightarrow\quad
(filament,\ wind,\ indoor\ obstacles).
\]

## 3. Why this matters relative to Native PMFS

Native PMFS handles obstacle interaction with a simplified stop-before-wall rule.

Its own source code notes that a more physical wall deflection would be desirable.

GADEN instead uses a recursive tangential deflection.

GeoPT pretraining exposes the model to large-scale synthetic supervision where velocity-driven point trajectories interact with boundaries.

Therefore the pretrained representation may already encode useful features for:
- wall distance;
- boundary orientation;
- velocity–normal relation;
- constrained transport direction.

These are exactly the features that a gas-specific model trained from scarce plume data would otherwise need to learn from scratch.

## 4. What GeoPT does NOT give us

Do not overclaim.

GeoPT synthetic dynamics does not directly pretrain:
- advection-diffusion PDE solutions;
- gas concentration;
- filament birth/death;
- plume intermittency;
- buoyancy;
- source injection;
- stochastic turbulence.

Those remain gas-specific adaptation targets.

Thus the scientific hypothesis is not:

> GeoPT already knows gas physics.

It is:

> GeoPT supplies a reusable geometry–dynamics interaction representation, reducing how much gas-specific data is required to learn plume transport around obstacles.

## 5. Stronger M6 architecture interpretation

Environment representation:

\[
E_{\rm env}
=
E_{\rm GeoPT}
(
x,\ d_{\rm wall},n_{\rm wall},W
).
\]

Candidate source enters only through a small source-injection adapter:

\[
z_s=A_s(x-s,Q_s).
\]

Gas-specific decoder:

\[
\hat C_s
=
D_{\rm gas}(E_{\rm env},z_s).
\]

Therefore:

- pretrained backbone = general geometry–dynamics prior;
- source adapter = PMFS candidate intervention;
- gas decoder = small task-specific mapping.

## 6. Key ablation implied by this interpretation

G1/G2 must compare:

1. full GeoPT dynamics-lifted pretraining;
2. random initialization;
3. where possible, geometry-only/static-pretraining control.

If dynamics-lifted pretraining does not outperform geometry-only or random initialization under low gas-data budgets, the central M6 transfer story fails.

## 7. Mechanism-specific prediction

The strongest transfer advantage should occur:
- near walls/obstacles;
- where wind direction is oblique to boundaries;
- around openings/corridors;
- in low-data source conditions.

In open unobstructed regions, random/from-scratch models may catch up quickly.

This gives a source-blind subgroup test for G1/G2.

## 8. Current M6 verdict

The previous concern:

> “the checkpoint loads, but maybe its learned knowledge is semantically unrelated”

is reduced.

GeoPT's pretraining task is directly about **velocity-conditioned moving points interacting with geometry**.

Status:

\`M6 LEAD — STRONG PHYSICAL PRETEXT ALIGNMENT; EMPIRICAL TRANSFER STILL REQUIRED\`.
