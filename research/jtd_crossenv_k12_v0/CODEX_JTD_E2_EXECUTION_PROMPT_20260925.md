# CODEX TASK — JTD-E2 Equal-Depth K=12 Cross-Environment Confirmation

Branch:
`research/jtd-crossenv-k12-confirmation-v0`

Authoritative files:
- `research/jtd_crossenv_k12_v0/POST_G1A_ZERO_PLUME_CROSSENV_COMPARATOR_AUDIT_20260925.md`
- `research/jtd_crossenv_k12_v0/JTD_E2_K12_CROSSENV_CONFIRMATION_CHARTER_20260925.md`

Upstream G1A final commit:
`17d3a5ce8aa42aeb70eaf57f6382412a952442fd`.

## Hard scope

- only the three OPEN environments;
- do not open H01 DEV;
- do not open House03;
- no reserve winds;
- no dense-bank model changes;
- no neural model;
- no closed loop;
- no mother-theory representation work.

## Phase R — reference deepening

1. Audit the six existing development realizations/source (4 E2 refs + 2 former E1 targets).
2. Freeze all 108 new reference seed keys and requested seeds before simulation.
3. Generate exactly 6 new reference realizations/source = 108 plume runs.
4. Extract and hash all 12-reference/source tensors.
5. Fit FULL/BP/MBD/DIAG and freeze transformations, covariance parameters, source order, all scoring code hashes, gates and SHUFFLED keys.
6. Commit a pre-target lock BEFORE any E2 fresh target simulation.

## Phase T — genuinely fresh targets

1. Freeze all 72 target seed keys before generation.
2. Generate exactly 4 new targets/source = 72 plume runs.
3. Targets are evaluation-only.
4. Score FULL/BP/MBD/DIAG and SHUFFLED continuity diagnostics without refitting.
5. Compute all target/source/environment/pooled metrics and E2-G1..G6.

## Required deliverables

- `JTD_E2_REFERENCE_ACQUISITION.json`;
- `JTD_E2_PRE_TARGET_LOCK.json`;
- `JTD_E2_TARGET_ACQUISITION.json`;
- `JTD_E2_RESULT.json`;
- 12-reference and 4-target manifests + hashes;
- target-level model metrics CSV;
- environment×source summary CSV;
- environment summary CSV;
- complete posterior arrays for FULL/BP/MBD/DIAG;
- nearest-neighbor diagnostics;
- 10,000 cluster-bootstrap output;
- tail-sensitivity output;
- independent recomputation JSON;
- independent model-refit verification on references;
- input/code/output SHA256 manifests;
- final branch commit;
- review package path/bytes/SHA256.

Final decision exactly one:
- `JTD_E2_GO_EQUAL_DEPTH_CROSS_ENVIRONMENT_CONFIRMED`
- `JTD_E2_HOLD_RESIDUAL_ENVIRONMENT_HETEROGENEITY`
- `JTD_E2_STOP_CROSSBLOCK_VALUE_NOT_ENVIRONMENT_GENERAL`

Stop immediately after E2.