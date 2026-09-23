# CURRENT LEAD DECISION — Parallel Main-Innovation Search

Date: 2026-09-23  
Branch: `research/main-innovation-search-parallel-v1`

## Current priority

### #1 — M6 Dynamics-Lifted Physics Foundation PMFS
**Status: LEAD FEASIBILITY + NOVELTY CANDIDATE**

Why it moved to #1:
- ICML 2026 physics-foundation mother idea;
- official pretrained checkpoint exists;
- official volume representation matches indoor geometry unusually well;
- geometry + SDF + boundary direction + dynamics prompt map naturally to House + wind;
- predicted >99.9% backbone parameter reuse;
- House PMFS token count is tiny relative to target mesh scale;
- 2026 DGSE-S does NOT use a pretrained physics foundation representation or a candidate-source forward simulator.

Immediate gate:
- actual G0.5 checkpoint load + frozen House02 forward;
- then low-data transfer curve versus same architecture from scratch.

Scientific claim under test:

> a dynamics-lifted pretrained physics representation can serve as the environmental transport backbone for PMFS candidate-source forward inference under scarce high-fidelity plume supervision.

Gas-specific second innovation:
- source-injection adapter that changes candidate source while preserving pretrained environment representation.

### #2 — M4 Causal Compositional Plume World Model
**Status: HIGH-RISK/HIGH-NARRATIVE CANDIDATE**

Why it remains:
- strongest “world model / causal intervention” paper story;
- source intervention is easy to generate with current GADEN tooling;
- candidate source naturally corresponds to `do(S=s)`.

Why it is now harder:
- historical causal gas models exist;
- 2025 causal source attribution exists;
- 2026 DGSE-S explicitly uses physical dependency structure wind→concentration→source.

M4 now survives ONLY if:
- source/wind/geometry are reusable mechanisms;
- unseen source×wind recombination beats matched monolithic baseline;
- module swaps behave physically;
- source-rank improves.

Immediate gate:
- C0 House02 4-source intervention pilot;
- then real wind-intervention availability audit.

### #3 — M3 Physics-Anchored Stochastic Plume World Model
**Status: HOLD / SECOND-LINE**

Why demoted:
- 2026 DGSE-S already provides probabilistic wind/concentration/source fields;
- gas-PINO near-neighbor exists;
- M3 only remains novel if it models genuine joint stochastic function-space structure beyond independent per-cell Gaussian uncertainty.

Required gate before serious implementation:
- stochastic model must beat:
  1. Native PMFS;
  2. deterministic residual operator;
  3. diagonal-Gaussian task-specific field model.

### #4 — M5 Generative Lagrangian Filament World Model
**Status: STRONG AUXILIARY / BACKUP MAIN**

Advantages:
- exceptional physical fit to PMFS/GADEN;
- direct filament supervision available.

Main-theme risk:
- learned particle dynamics is broad prior art outside GSL;
- must prove non-Gaussian/multimodal trajectory structure is source-critical.

## Parallel execution order

### Track M6
1. G0.5 actual checkpoint load.
2. Frozen House forward.
3. Tiny low-data adapter.
4. Pretrained vs from-scratch scaling curve.
5. Truth-source rank replay.

### Track M4
1. 3-D validate preregistered House02 source interventions.
2. Generate 4 sources × 2 plume seeds.
3. Small monolithic vs compositional model.
4. Held-out source intervention.
5. Wind intervention / source×wind recombination only if source-only C0 is positive.

## Promotion rule

No candidate becomes the paper main innovation on elegance alone.

Promotion requires:
- novelty survives latest 2026 GSL literature;
- interface works;
- source-blind mechanism signal;
- truth-source rank positive;
- independent realization;
- destructive null.

## Current statement

If forced to allocate compute **today**:

- first compute dollar/hour: **M6 G0.5/G1**;
- second: **M4 C0 intervention pilot**;
- do not train M3 OFM yet;
- do not build M5 large generative dynamics yet.
