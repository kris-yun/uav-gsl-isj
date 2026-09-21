# Plume Transport Geometry V1 — cheap screen

Date: 2026-09-21
Status: **POSITIVE MECHANISM / DEMOTED FROM MAIN-INNOVATION SLOT BY NOVELTY COLLISION**

## Mother idea tested

Treat the observed spatial gas field as a nonnegative mass distribution and compare source hypotheses by transport geometry rather than pointwise amplitude compatibility.

Remote-field anchor:
- NeurIPS 2025: Variational Regularized Unbalanced Optimal Transport (Var-RUOT), which combines stochastic transport with non-conserved mass and least-action structure.

## Cheap proxy

Before implementing unbalanced dynamic OT, a fixed sliced-Wasserstein proxy was used on the controlled 240-s VGR asset.

Construction:
1. aggregate gas on the existing 0.3 m spatial grid;
2. subtract each episode's minimum concentration;
3. normalize positive excess concentration to unit mass;
4. compute 16 fixed one-dimensional Wasserstein-1 projections;
5. average projection costs;
6. classify each episode against opposite-wind SA/SB templates.

No learned parameters and no post-result angle tuning.

## Result

Cross-wind source identity:
- overall: **11/12 = 91.67%**
- only failure: **H02_SA_slow**
- mean signed source margin: +2.4304

Disjoint spatial support controls:
- checkerboard-even: **11/12**
- checkerboard-odd: **11/12**

Positive affine nuisance stress:
- independent per-episode positive scale + additive offset leaves the construction invariant by design;
- fixed stress realization remains **11/12**.

Interpretation:
- transport geometry is a strong source-identity signal;
- it is distributed rather than confined to one local patch;
- it is not merely raw amplitude matching.

## Novelty collision

The main-innovation claim cannot be simply "use optimal transport for source localization".

Direct collisions found:
- 2025: Tuomo Valkonen, *Point source localisation with unbalanced optimal transport*.
- 2026: Thi Tam Dang & Tuomo Valkonen, *Leak localisation with a measure source convection-diffusion model*, directly targeting gas-leak localization with a measure-valued source and jointly estimated transport parameters.

These works are not identical to the present mobile turbulent-plume setting, but they make a generic OT/UOT source-localization novelty claim too weak.

## Decision

- **Do not promote OT/UOT as the paper-level mother idea.**
- Keep transport geometry as a strong auxiliary, ablation, or source-evidence construction candidate.
- Do not tune the 16 projection angles or hand-fit transport weights on these 12 cases.
- Continue searching for a different main innovation whose scientific object is not already "optimal transport source localization".
