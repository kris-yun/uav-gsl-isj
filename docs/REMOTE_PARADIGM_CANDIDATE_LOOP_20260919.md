# Remote-Paradigm Candidate Loop — 2026-09-19

Status: INTERNAL SCREENING ONLY. No paper-level claim authorized.

## Hard acceptance standard

A final 1+2 design must satisfy all of the following:

1. M1 is a paradigm-level idea from a 2025/2026 top venue or comparably strong journal, capable of supporting the paper's main scientific narrative.
2. M2 and M3 are independent auxiliary ideas from recent remote domains, each solving a distinct failure of M1 rather than decorating it.
3. None of the three may reduce to planner/OED, generic loss engineering, an attention block, a GNN/PINN wrapper, or an already-colliding GSL method.
4. The combined method must preserve a source-location probability map.
5. Existing project evidence must provide at least one falsifiable offline discriminator before new closed-loop runs.
6. Lightweight implementation is required but is not counted as an innovation.
7. The design must remain definable across VGR/GADEN, a public DNS/plume dataset, and real wind-tunnel data.

## Candidate families under screening

### C1 — Inverse Generative Modeling
Main idea: treat source localization as inverse generation under latent transport rather than direct source classification.
Current implementation family: flow / consistency / latent generative inverse models.
Primary risk: may collapse to a generic probabilistic inverse model without a distinct source-transport scientific mechanism.

### C2 — Physical World Models
Main idea: source is a persistent hidden cause inside a learned physical latent world model; infer source through latent dynamics consistency.
Primary risk: drifts into RL/planning/agent framing and may be heavier than needed.

### C3 — Physics-informed Self-Supervised Representation
Main idea: learn transport/source structure from unlabeled plume dynamics and only use source labels downstream.
Primary risk: may reduce to pretraining + head, with weak paper-level scientific thesis.

### C4 — State-first Inverse Inference
Main idea: reconstruct a physically meaningful intermediate transport state first, then infer source from that recovered state, rather than directly mapping sparse observations to source.
Primary risk: needs a modern 2025/2026 paradigm source stronger than classical state estimation.

### C5 — Mechanism-factorized Generative Inference
Main idea: compositional latent variables correspond to source, transport, sensor dynamics, and geometry; inference identifies the latent mechanism combination that generated observations.
Primary risk: disentanglement identifiability and collision with causal representation learning.

## Current negative constraints from project evidence

- Transport variation can approach cross-source variation (H01 ratio 0.952).
- Exact candidate-specific physical response can preserve source identity, while deployable approximations can destroy it.
- Native first-passage timing carries source information; coarse HIT compression can destroy it.
- Some source×wind combinations have nearly zero finite-horizon exposure.
- Posterior entropy can collapse while localization is wrong.
- Simple multi-receiver structure can increase measurements without recovering weak source modes.
- Cross-House nuisance removal fails when transport bias is candidate-dependent.

## Screening protocol

For each M1:
1. top-venue provenance screen;
2. GSL novelty collision screen;
3. theory-name-removal test;
4. lightweight feasibility;
5. existing-data offline falsification;
6. cross-dataset definability;
7. auxiliary M2/M3 search only after M1 survives.

Scoring is provisional and not shown externally until at least two independent literature lineages and multiple internal evidence families support the same M1.

