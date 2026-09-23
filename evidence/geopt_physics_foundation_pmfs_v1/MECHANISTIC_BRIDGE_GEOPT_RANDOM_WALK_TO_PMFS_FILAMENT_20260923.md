# M6 Mechanistic Bridge — GeoPT constrained random walks -> PMFS filament transport

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Why this matters

The strongest M6 transfer argument is not merely:

> GeoPT is a physics foundation model with geometry and dynamics inputs.

The released GeoPT pre-training generator shows a much closer mechanism.

GeoPT pre-training explicitly:

1. samples **volume points** around a 3-D geometry;
2. samples a 3-D unit movement direction for each point;
3. samples a movement step length;
4. performs **multi-step Lagrangian walks**;
5. ray-tests each intended movement against the geometry;
6. if a particle would hit the surface, truncates the movement to just before the collision;
7. uses the resulting geometry-constrained trajectories as self-supervision.

The condition vector is exactly:

`[direction_x, direction_y, direction_z, step_length]`.

This is a much more natural parent representation for PMFS than generic image/mesh pretraining.

## PMFS correspondence

Native PMFS filament transport has the structure:

`new_position = old_position + delta_t * (wind + stochastic_noise)`

plus obstacle handling.

Thus the common structural object is:

**a Lagrangian point/particle displacement conditioned by a vector direction and displacement magnitude, constrained by geometry.**

### GeoPT synthetic pretraining

`X_(k+1) = geometry_constrained_walk(X_k, direction, step_length)`

### PMFS physical transport

`X_(k+1) = obstacle_constrained_move(X_k, wind_direction, wind_speed * delta_t + stochastic_part)`

The two are not identical physical systems.

But the pretraining task has already taught the backbone a reusable representation of:

- interior volume points;
- distance/direction to boundaries;
- how movement direction interacts with geometry;
- how finite displacement is clipped by collision/boundaries.

These are directly relevant primitives for indoor gas transport.

## Gas dynamics prompt v2

Do not use an arbitrary four-channel wind encoding.

Use the GeoPT pretraining semantics.

For each gas free-space point x:

`direction(x) = wind(x) / (norm(wind(x)) + epsilon)`

Define a reference advective displacement over a source-blind physical horizon:

`step_length(x) = geometry_scale * norm(wind(x)) * tau_ref`

where:
- `geometry_scale` is the same world-to-GeoPT coordinate scaling used for the House;
- `tau_ref` is a predeclared physical time horizon.

Preferred first choice:
- use a protocol-defined wind/simulation interval, not a fitted hyperparameter;
- audit the resulting step-length distribution against GeoPT's pretraining range before training.

Then:

`fx11 = [x,y,z,SDF,boundary_dir_x,boundary_dir_y,boundary_dir_z,
          wind_dir_x,wind_dir_y,wind_dir_z,advective_step_length]`

This preserves the exact GeoPT dynamics semantics more faithfully than using raw wind speed alone.

## Zero-wind handling

For cells with near-zero wind:

- dynamics direction must be defined deterministically, e.g. [0,0,0];
- step length = 0.

Do not normalize near-zero vectors into arbitrary directions.

## Source injection as particle birth

GeoPT pretraining lacks gas-source birth/injection.

This becomes the PMFS-specific adapter:

- environment backbone = pretrained geometry-constrained transport representation;
- candidate source adapter = localized particle/mass injection mechanism.

Conceptually:

`environment transport prior + candidate source birth -> candidate plume field`.

This is a stronger PMFS-specific interpretation than generic source-coordinate conditioning.

## Stochasticity

M6 G1 should remain deterministic first to test foundation transfer.

If successful, M3/M5-style stochastic residual dynamics may later model:

- turbulent deviations from mean advective direction;
- spatially varying diffusion;
- multimodal recirculation.

Do not add them before the deterministic foundation-transfer signal is established.

## New physical ablation

In addition to wind shuffle, compare:

A. raw wind-vector prompt:
`[unit_wind, raw_speed]`

B. pretraining-aligned displacement prompt:
`[unit_wind, scale * speed * tau_ref]`

C. direction-only prompt with constant step length.

The purpose is not to truth-tune a winner.

Freeze `tau_ref` from the simulation protocol and report all three as an interface ablation.

If pretraining transfer is real, the pretraining-aligned prompt should be at least competitive with arbitrary channel encoding in low-data transfer.

## Important claim boundary

Do NOT claim GeoPT was pretrained on gas/fluid transport.

It was not.

The defensible mechanism statement is:

> GeoPT was pretrained on geometry-constrained multi-step particle walks, creating a representation whose primitive dynamics—directional Lagrangian displacement interacting with boundaries—are structurally aligned with PMFS filament transport.

This is a transfer hypothesis and must be validated against scratch controls.

## Updated confidence

This source-code finding reduces a major concern that M6 was only a generic geometry encoder.

M6 now has three aligned layers:

1. **geometry representation**:
   volume points + SDF + boundary direction;

2. **dynamics representation**:
   direction + finite displacement, learned through constrained walks;

3. **PMFS-specific mechanism**:
   candidate-source injection adapter.

Status:

`STRONGER MECHANISTIC JUSTIFICATION — STILL REQUIRES G1 SOURCE-RANK EVIDENCE`.
