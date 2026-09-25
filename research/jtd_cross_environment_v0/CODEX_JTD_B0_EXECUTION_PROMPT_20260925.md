# CODEX TASK — JTD-B0 R=4 Low-Sample Bridge

Branch:
`research/jtd-cross-environment-v0`

Authoritative charter:
`research/jtd_cross_environment_v0/JTD_B0_R4_BRIDGE_CHARTER_20260925.md`

Reference implementation:
JTD-G0 final commit `170d0ccddc559c97744af5409ec1e3642bcfa743`.

## Hard scope

- 0 new plume runs;
- do not touch E2 SEALED_DEV_HOLDOUT;
- do not touch House03;
- do not run dense-source expansion;
- do not change G0 block/PCA feature definition;
- no neural model;
- no closed loop.

## Work

1. Re-extract/verify the original 18×16 R0 observations exactly as in JTD-G0.
2. Construct Q1..Q4 quartets and 4-fold leave-one-realization-out evaluation within each quartet.
3. Implement the pooled within-source OAS covariance estimator exactly as frozen.
4. Implement marginal-preserving within-source temporal-block derangement null exactly as frozen.
5. Produce target-level FULL and SHUFFLED truth-source posterior NLL.
6. Compute all B0-G1..G6 metrics without changing thresholds.
7. Independently recompute the primary paired statistics from the target-level CSV.

## Deliverables

- `JTD_B0_RESULT.json`;
- target-level CSV;
- source-level CSV;
- quartet-level CSV;
- null/provenance manifest;
- hashes of inputs, scripts and outputs;
- branch/final commit;
- review package path/bytes/SHA256.

## Final decision

Exactly one:
- `JTD_B0_PASS_R4_ESTIMATOR_BRIDGE`
- `JTD_B0_FAIL_R4_ESTIMATOR_NOT_RELIABLE`

Stop after B0.