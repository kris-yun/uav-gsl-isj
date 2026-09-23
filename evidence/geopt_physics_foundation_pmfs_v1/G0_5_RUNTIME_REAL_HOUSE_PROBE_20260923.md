# G0.5 Runtime / Real-House Interface Probe

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Decision

`G0.5-A = PASS — architecture/runtime/real-House token interface`

`G0.5-B = HOLD — actual checkpoint-byte load still to be run on Codex/VM because this worker's shell DNS cannot resolve Hugging Face`

Do not conflate the two.

## 1. Official public artifacts independently verified

Official Hugging Face repository:

`GeoPT/GeoPT_Pretrained_Models`

contains:

- `GeoPT_8layers.pt`
- size: approximately 15.6 MB;
- published SHA256: `c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2`;
- Xet hash: `167964db1093a6390f1b5dc33db49688dba30cf4b9f6219e722005ecc38beb74`;
- `config.json`.

Official config:

- architecture: Transolver;
- coord_dim: 3;
- sdf_dim: 1;
- normal_dim: 3;
- condition_dim: 4;
- hidden_dim: 256;
- num_layers: 8;
- num_heads: 8;
- slice_num: 32;
- mlp_ratio: 2.

Official downstream shell script confirms:

- `space_dim=3`;
- `fun_dim=11`;
- `n_hidden=256`;
- `n_heads=8`;
- `n_layers=8`;
- `mlp_ratio=2`;
- `slice_num=32`;
- `finetune_name=GeoPT_8layers`.

## 2. Important exact-code contract

The official JSON describes the physical feature semantics as

[
3 + 1 + 3 + 4 = 11.
]

However the official fine-tuning implementation passes:

- `x[:, :, :3]` separately as model coordinates;
- a full 11-D `fx` containing:
  - xyz;
  - SDF;
  - boundary direction;
  - 4-D dynamics prompt.

The Transolver then concatenates coordinates and `fx`.

Therefore the actual first learned projection receives:

[
3 + 11 = 14
]

channels.

The official-compatible gas adaptation must preserve this exact code contract.

## 3. Reconstructed official 8-layer parameter count

A faithful local reconstruction of the released unstructured Transolver architecture gives:

- total parameters: **3,865,673**;
- FP32 parameter bytes: **15,462,692 bytes = 14.746 MiB**;
- final `ln_3 + mlp2` output-head parameters: **2,825**;
- fraction outside the final head: **99.9269%**;
- first input projection weight shape: **(512, 14)**.

The theoretical FP32 model size is highly consistent with the official ~15.6 MB checkpoint artifact.

This is strong architecture-consistency evidence, but **not a substitute for loading the actual checkpoint bytes**.

## 4. Scaling/runtime probe

CPU, 4 threads, no GPU.

Using the official unstructured Physics-Attention structure:

| tokens | output | forward time |
|---:|---:|---:|
| 626 | [1,626,9] | 0.066 s |
| 10,000 | [1,10000,9] | 0.892 s |
| 50,000 | [1,50000,9] | 11.15 s |

Peak RSS at the largest probe was ~629 MiB.

Thus PMFS-scale 2-D token sets are computationally small.

## 5. Real House02 feature reconstruction

Pilot snapshot:

- full grid: **27 × 39 = 1053 cells**;
- free cells: **631**;
- obstacle cells: **422**;
- wind rows: **631**, one-to-one with free cells.

Constructed GeoPT-style free-space geometry:

[
g(x)
=
[x,y,z,mathrm{SDF},d_x,d_y,d_z].
]

Procedure:

1. use all obstacle-cell centers as the boundary set;
2. nearest-neighbor query for every free cell;
3. SDF = distance to nearest obstacle center;
4. boundary direction = normalized vector from nearest obstacle center to free cell;
5. set z=0 for the PMFS sensor-height 2-D pilot;
6. apply GeoPT-like geometry scaling so x-extent is 5.

Dynamics prompt:

[
v(x)
=
[hat w_x,hat w_y,0,|w|].
]

This produces:

- coordinates `x.shape = (631,3)`;
- physical feature tensor `fx.shape = (631,11)`.

### Caveat

The pilot `estimated_wind.csv` comes from the historical R2/GMRF run.

It is used **only for shape/runtime/interface construction**.

Its tiny magnitudes must not be used for any physics/performance conclusion.

All G1 scientific experiments must use the recovered Native ground-truth wind contract.

## 6. Real-House forward cost

With the actual 631-token House02 tensor and the official architecture replica:

- output shape: `[1,631,9]`;
- CPU 4-thread forward: **0.0866 s**;
- process peak RSS: ~**276 MiB**.

Therefore backbone compute is not a blocker for PMFS-grid-scale use.

## 7. Source conditioning recommendation

Do not change the pretrained 14-channel input projection.

First probe should keep the environment backbone intact and add source conditioning after environment encoding.

A minimal source-relative feature is:

[
r_s(x)
=
[x-s,|x-s|,Q_s(x)].
]

A tiny source adapter, e.g. 4→64→256, has only about 17k parameters, less than 0.5% of the 3.87M-parameter backbone.

For maximum source-candidate reuse, prefer:

1. compute/cache a source-independent environment representation from geometry+wind;
2. inject candidate source through a small adapter/decoder;
3. predict the candidate plume/hit field.

This preserves the foundation-model hypothesis and makes sweeping many PMFS candidates cheap.

## 8. Remaining hard gate — actual weight loading

Codex/VM must now:

1. download `GeoPT_8layers.pt`;
2. verify SHA256:
   `c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2`;
3. instantiate exact official config;
4. use official filtered loader;
5. report loaded tensor count and loaded parameter percentage;
6. run the 631-token real-House feature tensor through the **actual pretrained weights**.

PASS target:
- all internal geometry/dynamics representation layers load;
- only task/output head is intentionally excluded/replaced.

## 9. Current M6 verdict

The following risks are now substantially reduced:

- volume-vs-surface mismatch: reduced;
- feature-semantic mismatch: reduced;
- token-count/runtime risk: reduced;
- need to modify pretrained input projection: avoided.

Still unresolved:

- actual checkpoint load on our adaptation;
- whether pretrained features transfer to indoor plume prediction;
- whether low-data plume adaptation improves truth-source rank.

Status:

`ADVANCE — G0.5-B CHECKPOINT LOAD, THEN G1 LOW-DATA FROZEN-FEATURE PROBE`.
