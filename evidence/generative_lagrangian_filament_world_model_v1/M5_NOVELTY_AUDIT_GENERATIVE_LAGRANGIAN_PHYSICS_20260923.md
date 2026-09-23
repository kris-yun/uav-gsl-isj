# M5 Novelty Audit — Generative Lagrangian Physics vs GSL

Date: 2026-09-23  
Branch: \`research/generative-lagrangian-filament-world-model-v1\`

## 1. Remote-field scientific lineage

### Nature Machine Intelligence 2024 — generative Lagrangian turbulence

Li et al., *Synthetic Lagrangian turbulence by generative diffusion models*, Nature Machine Intelligence 6, 393–403 (2024).

Key result:
- learn distributions of 3-D single-particle turbulent trajectories with a diffusion model;
- reproduce non-Gaussian velocity-increment statistics;
- reproduce anomalous scaling/intermittency;
- generate extreme events beyond those seen during training while maintaining turbulence statistics.

This establishes that a generative model over Lagrangian trajectories can capture physically meaningful stochastic structure that simple Gaussian trajectory models miss.

Novelty implication:

M5 cannot claim:
- first generative Lagrangian turbulence model;
- first diffusion model over particle trajectories.

### NeurIPS 2025 — PhysCtrl

Wang et al., *PhysCtrl: Generative Physics for Controllable and Physics-Grounded Video Generation*, NeurIPS 2025.

Key result:
- physical dynamics represented as 3-D point trajectories;
- generative diffusion model conditioned on physics parameters and applied forces;
- particle-interaction-aware spatiotemporal modeling;
- explicit physical constraints.

Transferable principle:

> learn a conditional distribution over physically grounded point trajectories rather than one deterministic future.

### NeurIPS 2024 — DeepLag

Ma et al., *DeepLag: Discovering Deep Lagrangian Dynamics for Intuitive Fluid Prediction*, NeurIPS 2024.

Key result:
- expose hidden fluid dynamics via tracked Lagrangian particles;
- combine Eulerian field state and Lagrangian trajectory information;
- demonstrate 2-D/3-D and simulated/real fluid prediction.

Transferable principle:

> Lagrangian trajectories are an efficient/interpretable state representation for fluid dynamics, not merely a visualization.

### NeurIPS 2025 — direct Lagrangian flow-map learning

Boffi, Albergo & Vanden-Eijnden, *How to build a consistency model: Learning flow maps via self-distillation*, NeurIPS 2025.

Relevant principle:
- direct learning of flow maps;
- explicitly distinguishes Eulerian, Lagrangian and progressive formulations;
- Lagrangian flow-map training can avoid spatial derivatives and unstable short-step bootstrapping.

This can become an efficiency reference only after M5's stochastic-necessity gate passes.

## 2. Current GSL collision search

Targeted search terms included:
- gas/odor source localization + learned filament dynamics;
- generative particle plume;
- learned gas filament trajectories;
- neural stochastic plume particles;
- generative plume transport source inversion.

Nearest GSL literature found still uses:
- hand-designed filament/particle plume equations;
- Gaussian/random particle transport;
- particle filtering over source hypotheses;
- learned Eulerian concentration fields;
- RL/planning over simulated plume observations.

A 2026 indoor OSL paper, for example, still models plume particles by an explicit wind + Gaussian stochastic process + settling equation before particle-filter localization.

No direct work was found that does all of:

1. learn a **generative Lagrangian gas-transport law**;
2. condition that law on physical wind/obstacle context;
3. make it source-agnostic after injection;
4. use it as the PMFS-style candidate forward model for mobile source localization.

This is not proof of absence; final systematic audit remains required.

## 3. Defensible novelty boundary

Do NOT claim:

- first particle/filament plume model;
- first neural fluid particle model;
- first generative Lagrangian turbulence;
- first diffusion model for trajectories;
- first ML gas-dispersion model.

The candidate novelty is much narrower:

> **A source-agnostic, wind-referenced generative Lagrangian transport world model used to replace PMFS's hand-coded candidate filament dynamics, with source hypotheses entering only through the particle-injection intervention.**

The scientific distinction is the factorization:

\[
Q_s
\longrightarrow
P_\theta(
X_{t+\Delta}\mid X_t,W,O,\sigma
)
\longrightarrow
H_s
\longrightarrow
\pi(s).
\]

The learned transport mechanism is reusable across all candidate source hypotheses.

## 4. Why source-agnosticity is the central second innovation

Most learned gas-field models learn:

\[
(S,W,O)\rightarrow C.
\]

Source coverage is therefore a training-data bottleneck.

M5 learns:

\[
(X_t,W,O,\sigma)\rightarrow
P(X_{t+\Delta}).
\]

Source \(S\) is not an input to the transport law after birth.

This converts every filament transition from a small number of plume realizations into reusable transport supervision.

A previously unseen PMFS candidate source can be evaluated by:
- injecting filaments at that candidate;
- rolling the same frozen transport world model.

No source-coordinate interpolation is required.

## 5. Strongest scientific threat

GADEN's own microscopic update law is already known and includes:
- deterministic wind advection;
- deterministic obstacle handling;
- deterministic sigma growth;
- Gaussian positional stochasticity.

Therefore a network trained only to reproduce GADEN may add no scientific value.

M5 becomes main-worthy only if L1/L2 show:

1. aggregated/high-fidelity transport has reproducible context-dependent structure beyond PMFS's simple law;
2. a genuinely generative model beats a small heteroscedastic Gaussian model;
3. the source-agnostic model generalizes to a new source without retraining;
4. this improves truth-source candidate rank.

Otherwise:

\`M5 MAIN = NO-GO\`.

## 6. Current verdict

Novelty collision status:
\`OPEN IN GSL / STRONG REMOTE-FIELD PRIOR ART\`.

Scientific-main status:
\`KEEP — CONDITIONAL ON L1 GENERATIVE-NECESSITY SIGNAL\`.
