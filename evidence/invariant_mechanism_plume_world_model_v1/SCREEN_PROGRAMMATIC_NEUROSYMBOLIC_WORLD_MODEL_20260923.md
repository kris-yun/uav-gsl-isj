# SCREEN — Programmatic / Neuro-Symbolic World Models

Date: 2026-09-23
Branch: \`research/invariant-mechanism-plume-world-model-v1\`
Decision: **NO-GO as a separate main innovation**

## Candidates screened

### PoE-World — NeurIPS 2025

Piriyakulkij et al., *PoE-World: Compositional World Modeling with Products of Programmatic Experts*.

Main idea:
- synthesize stochastic world-model experts as source code/programs;
- combine them using an exponentially weighted product of experts;
- learn useful world models from few observations;
- demonstrated on Atari/non-gridworld planning.

### Neurosymbolic World Models — ICML 2025

Hernandez Cano et al., *Neurosymbolic World Models for Sequential Decision Making*.

Main idea:
- synthesize finite-state-machine world models from low-level observations;
- use them in model-based RL / planning.

### Physically interpretable world-model principles — NeuS 2025

Peper et al., *Four Principles for Physically Interpretable World Models*.

Principles:
- organize latent variables by physical roles;
- align invariant/equivariant representations;
- exploit mixed-strength supervision;
- partition generated outputs for scalability/verifiability.

## Why PoE/FSM is not a good GSL main line

### 1. Programmatic-expert composition risks collapsing into prior-art multi-model plume inference

Gas/odor source localization already has:
- 2015 likelihood-free localization using multiple dispersion models;
- 2025 “many wrong models” odor-source localization using a bank of misspecified plume models and belief fusion.

If we synthesize several executable plume programs and combine them, the paper-level scientific story becomes too close to:
“use multiple alternative forward models to be robust.”

The program synthesis mechanism is newer, but the GSL scientific object is not sufficiently new.

### 2. FSM abstraction is poorly matched to the physical state

Indoor plume transport depends on:
- continuous vector wind;
- continuous concentration/density fields;
- obstacle boundaries;
- spatial gradients and fluxes.

Compressing the world to a small discrete-state machine would discard precisely the physical structure the user wants the method to preserve.

### 3. LLM/program synthesis adds an unnecessary failure mode

For this project:
- physical mechanisms are already known enough to name explicitly;
- source injection/advection/diffusion/boundary have mathematical forms;
- asking an LLM to rediscover these programs is not data- or physics-efficient.

It would weaken rather than strengthen physical defensibility.

## What is useful for M4

The 2025 physically interpretable world-model principles support M4's representation choices:

1. **functional physical organization**
   - source/advection/diffusion/boundary/residual mechanisms have explicit semantic roles;

2. **invariance/equivariance**
   - aligns with M4 Aux A contextual wind/wall symmetries;

3. **mixed supervision**
   - analytic physics + GADEN fields + sparse robot observations can provide different supervision strengths;

4. **partitioned/verifiable outputs**
   - mechanism-specific diagnostics and physical audits are possible.

These are conceptual supports, not additional claimed contributions.

## Decision

Do not create a “programmatic plume world model” branch.

Status:

\`NO_GO_AS_MAIN — USE PHYSICALLY INTERPRETABLE WORLD-MODEL PRINCIPLES AS M4 SUPPORT ONLY\`.
