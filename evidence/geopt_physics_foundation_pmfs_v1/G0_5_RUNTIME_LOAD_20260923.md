# M6 G0.5 runtime load and frozen-backbone probe

Date: 2026-09-23  
Worktree: `geopt-g05-20260923`  
Status: **G0.5 ENGINEERING PASS; M6 SCIENTIFIC CLAIM HOLD**

## Scope

This probe answers only whether the released GeoPT 8-layer backbone can be
instantiated with the official fine-tuning contract (`space_dim=3`,
`fun_dim=11`) and run once on an indoor-style point tensor. It does not train,
evaluate plume fidelity, or claim source-localization performance.

The official code was left untouched at:

`D:\ZYC\A-gas\_staging\geopt_official_20260923`

Official repository commit: `9984f359fd44b6332c03ca55ab2e659e0c6e899d`.  The
8-layer configuration is taken literally from
`scripts/finetune/GeoPT_craft.sh`: 256 hidden units, 8 heads, 8 layers,
`mlp_ratio=2`, `slice_num=32`, `geotype=unstructured`, `space_dim=3`,
`fun_dim=11`; the fine-tuning head uses `out_dim=6`.

## Checkpoint provenance

Official model page: <https://huggingface.co/GeoPT/GeoPT_Pretrained_Models/blob/main/GeoPT_8layers.pt>  
Direct download:

`https://huggingface.co/GeoPT/GeoPT_Pretrained_Models/resolve/main/GeoPT_8layers.pt?download=true`

Local file: `D:\ZYC\A-gas\_staging\GeoPT_8layers.pt`  
Size: `15,556,600` bytes  
SHA256: `C0B1B9C4E5D533DBC249190D3D1FBE8E6B066B36D325CF4377CC0D613C02D1C2`

The SHA256 matches the Hugging Face LFS metadata. The checkpoint is not part
of the GitHub code repository; the official loader expects it at
`./checkpoints/GeoPT_8layers.pt`.

## Exact filtered-loader audit

The loader is the code in `exp/GeoPT_finetune.py`:

```python
exclude_layers = ("mlp2", "ln_3")
filtered = {
    k: v for k, v in pretrained.items()
    if k in model_state
    and model_state[k].shape == v.shape
    and not any(excl in k for excl in exclude_layers)
}
```

| quantity | observed |
|---|---:|
| checkpoint tensor keys | 169 |
| checkpoint parameter count | 3,865,673 |
| loaded tensor keys | 165 |
| loaded parameter count | 3,862,848 |
| instantiated model parameters (`out_dim=6`) | 3,864,902 |
| loaded / model parameters | 0.9994685506 (99.9469%) |
| excluded keys | `blocks.7.ln_3.{weight,bias}`, `blocks.7.mlp2.{weight,bias}` |
| shape-mismatch keys | `blocks.7.mlp2.weight`, `blocks.7.mlp2.bias` |

The only mismatches are the final output head: the released pretraining head is
9-dimensional while the official fine-tune script requests 6 dimensions.
Every internal geometry/dynamics projection and all eight attention blocks
load by exact shape. The four excluded tensors are therefore the final head,
not a rebuilt backbone.

## Frozen forward probe

Runtime environment: Python 3.10.19, PyTorch 2.9.1+cu130, NVIDIA GeForce RTX
5060 Laptop GPU. The probe script is
`research/geopt_physics_foundation_pmfs_v1/g0_5_runtime_probe.py`.

The input has shape `x=(1,4096,3)` and `fx=(1,4096,11)`. It is a deterministic
normalized 7 x 5 x 3 m room proxy with two rectangular internal obstacles,
wall-distance proxy, wall-normal proxy, and a spatially varying horizontal
wind field. The 11-D feature contract is:

`[dwall, nx, ny, nz, wx, wy, wz, |w|, 0, 0, 0]`.

The three trailing zero channels are reserved metadata placeholders; no source
coordinates or plume values were supplied.

| device | tokens | wall time | peak VRAM allocated | peak VRAM reserved | RSS delta | output |
|---|---:|---:|---:|---:|---:|---|
| CUDA (RTX 5060 Laptop) | 4096 | 0.286 s | 54,855,168 B (52.3 MiB) | 81,788,928 B (78.0 MiB) | 1,218,969,600 B peak RSS (1.135 GiB) | `(1,4096,6)` |
| CPU control | 4096 | 0.172 s | n/a | n/a | 629,878,784 B peak RSS (600.6 MiB) | `(1,4096,6)` |

The raw JSON also records RSS before/after and delta; peak RSS was sampled at
1 ms intervals during the forward pass.

Raw machine-readable outputs:

- `evidence/geopt_physics_foundation_pmfs_v1/G0_5_runtime_result.json`
- `evidence/geopt_physics_foundation_pmfs_v1/G0_5_runtime_result_cpu.json`

## Gate interpretation

**PASS for G0.5 runtime/interface feasibility.** The exact released backbone
loads at 99.9469% of the `out_dim=6` model parameters, with no internal shape
mismatch, and executes a 4096-token 11-D indoor-style input on both CUDA and
CPU.

**HOLD for M6 scientific validity.** The final output head is excluded and is
randomly initialized in this probe; no plume-specific training, source
injection adapter, source-rank test, or low-data comparison was performed.
This result establishes engineering compatibility only. The next admissible
step is a preregistered frozen-backbone adapter/source-injection probe with
held-out source rank and from-scratch controls.
