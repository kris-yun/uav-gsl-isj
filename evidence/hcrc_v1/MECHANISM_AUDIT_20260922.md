# HCRC V1 — Cross-Scale/Renormalization Mechanism Audit

Date: 2026-09-22  
Base HCMC commit: `6afc592a5b43093efad7a4bda0c48c0cbb8a7cec`  
Data archive SHA256: `81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`

Status: **MECHANISM SUPPORTIVE / BENCHMARK-CONFOUND WARNING / INDEPENDENT VALIDATION STILL REQUIRED**

## 1. Main interpretation

The evidence is better described at one level above the original HCMC name:

**HCRC — Hypothesis-Conditioned Renormalization Conformance.**

Scientific claim under test:

> A compatible source hypothesis need not reproduce one stochastic turbulent-scalar realization point-by-point. It should reproduce how the scalar statistics evolve under ordered spatial coarse-graining.

The original HCMC structure-function slope vector is one lightweight estimator of this cross-scale flow. It should not be presented as proof of a universal indoor multifractal law.

## 2. Corrected native endpoint

The original PMFS C++ `GSL::Utils::ExpectedValue(grid,0.05)` includes cells while
`i < N_free*0.05`, which is equivalent to `ceil(0.05*N_free)` for noninteger 5%.

Re-evaluation with this semantics preserves the HCMC discovery signal:

| case | Native m | HCMC corrected m |
|---|---:|---:|
| H01/s0 | 5.527347 | ~2.023 |
| H01/s1 | 4.001642 | 2.1646 |
| H02/s0 | 4.107023 | 1.2388 |
| H02/s1 | 3.700743 | 3.0852 |
| H03/s0 | 7.782055 | 1.2808 |
| H03/s1 | 8.211551 | 4.7458 |

Native mean = **5.5551 m**; corrected HCMC mean ≈ **2.423 m**; pooled reduction ≈ **56.38%**; **6/6 improved**.

## 3. Independent real-space coarse-graining replication

A structurally different estimator was implemented as a mechanism check.

For each source-conditioned support field, form confidence-weighted block averages at dyadic scales 1,2,4,8 cells. For every child block, compute its residual relative to the parent block at the next scale. Compare measured and simulated **detail-moment flow** across successive coarse-graining levels.

This implementation does not use the HCMC pairwise increment construction.

Frozen p={1,2,3,4} result:

| case | Native m | real-space RG m |
|---|---:|---:|
| H01/s0 | 5.5273 | 4.2702 |
| H01/s1 | 4.0016 | 2.6934 |
| H02/s0 | 4.1070 | 2.7814 |
| H02/s1 | 3.7007 | 2.0670 |
| H03/s0 | 7.7821 | 1.5889 |
| H03/s1 | 8.2116 | 2.8759 |

Mean = **2.7128 m**, pooled reduction = **51.17%**, **6/6 improved**.

This is important because two different discretizations of cross-scale flow recover a large 6/6 discovery signal.

Preliminary controls for this RG estimator:
- random final-leaf assignment: 100 repetitions, mean ≈ **4.389 m**, **0/100** as good as real RG;
- simulated-field spatial shuffle: 10 repetitions, mean ≈ **5.161 m**, **0/10** as good as real RG.

These are discovery controls, not independent validation.

## 4. Scale order is load-bearing

A stronger destructive control preserves every candidate's structure-function values at all four scales and only changes which physical scale label is attached to each value.

All 24 global permutations of `(1,2,4,8)` were evaluated. The same permutation was applied coherently to all candidates and all powers within a replicate.

- correct physical order `(1,2,4,8)`: **2.4229 m**
- 23 nonidentity permutations: mean **3.4416 m**
- nonidentity median **3.4225 m**
- best nonidentity **2.7402 m**
- worst nonidentity **4.0117 m**
- nonidentity permutations as good as correct order: **0/23**

Therefore the signal is not merely a bag of multiscale features: the **ordered evolution along the scale axis** matters.

## 5. Scale-family falsification

Several predeclared diagnostic scale families were compared without promoting any post-hoc replacement:

