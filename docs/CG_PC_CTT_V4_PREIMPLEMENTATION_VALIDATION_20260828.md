# CG-PC-CTT V4 pre-implementation validation — revised science contract

Date: 2026-08-28
Status: **REFERENCE REVISED; C++ TEMPORARILY HELD FOR THREE-HOUSE TRUTH-BLIND COVERAGE**

## What remains valid from the earlier validation

The paper-level method remains:

1. M1 Spatiotemporal Transport Representation;
2. M2 Cross-Context Invariant Causal Source Residual;
3. M3 Observation-Resolved Minimum Causal Assimilation.

The archived cross-context response-field analysis still supports the existence of source-stable structure as **offline qualification evidence only**. The global eigenspace is never an online unobserved-field classifier.

The physical-stop conclusion also remains binding: eight completed blocks at one physical stop are repeated measurements of one spatial context, not eight independent spatial dimensions.

M3 stress tests remain valid: the KL/I-projection preserves native conditional shape and returns native PMFS exactly when `beta >= alpha`.

## Why the previous C++ authorization is superseded

A pre-translation scientific audit found three blocking defects in the then-final Python reference:

1. `component_labels` were consumed but never constructed, so calibration members `0..3` were absent from the final executable contract;
2. held-out scoring restarted the scoring-member mixture, violating coherent transport identity;
3. the geometry-prior mixture of the same candidate family was not an absolute adequacy screen and accepted a gross shared-misspecification counterexample.

During executable repair a fourth implementation defect was found: NumPy advanced indexing in `coherent_source_score()` changed axis order, so the code did not reliably implement "sum stops within member, then marginalize members."

These are upstream reference defects, not C++ issues. Therefore the older `CODEX_IMPLEMENTATION_AUTHORIZED = YES` is revoked.

## Revised M1 closure

The final reference now contains canonical `build_components(...)`:

- actual physical stops only;
- calibration members `0..3` only;
- persistent source-carrier rectangle adjacency;
- finite `C_eff = C_tr + (1/4 + eps_T^2)I`;
- leave-one-calibration-member-out boundary reproducibility;
- exact geometric aliases forced unresolved;
- connected components returned as the observation-resolved source quotient.

No hit outcome enters component construction.

## Revised M2 closure

Training and held-out prediction preserve the joint latent `(source, scoring transport member)`.

For held-out stop `h`, component predictive score is the log ratio of joint component evidence with and without `h`, conditioned on the other physical stops. A new uniform scoring-member mixture is forbidden.

The absolute source-null is now frozen as Jeffreys-Beta prequential Bernoulli prediction:

`theta ~ Beta(1/2,1/2)`,

fit only to training-stop hit fractions in each LOSO fold. The selected source component must beat this source-independent null on every held-out stop as well as not lose to a rival component.

This deterministic counterexample must now ABSTAIN:

- observed stop outcome `r=1`;
- selected candidate family predicts `p=0.01`;
- rival predicts `p=0.005`.

## Revised selftest status

The revised local reference/selftest passes:

`V4_FINAL_REFERENCE_SCIENCE_CONTRACT PASS`

The regression suite includes both earlier blocking counterexamples, component construction, finite stable-complement precision, candidate/member permutations, replay protection, and 10,000 KL/I-projection randomized states.

No localization outcome was used to select a scientific threshold.

## H02 old replay result is diagnostic, not revised coverage

The earlier H02 report of 48 ABSTAIN / 2 ACCEPT among 50 OFF windows was produced under the superseded M2 implementation. It remains useful historical diagnostic evidence but **must not be quoted as activation coverage for the revised reference**.

H01/H02/H03 revised truth-blind coverage must be recomputed from archived OFF development paths.

## Required next step before C++

Codex must materialize each available development OFF source-update context to:

- `stop_probability [S,M,J]`;
- `stop_r [J]`;
- `rectangles [S,4]`;
- `geometry_prior [S]`;
- metadata only: House, seed, update id, `T`.

Truth/source location, final localization error, ON result, route id, and plume seed must not enter the audit.

Then run:

`python3 experiments/cg_pc_ctt/v4_truthblind_coverage.py <context dirs/files> --out-csv <...> --out-json <...>`

Publish House-wise counts and ABSTAIN reasons.

If all three Houses yield zero ACCEPT, stop. If ACCEPT exists in only one House, stop. Otherwise the result is an actionability report—not performance evidence—and direct C++ translation may proceed.

## Development/confirmation boundary

If C++ parity and smoke pass, freeze source/binary/launch hashes and run exactly one development matrix:

`H01/H02/H03 × seeds 0..9 × OFF/ON`.

Do not tune after inspecting individual arms.

Only a frozen development GO can authorize fresh confirmatory seeds 10..19.

`CODEX_CPP_AUTHORIZATION = PENDING_TRUTHBLIND_COVERAGE`
