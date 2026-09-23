# CODEX M4 C0 TASK — Controlled Source Intervention Pilot

Branch: `research/causal-compositional-plume-world-model-v1`

Read first:

- `evidence/causal_compositional_plume_world_model_v1/C0_SOURCE_INTERVENTION_PILOT_CHARTER_20260923.md`
- `evidence/causal_compositional_plume_world_model_v1/C0_HOUSE02_SOURCE_POSITIONS_PREREG_20260923.md`
- `reference/select_m4_c0_source_positions.py`

## Objective

Generate the smallest controlled House02 source-intervention dataset needed to test M4.

Do NOT build a large causal world model yet.

## Step 1 — validate preregistered source points

Validate S1–S4 against the actual House02 3-D GADEN occupancy at the fixed benchmark source-height plane.

Do not manually replace invalid points.

If any fail:
- use a deterministic 3-D geometry-only selector;
- commit its code/output BEFORE generation.

## Step 2 — generation

Reuse the same generation contract as:

`reference/generate_hcmc_v1_realizations.sh`

Freeze:
- House02 occupancy;
- canonical wind directory;
- gas type;
- gas simulation parameters;
- simulation length;
- all non-source settings.

Change only:
- source x/y;
- stochastic plume seed.

Use 4 sources × 2 predeclared seeds.

Start with 120–180 s, not 1000 s.

## Step 3 — compact export

Prefer online/compact export:
- source label;
- seed;
- timestamp;
- sensor-height concentration/hit field;
- wind;
- occupancy/geometry metadata.

Optionally export filament states for M5 at negligible extra cost.

Record generation wall-clock, disk, RAM.

## Step 4 — C0 minimal models

Only after data generation passes.

Compare matched-capacity small models:

A. monolithic source-conditioned forward:
[
F(S,W,O)	o H
]

B. compositional source-injection form:
[
H_{m env}=E(W,O),quad H_s=D(H_{m env},Q_s).
]

No large world model.

Freeze architecture/hyperparameters source-blind.

Train S1–S3; hold out S4 completely.

## Step 5 — decision

Primary preliminary test:
- held-out S4 field/hit prediction.

Hard downstream test:
- PMFS candidate replay;
- truth-containing source-candidate rank.

M4 only advances if the compositional model beats the matched monolithic baseline on held-out intervention and source rank.

Commit after:
1. 3-D validation;
2. generation;
3. C0 model comparison.