| scale family | mean m | pooled gain | improved |
|---|---:|---:|---:|
| dyadic 1,2,4,8 | **2.4229** | **56.38%** | 6/6 |
| mixed 1,3,5,8 | 2.6073 | 53.06% | 6/6 |
| 2,4,8 | 2.6743 | 51.86% | 6/6 |
| 2,3,5,8 | 3.0357 | 45.35% | 6/6 |
| 1,3,6,8 | 3.2266 | 41.92% | 6/6 |
| 1,2,3,4 | 3.2973 | 40.64% | 6/6 |

Interpretation: the effect is not unique to one exact scale tuple, but the full dyadic family remains the strongest frozen discovery family. This supports a general cross-scale-conformance claim more than an exact Kolmogorov-law claim.

## 6. Phase/spectrum-preserving surrogate

For each candidate support graph:
1. construct the irregular-grid graph Laplacian;
2. transform the simulated field to graph-Fourier coordinates;
3. preserve each spectral coefficient magnitude;
4. randomize nonzero-mode signs (phase analogue);
5. invert and recompute HCMC.

50 deterministic repetitions:
- true corrected HCMC ≈ **2.423 m**
- spectral-surrogate null mean ≈ **4.187 m**
- median ≈ **4.238 m**
- 5–95% ≈ **3.585–4.658 m**
- best null ≈ **3.213 m**
- **0/50** as good as true HCMC.

Thus the HCMC gain is not explained by graph spectral power alone. Spatial phase/coherent or higher-order organization is load-bearing. This does **not** by itself prove intermittency.

## 7. Cross-seed replication of independent RG score

Spearman correlation of real-space RG candidate scores between seed0 and seed1 on common final leaves:

- House01: ~**0.420**
- House02: ~**0.836**
- House03: ~**0.223**

This closely mirrors the original HCMC reproducibility pattern and supports a shared mechanism rather than one exact score formula.

## 8. Important benchmark geometry confound

A severe benchmark confound was discovered.

All current authoritative source positions are relatively close to the global coordinate origin, and all starts are also only about 1.58–3.10 m from truth.

Pure source-leaf geometry baselines, with no gas and no wind:

| baseline | mean endpoint m | apparent gain vs Native | improved |
|---|---:|---:|---:|
| distance to global origin | **1.884** | **66.08%** | 6/6 |
| distance to robot start | **2.670** | **51.94%** | 6/6 |
| free-map centroid | 4.023 | 27.57% | 6/6 |
| measured-probability centroid | 4.272 | 23.09% | 6/6 |
| path bounding-box center | 4.417 | 20.49% | 5/6 |
| measured-confidence centroid | 4.504 | 18.93% | 5/6 |
| path mean | 4.619 | 16.85% | 5/6 |
| nearest-to-path | 5.071 | 8.72% | 5/6 |

This means the six fixed-source House/seed cases are suitable for **mechanism discovery and destructive controls**, but not sufficient by themselves to establish a 56% general localization improvement.

This does not imply HCMC/RG simply encode those priors. Candidate-score correlations with absolute-origin/start proximity are mostly small. For RG, for example, origin-score correlations range roughly 0.03–0.31 and start correlations roughly -0.31–0.19.

Nevertheless, the endpoint benchmark itself is confounded.

**Hard consequence:** after new stochastic plume validation, a source-position-transfer gate is mandatory. New seeds or new plume realizations at the same source coordinates do not remove this confound.

## 9. Multiscale observability audit

A truth-blind statistical precision diagnostic was built for the measured cross-scale vector.

Pairs are grouped into 4×4-cell blocks, corresponding to the pre-existing ~0.5 m PMFS correlation scale (about 2 sigma / 0.3 m per cell). Within each block, weighted structure-function contributions are summarized; effective block counts and delta-method standard errors of `log2 S_p(l)` are propagated to 95% half-widths for local scale slopes.

Across the 30 historical source-update snapshots:
- maximum 95% slope half-width vs HCMC improvement: Spearman ≈ **-0.558**, p≈**0.00136**;
- q90 half-width: Spearman ≈ **-0.554**, p≈**0.00149**;
- minimum effective block count: Spearman ≈ **+0.436**, p≈**0.016**.

Mean maximum 95% half-width by update:
- update1: ~4.33
- update2: ~3.79
- update3: ~2.91
- update4: ~1.53
- update5: ~1.24

This supports an evidence-maturity phenomenon, but **no release threshold has been fitted**.

A strict 95% candidate-level partial-identification set remained too broad (often ~90–100% of candidates even late), so unique-source certification is currently rejected as an operational gate.

