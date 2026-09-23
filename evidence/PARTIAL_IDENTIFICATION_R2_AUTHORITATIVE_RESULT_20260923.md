# R2 partial-identification frozen screen — authoritative six-case result

Date: 2026-09-23
Status: **DIAGNOSTIC NECESSITY POSITIVE / MAIN-LOCALIZATION UTILITY NO-GO**

## Frozen object

This executes the already-frozen V1 robustness-radius object on the authoritative R2 archive:
`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`.

For candidate source s:

`rho_star(s) = max_i confidence_i * |p_measured(i) - p_simulated(i|s)|`.

The identified set at radius rho is:
`I_rho = {s : rho_star(s) <= rho}`.

No radius is selected from source truth. Source truth is used only after the source-blind robustness calculation to evaluate whether the object carries source identity.

## Six-case result at the final update <= 300 s

| case | candidates | truth rho* | truth robustness rank | Native truth rank | min candidate rho* | robust-best distance to truth (m) | Native posterior max | Native posterior ESS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| House01 seed0 | 152 | 1.000 | 119.5 | 110 | 0.9450 | 3.551 | 0.383 | 5.03 |
| House01 seed1 | 148 | 1.000 | 120.0 | 117 | 0.8037 | 4.378 | 0.368 | 3.71 |
| House02 seed0 | 148 | 1.000 | 121.5 | 123 | 0.8912 | 3.893 | 0.531 | 2.61 |
| House02 seed1 | 144 | 1.000 | 112.5 | 121 | 0.8520 | 4.022 | **0.879** | **1.28** |
| House03 seed0 | 197 | 1.000 | 147.0 | 149 | 0.9300 | 8.289 | 0.354 | 3.93 |
| House03 seed1 | 199 | 1.000 | 148.5 | 148 | 0.99998 | 7.349 | 0.164 | 9.12 |

Candidate rho* distributions are near saturation:
- H01 seed0: min 0.945, median 1.000;
- H01 seed1: min 0.804, median 0.995;
- H02 seed0: min 0.891, median 1.000;
- H02 seed1: min 0.852, median 1.000;
- H03 seed0: min 0.930, median 1.000;
- H03 seed1: min 0.99998, median 1.000.

For every frozen radius in {0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50}:
- identified candidate count = 0 in all six cases.

At rho = 1.0:
- the set expands to essentially/all candidates, including the truth-nearest candidate.

## Interpretation

### Diagnostic necessity: PASS

The native PMFS posterior can be extremely sharp while **no source candidate is compatible with all high-confidence measured cells under any modest bounded forward-model discrepancy**.

The strongest example is House02 seed1:
- Native maximum posterior cell probability ≈ 0.879;
- Native ESS ≈ 1.28 cells;
- yet even the most robust source candidate requires rho* ≈ 0.852.

This is direct evidence that the classical point posterior is substantially more confident than the forward-model identification information warrants.

### Main localization utility: FAIL

The robustness object does not recover source identity:
- truth-nearest candidate robustness ranks are roughly 112–149;
- the source-blind robust-best candidates remain 3.55–8.29 m from truth;
- the identified set jumps from empty at moderate radius to non-discriminative at the maximal radius.

Therefore the predeclared V1 partial-identification object is useful as a **model-validity / abstention diagnostic**, but not as the main source-localization evidence mechanism.

## Decision

**PARTIAL IDENTIFICATION V1 = AUXILIARY-ONLY.**

Do not tune the radius grid, House-specific discrepancy norm, or thresholds on these six cases to rescue localization utility.

Retain the principle for a later reliability module:
- detect when PMFS is point-identifying beyond what its forward family supports;
- suppress false posterior collapse / abstain;
- possibly trigger model-switching or active acquisition.

The main-innovation search must continue upstream, toward a mechanism that changes or augments source-identifying forward semantics rather than only bounding posterior confidence.
