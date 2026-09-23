# CODEX M6 G0.5/G1 TASK — Physics Foundation Transfer

Branch:
`research/geopt-physics-foundation-pmfs-v1`

Read:

1. `evidence/geopt_physics_foundation_pmfs_v1/CANDIDATE_M6_DYNAMICS_LIFTED_PHYSICS_FOUNDATION_PMFS_20260923.md`
2. `evidence/geopt_physics_foundation_pmfs_v1/G0_INTERFACE_AUDIT_20260923.md`
3. `evidence/geopt_physics_foundation_pmfs_v1/G0_5_RUNTIME_REAL_HOUSE_PROBE_20260923.md`
4. `evidence/geopt_physics_foundation_pmfs_v1/G1_LOW_DATA_FOUNDATION_TRANSFER_HARD_GATE_20260923.md`

## Stage G0.5-B — actual official checkpoint load

Use official:

- repo: `Physics-Scaling/GeoPT`;
- HF model repo: `GeoPT/GeoPT_Pretrained_Models`;
- checkpoint: `GeoPT_8layers.pt`;
- expected SHA256:
  `c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2`.

Verify checksum.

Instantiate exact official downstream configuration:

- Transolver;
- unstructured;
- space_dim=3;
- fun_dim=11;
- n_hidden=256;
- n_heads=8;
- n_layers=8;
- mlp_ratio=2;
- slice_num=32.

Use the official filtered loading logic.

Report:

- checkpoint tensor count;
- model tensor count;
- matched tensors;
- skipped tensors;
- mismatches with names/shapes;
- loaded parameter count;
- total model parameter count;
- loaded parameter percentage.

Expected scientific criterion:

- input projection + internal blocks must load;
- task/output head may be excluded.

If substantial internal layers cannot load, mark M6 HOLD/NO-GO before training.

## Real-House frozen forward

Use:

`evidence/geopt_physics_foundation_pmfs_v1/build_pmfs_geopt_features.py`

Construct one **recovered Native** House geometry + ground-truth wind tensor.

Do not use historical GMRF wind for any scientific claim.

Run actual pretrained weights.

Record:
- token count;
- feature shapes;
- output shape;
- CPU/GPU;
- wall-clock;
- peak RAM/VRAM;
- hashes of input artifacts.

This stage is interface proof only.

## Stage G1-PILOT — no large training run

Only after G0.5-B passes.

### Data

Use the smallest honest multi-source GADEN pilot.

Prefer:
- one House;
- 4 source positions;
- 2 independent plume seeds/source;
- same physical wind first;
- reserve at least one source position completely unseen.

If an existing multi-source spatial field dataset already satisfies this, reuse it.

Do not use robot-path-only ppm as dense field supervision.

### Source adapter

Preserve the pretrained raw input projection.

Use one fixed tiny source adapter (<1% backbone parameters) after environment embedding.

Do not search many adapter designs on truth.

### Mandatory arms

A. Native PMFS  
B. GeoPT architecture, random initialization  
C. official pretrained GeoPT + same source adapter  
D. small gas-specific baseline

### Low-data fractions

Use nested source-blind subsets:

- 5%;
- 10%;
- 25%;
- 50%;
- 100%.

2.5% is optional only if sample count makes it meaningful.

### First G1 endpoint

Before PMFS replay:
- held-out source field error;
- convergence/data-efficiency curve;
- pretrained-vs-random paired comparison.

The foundation thesis gets a positive signal only if C materially beats B in the low-data regime.

## Hard source-localization gate

Only after a positive low-data signal:

- freeze all models;
- use same PMFS candidate source set;
- same observations;
- same source-update contract;
- compare truth-containing candidate rank.

The scientific comparison is:

[
	ext{pretrained GeoPT}
quad vs quad
	ext{same architecture random-init}.
]

If pretraining does not improve source rank on independent plume realizations, M6 is not the main innovation.

## Nulls

Mandatory:
- random-init backbone;
- wind-prompt shuffle;
- geometry SDF/direction corruption;
- source-label/source-adapter shuffle.

## Prohibitions

Do not:
- change GeoPT hidden size to rescue it;
- add OFM/M7 causal/operator modules before M6 passes;
- tune source adapter per House;
- select a checkpoint by truth-source rank;
- claim foundation transfer from field MSE alone.

## Git checkpoints

1. `evidence:` checkpoint-byte verification/load coverage;
2. `evidence:` real-House pretrained forward;
3. `evidence:` G1 data manifest/split;
4. `evidence:` pretrained-vs-random low-data result;
5. `decision:` source-rank result / M6 ADVANCE-HOLD-NO-GO.