Inverse-variance weighting of HCMC components reduced some early damage but weakened the final discovery gain (about 49–54% versus 56.4%). Therefore uncertainty weighting is not promoted yet.

## 10. SCAS auxiliary feasibility

A source-truth-blind scale-completion active-sensing diagnostic was tested at the final snapshots.

For an unobserved aligned cell `a`, the screen:
- identifies existing neighbors at 1/2/4/8-cell separations;
- computes source-hypothesis variation of predicted increment moments;
- prioritizes scales with fewer existing dyadic edges.

Across six cases, the top scale-aware action had mean source-hypothesis increment discrimination ≈ **0.119**, versus ≈ **0.051** for a random available cell and ≈ **0.086** for a generic pointwise-variance action.

This only establishes that the action functional is nontrivial and computable from the frozen candidate bank. It is **not yet a closed-loop performance claim**.

## 11. Current method architecture

The most coherent architecture is:

### Main innovation — HCRC
**WHAT evidence should source inference use?**  
Candidate-conditioned agreement of ordered cross-scale coarse-graining / renormalization behavior.

### Auxiliary 1 — Multiscale Observability / Evidence Precision
**WHEN is HCRC evidence estimable?**  
Use source-truth-blind scale-resolved uncertainty from physically blocked structure-function estimates. Current evidence supports a continuous precision measure; a hard release threshold is not yet justified.

### Auxiliary 2 — Scale-Completion Active Sensing (SCAS)
**WHERE should the robot measure next?**  
Choose actions that both fill deficient adjacent scales and maximally separate source hypotheses in the same cross-scale statistics used by HCRC.

This gives one scientific story rather than three unrelated modules: **WHAT / WHEN / WHERE** around the same scale-space object.

## 12. Literature/novelty boundary

Relevant remote-field anchors:
- Morel et al., ACHA 75, 101724 (2025): cross-scale wavelet/scattering dependencies and scale-invariant representations of non-Gaussian intermittent processes.
- Calascibetta et al., Phys. Rev. Fluids 10, 084605 (2025): hidden scaling symmetry and scalar multiplier statistics for passive scalars.
- Lempereur & Mallat, ACHA 83, 101854 (2026): hierarchical probability flows interpreted as an inverse renormalization group for complex physical fields including turbulence.
- Fossella et al., Phys. Rev. E 113, 024208 (2026), Editors' Suggestion: multiscale turbulent data assimilation; observations at multiple adjacent mesoscales can be load-bearing for synchronization.
- Biferale et al., Scientific Data 13, 428 (2026): TURB-Smoke DNS benchmark with five independent point sources and multiple wind conditions.

Important collision to acknowledge:
- Caticha, Entropy 17, 2573–2589 (2015), "Source Localization by Entropic Inference and Backward Renormalization Group Priors", already used RG ideas for generic inverse source localization (fMRI/EEG). Therefore novelty must **not** be stated as "using renormalization group for source localization."

Target novelty remains narrower:
> **source inference by hypothesis-conditioned conformity of turbulent-scalar statistics under ordered physical coarse-graining**, rather than RG priors over source-resolution lattices.

Adjacent gas/odor work also already includes wavelet neural networks, entropy/information active sensing, Bayesian turbulent search, and calibration-free ranking. Avoid claiming those general concepts as new.

## 13. Mandatory next gates

1. Finish current Codex independent-plume validation with HCMC frozen.
2. Regardless of that outcome, do not interpret same-source new realizations as final generalization evidence.
3. Add **source-position transfer** with pre-frozen alternate source positions and preferably changed start/source geometry.
4. Strong external mechanism candidate: TURB-Smoke 2026, which contains five distinct point sources and multiple wind intensities.
5. Only after source-position/plume transfer should HCRC be promoted into closed-loop HCRC V2.
6. MOC threshold and SCAS policy must be frozen on development data and evaluated on independent runs; no tuning on the six discovery cases.

## Current decision

- HCMC remains the strongest frozen performance realization of HCRC.
- HCRC is now better supported as the **paper-level mother idea** than "multifractality" alone.
- Real-space RG replication and scale-order permutation are the strongest new mechanism evidence.
- The geometry/start confound is the strongest new threat to the current performance claim.
- Independent source-position validation is now a **hard requirement**.
