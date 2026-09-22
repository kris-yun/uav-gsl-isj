# HCRC mechanism + auxiliary-innovation screen

Date: 2026-09-22  
Parent HCMC commit: `6afc592a5b43093efad7a4bda0c48c0cbb8a7cec`  
Data: frozen TNQC V5 R2 House01/02/03 × seed0/1 archive  
Archive SHA256: `81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`

Status: **EXPLORATORY DISCOVERY-SCOPE EVIDENCE ONLY.** This package must not be used to tune or reinterpret the in-progress Codex independent-realization validation. The frozen HCMC V1 validation contract remains unchanged.

## 1. Updated paper-level hypothesis

The strongest current interpretation is broader than one structure-function formula:

> A source hypothesis is physically compatible with the observations when the measured and source-conditioned scalar fields remain statistically conformant under successive spatial coarse-graining. Source inference should therefore test **hypothesis-conditioned cross-scale / renormalization conformance**, not pointwise reproduction of one turbulent plume realization.

Working umbrella name: **HCRC — Hypothesis-Conditioned Renormalization Conformance**.

HCMC V1 remains the best current implementation of this principle; HCRC is not a post-hoc replacement of the frozen HCMC validation algorithm.

## 2. Independent mathematical realization of the same principle

A second discovery-only implementation was constructed using coarse-to-fine detail-energy flow rather than HCMC's fixed-separation structure-function slopes. It compares how much detail is removed at successive coarse-graining levels for the measured field and each source-conditioned simulated field.

On the same six discovery cases, with the corrected ceil-style top-5% endpoint clone:

| representation | mean endpoint m | pooled reduction | improved |
|---|---:|---:|---:|
| Native PMFS | 5.5551 | — | — |
| HCMC cross-scale slope conformance | 2.4232 | 56.38% | 6/6 |
| RG detail-energy conformance, p=1..4 | 2.7128 | 51.17% | 6/6 |

The RG implementation was not used during HCMC discovery and is mathematically distinct. This supports the broader cross-scale-conformance hypothesis, but it is still evaluated on the same six discovery cases and is therefore not independent statistical validation.

### RG destructive controls

For the RG p=1..4 representation:

- final-leaf permutation, 300 repetitions: null mean `4.3894 m`, median `4.3297 m`, 5–95% `3.4029–5.4633 m`, `0/300` as good as the real RG result;
- simulated-field spatial shuffle, 30 repetitions: null mean `5.1610 m`, median `5.2391 m`, 5–95% `4.6187–5.5238 m`, `0/30` as good as the real RG result.

This makes it unlikely that the RG result is explained only by final partition geometry or marginal simulated values.

## 3. Stronger HCMC spectral surrogate control

The earlier spatial-shuffle null destroys all spatial structure. A stronger surrogate was therefore tested that keeps, candidate by candidate, the **magnitudes of all graph-Fourier coefficients** on the observed support graph while randomizing the signs/phases of non-nullspace coefficients. This approximately preserves the candidate's second-order graph-spectral content while disrupting phase/coherent higher-order organization.

Across 50 deterministic repetitions:

- real HCMC mean: about `2.4231 m`;
- graph-spectral surrogate null mean: `4.1868 m`;
- median: `4.2380 m`;
- 5–95%: `3.5853–4.6581 m`;
- best null: `3.2135 m`;
- `0/50` null repetitions were as good as real HCMC.

Interpretation: the HCMC advantage is not explained by second-order graph-spectral magnitudes alone. Phase/coherent and/or higher-order cross-scale organization is load-bearing. This is still a diagnostic surrogate, not a theorem that indoor GADEN fields satisfy a universal multifractal law.

## 4. Scale-family falsification

The effect is not unique to the dyadic scale tuple `{1,2,4,8}`:

| scale family | mean m | reduction | improved |
|---|---:|---:|---:|
| 1,2,4,8 | 2.4229 | 56.38% | 6/6 |
| 1,3,5,8 | 2.6073 | 53.06% | 6/6 |
| 2,4,8 | 2.6743 | 51.86% | 6/6 |
| 2,3,5,8 | 3.0357 | 45.35% | 6/6 |
| 1,3,6,8 | 3.2266 | 41.92% | 6/6 |
| 1,2,3,4 | 3.2973 | 40.64% | 6/6 |

A robust consensus over six scale families also stays positive:

- median consensus: `2.4807 m`, `55.34%`, 6/6;
- conservative minimum-rank consensus: `2.8365 m`, `48.94%`, 6/6.

This argues against a single lucky scale tuple being the sole explanation.

## 5. Hidden-multiplier literal transfer was screened and rejected as the primary implementation

