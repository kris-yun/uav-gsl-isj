# Topological Plume Invariants V1 — cheap screen

Date: 2026-09-21  
Status: **NO-GO AS MAIN INNOVATION IN CURRENT FORM**

## Mother idea tested

Use rank-based spatial excursion-set topology rather than raw gas amplitude as a source fingerprint.

Scientific motivation: topological summaries can remain stable under strong metric/amplitude distortion, making them a plausible remote-field transfer for turbulent plume observations.

This screen deliberately used a minimal, training-free topology proxy before any persistent-homology implementation.

## Data

Frozen controlled VGR 240-s asset:

- H01/H02/H03
- SA/SB
- fast/slow
- 12 cases total
- identical within-House geometry/timing paths
- 0.3 m spatial aggregation

This is a source-identity mechanism screen only, not the authoritative 300-s localization endpoint.

## Predeclared proxy

For each spatial gas field:

1. replace cell amplitudes by empirical ranks;
2. threshold at fixed quantiles 0.50 / 0.65 / 0.75 / 0.85 / 0.92 / 0.97;
3. compute 4-neighbour excursion components;
4. summarize active fraction, component count, largest-component fraction, and anchored centroids/sizes of the three largest components;
5. compare each episode against opposite-wind SA/SB templates using the same feature construction.

No threshold search was performed after seeing results.

Because the descriptor is rank based, positive affine amplitude transforms do not change it.

## Result

Cross-wind source identity:

- overall: **10/12 = 83.33%**
- H01: 3/4
- H02: 3/4
- H03: 4/4
- mean signed source margin: +0.1521

Failures:

- H01_SB_fast
- H02_SA_slow

Source-blind destructive control:

Spatially shuffle the cell ranks independently within each episode while preserving the full value/rank distribution.

Across 100 deterministic shuffles:

- mean accuracy: **53.17%**
- median: **50%**
- min: 16.67%
- max: 91.67%
- perfect 12/12 runs: 0

Therefore the proxy detects genuine spatial organization rather than only the marginal concentration distribution.

## Decision

The topology signal is real but **not competitive with the already-frozen affine/quotient source identity signal**, which reaches 12/12 on this asset and survives strong scale/background nuisance stress.

Do not tune quantile thresholds or component weights on these same 12 cases.

Do not promote TDA/persistent-homology plume topology as the new main innovation from this evidence.

A richer topology construction could still be scientifically interesting, but the cheap necessary screen does not justify spending the main-innovation budget on it.
