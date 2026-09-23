# M6 Obstacle-Transport Alignment Audit

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Decision

`MECHANISTIC ALIGNMENT = STRONGER THAN GENERIC GEOMETRY TRANSFER`

A source-code comparison shows that GeoPT's synthetic particle-walk pretraining and PMFS's native filament simulator share a closely related obstacle-transport primitive.

## 1. GeoPT pretraining

Released GeoPT pretraining code:

- samples volume points;
- assigns a movement direction and step length;
- computes an intended end point;
- performs ray/mesh intersection;
- if the ray hits geometry before the intended step ends:
  - movement distance is truncated to approximately 99% of the collision distance;
- otherwise the full step is taken.

Thus the learned primitive is:

`directional Lagrangian transport + stop-before-boundary`.

## 2. Native PMFS candidate simulator

Official PMFS `Simulations::moveFilament()`:

`velocity = wind + Gaussian noise`

`newPos = position + deltaTime * velocity`

then `moveAlongPath(position,newPos)`.

With the currently compiled non-DDA branch, `moveAlongPath`:

- walks along the intended vector in sub-cell increments;
- tests occupancy after each increment;
- if a cell is not free:
  - subtracts the last increment;
  - leaves the filament at the last free position.

Thus PMFS also uses:

`directional Lagrangian transport + stop-before-obstacle`.

This is a very close structural analogue to GeoPT's constrained-walk pretraining.

## 3. GADEN high-fidelity simulator

Current GADEN core is more expressive.

`RunningSimulation::MoveSingleFilament()`:
- advects by the wind field;
- adds buoyancy;
- adds stochastic displacement;
- calls `StepTowards`.

`StepTowards`:
- steps along the desired displacement;
- on obstacle contact:
  - restores the previous free position;
  - estimates a local wall normal from cell indices;
  - removes the normal component of the remaining displacement;
  - recursively continues with the tangential component.

Thus GADEN can approximately slide/deflect along walls.

## 4. Scientific interpretation

GeoPT pretraining is **closer to the native PMFS obstacle-motion primitive** than to full GADEN wall interaction.

This is useful for the intended architecture:

- GeoPT backbone supplies a pretrained PMFS-compatible geometry/transport prior;
- scarce GADEN fine-tuning teaches the high-fidelity deviations:
  - wall sliding/deflection;
  - spatially varying wind;
  - buoyancy;
  - stochastic turbulent dispersion;
  - source birth/injection.

This is exactly the type of low-data transfer hypothesis M6 is meant to test.

## 5. Important mismatches

Do not overclaim equivalence.

GeoPT pretraining does NOT natively include:

1. gas source birth;
2. concentration/hit probability;
3. Gaussian turbulence at every time step;
4. spatially varying wind along a trajectory;
5. filament growth;
6. buoyancy;
7. GADEN's tangential wall deflection.

These are adaptation targets, not already-solved physics.

## 6. Why this strengthens M6

The transfer hierarchy is now:

### Pretrained
- free/interior volume representation;
- SDF/boundary-direction representation;
- direction-conditioned finite particle displacement;
- collision-aware geometry interaction.

### Gas-specific small adaptation
- source injection;
- wind field semantics;
- concentration/hit-map decoding.

### Higher-fidelity residual to learn from GADEN
- turbulent stochasticity;
- wall deflection;
- plume intermittency;
- finer transport effects.

This is substantially more defensible than treating GeoPT as a generic pretrained neural operator.

## 7. New required ablation

If G1 is positive, compare against a geometry-only pretrained/random control.

The key claim is that **dynamics-lifted constrained-walk pretraining**, not merely ShapeNet geometry exposure, provides the low-data advantage.

If that distinction cannot be demonstrated, narrow the paper claim accordingly.

Status:

`STRONG MECHANISTIC PRIOR — STILL REQUIRES GEO-PT-vs-SCRATCH SOURCE-RANK EVIDENCE`.
