# Status Update — M7 Joins M6 in Tier A

Date: 2026-09-23  
Branch: \`research/main-innovation-search-parallel-v1\`

## Tier A — current main competitors

### M6 — Dynamics-Lifted Physics Foundation PMFS

Mother idea:
- ICML 2026 GeoPT;
- cross-physics geometry–dynamics pretraining;
- transfer pretrained representation into scarce-data plume forward modeling.

Current positives:
- official volume representation maps closely to indoor free-space geometry;
- exact 11-D physical feature contract can be preserved;
- House02 631-token forward cost is small;
- source adapter can be added after pretrained embedding;
- no direct GSL foundation-transfer collision found.

Current hard gate:
- actual official checkpoint load on Codex/VM;
- pretrained vs same-architecture random-init low-data scaling;
- truth-source rank.

Strength:
- fastest route to a real empirical answer.

Risk:
- if pretraining does not beat random initialization, the idea collapses into generic Transolver/PINO.

### M7 — Test-Time Compositional Plume Operators

Mother idea:
- ICML 2026 neural operator splitting/test-time composition;
- AISTATS 2026 learning physical operators by operator splitting;
- broader 2026 compositional neural-operator trend.

Core gas-specific representation:

\[
\mathcal F_{\rm plume}
=
\mathcal B_O
\circ
\mathcal D
\circ
\mathcal A_W
\circ
\mathcal J_S.
\]

Refined first version keeps known physics explicit:
- source injection: analytic;
- spatial wind advection: explicit;
- obstacle/boundary: explicit;
- baseline diffusion: explicit.

Only the unresolved transport residual is represented by a reusable operator dictionary selected/composed at test time.

Current positives:
- extremely strong physical semantics;
- wind is an actual transport operator;
- PMFS candidate source naturally changes only the source-injection operator;
- direct GSL collision not found;
- corrected R1 shows source identity is highly sensitive to individual forward mechanisms.

Current hard gate:
- export a small real GADEN field sequence;
- analytical splitting O0;
- demonstrate a structured, source-transferable residual family;
- only then learn any operator.

Strength:
- strongest physical/scientific narrative currently under consideration.

Risk:
- if residual is unstructured or a single monolithic residual model works equally well, test-time operator composition is unjustified.

Branch:
\`research/testtime-compositional-plume-operators-v1\`

Key commits:
- candidate: \`c26af7df831053e4b05686a7076417fa8f324a63\`;
- O0: \`dee93e38ad1fcfbcd3a84c42c5d6f7309a44420a\`;
- baseline motivation: \`df08d5d85ee07c76c3dc7b2a5cf307d535fb9848\`;
- exact-physics residual-dictionary refinement: \`07e1172a6af95cbbba2518049aff18e14237034e\`.

## Tier B

### M3 — stochastic plume world model
Keep:
- strongest stochastic-field representation idea.
Hold:
- dense/high-fidelity data burden;
- must beat deterministic residual model.

### M5 — generative Lagrangian filament world model
Keep:
- natural PMFS/GADEN interface;
- possible future stochastic residual mechanism.
Hold:
- main-theme novelty weaker unless filament dynamics are demonstrably multimodal/non-Gaussian and source-critical.

## HOLD

### M4 — causal compositional plume world model

Historical 2×2 source×transport asset is clean, but compositional recombination showed no unique benefit over same-source transfer.

Status remains HOLD.

## Zebra / in-context PDE learning

ICML 2025 Zebra remains an important conceptual parent for test-time adaptation.

Direct Zebra implementation is not currently promoted because:
- core 2-D path uses regular-grid state tokens;
- source forcing is not explicitly encoded in the main ICL sequence;
- geometry/local wind are not native prompt objects.

The search for Zebra led to the stronger M7 test-time physics-composition formulation.

## Immediate empirical priorities

1. **M6 G0.5-B/G1**
   - actual GeoPT checkpoint load;
   - frozen/low-data pretrained-vs-random test.

2. **M7 O0**
   - playback one GADEN realization;
   - export 20–40 concentration snapshots;
   - run analytical source/advection/diffusion/boundary splitting;
   - test residual structure and source-transferability.

Whichever obtains a genuine positive signal first gets the next implementation budget.

No merging of M6 and M7 before these gates.
