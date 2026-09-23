> **SOURCE-PLANE RESOLUTION:** The House02 source plane is now frozen to `z=0.20 m` as a known House-specific nuisance constant for the 2-D PMFS localization task. See `G1_HOUSE02_FIXED_SOURCE_PLANE_20260923.md`. This supersedes the earlier HOLD wording below.\n\n# M6 G1 House02 pilot source-position preregistration

Date: 2026-09-23  
Status: **FROZEN BEFORE MODEL TRAINING / SOURCE-RANK REVEAL**

## Purpose

Pre-register the source positions for the first low-data GeoPT-transfer pilot.

These positions were selected using **environment geometry only**.

No use was made of:
- gas probability;
- source posterior;
- truth-source coordinates;
- candidate source score;
- endpoint error;
- any M6 model output.

## Geometry source

The 27×39 House02 PMFS occupancy grid was used only for:
- free/obstacle classification;
- grid coordinates;
- world x/y coordinates.

Historical R2 wind and gas values are scientifically irrelevant to this selection.

## Eligibility rule

A source location is eligible iff:
- its PMFS cell is free;
- Euclidean distance-transform clearance from the nearest obstacle is at least 0.6 m.

This leaves 398 eligible cells from 631 free cells.

## Deterministic selection algorithm

1. Compute the centroid of all eligible x/y coordinates.
2. First training location = eligible cell nearest that centroid.
3. Select the remaining training locations by farthest-point sampling:
   maximize minimum Euclidean distance to already selected training locations.
4. After 8 training sources freeze, select two **test** locations by the same farthest-from-training rule.
5. Then select two **validation** locations farthest from the already frozen train+test set.
6. Ties are broken lexicographically by `(grid_i, grid_j)`.

No random seed is required.

The exact frozen positions are in:

`G1_HOUSE02_PILOT_SOURCE_POSITIONS_20260923.csv`

## z-coordinate rule

The x/y positions are frozen here.

Do **not** set z from the known House02 truth source.

Use the fixed source plane already defined by the simulator/benchmark protocol if one exists and record the config line proving it.

If the protocol does not define a source plane, STOP and define a source-blind z policy before generation.

## Plume realizations

For each source location generate two independent plume realizations with predeclared new simulator seeds.

Preferred seed labels: 11 and 12, if those map cleanly to the GADEN stochastic seed interface.

If the simulator uses a different seed convention, document the mapping before running.

## Split discipline

- train: 8 sources;
- validation: 2 sources;
- test: 2 sources.

The test source fields must not be used:
- for optimizer selection;
- for adapter width selection;
- for source-kernel scale selection;
- for early stopping;
- for deciding whether to unfreeze GeoPT blocks.

## Hard test

After models freeze, test sources are used for:
1. held-out plume/hit-map prediction;
2. independent-realization sparse observation replay;
3. truth-containing PMFS source-candidate rank.

This file is a preregistration artifact. Do not edit the coordinates after seeing model results.
