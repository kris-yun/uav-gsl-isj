# CODEX M7 O0 TASK — No Neural Training Yet

Branch:
`research/testtime-compositional-plume-operators-v1`

Read in this order:

1. `evidence/testtime_compositional_plume_operators_v1/CANDIDATE_M7_TESTTIME_COMPOSITIONAL_PLUME_OPERATORS_20260923.md`
2. `evidence/testtime_compositional_plume_operators_v1/REFINEMENT_EXACT_PHYSICS_RESIDUAL_DICTIONARY_20260923.md`
3. `evidence/testtime_compositional_plume_operators_v1/O0_ANALYTICAL_SPLITTING_CHARTER_20260923.md`

Then execute O0 only.

## Critical prohibition

**Do not train DISCO/FNO/PINO/GeoPT/OFM or any neural model in O0.**

O0 exists to decide whether neural mechanism operators are justified at all.

## Stage 1 — export proof

Use one existing House02 high-fidelity GADEN realization.

Prefer playback of an already generated realization rather than regenerating a plume.

Use:

`evidence/testtime_compositional_plume_operators_v1/export_gaden_playback_slices.py`

if the installed `gaden_core/gaden_py` environment can directly read the realization.

If the historical realization/config cannot be opened by the current gaden_core API:
- use the existing canonical GADEN playback ROS stack to query the same concentration/wind fields;
- document the exact route;
- do not rebuild or approximate the field from robot-path observations.

Export 20–40 predeclared sensor-height snapshots after warmup.

Commit:
- manifest;
- iteration list;
- hashes/provenance;
- small export or checksums if the field artifact is too large;
- an `O0_EXPORT_PROOF.md`.

## Stage 2 — analytical split

Run:

`evidence/testtime_compositional_plume_operators_v1/run_o0_analytical_split.py`

or a corrected version if a documented API/format issue is found.

Required variants:
- persistence;
- advection;
- advection + wall blocking;
- diffusion;
- advection + diffusion;
- Strang advection/diffusion + wall handling;
- wind-shuffle destructive null.

Diffusivity may only be chosen from a predeclared panel on a calibration prefix and must be frozen before evaluation transitions.

Exclude a predeclared source-neighborhood radius from transport-error scoring so source-injection conversion does not become a hidden tuning parameter.

## Stage 3 — decision

Report:
- held-out relative L2;
- log concentration error;
- centroid error;
- wind-shuffle degradation;
- residual spatial/temporal structure;
- whether parameters transfer to a second independent plume realization.

Decision:

### PASS
Only if:
- physical split beats persistence;
- correct wind matters;
- obstacle handling matters;
- residual is smaller and structured;
- frozen parameters transfer to a second plume realization.

### NO-GO
If:
- persistence is competitive/better;
- wrong wind does not hurt;
- residual is unstructured;
- every case needs its own diffusion parameter.

## Git discipline

Commit immediately after:
1. export proof;
2. analytical metrics;
3. independent-realization check;
4. final O0 decision.

Do not use source truth rank in O0.

Do not continue to neural training unless O0 is PASS.
