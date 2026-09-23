# Novelty Boundary Update — PHOENIX-UNet vs M6 GeoPT

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## 1. Direct 2026 gas-dispersion near-neighbor

Jianyao et al., *Physics-enhanced deep learning for obstacle-resolved atmospheric dispersion in leakage accidents*, Building and Environment, 2026.

Public code:
`Jyyd/PHOENIX-UNet`

Public dataset:
Zenodo record `17008799`, approximately 4000 steady-state dispersion cases.

## 2. What PHOENIX-UNet already does

The official code/data show:

### Inputs

Preprocessed image input:

[
[	ext{building mask}, 	ext{Gaussian plume prior}, 	ext{source map}]
]

with shape:

[
(3,H,W).
]

Metadata concatenates:
- source vector;
- meteorological vector.

The network uses a PhysicsEnhanced module to project metadata and fuse it throughout the U-Net.

### Conditions varied

The public dataset spans:
- multiple wind directions;
- multiple wind speeds;
- atmospheric stability classes;
- many source locations.

### Generalization claim

The published work explicitly evaluates unseen:
- wind directions;
- wind speeds;
- source locations.

### Geometry scope

The study holds the built environment fixed:
- one Chemical Park geometry.

### Training paradigm

The official training code initializes PHOENIX-UNet normally and trains it directly on the gas-dispersion dataset.

There is no released cross-physics foundation pretraining stage in the PHOENIX training pipeline.

## 3. Consequence for M6 novelty

M6 can **not** claim:

- first learned gas-dispersion surrogate that uses physics;
- first obstacle-aware gas field model;
- first source-conditioned gas field model;
- first model to generalize to unseen wind/source conditions;
- first fast learned dispersion simulator.

Those claims are already occupied.

The only defensible M6 thesis is narrower:

> **Transfer a cross-physics, dynamics-lifted foundation representation into gas dispersion so that PMFS candidate forward modeling requires substantially less gas-specific high-fidelity data than task-specific gas networks trained from scratch.**

The source-localization endpoint remains essential:

> reduced gas-data demand must eventually translate into better truth-source candidate ranking under scarce training data.

## 4. Why M6 still differs scientifically

PHOENIX:

[
	ext{gas data}
ightarrow
	ext{gas-specific U-Net training}
ightarrow
C(x)
]

M6:

[
	ext{cross-physics pretraining}
ightarrow
E_{m physics}(geometry,dynamics)
]

then

[
E_{m physics}
+
	ext{small gas/source adapter}
ightarrow
C_s(x).
]

The scientific question becomes:

> Does a representation learned from broad geometry–dynamics physics contain reusable structure for indoor plume transport that ordinary gas-specific training must otherwise learn from expensive dispersion simulations?

That is the foundation-model hypothesis.

## 5. External sandbox opportunity

PHOENIX's public dataset is useful as an **external low-data transfer sandbox** before generating a large GADEN dataset.

It provides:
- fixed obstacle geometry;
- many source locations;
- many meteorological conditions;
- concentration fields;
- public train/test code.

### Proposed benchmark

Compare:

1. PHOENIX-style / from-scratch gas model;
2. GeoPT backbone from random initialization;
3. pretrained GeoPT backbone + small gas/source head.

Use identical low-data subsets:

- 2.5%;
- 5%;
- 10%;
- 25%;
- 100%.

Primary external-sandbox metrics:
- concentration-field error;
- convergence/data efficiency;
- held-out source/wind generalization.

This sandbox is **not sufficient to validate PMFS source localization**.

It only asks whether cross-physics pretraining transfers to gas dispersion at all.

## 6. Important input mismatch

PHOENIX data exposes meteorological conditions but not necessarily the full obstacle-resolved local wind vector field used internally by GRAMM/GRAL.

Therefore two external-sandbox modes must be distinguished:

### P-S0 — global wind prompt

Construct a pointwise dynamics field by repeating the global meteorological wind vector over free cells:

[
v(x)
=
[hat w_x,hat w_y,0,|w|].
]

This tests basic transfer, not local transport fidelity.

### P-S1 — local flow prompt

Only if the public dataset exposes local flow fields.

This would be the stronger GeoPT-compatible test.

Do not claim wind-field physics from P-S0.

## 7. Hard external-sandbox interpretation

### Positive
If pretrained GeoPT clearly beats the same architecture from scratch at low gas-data fractions, M6 gets a real transfer signal.

### Negative
If pretrained and random initialization are indistinguishable across low-data fractions, M6's foundation-model thesis weakens substantially.

### Not enough
Even a positive PHOENIX result does not prove source-localization value.

The final hard gate still requires:
- Native/GADEN PMFS candidate replay;
- truth-source rank;
- independent plume realizations.

## 8. Current decision

`M6 = KEEP`

But its novelty wording is now strictly:

**cross-physics foundation transfer for low-data PMFS candidate forward modeling**

not:

**generalizable learned gas dispersion**.
