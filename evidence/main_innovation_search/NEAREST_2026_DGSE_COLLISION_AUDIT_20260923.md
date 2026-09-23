# 2026 Nearest-Collision Audit — DGSE-S

Date: 2026-09-23  
Scope: M3 / M4 / M6 main-innovation search

Paper:
Seunghwan Kim, Hyungjin Kim, Junhee Lee, Hyondong Oh,
*Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference*,
arXiv:2608.16221, submitted to IEEE Transactions on Robotics, Aug. 2026.

## 1. Why this is a critical near-neighbor

The paper directly targets:
- complex indoor multi-room GSL;
- mobile-robot sparse gas + wind observations;
- probabilistic source posterior;
- wind-field inference;
- concentration-field inference;
- active GSL;
- embedded-GPU online deployment.

It explicitly argues that wind and source govern the concentration field and builds network structure around physical dependencies.

Therefore any broad claim such as:
- "deep probabilistic physical GSL";
- "joint wind/concentration/source inference";
- "physical dependency-guided GSL";
- "probabilistic concentration field for active GSL"

is already occupied.

## 2. Exact DGSE-S factorization

The paper's proposed sequential model performs inverse conditional inference:

[
p(wmid z^w,z^c,o)
]

then

[
p(cmid w,z^c,o)
]

then

[
p(smid w,c,o).
]

The final source posterior is obtained by sequential marginalization over latent wind and concentration fields.

Outputs:
- wind field: diagonal Gaussian per cell;
- concentration field: diagonal Gaussian per cell;
- source: categorical distribution over grid cells.

Architecture:
- U-Net-style convolutional networks/subnetworks;
- sparse observation maps + environment map as inputs.

Important:
the field uncertainty is computationally lightweight **independent per-cell Gaussian uncertainty**, not a source-conditioned stochastic function-space process with explicit spatial joint covariance.

## 3. What DGSE-S does NOT appear to do

Based on v1 full method text:

### Not a candidate-source forward world model
It does not evaluate PMFS-style counterfactuals:

[
do(S=s)ightarrow p(Cmid S=s,W,O).
]

Instead it infers source posterior from reconstructed fields.

### Not a compositional intervention world model
No explicit source/wind/geometry mechanism modules are trained and swapped/recombined under controlled interventions.

No held-out source×wind mechanism-combination test is the central claim.

### Not a physics foundation model
No pretrained cross-domain geometry–dynamics backbone is transferred.

The U-Net is trained for the GSL/GDM task on CFD-generated data.

### Not stochastic function-space field generation
Field uncertainty is diagonal Gaussian by cell.

No operator flow matching / joint stochastic process density over arbitrary spatial query sets is described.

## 4. Consequence for M3

M3 cannot claim:
- first deep probabilistic plume/concentration field in indoor GSL;
- first uncertainty-aware learned concentration field used for source posterior;
- first probabilistic GDM+GSL framework.

M3 only survives if it proves value from the stronger object:

> source-conditioned **joint stochastic plume process distribution**, including spatial/intermittency structure beyond independent per-cell Gaussian uncertainty.

The stochastic model must beat:
- deterministic residual model;
- diagonal-Gaussian field model analogous to DGSE-S.

## 5. Consequence for M4

M4 cannot claim:
- first physical dependency graph for deep GSL;
- first sequential wind→concentration→source structure;
- first causal/physical factorization in indoor GSL.

M4 only survives as:

> **interventional compositional forward world modeling**, where source, wind and geometry are explicit reusable mechanisms and the key test is unseen intervention recombination.

Required distinction:
- DGSE-S = inverse conditional dependency factorization;
- M4 = forward mechanism modularity + `do(S=s)` / `do(W=w)` counterfactual recombination.

If M4 never demonstrates mechanism recombination, it is too close conceptually and should be killed.

## 6. Consequence for M6

M6 remains comparatively well separated.

DGSE-S:
- task-specific U-Net;
- trained on CFD GSL/GDM data;
- sparse-observation inverse inference.

M6:
- pretrained cross-physics geometry–dynamics representation;
- candidate-source forward prediction;
- low-data adaptation via source-injection adapter;
- PMFS candidate belief retained.

M6 novelty still cannot be:
- first learned indoor gas model;
- first physically structured deep GSL;
- first wind/geometry-aware network.

It must be:

> **transfer of a dynamics-lifted physics foundation representation into PMFS candidate-source forward simulation under scarce plume supervision.**

## 7. Required new baselines

If M3/M4/M6 advances, include a conceptual baseline inspired by DGSE-S where feasible:

- task-specific U-Net / matched model trained from scratch;
- field uncertainty as diagonal Gaussian;
- no pretrained physics representation;
- no compositional intervention module.

This prevents attributing gains to generic deep probabilistic field reconstruction.

## 8. Current decision

- M3: `KEEP BUT NOVELTY NARROWED SIGNIFICANTLY`
- M4: `KEEP ONLY IF INTERVENTION/COMPOSITION TEST PASSES`
- M6: `KEEP — DISTINCTEST CURRENT LEAD RELATIVE TO DGSE-S`

This paper raises M6's relative priority.
