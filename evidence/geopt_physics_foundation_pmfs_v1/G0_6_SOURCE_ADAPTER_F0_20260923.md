# G0.6 Source Injection Adapter F0

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Decision

`G0.6 = PASS`

The PMFS-specific candidate-source mechanism can be added without changing GeoPT's pretrained raw input projection.

## Adapter

For each query point x and candidate source s:

`q = exp(-||x-s||^2 / (2 sigma_s^2))`

`r_s = [q, q*dx, q*dy, q*dz]`

A small MLP maps the 4-D localized source feature into GeoPT hidden width 256.

Architecture:

`4 -> 64 -> 256`

plus one scalar learnable gate.

Parameter count:

`16,961`

Reference GeoPT 8-layer model:

`3,865,673`

Adapter fraction:

`0.43876%`

Thus source adaptation is small relative to the foundation backbone.

## Zero-init preservation

The adapter gate is initialized to zero.

At initialization:

`hidden = pretrained_environment_embedding + 0 * source_adapter`

Therefore:
- loading a pretrained GeoPT backbone preserves its initial function;
- source conditioning is introduced gradually by training;
- random source-adapter initialization cannot immediately destroy the foundation representation.

## Exact input contract

The corrected GeoPT contract remains unchanged:

- separate `pos3`;
- `fx11 = geometry7 + dynamics4`;
- preprocess sees 14 dimensions.

Source is not concatenated into raw inputs.

## Physical source-kernel scale

The first probe ties `sigma_s` to the source/candidate-cell geometric scale.

Do not tune `sigma_s` using truth-source rank.

The exact first-pilot convention must be frozen before training.

## Interpretation

M6 can now be decomposed cleanly into:

1. **pretrained environment transport representation**:
   geometry + boundary relations + wind-displacement prompt;

2. **small PMFS-specific source birth/injection adapter**:
   candidate source enters as a localized forcing;

3. **plume/hit-map output head**.

This keeps the main novelty centered on foundation transfer rather than rebuilding a task-specific neural operator.

Status:

`PASS — IMPLEMENTATION INTERFACE READY FOR G1`.
