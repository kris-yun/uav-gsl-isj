# Revised V3 evidence-bound checkpoint

Implemented evidence_bounds.py: deterministic bounds on pairwise log working
likelihood in pre-whitened coordinates, matched-key min/max aggregation and
cross-member response overlap diagnostic. It performs no covariance fitting
or epsilon calibration and makes no deployed Bayes-error guarantee.

Tests passed: 10,000 random in-ball perturbations, swap symmetry, monotone
interval expansion, zero-radius collapse, identical candidate separation,
member-key mismatch rejection and the unknown-member swapped-mean counterexample.
Shared random forcing is now M1_CRN_V1, addressed by seed/member/emission
ordinal/time/axis, without candidate position or live-vector ordering. A
particle-removal test confirms new corresponding particles retain their forcing.

## Existing 12-case sensitivity diagnostic

No C2 trace is available yet, so do NOT call this a C2 test. Use opposite-wind
exact response as nominal and same-wind exact response as reference. The norm
of their difference supplies an evaluator-only radius. All sensor outputs
and observations are transformed as log(1+ppm/1ppm), after FOPDT. The identity
metric is a diagnostic normalization, not an estimated Gaussian residual law.

| Prefix s | Nominal correct | V3 accepted correct | Accepted wrong | Abstained |
|---|---:|---:|---:|---:|
| 60 | 5/12 | 4/12 | 0/12 | 8/12 |
| 120 | 7/12 | 4/12 | 0/12 | 8/12 |
| 180 | 12/12 | 4/12 | 0/12 | 8/12 |
| 240 | 12/12 | 4/12 | 0/12 | 8/12 |

Reference evidence lies within every propagated interval. This only checks
the supplied perturbations, not generalization. Zero wrong acceptances is not
sufficient success: the bound rejects most later correct rankings. It must
be evaluated for informative acceptance and matched-coverage baseline utility.
Crosswind radius is NOT provider approximation error and is forbidden online.

Evidence: cstar_m1_v3_existing12_sensitivity_20260910.json, with source trace
hashes and all 48 case/prefix records. No data generation, seed expansion,
posterior/controller edit or closed-loop effectiveness claim.

Next: obtain legal C2 field history/parameter inputs and measure actual
provider-to-reference error separately from intervention variation. Do not
shrink epsilon to make cases pass, treat oracle radii as calibration, or
replace missing deployment wind by full ground-truth wind.
