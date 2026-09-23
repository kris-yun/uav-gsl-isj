# Candidate M7 — Symbolic Missing-Physics / Closure Discovery

Date: 2026-09-23  
Status: **NO-GO AS MAIN INNOVATION**

## Proposed mother idea

Use 2025 symbolic-PDE discovery / abductive learning to infer a missing transport or closure term from high-fidelity plume data, then insert the discovered interpretable term back into PMFS/advection–diffusion physics.

Remote-field anchor considered:
- Gao et al., *Discovering Symbolic Partial Differential Equation by Abductive Learning*, NeurIPS 2025.

The attraction was strong:
- interpretable physics rather than a black-box surrogate;
- neural learning + logic/physics hypothesis space;
- potentially discover a missing PMFS transport closure.

## Direct domain collision

However, equation-discovery correction of contaminant-transport physics is already present in the adjacent domain.

A prior work titled:

*Equation discovery of dynamized coefficients in the k-ε model for urban airflow and airborne contaminant dispersion*

already:
- targets urban airflow;
- targets airborne contaminant dispersion;
- uses gene-expression-programming / symbolic equation discovery;
- constructs dynamic corrections to the turbulence model;
- learns corrected model formulations / closure coefficients;
- constrains expressions for robustness/convergence;
- evaluates generalization across urban cases.

Thus the broad paper-level thesis

> “discover missing symbolic closure physics for gas/contaminant dispersion and put it into the simulator”

is already occupied.

## Why NeurIPS 2025 ABL-PDE does not rescue it

ABL-PDE is a newer and stronger equation-discovery methodology.

But replacing the older symbolic-regression engine with ABL-PDE would primarily be:
- a newer discovery algorithm;
- applied to an already established contaminant-dispersion closure-discovery problem.

That does not meet the user's required main-innovation standard.

## Possible future role

Symbolic discovery could still be an interpretability/diagnostic tool if M6/M3 residual analysis identifies a compact, repeatable physical residual.

But it should not carry the paper thesis.

## Decision

`NO-GO AS MAIN`

Do not implement unless a later main candidate creates a specific auxiliary need for interpretable closure extraction.
