# M6 G1-B compact pilot protocol

Date: 2026-09-23  
Status: **FROZEN BEFORE NEW PILOT GENERATION**

## Gate purpose

Generate the smallest source-blind high-fidelity target bank needed for the
pretrained-vs-scratch hard gate. This bank is not a closed-loop run and is not
used to tune source candidates after truth is inspected.

## Frozen intervention table

The exact 12 House02 source positions and `train/val/test` split are the
pre-registered geometry-only table in
`G1_HOUSE02_PILOT_SOURCE_POSITIONS_20260923.csv` (8 train, 2 validation, 2
test). All sources use `z_source=0.20 m`; the table is not edited after field
generation. Two process-level stochastic seeds are generated for every row:
`2026092311` and `2026092312`. The audited seeded GADEN binary and its source
patch are recorded in `G1A_COST_RAW_20260923/`.

## Fixed environment and target

- House02 occupancy: `OccupancyGrid3D.csv`, SHA256 recorded in G1-A evidence.
- Wind: fixed House02 `3,5-1_fast`, files `wind_iteration_0..10`.
- Free-token geometry: `G1_HOUSE02_GRID_GEOMETRY_20260923.csv`, SHA256
  `F30C7DE2EA892120B70411EDB7187F2769246896152F9BB9B8181E15F749A397`;
  1053 rows, exactly 631 `Free` rows. The CSV contains no gas posterior.
- Source plane: `z_source=0.20 m`; sensor plane: `z_sensor=0.30 m`.
- Hit rule: strict `C > 0.1`; horizon 300 s; burn-in 50 s; 1 Hz samples
  at integer times `t=50,...,299` (250 samples).
- Frozen GADEN params: butane; `deltaTime=0.1`; wind step 1.0 s; filament
  center 10 ppm; initial sigma 10 cm; growth gamma 15 cm2/s; noise 0.01;
  release rate 7 filaments/s; wind loop `[1,10]`.

## Compact output schema

Each `source_id/seed` directory contains only `metadata.json`,
`hit_samples_u8.bin` with shape `(250,631)`, primary
`hit_frequency_f32.bin` with shape `(631,)`, mean/variance concentration
diagnostics, and a fixed-window diagnostic map. A post-generation manifest
hashes every file. No filament dumps, full concentration volumes, or ROS/PMFS
loop outputs are written.

## Split and truth-blind rule

Generation uses the frozen table before any model, source-rank, or truth-based
metric is read. Test rows are not used for optimizer selection, adapter choice,
or early stopping. Only after the bank and hashes are complete may G1-C and
G1-D run.

## Independent realization rule

`GADEN_RNG_SEED` is set before each sampler process. A same-seed rerun must be
byte-identical; the second seed must differ for at least one compact output
hash. Source, binary, and patch hashes remain attached to the bank. If the
seeded binary cannot be matched to the audited source patch, the bank is HOLD.

## Hard stop

This protocol permits G1-B data generation only. It does not authorize model
training, closed-loop replay, source-rank inspection before freeze, or parameter
retuning after seeing targets.
