# Candidate Ranking Update — M6 GeoPT G0 Positive

Date: 2026-09-23

## New evidence

M6 (Dynamics-Lifted Physics Foundation Model for PMFS) passed its first interface audit.

Official GeoPT code confirms a volume representation:

[
[x,y,z,mathrm{SDF},d_x,d_y,d_z]
]

for interior CFD cells, plus a four-dimensional dynamics field.

This maps naturally to indoor gas transport:

- xyz: free-space location;
- SDF: distance to nearest wall/obstacle;
- direction: nearest-wall/boundary direction;
- dynamics field: local wind direction + speed.

The official fine-tuning path uses `fun_dim=11`, so this mapping preserves the pretrained input-embedding dimensionality.

## Gas-specific source conditioning

Do not add raw source channels to the 11-D input.

Candidate source should enter through a small **source injection adapter** after the pretrained environment embedding.

Conceptually:

[
h_0(x)
=
E_{m GeoPT}(geometry,wind)
+
A_s(x-s,Q_s(x)).
]

This preserves GeoPT's pretrained geometry/dynamics representation while making PMFS candidate source a counterfactual source injection.

## Updated candidate priority

### Tier A
- **M4 Causal Compositional Plume World Model**
  - strongest paper-level scientific narrative;
  - source candidate = intervention;
  - key test: unseen source×wind recombination.

- **M6 Dynamics-Lifted Physics Foundation PMFS**
  - strongest immediate feasibility/data-efficiency candidate;
  - official pretrained model/code;
  - strong volume-geometry/wind interface match.

### Tier B
- M3 Physics-Anchored Stochastic Plume World Model
  - strong stochastic-field thesis;
  - heavier data/training burden.

- M5 Generative Lagrangian Filament World Model
  - strongest PMFS physical fit;
  - main-theme novelty weaker unless non-Gaussian trajectory structure is source-critical.

## Immediate Codex action for M6 — G0.5 only

Before plume training:

1. obtain official GeoPT pretrained checkpoint;
2. instantiate official `fun_dim=11` model;
3. report loaded parameter fraction;
4. create one House geometry/wind feature tensor;
5. run frozen forward pass;
6. report token count, memory and inference time.

No truth use.
No source-rank claim yet.
No large GADEN data generation yet.

If the frozen pretrained backbone cannot be used with high parameter-load coverage, demote M6.
