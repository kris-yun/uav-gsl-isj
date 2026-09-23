# M6 GeoPT G0.5-B Actual Checkpoint Load — PASS

Date: 2026-09-24  
Branch: `research/m6-geopt-g05-runtime-v1`  
Workflow run: `35915527445`  
Official GeoPT source commit: `9984f359fd44b6332c03ca55ab2e659e0c6e899d`

Decision: **G0_5_B_PASS**

## Official artifact

Repository: `GeoPT/GeoPT_Pretrained_Models`  
Checkpoint: `GeoPT_8layers.pt`

Observed:
- bytes: **15,556,600**
- SHA256: **c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2**
- tensors: **169**
- parameters: **3,865,673**

The SHA256 exactly matches the preregistered public artifact hash.

## Exact model/interface

Official configuration:
- Transolver;
- coordinate dim 3;
- SDF dim 1;
- boundary-direction dim 3;
- dynamics-condition dim 4;
- hidden 256;
- 8 layers;
- 8 heads;
- 32 slices;
- MLP ratio 2;
- pretraining trajectory output dim 9.

The instantiated first learned projection has shape:

`[512,14]`

confirming the corrected released contract:

`pos3 + fx11 -> 14-D preprocess input`.

## Actual filtered load

Using the official fine-tuning exclusion rule:
- exclude `ln_3`;
- exclude `mlp2`.

Observed:
- loaded tensors: **165/169**;
- loaded parameters: **3,862,848**;
- loaded fraction of complete model: **99.9269209%**;
- loaded fraction after excluding the intentional task head: **100.0%**;
- missing non-head internal tensors: **0**.

The only four skipped tensors are exactly:
- `blocks.7.ln_3.weight`;
- `blocks.7.ln_3.bias`;
- `blocks.7.mlp2.weight`;
- `blocks.7.mlp2.bias`.

There is no input-projection or internal-block shape mismatch.

## House02 frozen forward

A source-blind 631-free-cell House02 token set was built with:
- y-up coordinate mapping;
- pretraining-sign wall direction (free point -> nearest boundary);
- 1 s protocol-derived dynamics horizon.

Historical estimated wind is used here only for interface/runtime smoke, not for a scientific transfer claim.

Observed:
- `x: [1,631,3]`;
- `fx: [1,631,11]`;
- output: `[1,631,9]`;
- all outputs finite;
- CPU threads: 4;
- measured forward: **0.04546 s**;
- peak process RSS: ~**775 MiB** including Python/PyTorch runtime.

## Consequence

The old M6 infrastructure HOLD is removed.

GeoPT can be transferred without modifying:
- its pretrained 14-D input projection;
- any internal geometry/dynamics block.

Therefore the next hard question is scientific, not engineering:

> Does the official cross-physics pretrained representation outperform the same architecture with random weights under scarce gas-plume supervision?

No source-localization or plume-performance claim is made by G0.5.

Next:
**development-only House02 pretrained-vs-random frozen-feature kill test before any new GADEN generation.**
