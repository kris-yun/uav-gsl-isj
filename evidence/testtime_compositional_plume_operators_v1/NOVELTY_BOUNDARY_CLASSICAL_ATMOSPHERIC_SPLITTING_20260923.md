# Novelty Boundary — Classical Atmospheric Operator Splitting Is Old

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`

## Hard prior-art boundary

Operator splitting for atmospheric transport and pollutant advection–diffusion is classical.

Examples:

- McRae, Goodin & Seinfeld (1982): atmospheric diffusion equation numerical methods including operator splitting.
- Khan & Liu (1995): operator splitting for advection–diffusion–reaction equations.
- Lanser & Verwer (1998/1999): analysis of operator splitting for advection–diffusion–reaction problems from air-pollution modelling.
- later work analyzes splitting/discretization/boundary-condition errors for advection–diffusion.

Therefore M7 must **never** claim:
- first operator splitting for gas/plume transport;
- first advection/diffusion decomposition for pollutant modeling;
- first Strang splitting for plume simulation;
- first modular atmospheric transport solver.

## Modern 2025–2026 novelty source

The relevant remote-field shift is:

### ICML 2025 DISCO
Discover an evolution operator from a short trajectory using a hypernetwork, separating:
- dynamics/operator inference;
- state evolution.

### ICML 2026 Neural Operator Splitting
Freeze a dictionary of learned dynamics/operators and use **test-time computation over operator compositions** to approximate unseen physics without weight updates.

### AISTATS 2026 Learning Physical Operators
Use operator splitting to create interpretable learned/fixed physical operators and improve unseen-physics generalization.

The main transferable idea is therefore:

> **learned reusable physical mechanisms as operator blocks, with test-time composition/generalization.**

## PMFS-specific novelty hypothesis

The candidate claim is not numerical splitting.

It is:

> A PMFS candidate forward model can be represented by a reusable library of transport-mechanism operators, preserving known wind/source/obstacle physics explicitly while learning only unresolved transport mechanisms; the appropriate world model for an unseen environment is constructed at test time by composing frozen mechanism operators, and this improves candidate-source identity without per-environment retraining.

## Hard comparison required

M7 must beat:

1. classical analytical split;
2. native PMFS;
3. equal-capacity monolithic learned plume surrogate;
4. fixed learned residual model without a mechanism dictionary.

If only (1) improves, the result is a numerical modeling improvement, not the requested main innovation.

If only a monolithic learned residual is needed, the 2026 test-time composition thesis is unsupported.

Status:

\`NOVELTY BOUNDARY FROZEN\`.
