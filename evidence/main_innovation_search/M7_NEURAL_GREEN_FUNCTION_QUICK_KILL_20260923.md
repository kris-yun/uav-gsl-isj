# M7 Quick-Kill — Neural Green's Function Response Kernel

Date: 2026-09-23  
Branch: \`research/main-innovation-search-parallel-v1\`

## Candidate

2025 Neural Green's Functions suggests learning a geometry-dependent PDE response kernel:

\[
G_E(x,s)
\]

so arbitrary source forcing can be evaluated without retraining.

This maps elegantly to PMFS candidate sources:

\[
C_s(x)=G_{W,O}(x,s)Q_s.
\]

## Why it is attractive

- source-agnostic by construction;
- one environment response operator serves all source candidates;
- candidate-source sweep becomes very cheap;
- 2025 Neural Green's Functions explicitly targets unseen source/boundary-function generalization.

## Hard prior-art collision

The **scientific source-inversion idea** is not new.

### Urban contaminant inversion, 2006

Building-resolving urban contaminant source inversion already used large forward databases with a **Green's-function approach** to accelerate source-location/release-rate inference.

### Advection–diffusion source identification, 2018

Stanev et al., *Identification of release sources in advection–diffusion system by machine learning combined with Green's function inverse method*, Applied Mathematical Modelling 60 (2018) 64–76.

This explicitly combines:
- machine learning;
- Green functions;
- advection–diffusion;
- unknown release-source identification.

Therefore M7 cannot defensibly claim:
- first response-kernel source localization;
- first ML + Green-function advection–diffusion source inversion;
- first source-agnostic Green-kernel representation for release-source identification.

## Additional collision pressure

Generic learned operator/PINO gas-source localization is already occupied in 2026.

A Neural-Green implementation would risk becoming:

> a newer operator architecture applied to an old Green-function source-inversion idea.

That does not meet the requested paper-level “remote big idea not already present in the field” standard.

## Decision

\`NO-GO AS MAIN INNOVATION\`.

Possible future auxiliary role:
- source-query-efficient decoder for M6;
- analytic/physical response-kernel regularizer;
- fast ablation baseline.

Do not allocate main-search resources to M7.
