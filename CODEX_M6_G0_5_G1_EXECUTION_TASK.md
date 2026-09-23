> **PMFS CANDIDATE-SEMANTICS UPDATE:** Also read `evidence/geopt_physics_foundation_pmfs_v1/G0_9_QUADTREE_SOURCE_INTEGRATION_20260923.md`. In the hard source-rank replay, a PMFS quadtree candidate is a source **region**, not a center point. Primary M6 inference must average the point-conditioned forward model over the fixed 2×2 Gauss-Legendre quadrature points of each candidate rectangle. Center-only is diagnostic/ablation only and must not be selected by truth rank.

> **PRETRAINING-SEMANTICS UPDATE:** Also read `evidence/geopt_physics_foundation_pmfs_v1/G0_7_PRETRAINING_SEMANTICS_ALIGNMENT_20260923.md`. Preserve the pretraining sign/convention: wall direction points from free point toward nearest boundary; dynamics4 is local move direction plus normalized advective step length; use a consistent y-up coordinate transform for geometry/wind/source.\n\n> **DYNAMICS-PROMPT UPDATE (2026-09-23):** Read `evidence/geopt_physics_foundation_pmfs_v1/MECHANISTIC_BRIDGE_GEOPT_RANDOM_WALK_TO_PMFS_FILAMENT_20260923.md`. GeoPT pretraining conditions on `[direction_x,direction_y,direction_z,step_length]`. For G1, prefer the physically aligned gas prompt `[wind_unit_vector, geometry_scaled_advective_displacement]` with a predeclared protocol-derived time horizon. Raw-speed encoding may be retained only as an ablation.\n\n# CODEX M6 EXECUTION TASK — GeoPT Foundation Transfer

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Read first

Read these in order:

1. `evidence/geopt_physics_foundation_pmfs_v1/CRITICAL_INTERFACE_CORRECTION_POS3_PLUS_FX11_20260923.md`
2. `evidence/geopt_physics_foundation_pmfs_v1/G0_5_RUNTIME_FEASIBILITY_20260923.md`
3. `evidence/geopt_physics_foundation_pmfs_v1/NOVELTY_AUDIT_V1_20260923.md`
4. `evidence/geopt_physics_foundation_pmfs_v1/G1_LOW_DATA_FOUNDATION_TRANSFER_CHARTER_20260923.md`
5. `evidence/geopt_physics_foundation_pmfs_v1/G1_HOUSE02_PILOT_PREREGISTRATION_20260923.md`

Do not use any older shorthand that treats 11 dimensions as the total GeoPT preprocess input.

Exact released contract:
- `pos3` is passed separately;
- `fx11` contains geometry7 + dynamics4;
- GeoPT preprocess receives 14 dimensions after concatenation.

## Stage 1 — finish G0.5 actual checkpoint load

Use official:
- repo: `Physics-Scaling/GeoPT`;
- checkpoint: `GeoPT/GeoPT_Pretrained_Models / GeoPT_8layers.pt`.

Required evidence:
- checkpoint SHA256;
- exact model args;
- total checkpoint tensors;
- loaded tensors;
- skipped tensors with reason;
- checkpoint parameter count;
- loaded parameter count;
- actual load fraction.

Expected architecture-derived internal coverage is near 99.93%.
Do not force-load incompatible shapes.

Commit immediately:
`evidence/geopt_physics_foundation_pmfs_v1/G0_5_ACTUAL_CHECKPOINT_LOAD_20260923.md`

## Stage 2 — one real Native House02 token smoke

Construct House02 tokens from recovered Native inputs, not old R2 wind:

- pos3 = xyz;
- fx11 =
  [x,y,z,wall_SDF,wall_dir_x,wall_dir_y,wall_dir_z,
   wind_dir_x,wind_dir_y,wind_dir_z,wind_speed].

Requirements:
- use GADEN ground-truth wind;
- preserve official GeoPT normalization/alignment as far as applicable;
- record token count;
- record geometry transform;
- record wind normalization;
- frozen checkpoint forward;
- runtime/RAM/VRAM.

No plume training yet.

Commit immediately.

## Stage 3 — validate source-height protocol

Before generating any new source:
- locate the benchmark/simulator rule that defines allowed source z;
- prove whether a fixed source plane is part of the experiment protocol.

Do NOT copy z from the known House02 truth source just because it is available.

If there is no fixed source-plane rule:
- STOP;
- write a source-blind z policy;
- commit it before generation.

## Stage 4 — one-source GADEN generation benchmark only

Use the first frozen TRAIN source from:

`G1_HOUSE02_PILOT_SOURCE_POSITIONS_20260923.csv`

Do not use validation/test yet.

Generate two independent plume realizations only if cheap, otherwise start with one.

Prefer current GADEN core / RunningSimulation:
- reuse House02 environment + wind;
- change only source position;
- `saveResults=false`;
- sample concentration at the PMFS sensor-height grid at predeclared times.

Record:
- setup time;
- simulation wall-clock per 300 s physical time;
- CPU/GPU;
- RAM;
- output size;
- number of temporal samples;
- whether wind preprocessing was reused.

Also export enough metadata to reproduce:
- source xyz;
- wind config hash/path;
- gas params;
- random seed;
- grid coordinates;
- threshold used to convert concentration to hit.

Commit benchmark before generating more sources.

## Stage 5 — generation GO/NO-GO

GO only if the one-source benchmark makes the preregistered 12 sources × 2 plume seeds practical.

If GO:
- generate exactly the frozen source table;
- preferred new stochastic seeds: 11 and 12 if compatible with GADEN's seed interface;
- do not modify train/val/test coordinates.

If NO-GO:
- do not silently shrink/alter the test split;
- report HOLD and generation cost;
- return to the main-search branch.

## Stage 6 — G1a strict frozen representation probe

Only after Stage 5 data exists.

Compare:

A. Native PMFS  
B. same Transolver architecture, random/scratch weights  
C. official GeoPT pretrained backbone

First probe:
- freeze backbone;
- train only gas/source adapter + output head;
- identical training samples, optimizer budget and stopping rule.

Use the corrected source adapter code:
`probe_geopt_source_injection_adapter.py`

Important:
the current adapter is an **early post-preprocess injection** and reruns the blocks per source candidate.
Do not optimize runtime yet.

Run nested low-data subsets:
- 2 training sources;
- 4 training sources;
- 8 training sources.

Do not use validation/test truth to choose the subset or architecture.

## Stage 7 — hard source-rank replay

Only after models freeze.

Use:
- same test source positions;
- independent plume realization;
- same sparse observation locations;
- same candidate-source set;
- same source update rule.

Report:
- truth-containing candidate rank;
- rank for Native PMFS;
- rank for Scratch Transolver;
- rank for GeoPT transfer.

No endpoint-only rescue.

## Stage 8 — destructive nulls if positive

Minimum:
- wind shuffle;
- source-injection label shuffle;
- random backbone.

If the M6 advantage survives these nulls, do not advance.

## Git discipline

Commit after every stage.

Do not overwrite old R2/baseline evidence.
Do not tune using truth.
Do not combine M3/M4/M5 modules into this branch.

## Decision

At the end write:

`evidence/geopt_physics_foundation_pmfs_v1/M6_G1_DECISION_20260923.md`

with exactly one:
- `ADVANCE`
- `HOLD`
- `NO-GO`

and the truth-source-rank evidence supporting it.
