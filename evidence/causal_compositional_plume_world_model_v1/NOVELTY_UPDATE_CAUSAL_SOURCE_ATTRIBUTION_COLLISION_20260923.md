# M4 Novelty Update — Direct causal source-attribution collision

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`

## New near-direct collision

Bhardwaj & Subramanian, *Towards Causal Understanding of Urban Air Pollution: Mechanistic Models under Sparse Sensing*, NeurIPS 2025 CauScien Workshop.

The work explicitly:

- frames pollution source attribution as causal inference;
- treats emission sources as treatments;
- uses meteorology/wind as transport context;
- links source emissions to measured concentrations through mechanistic dispersion physics;
- reasons about counterfactual source interventions such as changing/reducing a source.

Therefore the following are NOT novel enough:

- “source is an intervention”;
- “use do(source) in atmospheric source attribution”;
- “causal source attribution through plume physics”;
- “counterfactual plume reasoning” in broad terms.

## Remaining M4 hypothesis

M4 only remains distinct at the stronger **learned compositional world-model** level:

> learn reusable source-injection and environment/transport modules whose recombination predicts an unseen source × wind intervention pair, and use that prediction to improve PMFS source identity.

This is closer to ICLR 2025 WM3C's compositional-mechanism idea than to classical causal attribution.

## Priority change

M4 should no longer be treated as a co-equal main candidate by default.

Current role:

- **auxiliary / structural hypothesis for M6 CF-PFM**, unless C0 produces a strong unseen-recombination advantage;
- independent main candidate only if factorized intervention recombination materially beats matched-capacity monolithic models and improves truth-source rank.

## Hard survival gate

C0 remains valid:

- one House;
- 2 sources × 2 physical wind conditions;
- hold one combination out;
- matched-capacity monolithic vs compositional model;
- intervention-label destructive null;
- truth-source candidate rank downstream.

If this does not clearly favor compositional structure, M4 is `NO-GO AS MAIN`.

Current status:

`DEMOTED — AUXILIARY/STRUCTURAL CANDIDATE PENDING C0`.
