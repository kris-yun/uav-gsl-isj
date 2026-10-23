# M4-v2 frozen transport-response audit — House02

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`  
Frozen parent checkpoint state: `0f322a5561f4a1ba05c19544f3094f8b09e12665`  
Workflow run: `35865947118`  
Decision: **NO-GO — REUSABLE TRANSPORT MECHANISM NOT SUPPORTED**

## Scope

This was a **kill-only** audit of the already frozen M4-v2 checkpoints. It did not:
- retrain either model;
- change architecture, loss, normalization, or checkpoint weights;
- add a plume seed;
- modify ROS/PMFS;
- run a closed loop.

It can reject the reusable-transport interpretation of M4-v2. It cannot promote M4-v2 to ADVANCE.

## Frozen test

For each training seed and each paired plume realization, compare the real GADEN wind intervention

[
Delta_W^{true}=C(S2,W2)-C(S2,W1)
]

against the frozen model intervention

[
Delta_W^{pred}=hat C(S2,W2)-hat C(S2,W1).
]

The source intervention

[
Delta_S=C(S2,W2)-C(S1,W2)
]

is evaluated in parallel so that wind sensitivity can be interpreted relative to source sensitivity.

All fields use the same frozen 2x spatial reduction and `log1p(concentration)` representation as C0.5.

## Predeclared kill-only rules

Before execution:

- K1: kill if, for **both** operator training seeds, the maximum over plume A/B of
  `||ΔW_pred|| / ||ΔW_true|| < 0.10`.
- K2: kill if wind-delta cosine is non-positive in more than one of the four operator comparisons.
- K3: kill if, for **both** operator training seeds, the predicted wind/source response ratio is less than 25% of the true wind/source ratio.

Crossing any kill rule is sufficient for NO-GO. Avoiding the rules would only authorize a later dense inverse-ranking test, not ADVANCE.

## Result

### Operator M4-v2

| Train seed | Plume | Wind amplitude ratio | Wind delta cosine | Source amplitude ratio | True wind/source | Pred wind/source | Relative wind/source |
|---|---|---:|---:|---:|---:|---:|---:|
| 1729 | A | 0.04878 | 0.40440 | 0.82686 | 0.52567 | 0.03101 | 0.05899 |
| 1729 | B | 0.05248 | 0.51491 | 0.85834 | 0.50717 | 0.03101 | 0.06115 |
| 2718 | A | 0.04312 | 0.44098 | 0.80600 | 0.52567 | 0.02812 | 0.05350 |
| 2718 | B | 0.04639 | 0.52544 | 0.83669 | 0.50717 | 0.02812 | 0.05545 |

K1: **TRIGGERED**.  
K2: not triggered; all four wind-delta cosines are positive.  
K3: **TRIGGERED**.

The operator therefore captures some *directional/spatial correlation* with the wind intervention, but its wind-driven change is only about **4.3%–5.25% of the real GADEN intervention amplitude**. By contrast, its source-driven change is about **80.6%–85.8% of the real source intervention amplitude**.

The real GADEN wind/source intervention-norm ratio is about 0.51–0.53. M4-v2 predicts only 0.028–0.031, i.e. about **5.35%–6.11% of the physically observed relative wind sensitivity**.

### Centroid transport diagnostic

For plume A/B, the real W1→W2 mean centroid displacement has magnitude about **6.36 / 5.00 pooled-grid cells**.

- operator seed 1729 predicts magnitude **0.126**;
- operator seed 2718 predicts magnitude **0.155**.

The predicted centroid displacement direction is positively aligned with the real displacement (cosine about 0.90–0.98), but its magnitude is only a few percent of the real shift.

This is consistent with a model that senses the wind label enough to perturb the predicted field in a partly correct direction, but does **not** reproduce the magnitude of the reusable transport intervention.

## Interpretation

The earlier held-out field-MSE advantage is real as a local predictive result, but this audit does not support attributing that gain to the proposed reusable wind-conditioned transport mechanism.

The strongest surviving explanation for the current M4-v2 signal is a **source-structured inductive bias**: the operator preserves and propagates source identity strongly, while the frozen transport conditioning is much too weak relative to the physical W1→W2 intervention.

This conclusion is additionally consistent with the implementation: the spatial convolution in each transport step is fixed, while wind/obstacle/time context modulates it through a pointwise gate rather than explicitly advecting state along the local wind vector.

The frozen model also uses only one canonical wind slice whereas the GADEN realization uses a time-varying wind sequence. That limitation may explain part of the failure, but it is part of the tested M4-v2 contract and cannot be repaired after opening S2×W2 and still counted as the same validation.

## Decision

**M4-v2: NO-GO AS THE MAIN INNOVATION.**

Do not proceed to:
- dense multi-candidate ranking for this frozen v2;
- G3 unknown-House generation for this frozen v2;
- PMFS/ROS integration;
- 300 s closed-loop experiments;
- extra training seeds intended to rescue v2.

This result does **not** prove the broader causal-compositional plume-world-model idea impossible. It rejects this M4-v2 realization as evidence for a reusable transport mechanism. Any later M4-v3 would need a new preregistered contract and genuinely new holdout data, with wind-direction-aware/time-varying transport fixed before target inspection.
