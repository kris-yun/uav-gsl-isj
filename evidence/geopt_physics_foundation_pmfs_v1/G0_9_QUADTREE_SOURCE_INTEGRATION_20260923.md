# M6 G0.9 — Quadtree-Consistent Source Integration

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Problem

Native PMFS source candidates are not always point sources.

For an NQA/quadtree source candidate, official `SimulationSource::getPoint()` samples uniformly inside the candidate rectangle whenever a filament is emitted.

Therefore the native candidate forward prediction implicitly represents a **source-region mixture**, not merely the field generated from the rectangle center.

A foundation-model replacement must preserve this candidate semantics.

## Decision

Do NOT represent a quadtree candidate only by its center in the hard source-rank replay.

Use deterministic quadrature over the candidate source region.

## Primary quadrature rule

For rectangular candidate region:

`R_s = [x_min,x_max] × [y_min,y_max]`

use tensor-product 2-point Gauss-Legendre quadrature in each axis.

1-D canonical points:

`xi = ±1/sqrt(3)`

Map into each world interval.

This gives four deterministic source positions per candidate.

All weights are equal:

`weight = 1/4`.

For foundation-model candidate map:

`H_s(x) ≈ (1/4) * sum_{k=1..4} H(x | source = s_k)`

This approximates the uniform source-location marginal over the quadtree rectangle.

## Why this rule

- deterministic;
- source-blind;
- no truth tuning;
- mathematically tied to uniform-region integration;
- more faithful to PMFS than center-only injection;
- only four source prompts per candidate.

## Point/small-cell candidates

Use the same rule for all rectangular candidates for consistency.

If the candidate contract explicitly identifies a true point source with zero region extent, use that point directly.

Do not switch quadrature order based on truth or candidate score.

## z coordinate

All quadrature points inherit the same protocol-defined source plane.

Do not derive z from the known truth source.

## Training vs PMFS replay

### Training pilot
GADEN pilot sources are point interventions at the preregistered source positions.

### Candidate replay
A PMFS quadtree candidate is a mixture over possible point-source locations.

Therefore candidate forward prediction may average the point-conditioned model over the fixed quadrature points.

This is a valid and explicit bridge between point-source training and PMFS region-candidate inference.

## Required control

Report a center-only inference ablation for runtime/diagnosis, but do not choose between center and quadrature using truth rank.

Primary preregistered candidate representation is 2×2 quadrature.

## Computational note

For S candidates:
- naive calls = 4S;
- source prompts can be batched;
- environment geometry/wind is identical.

Do not optimize until G1 establishes source-rank value.

## Scientific benefit

This keeps M6 recognizably PMFS-native:

- PMFS quadtree candidate space remains unchanged;
- only the candidate forward simulator is replaced;
- candidate-region uncertainty is preserved rather than silently collapsed.

Status:

`REQUIRED FOR FAIR M6-vs-PMFS SOURCE-RANK REPLAY`.
