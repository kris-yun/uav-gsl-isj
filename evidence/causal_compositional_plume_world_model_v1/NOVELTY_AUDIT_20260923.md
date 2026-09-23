# Novelty Audit — M4 Causal Compositional Plume World Model

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`

## Decision

`KEEP — but broad "causal GSL" claims are forbidden`

## 1. Direct historical boundary: causal graphical models in gas localization are old

A classical Bayesian gas-detection/source-localization line already represented gas propagation through a discretized area with an explicit causal graphical model / HMM-style dependency structure.

Therefore M4 must NOT claim:
- first causal model of gas propagation;
- first graphical causal reasoning for gas-source localization;
- first Bayesian source localization with directed dependencies.

## 2. 2025 near-neighbor: causal source attribution in atmospheric pollution

Recent urban-air work explicitly frames pollution source attribution as causal inference:

- emission source categories act as treatments;
- concentrations are effects;
- atmospheric/dispersion physics mediate the causal mechanism;
- counterfactual emission interventions are analyzed.

Therefore M4 must NOT claim:
- first causal source attribution under dispersion physics;
- first counterfactual reasoning about emission/source changes.

This work is not the same task as mobile robotic GSL, but it materially narrows the novelty claim.

## 3. Remote-field parent that remains relevant

WM3C, ICLR 2025:
*Modeling Unseen Environments with Language-guided Composable Causal Components in Reinforcement Learning.*

Transferable principle:
- world dynamics are decomposed into reusable causal mechanisms;
- new environments are handled by recombining known causal components;
- the hard evaluation is unseen mechanism composition, not in-distribution prediction.

The language-based decomposition is NOT transferred.

For plume physics, mechanism identities are known from physical semantics.

## 4. Defensible novelty hypothesis

M4 survives only under the narrower statement:

> PMFS source-candidate simulation is reformulated as **compositional interventional world modeling**, in which source injection, wind transport, obstacle/boundary effects, unresolved turbulence and sensing are reusable mechanisms; candidate-source evaluation corresponds to `do(S=s)`, and the learned model is explicitly tested on unseen source×wind×geometry recombinations.

This is materially different from:
- a causal DAG drawn around an existing dispersion model;
- source attribution from passive atmospheric data;
- generic causal representation learning;
- generic neural plume prediction.

## 5. Required empirical novelty evidence

A causal/compositional claim requires all of:

1. controlled interventions where one mechanism changes while others are fixed;
2. a monolithic matched-capacity baseline;
3. held-out mechanism recombinations;
4. module-swap/intervention-specific diagnostics;
5. downstream truth-source candidate rank.

If M4 only improves ordinary interpolation on random train/test splits, the causal claim fails.

## 6. Kill rule

If a direct robotic/plume source-localization work is found that:
- factorizes source/wind/geometry mechanisms;
- learns them as reusable modules;
- explicitly evaluates unseen intervention recombinations;

then M4 is NO-GO as the paper-level main innovation.
