# M5 Architecture Discipline — WorldParticle Main, Stochastic Particle Models Conditional

Date: 2026-09-23  
Branch: \`research/generative-lagrangian-filament-world-model-v1\`

## 1. Primary mother idea

Use **WorldParticle (SIGGRAPH Asia 2026)** as the primary 2026 world-model parent.

Transfer only the high-level physical architecture:

\[
\text{explicit known-physics predictor}
\rightarrow
\text{learned Lagrangian residual corrector}.
\]

Gas-specific predictor:
- wind advection;
- buoyancy when retained;
- sigma growth;
- known source-independent physics.

Gas-specific corrector:
- particle-boundary interaction;
- unresolved high-fidelity transport residual;
- stochasticity only if data requires it.

## 2. Do not copy WorldParticle blindly

WorldParticle models many interacting physical systems.

Current GADEN filaments do not exert particle-particle forces.

Therefore initial PMFS transfer should **remove** unnecessary:
- particle-particle interaction branches;
- material/topology branches irrelevant to gas;
- global hierarchy if local correction is already sufficient.

A smaller corrector is scientifically preferable if it passes source-rank gates.

## 3. Conditional stochastic parent

**Latent Particle World Models (LPWM), ICLR 2026 Oral** is relevant only if L1 demonstrates a stochastic/multimodal residual that a conditional Gaussian cannot model.

LPWM's transferable idea:
- stochastic particle dynamics as a world-model state;
- conditional future distributions rather than one deterministic rollout.

But LPWM is object-centric video/world-model work, not gas physics.

Do not use LPWM to justify a stochastic network before L1.

## 4. Conditional generative-physics parents

Likewise:

- PhysCtrl, NeurIPS 2025;
- Synthetic Lagrangian Turbulence, Nature Machine Intelligence 2024;

become implementation/theory parents only after a \`GENERATIVE_NEEDED\` result.

## 5. Model-complexity ladder

Freeze this order:

### Tier 0
Native PMFS.

### Tier 1
Explicit high-fidelity physics corrections:
- wall deflection;
- 3-D drift/buoyancy as appropriate.

### Tier 2
Small deterministic learned residual corrector.

### Tier 3
Context-conditioned heteroscedastic Gaussian corrector.

### Tier 4
Generative/stochastic particle corrector.

A higher tier is allowed only if the lower tier fails on an independent realization.

## 6. Scientific narrative

The main paper does not need the word “generative” if the evidence does not support it.

The robust main narrative is:

> **A source-agnostic Lagrangian particle world model replaces PMFS's hand-designed candidate transport, combining explicit wind-driven prediction with a learned high-fidelity correction.**

Generative stochastic dynamics is an evidence-triggered extension, not the definition of the method.

## 7. Reason

This discipline preserves:
- physical interpretability;
- PMFS identity;
- causal responsibility of each module;
- falsifiability.

It prevents the paper from becoming a stack of fashionable 2025–2026 models without evidence.

Status:
\`FROZEN ARCHITECTURE ESCALATION RULE\`.
