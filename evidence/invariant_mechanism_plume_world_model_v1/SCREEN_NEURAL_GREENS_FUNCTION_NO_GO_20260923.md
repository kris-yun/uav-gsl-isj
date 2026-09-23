# SCREEN — Neural Green's Function for PMFS

Date: 2026-09-23  
Decision: **NO-GO as main innovation**

## Attractive remote idea

Yoo et al., *Neural Green's Functions*, NeurIPS 2025.

The method learns Green-function-like linear PDE solution operators with strong generalization across:
- source functions;
- boundary conditions;
- irregular geometries.

This appears superficially ideal for PMFS because every candidate source can be viewed as a source impulse whose field is the environment response.

## Direct GSL collision

However, gas-source localization already has a direct Green-function neural formulation.

DLR work:

*Physics-Guided Neural Networks for Distributed Sparse Gas Source Localization Using Poisson's Equation and Green's Function Method* (2024-era conference work).

The public description explicitly states that:
- a PGNN approximates a parameterized Green's function of the gas-dispersion PDE;
- the surrogate is inserted into source-localization optimization;
- arbitrary/super-resolution source locations can be estimated.

Therefore the broad contribution

> neural/learned Green's function as the source-to-field operator for gas-source localization

is already occupied.

## Decision

Do not spend offline experiment budget on this candidate.

A newer NeurIPS-2025 Green-function architecture is an implementation upgrade, not the requested new paper-level mother idea.

Status:

\`NO_GO_DIRECT_GSL_GREEN_FUNCTION_COLLISION\`.
