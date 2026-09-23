# DECISION UPDATE — Demote M4 causal-compositional world model after 2026 GSL collision

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`

## Decision

`M4 = DEMOTE AS MAIN / KEEP ONLY NARROW COMPOSITIONAL-GENERALIZATION HYPOTHESIS`

The broad main-theme claim "causal/physical-dependency world modeling for gas-source localization" is no longer sufficiently clean.

## Collision 1 — causal probabilistic GSL is old

Pavlin, de Oude & Mignet, *Gas Detection and Source Localization: A Bayesian Approach*, FUSION 2011.

The work uses causal probabilistic/Bayesian-network models to represent gas propagation and source hypotheses.

Therefore do not claim:
- first causal model for GSL;
- first causal graph of gas propagation for source localization.

## Collision 2 — very close 2026 deep probabilistic GSL

Kim, Kim, Lee & Oh, *Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference*, arXiv:2608.16221, submitted 17 Aug 2026.

Their DGSE-S framework explicitly:
- maintains a source posterior over map cells;
- uses sparse mobile-robot gas/wind measurements;
- estimates probabilistic wind and concentration fields;
- encodes physical dependency structure through sequential conditional inference;
- conditions concentration inference on inferred wind;
- conditions source-location inference on inferred wind and concentration;
- supports uncertainty-aware active GSL;
- evaluates complex multi-room indoor environments.

This occupies much of the broad narrative:
> "decompose indoor GSL according to causal/physical dependencies among wind, concentration, and source."

## What remains potentially distinct

The following narrower hypothesis is still open enough to test:

> **interventional compositional generalization:** learn separately reusable source-injection, wind-transport and geometry mechanisms, then predict unseen source×wind×geometry recombinations by module composition.

The hard distinction from DGSE-S would have to be:
- explicit intervention semantics `do(S=s)`, `do(W=w)`;
- train/test on held-out mechanism combinations;
- module swapping;
- counterfactual source replay inside PMFS.

But this is now a **narrow algorithmic hypothesis**, not a clean untouched paper-level mother idea.

## Consequence

Do not spend current primary compute on M4.

Priority moves to M6:
**Dynamics-Lifted Physics Foundation Model for PMFS.**

M4 may return later as:
- a compositional generalization auxiliary;
- an ablation architecture;
- a source/wind module-separation technique.

Status:

`DEMOTED — NOT CURRENT MAIN LEAD`.
