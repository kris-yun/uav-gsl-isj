# Mainline candidate — Persistent 3D Transport World Model for PMFS-compatible GSL

Date: 2026-10-01
Status: PRIMARY THEORY CANDIDATE / DEVELOPMENT ONLY
Execution order: finish R1P5 first; then run P3T-D0. No parallel closed-loop work.

## 1. Why PMFS historically compressed transport to 2-D

PMFS should not be criticized as if its 2-D design were an arbitrary mistake.

The original method had to solve an online source-inference problem under three simultaneous constraints:

1. Global wind was represented on a 2-D lattice. The upstream implementation stores the gas-hit map, source-probability map and estimated wind as Grid2D objects; the wind vectors are Vector2.
2. Candidate-conditioned dispersion was already expensive in 2-D. The PMFS paper therefore used coarse-to-fine candidate refinement instead of simulating every possible source at full spatial resolution.
3. The observation abstraction intentionally discarded exact concentration amplitude in favor of gas-hit probability, because source release strength and boundary conditions are uncertain and exact simulated amplitudes are not reliable enough for online matching.

Thus 2-D PMFS was a rational real-time and observability compromise for a mobile robot. It was not a physical claim that plume transport is intrinsically 2-D.

## 2. Why the old compromise is not sufficient for this UAV problem

Frozen project evidence now establishes:

- PMFS3D-O0: FULL3D versus a vertically projected 2-D GADEN counterfactual produced 4/4 larger source-discrimination margins; median gain was about 0.518.
- Earlier House02 checks found source-dependent vertical channels and horizontal divergence between free-3D and forced-fixed-height trajectories.
- Therefore the fixed-height 2-D state is not dynamically closed.
- PMFS3D-R1 restored xyz transport but retained a point-filament / hard-voxel hit observation rule.
- In R1, Oracle-2D and Oracle-3D true-source log scores were identical in all four cases, and the true template had zero support at confident observation cells. The 3-D gain therefore came from suppressing some false hypotheses, not from adding positive evidence at the truth.

The diagnosis is:

The missing state is 3-D, but simply adding a z coordinate to the old sparse hit simulator is not enough. The method needs a persistent, continuous and sparse 3-D transport state whose observation operator can be queried by a moving UAV.

## 3. What changed after PMFS

### 3.1 Same-domain enabling technology: Gaden-RT, SoftwareX 2025

Gaden-RT makes GADEN interactive and faster than real time. Gas filaments are represented as 3-D Gaussian distributions, and concentration can be queried only at requested sensor positions instead of constructing a dense 3-D concentration map everywhere.

This is not our novelty. It changes the engineering boundary that originally favored a low-dimensional online simulator.

Reference:
Pepe Ojeda, Javier Monroy, Javier Gonzalez-Jimenez,
"Gaden-RT: A real time and interactive gas dispersion simulator for mobile robotics",
SoftwareX 32, 2025, 102388.
Code: https://github.com/MAPIRlab/gaden_core

### 3.2 Main remote-domain parent: persistent 3-D world state, ICML 2026

PERSIST — "Beyond Pixel Histories: World Models with Persistent 3D State".

Its useful principle is that a partially observed dynamic world should not be represented only through a short history of projected observations. It keeps a persistent latent 3-D scene, evolves that state, and renders observations from it.

Transfer:
- image history -> sparse gas/wind observation history;
- camera pose -> UAV pose;
- persistent latent 3-D scene -> persistent latent 3-D gas/transport state;
- renderer -> olfactory observation operator.

Reference:
Garcin et al., ICML 2026, PMLR 306.
Code: https://github.com/francelico/PERSIST

### 3.3 Task-sufficient state compression, ICML 2026

"Learning Task-Sufficient World Models by Synergizing Agentic Exploration and Structured Modeling" identifies a second problem that matters directly here: generic high-dimensional latent states retain task-irrelevant factors, increasing cost and hurting generalization. It instead distills compact representations that are minimal and sufficient for the downstream task.

Transfer:
- full 3-D concentration reconstruction -> unnecessary target;
- source-discriminative hidden transport factors -> task-sufficient state;
- generic high-dimensional latent -> compact source-localization-sufficient latent;
- informative agent probing -> UAV measurements selected to expose unresolved transport factors.

This is the key answer to the objection that "going 3-D" simply restores an unaffordable high-dimensional state.

Reference:
Feng et al., "Learning Task-Sufficient World Models by Synergizing Agentic Exploration and Structured Modeling", ICML 2026, PMLR 306.

### 3.4 Structured-memory parent: Flow Equivariant World Models, ICML 2026

FloWM structures latent memory so it evolves consistently under self-motion and external dynamics rather than relearning those transformations from observations.

Transfer:
- self-motion -> UAV motion;
- external flow -> wind-driven plume motion;
- out-of-view dynamic state -> unobserved 3-D plume volume;
- equivariant memory -> persistent transport belief aligned over a moving trajectory.

Reference:
Lillemark et al., ICML 2026, PMLR 306.
Code: https://github.com/hlillemark/flowm

