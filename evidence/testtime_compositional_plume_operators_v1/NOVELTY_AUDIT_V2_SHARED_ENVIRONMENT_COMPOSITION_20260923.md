# M7 Novelty Audit v2 — Direct GSL / Source-Inversion Collision Search

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`

## Search scope

Systematic searches covered combinations of:

- gas source localization;
- odor source localization;
- plume source / pollutant source inversion;
- atmospheric / gas / pollutant dispersion;
- neural operator splitting;
- compositional neural operator;
- operator library;
- test-time physics composition;
- world model;
- in-context operator learning;
- source identification + learned physical operators.

Sources searched include Scite-indexed literature and public code/repository evidence.

## Result

No direct prior work was found that combines all of the following:

1. robotic/mobile gas-source localization;
2. PMFS-like discrete candidate-source inference;
3. a reusable library of learned physical transport operators;
4. explicit wind/source/obstacle mechanisms;
5. test-time composition/search over frozen operators;
6. source-location inference using the resulting candidate forward maps.

## Important nearby classes that are already occupied

### A. Classical atmospheric operator splitting

Old and established:
- advection/diffusion/reaction splitting;
- Strang splitting;
- atmospheric pollution transport solvers.

This is **not** novelty.

### B. Learned gas-dispersion surrogates

Occupied:
- physics-guided neural gas-dispersion models;
- PINN/PINO gas-source localization;
- PHOENIX-UNet-style obstacle-aware gas surrogate modeling.

A single monolithic learned plume operator is **not** novelty.

### C. PDE source inversion using numerical splitting

Source-identification literature contains inverse PDE methods where operator splitting may be suggested or used as a numerical integrator.

This does **not** constitute the modern M7 idea unless the physical operators themselves are reusable learned modules composed at test time.

### D. 2025–2026 compositional physics learning

Remote-field parent work already establishes:
- operator discovery from trajectories;
- learned physical operator blocks;
- neural operator splitting;
- test-time composition for unseen PDE dynamics.

Therefore M7 cannot claim those general methods themselves.

## Surviving novelty hypothesis

The candidate remains defensible only at this gas/PMFS-specific interface:

> **Construct a PMFS candidate plume world model from explicit known gas-transport mechanisms plus a reusable learned dictionary of unresolved transport operators, and select/compose those frozen operators at test time for the current wind/geometry regime, so source-candidate forward inference generalizes without per-environment retraining.**

The scientific object is not the split equation.

The scientific object is the **environment-conditioned mechanism composition used inside source-hypothesis testing**.

## What must make M7 more than an application paper

A mere transfer of ICML-2026 operator splitting to gas is insufficient.

M7 needs at least one gas-specific second derivation that is absent from the parent method.

Current strongest candidate:

### Candidate-conditioned shared world model

All PMFS source hypotheses share the same environment transport composition:

\[
\mathcal T_{E}
=
\mathcal B_O
\circ
\mathcal R_{k_m}
\circ\cdots\circ
\mathcal R_{k_1}
\circ
\mathcal D_0
\circ
\mathcal A_W.
\]

Only source injection changes:

\[
c_s
=
\mathcal T_E[
\mathcal J_s
].
\]

Thus the robot does **not** independently fit a forward model for each source candidate.

It first infers/selects one **shared environment mechanism composition** from source-blind evidence, then reuses it across every candidate source.

This shared-environment constraint is specific to the inverse-source problem and should become a central second derivation if O0/O1 support it.

## Why the shared-environment constraint matters

Without it, a learned simulator could choose a different transport explanation for every candidate source and make all candidates artificially easy to fit.

The physical world has one wind/geometry/turbulence regime at a time.

Therefore all candidate sources must be evaluated under the same frozen environment composition.

This creates a principled separation:

- environment inference/composition;
- source intervention/query.

## Hard empirical implication

At one source-update time:

1. infer/select \(\mathcal T_E\) without using source truth;
2. freeze \(\mathcal T_E\);
3. sweep every PMFS candidate \(s\) only by changing \(\mathcal J_s\);
4. rank candidates.

Forbidden:
- choosing a different residual/operator composition per source candidate.

If a per-source composition is necessary to get positive results, the main physical claim fails.

## Current novelty decision

\`NO DIRECT GSL COLLISION FOUND\`

but

\`APPLICATION-ONLY TRANSFER IS NOT ENOUGH\`.

Required second derivation:

\`ONE SHARED TEST-TIME ENVIRONMENT COMPOSITION, MANY SOURCE INTERVENTIONS\`.

This is now part of the M7 hard design boundary.
