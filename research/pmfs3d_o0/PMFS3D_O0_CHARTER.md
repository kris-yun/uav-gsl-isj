# PMFS3D-O0 — 3D transport information recovery pilot

Date: 2026-10-01
Status: DEVELOPMENT ONLY / ONE HOUSE / NO OUTDOOR CLAIM

## Scientific question

Does the fixed-height 2-D transport projection used by native PMFS discard source-discriminative information that is present in the 3-D GADEN transport field?

This pilot does **not** claim that 3-D PMFS is already the final method. It is an oracle/mechanism gate before any GenDA/world-model/3-D PMFS implementation.

## Why this test now

Native PMFS stores source-forward filament position and wind as `Vector2`; the source map is a 2-D probability grid. Earlier House02 audits already showed strong source-dependent vertical transport and horizontal divergence between free-3D and forced-fixed-height streamlines. The current T02 audit further showed that source information is primarily spatial rather than temporal. Therefore the next cheapest falsifiable question is whether restoring vertical transport improves *source discrimination*, not merely field MSE.

## Fixed development data

House02 only, already opened development data.

- occupancy: canonical `House02/OccupancyGrid3D.csv`
- wind: canonical `3,5-1_fast`
- source S1: `(-2.242730141, -2.200880051, 0.2)`
- source S2: `(-4.342730045,  2.899120331, 0.2)`
- both sources have identical fixed source height `z=0.2 m`
- full-3D GADEN plume realizations A/B already exist in the frozen C0.5 bank
- target representation is the static compositional spatial concentration profile at `z=0.2 m`, motivated by the later T02 result that stable source information is primarily spatial.

No H01, H03, confirmation, or closed loop is opened by this pilot.

## Counterfactual 2-D projection

Do **not** modify the target plume.

Starting from the exact canonical 3-D GADEN wind sequence, construct a projected-2D wind field by:

1. taking `(u,v)` at the sensor/source plane `z=0.2 m`;
2. copying this same `(u,v)` slice to every z layer;
3. setting `w=0` everywhere;
4. preserving the original binary wind file format, occupancy, simulator settings, source coordinates, and RNG seeds.

This creates a vertically extruded fixed-height-flow counterfactual. It is intentionally closer to PMFS's information content than simply setting `w=0`: horizontal flow can no longer change when a filament visits a different height.

It is still not a byte-identical implementation of native PMFS, so the only authorized claim is about **information lost by vertical transport projection**.

## Source-discrimination protocol

Reality/target is always the original full-3D GADEN plume.

For each target source/replicate, use the opposite plume replicate as the candidate template so no target is compared to itself:

- target S1/A -> candidate templates S1/B vs S2/B
- target S1/B -> candidate templates S1/A vs S2/A
- target S2/A -> candidate templates S2/B vs S1/B
- target S2/B -> candidate templates S2/A vs S1/A

Two candidate-template arms are compared:

- `FULL3D`: existing full-3D GADEN candidate templates;
- `PROJECTED2D`: newly generated candidate templates with the projected-2D wind counterfactual.

Each concentration cube is averaged across the 10 frozen time snapshots, restricted to free cells, and normalized to unit mass. Candidate similarity uses Hellinger affinity:

`A(p,q) = sum_i sqrt(p_i q_i)`.

Truth margin:

`margin = affinity(target, true-source-template) - affinity(target, false-source-template)`.

This removes total concentration amplitude and tests the spatial source fingerprint isolated by T02.

## Frozen decision

- `PMFS3D_O0_REFERENCE_3D_NOT_STABLE`: FULL3D fails any of the 4 cross-replicate source rankings. Stop; the reference itself is too unstable.
- `PMFS3D_O0_VERTICAL_INFORMATION_STRONG`: FULL3D is 4/4 correct, at least 3/4 margins improve over PROJECTED2D, median margin gain is positive, and either PROJECTED2D has <=2/4 correct rankings or median absolute margin gain >=0.05.
- `PMFS3D_O0_VERTICAL_INFORMATION_PROMISING`: FULL3D is 4/4 correct, at least 3/4 margins improve, and median margin gain >0, but the strong-effect condition is not met.
- `PMFS3D_O0_NO_VERTICAL_INFORMATION_GAIN`: otherwise.

After any decision: STOP. No parameter tuning, no second wind context, no PMFS integration, no GenDA training.

## Interpretation boundary

A PASS/PROMISING result would establish only:

> In one fixed-z House02 development context, source-discriminative spatial structure is better preserved by full 3-D transport than by a sensor-height 2-D wind projection.

It would justify the next experiment: integrate a true 3-D oracle forward model into the PMFS candidate-ranking replay, then test sparse 3-D wind assimilation.

It would **not** establish outdoor generalization.

The intended deployment ladder remains:

House mechanism -> PMFS source-rank oracle -> sparse/deployable 3-D wind belief -> unknown/partial-map planner -> outdoor open/semi-open simulation -> hardware-in-loop -> controlled lakeshore flight.