### 3.5 Physical sparse-volume parent: Lagrangian Gaussian fluid representations, SIGGRAPH 2026

LagrangianSplats and GauSmoke show that a physically structured 3-D fluid does not require a dense voxel tensor.

Useful principles:
- Lagrangian 3-D Gaussian primitives;
- continuous density/support;
- physically constrained velocity evolution;
- sparse representation of a dynamic volume;
- tractable long-horizon propagation.

References:
Tao, Chen, Chu, "LagrangianSplats: Divergence-Free Transport of Gaussian Primitives for Fluid Reconstruction", SIGGRAPH 2026, DOI 10.1145/3799902.3811188.
Code: https://github.com/taoningxiao/LagrangianSplats

Zhang et al., "GauSmoke: Hybrid Physics-Optical Gaussian Splatting for Sparse Smoke Reconstruction", SIGGRAPH 2026, DOI 10.1145/3799902.3811148.

These are parent representations, not odor-localization novelty claims.

## 4. Proposed main innovation

Working name:

TS-P3T-WM — Task-Sufficient Persistent 3-D Transport World Model for Probabilistic Gas Source Localization

Maintain an internal state:

Z_t = {G_t, V_t, O}

where G_t is a sparse set of 3-D Gaussian gas primitives, V_t is a 3-D transport/wind belief, and O is geometry/occupancy.

The method is not required to reconstruct the complete 3-D plume. A compact latent U_t = C(Z_t) should retain only transport factors needed to distinguish source hypotheses. The scientific requirement is source-localization sufficiency, not pixel/voxel reconstruction fidelity.

Dynamics:

Z_(t+1) = T(Z_t, V_t, O, source_hypothesis) + process_uncertainty

Observation at UAV pose pose_t:

p(y_t | source_hypothesis) = R_pose_t(Z_t)

The final exported map remains PMFS-compatible and 2-D. If source height is uncertain, marginalize it:

P_PMFS(x,y) = sum_z p(x,y,z | observations)

If source height is fixed, directly export p(x,y | observations).

The paper story is therefore not "PMFS was 2-D, so we make it 3-D."

It is:

PMFS compressed a partially observed 3-D transport process into a 2-D hit state for online tractability. Modern persistent world-state, task-sufficient compression, flow-equivariant memory and sparse Lagrangian Gaussian representations make it possible to retain the source-relevant hidden 3-D transport state without paying the cost of a dense 3-D plume, while still exposing a lightweight probabilistic source map.

## 5. One-main-two-auxiliary structure

Main innovation:
Task-sufficient persistent 3-D transport world model.
Parent theory: PERSIST plus Task-Sufficient World Models, ICML 2026.
Role: retain a persistent hidden 3-D state, but compress it to the minimal transport information sufficient for source discrimination. This directly addresses both the missing-3D-information problem and PMFS's original real-time motivation.

Auxiliary innovation A:
Flow-equivariant transport memory.
Parent theory: Flow Equivariant World Models, ICML 2026.
Role: make the hidden state evolve consistently with UAV self-motion and wind-driven external flow, preserving unobserved plume state rather than rebuilding it from each local measurement.

Auxiliary innovation B:
Physics-structured Lagrangian Gaussian gas state.
Parent theory: LagrangianSplats and GauSmoke, SIGGRAPH 2026; gas physics grounded by GADEN/Gaden-RT.
Role: represent continuous 3-D gas support sparsely and physically, avoiding a dense voxel plume while retaining vertical/path information.

Counterexample-guided elimination remains a conditional R1P5 mechanism branch, not one of the three core thesis modules. If R1P5 passes, it may later become a source-hypothesis pruning mechanism; if it fails, the main world-model thesis is unaffected.

## 6. Novelty boundary

Forbidden novelty claims:
- first 3-D odor/source search;
- first UAV 3-D odor localization;
- first filament/Lagrangian OSL;
- first Gaussian gas dispersion;
- first 3-D Gaussian fluid reconstruction;
- first world model;
- first use of gas non-detection/negative evidence.

The candidate contribution, only after experiments and a dedicated prior-art audit, is much narrower:

A persistent 3-D transport world state for probabilistic gas-source inference, using a sparse physically structured gas representation and projecting the hidden 3-D state back to a PMFS-compatible source posterior.

## 7. Why this is different from the failed M4/neural-operator line

M4 required a learned model to discover transport geometry from limited data and failed the intervention-geometry gate.

P3T-WM changes the representation first:
- 3-D state is explicit;
- persistence is explicit;
- advection is explicit;
- Gaussian support is continuous;
- geometry is explicit;
- physics can be enforced by construction.

Any learned component should estimate hidden state or residual uncertainty, not replace the whole transport law.

This is a better hypothesis for cross-environment transfer because transport and geometry, rather than House identity, carry the main inductive bias.

## 8. Frozen execution order

1. Finish R1P5 saved-score suppression audit.
2. Run P3T-D0 Gaussian-support kill test.
3. Only if D0 creates positive truth evidence, test persistent 3-D state across source updates.
4. Only after cross-environment source-rank signal, develop deployable sparse-wind inference.
5. Closed loop last.

No parallel expansion.
