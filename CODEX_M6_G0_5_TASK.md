# CODEX M6 G0.5 TASK — GeoPT Frozen-Backbone Feasibility

Branch: `research/geopt-physics-foundation-pmfs-v1`

Read first:

`evidence/geopt_physics_foundation_pmfs_v1/G0_INTERFACE_AUDIT_20260923.md`

## Objective

Verify the actual official checkpoint transfer and run one frozen-backbone House02 forward pass.

Do NOT train plume data yet.

## Official model

- GitHub: `Physics-Scaling/GeoPT`
- HF checkpoint: `GeoPT/GeoPT_Pretrained_Models/GeoPT_8layers.pt`
- expected checkpoint SHA256:
  `c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2`

Official config:
- Transolver;
- 8 layers;
- hidden 256;
- 8 heads;
- slice_num 32;
- mlp_ratio 2;
- `space_dim=3`;
- `fun_dim=11`.

## Expected architecture check

From official source reconstruction:

- pretrained 9-D-head params: 3,865,673;
- 1-D downstream-head params: 3,863,617;
- predicted loaded backbone params under official `mlp2/ln_3` exclusion:
  3,862,848;
- expected pretrained coverage ≈ 99.927%.

These are predictions. Record the ACTUAL values.

## House02 input

Use the recovered/native House02 geometry/wind artifacts available on VM.

Construct free-space tokens:

### position
[
[x,y,z]
]

### 7-D geometry feature
[
[x,y,z,mathrm{SDF},d_x,d_y,d_z]
]

where SDF/direction refer to nearest wall/obstacle boundary.

### 4-D dynamics field
[
[hat w_x,hat w_y,hat w_z,|w|].
]

Thus:
- `fx` = 11-D;
- model additionally receives 3-D position;
- pretrained first MLP sees 14 dimensions exactly as official GeoPT.

Use ground-truth/recovered wind, not the old R2 GMRF field.

## Required output report

Create:

`evidence/geopt_physics_foundation_pmfs_v1/G0_5_ACTUAL_CHECKPOINT_HOUSE_FORWARD_20260923.md`

Report:

1. exact GeoPT commit;
2. exact checkpoint SHA256;
3. checkpoint file size;
4. actual tensor/key count;
5. actual loaded tensor/key count;
6. actual loaded parameter count and percent;
7. missing/unexpected keys;
8. House02 token count;
9. feature min/max and finite checks;
10. CPU/GPU device;
11. frozen forward latency;
12. peak memory;
13. output tensor shape;
14. finite output check.

No accuracy/source-rank conclusion yet.

## Fail conditions

Demote M6 if:
- checkpoint hash mismatch;
- actual load coverage materially below expected due structural mismatch;
- House geometry/wind cannot be represented without changing pretrained input layer;
- frozen forward is impractical.

Commit/push immediately after G0.5.
