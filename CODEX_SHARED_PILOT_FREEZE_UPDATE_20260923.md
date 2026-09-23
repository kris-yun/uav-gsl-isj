# CODEX Shared-Pilot Freeze Update — House02 S1-S4 fixed

Date: 2026-09-23  
Branch: `research/main-innovation-search-parallel-v1`

## Source positions are now frozen

Read:

- `evidence/main_innovation_search/SHARED_PILOT_H02_SOURCE_FREEZE_20260923.md`
- `evidence/main_innovation_search/SHARED_PILOT_H02_SOURCE_POSITIONS_20260923.tsv`

Frozen XY:

- S1 = (-2.242730, -1.600880)
- S2 = ( 2.557270,  2.599120)
- S3 = (-4.342730,  4.099120)
- S4 = (-4.342730, -6.400880)

Preferred fixed source height:

- z = 0.20 m.

Selection was source-blind deterministic maximin over free cells with >=0.9 m nearest-obstacle-center margin.

Before generation, verify each point is free in the actual 3-D GADEN environment at z=0.20.

If invalid, use the predeclared nearest-valid replacement rule in the freeze document. Do not choose replacements based on gas/source-localization results.

## One-source benchmark

Use S1 for the first GADEN-RT cost benchmark if 3-D valid.

## Wind factor remains pending

Do not invent W2.

On the VM, audit House02 for:

1. a second existing physical CFD/GADEN wind configuration;
2. otherwise a distinct physical replayable wind regime/sequence;
3. only if neither exists, propose a source-blind scalar speed transform W2=gamma W1 that preserves vector-field topology.

If option 3 is required:
- freeze gamma before plume generation;
- justify it using a physical/runtime scale, not source truth.

Never create W2 by arbitrary rotation through indoor walls.

Commit W1/W2 provenance before generating the 16-run batch.
