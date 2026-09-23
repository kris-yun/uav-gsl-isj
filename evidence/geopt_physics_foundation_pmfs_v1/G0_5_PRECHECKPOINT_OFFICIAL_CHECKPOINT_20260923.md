# G0.5 PRE-CHECKPOINT — Official GeoPT checkpoint availability and exact input contract

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Status

`G0.5 = READY FOR RUNTIME LOAD TEST`

The official GeoPT release exposes a pretrained checkpoint named:

`GeoPT_8layers.pt`

Public metadata indicates an approximately 15.6 MB checkpoint.

The official released fine-tuning configuration uses the same 11-D pointwise input contract already audited:

[
3 	ext{coordinates}
+
1 	ext{boundary distance / SDF}
+
3 	ext{boundary-direction components}
+
4 	ext{dynamics-field components}
=
11.
]

For indoor gas transport this maps naturally to:

[
[x,y,z,d_{m wall},n_x^{wall},n_y^{wall},n_z^{wall},
hat w_x,hat w_y,hat w_z,|w|].
]

This means the first runtime probe should **not** modify the pretrained GeoPT input embedding.

## Required runtime test

1. obtain the official GeoPT repository code and `GeoPT_8layers.pt`;
2. instantiate the exact official 8-layer Transolver configuration used for fine-tuning;
3. load the checkpoint using the official filtered-loader logic;
4. report:
   - number of checkpoint tensors;
   - number loaded;
   - loaded parameter count / total parameter count;
   - exact excluded heads;
   - any shape mismatch;
5. construct one real House geometry+wind tensor in 11-D format;
6. run one frozen forward pass;
7. report:
   - number of tokens;
   - wall-clock;
   - peak RAM/VRAM;
   - CPU/GPU device;
   - output shape.

## Hard interpretation rule

A high load percentage is necessary for the "physics foundation model transfer" claim.

If the gas adaptation forces changes to the input projection or most internal blocks, M6 collapses toward generic Transolver/PINO and must be demoted.

## Source injection remains outside raw 11-D input

Candidate-source information should initially enter through a small post-embedding adapter / FiLM-style modulation so that the pretrained geometry+dynamics representation remains intact.

No plume training is allowed before this runtime compatibility probe passes.
