# Priority Update — WorldParticle Makes M5 the Top Conceptual Candidate

Date: 2026-09-23  
Branch: `research/main-innovation-search-parallel-v1`

## Current active leaders

### M5 V3 — Wind-Driven Particle World Model for PMFS
**Conceptual rank: #1**

2026 mother idea:
- WorldParticle, SIGGRAPH Asia 2026;
- explicit known-force predictor + learned particle residual corrector;
- unified Lagrangian world simulation;
- generalization to unseen external forces and boundary configurations.

PMFS transfer:
- wind + known gas physics = explicit predictor;
- wall/3-D/high-fidelity transport residual = learned corrector;
- source candidate = filament injection intervention;
- one frozen source-agnostic transport world model serves all PMFS candidates.

Why it currently leads conceptually:
- very recent remote-field big idea;
- changes PMFS's internal world representation, not its score;
- wind has an explicit dynamical role;
- obstacles have explicit boundary role;
- source-agnostic transition supervision avoids the multi-source field-data bottleneck;
- source-code audit establishes a real PMFS↔GADEN physics gap.

Hard gate:
- L1 must determine whether learned correction adds value beyond explicit/simple stochastic corrections;
- L2 must generalize to a new source without retraining;
- L3 must improve truth-source candidate rank.

Branch:
`research/generative-lagrangian-filament-world-model-v1`

Current defining file:
`M5_V3_WIND_DRIVEN_PARTICLE_WORLD_MODEL_PMFS_20260923.md`

### M6 — Dynamics-Lifted Physics Foundation PMFS
**Practical/pretraining rank: #1, conceptual rank: #2**

2026 mother idea:
- GeoPT, ICML 2026;
- geometry + synthetic dynamics self-supervision;
- cross-physics foundation representation;
- 20–60% reported labeled-data reduction on published tasks.

PMFS transfer:
- indoor volume geometry + SDF + wall direction;
- local wind dynamics prompt;
- small source-injection adapter;
- candidate field prediction.

Strong positive evidence:
- official input semantics align unusually well;
- real House token/runtime G0.5-A passed;
- GeoPT pretext task itself trains velocity-driven points interacting with geometry.

Pending:
- actual checkpoint load G0.5-B on Codex/VM;
- G1 pretrained-vs-random-vs-scratch low-data transfer.

## Secondary candidates

### M3 — stochastic field world model
Strong but data-heavy and closer to existing gas PINO.

### M4 — causal compositional world model
HOLD after matched-capacity historical pre-screen showed no clear advantage.

## Search discipline

Do not merge M5 and M6 yet.

They test distinct hypotheses:

- M5:
  **Is the correct scientific state a reusable Lagrangian transport world model?**

- M6:
  **Can broad geometry–dynamics pretraining reduce gas-specific forward-model data needs?**

Only if both independently pass may GeoPT-like environment features become an auxiliary encoder inside M5.

## Immediate evidence race

1. Codex M5 L1 extraction + simple-model kill gate.
2. Codex M6 G0.5-B checkpoint load + G1 low-data transfer.
3. Promote whichever first gives an independent positive signal tied to source identity / forward fidelity.

No full closed-loop integration before these gates.
