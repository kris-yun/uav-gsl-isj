# Native615 VGR interactive pilot: P1 complete, stop

Status: `P1_COMPLETE_STOP`. Four frozen cases, four arms, 16/16 results.
This is a two-source development pilot, not a 96-case campaign or a scientific
main-innovation PASS. No new GADEN plumes were generated. No model was changed
or retrained after pilot outcomes.

All arms used the same Native615 support and Native top-5-percent probability
weighted source-position estimator. Geometry success is final valid estimate
error <=0.5 m within the fixed 300 s search budget; timeout is reported separately.

| Arm | Geometric successes | Mean error m | Mean path m | Timeout | Declared | Wrong declaration |
| --- | --- | --- | --- | --- | --- | --- |
| Native | 2/4 | 4.1652174501 | 100.9208530633 | 4 | 0 | 0 |
| Candidate-GRU | 1/4 | 2.7481326303 | 64.5162309807 | 2 | 2 | 1 |
| BRG | 0/4 | 7.1235073010 | 67.9568993853 | 1 | 3 | 3 |
| BRG-ungated | 0/4 | 6.6403811625 | 77.9530681550 | 2 | 2 | 2 |

## Fixed cases and failure observations

The exact original first/fourth sources and first two realizations were used:
`source_0_replica_0`, `source_0_replica_1`, `source_3_replica_0`,
`source_3_replica_1`.

The first source is `pmfs_24_13`, outside the exact Native615 label support.
Both cases are retained: Native's final errors were 0.400974696 and 0.407649266 m,
counted as geometric success despite timeout. All learned arms received zero
positive measurement blocks in these two cases and geometrically failed.
Unsupported exact-cell rank is NA; extended true-label probability is zero and
NLL is positive infinity, without nearest-label substitution.

The second source is the in-support `pmfs_2_4`. GRU succeeded on its second
realization (0.318282589 m); its first declaration at 0.754692724 m is incorrect
under the frozen radius. Both BRG arms declared success on both realizations
but their final source estimates were wrong. Their trajectories did receive
positive gas measurements; this is not a missing-observation execution failure.

All 16 valid runs have finite final estimates, matching Native615 support,
zero recorded navigation failures, and no service/infrastructure failure.
Raw endpoint geometry, probability-map estimator, four-arm context, and path
length were independently recomputed in `INDEPENDENT_RECOMPUTATION.json`.
Shorter paths alone are not evidence of better localization, since some arms
stopped on wrong declarations.

## Preserved provenance and execution repairs

The original support HOLD and 96-case manifest remain intact. The authorized
H01-only rebuild contains 596 legal candidates and 52,448 PMFS forwards;
H02/H03 caches are reused. Training used the local RTX5060 GPU, fixed recipe
and reference/dev selection, with all three weights frozen before P0.

Two representational H01 projected probabilities were 1.0000000000000004.
Validation stopped before an optimizer step; the documented roundoff-only
projection correction preserves the feature/model equations.

Original P0 V1 is preserved and excluded as an infrastructure batch: GRU
action discovery timed out before PMFS initialization and delivered no events.
The readiness wait changed from 10 to 120 wall seconds while simulation clock
remained zero. All four P0 arms were rerun under that shared V2 runner, with
identical frozen weights. No selective outcome reuse.

## Review artifact

`C:/Users/50176/Downloads/BRG_NATIVE615_P1_REVIEW_20260927.zip`

- Bytes: 43,917,486
- SHA256: `923d4f2c383a61c618af25b6e2c18fc8378fb54e008af19ba4f2e0ed23979b5e`
- 945 internal SHA256 entries verified after local copy; no duplicate entries.
- Includes V2 and excluded V1 raw poses, goals, observations, beliefs,
  runtime bindings, all96 case contracts, weights, legal-support views,
  source/feature/training provenance, and independent verification code.

The pilot shows no BRG closed-loop gain on these four cases. It does not
estimate all96-case performance. Automatic expansion remains disabled.
