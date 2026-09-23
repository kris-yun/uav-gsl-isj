# Candidate Priority Update — after M4 neutral pre-screen and M5 L0 positive

Date: 2026-09-23  
Branch: \`research/main-innovation-search-parallel-v1\`

## Current priority

### #1 M6 — Dynamics-Lifted Physics Foundation PMFS
Status: \`LEAD / G0.5-A PASS / G0.5-B CHECKPOINT LOAD PENDING\`

Why it leads:
- 2026 ICML remote-field mother idea;
- official volume geometry representation maps naturally to indoor gas geometry/wind;
- real House token/runtime cost is low;
- preserves >99.9% of backbone if only output/source adapter is replaced;
- direct GSL foundation-transfer collision not found so far;
- strong low-data rationale.

Immediate next step:
- actual official checkpoint load on Codex/VM;
- then G1 historical low-data pretrained-vs-scratch pilot.

### #2 M5 — Generative Lagrangian Filament World Model
Status: \`L0 POSITIVE / L1 PENDING\`

Why it rose:
- NeurIPS 2025 generative-physics mother idea over 3-D point trajectories;
- PMFS/GADEN are natively filament/particle systems;
- GADEN pseudo trajectories are recoverable despite no explicit ID because:
  - survivor order is preserved;
  - births append;
  - sigma deterministically encodes age;
  - current 7Hz × 0.1s generator has ≤1 birth per step.

Main risk:
- GADEN's transition law is itself known and partly Gaussian.
- M5 only survives as a main idea if L1 shows source-relevant structure beyond simple PMFS/Gaussian transition modeling.

### #3 M3 — Physics-Anchored Stochastic Plume World Model
Status: \`HOLD / W0 DATA-GENERATION GATE\`

Strength:
- NeurIPS 2025 function-space stochastic process / flow-matching mother idea;
- strongest stochastic-field representation.

Weakness:
- denser high-fidelity data requirement;
- 2026 gas-PINO near-neighbor;
- current archived data insufficient for direct training.

### #4 M4 — Causal Compositional Plume World Model
Status: \`HOLD / SCIENTIFIC NARRATIVE STRONG, EMPIRICAL DIFFERENTIATION ABSENT\`

What happened:
- historical 2×2 intervention asset is genuinely controlled;
- simple additive composition failed 0/12;
- matched-capacity physical-compositional vs monolithic learned representations both achieve 12/12 source identity;
- no decisive compositional advantage.

M4 remains scientifically plausible only under the stronger operator form:

\[
C=\mathcal T_{W,O}(Q_S),
\]

but should not consume the main resources until new dense-field intervention data exist.

## Execution note

Attempting to use Hugging Face Jobs for GeoPT checkpoint auditing returned a 402 Payment Required response in the current assistant environment.

This is an infrastructure limitation only.

Codex should run G0.5-B locally using the public \`GeoPT_8layers.pt\` checkpoint.
