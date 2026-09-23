# M4-v2 G3 — Unknown-House Transfer Hard Gate

Date: 2026-09-23  
Status: **REQUIRED BEFORE ANY MAIN-LINE CLAIM**

## Why the existing C0.5 is insufficient

C0.5 tests source x wind recombination inside one House. That can falsify a local compositionality claim, but it does not establish operation in an unfamiliar real environment. A same-geometry holdout is not an unseen-House test.

## Frozen deployment test

For each preregistered leave-one-House-out fold:

1. Train the source-injection and transport components on two Houses only.
2. Hold the third House out by occupancy/geometry hash.
3. Use a physical wind family in the held-out House that is not used to fit the corresponding training fold.
4. Use two independent plume seeds in the held-out House.
5. Do not use held-out plume fields, source truth, sensor traces, or final rank to choose architecture, normalization, source locations, or thresholds.
6. Geometry, wind, and candidate-source coordinates may be measured at deployment; target-House plume labels may not be used for zero-shot selection.

The minimum acceptable study has two independent held-out Houses. Three leave-one-House-out folds are preferred.

## Required comparison

- Native PMFS;
- matched-capacity monolithic forward model;
- operator-compositional model `Q_s=I_S(s); C=T_{W,O}(Q_s)`;
- additive source-plus-transport control;
- source-label, wind-label, source-module, and transport-module nulls.

## Hard endpoints

- truth-containing source-candidate rank on the held-out House;
- paired rank change against Native and monolithic controls;
- localization error and time with the same observation budget;
- stability across both held-out plume seeds;
- compute and target-data cost.

Field MSE is secondary. A field fit without improved source rank is not a main-line result.

## Decision rule

`ADVANCE` only if the compositional model improves rank over the matched monolithic and Native controls on both held-out seeds in at least two held-out Houses, while all nulls remove the advantage.

`HOLD` if a valid held-out House, wind family, independent seed, or spatial field is unavailable.

`NO-GO AS MAIN` if the model ties/reverses, needs target-House plume tuning, or improves only field MSE.

The current same-House C0.5 inventory is an infrastructure precondition only; it cannot satisfy this gate.
