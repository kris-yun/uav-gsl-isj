# CODEX TASK — JTD-E1 Fresh Cross-Environment Gate

Branch: `research/jtd-cross-environment-v0`

Authoritative charter:
`research/jtd_cross_environment_v0/JTD_E1_CROSS_ENVIRONMENT_GATE_20260925.md`

Upstream B1 final commit:
`9bd5d8325f73e5958408e83dc252e24274a65f5d`.

## Hard scope

Use only the three E2 OPEN environments:
- H01 `1,3-2,4_fast`;
- H02 `3,5-1_slow`;
- H02 `4,5-3_slow`.

Existing four E2 realizations/source are frozen references.

Generate exactly 36 new plume runs:
- 2 fresh target realizations;
- 6 frozen sources;
- 3 OPEN environments.

Do not open House01 DEV.
Do not open House03.
Do not generate any reserve wind.
Do not run dense-source expansion.
Do not run closed loop.

## Pre-run lock

Before the first new plume run, commit/save:
- exact 18 reference source×environment groups and their four reference run hashes;
- exact source/probe/time contract hashes;
- exact canonical wind hashes;
- deterministic fresh-target seeds;
- JTD feature contract;
- 200 null derangement keys/environment;
- E1-G1..G7 thresholds;
- scorer/code SHA256.

## Computation

Restore the G0/B1 source-specific OAS model exactly.

For each environment independently:
1. fit scaler/PCA on the 24 frozen reference observations only;
2. fit source-specific FULL Gaussian likelihoods from K=4 reference samples/source;
3. fit 200 SHUFFLED null models using marginal-preserving block derangements of references only;
4. evaluate the 12 genuinely fresh target runs;
5. compute target/source/environment/pooled metrics;
6. apply frozen E1-G1..G7 without modification.

## Required deliverables

- `JTD_E1_PRE_RUN_LOCK.json`;
- `JTD_E1_RESULT.json`;
- fresh-target run manifest and cube hashes;
- target-level CSV;
- environment×source CSV;
- environment summary CSV;
- bootstrap output;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- branch/final commit;
- review package path/bytes/SHA256.

Final decision exactly one:
- `JTD_E1_GO_CROSS_ENVIRONMENT_TEMPORAL_DEPENDENCE`
- `JTD_E1_HOLD_ENVIRONMENT_HETEROGENEOUS_SIGNAL`
- `JTD_E1_STOP_TEMPORAL_DEPENDENCE_NOT_GENERAL`

Stop immediately after E1.