A direct local multiplier-distribution implementation was tested using adjacent scale ratios and Wasserstein/quantile distances. The best variant (`ratioW1`) reached only:

- mean `3.9165 m`;
- `29.50%` pooled reduction;
- `5/6` improved.

Other log/bounded multiplier distances were around 6–10% pooled improvement. Therefore the modern hidden-scaling/multiplier literature is useful as a mother-theory anchor, but directly copying a multiplier-distribution statistic is **not** currently competitive with HCMC or RG conformance.

Decision: keep HCMC as the frozen primary implementation; use multiplier theory to motivate the broader cross-scale principle, not as a forced replacement.

## 6. Benchmark-geometry confound discovered

The six R2 discovery truths happen to lie near their local coordinate origins. A deliberately nonphysical control that ranks final leaves only by distance to global coordinate origin obtains:

- mean `1.8842 m`;
- apparent `66.08%` reduction;
- 6/6 improved.

Other geometry-only controls are also surprisingly strong, e.g. start-position ranking gives about `51.94%`, 6/6.

This does **not** prove HCMC is a geometry artifact: HCMC candidate scores are not equivalent to these geometry ranks, and the existing controlled SA/SB asset contains source reversals, including a House03 source around `(8.2, 5.0)`, where a fixed origin prior cannot solve balanced SA/SB source identity. Nevertheless it proves that **the six-case absolute localization endpoint alone is insufficient to establish source-location generalization**.

Required later gate: after independent plume-realization validation, perform a full 300-s source-position-transfer localization matrix with truth positions materially different from the R2 positions.

## 7. Auxiliary innovation A: SCAS — Scale-Completion Active Sensing

A source-blind feasibility screen was run on all `6 cases × 5 source updates = 30` frozen states.

For every candidate next cell, SCAS values observations that simultaneously:

1. complete under-supported scale edges in the frozen cross-scale family; and
2. maximize dispersion between current source hypotheses in the predicted increment statistics.

### Uncosted screen

Compared with the mean of currently unobserved candidate cells:

- SCAS source-discrimination utility was higher in **30/30** states;
- minimum SCAS/random discrimination ratio: `1.711×`;
- median: `2.495×`;
- mean: `2.585×`.

### Distance-aware screen

With a fixed physical distance penalty normalized by the largest frozen scale (`8 × 0.3 = 2.4 m`):

- discrimination remained higher than random in **30/30** states;
- minimum ratio: `1.075×`;
- median: `2.082×`;
- mean: `2.261×`;
- mean selected-distance/random-distance ratio: `0.495`;
- selected location was no farther than the random mean in `24/30` states.

This is only an offline next-observation feasibility screen; it does not establish closed-loop localization improvement. However, it is currently a strong auxiliary-innovation candidate because it directly follows the main HCRC thesis: actively complete the most source-discriminative missing part of the renormalization trajectory.

## 8. Auxiliary innovation B remains unpromoted

A truth-blind multiscale-observability / maturity certificate was explored using effective pair counts, split-support statistics, bootstrap stability and slope uncertainty. Some features correlate with HCMC maturity, but current rules still produce false releases on early snapshots.

Decision: **do not promote MOC yet**. The scientifically appropriate next version should be an anytime-valid / confidence-sequence-style identifiability certificate rather than a hand-tuned ppm or support threshold.

## 9. Current hierarchy and hard boundary

Current discovery-stage hierarchy:

1. **Main thesis candidate:** HCRC — hypothesis-conditioned renormalization / cross-scale conformance.
2. **Frozen main implementation under independent validation:** HCMC V1.
3. **Independent mechanism corroboration:** RG detail-energy flow, 51.17%, 6/6 on discovery data.
4. **Auxiliary candidate A:** SCAS, positive in 30/30 frozen next-observation screens.
5. **Auxiliary candidate B:** not yet selected; MOC remains research-only.

Nothing in this branch changes the HCMC V1 algorithm being independently validated by Codex. Do not tune the independent validation from these exploratory results.

## 10. Next decision after Codex returns

If the frozen independent-plume HCMC gate passes:

1. freeze the HCRC paper-level interpretation without changing HCMC V1;
2. run source-position-transfer 300-s localization to eliminate the discovered coordinate/start-position benchmark confound;
3. port SCAS to a shadow planner and test whether scale completion accelerates HCRC identifiability before allowing planner feedback;
4. continue MOC only if a source-blind certificate can be defined without truth-tuned thresholds.

If the independent-plume gate fails, do not rescue HCMC by using RG/SCAS tuning on the validation set. Return to the main-innovation candidate pool.
