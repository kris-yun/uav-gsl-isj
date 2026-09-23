# Stage-A R2 authoritative execution — structured static operator correction

Date: 2026-09-23
Status: **NO-GO FOR MAIN SOURCE-IDENTIFICATION MECHANISM**

This executes the already-frozen House-level holdout structured-discrepancy principle on the now-available authoritative R2 six-case archive. It does **not** claim ANI semantics; the existing PMFS simulator is not a composable state propagator.

## Frozen screen

Training for each held-out House uses the other two Houses (two seeds each).

Correction:
- candidate-shared;
- no House/source-ID feature;
- target = logit(measured field) - logit(simulated field) on the training truth-owner candidate;
- equal total weight per training run;
- ridge = 1e-3;
- residual clip = 3;
- structured features exactly follow the pre-existing Stage-A script:
  prior logit, candidate-relative x/y/r, interactions, and quadratic anisotropy terms.

The corrected candidate field is scored by the unchanged Native PMFS cell likelihood.

Native posterior reconstruction from the final-leaf partition reproduces the exported source posterior to machine precision (~1e-16 max error), and the Python implementation reproduces the logged Native top-5% endpoint values:
5.527347, 4.001642, 4.107023, 3.700743, 7.782055, 8.211551 m.

## Result

| held-out case | final leaves | Native truth-owner rank | structured rank | Native endpoint m | structured endpoint m |
|---|---:|---:|---:|---:|---:|
| House01 seed0 | 123 | 81 | 87 | 5.5273 | 5.4332 |
| House01 seed1 | 121 | 90 | 92 | 4.0016 | 4.4037 |
| House02 seed0 | 123 | 102 | 106 | 4.1070 | 4.5079 |
| House02 seed1 | 119 | 100 | 101 | 3.7007 | 2.8554 |
| House03 seed0 | 160 | 112 | 158 | 7.7821 | 7.8891 |
| House03 seed1 | 160 | 109 | 159 | 8.2116 | 7.2769 |

Aggregate:
- Native mean endpoint: **5.5551 m**
- scalar-only calibration mean: **5.5633 m**
- structured correction mean: **5.3944 m**
- structured pooled endpoint improvement: **2.89%**
- endpoint non-worse: **3/6**
- truth-owner rank improved: **0/6**
- truth-owner rank non-worse: **0/6**

Thus the endpoint-only 2% gate would misleadingly look positive, but the source-identity gates fail maximally.

## Interpretation

A low-order shared discrepancy contains some transferable structure across Houses, because the structured correction slightly improves the pooled top-5% centroid while scalar calibration does not.

However this transferable structure is **not source-identifying**. In every held-out case the truth-owner candidate rank worsens. The H03 degradation to 158/160 and 159/160 is particularly decisive.

This is another direct example of the already-known benchmark/geometry failure mode:

> a counterfactual probability map can move its top-5% centroid closer to truth even while the candidate evidence assigns a worse ordering to the true source hypothesis.

Therefore a learned static correction of the PMFS source-to-hitMap operator must not be promoted from endpoint gain alone.

## Decision

**STATIC PHYSICS-GUIDED / STRUCTURED OPERATOR CORRECTION = NO-GO AS THE MAIN SOURCE-EVIDENCE MECHANISM ON R2.**

The direct ANI interpretation was already rejected on simulator-semigroup grounds. This new result additionally rejects the retained static-discrepancy rescue as the main line.

Do not tune ridge, residual clip, feature polynomial order, or per-House correction after observing these six cases.

A future correction model would require genuinely richer training data spanning source positions and stochastic plume realizations and must first demonstrate truth-candidate ranking improvement, not just endpoint centroid motion.
