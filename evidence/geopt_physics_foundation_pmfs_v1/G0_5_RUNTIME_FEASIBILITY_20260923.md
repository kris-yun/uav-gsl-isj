# G0.5 Runtime Feasibility — GeoPT backbone on a real House token set

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Decision

`G0.5-RUNTIME = POSITIVE`

`G0.5-CHECKPOINT-LOAD = HOLD FOR CODEX / NETWORK-ENABLED HOST`

The runtime/interface part of G0.5 is positive. The actual checkpoint tensor-load fraction still requires execution on a host that can download the public Hugging Face Xet binary.

## 1. Official checkpoint facts independently verified

Official repository:

`GeoPT/GeoPT_Pretrained_Models`

Released file:

`GeoPT_8layers.pt`

Public metadata:

- size: ~15.6 MB;
- SHA256: `c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2`;
- architecture config:
  - coordinate dimension: 3;
  - SDF dimension: 1;
  - normal/boundary-direction dimension: 3;
  - dynamics-condition dimension: 4;
  - hidden dimension: 256;
  - layers: 8;
  - heads: 8;
  - slice number: 32;
  - MLP ratio: 2;
  - pretraining output trajectory dimension: 9.

The current analysis environment could read all public metadata/configuration but could not download the Xet checkpoint bytes because of network/DNS restrictions. Do not interpret this infrastructure failure as a model failure.

## 2. Official architecture reconstructed from released source

Using the official:

- `models/Transolver.py`;
- `layers/Physics_Attention.py`;
- `scripts/finetune/GeoPT_craft.sh`;

the 8-layer unstructured Transolver configuration has:

[
3,865,673
]

parameters with a 9-D pretraining output head.

FP32 parameter storage:

[
15.462692 {m MB},
]

which is consistent with the public ~15.6 MB checkpoint size.

This is a strong architecture-consistency check, but is not a substitute for loading the checkpoint.

## 3. Real House02 geometry+dynamics token construction

Source archive:

`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

Used only for **interface/runtime construction**, not scientific wind validation.

House02 source-update-0001 PMFS grid:

- full cells: 1053;
- free cells: 631;
- obstacles: 422.

For every free cell, constructed the GeoPT-compatible 11-D feature:

[
[x,y,z,d_{m wall},n_x,n_y,n_z,hat w_x,hat w_y,hat w_z,|w|].
]

Geometry:
- nearest obstacle center used for the source-blind SDF/direction smoke test;
- horizontal geometry normalized to GeoPT-style target extent 5;
- 2-D sensor plane embedded at fixed z.

Wind:
- historical R2 `estimated_wind.csv` was used **only to populate the four dynamics slots for shape/runtime testing**;
- these old GMRF values are known to be unsuitable for scientific Native-PMFS conclusions;
- G0.5 scientific adaptation must use recovered ground-truth GADEN wind.

Feature checks:

- token count: 631;
- `pos.shape = (631,3)`;
- `fx.shape = (631,11)`;
- all features finite.

## 4. CPU forward benchmark

Environment:
- PyTorch 2.10 CPU;
- no CUDA available;
- batch size 1;
- official 8-layer / hidden-256 / 8-head / 32-slice structure;
- random weights;
- no training.

Results:

| Token set | N | CPU forward |
|---|---:|---:|
| House01-like PMFS free cells | 626 | ~0.10 s |
| House02-like PMFS free cells | 631 | ~0.11–0.15 s |
| full 83×119 sensor-height grid upper bound | 9877 | ~1.1 s |

These numbers test computational feasibility only.

No prediction/source-rank conclusion may be drawn from random weights.

## 5. Theoretical pretrained parameter retention

GeoPT's official fine-tune loader excludes:

- final `ln_3`;
- final `mlp2` output head.

For the reconstructed 8-layer/9-output model those account for:

[
2,825
]

parameters.

Therefore, **if** the public checkpoint state dictionary exactly matches the released architecture, the maximum transferable backbone is:

[
3,862,848 / 3,865,673
=
99.9269%.
]

This is a **theoretical architecture-derived fraction**, not an observed checkpoint-load fraction.

Codex must verify actual tensor-by-tensor loading.

## 6. Scientific consequence

M6 is not blocked by:
- token count;
- model size;
- indoor-volume representation;
- first-layer dimensional mismatch.

The remaining immediate gate is now narrow:

> Does the official checkpoint actually load at the predicted near-complete coverage, and do its frozen/pretrained features give a low-data advantage on gas transport?

## 7. Required Codex completion of G0.5

On the network-enabled VM:

1. download `GeoPT_8layers.pt`;
2. verify SHA256 exactly;
3. instantiate the official 8-layer Transolver;
4. run the official filtered load;
5. export:
   - total checkpoint tensors;
   - loaded tensors;
   - skipped tensors and reasons;
   - total checkpoint parameters;
   - loaded parameters;
   - actual load fraction;
6. construct one recovered-Native House tensor using **GADEN ground-truth wind**;
7. run frozen forward;
8. record CPU/GPU memory and timing.

### PASS target

- no input-projection mismatch;
- internal blocks load;
- only expected downstream output-head differences are excluded;
- loaded parameter fraction is near the architecture-derived ~99.93%.

If not, demote M6 before plume training.

## 8. Current verdict

`M6 = ADVANCE`

Reason:
the strongest early transfer risks have now been reduced:
- indoor **volume** geometry is supported by the parent model;
- the 11-D gas mapping is semantically aligned;
- architecture size/checkpoint size agree;
- realistic House token counts are cheap.

Still unproven:
- actual checkpoint load;
- feature transfer usefulness;
- plume/source-rank benefit.
