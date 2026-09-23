# M6 G1 House02 source-plane protocol — 2-D PMFS target, fixed z nuisance

Date: 2026-09-23  
Status: **FROZEN BEFORE NEW GADEN GENERATION**

## Decision

For the House02 G1 pilot, all newly generated source interventions use:

`SOURCE_Z = 0.20 m`

This is **not** treated as an inferred source coordinate.

## Why this is scientifically legitimate

Official PMFS candidate-source simulation is 2-D.

Its `SimulationSource` stores/samples a `Vector2` source point and, for quadtree candidates, samples only within the candidate rectangle in x/y.

Thus the PMFS localization target is:

`source = (x,y)`

not:

`source = (x,y,z)`.

The existing House02 benchmark runner fixes:

`SOURCE_Z="0.20"`

for the House02 GADEN scenario.

Therefore z is interpreted as a **House-specific known experimental nuisance/plane**, held constant while x/y are varied.

## G1 generation rule

For every frozen House02 train/validation/test x/y source position:

`z = 0.20 m`.

Do not vary z during M6 G1.

Do not train a model to infer z.

Do not use z as an output label.

## Claim boundary

M6 G1 evaluates **2-D gas-source localization** under a fixed source-height plane.

Any future claim about 3-D source localization requires a separate experiment with source-height variation and is outside this branch.

## Why this is not truth tuning

The rule is fixed from the benchmark/environment contract before generating the new source-position dataset.

All candidate x/y positions use the same z.

No z value is selected by:
- source-rank performance;
- gas likelihood;
- candidate score;
- endpoint error.

## Caveat

The existing independent realization logs show House-specific source heights differ across Houses.

Therefore do not generalize `z=0.20` to House01/House03.

Each House requires its own predeclared fixed-plane contract if later included.

Status:

`HOUSE02 SOURCE PLANE FROZEN: z=0.20 m`.
